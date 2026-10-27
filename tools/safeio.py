"""IrisArsenal安全写入：仅本项目、双外部备份、编码保持及逐文件即时记录。"""
from pathlib import Path
import datetime,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
STAMP='IrisArsenal-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
def put(path,data,role,changes,unresolved='用户编译与实机验收待完成'):
    path=Path(path).resolve();assert path.is_relative_to(ROOT)
    old=path.read_bytes() if path.exists() else None;backups=[];encoding='binary'
    if isinstance(data,str):
        bom=old is not None and old.startswith(b'\xef\xbb\xbf')
        previous=old.decode('utf-8-sig') if old is not None else ''
        ending='\r\n' if '\r\n' in previous or path.suffix in ('.cpp','.h','.sln','.vcxproj','.cmd') else '\n'
        text=data.replace('\r\n','\n').replace('\n',ending)
        assert not any(x in text for x in ('\ufffd','\u951f\u65a4\u62f7','\u00c3','\u00c2','\u00ef\u00bb\u00bf','\x3f\x3f\x3f'))
        data=(b'\xef\xbb\xbf' if bom else b'')+text.encode('utf-8');encoding='UTF-8'+(' BOM' if bom else '')+('/CRLF' if ending=='\r\n' else '/LF')
    if old==data:return
    if old is not None:
        assert len(old)<=20*1024*1024,'大文件先说明备份'
        for base in ('D:/CodexBackups','E:/AIWorkSpace/_backups'):
            dest=Path(base)/STAMP/('edit-'+datetime.datetime.now().strftime('%H%M%S-%f'))/path.drive.rstrip(':')/Path(*path.parts[1:]);dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb') as f:f.write(old)
            assert dest.read_bytes()==old;backups.append(str(dest))
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('wb' if old is not None else 'xb') as f:f.write(data)
    assert path.read_bytes()==data
    report={'File':str(path),'Role':role,'Code location':'新增独立单元/生成区域','Before':hashlib.sha256(old).hexdigest() if old is not None else '不存在','Changes':changes,'Reasons':'用户授权IrisArsenal清理与长期日志；按本条Changes限定，历史授权不扩大本次范围','After':hashlib.sha256(data).hexdigest(),'Impact':'仅IrisArsenal项目，不编译、不部署、不写其他项目','Validation':'字节回读；文本严格UTF-8和中文乱码扫描','Safety':{'backups':backups,'encoding':encoding},'Unresolved':unresolved}
    folder=ROOT/'docs/change-reports';folder.mkdir(parents=True,exist_ok=True)
    dest=folder/(datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'-'+path.name+'.json')
    with dest.open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print('WRITE',path.relative_to(ROOT))

def retire(path,reason):
    # 052精确清理：仅本项目普通文件，全部双备份验证后删除；不递归、不碰联接或未知目录。
    path=Path(path);assert not path.is_symlink();resolved=path.resolve();assert resolved.is_relative_to(ROOT.resolve())
    if not resolved.exists():return
    assert resolved.is_file();data=resolved.read_bytes();assert len(data)<=20*1024*1024
    backups=[]
    for base in ('D:/CodexBackups','E:/AIWorkSpace/_backups'):
        dest=Path(base)/STAMP/('retire-'+datetime.datetime.now().strftime('%H%M%S-%f'))/resolved.drive.rstrip(':')/Path(*resolved.parts[1:]);dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as f:f.write(data)
        assert dest.read_bytes()==data;backups.append(str(dest))
    assert resolved.read_bytes()==data;resolved.unlink()
    row={'File':str(resolved),'Role':'已确认无消费者资源','Code location':str(resolved.relative_to(ROOT)),'Before':hashlib.sha256(data).hexdigest(),'Changes':'双备份后精确删除','Reasons':reason,'After':None,'Impact':'只清理指定旧资源','Validation':'引用白名单/备份和删除后存在性','Safety':{'backups':backups,'encoding':'binary'},'Unresolved':'游戏部署由用户更新脚本执行'}
    folder=ROOT/'docs/change-reports';folder.mkdir(parents=True,exist_ok=True)
    with (folder/(datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'-retire-'+resolved.name+'.json')).open('x',encoding='utf8') as f:json.dump(row,f,ensure_ascii=False,indent=2)
    print('RETIRED',resolved.relative_to(ROOT))
