"""Proprioception-only static gravity compensation for the known G1/costume.

The exported rigid-body masses/COMs are used for waist/arm feedforward only.
No simulator state, contacts, external body support or base translation is used.
"""
from pathlib import Path
import json
import numpy as np

def rotation(quat):
    w,x,y,z=quat
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])

def axis_rotation(axis,angle):
    a=np.asarray(axis);c=np.cos(angle);s=np.sin(angle)
    x,y,z=a;skew=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    return c*np.eye(3)+(1-c)*np.outer(a,a)+s*skew

class GravityCompensator:
    def __init__(self):
        p=Path(__file__).resolve().parent/'assets/g1_dynamics.json'
        self.bodies=json.loads(p.read_text())['bodies']
        self.rest=[rotation(b['quat']) for b in self.bodies]

    def calculate(self,q,quat):
        count=len(self.bodies);r=np.zeros((count,3,3));p=np.zeros((count,3))
        f=np.zeros((count,3));moment=np.zeros((count,3));axes=np.zeros((29,3));origins=np.zeros((29,3))
        r[0]=np.eye(3);base=rotation(quat)
        for i,b in enumerate(self.bodies):
            if i==0:continue
            parent=b['parent'];index=b['motor_index']
            if b['name']=='pelvis':r[i]=base;p[i]=0
            else:
                r[i]=r[parent]@self.rest[i]
                p[i]=p[parent]+r[parent]@np.array(b['pos'])
                if index>=0:
                    axis=np.array(b['axis']);jp=np.array(b['joint_pos'])
                    axes[index]=r[i]@axis;origins[index]=p[i]+r[i]@jp
                    turn=axis_rotation(axis,q[index]-b['qref'])
                    p[i]+=r[i]@(jp-turn@jp);r[i]=r[i]@turn
            f[i,2]=9.81*b['mass']
            com=p[i]+r[i]@np.array(b['com'])
            moment[i]=np.cross(com,f[i])
        tau=np.zeros(29)
        for i in range(count-1,0,-1):
            b=self.bodies[i];index=b['motor_index']
            if index>=0:tau[index]=axes[index]@(moment[i]-np.cross(origins[index],f[i]))
            parent=b['parent'];f[parent]+=f[i];moment[parent]+=moment[i]
        return tau

def export_model(model,path):
    from vendor.him.hardware_constants import G1_29_JOINT_NAMES
    motor={model.joint(n+'_joint').id:i for i,n in enumerate(G1_29_JOINT_NAMES)}
    bodies=[]
    for i in range(model.nbody):
        joint=int(model.body_jntadr[i]);idx=motor.get(joint,-1) if model.body_jntnum[i] else -1
        bodies.append({'name':model.body(i).name,'parent':int(model.body_parentid[i]),
          'pos':model.body_pos[i].tolist(),'quat':model.body_quat[i].tolist(),
          'mass':float(model.body_mass[i]),'com':model.body_ipos[i].tolist(),'motor_index':idx,
          'axis':model.jnt_axis[joint].tolist() if idx>=0 else [0,0,1],
          'joint_pos':model.jnt_pos[joint].tolist() if idx>=0 else [0,0,0],
          'qref':float(model.qpos0[model.jnt_qposadr[joint]]) if idx>=0 else 0})
    Path(path).write_text(json.dumps({'gravity_m_s2':9.81,'bodies':bodies},indent=2)+'\n')
