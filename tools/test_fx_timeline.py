# 047新增源electro_area，所有13类曲线仍逐层验证GPU包络/有限数/绑定/源哈希。
"""031针对新源资源的序列化/有界曲线/材质接口检查，不运行游戏或任何编译器。"""
from pathlib import Path
import json,configparser,hashlib,struct
import numpy as np
from safeio import ROOT
import verify_prototype as base

def verify_fx_timeline():
    A=ROOT/'package/IrisArsenal/assets';doc=json.loads((ROOT/'docs/eight-effects.json').read_text('utf-8'));assets={x['key']:x for x in doc['assets']}
    assert len(assets['pulse_blast']['materials'])==4 and Path(assets['pulse_blast']['source']).name=='RimMagicdlc1aurielsskyboltexplosion01.nif'
    data=(A/'effect_curves.csv').read_text('utf-8').split();assert data[:3]==['IRIS_FX_CURVES','1','14'];at=3;result={}
    for _ in range(14):
        key=data[at];subs,n=int(data[at+1]),int(data[at+2]);duration,peak=float(data[at+3]),float(data[at+4]);at+=5
        assert key in ('pulse_blast','beam','exhaust','shock','drill_blast','fire_blast','charge_halo','drill_wings','muzzle_fire','roll_blast','full_blast','electro_burst','electro_area','ion') and key not in result and 2<=n<=241 and subs==len(assets[key]['materials'])
        values=np.array(list(map(float,data[at:at+subs*n*25]))).reshape(subs,n,25);at+=subs*n*25
        assert np.isfinite(values).all() and abs(values).max()<1e6 and 0<duration<=8 and peak>0
        vertices,mats=base.mesh(A/('iris_fx_'+key+'.mesh'),52 if key=='muzzle_fire' else 48,True);lo=np.full(3,np.inf);hi=np.full(3,-np.inf);largest=0
        for p,states in zip(vertices,values):
            for state in states:
                m=state[13:].reshape(3,4);q=np.asarray(p)@m[:,:3].T+m[:,3]
                lo=np.minimum(lo,q.min(0));hi=np.maximum(hi,q.max(0));largest=max(largest,float(np.linalg.norm(q,axis=1).max()))
        assert largest<=peak+.002,(key,largest,peak)
        # 尾部9000包围块必须覆盖Shader动态后的所有源顶点，不能只包住静止网格。
        raw=(A/('iris_fx_'+key+'.mesh')).read_bytes();typ,size=struct.unpack('<HI',raw[-34:-28]);bounds=struct.unpack('<7f',raw[-28:]);assert typ==0x9000 and size==34
        assert np.all(lo>=np.array(bounds[:3])-.002) and np.all(hi<=np.array(bounds[3:6])+.002)
        source=Path(assets[key]['source']);assert hashlib.sha256(source.read_bytes()).hexdigest()==assets[key]['sha256']
        changed=[k for k in range(25) if np.ptp(values[:,:,k])>1e-4]
        assert changed or key=='muzzle_fire' and assets[key].get('particle_mesh') or key=='beam' and assets[key].get('external_CC0'),(key,'除粒子年龄驱动附件外，曲线不能恒定')
        result[key]={'layers':subs,'samples':n,'source_seconds':duration,'peak_radius':peak,'channels_changed':changed}
    assert at==len(data)
    pulse=result['pulse_blast'];assert pulse['source_seconds']==3 and pulse['layers']==4
    ini=configparser.ConfigParser();ini.read(ROOT/'package/IrisArsenal/IrisArsenal.ini',encoding='utf-8');assert ini.getfloat('IrisArsenal','RangedActionInterval')==1
    enabled={k for k,v in ini['MoveWeights'].items() if float(v)>0};assert enabled=={'fire_roll','spiral','earthquake','drill','full_burst','vulcan','pulse','drive','electro_cannon','hammer_combo'}
    moves=json.loads((ROOT/'docs/eight-moves.json').read_text('utf-8'))['moves']
    for i in (5,6,7):assert [moves[i]['attack_min'],moves[i]['attack_max']]==[0,10000]
    assert len(moves[1]['events'])==3 and all(e['kind']=='weapon' for e in moves[1]['events'])
    assert len(moves[7]['events'])==4 and all(e['kind']=='beam' for e in moves[7]['events'])
    combat=(ROOT/'IrisCombat.cpp').read_text('utf-8');shader=(A/'iris_eight.hlsl').read_text('utf-8');program=(A/'iris_eight.program').read_text('utf-8')
    assert 'version!=4||count!=20' in combat and 'samples>241' in combat and 'struct FxState {float value[25];};' in combat
    assert 'a.flash.Clear(alive)' in combat and 'a.flash.Hide();' in combat
    assert 'residues[n].cast==a.id' in combat and 'r.length=length;' in combat
    assert 's.collisionRadius=e.kind==6?e.radius:e.kind==7?4.5f' in combat
    for token in ['sourceTint','sourceUV','sourceMisc','sourceFalloff','delta0','delta1','delta2']:assert token in shader and token in (program+(A/'iris_eight.material').read_text('utf-8'))
    trail=program.split('vertex_program IrisTrailVP hlsl',1)[1].split('fragment_program IrisTrailFP',1)[0];assert 'custom' not in trail
    # 对动作之外的普通武器、原生装填计时/命中路径不引入新钩子和重复伤害入口。
    assert combat.count('->_NV_hitByMeleeAttack(')==1
    return {'serialized_source_timelines':result,'pulse_radius':{'body':4.5,'blast':36},'ranged_FCS':[0,10000],'weights':sorted(enabled),'ranged_interval':1,'source_particle_runtime_ported':False,'GPU_compiled':False,'game_tested':False}
if __name__=='__main__':print(json.dumps(verify_fx_timeline(),ensure_ascii=False,indent=2))
