"""仅刷新Iris锤枪原生自动图标缓存；由完整部署成功后调用，不操作游戏进程。"""
from pathlib import Path
import datetime,uuid
def refresh(game,backup_bases,guard):
    from update_mod import no_reparse,require
    # 两份外部备份是强制条件，不能因调用者传空列表而无备份删除缓存。
    require(len(backup_bases)==2,'图标刷新必须有两份外部备份')
    game=Path(game).absolute();icons=no_reparse(game/'data/icons');guard();removed=[]
    if not icons.is_dir():return removed
    targets=[no_reparse(p) for p in icons.glob('1-IrisArsenal.mod.*.png') if p.is_file()]
    stamp='IrisArsenal-Icon047-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-')+uuid.uuid4().hex[:8]
    # 先验证全部目标绝对路径仍位于固定icons，再逐一备份全部文件；失败时绝不提前删除。
    for p in targets:
        require(p.resolve().parent==icons.resolve() and p.name.startswith('1-IrisArsenal.mod.'),'图标路径越界')
        raw=p.read_bytes();require(len(raw)<=20*1024*1024,'大缓存不能自动处理')
        backups=[]
        for root in backup_bases:
            dest=Path(root)/stamp/p.drive.rstrip(':')/Path(*p.parts[1:]);dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb') as f:f.write(raw)
            require(dest.read_bytes()==raw,'图标备份校验失败');backups.append(str(dest))
        removed.append({'file':str(p),'backups':backups,'data':raw})
    guard()
    for row in removed:
        p=no_reparse(Path(row['file']));require(p.read_bytes()==row['data'],'缓存并发变化，停止刷新')
    for row in removed:Path(row['file']).unlink()
    return [{k:v for k,v in row.items() if k!='data'} for row in removed]
