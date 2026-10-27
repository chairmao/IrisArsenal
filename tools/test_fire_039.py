"""039实录尾帧重放/32帧火焰/透明度回归；非编译分析，不当作实际C++执行。"""
import json,hashlib,re
from pathlib import Path
import numpy as np
from PIL import Image
from safeio import ROOT
from fx_timeline import raw_blocks
from drill_particles import atlas_layout
from test_drill_visibility import buffers

def cycle_replay(events,trace,old):
    # 独立事件观察模型：通知、真实片段时钟、暂停、开/关沿分开输入；以事件数量为输出验收。
    active=False;last=0;notice_used=0;next_event=0;out=[];cycles=0
    for t,notice,live,paused,dt in trace:
        if not live:active=False;continue
        if active and (t+.0001<last or old and notice!=notice_used):active=False
        if not active and not paused:
            if not old and t>events[0]+max(0,dt):continue
            active=True;cycles+=1;notice_used=notice;next_event=0;last=0
        if not active:continue
        if not paused:
            while next_event<len(events) and events[next_event]<=t:
                out.append((cycles,next_event,t));next_event+=1
        last=t
    return out

def verify_fire039():
    a=ROOT/'package/IrisArsenal/assets';fx=json.loads((ROOT/'docs/eight-effects.json').read_text('utf8'));moves=json.loads((ROOT/'docs/eight-moves.json').read_text('utf8'))['moves']
    code=(ROOT/'IrisCombat.cpp').read_text('utf8');segment=code[code.index('// 039：startCombatAnimation'):code.index('if(!a.active){++i;continue;}Ogre::Entity* actual=')]
    assert 'a.start!=a.consumed||' not in segment and 'if(t>opening)' in segment and 'gameDelta*a.rates[move]' in segment
    assert code.count('->_NV_hitByMeleeAttack(')==1 and code.count('KenshiLib::AddHook(')==3
    replay={}
    for move in moves:
        times=[e['time'] for e in move['events']];tail=move['duration']-.05
        trace=[(0,1,True,False,1/60)]+[(t+1e-5,1,True,False,1/60) for t in times]
        trace += [(tail,1,True,False,1/60),(tail,2,True,False,1/60),(tail,3,True,True,0),(0,3,False,False,1/60),(tail,3,True,False,1/60)]
        before=cycle_replay(times,trace,True);after=cycle_replay(times,trace,False)
        assert len(after)==len(times) and len(before)>len(after),(move['key'],before,after)
        # 真正新周期回零后仍能重复使用；不是靠永久已爆炸位或新增冷却压掉正常下一招。
        two=trace+[(0,4,True,False,1/60)]+[(t+1e-5,4,True,False,1/60) for t in times]
        assert len(cycle_replay(times,two,False))==len(times)*2
        # 第一帧较晚但仍处于本帧实际推进窗口，不会按墙钟固定阈值拒绝快进/低帧率动作。
        hitch=[(times[0]+.2,1,True,False,.25)]
        assert cycle_replay(times,hitch,False)
        replay[move['key']]={'events':len(times),'old_model_replayed':len(before)-len(after),'new_model_replayed':0,'next_real_cycle_enabled':True}
    # 本次实录：13->14、15->16均在相同8秒尾帧重新消费全部12事件，不是单纯特效余焰。
    fixture=Path(__file__).resolve().parents[0]/'source-cache/drill-038-tail-replay.json'
    log=json.loads(fixture.read_text('utf8'));assert len(log['cases'])==2
    for case in log['cases']:
        assert len(case['replayed_events'])==12 and len(set(case['replayed_clips']))==1 and case['damage_applied']==2
        trace=[(0,1,True,False,1/60)]+[(e['time']+1e-5,1,True,False,1/60) for e in moves[3]['events']]+[(case['replayed_clips'][0],1,True,False,1/60),(case['replayed_clips'][0],2,True,False,1/60)]
        assert sum(e[1]==11 for e in cycle_replay([e['time'] for e in moves[3]['events']],trace,False))==1
    from test_source_fire040 import verify_source040
    return {'recorded_regression':log,'cycle_models':replay,'source_fire040':verify_source040(),'compiled':False,'game_tested':False}

if __name__=='__main__':print(json.dumps(verify_fire039(),ensure_ascii=False,indent=2))
