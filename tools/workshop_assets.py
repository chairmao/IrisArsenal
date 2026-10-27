"""工坊发布资料组包；不编译、不上传、不写游戏目录。"""
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from safeio import ROOT,put

FILES=('preview.jpg','_IrisArsenal.img','WORKSHOP_DESCRIPTION.txt','WORKSHOP_CHANGELOG.txt','README.txt','CREDITS.txt')
INSTALLED_INFO=Path('D:/steam/steamapps/common/Kenshi/mods/IrisArsenal/_IrisArsenal.info')

def merge_info(template,candidates):
    # 工坊ID是已发布条目的身份，不是运行版本。清空安装目录前将已有ID写入待复制包，
    # 最终仍按原Update全量替换；只读本地元数据，不创建条目、不改变Steam可见性。
    base=ET.fromstring(template);assert base.tag=='ModData' and base.findtext('mod')=='IrisArsenal'
    rows=[base]+[ET.fromstring(value) for value in candidates]
    for row in rows:
        if row.findtext('mod')!='IrisArsenal':raise RuntimeError('工坊元数据不属于IrisArsenal')
        value=row.findtext('id','0')
        if not value.isdecimal() or int(value)>2**64-1:raise RuntimeError('无效工坊条目ID')
    ids={int(row.findtext('id','0')) for row in rows if int(row.findtext('id','0'))}
    if len(ids)>1:raise RuntimeError('发现不同工坊条目ID，未覆盖发布身份，请先核对.info')
    if not ids:return template
    published=ids.pop();result=re.sub(r'<id>\d+</id>','<id>'+str(published)+'</id>',template,count=1)
    # 已发布时沿用已有可见性和更新时间，避免源模板的私人草稿值覆盖公开条目状态。
    for row in reversed(rows):
        if int(row.findtext('id','0'))!=published:continue
        for name in ('visibility','lastUpdate'):
            element=row.find(name)
            if element is None:continue
            fragment=ET.tostring(element,encoding='unicode').strip()
            if re.search(r'<'+name+r'>.*?</'+name+r'>',result,flags=re.S):result=re.sub(r'<'+name+r'>.*?</'+name+r'>',lambda m:fragment,result,count=1,flags=re.S)
            else:result=result.replace('</ModData>',' '+fragment+'\n</ModData>')
        break
    return result

def prepare():
    source=ROOT/'distribution';out=ROOT/'package/IrisArsenal'
    # 先完整读取、校验，再写包，缺少封面／说明或冲突ID不会触发游戏部署。
    data={name:(source/name).read_bytes() for name in FILES}
    assert data['preview.jpg']==data['_IrisArsenal.img'] and data['preview.jpg'].startswith(b'\xff\xd8')
    template=(source/'_IrisArsenal.info').read_text('utf-8-sig')
    candidates=[p.read_text('utf-8-sig') for p in (out/'_IrisArsenal.info',INSTALLED_INFO) if p.is_file()]
    metadata=merge_info(template,candidates)
    for name,value in data.items():put(out/name,value,'工坊发布资料','同步distribution中的封面、介绍和来源；不改变战斗构件','Steam上传由用户执行')
    put(out/'_IrisArsenal.info',metadata,'工坊元数据','更新标题并保留已发布ID／可见性；不分配条目ID','Steam上传由用户执行')
