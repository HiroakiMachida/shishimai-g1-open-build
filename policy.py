"""Shishimai choreography + credited NVIDIA lower-body balance inference.

Only joint/IMU observations enter act(). No world pose, contact oracle or mocap.
The lion head is a lightweight torso-mounted costume, not a manipulated object.
"""
from pathlib import Path
import math,json
import numpy as np
from vendor.him.balance_policy import BalancePolicy
from vendor.him.hardware_constants import G1_29_JOINT_NAMES

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
    """Slow, bounded 29-joint offsets; standing balance controls the legs."""
    q=np.zeros(29)
    # Raised forearms frame the lion without claiming a physical grasp.
    q[15:22]=[-.35,.28,0,1.15,0,0,0]
    q[22:29]=[-.35,-.28,0,1.15,0,0,0]
    bow=window(t,4,10,1.5)*(.5-.5*math.cos(2*math.pi*(t-4)/6))
    gaze=window(t,11,19,1.2)*math.sin(2*math.pi*(t-11)/8)
    pulse=window(t,20,29,1.0)*math.sin(2*math.pi*(t-20)/2.3)
    finale=window(t,30,35,1.4)
    q[12]=.35*gaze+.11*pulse
    q[13]=.025*pulse
    q[14]=.19*bow+.055*pulse+.10*finale
    q[15]+=-.18*bow-.14*pulse-.22*finale
    q[22]+=-.18*bow-.14*pulse-.22*finale
    q[16]+=.10*pulse+.24*finale
    q[23]+=-.10*pulse-.24*finale
    q[18]+=.12*bow+.10*pulse
    q[25]+=.12*bow+.10*pulse
    q[19]=.10*gaze
    q[26]=-.10*gaze
    return q

def phase(t):
    for end,name in [(4,'Awakening'),(10,'Rei / greeting bow'),(19,'Mie / left and right'),
                     (29,'Mai / rhythmic head shake'),(35,'Final blessing'),(1000,'Quiet stand')]:
        if t<end:return name

class Policy:
    def __init__(self,neutral=False):
        self.balance=BalancePolicy(str(ROOT/'models/balance.onnx'))
        self.balance.warmup()
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
        max_delta=np.r_[np.ones(12)*.25,np.ones(3)*.018,np.ones(14)*.024]
        target=self.last+np.clip(target-self.last,-max_delta,max_delta)
        # Keep margin in the host-approved PD demand budget at each observation.
        lower_bound=np.maximum(QMIN+.02,q+(-.82*EFFORT+KD*dq)/KP)
        upper_bound=np.minimum(QMAX-.02,q+(.82*EFFORT+KD*dq)/KP)
        if np.any(lower_bound>upper_bound):raise ValueError('No feasible bounded motor command')
        target=np.clip(target,lower_bound,upper_bound)
        self.last=target.copy()
        return {'q':target,'dq':np.zeros(29),'kp':KP.copy(),'kd':KD.copy(),'tau':np.zeros(29)}

_policy=None
def reset():
    global _policy
    if _policy is None:_policy=Policy()
    else:_policy.reset()

def act(observation):
    global _policy
    if _policy is None:reset()
    return _policy.act(observation)
