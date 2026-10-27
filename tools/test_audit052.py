"""052非编译验收：实际源码/序列化引用及独立统计边界；不执行C++、GPU或游戏。"""
from pathlib import Path
import ast,configparser,hashlib,json,re,xml.etree.ElementTree as ET
from safeio import ROOT
def verify_audit052():
    d=(ROOT/'IrisDiagnostics.cpp').read_text('utf8');h=(ROOT/'IrisDiagnostics.h').read_text('utf8');main=(ROOT/'IrisArsenal.cpp').read_text('utf8');c=(ROOT/'IrisCombat.cpp').read_text('utf8');r=(ROOT/'IrisRanged.cpp').read_text('utf8')
    cfg=configparser.ConfigParser();cfg.read(ROOT/'distribution/IrisArsenal.ini',encoding='utf8');section=cfg['IrisArsenal']
    for key in ('EnableLogging','EnablePerformanceLogging','EnableResourceLogging'):assert section.getint(key)==1 and key in d
    assert section.getfloat('LogSummarySeconds')==60 and section.getfloat('LogFlushSeconds')==2 and section.getfloat('SlowFrameThresholdMs')==8
    for token in ('creation_filetime=','executable=','game_version=','installed_asset_revision=','log_total_limit=0','counter_bits=64','background_thread=0'):assert token in d
    for bad in ('CreateThread(', 'Sleep(', 'CreateProcess(', 'TerminateProcess(', 'NxCreatePhysicsSDK(', 'setUserContactReport('):assert bad not in d
    assert 'if(!enabled)return;Guard guard;if(pending.empty())return;' in d
    assert 'if(!PerformanceEnabled())return;' in d and 'ResourceKind(k)?resource:(performance&&(k<QUERY_WAIT||details))' in d
    assert '65536' in d and 'droppedBytes+=line.size()' in d and 'pending.erase' in d
    assert 'if(force&&frameOpen){summaryPending=true;' in d and 'if(summaryPending)' in d
    assert 'for(unsigned scope=0;scope<2;++scope)' in d and 'window[i]=Stats()' in d and 'run[i]=Stats()' not in d
    assert 'GetProcessTimes(' in d and 'FILE_APPEND_DATA' in d and 'TRUNCATE_EXISTING' not in d
    assert 'i!=DAMAGE_WAIT' in d and 'request_wall_latency' in d
    assert d.index('snapshot[0][i]=window[i]')<d.index('for(unsigned scope=0;scope<2;++scope)')
    assert 'audit_summary_end id=' in d and '++timingLines' in d
    assert 'std::uncaught_exception()' in d and 'resource_begin channel=' in d and 'resource_end channel=' in d
    assert 'IrisDiagnostics::MATERIAL_LOAD' in c and 'material->load()' in c and 'IrisDiagnostics::RESOURCE_GROUP' in main
    assert 'IrisDiagnostics::PREWARM' in c and 'IrisDiagnostics::ASSET_READ' in c
    assert (main+c+r).count('KenshiLib::AddHook(')==18 and c.count('->_NV_hitByMeleeAttack(')==1
    assert 'QueryMetrics' not in c and 'j.wall' not in c and 'bool wall' not in c
    assert 'RangedMove(r.move)&&moves[r.move].bypassDefence' in c and 'unsigned budget=64' in c
    project=ET.parse(ROOT/'IrisArsenal.vcxproj');units=[n.attrib['Include'] for n in project.iter() if n.tag.endswith('ClCompile') and 'Include' in n.attrib]
    assert len(units)==5 and 'IrisDiagnostics.cpp' in units
    # 分位上界/零样本/末桶/64位与窗口重置独立模型，不宣称执行了C++。
    bounds=[0,.01,.025,.05,.1,.25,.5,1,2,4,8,16,32,64,128]
    def percentile(values,p):
        buckets=[0]*16
        for value in values:
            b=next((i for i,x in enumerate(bounds) if value<=x),15);buckets[b]+=1
        target=(len(values)*p+99)//100;count=0
        for i,n in enumerate(buckets):
            count+=n
            if count>=target:return bounds[i] if i<15 else -1
        return 0
    assert percentile([0]*99+[200],95)==0 and percentile([200]*100,99)==-1
    assert percentile([0]*95+[8]*5,99)==8
    counter=2**32+123;assert counter>2**32 and counter+100-counter==100
    process=[0,1,2];window=list(process);window.clear();assert len(process)==3
    # 实际材质引用/效果清单；只删除7个明确文件，保持20有效效果和全部动画/FCS。
    A=ROOT/'package/IrisArsenal/assets';retired=json.loads((ROOT/'docs/retired-runtime-052.json').read_text('utf8'))
    assert len(retired['files'])==7 and len(retired['before_sha256'])==7
    for name in retired['files']:assert not (A.parent/name).exists()
    rows=(A/'effects.csv').read_text('utf8').splitlines();assert rows[0]=='IRIS_FX 4 20' and not any(x.startswith('heavy ') for x in rows)
    fx=json.loads((ROOT/'docs/eight-effects.json').read_text('utf8'));assert len(fx['assets'])==20 and all(a['key']!='heavy' for a in fx['assets'])
    for file in A.glob('*.material'):
        for texture in re.findall(r'\btexture\s+(\S+)',file.read_text('utf8')):assert (A/texture).is_file(),texture
    for p in (ROOT/'tools').rglob('*.py'):ast.parse(p.read_text('utf-8-sig'))
    return {'hooks':18,'compile_units':5,'effective_effect_assets':20,'retired_files':7,'configuration_defaults':dict(section),'independent_histogram_models':3,'zero_frames_included':True,'process_counters_reset_on_load':False,'resource_begin_end':True,'bounded_write_failure_buffer':65536,'compiled':False,'C++_executed':False,'game_tested':False,'GPU_tested':False}
if __name__=='__main__':print(json.dumps(verify_audit052(),ensure_ascii=False,indent=2))
