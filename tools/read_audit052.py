"""手动离线分析052日志；逐行读取、不设行数上限、不轮询、不修改原日志。"""
from pathlib import Path
import argparse,json,re
def fields(line):return dict(re.findall(r'([A-Za-z_]\w*)=([^\s]+)',line))
def read_log(path):
    identity=None;groups={};latest=None;complete=0;partial=0;stages={};warnings=[];trend=[];pressure=[]
    with Path(path).open('r',encoding='utf-8-sig',errors='strict') as stream:
        for number,line in enumerate(stream,1):
            if 'audit_run_identity ' in line:
                identity=fields(line);m=re.search(r' executable=(.*?) game_version=',line)
                if m:identity['executable']=m.group(1)
            elif 'damage_queue_pressure ' in line:
                pressure.append(dict(fields(line),line=number));pressure=pressure[-8:]
            elif 'resource_begin ' in line:
                f=fields(line);key=(f.get('channel'),f.get('name'));stages[key]=stages.get(key,0)+1
            elif 'resource_end ' in line:
                f=fields(line);key=(f.get('channel'),f.get('name'));stages[key]=max(0,stages.get(key,0)-1)
                if f.get('failed')=='1':warnings.append({'line':number,'kind':'resource_failed','evidence':f})
            elif any(tag in line for tag in ('audit_counters ','audit_timing ','audit_resources ')):
                f=fields(line);key=f.get('id');g=groups.setdefault(key,{'counters':{},'resources':{},'timing':{}});scope=f.get('scope')
                if 'audit_counters ' in line:g['counters'][scope]=f
                elif 'audit_resources ' in line:g['resources'][scope]=f
                else:g['timing'][(scope,f.get('channel'))]=f
            elif 'audit_summary_end ' in line:
                f=fields(line);g=groups.pop(f.get('id'),None)
                valid=g and set(g['counters'])=={'window','process'} and set(g['resources'])=={'window','process'} and len(g['timing'])==int(f.get('timing_lines',-1)) and all(row.get('frame')==f.get('frame') for table in ('counters','resources') for row in g[table].values())
                if valid:
                    latest={'end':f,'counters':g['counters'],'resources':g['resources'],'timing':list(g['timing'].values())};complete+=1
                    resource=g['resources']['process'];trend.append({k:resource[k] for k in ('id','actors','active','projectiles','residues','idle_visuals','attached_visuals','jobs','pending_damage') if k in resource});trend=trend[-8:]
                else:partial+=1
                # 旧未闭合摘要不可能再补齐，丢弃内存中的组但统计为partial，保留整个原始文件。
                partial+=len(groups);groups.clear()
            elif 'plugin_disabled' in line or 'cleanup_' in line and 'error' in line:warnings.append({'line':number,'kind':'runtime_error','evidence':line.strip()})
    partial+=len(groups)
    return {'file':str(Path(path).resolve()),'identity':identity,'complete_summaries':complete,'incomplete_summaries':partial,'latest_complete':latest,'recent_resource_snapshots':trend,'recent_damage_queue_pressure':pressure,'incomplete_resource_stages':[{'channel':k[0],'name':k[1],'count':v} for k,v in stages.items() if v],'warnings':warnings,'interpretation':'process累计不能相加；队列延迟是墙钟；资源数量不是显存；不依据退出/半日志断言崩溃'}
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('files',nargs='*',type=Path);parser.add_argument('--log-dir',type=Path,default=Path('D:/steam/steamapps/common/Kenshi/mods/IrisArsenal/logs'));args=parser.parse_args()
    paths=args.files or sorted(args.log_dir.glob('IrisArsenal-*.log'));runs=[]
    for path in paths:
        try:runs.append(read_log(path))
        except (OSError,UnicodeError,ValueError) as error:runs.append({'file':str(path),'read_error':str(error)})
    print(json.dumps({'polling':False,'files_modified':False,'runs':runs},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
