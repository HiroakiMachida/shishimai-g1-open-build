"""Build an allowlisted, audited public source archive, never a workspace dump."""
from pathlib import Path
import hashlib,json,re,zipfile,shutil

ROOT=Path(__file__).resolve().parent
TOP=['.gitattributes','.gitignore','.dockerignore','README.md','LICENSE',
     'THIRD_PARTY_NOTICES.md','SAFETY_REPORT.md','SENSOR_CONTRACT.md','NEXT_IDEAS.md',
     'build_scene.py','policy.py','run.py','video.py','package.py','finalize.py',
     'run.sh','run.ps1','submit.ps1','submission.json','requirements.txt','requirements-lock.txt',
     'scene.xml','g1-runner.json']
EVIDENCE=['benchmark.json','episode.json','episode.npz','video-check.json','provenance.json','task-summary.json',
          'frame-0000.jpg','frame-0180.jpg','frame-0420.jpg','frame-0690.jpg','frame-0960.jpg']

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    files=[ROOT/p for p in TOP]
    for directory in ['assets','models','vendor','runner','tests']:
        files += [p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
    files += [ROOT/'evidence'/p for p in EVIDENCE]
    files += [p for p in (ROOT/'evidence').glob('container-*/**/*') if p.is_file() and p.suffix in ('.json','.npz','.log','.txt')]
    files=sorted(set(files))
    for path in files:
        assert path.is_file(),f'Missing required public artifact: {path}'
        rel=path.relative_to(ROOT).as_posix()
        assert not any(part in ('.git','.venv','.simenv','.ssh','reference','node_modules') for part in path.relative_to(ROOT).parts)
        assert not path.name.startswith('.env')
        if path.suffix in ('.py','.json','.md','.txt','.ps1','.sh'):
            data=path.read_text(encoding='utf-8-sig',errors='replace')
            assert not re.search(r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|him_pat_[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{32,}',data),f'Secret-shaped content: {rel}'
    dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    archive=dist/'submission.zip'
    inventory=[]
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        for path in files:
            rel=path.relative_to(ROOT).as_posix();payload=path.read_bytes()
            info=zipfile.ZipInfo(rel,date_time=(2026,11,5,0,0,0));info.create_system=3
            info.external_attr=(0o100755 if path.suffix=='.sh' else 0o100644)<<16
            info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,payload)
            inventory.append({'path':rel,'bytes':len(payload),'sha256':sha(path)})
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    shutil.copy2(ROOT/'result.mp4',dist/'result.mp4')
    assert (dist/'result.mp4').stat().st_size<=50*1024**2
    assert archive.stat().st_size+(dist/'result.mp4').stat().st_size<=100*1024**2
    (dist/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    artifacts={'files':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in [archive,dist/'result.mp4']},
        'upload_idempotency_key':'shishimai:'+sha(archive)[:24]+':'+sha(dist/'result.mp4')[:24],
        'inventory_entries':len(files),'secrets_scan':'allowlist and secret-pattern checks passed'}
    (dist/'artifacts.json').write_text(json.dumps(artifacts,indent=2)+'\n')
    print(json.dumps(artifacts,indent=2))
    print('Public ZIP inventory:')
    for row in inventory:print(f"{row['bytes']:>9}  {row['path']}")

if __name__=='__main__':main()
