"""一键重建、校验与同步IrisArsenal；不编译，不操作游戏进程/勾选/存档。"""
from pathlib import Path,PurePosixPath
import argparse,ctypes,datetime,hashlib,json,os,shutil,stat,subprocess,sys,uuid
from safeio import ROOT
MOD=Path('D:/steam/steamapps/common/Kenshi/mods/IrisArsenal')
BACKUPS=(Path('D:/CodexBackups'),Path('E:/AIWorkSpace/_backups'))

def digest(data):return hashlib.sha256(data).hexdigest()
def require(condition,message):
    if not condition:raise RuntimeError(message)

def no_reparse(path):
    # 先逐级检查原始路径，拒绝目录联接，不能resolve后掩盖目录跳转。
    path=Path(path).absolute()
    for p in (path,*path.parents):
        if p.exists() or p.is_symlink():
            require(not getattr(p.lstat(),'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT,'拒绝重解析点：'+str(p))
            require(not p.is_symlink(),'拒绝符号链接：'+str(p))
    return path

def safe_child(root,name):
    name=name.replace('\\','/');parts=PurePosixPath(name).parts
    require(parts and not name.startswith('/') and all(p not in ('.','..') and ':' not in p for p in parts),'非法清单路径：'+name)
    p=no_reparse(Path(root).joinpath(*parts))
    require(p.is_relative_to(Path(root).absolute()),'文件越过目录：'+name)
    return p

def game_stopped():
    # 查询失败也停止，不把错误误认为游戏已关闭。
    script="[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false); $ErrorActionPreference='Stop'; ConvertTo-Json -Compress -InputObject @(Get-CimInstance Win32_Process -Filter \"Name='kenshi_x64.exe' OR Name='kenshi_x64_gog.exe'\" | Select-Object ProcessId,ExecutablePath)"
    r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],capture_output=True,timeout=30)
    require(r.returncode==0,'无法查询游戏进程：'+r.stderr.decode('utf-8',errors='replace'))
    processes=json.loads(r.stdout.decode('utf-8-sig').strip())
    require(not processes,'Kenshi仍在运行，请正常退出后重新双击 UpdateMod.cmd：'+json.dumps(processes,ensure_ascii=False))

def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2)

def replace_bytes(path,data):
    # 图标缓存适配器仍调用此原子写接口；整目录部署不再通过它逐项合并。
    no_reparse(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name('.'+path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        with temp.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        no_reparse(path);os.replace(temp,path)
        require(path.read_bytes()==data,'回读失败：'+str(path))
    finally:
        if temp.exists():temp.unlink()

def file_hash(path):
    # 流式计算哈希，旧日志再大也不必整份读入内存；备份保留原字节和编码。
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def tree_state(root):
    root=no_reparse(root);files={};directories=[]
    if not root.exists():return {'exists':False,'files':files,'directories':directories}
    require(root.is_dir(),'不是目录：'+str(root))
    for p in sorted(root.rglob('*')):
        no_reparse(p);name=p.relative_to(root).as_posix()
        if p.is_dir():directories.append(name)
        else:
            require(p.is_file(),'目录中含非普通文件：'+str(p));files[name]=file_hash(p)
    return {'exists':True,'files':files,'directories':directories}

def check_target(target):
    # 唯一允许清理的是明确指定的mods/IrisArsenal；先检查原路径再resolve，防止联接越界。
    target=no_reparse(target)
    require(target.name=='IrisArsenal' and target.parent.name.casefold()=='mods','目标必须是mods/IrisArsenal')
    require(target.resolve()==target,'目标路径必须是规范绝对路径：'+str(target))
    return target

def clear_target(target):
    target=check_target(target)
    tree_state(target) # 每次递归删除前重查所有子路径，拒绝目录联接/符号链接。
    if not target.exists():return
    for child in list(target.iterdir()):
        child=no_reparse(child)
        require(child.resolve().is_relative_to(target.resolve()) and child.parent==target,'清理路径越界：'+str(child))
        if child.is_dir():shutil.rmtree(child)
        else:child.unlink()

def copy_tree(source,dest,state,inject=None,report=None):
    no_reparse(source);no_reparse(dest);dest.mkdir(parents=True,exist_ok=True)
    for name in state['directories']:safe_child(dest,name).mkdir(parents=True,exist_ok=True)
    for i,(name,sha) in enumerate(state['files'].items()):
        row={'name':name,'dest':safe_child(dest,name)}
        if inject:inject(i,row)
        src=safe_child(source,name);require(file_hash(src)==sha,'源文件哈希不符：'+name)
        row['dest'].parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,row['dest'])
        require(file_hash(row['dest'])==sha,'复制校验失败：'+name)
        if report:report(i,name,sha)
    require(tree_state(dest)==state,'整目录复制终验失败：'+str(dest))

def deploy_package(package,target,backup_bases=BACKUPS,guard=game_stopped,inject=None,audit_root=None):
    package=no_reparse(package);target=check_target(target)
    require(not package.is_relative_to(target) and not target.is_relative_to(package),'模组包与安装目录不能相互包含')
    manifest=json.loads((package/'IrisPackage.json').read_text('utf-8-sig'))
    require(manifest.get('ready') is True,'运行包尚未通过组包')
    files=manifest['files'];required={'IrisArsenal.dll','IrisArsenal.mod','IrisArsenal.ini','RE_Kenshi.json','_IrisArsenal.info'}
    expected={}
    for name,sha in files.items():
        # 所有包内构件均同步，包含署名、图标和新资源；仅拒绝越界、重复及内容损坏。
        normalized=name.replace('\\','/');safe_child(package,name)
        require(normalized.casefold() not in expected,'清单路径重复：'+name)
        require(isinstance(sha,str) and len(sha)==64 and all(c in '0123456789abcdef' for c in sha),'非法SHA256：'+name)
        expected[normalized.casefold()]=normalized
    require(required<=set(expected.values()) and 'irispackage.json' not in expected,'运行入口缺失或清单自引用')
    source=tree_state(package)
    require(set(source['files'])==set(expected.values())|{'IrisPackage.json'},'运行包文件与清单不一致，请重新组包')
    for name,sha in files.items():require(source['files'][name.replace('\\','/')]==sha,'源文件哈希不符：'+name)
    guard()
    old=tree_state(target)
    stamp='IrisArsenal-CleanUpdate-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'-'+uuid.uuid4().hex[:8]
    audit=Path(audit_root or ROOT/'docs/update-runs')/stamp
    require(not audit.absolute().is_relative_to(target),'报告目录不能位于待清空目录内')
    audit.mkdir(parents=True,exist_ok=False);saved=[]
    # 先备份全部既有内容（含日志、旧配置及未知文件），全部哈希验证后才允许清空。
    # 不再合并INI或保留info，也不再使用逐文件部署白名单；最终目录与package逐字节一致。
    if old['exists']:
        require(len(backup_bases)>=2,'清空之前必须有两份独立备份')
        for name in old['files']:
            p=safe_child(target,name)
            if p.stat().st_size>20*1024*1024:print('将完整备份大文件后替换：'+str(p),flush=True)
        for base in backup_bases:
            dest=no_reparse(Path(base)/stamp/target.drive.rstrip(':')/Path(*target.parts[1:]))
            require(not dest.is_relative_to(target) and not dest.is_relative_to(package),'备份位置不能位于源/目标内')
            require(not dest.exists(),'备份目录已存在：'+str(dest))
            copy_tree(target,dest,old);saved.append(dest)
    write_json(audit/'before.json',{'target':str(target),'old':old,'source':source,'backups':[str(p) for p in saved]})
    changed=False
    try:
        guard();require(tree_state(target)==old,'目标在备份后被其他程序修改，未清空')
        print('清空并完整复制到：'+str(target),flush=True)
        changed=True;clear_target(target)
        def report(i,name,sha):
            write_json(audit/('%04d.json'%i),{'File':str(safe_child(target,name)),'Role':'完整模组构件','Code location':name,'Before':old['files'].get(name),'Changes':'清空后原字节复制完整package','Reasons':'用户要求全量替换','After':sha,'Impact':'仅目标IrisArsenal目录','Validation':'写后SHA256一致','Safety':{'backups':[str(p) for p in saved],'encoding':'原字节复制，编码/换行保持'},'Unresolved':'未进行游戏测试'})
        copy_tree(package,target,source,inject,report)
        result={'success':True,'mode':'clean_replace','target':str(target),'version':manifest['version'],'contract':manifest['contract'],'files_verified':len(source['files']),'files_written':len(source['files']),'old_files_removed':len(set(old['files'])-set(source['files'])),'configuration':'replaced_from_package','dll_sha256':source['files']['IrisArsenal.dll'],'backup_roots':[str(Path(b)/stamp) for b in backup_bases] if saved else [],'audit':str(audit),'game_tested':False,'compiled_by_script':False}
        write_json(audit/'result.json',result)
        return result
    except BaseException as error:
        failures=[]
        if changed:
            try:
                # 恢复整目录快照，连空文件夹/旧日志/个人配置一起恢复；不只回退本次清单中的文件。
                guard();clear_target(target)
                if old['exists']:copy_tree(saved[0],target,old)
                elif target.exists():target.rmdir()
                require(tree_state(target)==old,'旧目录恢复终验失败')
            except BaseException as rollback:failures.append(str(rollback))
        write_json(audit/'failure.json',{'error':str(error),'rollback_errors':failures,'backups':[str(p) for p in saved]})
        raise RuntimeError('更新失败：'+str(error)+'；恢复错误：'+str(failures)+'；备份与报告：'+str(audit)) from error

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--package-only',action='store_true');args=parser.parse_args()
    # 仅更新脚本互斥，不在插件或游戏线程加锁；进程退出时由Windows释放。
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.CreateMutexW.restype=ctypes.c_void_p
    kernel.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_wchar_p];kernel.CloseHandle.argtypes=[ctypes.c_void_p]
    handle=kernel.CreateMutexW(None,0,'Local\\IrisArsenal_Update_'+digest(str(ROOT).encode())[:16])
    require(handle is not None,'无法取得更新脚本互斥句柄')
    try:
        require(ctypes.get_last_error()!=183,'另一个IrisArsenal更新脚本仍在运行')
        if not args.package_only:
            require((MOD.parents[1]/'kenshi_x64.exe').is_file(),'未找到目标Kenshi游戏目录')
            no_reparse(MOD);game_stopped()
        from stage_package import validate_dll
        validate_dll()
        # 日常更新只把已有完整资源与用户编译DLL组包后复制；不重建资源、不跑历史测试。
        import stage_package
        stage_package.main(run_checks=False)
        if args.package_only:print('完整组包成功，没有写入游戏目录。');return
        result=deploy_package(ROOT/'package/IrisArsenal',MOD)
        # 本入口只替换固定mod目录；图标已包含在包内icons，不再顺带改写全局data/icons缓存。
        print('更新成功：'+json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    finally:kernel.CloseHandle(handle)

if __name__=='__main__':
    try:main()
    except Exception as error:
        print('更新未完成：'+str(error),file=sys.stderr,flush=True);sys.exit(1)
