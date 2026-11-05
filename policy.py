"""Shishimai choreography + credited NVIDIA lower-body balance inference.

Only joint/IMU observations enter act(). No world pose, contact oracle or mocap.
The lion head is a lightweight torso-mounted costume, not a manipulated object.
"""
from pathlib import Path
import math,json
import numpy as np
from vendor.him.balance_policy import BalancePolicy
from vendor.him.hardware_constants import G1_29_JOINT_NAMES
from kinematics import GravityCompensator

ROOT=Path(__file__).resolve().parent
DT=.02
DURATION=36.0
PROFILE=json.loads((ROOT/'assets/g1_profile.json').read_text())
LIMITS=[PROFILE['joints'][n] for n in G1_29_JOINT_NAMES]
KP=np.array([v['kp'] for v in LIMITS],dtype=float)
KD=np.array([v['kd'] for v in LIMITS],dtype=float)
EFFORT=np.array([v['max_torque_nm'] for v in LIMITS],dtype=float)
QMIN=np.array([v['position_min_rad'] for v in LIMITS])
QMAX=np.array([v['position_max_rad'] for v in LIMITS])

def smooth(x):
    x=float(np.clip(x,0,1));return x*x*x*(10+x*(-15+6*x))

def window(t,start,end,ramp=.7):
    return smooth((t-start)/ramp)*smooth((end-t)/ramp)

def choreography(t):
    """Large expressive motor targets; floating-base balance still owns the legs."""
    def pose(yaw=0,roll=0,pitch=0,lp=-.35,lr=.28,le=1.15,rp=None,rr=None,re=None):
        q=np.zeros(29);q[12:15]=[yaw,roll,pitch]
        q[15:22]=[lp,lr,0,le,0,0,0]
        q[22:29]=[lp if rp is None else rp,-lr if rr is None else rr,0,le if re is None else re,0,0,0]
        return q
    poses=[
      (0.,pose()),
      (2.5,pose(lp=-.80,lr=.8,le=.3)),
      (4.,pose(pitch=.23,lp=-1.15,lr=.5,le=.4)),
      (5.5,pose(pitch=-.12,lp=-1.90,lr=.25,le=.2)),
      (7.,pose(pitch=.02,lp=-.35,lr=1.20,le=.15)),
      (8.8,pose(yaw=-.80,roll=-.08,pitch=.06,lp=-.4,lr=1.1,le=.2,rp=-1.25,rr=-.35,re=.65)),
      (10.6,pose(yaw=.80,roll=.08,pitch=.06,lp=-1.25,lr=.35,le=.65,rp=-.4,rr=-1.1,re=.2)),
      (12.4,pose(yaw=-.80,pitch=.05,lp=-.6,lr=1.0,le=.25)),
      (14.,pose(lp=-1.05,lr=1.1,le=.6)),
      (23.,pose(lp=-1.05,lr=1.1,le=.6)),
      (24.8,pose(yaw=.90,pitch=-.08,lp=-1.65,lr=.65,le=.25)),
      (26.6,pose(yaw=-.90,pitch=.10,lp=-.65,lr=1.2,le=.25)),
      (28.4,pose(yaw=.90,pitch=-.08,lp=-1.65,lr=.65,le=.25)),
      (30.,pose(pitch=.02,lp=-.5,lr=1.2,le=.15)),
      (31.6,pose(pitch=.24,lp=-1.1,lr=.55,le=.35)),
      (33.5,pose(pitch=-.10,lp=-1.90,lr=.45,le=.15)),
      (35.,pose(lp=-.55,lr=1.0,le=.25)),
      (36.,pose())]
    q=poses[-1][1].copy()
    for (a,qa),(b,qb) in zip(poses,poses[1:]):
        if t<=b:
            u=smooth((t-a)/(b-a));q=qa*(1-u)+qb*u;break
    if 14<=t<=23:
        a=2*math.pi*(t-14)/1.5;w=window(t,14,23,.7)
        q[12]+=.32*w*math.sin(a)
        q[13]+=.085*w*math.sin(a)
        q[14]+=.12*w*(.2+math.cos(a))
        q[15]+=.42*w*math.sin(a);q[22]-=.42*w*math.sin(a)
        q[16]-=.28*w*(1-math.cos(a));q[23]+=.28*w*(1-math.cos(a))
        q[18]+=.25*w*math.sin(a);q[25]-=.25*w*math.sin(a)
    return q

def phase(t):
    for end,name in [(2.5,'Awakening'),(7,'Rei / bow and sky reach'),(14,'Mie / sweeping turns'),
                     (23,'Mai / lion frenzy'),(30,'Festival fan'),(35,'Final blessing'),(1000,'Quiet stand')]:
        if t<end:return name

class Policy:
    def __init__(self,neutral=False):
        self.balance=BalancePolicy(str(ROOT/'models/balance.onnx'))
        self.balance.warmup()
        self.gravity=GravityCompensator()
        self.neutral=neutral
        self.reset()

    def reset(self):
        self.balance.reset();self.calls=0;self.last=None;self.initial=None;self.aborted=False

    def act(self,observation):
        q=np.asarray(observation['q'],dtype=float)
        dq=np.asarray(observation['dq'],dtype=float)
        quat=np.asarray(observation['quat'],dtype=float)
        gyro=np.asarray(observation['gyro'],dtype=float)
        if q.shape!=(29,) or dq.shape!=(29,) or quat.shape!=(4,) or gyro.shape!=(3,):
            raise ValueError('Expected 29 q/dq, quaternion wxyz, body-frame gyro')
        if not all(np.isfinite(a).all() for a in (q,dq,quat,gyro)):
            raise ValueError('Nonfinite observation')
        self.calls+=1
        t=(self.calls-1)*DT
        if self.initial is None:self.initial=q.copy();self.last=q.copy()
        target=choreography(0 if self.neutral else t)
        lower=self.balance.update(q,dq,quat,gyro)
        target[:12]=lower[:12]
        heading=math.atan2(2*(quat[0]*quat[3]+quat[1]*quat[2]),1-2*(quat[2]**2+quat[3]**2))
        target[[2,8]]+=np.clip(.45*heading,-.25,.25)
        alpha=smooth(t/2.5)
        target=(1-alpha)*self.initial+alpha*target
        # The deployed controller also refuses to dance when started on its side.
        tilt=math.acos(float(np.clip(1-2*(quat[1]**2+quat[2]**2),-1,1)))
        if tilt>.6:self.aborted=True
        if self.aborted:
            return {'q':q.copy(),'dq':np.zeros(29),'kp':np.zeros(29),'kd':np.ones(29)*2,'tau':np.zeros(29)}
        max_delta=np.r_[np.ones(12)*.25,np.ones(3)*.024,np.ones(14)*.038]
        target=self.last+np.clip(target-self.last,-max_delta,max_delta)
        tau=np.zeros(29)
        tau[12:]=np.clip(self.gravity.calculate(q,quat)[12:],-.65*EFFORT[12:],.65*EFFORT[12:])
        # Keep margin in the host-approved PD demand budget at each observation.
        lower_bound=np.maximum(QMIN+.02,q+(-.82*EFFORT+KD*dq-tau)/KP)
        upper_bound=np.minimum(QMAX-.02,q+(.82*EFFORT+KD*dq-tau)/KP)
        if np.any(lower_bound>upper_bound):raise ValueError('No feasible bounded motor command')
        target=np.clip(target,lower_bound,upper_bound)
        self.last=target.copy()
        return {'q':target,'dq':np.zeros(29),'kp':KP.copy(),'kd':KD.copy(),'tau':tau}

_policy=None
def reset():
    global _policy
    if _policy is None:_policy=Policy()
    else:_policy.reset()

def act(observation):
    global _policy
    if _policy is None:reset()
    return _policy.act(observation)
