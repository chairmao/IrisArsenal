"""047兼容历史回归：仅允许已登记的精确before→after，不能宽泛跳过文件或函数。"""
import json
from safeio import ROOT
def assert_047_hash(key,actual,expected):
    if actual==expected:return
    # 历史Windows记录使用反斜杠，统一清单键而不改变路径或摘要约束。
    key=key.replace(chr(92),'/')
    # root:package与package指向同一运行文件；统一身份后仍逐段比对完整SHA256。
    if key.startswith('root:package/IrisArsenal/'):key='package:'+key[len('root:package/IrisArsenal/'):]
    previous=expected
    # 047→049→050→051→052→053→053-queue32→054→055→056→057→058只接受每一段精确摘要链接；无记录的文件/函数仍拒绝，不能跳过整目录。
    for revision in ('047','049','050','051','052','053','053-queue32','054','055','056','057','058','059'):
        changes=json.loads((ROOT/('docs/authorized-delta-'+revision+'.json')).read_text('utf8'));change=changes.get(key)
        if change and change['before']==previous:previous=change['after']
        if previous==actual:return
    assert previous==actual,key

def original_specs047(moves,previous):
    import copy
    result=copy.deepcopy(moves)
    # 059唯一改招是drive。先逐字核对登记的新规格，再恢复058规格供历史回归比较；
    # 不宽泛跳过drive，其PA10/站姿/R9/源准星由059专项独立核验。
    if len(result)>7 and 'mco_powerattack10.hkx' in ' '.join(result[7]['sources']):
        evidence=json.loads((ROOT/'docs/drive059-spec-change.json').read_text('utf8'))
        assert result[7]==evidence['after']
        result[7]=copy.deepcopy(evidence['before'])
    # 只恢复两招已授权的重定向审计字段，源文件/事件/距离/倍率/根轨道仍完整对比旧规格。
    for i in (5,7):
        result[i].pop('height047',None);result[i].pop('seat049',None);result[i].pop('seat050',None);result[i]['retarget']=previous[i]['retarget']
    return result

def package_hash052(path):
    # 052只承认精确退役白名单的原散列；这是退役身份校验，不声称文件仍在新包内。
    import hashlib
    path=__import__('pathlib').Path(path)
    if path.is_file():return hashlib.sha256(path.read_bytes()).hexdigest()
    package=(ROOT/'package/IrisArsenal').resolve();resolved=path.resolve();assert resolved.is_relative_to(package)
    relative=resolved.relative_to(package).as_posix();doc=json.loads((ROOT/'docs/retired-runtime-052.json').read_text('utf8'))
    assert relative in doc['files'] and relative in doc['before_sha256'],relative
    return doc['before_sha256'][relative]
