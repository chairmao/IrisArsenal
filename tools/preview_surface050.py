"""050真实Ogre人体/锤体深度预览；诊断灰模，不生成或替换产品纹理。"""
from pathlib import Path
from io import BytesIO
import json,math,numpy as np
from PIL import Image,ImageDraw
from safeio import ROOT,put
from scene_geometry import mesh,skin,world_weapon,actual_frames
A=ROOT/'package/IrisArsenal/assets'
def render(objects,yaw=90,elev=8,size=(640,640),origin=(0,10,0),span=34):
    yaw=math.radians(yaw);elev=math.radians(elev);right=np.array([math.cos(yaw),0,-math.sin(yaw)]);view=np.array([math.sin(yaw)*math.cos(elev),math.sin(elev),math.cos(yaw)*math.cos(elev)]);up=np.cross(view,right)
    transform=np.array([right,up,view]);W,H=size;scale=min(W,H)/span;rgb=np.full((H,W,3),[30,33,39],dtype=float);depth=np.full((H,W),-np.inf)
    for parts,color in objects:
        for part in parts:
            point=part['p'];p=(point-origin)@transform.T;p[:,:2]=p[:,:2]*[scale,-scale]+[W/2,H/2]
            for tri in part['tri']:
                xyz=p[tri];lo=np.maximum([0,0],np.floor(xyz[:,:2].min(0)).astype(int));hi=np.minimum([W-1,H-1],np.ceil(xyz[:,:2].max(0)).astype(int))
                if np.any(hi<lo):continue
                x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);a,b,c=xyz;det=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                if abs(det)<1e-8:continue
                u=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/det;w=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/det;z=1-u-w;d=u*a[2]+w*b[2]+z*c[2]
                sl=(slice(lo[1],hi[1]+1),slice(lo[0],hi[0]+1));mask=(u>=0)&(w>=0)&(z>=0)&(d>depth[sl]);normal=np.cross(point[tri[1]]-point[tri[0]],point[tri[2]]-point[tri[0]]);normal/=max(1e-9,np.linalg.norm(normal));lighting=.3+.7*abs(normal@np.array([.3,.8,.52]))
                rgb[sl][mask]=np.array(color)*lighting;depth[sl][mask]=d[mask]
    return Image.fromarray(np.clip(rgb,0,255).astype('uint8'))

def preview(key='drive',sex='female',label='surface050',path=None):
    spec=next(x for x in json.loads((ROOT/'docs/eight-moves.json').read_text('utf8'))['moves'] if x['key']==key)
    ids,world,bones=actual_frames(path or A/f'iris_action_{key}_{sex}.skeleton',spec);body=mesh(Path('D:/steam/steamapps/common/Kenshi/data/character/meshes/human')/f'human_{sex}.mesh');weapon=mesh(A/'iris_weapon.mesh');times=[1.5,1.8,2.3,2.6]
    sheet=Image.new('RGB',(4*480,3*500))
    for j,t in enumerate(times):
        k=round(t/spec['duration']*(spec['frames']-1));pose=world[k];root=np.array(pose[ids['Bip01']][0]);pbody=skin(body,bones,pose);pweapon=world_weapon(weapon,pose,ids)
        for row,yaw in enumerate([90,0,-45]):
            im=render([(pbody,[210,215,225]),(pweapon,[70,180,205])],yaw=yaw,size=(480,480),origin=root+[0,10,0],span=30)
            ImageDraw.Draw(im).text((12,12),f'{label} {key} {sex} / {t:.2f}s / yaw {yaw}',fill='white');sheet.paste(im,(j*480,row*500))
    dest=ROOT/'docs/previews050'/f'{label}-{key}-{sex}.jpg';buffer=BytesIO();sheet.save(buffer,format='JPEG',quality=90);put(dest,buffer.getvalue(),'真实人体/锤体CPU蒙皮预览','原生男女身体真实网格、真实骨权、序列化动作、实际持械模型；非游戏截图');return sheet
if __name__=='__main__':
    for key in ('drive','electro_cannon'):
        for sex in ('male','female'):preview(key,sex)
