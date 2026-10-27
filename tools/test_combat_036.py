# 070：历史回归读取迁移后的开发证明表，保留原数据和断言。
# 047新增电脉源范围时间流，头部/消费者仍必须完全一致。
# 045：倍率与防御策略可配置，原几何/源素材回归仍保持；默认与完整开关组合由test_move_parameters045核验。
"""035故障隔离、物理体积和源挥击窗口回归；纯Python模型/源约束，不替代C++和实机。"""
from collections import deque
from pathlib import Path
import json,math,re,struct
import numpy as np
from safeio import ROOT

def verify_combat036():
    c=(ROOT/'IrisCombat.cpp').read_text('utf-8');n=(ROOT/'native/NativeMultiContact.cpp').read_text('utf-8');main=(ROOT/'IrisArsenal.cpp').read_text('utf-8')
    # 永久失败排队首是本次真实故障；比较旧FIFO和新有界轮转，而非只核对注释。
    def simulate(round_robin):
        queue=deque([{'id':'bad','paths':[False],'cursor':0}]+[{'id':str(k),'paths':[True]*17,'cursor':0} for k in range(12)])
        committed=[]
        for tick in range(48):
            budget=64;visits=len(queue)
            while visits and queue and budget:
                visits-=1;j=queue[0];used=0
                while j['cursor']<len(j['paths']) and budget and used<8:
                    used+=1;budget-=1
                    if not j['paths'][j['cursor']]:break
                    j['cursor']+=1
                if j['cursor']<len(j['paths']):
                    if not round_robin:break
                    queue.rotate(-1);continue
                committed.append(j['id']);queue.popleft()
        return committed,list(queue)
    old,_=simulate(False);new,pending=simulate(True)
    assert not old and set(new)==set(map(str,range(12))) and len(new)==12 and len(pending)==1 and pending[0]['id']=='bad'
    resolver=c[c.index('void ResolveJobs('):c.index('bool Blast(')]
    assert 'size_t visits=jobs.size();' in resolver and 'used<8' in resolver and '++j.cursor;++used;' in resolver and 'jobs.splice(jobs.end(),jobs,jobs.begin());IrisDiagnostics::Add(IrisDiagnostics::JOB_ROTATIONS);continue;' in resolver
    assert 'if(!Contacts(w,path,contacts,budget,&length))return;' not in resolver and 'return;' not in resolver.split('void CollectBladeLedgers')[0]
    # 64发长途弹体也不能耗尽既有伤害作业的每帧预算；每一发轮到而非前48永久优先。
    cursor=0;processed=[0]*64;health_progress=0
    for _ in range(8):
        reserve=16;budget=64-reserve
        for k in range(budget):processed[cursor%64]+=1;cursor+=1
        health_progress+=reserve
    assert min(processed)==6 and max(processed)==6 and health_progress==128
    assert 'shotCursor%shots.size()' in c and 'budget-(jobs.empty()?0U:16U)' in c and 'budget-=before-shotBudget;' in c
    assert 'else if(path.volume)status=IrisNative::OverlapCapsule' in c
    assert 'scene->overlapCapsuleShapes(capsule,NX_ALL_SHAPES,64,batch,&collector,groups,0,true)' in n
    assert 'if(!hit.hitShape->checkOverlapSphere(initial))return Reject(ISSUE_HIT_RANGE' in n
    assert n.index('if(!Finite(hit.t))return Reject')<n.index('checkOverlapSphere(initial)')
    # 非重叠坏比例必须失败，只有真实初始重叠才恢复t=0，不能当正常穿墙。
    def fraction(t,overlap):
        if not math.isfinite(t):return None
        if t<0 or t>1.001:return 0 if overlap else None
        return min(1,t)
    assert [fraction(t,o) for t,o in [(-1,True),(-1,False),(2,False),(2,True),(.4,False),(float('nan'),True)]]==[0,None,None,0,.4,None]
    # 同一空间胶囊对静止/初始重叠仍应命中；旧球扫掠t=-1不能成为刀/钻体积的必要条件。
    def capsule(p,a,b,r):
        p,a,b=map(np.asarray,(p,a,b));d=b-a;u=np.clip(np.dot(p-a,d)/max(float(np.dot(d,d)),1e-12),0,1)
        return np.linalg.norm(p-a-u*d)<=r
    assert capsule([.5,0,5],[0,0,0],[0,0,10],1) and not capsule([1.01,0,5],[0,0,0],[0,0,10],1)
    assert capsule([0,0,0],[0,0,0],[0,0,0],1)
    moves=json.loads((ROOT/'docs/eight-moves.json').read_text('utf-8'))['moves'];windows=moves[4]['blade_windows']
    rows=(ROOT/'package/IrisArsenal/assets/blade_windows.csv').read_text('utf-8').splitlines();assert rows.pop(0)=='IRIS_BLADE_WINDOWS 1 3'
    for i,(w,row,e) in enumerate(zip(windows,rows,moves[4]['events'])):
        a,b,csv_end=map(float,row.split());assert int(a)==i and abs(b-w['begin'])<1e-8 and abs(csv_end-w['end'])<1e-8 and w['begin']<e['time']<w['end']
        assert w['source_id']==str(i+2)
    # 敌人在弧中间：只取末帧轴会漏；窗口覆盖中段且每次挥击只结算一次。
    angles=np.linspace(-math.pi/2,math.pi/2,61);target=np.array([0.,0.,60.]);axes=[np.array([math.sin(t),0.,math.cos(t)])*90 for t in angles]
    assert not capsule(target,[0,0,0],axes[-1],4) and any(capsule(target,[0,0,0],p,4) for p in axes)
    seen=set();health=[i for i,p in enumerate(axes) if capsule(target,[0,0,0],p,4) and 'enemy' not in seen and not seen.add('enemy')];assert len(health)==1
    # 直接用本次导出的真实源武器姿态和根位移验证，不仅测试合成圆弧。
    import port_math as m
    spec=moves[4];pose=np.loadtxt(ROOT/'docs/pose-proofs/iris_full_burst_weapon_proof_female.csv',skiprows=1)
    times=np.linspace(0,spec['duration'],len(pose));motion=np.asarray(spec['motion']);pose[:,2]+=np.interp(times,motion[:,0],motion[:,1]);actual=[]
    def point_segment(p,a,b):
        d=b-a;u=np.clip(np.dot(p-a,d)/max(float(np.dot(d,d)),1e-12),0,1);return float(np.linalg.norm(p-a-u*d))
    for n,w in enumerate(windows[:2]):
        idx=np.flatnonzero((times>=w['begin'])&(times<=w['end']));hit=int(np.argmin(abs(times-spec['events'][n]['time'])));target=np.array([0.,8.,40.])
        def endpoints(k):return pose[k,:3]+m.rotate(pose[k,3:7],[1.807138657,0,8.534358047]),pose[k,:3]+m.rotate(pose[k,3:7],[1.807138657,0,98.534358047])
        old_distance=point_segment(target,*endpoints(hit));new_distance=min(point_segment(target,*endpoints(k)) for k in idx)
        assert old_distance>spec['events'][n]['radius'] and new_distance<spec['events'][n]['radius'];actual.append({'phase':n,'old_single_frame_distance':old_distance,'window_distance':new_distance})
    assert 'bladeVictims[key].insert(*h).second' in c and 'TraceBladeWindows(i->first,a,weapon,t)' in c and 'if(e.kind==5)return true;' in c
    # 严查producer→文件头→C++消费者，避免新增第5条曲线后消费者仍只接受4条而加载失败。
    header=(ROOT/'package/IrisArsenal/assets/effect_curves.csv').read_text('utf-8').splitlines()[0].split()
    required=int(re.search(r'magic!=\"IRIS_FX_CURVES\"\|\|version!=1\|\|count!=(\d+)',c).group(1))
    assert int(header[2])==required==14 and 'blade windows timing mismatch' in c
    assert 'projectile_query_wait cast=' in c and 'other_shots_continue=1' in c and 's.retries=0;' in c
    assert 'raw_fraction="<<contacts.diagnostic.rawFraction' in c and 'DamageOutcome(r,int(result));' in c
    assert 's.speed=e.kind==6?800.f:e.kind==7?440.f:220.f;' in c
    assert 320*2.5==800 and 220*2==440
    # 本次只抑制钻天破原生反应，不产生第二条医疗、状态写入、强制动画或全局无敌。
    # 044将drill专属反应门推广到同一六招窗口；护甲/医疗不能被门吞掉。
    guard=c[c.index('int ProtectedMeleeMove('):c.index('void InstallDefenceGate(')]
    for token in ['!Iris::ActorReady(c)','c->isRagdoll()','PS_NORMAL','currentlyStumbling()','getChainedModeShackles()','BlockGuardMove(unsigned(move))','currentTechniqueHasFinished','_currentCombatTechnique!=technique','combat->_getHit(dir,damage,attacker,false)','originalMeleeStumble(self,dir,damage,part,attacker)']:assert token in guard,token
    for forbidden in ['setHealth','startCombatAnimation','setEnabled','setTimePosition','damage.multiply','addWound']:assert forbidden not in re.sub(r'//[^\n]*','',guard) # 注释说明原生医疗顺序不等于再次调用医疗。
    assert 'Native(&Character::_startStumble,' in main
    sdk=Path('E:/KenshiProject/1.Dependencies/KenshiLib_0.5.0')
    assert '_startStumble' in (sdk/'Include/kenshi/Character.h').read_text('utf-8-sig')
    assert b'?_startStumble@Character@@' in (sdk/'Libraries/KenshiLib.lib').read_bytes()
    # 真实Ogre脚本语法：不再仅检查括号平衡；不透明one zero，透明维持原alpha。
    allowed={'one','zero','src_colour','one_minus_src_colour','dest_colour','one_minus_dest_colour','src_alpha','one_minus_src_alpha','dest_alpha','one_minus_dest_alpha'}
    shorthand={'add','modulate','colour_blend','alpha_blend'}
    count=0
    for path in (ROOT/'package/IrisArsenal/assets').glob('*.material'):
        for row in re.findall(r'^\s*scene_blend\s+([^\r\n{}]+)',path.read_text('utf-8'),re.M):
            t=row.split();assert (len(t)==1 and t[0] in shorthand) or (len(t)==2 and set(t)<=allowed),(path,row);count+=1
    drill=(ROOT/'package/IrisArsenal/assets/iris_drill_optics.material').read_text('utf-8');assert 'scene_blend one zero' in drill and 'scene_blend replace' not in drill
    fx=json.loads((ROOT/'docs/eight-effects.json').read_text('utf-8'));fin=next(x for x in fx['assets'] if x['key']=='drill_blast');assert len(fin['materials'])==13
    assert len(fin['source_layers'])==2 and '非地震' in fin['limitations'];assert 'DamageOutcome(r,int(result));' in c
    # 昏迷与敌我采用独立资格门，在真实接触收集和原生医疗前均重核。原生远程选敌不被选项篡改。
    gate=c[c.index('bool DamageTarget('):c.index('// 只改变自有远程投射物')]
    assert 'Enemy(caster,victim)&&(damageUnconscious||!victim->medical.isUnconcious())' in gate
    assert 'if(DamageTarget(caster,victim))j.victims.insert(h);' in c and 'eligible=DamageTarget(caster,victim)&&caster->stats&&damageEnabled;' in c and 'if(!eligible){DamageOutcome(r,-1);continue;}' in c
    assert 'L"DamageUnconsciousTargets",L"1"' in c and 'unconscious!=0&&unconscious!=1' in c and 'unconsciousEnd==unconsciousText' in c
    def eligible(enemy,player,dead,unconscious,allow):return enemy and not player and not dead and (allow or not unconscious)
    eligibility=[]
    for allow in (False,True):
        for enemy,player,dead,unconscious in [(True,False,False,False),(True,False,False,True),(False,False,False,False),(True,True,False,False),(True,False,True,False)]:
            expected=enemy and not player and not dead and (allow or not unconscious)
            assert eligible(enemy,player,dead,unconscious,allow)==expected;eligibility.append(expected)
    # 同一敌人在查询后昏迷，关闭选项后医疗门必须再拒绝；趴地清醒不受该选项排除。
    assert eligible(True,False,False,False,False) and not eligible(True,False,False,True,False)
    import configparser
    ini=configparser.ConfigParser();ini.read(ROOT/'package/IrisArsenal/IrisArsenal.ini',encoding='utf-8');assert ini.getint('IrisArsenal','DamageUnconsciousTargets')==1
    assert 'const bool unavoidable=!RangedMove(r.move)&&moves[r.move].bypassDefence;' in c
    assert 'native_defence_not_observed cast=' in c and 'other_events_continue=1' in c
    # 实际FCS重武器类型与八个私有技巧同步，公共chance仍0，不能把所有重武器导入私有招式。
    import verify_prototype as base
    records=base.records(ROOT/'package/IrisArsenal/IrisArsenal.mod');weapon=base.fields(next(r for r in records if r['key']=='1-IrisArsenal.mod'))
    assert weapon['skill category']==3 and weapon['skill category animation override']==21
    for spec in moves:
        data=base.fields(next(r for r in records if r['key']==spec['technique']));assert data['heavy weapons'] and not data['polearm'] and data['chance']==0 and data['disabled']
    # 逐行沿源HKX提示→CSV→C++核对，不是只检查新文件是否存在。
    rows=(ROOT/'package/IrisArsenal/assets/effect_cues.csv').read_text('utf-8').splitlines();head=rows.pop(0).split();assert head[:2]==['IRIS_FX_CUES','1'] and len(rows)==int(head[2])<=64
    aliases={'PIE.$IrisBackfire':'backfire','PIE.$IrisAnim':'gun','PIE.$IrisOffAll':'off','PIE.$IrisExplosion':'ignition','PIE.$IrisCharge3':'charge_halo','PIE.$IrisEXDrill2':'wing','PIE.$IrisEXDrillOFF':'wing_off'}
    expected=sorted(set((s['index'],aliases[e['text']],round(e['time']+(.02 if e['text']=='PIE.$IrisEXDrill2' else 0),9)) for s in moves for e in s['source_events'] if s['index']!=9 and e['text'] in aliases))
    actual_cues=sorted((int(row.split()[0]),row.split()[1],float(row.split()[2])) for row in rows);assert actual_cues==expected
    assert 'cueCount>64' in c and 'CueAge(a,"backfire",t)' in c and 'a.exhaust.Draw(w,exhaustAge,1.f)' in c
    assert 'offAge<0||offAge>chargeAge' in c # 先前0.033s清理不能隐藏0.889s后才出生的光层。
    assert 'a.halo.Clear(alive)' in c and 'a.ignition.Clear(alive)' in c and 'a.halo.Hide();a.ignition.Hide();' in c
    # 折射辅助壳不是合法不透明爆炸。实际序列化子材质必须全透明，不准用one-zero顶替场景折射。
    assert all('explosionwarm0' not in x['file'] for x in fin['source_layers']) # 037终结不再借地震/折射球壳
    assert all(not fx['materials'][name]['opaque'] and fx['materials'][name]['blend']!='one zero' for name in fin['materials'])
    # 真实曲线/顶点测量火焰高度：水平R36不变，两条主体火焰比035约4.7升至25.92单位。
    tokens=(ROOT/'package/IrisArsenal/assets/effect_curves.csv').read_text('utf-8').split();at=3;fire_heights={}
    for _ in range(int(tokens[2])):
        name=tokens[at];subs,n=int(tokens[at+1]),int(tokens[at+2]);at+=5;values=np.array(list(map(float,tokens[at:at+subs*n*25]))).reshape(subs,n,25);at+=subs*n*25
        if name!='shock':continue
        verts,_=base.mesh(ROOT/('package/IrisArsenal/assets/iris_fx_'+name+'.mesh'),48,True);heights=[]
        for p,tr in zip(verts,values):
            clouds=[p@v[13:].reshape(3,4)[:,:3].T+v[13:].reshape(3,4)[:,3] for v in tr];points=np.concatenate(clouds)
            assert .999<np.linalg.norm(points[:,[0,2]],axis=1).max()<1.001;heights.append(float(points[:,1].max()))
        assert abs(heights[4]-.72)<1e-4 and abs(heights[5]-.72)<1e-4;fire_heights[name]=heights
    assert 'move==0?"roll_blast":move==4?"full_blast"' in c and 'r.key=="shock"||r.key=="fire_blast"' in c
    assert len(next(x for x in fx['assets'] if x['key']=='charge_halo')['materials'])==5
    assert len(next(x for x in fx['assets'] if x['key']=='fire_blast')['materials'])==8
    return {'FIFO_fault':{'old_completed':len(old),'new_completed':len(new),'failed_event_retained':True},'full_burst_windows':windows,'one_health_per_enemy_per_window':True,'actual_exported_full_burst_cases':actual,'reserved_health_queries_with_64_shots':health_progress,'speeds':{'vulcan':800,'pulse':440},'melee_immunity':'six private live melee moves; combo/ranged/health/death/unconscious unchanged','Ogre_blend_statements_checked':count,'finisher_layers':13,'original_ALS_files_missing':False,'enemy_unconscious_cases':eligibility,'weapon_category':3,'source_cues':actual_cues,'fire_canonical_heights':fire_heights,'charge3_source_layers':5,'C++_compiled':False,'game_run':False}
if __name__=='__main__':print(json.dumps(verify_combat036(),ensure_ascii=False,indent=2))
