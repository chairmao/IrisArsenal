"""050只读Ogre网格/原生蒙皮；用于作者和离线预览，不修改游戏或源资料。
格式依据本机OgreMeshFileFormat.h的GEOMETRY/SUBMESH_BONE_ASSIGNMENT；逐块长度严格核验。
"""
from pathlib import Path
import struct,numpy as np
import port_math as m
def chunks(b,start,end):
    while start<end:
        kind,n=struct.unpack_from('<HI',b,start);assert n>=6 and start+n<=end
        yield kind,start+6,start+n;start+=n
    assert start==end
def mesh(path):
    b=Path(path).read_bytes();version=b[2:b.index(b'\n')].decode();assert version in ('[MeshSerializer_v1.41]','[MeshSerializer_v1.100]');result=[]
    for kind,s,e in chunks(b,b.index(b'\n')+1,len(b)):
        if kind!=0x3000:continue
        for kind,ss,ee in chunks(b,s+1,e):
            if kind!=0x4000:continue
            nl=b.index(b'\n',ss);name=b[ss:nl].decode();shared,n,wide=struct.unpack_from('<?I?',b,nl+1);assert not shared
            offset=nl+7;tri=np.frombuffer(b, '<u4' if wide else '<u2',n,offset).reshape(-1,3).copy();offset+=n*(4 if wide else 2);weights=[];buffers={};elements=[]
            for typ,start,end in chunks(b,offset,ee):
                if typ==0x4100:weights.append(struct.unpack_from('<IHf',b,start))
                if typ!=0x5000:continue
                count=struct.unpack_from('<I',b,start)[0]
                for typ,x,y in chunks(b,start+4,end):
                    if typ==0x5100:
                        for typ,u,z in chunks(b,x,y):assert typ==0x5110;elements.append(struct.unpack_from('<5H',b,u))
                    if typ==0x5200:
                        bind,stride=struct.unpack_from('<HH',b,x)
                        for typ,u,z in chunks(b,x+4,y):assert typ==0x5210 and z-u==count*stride;buffers[bind]=(b[u:z],stride)
            source,kind,semantic,offset,index=next(el for el in elements if el[2]==1);assert kind==2
            raw,stride=buffers[source];points=np.ndarray((count,3),dtype='<f4',buffer=raw,offset=offset,strides=(stride,4)).copy()
            result.append({'name':name,'p':points,'tri':tri,'weights':np.asarray(weights)})
    assert result;return result

def rotation(q):
    return np.asarray([m.rotate(q,np.eye(3)[i]) for i in range(3)]).T

def skin(parts,bones,pose):
    rest=m.world(bones,[b['orientation'] for b in bones]);result=[]
    for part in parts:
        p=part['p'];q=np.zeros_like(p,dtype=float);total=np.zeros(len(p))
        for bone in np.unique(part['weights'][:,1]).astype(int):
            rows=part['weights'][part['weights'][:,1]==bone];ids=rows[:,0].astype(int);w=rows[:,2]
            rb=rotation(rest[bone][1]);rt=rotation(pose[bone][1]);local=(p[ids]-rest[bone][0])@rb;target=local@rt.T+pose[bone][0]
            np.add.at(q,ids,target*w[:,None]);np.add.at(total,ids,w)
        assert np.max(abs(total-1))<.001
        result.append({**part,'p':q/total[:,None]})
    return result

def world_weapon(parts,pose,ids):
    point,q=pose[ids['Bip01 Prop2']];rot=rotation(q)
    return [{**part,'p':part['p']@rot.T+point} for part in parts]


def actual_frames(path,spec):
    bones,L,tracks=__import__('verify_prototype').skeleton(path,spec['animation']);ids={b['name']:b['id'] for b in bones};result=[]
    for k in range(spec['frames']):
        world=[]
        for bone in bones:
            row=tracks[bone['id']][k] if bone['id'] in tracks else (0,0,0,0,1,0,0,0);q=m.qmul(bone['orientation'],(row[4],*row[1:4]));p=m.vadd(bone['position'],row[5:]);parent=bone['parent']
            if parent>=0:pp,pq=world[parent];p=m.vadd(pp,m.rotate(pq,p));q=m.qmul(pq,q)
            world.append((p,q))
        result.append(world)
    return ids,result,bones

