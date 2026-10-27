"""070只裁剪运行包无引用项；开发源/验证数据与运行资产分别保留，不编译。"""
from pathlib import Path
import collections,hashlib,json,re,struct
import kenshi_mod_writer as fcs
from safeio import ROOT,put,retire
EXTERNAL_PROGRAMS={'Basic_Texture_VP','Basic_Coloured_Texture_VP'}
PROOFS=ROOT/'docs/pose-proofs'

def objects(text):
    # 按完整顶层对象和配平括号裁剪，不能按空行或材质名字前缀截断；跳过字符串/注释中的括号。
    for match in re.finditer(r'(?m)^[ \t]*(material|vertex_program|fragment_program)\s+(?:"([^"\n]+)"|([^\s:{]+))',text):
        start=text.index('{',match.end());depth=0
        for token in re.finditer(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|[{}]',text[start:]):
            if token[0]=='{':depth+=1
            elif token[0]=='}':
                depth-=1
                if depth==0:
                    end=start+token.end();yield match[2]or match[3],match.start(),end,text[match.start():end];break
        else:raise ValueError('资源对象括号未闭合：'+match[0])

def chunks(data,start,end):
    while start<end:
        kind,length=struct.unpack_from('<HI',data,start)
        if length<6 or start+length>end:raise ValueError('非法mesh chunk')
        yield kind,start+6,start+length;start+=length
    if start!=end:raise ValueError('mesh chunk边界不完整')

def mesh_materials(path):
    # 只读取submesh默认名，与32/48/52字节顶点格式无关；这些默认材质也必须保留，不能只看CSV覆盖名。
    data=path.read_bytes();names=set()
    for kind,start,end in chunks(data,data.index(b'\n')+1,len(data)):
        if kind!=0x3000:raise ValueError('非本项目mesh序列格式')
        for sub,ss,ee in chunks(data,start+1,end):
            if sub==0x4000:names.add(data[ss:data.index(b'\n',ss)].decode('utf8'))
    return names

def fcs_files(path):
    data=path.read_bytes();offset=fcs.find_records_start(data);names=set();prefix='./mods/IrisArsenal/'
    while offset<len(data):
        record=fcs.read_record(data,offset,len(data));offset=record['end']
        for section in record['sections']:
            for field,kind,value in section:
                if kind in ('filename','string'):
                    name=fcs.Reader(value).string(0)[0]
                    if name.startswith(prefix):
                        rel=name[len(prefix):].replace('\\','/')
                        if '..' in Path(rel).parts or ':' in rel:raise ValueError('FCS路径越界')
                        names.add(rel)
    return names

def erase(text,spans):
    for start,end in sorted(spans,reverse=True):text=text[:start]+text[end:]
    return text

def plan(root=ROOT):
    package=root/'package/IrisArsenal';assets=package/'assets';materials=collections.defaultdict(list);programs={};sources={}
    for suffix,catalog in [('material',materials),('program',programs)]:
        for path in sorted(assets.glob('*.'+suffix)):
            text=path.read_text('utf-8-sig');sources[path]=text
            for name,start,end,body in objects(text):
                record=(path,start,end,body)
                if suffix=='material':catalog[name].append(record)
                else:
                    if name in catalog:raise ValueError('重复GPU程序声明：'+name)
                    catalog[name]=record
    roots={'IrisArsenal/Debug','IrisArsenal/Eight/WeaponTrail'}
    for path in assets.glob('*.mesh'):roots.update(mesh_materials(path))
    roots.update(line for line in (assets/'effects.csv').read_text('utf8').splitlines()if line.startswith('IrisArsenal/'))
    roots.update(line.split()[1]for line in (assets/'drill.csv').read_text('utf8').splitlines()[10:])
    missing=roots-materials.keys()
    if missing:raise ValueError('运行/mesh默认材质缺失：'+str(sorted(missing)))
    live_programs=set();textures=set();live_objects=[]
    for name in roots:
        # 现有重复d731声明depth_write不同，顺序语义尚未唯一确认。两个原块一起保留，不在清理中改渲染策略。
        for path,start,end,body in materials[name]:
            live_objects.append({'name':name,'file':path.name,'sha256':hashlib.sha256(body.encode('utf8')).hexdigest()})
            live_programs.update(re.findall(r'(?:vertex|fragment)_program_ref\s+(\S+)',body));textures.update(re.findall(r'\btexture\s+(\S+)',body))
    external=live_programs-programs.keys()
    if external-EXTERNAL_PROGRAMS:raise ValueError('未知外部GPU程序：'+str(external-EXTERNAL_PROGRAMS))
    shader_names=set()
    for name in live_programs&programs.keys():shader_names.update(re.findall(r'\bsource\s+(\S+)',programs[name][3]))
    explicit=fcs_files(package/'IrisArsenal.mod')
    for name in explicit:
        if not (package/name).is_file():raise ValueError('FCS构件缺失：'+name)
    files={assets/name for name in textures|shader_names}|{package/name for name in explicit}
    for path in files:
        if path.parent!=assets and not path.is_relative_to(package/'icons'):raise ValueError('资源引用超出已知目录：'+str(path))
        if not path.is_file():raise ValueError('资源引用缺失：'+str(path))
    updates={};deleted=[];material_count=0;program_count=0
    for path,text in sources.items():
        blocks=list(objects(text));dead=[(start,end)for name,start,end,body in blocks if name not in (roots if path.suffix=='.material'else live_programs)]
        if not dead:continue
        if path.suffix=='.material':material_count+=len(dead)
        else:program_count+=len(dead)
        if len(dead)==len(blocks):deleted.append(path)
        else:updates[path]=erase(text,dead)
    for path in assets.iterdir():
        if path.suffix.lower()in('.png','.dds')and path not in files:deleted.append(path)
    # 只删除本轮已证明没有入口/调用的两段旧能量函数；其他HLSL函数及共享定义逐字保持。
    hlsl=assets/'iris_eight.hlsl';text=hlsl.read_text('utf8');spans=[];functions=[]
    for name,program in [('iris_energy_vp','IrisEnergyVP'),('iris_energy_fp','IrisEnergyFP')]:
        match=re.search(r'(?m)^\w+ '+name+r'\([^\n]*',text)
        if program in live_programs or not match:continue
        start=text.index('{',match.start());depth=0
        for index in range(start,len(text)):
            if text[index]=='{':depth+=1
            elif text[index]=='}':
                depth-=1
                if not depth:break
        end=index+1
        outside=text[:match.start()]+text[end:]
        if re.search(r'\b'+name+r'\b',outside):raise ValueError('旧函数仍有调用：'+name)
        spans.append((match.start(),end));functions.append(name)
    if spans:
        changed=erase(text,spans)
        changed=changed.replace('// 光炮金环和枪口离子光只使用自有三维几何；长度/相位来自实例游戏时钟，不用墙钟。','// 070：旧能量入口已被059源光流取代；仅裁剪无调用函数，保留所有有效入口。')
        updates[hlsl]=changed
    proofs=sorted(assets.glob('*weapon_proof*.csv'))
    report={'material_definitions_removed':material_count,'program_definitions_removed':program_count,'hlsl_functions_removed':functions,'retired_files':[p.relative_to(package).as_posix()for p in deleted],'proofs_to_developer':[p.name for p in proofs],'live_objects':sorted(live_objects,key=lambda x:(x['file'],x['name'])),'live_programs':sorted(live_programs),'external_programs':sorted(external),'shader_sources':sorted(shader_names),'fcs_files':sorted(explicit),'duplicates_retained':{n:[p.name for p,s,e,b in rows]for n,rows in materials.items()if len(rows)>1},'scope':'不修改C++/H/DLL/模型/图集/动作/FCS/判定，完整重建依赖和诊断模式保留'}
    return updates,sorted(set(deleted)),proofs,report

def main():
    updates,deleted,proofs,report=plan()
    # 先完成全部图检查，再改写。证明表先原字节复制到开发目录，校验后才从运行包精确移除。
    for path in proofs:
        dest=PROOFS/path.name;data=path.read_bytes();put(dest,data,'开发姿势证明表','保留离线交叉验证；不让运行包携带未被游戏读取的CSV')
        if dest.read_bytes()!=data:raise ValueError('证明表迁移校验失败')
    for path,text in updates.items():put(path,text,'运行资源裁剪','按实际材质/程序引用图裁剪；所有有效对象正文保持')
    for path in deleted+proofs:retire(path,'070完整根集无引用，或原字节证明表已迁至docs/pose-proofs；先双备份')
    # 重跑应完全幂等；这里检查实际结果，而非只相信计划。
    again=plan()
    if again[0]or again[1]or again[2]:raise ValueError('070清理非幂等')
    if report['live_objects']!=again[3]['live_objects']:raise ValueError('有效材质正文发生变化')
    put(ROOT/'docs/cleanup-runtime070.json',json.dumps(report,ensure_ascii=False,indent=2),'070清理依据','记录有效对象正文哈希、精确退役项与开发证明表；不以年龄/文件名前缀删源作者')
    print('CLEANUP070',report['material_definitions_removed'],'materials',report['program_definitions_removed'],'programs',len(deleted),'files',len(proofs),'developer proofs')
    return report
if __name__=='__main__':main()
