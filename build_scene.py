"""Original procedural shishi costume and stage; preserve the floating G1."""
from pathlib import Path
import math
import json
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent

def sub(parent, tag, **kw):
    return ET.SubElement(parent, tag, {k: str(v) for k, v in kw.items()})

def geom(body, kind, pos, size, material, **kw):
    return sub(body, 'geom', type=kind, pos=pos, size=size, material=material,
               contype='0', conaffinity='0', group='2', density='0', **kw)

def texture():
    im = Image.new('RGB', (512,512), '#0d543e')
    d = ImageDraw.Draw(im)
    for ox in range(-64,600,128):
        for oy in range(-64,600,128):
            pts=[]
            for i in range(110):
                a=i/109*math.pi*3.9
                r=2+i/109*37
                pts.append((ox+r*math.cos(a),oy+r*math.sin(a)))
            d.line(pts, fill='#d6dbc0', width=5, joint='curve')
            d.arc((ox-42,oy-42,ox+86,oy+85),0,100, fill='#d6dbc0',width=4)
            d.ellipse((ox+47,oy+40,ox+58,oy+47),fill='#d6dbc0')
    im.save(ROOT/'assets/karakusa.png')

def cloak():
    # A rigid visual approximation, deliberately not a fabric simulation.
    lines=[]; rows=14; cols=29
    for i in range(rows):
        u=i/(rows-1)
        for j in range(cols):
            a=math.pi*0.29+j/(cols-1)*math.pi*1.42
            r=.215+u*.04+.014*math.sin(j*math.pi/2)
            x=-.055+r*math.cos(a)
            y=r*math.sin(a)
            z=-.055-u*.57+.016*math.cos(j*2.2)*u
            lines.append(f'v {x:.6f} {y:.6f} {z:.6f}')
    for i in range(rows):
        for j in range(cols):
            lines.append(f'vt {j/(cols-1)*2:.6f} {i/(rows-1)*2:.6f}')
    for i in range(rows-1):
        for j in range(cols-1):
            a=i*cols+j+1;b=a+1;c=a+cols;dd=c+1
            lines += [f'f {a}/{a} {c}/{c} {b}/{b}',f'f {b}/{b} {c}/{c} {dd}/{dd}']
    (ROOT/'assets/cloak.obj').write_text('\n'.join(lines)+'\n')

def main():
    texture();cloak()
    tree=ET.parse(ROOT/'assets/g1/g1_original.xml');root=tree.getroot()
    root.set('model','shishimai_g1_free_standing')
    root.find('compiler').set('meshdir','assets/g1/third_party/unitree_g1/assets')
    root.find('option').set('timestep','.002')
    root.find('option').set('gravity','0 0 -9.81')
    root.find('option').set('iterations','60')
    profile=json.loads((ROOT/'assets/g1_profile.json').read_text())
    for name,v in profile['joints'].items():
        root.find(f".//joint[@name='{name}_joint']").set('actuatorfrcrange',f"{-v['max_torque_nm']} {v['max_torque_nm']}")
    vis=sub(root,'visual')
    sub(vis,'global',offwidth='1280',offheight='720',azimuth='25',elevation='-10')
    sub(vis,'quality',shadowsize='4096',offsamples='4')
    sub(vis,'headlight',ambient='.24 .24 .29',diffuse='.5 .5 .5',specular='.2 .2 .2')
    sub(vis,'map',znear='.01',zfar='30',fogstart='8',fogend='20')
    asset=root.find('asset')
    for name,rgba in [('lacquer','.64 .025 .025 1'),('gold','.83 .57 .17 1'),
                      ('ivory','.91 .88 .76 1'),('ink','.012 .014 .016 1'),
                      ('stage','.17 .10 .055 1'),('navy','.018 .029 .05 1'),
                      ('vermillion','.49 .04 .025 1'),('paper','.92 .65 .35 1')]:
        sub(asset,'material',name=name,rgba=rgba,specular='.4' if name in ('gold','lacquer') else '.1',
            shininess='.5' if name=='lacquer' else '.1')
    sub(asset,'texture',name='karakusa',type='2d',file='assets/karakusa.png')
    sub(asset,'material',name='cloth',texture='karakusa',texuniform='false',specular='.03')
    sub(asset,'mesh',name='cloak',file='../../../../cloak.obj')
    world=root.find('worldbody')
    sub(world,'geom',name='safety_floor',type='plane',size='0 0 .05',material='stage',friction='1.15 .005 .0001')
    sub(world,'light',pos='2 -3 4',dir='-.4 .5 -1',diffuse='.95 .78 .54',specular='.5 .4 .25',castshadow='true')
    sub(world,'light',pos='-1 2 3',dir='.3 -.4 -1',diffuse='.4 .5 .65')
    sub(world,'light',pos='0 -2 2',dir='0 1 -.2',diffuse='.5 .5 .5',castshadow='false')
    # Plank seams, stage edge and a restrained, original festival setting.
    for i in range(-36,37):
        geom(world,'box',f'{i*.25} 0 -.0006','.002 9 .001','navy')
    for y in (-7.5,7.5):
        geom(world,'box',f'0 {y} .025','9 .04 .025','gold')
    geom(world,'box','-7 0 1.5','.03 9 1.5','navy')
    for y in (-3.0,3.0):
        geom(world,'cylinder',f'-4.5 {y} 1.25','.09 1.25','vermillion')
        geom(world,'ellipsoid',f'-4.5 {y} 2.32','.21 .21 .28','paper')
        for z in (2.08,2.16,2.24,2.32,2.40,2.48,2.56):
            geom(world,'cylinder',f'-4.5 {y} {z}','.212 .005','gold')
    geom(world,'box','-4.55 0 2.8','.10 3.5 .08','vermillion')
    geom(world,'box','-4.55 0 2.95','.14 3.7 .04','ink')
    torso=root.find(".//body[@name='torso_link']")
    mask=sub(torso,'body',name='shishi_costume',pos='.045 0 .395')
    sub(mask,'inertial',mass='.45',pos='0 0 -.04',diaginertia='.006 .006 .007')
    geom(mask,'ellipsoid','0 0 0','.16 .205 .145','lacquer')
    geom(mask,'mesh','0 0 0','1','cloth',mesh='cloak')
    geom(mask,'box','.13 0 -.092','.105 .177 .025','lacquer')
    geom(mask,'box','.205 0 -.043','.014 .165 .032','ink')
    geom(mask,'box','.223 0 -.085','.019 .174 .012','gold')
    geom(mask,'ellipsoid','.175 0 .009','.075 .12 .041','ivory')
    geom(mask,'ellipsoid','.226 0 .039','.042 .088 .035','lacquer')
    for y in (-.044,.044):
        geom(mask,'ellipsoid',f'.263 {y} .035','.012 .02 .012','ink')
    for y in (-.18,.18):
        geom(mask,'ellipsoid',f'-.015 {y} .078','.07 .045 .087','gold')
    for side in (-1,1):
        y=side*.113
        geom(mask,'ellipsoid',f'.125 {y} .082','.075 .068 .07','gold')
        geom(mask,'ellipsoid',f'.184 {y} .083','.019 .044 .047','ivory')
        geom(mask,'ellipsoid',f'.202 {y} .083','.009 .024 .028','ink')
        geom(mask,'sphere',f'.211 {y-.009} .094','.007','ivory')
        geom(mask,'capsule',f'.135 {y} .15','.021 .056','ivory',euler='1.570796 0 .25')
    for y in (-.133,-.088,-.044,0,.044,.088,.133):
        geom(mask,'box',f'.224 {y} -.025','.013 .014 .013','ivory')
        geom(mask,'box',f'.223 {y} -.071','.012 .014 .009','ivory')
    for j in range(15):
        a=-math.pi*.55+j/14*math.pi*1.1
        y=.19*math.sin(a);z=.125*math.cos(a)
        geom(mask,'ellipsoid',f'-.035 {y} {z+.04}','.08 .029 .053','ivory',euler=f'{-a} 0 0')
    sub(mask,'site',name='lion_nose',pos='.27 0 .035',size='.006',rgba='0 0 0 0')
    sub(mask,'site',name='lion_center',pos='0 0 0',size='.006',rgba='0 0 0 0')
    # Use the exact public model's floating joint and all 29 position actuators.
    ET.indent(tree,space='  ')
    tree.write(ROOT/'scene.xml',encoding='unicode',xml_declaration=False)
    import mujoco
    from kinematics import export_model
    export_model(mujoco.MjModel.from_xml_path(str(ROOT/'scene.xml')),ROOT/'assets/g1_dynamics.json')
    print('Wrote scene.xml: floating G1, 29 actuators, 0.45 kg torso-mounted costume.')

if __name__=='__main__':main()
