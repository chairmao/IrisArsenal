"""武器FCS平衡：074恢复Falling Sun×1.2正式伤害及玩家指定加成，不运行编译器。"""
from pathlib import Path
import struct,math
import kenshi_mod_writer as fcs

GAME=Path('D:/steam/steamapps/common/Kenshi')
REFERENCE_KEY='52306-rebirth.mod'
FORMAL_MULTIPLIER=1.2
# 074：结束十分之一伤害测试；保留常量接口，完整重建与现存FCS补丁共用同一份正式数据。
TEST_FRACTION=1.0
FCS_DESCRIPTION='IrisArsenal：同锤枪远程三招、近战七招；基础切割/钝伤为Falling Sun×1.2，失血2.5，攻击+20、防御+10、室内0。'

def reference():
    raw=(GAME/'data/rebirth.mod').read_bytes();p=fcs.find_records_start(raw);selected=[]
    while p<len(raw):
        row=fcs.read_record(raw,p,len(raw));assert row is not None;p=row['end']
        if row['key']==REFERENCE_KEY:selected.append(row)
    assert len(selected)==1 and selected[0]['type']==2 and selected[0]['name']=='Falling Sun'
    fields={key:(kind,value) for section in selected[0]['sections'] for key,kind,value in section}
    values={}
    for key in ('cut damage multiplier','blunt damage multiplier'):
        kind,data=fields[key];assert kind=='f32';value=struct.unpack('<f',data)[0];assert math.isfinite(value) and value>0;values[key]=value
    return values

def expected_fields():
    # 074：基础武器恢复正式参考×1.2（此前测试值的10倍）；不修改各招独立事件倍率。
    values={key:value*FORMAL_MULTIPLIER*TEST_FRACTION for key,value in reference().items()}
    values.update({'attack mod':20,'defence mod':10,'armour penetration':.5,'bleed mult':2.5,'indoors mod':0})
    return values

def apply_existing(record,values):
    # 保持FCS字段顺序，避免完整UpdateMod重建把已验证的同值字段重新排列。
    seen=set()
    for section in record['sections']:
        for i,(key,kind,data) in enumerate(section):
            if key not in values:continue
            assert key not in seen and kind==('long' if key in ('attack mod','defence mod','indoors mod') else 'f32')
            section[i]=(key,kind,struct.pack('<i' if kind=='long' else '<f',values[key]));seen.add(key)
    assert seen==set(values)

def patch_existing_mod(raw,values):
    # 074：只改玩家指定的既有4字节数值；包含室内long和失血f32，保留穿甲及其他记录。
    p=fcs.find_records_start(raw);selected=[]
    while p<len(raw):
        row=fcs.read_record(raw,p,len(raw));assert row is not None
        if row['key']=='1-IrisArsenal.mod':selected.append((p,row))
        p=row['end']
    assert len(selected)==1;start,row=selected[0];end=row['end'];body=bytearray(raw[start:end]);offsets=[]
    entries={key:(kind,data) for section in row['sections'] for key,kind,data in section}
    for key,value in values.items():
        kind,old=entries[key];assert kind==('long' if key in ('attack mod','defence mod','indoors mod') else 'f32') and len(old)==4
        marker=fcs.w_str(key)+old;assert body.count(marker)==1;offset=body.index(marker)+len(marker)-4
        body[offset:offset+4]=struct.pack('<i' if kind=='long' else '<f',value);offsets.append((key,start+offset))
    result=raw[:start]+bytes(body)+raw[end:];assert len(result)==len(raw)
    allowed={j for _,offset in offsets for j in range(offset,offset+4)}
    assert all(i in allowed for i,(old,new) in enumerate(zip(raw,result)) if old!=new)
    return result,offsets
