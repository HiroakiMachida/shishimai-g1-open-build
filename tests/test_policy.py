"""Integration checks of control, counterfactual behavior and task causality."""
import sys,json,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import mujoco
from run import setup,observation,evaluate,ROOT
from policy import Policy,DT,EFFORT,QMIN,QMAX,LIMITS

class PolicyContract(unittest.TestCase):
    def test_controller_uses_measured_feedback_and_bounded_commands(self):
        m,d,qa,va=setup()
        a=observation(m,d,qa,va);a['q'][3]=.30;a['q'][9]=.30
        b={k:v.copy() for k,v in a.items()};b['gyro'][1]=.2
        one=Policy();two=Policy()
        for _ in range(150):x=one.act(a);y=two.act(b)
        self.assertGreater(np.linalg.norm(x['q']-y['q']),1e-4)
        for k in ['q','dq','kp','kd','tau']:
            self.assertEqual(x[k].shape,(29,));self.assertTrue(np.isfinite(x[k]).all())
        self.assertTrue((x['q']>=QMIN).all() and (x['q']<=QMAX).all())
        self.assertTrue((np.abs(x['kp']*(x['q']-a['q'])-x['kd']*a['dq'])<=.82*EFFORT+1e-6).all())
    def test_floating_base_and_no_hidden_assistance(self):
        m,d,qa,va=setup()
        self.assertEqual(m.nu,29);self.assertEqual(m.neq,0);self.assertEqual(m.nmocap,0)
        self.assertEqual(m.jnt_type[m.joint('floating_base_joint').id],mujoco.mjtJoint.mjJNT_FREE)
        self.assertTrue((d.xfrc_applied==0).all());self.assertTrue((d.qfrc_applied==0).all())
    def test_bad_observation_and_counterfactual_start(self):
        m,d,qa,va=setup();a=observation(m,d,qa,va)
        a['quat']=np.array([2**-.5,2**-.5,0,0]);c=Policy().act(a)
        self.assertTrue((c['kp']==0).all());self.assertTrue((c['kd']==2).all())
        a['q'][0]=np.nan
        with self.assertRaises(ValueError):Policy().act(a)

def benchmark(seeds=range(1000,1012)):
    rows=[]
    for seed in seeds:
        active=evaluate(seed=seed);neutral=evaluate(seed=seed,neutral=True)
        rows.extend([active,neutral])
        print(f"seed {seed}: dance={active['success']} neutral={neutral['success']} tilt={active['max_pelvis_tilt_deg']:.2f}deg",flush=True)
    pushes=[evaluate(seed=2000+i,push=p) for i,p in enumerate([-20,-10,10,20])]
    report={'definition':'36 s upright; waist yaw span > 0.45 rad and pitch span > 0.12 rad',
       'seed_protocol':'independent uniform joint position perturbations +/-0.003 rad at reset',
       'episodes':rows,'perturbation_episodes':pushes,
       'active_successes':sum(r['success'] for r in rows if not r['neutral']),
       'neutral_successes':sum(r['success'] for r in rows if r['neutral']),
       'nominal_trials':len(rows)//2,'perturbation_successes':sum(r['success'] for r in pushes),
       'official_safety_validation':'separate; these are custom local task checks'}
    (ROOT/'evidence/benchmark.json').write_text(json.dumps(report,indent=2)+'\n')
    # Applied pushes are a stress characterization, not an undisclosed pass gate.
    for r in rows:
        assert r['stood'],r
        assert r['min_joint_limit_margin_rad']>=0,r
        assert r['torque_limit_exceeding_substeps']==0,r
        assert r['policy_calls']==1800,r
        assert np.max(np.array(r['max_observed_pd_demand_nm'])/EFFORT)<=.820001,r
    assert report['active_successes']==report['nominal_trials'],report
    assert report['neutral_successes']==0,report
    print(json.dumps({k:v for k,v in report.items() if k not in ('episodes','perturbation_episodes')},indent=2))

if __name__=='__main__':
    if '--benchmark' in sys.argv:benchmark()
    else:unittest.main()
