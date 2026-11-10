from pathlib import Path
from collections import Counter
import csv, json, shutil, sys, traceback

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parents[1]
GAME = ROOT / 'Trainee Death Simulator' / 'Death_Data'
sys.path.insert(0, str(ROOT / '.unpack_tools'))
import UnityPy

def safe(s):
    s = ''.join('_' if c in '<>:"/\\|?*' or ord(c)<32 else c for c in str(s)).strip(' .')[:90]
    return s or '未命名'

files = [GAME / 'resources.assets', GAME / 'globalgamemanagers.assets', GAME / 'sharedassets0.assets']
files += sorted((GAME / 'StreamingAssets' / 'yoo' / 'Main').glob('*.bundle'))
counts, errors, rows = Counter(), [], []
for f in files:
    try:
        env = UnityPy.load(str(f))
        for obj in env.objects:
            typ = obj.type.name
            if typ not in ('Texture2D', 'Sprite', 'TextAsset', 'AudioClip'): continue
            try:
                asset = obj.read(check_read=False)
                name = safe(asset.m_Name)
                base = f'{name}__{obj.path_id}'
                package = f.stem
                if typ in ('Texture2D', 'Sprite'):
                    dest = OUT / ('图片/原始纹理' if typ == 'Texture2D' else '图片/精灵切图') / package / (base + '.png')
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    asset.image.save(dest)
                elif typ == 'TextAsset':
                    b = asset.m_Script
                    if isinstance(b, str): b = b.encode('utf-8', 'surrogateescape')
                    dest = OUT / '文本与数据/原始数据' / (base + '.bin')
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(b)
                    try:
                        s = b.decode('utf-8')
                        if s and sum(c.isprintable() or c in '\r\n\t' for c in s) / len(s) > .95:
                            readable = OUT / '文本与数据/可直接阅读' / (base + '.txt')
                            readable.parent.mkdir(parents=True, exist_ok=True)
                            readable.write_text(s, encoding='utf-8')
                    except UnicodeDecodeError: pass
                else:
                    dest = OUT / '音频/Unity音频' / package
                    dest.mkdir(parents=True, exist_ok=True)
                    samples = asset.samples
                    for n, b in samples.items(): (dest / (base + '__' + safe(n))).write_bytes(b)
                counts[typ] += 1
                rows.append((f.name, typ, asset.m_Name, obj.path_id, str(dest.relative_to(OUT))))
            except Exception as exc:
                errors.append((f.name, typ, str(obj.path_id), repr(exc)))
    except Exception as exc:
        errors.append((f.name, '资源包', '', repr(exc)))
    print(f.name, dict(counts), 'failures', len(errors), flush=True)

for group, pattern, target in [('视频','Video/*.mp4','视频'), ('音频库','*.bank','音频/FMOD音频库')]:
    for src in (GAME / 'StreamingAssets').glob(pattern):
        dest = OUT / target / src.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        counts[group] += 1

log = OUT / '工具与日志'
with (log / '导出索引.csv').open('w', encoding='utf-8-sig', newline='') as f:
    w=csv.writer(f); w.writerow(['来源文件', '资源类型', '原名称', '对象ID', '导出路径']); w.writerows(rows)
with (log / '失败清单.csv').open('w', encoding='utf-8-sig', newline='') as f:
    w=csv.writer(f); w.writerow(['来源文件', '资源类型', '对象ID', '错误']); w.writerows(errors)
(log / '统计.json').write_text(json.dumps(dict(counts), ensure_ascii=False, indent=2), encoding='utf-8')
print('完成', dict(counts), '失败', len(errors), flush=True)
