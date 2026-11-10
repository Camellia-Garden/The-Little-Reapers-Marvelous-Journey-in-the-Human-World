from pathlib import Path
import csv, html, re

out = Path(__file__).resolve().parents[1] / '文本与数据'
raw = out / '原始数据'
def varint(b, i):
    n=0
    for shift in range(0,70,7):
        if i>=len(b): raise ValueError()
        c=b[i]; i+=1; n |= (c & 127)<<shift
        if c<128: return n,i
    raise ValueError()
def parse(b):
    fields={}; i=0
    while i<len(b):
        tag,i=varint(b,i); key,wire=tag>>3,tag&7
        if not key or key in fields: raise ValueError()
        if wire==0: value,i=varint(b,i)
        elif wire==2:
            n,i=varint(b,i)
            if n>len(b)-i: raise ValueError()
            value=b[i:i+n]; i+=n
        else: raise ValueError()
        fields[key]=value
    return fields
def scan(path, mode):
    b=path.read_bytes(); pos=0; rows=[]
    while True:
        pos=b.find(b'\x12',pos)
        if pos<0: break
        start=pos; pos+=1
        try:
            length,begin=varint(b,pos)
            if length<5 or length>100000 or begin+length>len(b): continue
            fields=parse(b[begin:begin+length])
            if mode=='talk':
                if set(fields)!={1,2,3} or not isinstance(fields[1],int) or not isinstance(fields[3],int): continue
                values=[fields[1],fields[3],fields[2].decode('utf-8')]
            else:
                if set(fields)!={1,2,3,4,5} or not isinstance(fields[1],int): continue
                values=[fields[1]]+[fields[i].decode('utf-8') for i in range(2,6)]
            rows.append([start]+values); pos=begin+length
        except (ValueError,TypeError,UnicodeError,IndexError): continue
    return rows
for mode, pattern, label in [('talk','LanguageTalk__*.bin','剧情台词'),('language','Language__*.bin','游戏文本')]:
    rows=scan(next(raw.glob(pattern)),mode)
    folder=out / label; folder.mkdir(parents=True, exist_ok=True)
    header = ['原文件偏移','文本ID','关联编号','简体中文'] if mode=='talk' else ['原文件偏移','文本ID','简体中文','繁体中文','英文','日文']
    with (folder / (label+'索引.csv')).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f); w.writerow(header); w.writerows(rows)
    with (folder / (label+'简体中文.txt')).open('w',encoding='utf-8') as f:
        for row in rows:
            text=row[3] if mode=='talk' else row[2]
            text=html.unescape(re.sub(r'<[^>]*>','',text)).replace('\r','')
            f.write(f'[{row[1]}] {text}\n')
    print(label, len(rows))
