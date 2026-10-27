"""073：仅移除翻滚两层pFireBall深色Billboard；保留其他层原始chunk和时序。"""
from pathlib import Path
import json,re,struct
from safeio import ROOT,put
from prune_runtime070 import chunks,objects,erase
CONTRACT='IRIS_ROLL_SPHERE_073'
KEY='roll_blast'
REMOVED={'IrisArsenal/Source069/roll_blast/6','IrisArsenal/Source069/roll_blast/10'}

def blocks(text,curves=False):
    # 以原始文本块为单位切分；非目标招式和保留层的浮点行绝不重新序列化。
    lines=text.splitlines(keepends=True);i=1;result=[]
    while i<len(lines):
        row=lines[i].split();size=int(row[1])*int(row[2]) if curves else int(row[2])
        end=i+1+size
        if end>len(lines):raise ValueError('效果表边界不完整')
        result.append((row[0],lines[i:end]));i=end
    return lines[0],result

def plan(root=ROOT):
    root=Path(root);assets=root/'package/IrisArsenal/assets';docpath=root/'docs/eight-effects.json'
    doc=json.loads(docpath.read_text('utf-8-sig'));asset=next(x for x in doc['assets'] if x['key']==KEY);names=asset['materials']
    previous=doc.get('roll_sphere073')
    if previous and previous.get('contract')==CONTRACT:
        if REMOVED&set(names):raise ValueError('073元数据与活动层矛盾')
        return {},previous
    if len(names)!=12 or not REMOVED<=set(names):raise ValueError('073只接受已确认069翻滚12层前驱')
    for name in REMOVED:
        d=doc['materials'][name]
        if d.get('system069')!='pFireBall' or Path(d.get('source069','')).name!='FireBallExp01.nif' or d.get('blend')!='src_alpha one_minus_src_alpha':
            raise ValueError('目标不是已确认的深色火团：'+name)
    keep=[i for i,name in enumerate(names) if name not in REMOVED];kept=[names[i] for i in keep]
    meshpath=assets/'iris_fx_roll_blast.mesh';raw=meshpath.read_bytes();begin=raw.index(b'\n')+1;top=list(chunks(raw,begin,len(raw)))
    if len(top)!=1 or top[0][0]!=0x3000:raise ValueError('未知mesh顶层结构')
    kind,start,end=top[0];subs=list(chunks(raw,start+1,end));submeshes=[x for x in subs if x[0]==0x4000]
    # 此作者只输出独立submesh和bounds；若出现边线/命名表等索引引用，不能盲删后留下错误索引。
    if len(submeshes)!=len(names) or any(x[0] not in (0x4000,0x9000) for x in subs):raise ValueError('未知mesh引用结构')
    payload=[raw[start:start+1]];removed_chunks=[];index=0
    for typ,ss,ee in subs:
        part=raw[ss-6:ee]
        if typ==0x4000:
            actual=raw[ss:raw.index(b'\n',ss)].decode('utf-8')
            if actual!=names[index]:raise ValueError('mesh与CSV材质顺序不一致')
            if index in keep:payload.append(part)
            else:removed_chunks.append(index)
            index+=1
        else:payload.append(part)
    body=b''.join(payload);outmesh=raw[:begin]+struct.pack('<HI',0x3000,len(body)+6)+body
    outputs={meshpath:outmesh}
    for filename,iscurves in [('effects.csv',False),('effect_curves.csv',True)]:
        path=assets/filename;header,allblocks=blocks(path.read_text('utf-8-sig'),iscurves);out=[header];found=False
        for key,lines in allblocks:
            if key!=KEY:out.extend(lines);continue
            if found:raise ValueError('重复翻滚记录')
            found=True;row=lines[0].split()
            if iscurves:
                count,samples=int(row[1]),int(row[2]);assert count==len(names)
                head=re.sub(r'^(\S+\s+)\d+',lambda m:m[1]+str(len(keep)),lines[0],count=1)
                out.append(head)
                for i in keep:out.extend(lines[1+i*samples:1+(i+1)*samples])
            else:
                if int(row[2])!=len(names) or [s.strip() for s in lines[1:]]!=names:raise ValueError('效果表材质不匹配')
                out.append(re.sub(r'^(\S+\s+\S+\s+)\d+',lambda m:m[1]+str(len(keep)),lines[0],count=1))
                out.extend(lines[1+i] for i in keep)
        if not found:raise ValueError('缺少翻滚效果')
        outputs[path]=''.join(out)
    # 仅裁剪这两个私有材质对象；共享纹理、着色器及其他层参数不变。
    material_hits=[]
    for path in assets.glob('*.material'):
        text=path.read_text('utf-8-sig');spans=[]
        for name,ss,ee,body in objects(text):
            if name in REMOVED:spans.append((ss,ee));material_hits.append(name)
        if spans:outputs[path]=erase(text,spans)
    if set(material_hits)!=REMOVED or len(material_hits)!=2:raise ValueError('目标材质声明不唯一或缺失')
    asset['materials']=kept;asset['source_revision']='073'
    for name in REMOVED:doc['materials'].pop(name)
    proof={'contract':CONTRACT,'key':KEY,'source_system':'FireBallExp01.nif / pFireBall','removed_original_layers':removed_chunks,'removed_materials':sorted(REMOVED),'retained_original_layers':keep,'retained_materials':kept,'layers_before':len(names),'layers_after':len(kept),'outer_geometry_materials_and_tracks':'original bytes retained','radius_and_clock':'unchanged R24 and original game-second tracks','bounds':'original conservative bounds retained','scope':'仅翻滚内部深色火团；外层球形主体、闪光及原细火星保持，其他招式/C++/DLL/判定保持'}
    doc['roll_sphere073']=proof;outputs[docpath]=json.dumps(doc,ensure_ascii=False,indent=2)
    return outputs,proof

def apply(root=ROOT):
    outputs,proof=plan(root)
    # 所有结构/目标检查完成后才写；每项仍经既有双备份、编码与中文检查。
    for path,data in outputs.items():put(path,data,'073翻滚去除深色火团','仅移除源pFireBall两层，保留外球原字节/曲线与其他招式')
    return proof

if __name__=='__main__':print(json.dumps(apply(),ensure_ascii=False,indent=2))
