"""Full-frame dynamic edition, rendered from the evaluated physics trajectory."""
from pathlib import Path
import argparse,json,subprocess
import imageio.v2 as imageio
import imageio_ffmpeg
import mujoco
import numpy as np
from PIL import Image,ImageDraw
from policy import phase
from video import font,sound

ROOT=Path(__file__).resolve().parent

def prepare(width,height):
    episode=np.load(ROOT/'evidence/episode.npz')
    states=episode['qpos']
    m=mujoco.MjModel.from_xml_path(str(ROOT/'scene.xml'));d=mujoco.MjData(m)
    m.vis.global_.offwidth=max(width,1920);m.vis.global_.offheight=max(height,1080)
    r=mujoco.Renderer(m,height=height,width=width)
    c=mujoco.MjvCamera();c.type=mujoco.mjtCamera.mjCAMERA_FREE
    c.azimuth=205;c.elevation=-10;c.distance=2.72
    opt=mujoco.MjvOption();opt.geomgroup[3]=0;opt.sitegroup[:]=0
    return states,m,d,r,c,opt

def frame_at(t,states,m,d,r,c,opt,width,height):
    index=min(len(states)-1,round(t/.02));d.qpos[:]=states[index];mujoco.mj_forward(m,d)
    c.lookat[:]=[d.qpos[0],d.qpos[1],.77]
    r.update_scene(d,camera=c,scene_option=opt)
    im=Image.fromarray(r.render()).convert('RGBA')
    overlay=Image.new('RGBA',im.size);draw=ImageDraw.Draw(overlay)
    scale=height/1080
    def point(x,y):return (round(x*scale),round(y*scale))
    def text(x,y,s,size,color):
        draw.text(point(x,y),s,font=font(round(size*scale)),fill=color,
                  stroke_width=max(1,round(scale)),stroke_fill=(8,14,19,220))
    ivory=(239,232,211,255);gold=(219,185,110,255);muted=(190,202,202,255)
    text(36,20,'獅子舞',76,ivory)
    text(40,112,'SHISHIMAI / DYNAMIC V2',28,gold)
    text(width/scale-510,30,'ACTUAL MUJOCO ROLLOUT / 1x',23,ivory)
    offset=float(np.linalg.norm(d.qpos[:2]-states[0,:2]))
    text(width/scale-510,69,f'Tracking view / root offset {offset:.2f} m',21,muted)
    draw.rectangle((0,height-round(96*scale),width,height),fill=(9,17,23,226))
    number=1+sum(t>=v for v in (2.5,7,14,23,30,35))
    name=phase(t).split(' / ')[-1].upper()
    text(40,height/scale-87,f'{number:02d}  /  {name}',32,gold)
    text(40,height/scale-39,'Free-standing / 29 motor joints / scripted dance + pretrained balance / simulation only',21,ivory)
    text(width/scale-245,height/scale-83,f'{t:04.1f} / 36.0 s',27,ivory)
    draw.rectangle((0,height-round(6*scale),round(width*t/36),height),fill=(185,60,41,255))
    return Image.alpha_composite(im,overlay).convert('RGB')

def preview():
    width,height=1280,720
    states,m,d,r,c,opt=prepare(width,height)
    times=[0,4,5.5,8.8,10.6,17,25,33.5]
    sheet=Image.new('RGB',(width*4//2,height*2//2))
    for i,t in enumerate(times):
        image=frame_at(t,states,m,d,r,c,opt,width,height)
        image.save(ROOT/f'evidence/preview-v2-{i}.jpg',quality=94)
        sheet.paste(image.resize((width//2,height//2)),((i%4)*width//2,(i//4)*height//2))
    r.close();sheet.save(ROOT/'evidence/preview-v2-sheet.jpg',quality=95)
    print('Wrote eight actual-trajectory preview frames and preview-v2-sheet.jpg')

def render_episode(output,width=1920,height=1080):
    states,m,d,r,c,opt=prepare(width,height)
    duration=len(states)*.02;fps=30
    silent=output.with_name(output.stem+'-silent.mp4')
    writer=imageio.get_writer(str(silent),fps=fps,codec='libx264',quality=7,
        pixelformat='yuv420p',macro_block_size=1,ffmpeg_params=['-movflags','+faststart','-preset','fast'])
    for k in range(round(duration*fps)):
        frame=frame_at(k/fps,states,m,d,r,c,opt,width,height)
        writer.append_data(np.asarray(frame))
        if k in [0,180,420,690,960]:frame.save(ROOT/f'evidence/frame-{k:04d}.jpg',quality=94)
        if k%180==0:print(f'Rendered dynamic v2: {k}/{round(duration*fps)} frames',flush=True)
    writer.close();r.close()
    wav=ROOT/'evidence/percussion.wav';sound(duration,wav)
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-v','error','-i',str(silent),'-i',str(wav),
      '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','128k','-shortest',
      '-movflags','+faststart',str(output)],check=True)
    print(json.dumps({'video':str(output),'duration':duration,'fps':fps,'resolution':[width,height],
      'bytes':output.stat().st_size,'camera':'tracks actual base XY; fixed angle and distance; root-offset HUD'},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');a=p.parse_args()
    if a.preview:preview()
    else:render_episode(ROOT/'result.mp4')
