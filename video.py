"""Render saved physics states. Editorial graphics and original synthesized audio."""
from pathlib import Path
import math,subprocess,wave,json
import imageio.v2 as imageio
import imageio_ffmpeg
import mujoco
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from policy import phase

ROOT=Path(__file__).resolve().parent
FONT=ROOT/'assets/fonts/ZenOldMincho-Regular.ttf'
def font(size):
    for path in (FONT,Path('C:/Windows/Fonts/YuGothM.ttc'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')):
        if path.exists():return ImageFont.truetype(str(path),size)
    return ImageFont.load_default()

def sound(seconds,path):
    sr=48000;n=round(seconds*sr);out=np.zeros(n,dtype=float);rng=np.random.default_rng(42)
    def hit(start,kind,amp):
        length=.6 if kind=='drum' else .16
        t=np.arange(int(sr*length))/sr
        if kind=='drum':
            f=65+55*np.exp(-t*35)
            s=(np.sin(2*np.pi*np.cumsum(f)/sr)+.32*np.sin(2*np.pi*151*t))*np.exp(-t*9)
            s+=rng.normal(0,.12,len(t))*np.exp(-t*65)
        else:s=(np.sin(2*np.pi*1450*t)+.35*np.sin(2*np.pi*2141*t))*np.exp(-t*40)
        s*=np.minimum(t*1500,1)*amp
        k=round(start*sr);m=min(len(s),n-k)
        if m>0:out[k:k+m]+=s[:m]
    for k in range(int((seconds-.25)/.5)):
        t=.25+k*.5
        hit(t,'drum' if k%4 in (0,2) else 'wood',.34 if k%4==0 else .16)
    out*=np.minimum(np.arange(n)/sr,1)*np.minimum((n-np.arange(n))/sr,1)
    out=np.clip(out,-.94,.94)
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((out*32767).astype('<i2').tobytes())

def render_episode(output,width=1280,height=720):
    episode=np.load(ROOT/'evidence/episode.npz');states=episode['qpos'];times=episode['times']
    model=mujoco.MjModel.from_xml_path(str(ROOT/'scene.xml'));data=mujoco.MjData(model)
    fps=30;duration=len(states)*.02;panel=round(width*.29);view_width=width-panel
    renderer=mujoco.Renderer(model,height=height,width=view_width)
    camera=mujoco.MjvCamera();camera.type=mujoco.mjtCamera.mjCAMERA_FREE
    camera.azimuth=205;camera.elevation=-10;camera.distance=3.0
    camera.lookat[:]=[.0,0,.78]
    opt=mujoco.MjvOption();opt.geomgroup[3]=0;opt.sitegroup[:]=0
    silent=output.with_name(output.stem+'-silent.mp4')
    writer=imageio.get_writer(str(silent),fps=fps,codec='libx264',quality=8,
                             pixelformat='yuv420p',macro_block_size=1,
                             ffmpeg_params=['-movflags','+faststart','-preset','fast'])
    title_font=font(round(height*.062));jp_font=font(round(height*.094))
    body_font=font(round(height*.024));small_font=font(round(height*.019));big_font=font(round(height*.04))
    samples=[]
    for k in range(round(duration*fps)):
        t=k/fps;idx=min(len(states)-1,round(t/.02))
        data.qpos[:]=states[idx];mujoco.mj_forward(model,data)
        # Camera follows no actor; one continuous, fixed framing shows real drift.
        renderer.update_scene(data,camera=camera,scene_option=opt)
        frame=Image.new('RGB',(width,height),'#0d141a')
        frame.paste(Image.fromarray(renderer.render()),(panel,0))
        d=ImageDraw.Draw(frame);cream='#ebe4d3';muted='#a2adae';gold='#cbb071';red='#bd4236'
        x=round(panel*.09)
        d.text((x,36),'HIM OPEN BUILD  /  2026',font=small_font,fill=gold)
        d.line((x,75,panel-x,75),fill='#3a4446',width=1)
        d.text((x,108),'獅子舞',font=jp_font,fill=cream)
        d.text((x,195),'SHISHIMAI',font=title_font,fill=cream)
        d.text((x,260),'THE LION,\nREAWAKENED.',font=big_font,fill=gold,spacing=6)
        d.text((x,365),'A Japanese lion dance\nperformed by Unitree G1.',font=body_font,fill=cream,spacing=8)
        phase_index=1+sum(t>=v for v in (4,10,19,29,35))
        d.text((x,456),f'{phase_index:02d}  /  '+phase(t).split(' / ')[0].upper(),font=small_font,fill=gold)
        d.text((x,491),phase(t).split(' / ')[-1],font=body_font,fill=cream)
        d.text((x,558),'Free-standing · 29 joints\n0.45 kg wearable costume\nJoint + IMU feedback',font=small_font,fill=muted,spacing=7)
        d.rectangle((panel,0,width,30),fill='#0d141a')
        d.text((panel+18,5),'ACTUAL PHYSICS ROLLOUT  /  1x SPEED',font=small_font,fill=cream)
        d.rectangle((panel,height-57,width,height),fill='#0d141a')
        d.text((panel+18,height-48),'Pretrained balance + scripted dance · Simulation only',font=small_font,fill=cream)
        d.text((panel+18,height-26),'Torso-mounted mask; rigid visual cloth. No hardware validation.',font=small_font,fill=muted)
        d.text((width-113,45),f'{t:04.1f}s',font=body_font,fill=cream)
        d.rectangle((0,height-5,width,height),fill='#283635')
        d.rectangle((0,height-5,round(width*t/duration),height),fill=red)
        writer.append_data(np.asarray(frame))
        if k in [0,180,420,690,960]:
            f=ROOT/f'evidence/frame-{k:04d}.jpg';frame.save(f,quality=94);samples.append(str(f.name))
        if k%180==0:print(f'Rendered {k}/{round(duration*fps)} frames',flush=True)
    writer.close();renderer.close()
    audio=ROOT/'evidence/percussion.wav';sound(duration,audio)
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ffmpeg,'-y','-v','error','-i',str(silent),'-i',str(audio),'-map','0:v:0','-map','1:a:0',
                    '-c:v','copy','-c:a','aac','-b:a','128k','-shortest','-movflags','+faststart',str(output)],check=True)
    print(json.dumps({'video':str(output),'duration':duration,'fps':fps,'resolution':[width,height],
                      'bytes':output.stat().st_size,'frames':round(duration*fps),'inspected_frames':samples},indent=2))

if __name__=='__main__':render_episode(ROOT/'result.mp4')
