"""059作者端只读原Ogre FX/25维曲线；不依赖测试模块，不执行游戏。"""
from pathlib import Path
import numpy as np
def buffers(path):
    from drive_effects059 import buffers_from_bytes
    return buffers_from_bytes(Path(path).read_bytes())
def curves(path,key):
    lines=Path(path).read_text('utf8').splitlines();assert lines[0].startswith('IRIS_FX_CURVES 1 ');i=1
    while i<len(lines):
        row=lines[i].split();n,samples=int(row[1]),int(row[2]);duration,peak=float(row[3]),float(row[4]);i+=1;count=n*samples
        if row[0]==key:
            values=np.asarray([[float(v) for v in x.split()] for x in lines[i:i+count]]);assert values.shape==(count,25)
            return values.reshape(n,samples,25),duration,peak
        i+=count
    raise ValueError('effect curve missing: '+key)
