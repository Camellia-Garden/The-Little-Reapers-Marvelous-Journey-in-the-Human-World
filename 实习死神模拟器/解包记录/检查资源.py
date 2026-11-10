from pathlib import Path
from collections import Counter
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.unpack_tools'))
import UnityPy
data = ROOT / 'Trainee Death Simulator' / 'Death_Data'
files = [data / 'resources.assets', data / 'globalgamemanagers.assets', data / 'sharedassets0.assets'] + list((data / 'StreamingAssets' / 'yoo' / 'Main').glob('*.bundle'))
for f in files:
    try:
        env = UnityPy.load(str(f))
        print(f.name, Counter(o.type.name for o in env.objects), flush=True)
        for obj in env.objects:
            if obj.type.name in ('TextAsset', 'AudioClip'):
                try:
                    item = obj.read(check_read=False)
                    print(' ', obj.type.name, obj.path_id, repr(item.m_Name), flush=True)
                except Exception as exc:
                    print(' ', 'ERROR', repr(exc), flush=True)
    except Exception as exc:
        print(f.name, 'ERROR', repr(exc), flush=True)
