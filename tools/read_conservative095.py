"""只读095日志：碰撞配对成本、名单比及测试自身成本；不换算FPS。"""
from pathlib import Path
import argparse,json,re

def analyze(path,since=None):
    # 进程累计不能相加；只接纳带summary_end的完整窗口，同id只保留最后一份。
    rows={};pending={};versions=set();ready=[]
    for line in Path(path).read_text('utf-8-sig').splitlines():
        match=re.match(r'(.+?) \[IrisArsenal ([^]]+)\] (\S+)',line)
        if not match:continue
        versions.add(match[2]);kind=match[3]
        if kind=='conservative_proof_ready':ready.append(line)
        if kind not in ('audit_conservative_proof','audit_summary_end'):continue
        row=dict(re.findall(r'(\w+)=([^\s]+)',line));identity=row.get('id')
        if not identity:continue
        if kind=='audit_conservative_proof':
            if row.get('scope')=='window' and row.get('contract')=='IRIS_CONSERVATIVE_PROOF_095':pending[identity]=row
        else:
            row=pending.pop(identity,None)
            if row is not None and (not since or match[1]>=since):
                row['time']=match[1];rows[identity]=row
    counts='batches timed_batches candidates type_reads_saved parallel_axes_saved audits paired_calls_each reference_shape_calls compared_paths approx_unique exact_unique extra_unique missing_unique invalid_comparisons'.split()
    times='reference_kernel_ms optimized_kernel_ms exact_shape_ms approximate_stage_ms audit_total_ms'.split()
    out={key:sum(int(r.get(key,0)) for r in rows.values()) for key in counts}
    out.update({key:sum(float(r.get(key,0)) for r in rows.values()) for key in times})
    out.update(file=str(path),versions=sorted(versions),windows=len(rows),incomplete_windows_ignored=len(pending),first_summary=min((r['time'] for r in rows.values()),default=None),last_summary=max((r['time'] for r in rows.values()),default=None),ready=ready[-1:] or [],cost_scope='collision_only',injury_cost_included=False,FPS_measured=False)
    # 精确0时人数比无定义；不得把额外项、漏项或异常批次藏进平均值。
    out['approximate_to_exact_ratio']=out['approx_unique']/out['exact_unique'] if out['exact_unique'] else None
    out['kernel_new_to_reference_ratio']=out['optimized_kernel_ms']/out['reference_kernel_ms'] if out['reference_kernel_ms'] else None
    out['approximate_stage_to_exact_reference_ratio']=out['approximate_stage_ms']/out['exact_shape_ms'] if out['exact_shape_ms'] else None
    out['set_balance_valid']=out['approx_unique']-out['exact_unique']==out['extra_unique']-out['missing_unique']
    out['notes']=['名单比是采样逐路径角色集合，未经过敌我/昏迷/逐段医疗资格，不冒充最终受伤人数。',
        'since按完整摘要结束时间筛选，首窗可能跨越边界；摘要不能伪拆为逐秒。',
        'approximate_stage含正式近似准备/读取/结果分发；exact参考复用bounds且不计名单比较/医疗；仅timed_batches完整有效批参与。',
        'audit_total_ms为显式测试总成本，包含精确参考和微测，属于测试开销；外层根计时仍包含它，不能当正常性能。']
    return out

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('log',type=Path);parser.add_argument('--since');args=parser.parse_args()
    print(json.dumps(analyze(args.log,args.since),ensure_ascii=False,indent=2))
