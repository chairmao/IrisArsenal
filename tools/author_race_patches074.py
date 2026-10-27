"""074两个独立种族兼容补丁：只追加现有Iris动画集引用，不复制/重定向动画，不改原MOD。"""
from pathlib import Path
import hashlib,json,struct
import kenshi_mod_writer as fcs
from safeio import ROOT,put

GAME=Path('D:/steam/steamapps/common/Kenshi')
PATCHES=(
 ('IrisArsenal_IKEMEN_Patch','ep_ikemen_Animation_Patch_My','IKEMEN',1),
 ('IrisArsenal_EndPoem_Patch','End Poem MC_My','End Poem MC',97),
)
ANIMATIONS=tuple(str(i)+'-IrisArsenal.mod' for i in range(30,40))

def records(raw):
    # 完整消费现有17格式；有不识别的记录或尾部时停止，避免漏掉种族后声称全部覆盖。
    assert fcs.u32(raw,0)==17
    pos=fcs.find_records_start(raw);out=[]
    while pos<len(raw):
        row=fcs.read_record(raw,pos,len(raw));assert row is not None
        out.append(row);pos=row['end']
    assert pos==len(raw)
    assert len({r['key'] for r in out})==len(out)
    return out

def build(source,iris_raw,patch_name,expected_count):
    # 身份严格取玩家指定补丁里的RACE记录；不猜种族名称，不按机器人标签改医疗或武器资格。
    source=Path(source);raw=source.read_bytes();races=[r for r in records(raw) if r['type']==7]
    assert len(races)==expected_count,(str(source),len(races),expected_count)
    iris={r['key']:r for r in records(iris_raw)}
    assert all(key in iris and iris[key]['type']==112 for key in ANIMATIONS)
    category=fcs.w_str('animation files')+fcs.put(len(ANIMATIONS))
    category+=b''.join(fcs.w_str(key)+struct.pack('<3i',0,0,0) for key in ANIMATIONS)
    rows=[]
    for race in races:
        # FCS按原StringID合并；不携带生命、模型、速度、既有动作等覆盖字段，仅增加本武器十招动画引用。
        rows.append(dict(type=7,id=0,name=race['name'],key=race['key'],save=0,
                         sections=[[] for _ in range(7)],cats=[category],inst=fcs.put(0)))
    # 显式依赖原补丁和Iris。新补丁应放在两者之后；不复制原补丁的空动画占位，避免覆盖真实男女动画路径。
    dependencies=source.name+',IrisArsenal.mod'
    description=patch_name+'：只为'+str(len(rows))+'个既有种族追加IrisArsenal十招动画；原种族与医疗规则保持。'
    header=fcs.put(1)+b''.join(fcs.w_str(s) for s in ('Codex',description,dependencies,''))+b'\0'*10
    result=struct.pack('<II',17,len(header))+header+struct.pack('<II',100,len(rows))
    result+=b''.join(fcs.write_record(row) for row in rows)
    reread=records(result)
    assert len(reread)==len(rows) and all(r['type']==7 for r in reread)
    assert all(not any(r['sections']) and r['cats']==[category] for r in reread)
    info=('<?xml version="1.0" encoding="utf-8"?>\n<ModData>\n'
          '  <id>0</id>\n  <mod>'+patch_name+'</mod>\n'
          '  <title>IrisArsenal - '+patch_name.removeprefix('IrisArsenal_')+'</title>\n'
          '  <visibility>0</visibility>\n</ModData>\n')
    evidence={'source':str(source),'source_sha256':hashlib.sha256(raw).hexdigest(),
              'dependencies':dependencies.split(','),'race_count':len(rows),
              'races':[{'id':r['key'],'name':r['name']} for r in races],
              'animation_sets':list(ANIMATIONS),'runtime_tested':False}
    return result,info,evidence

def main():
    # 只生成项目compatibility目录；部署/启用由明确授权的任务处理，绝不改mods.cfg或用户勾选。
    iris=(ROOT/'package/IrisArsenal/IrisArsenal.mod').read_bytes()
    for name,original,label,count in PATCHES:
        raw,info,evidence=build(GAME/'mods'/original/(original+'.mod'),iris,name,count)
        target=ROOT/'compatibility'/name
        put(target/(name+'.mod'),raw,'独立FCS种族动画兼容补丁','只追加十招动画集引用，不修改原补丁','新补丁需用户在启动器勾选并置于原补丁及IrisArsenal之后；未游戏实测')
        put(target/('_'+name+'.info'),info,'独立补丁启动器说明','本地补丁标识，不发布工坊','需用户勾选新补丁')
        print(json.dumps({'patch':name,'races':evidence['race_count']},ensure_ascii=False))

if __name__=='__main__':main()
