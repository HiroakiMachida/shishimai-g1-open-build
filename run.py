"""Evaluate the real actuator-driven episode, then render those same states."""
from pathlib import Path
import argparse,json,math
import mujoco
import numpy as np
from policy import Policy,DT,DURATION,EFFORT,phase
from vendor.him.hardware_constants import G1_29_JOINT_NAMES

ROOT=Path(__file__).resolve().parent

def setup(seed=0,noise=True):
    model=mujoco.MjModel.from_xml_path(str(ROOT/'scene.xml'))
    data=mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model,data,model.key('stand').id)
    joints=np.array([model.joint(n+'_joint').id for n in G1_29_JOINT_NAMES])
    qa=model.jnt_qposadr[joints];va=model.jnt_dofadr[joints]
    # Entry is the public model's standing keyframe, not a solved dance pose.
    if noise:
        rng=np.random.default_rng(seed)
        data.qpos[qa]+=rng.uniform(-.003,.003,29)
    mujoco.mj_forward(model,data)
    return model,data,qa,va

def observation(model,data,qa,va):
    gyro=model.sensor('imu-pelvis-angular-velocity')
    return {'q':data.qpos[qa].copy(),'dq':data.qvel[va].copy(),
            'quat':data.qpos[3:7].copy(),'gyro':data.sensordata[int(gyro.adr[0]):int(gyro.adr[0])+3].copy()}

def evaluate(seed=0,neutral=False,seconds=DURATION,record=False,push=0):
    model,data,qa,va=setup(seed)
    policy=Policy(neutral=neutral)
    frames=[];times=[];tilts=[];heights=[];yaws=[];pitches=[];contacts=[];speeds=[];torques=[]
    hip=[];traces=[];saturated=0;joint_margin=100.;max_cmdstep=0.;last=None
    arms=[];hands=[]
    peak_torque=np.zeros(29);peak_speed=np.zeros(29);peak_demand=np.zeros(29)
    torso=model.body('torso_link').id
    floor=model.geom('safety_floor').id
    for step in range(round(seconds/DT)):
        obs=observation(model,data,qa,va)
        command=policy.act(obs)
        target=command['q']
        peak_demand=np.maximum(peak_demand,np.abs(command['kp']*(target-obs['q'])-command['kd']*obs['dq']+command['tau']))
        if last is not None:max_cmdstep=max(max_cmdstep,float(np.max(np.abs(target-last))))
        last=target.copy()
        # Position actuators implement the same PD law as the robot runner.
        model.actuator_gainprm[:,0]=command['kp']
        model.actuator_biasprm[:,0]=command['tau']
        model.actuator_biasprm[:,1]=-command['kp']
        model.actuator_biasprm[:,2]=-command['kd']
        data.ctrl[:]=target
        for k in range(10):
            if push and 12<=data.time<12.12:data.xfrc_applied[model.body('pelvis').id,:3]=[0,push,0]
            else:data.xfrc_applied[:]=0
            mujoco.mj_step(model,data)
            torque=np.abs(data.qfrc_actuator[va])
            peak_torque=np.maximum(peak_torque,torque)
            peak_speed=np.maximum(peak_speed,np.abs(data.qvel[va]))
            saturated+=int(np.any(torque>EFFORT+.01))
            margin=np.minimum(data.qpos[qa]-model.jnt_range[1:,0],model.jnt_range[1:,1]-data.qpos[qa])
            joint_margin=min(joint_margin,float(np.min(margin)))
        tilt=math.acos(float(np.clip(1-2*(data.qpos[4]**2+data.qpos[5]**2),-1,1)))
        mat=data.xmat[torso].reshape(3,3)
        yaw=float(data.qpos[qa[12]]);pitch=float(data.qpos[qa[14]])
        onfloor=sum(c.geom1==floor or c.geom2==floor for c in data.contact)
        tilts.append(tilt);heights.append(float(data.qpos[2]));yaws.append(yaw);pitches.append(pitch)
        contacts.append(onfloor);speeds.append(float(np.max(np.abs(data.qvel[va]))));torques.append(torque.tolist())
        arms.append(data.qpos[qa[15:]].copy())
        hand_points=[]
        for side in ('left','right'):
            body=model.body(side+'_wrist_yaw_link').id
            point=data.xpos[body]+data.xmat[body].reshape(3,3)@np.array([.078,0,0])
            hand_points.append(point-data.qpos[:3])
        hands.append(hand_points)
        hip.append(data.qpos[:3].tolist())
        margin=np.minimum(data.qpos[qa]-model.jnt_range[1:,0],model.jnt_range[1:,1]-data.qpos[qa])
        joint_margin=min(joint_margin,float(np.min(margin)))
        traces.append([float(data.time),*data.qpos[qa].tolist(),*target.tolist(),tilt,float(data.qpos[2]),yaw,pitch])
        if record:frames.append(data.qpos.copy());times.append(float(data.time))
        if not np.isfinite(data.qpos).all() or data.qpos[2]<.38 or tilt>.9:break
    duration=float(data.time)
    yaw_span=float(np.ptp(np.unwrap(yaws)));pitch_span=float(np.ptp(pitches))
    stood=duration>=seconds-.03 and min(heights)>.55 and max(tilts)<.4
    hand_span=np.ptp(hands,axis=0)
    arm_span=np.ptp(arms,axis=0)
    danced=yaw_span>1.57 and pitch_span>.30 and min(arm_span[0],arm_span[7])>1.57 and min(hand_span[:,2])>.65
    result={'seed':seed,'neutral':neutral,'requested_seconds':seconds,'simulated_seconds':duration,
      'success':bool(stood and danced),'stood':bool(stood),'dance_completed':bool(danced),
      'policy_calls':policy.calls,'max_pelvis_tilt_deg':math.degrees(max(tilts)),
      'min_pelvis_height_m':min(heights),'torso_yaw_span_deg':math.degrees(yaw_span),
      'torso_pitch_span_deg':math.degrees(pitch_span),'max_joint_speed_rad_s':float(np.max(peak_speed)),
      'min_joint_limit_margin_rad':joint_margin,'max_command_step_rad':max_cmdstep,
      'max_torque_nm':peak_torque.tolist(),'max_observed_pd_demand_nm':peak_demand.tolist(),
      'max_joint_speed_by_joint_rad_s':peak_speed.tolist(),'torque_limit_exceeding_substeps':saturated,
      'floor_contact_control_steps':sum(c>0 for c in contacts),'control_steps':len(contacts),
      'pelvis_displacement_m':float(np.linalg.norm(np.array(hip[-1])[:2]-np.array(hip[0])[:2])),
      'arm_joint_span_deg':np.rad2deg(np.ptp(arms,axis=0)).tolist(),
      'hand_xyz_span_m':np.ptp(hands,axis=0).tolist(),
      'task_definition':'36 s upright; waist yaw >90 deg, pitch >17 deg, both shoulder-pitch spans >90 deg, both hand vertical spans >0.65 m',
      'push_newtons':push,'base_support':'free-standing, unassisted','costume_mass_kg':.45,
      'controller':'scripted upper body + pretrained NVIDIA balance + analytical waist/arm gravity compensation; no new training',
      'official_container_safety_pass':False,'hardware_tested':False}
    if record:
        np.savez_compressed(ROOT/'evidence/episode.npz',qpos=frames,times=times,traces=traces)
    return result

def render(output='result.mp4',width=1920,height=1080):
    from video_v2 import render_episode
    render_episode(ROOT/output,width,height)

def main():
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=1008)
    p.add_argument('--seconds',type=float,default=DURATION);p.add_argument('--neutral',action='store_true')
    p.add_argument('--render',action='store_true');p.add_argument('--render-only',action='store_true')
    p.add_argument('--width',type=int,default=1920);p.add_argument('--height',type=int,default=1080)
    p.add_argument('--output',default='result.mp4');args=p.parse_args()
    if not args.render_only:
        r=evaluate(args.seed,args.neutral,args.seconds,record=args.render)
        print(json.dumps(r,indent=2));(ROOT/'evidence/episode.json').write_text(json.dumps(r,indent=2)+'\n')
        if args.render and not r['success']:raise SystemExit('Refusing to render an unsuccessful demonstration episode.')
    if args.render or args.render_only:render(args.output,args.width,args.height)

if __name__=='__main__':main()
