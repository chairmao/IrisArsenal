"""049原网格库存展示：仅UI沿长度展开，战斗网格/占格/握点/长度均不变。"""
from io import BytesIO
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from safeio import ROOT,put
NAMES=('1-IrisArsenal.mod.52293-rebirth.mod.png',)

def main():
    import author_prototype as a
    meshes,_=a.read_nif(a.SOURCE/'Meshes/SW/Iris/2.nif')
    points=[(np.asarray(x['vertices'])@x['matrix'][:3,:3].T+x['matrix'][:3,3])@a.C.T@a.R.T*a.SCALE for x in meshes]
    allp=np.concatenate(points);lo=allp[:,[1,0]].min(0);hi=allp[:,[1,0]].max(0);center=(lo+hi)*.5
    # 原生固定武器相机只能整体放大，会裁掉粗锤头。库存示意图单独沿长度展开到宽槽，
    # 使用原网格/纹理投影；这是UI排版适配，不是拉长实际武器或改变装备占格。
    logical=Image.new('RGBA',(1000,200));draw=ImageDraw.Draw(logical);triangles=[]
    scale=np.array([960,176])/(hi-lo)
    for mesh,p in zip(meshes,points):
        texname=a.texture(mesh['textures'][0]);tex=Image.open(a.TEXTURES[texname]).convert('RGB')
        xy=(p[:,[1,0]]-center)*scale*[1,-1]+[500,100]
        for tri in mesh['triangles']:
            uv=np.asarray(mesh['uv'])[tri].mean(0)%1;rgb=tex.getpixel((int(uv[0]*(tex.width-1)),int(uv[1]*(tex.height-1))))
            triangles.append((float(p[tri,2].mean()),[tuple(xy[i]) for i in tri],(*rgb,255)))
    for _,xy,rgba in sorted(triangles,key=lambda row:row[0]):draw.polygon(xy,fill=rgba)
    output=BytesIO();logical.resize((512,128),Image.Resampling.LANCZOS).save(output,format='PNG');data=output.getvalue()
    for name in NAMES:put(ROOT/'package/IrisArsenal/icons'/name,data,'库存预制展示图','原2.nif纹理投影，UI纵长独立排版；实际战斗模型与10x2占格不变')
    return data

def install(game,backup_bases,guard):
    # 只覆盖已实际生成过的本武器材质键；未知材质仍走原生相机，不触碰其他图标。
    import datetime
    from update_mod import no_reparse,require,replace_bytes
    require(len(backup_bases)==2,'图标写入必须有两份外部备份')
    stamp='IrisArsenal-Icon049-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');rows=[]
    for name in NAMES:
        target=no_reparse(Path(game)/'data/icons'/name);source=no_reparse(ROOT/'package/IrisArsenal/icons'/name);data=source.read_bytes();guard()
        if target.exists() and target.read_bytes()==data:continue
        backups=[]
        if target.exists():
            old=target.read_bytes()
            for base in backup_bases:
                dest=no_reparse(Path(base)/stamp/target.drive.rstrip(':')/Path(*target.parts[1:]));dest.parent.mkdir(parents=True,exist_ok=True)
                with dest.open('xb') as f:f.write(old)
                assert dest.read_bytes()==old;backups.append(str(dest))
        guard();no_reparse(target)
        # 缓存与运行部署共用原子写/回读，拒绝目录联接，避免写到其他mod或半张PNG。
        replace_bytes(target,data)
        assert target.read_bytes()==data;rows.append({'file':str(target),'backups':backups})
    return rows
if __name__=='__main__':main()
