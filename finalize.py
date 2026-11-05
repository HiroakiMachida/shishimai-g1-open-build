"""Record exact provenance, decode the video and summarize measured evidence."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess
import imageio_ffmpeg
import numpy as np
import mujoco,onnxruntime,PIL,imageio

ROOT=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name,value):(ROOT/name).write_text(json.dumps(value,indent=2)+'\n')

def main():
    git_result=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,text=True,capture_output=True)
    source_commit=git_result.stdout.strip() if git_result.returncode==0 else json.loads((ROOT/'g1-runner.json').read_text())['repository_commit']
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    result=subprocess.run([ffmpeg,'-hide_banner','-v','error','-i',str(ROOT/'result.mp4'),'-f','null','-'],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    reader=imageio_ffmpeg.read_frames(str(ROOT/'result.mp4'));meta=next(reader);reader.close()
    assert meta['size']==(1280,720) and abs(meta['duration']-36)<.15 and abs(meta['fps']-30)<.01,meta
    check={'decoded_without_errors':True,'duration_seconds':meta['duration'],'resolution':meta['size'],
      'fps':meta['fps'],'codec':meta['codec'],'bytes':(ROOT/'result.mp4').stat().st_size,
      'sha256':sha(ROOT/'result.mp4'),'representative_frames':[0,180,420,690,960],
      'editorial_additions':'titles, progress bar and original synthesized percussion',
      'physical_outcome':'continuous real-time replay of evaluated seed 1000; no outcome editing'}
    write('evidence/video-check.json',check)
    prov={'created_at':datetime.now(timezone.utc).isoformat(),
      'repository_commit':source_commit,
      'g1_builder_kit_revision':'e93c49267a7b6b905c6666c8c70668f8ee7ac397',
      'g1_builder_kit_url':'https://arena.himrobotics.com/policy-contracts/g1-builder-kit-e93c492-v1.zip',
      'g1_builder_kit_zip_sha256':sha(ROOT/'reference/g1-builder-kit.zip') if (ROOT/'reference/g1-builder-kit.zip').exists() else None,
      'menagerie_commit':'8161bba264d7fa7c99ca301e91e7fb44737676ad',
      'nvidia_revision':'b042411fae38ee4d1af9aac82a37a1f8d14d6dd0',
      'balance_sha256':sha(ROOT/'models/balance.onnx'),
      'scene_sha256':sha(ROOT/'scene.xml'),'policy_sha256':sha(ROOT/'policy.py'),
      'versions':{'mujoco':mujoco.__version__,'numpy':np.__version__,'onnxruntime':onnxruntime.__version__,
                  'Pillow':PIL.__version__,'imageio':imageio.__version__},
      'physics_dt':.002,'control_dt':.02,'video_seed':1000,'costume_mass_kg':.45,
      'base_support':'floating pelvis, no external support','compute':'local Windows simulation; local WSL Docker builds; no paid cloud resources',
      'original_assets':{p.name:sha(p) for p in [ROOT/'assets/karakusa.png',ROOT/'assets/cloak.obj',ROOT/'assets/fonts/ZenOldMincho-Regular.ttf']}}
    assert prov['balance_sha256']=='f645da599d4ca3d29ed273c8f4712620bb680d34977469ca3aeabe5bb9631c18'
    write('evidence/provenance.json',prov)
    b=json.loads((ROOT/'evidence/benchmark.json').read_text());active=[e for e in b['episodes'] if not e['neutral']]
    summary={'active':f"{b['active_successes']}/{b['nominal_trials']}",'neutral':f"{b['neutral_successes']}/{b['nominal_trials']}",
      'lateral_push':f"{b['perturbation_successes']}/4",'worst_nominal_tilt_deg':max(e['max_pelvis_tilt_deg'] for e in active),
      'minimum_nominal_joint_margin_rad':min(e['min_joint_limit_margin_rad'] for e in active),
      'maximum_nominal_displacement_m':max(e['pelvis_displacement_m'] for e in active)}
    write('evidence/task-summary.json',summary)
    print(json.dumps({'video':check,'task':summary},indent=2))

if __name__=='__main__':main()
