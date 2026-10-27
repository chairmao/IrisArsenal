"""034九点修正的实际资产与边界验证；仅Python/序列化/语法，不声称C++或GPU已运行。"""
from pathlib import Path
import json,math,re
import numpy as np
from safeio import ROOT
import verify_prototype as base
import port_math as m

def verify_optics():
    A=ROOT/'package/IrisArsenal/assets';fx=json.loads((ROOT/'docs/eight-effects.json').read_text('utf-8'));assets={x['key']:x for x in fx['assets']}
    moves=json.loads((ROOT/'docs/eight-moves.json').read_text('utf-8'))['moves'];C=(ROOT/'IrisCombat.cpp').read_text('utf-8')
    # 实际序列化的源ShockRing应处于XY平面，即法向Z；三层仍保留完整源顶点和同一个真实球心。
    p,_=base.mesh(A/'iris_fx_shell.mesh',48);q=p[0];_,_,axes=np.linalg.svd(q-q.mean(0));normal=axes[-1]
    assert abs(normal[2])>.999 and np.ptp(q[:,2])<.25 and np.ptp(q[:,0])>12
    directions=[[0,0,1],[1,0,0],[.3,-.4,.8660254],[0,1,0]]
    for ray in directions:
        ray=np.array(ray,dtype=float);ray/=np.linalg.norm(ray);qq=m.from_to([0,0,1],ray);nn=m.rotate(qq,normal)
        assert abs(np.dot(nn,ray))>.999
    assert fx['optics034']['pulse_disc_normal']=='canonical +Z'
    # 水平范围校准使用真实六层、每层121帧，不以静止包围盒冒称最亮火环大小。
    tokens=(A/'effect_curves.csv').read_text('utf-8').split();at=3;states={}
    for _ in range(int(tokens[2])):
        key=tokens[at];subs,n=int(tokens[at+1]),int(tokens[at+2]);at+=5
        states[key]=np.array(list(map(float,tokens[at:at+subs*n*25]))).reshape(subs,n,25);at+=subs*n*25
    points,_=base.mesh(A/'iris_fx_shock.mesh',48,True);radius=[]
    for p,track in zip(points,states['shock']):
        largest=0
        for v in track:
            t=v[13:].reshape(3,4);q=p@t[:,:3].T+t[:,3];largest=max(largest,float(np.linalg.norm(q[:,[0,2]],axis=1).max()))
        assert .9999<largest<=1.0001;radius.append(largest*36)
    assert 'float size=r.radius;' in C and fx['timelines']['shock']['ground_normalization']['horizontal_radius']==1
    assert all(e['radius']==36 for e in moves[2]['events']) and all(e['radius']==9 for e in moves[7]['events'])
    # 四次落锤的实际序列化Prop2和枪口，双性别锤头距脚底均0.6；不写运行时骨/位置。
    heights={}
    for sex in ['male','female']:
        spec=moves[2];bones,le,tracks=base.skeleton(A/('iris_action_earthquake_'+sex+'.skeleton'),spec['animation']);bn={b['name']:b['id'] for b in bones};values=[]
        for event in spec['events']:
            k=round(event['time']/le*(spec['frames']-1));world=[]
            for b in bones:
                v=tracks[b['id']][k] if b['id'] in tracks else (0,0,0,0,1,0,0,0);q=m.qmul(b['orientation'],(v[4],v[1],v[2],v[3]));p=m.vadd(b['position'],v[5:]);par=b['parent']
                if par>=0:pp,pq=world[par];p=m.vadd(pp,m.rotate(pq,p));q=m.qmul(pq,q)
                world.append((p,q))
            p,q=world[bn['Bip01 Prop2']];q=m.qmul(q,m.axis((1,0,0),-90));head=np.asarray(p)+m.rotate(q,[1.807138657,0,8.534358047]);floor=min(world[bn['Bip01 '+side+' Foot']][0][1] for side in ['L','R'])
            values.append(float(head[1]-floor));assert .59<head[1]-floor<.61
        heights[sex]=values
    # 独立命中语义反例：透明对象后面的敌人与墙仍须保留，中立仍可挡；本模型不冒充PhysX执行。
    def first(contacts):
        for fraction,kind in sorted(contacts):
            if kind in ('self','player','ally'):continue
            return kind
        return None
    cases=[([(0,'self'),(.1,'ally'),(.3,'enemy')],'enemy'),([(.1,'player'),(.2,'wall'),(.4,'enemy')],'wall'),([(.1,'ally'),(.2,'neutral'),(.4,'enemy')],'neutral'),([(.1,'ally'),(.2,'player')],None),([(.1,'enemy'),(.4,'ally')],'enemy')]
    for contacts,expected in cases:assert first(contacts)==expected
    section=C[C.index('bool IgnoreRangedContact('):C.index('Matrix4 Pose(')]
    for token in ['victim==caster','victim->isPlayerCharacter()','caster->isAlly(victim,false)','victim->isAlly(caster,false)']:assert token in section
    sweep=C[C.index('void AdvanceEffects('):C.index('void EnsureMoves(')]
    assert sweep.index('IgnoreRangedContact(caster,c)')<sweep.index('hit=true;blocker=h;')
    assert 'RangedMove(s.move)&&IgnoreRangedContact' in sweep and 'world_geometry=' in sweep and 'ignored_friendly_shapes=' in sweep
    deps=Path('E:/KenshiProject/1.Dependencies/KenshiLib_0.5.0');header=(deps/'Include/kenshi/Character.h').read_text('utf-8-sig')
    assert re.search(r'virtual bool isAlly\(Character\* who, bool factorInDisguises\)',header)
    assert b'?isAlly@Character@@' in (deps/'Libraries/KenshiLib.lib').read_bytes()
    # 原生光炮墙查询已跳过所有角色，所以盟友不会裁短；伤害仍有独立enemy/玩家保护。
    native=(ROOT/'native/NativeMultiContact.cpp').read_text('utf-8');assert 'key.type==unsigned(CHARACTER))return true;' in native and 'caster->isEnemy(victim,false)' in C
    beam,_=base.mesh(A/'iris_fx_beam.mesh',48,True);ion,_=base.mesh(A/'iris_fx_ion.mesh',48,True)
    assert len(beam)==3 and len(states['beam'])==3 and len(ion)>11
    assert all(np.ptp(p[:,2])==1 for p in beam)
    assert all(len(p)==1757 for p in beam) # 059真实闭合圆柱；源炮体/准星与蓝火另由059核对。
    hlsl=(A/'iris_eight.hlsl').read_text('utf-8');assert 'min(clock.w,240)/clock.w' in hlsl and 'if(presentation.z>.5)' in hlsl
    assert 'a.ion.Clear(alive)' in C and 'else a.ion.Hide();' in C and 'r.age,alpha,r.length' in C
    assert all(s['weight']==1 for s in moves)
    return {'pulse_disc_normal':normal.tolist(),'disc_direction_cases':len(directions),'quake_horizontal_layers_radius':radius,'hammer_head_above_foot_by_sex':heights,'beam_radius':9,'beam_layers':{'external_CC0_closed_cylinders':3},'muzzle_ion':'059 actual EXanim1 reticle/cannon and original blue/fire layers','friendly_collision_cases':len(cases),'unchanged_native_pre_shot_LOS_gate':True,'ground_obstruction_retained':True,'all_8_weights':1,'C++_GPU_or_game_executed':False}
if __name__=='__main__':print(json.dumps(verify_optics(),ensure_ascii=False,indent=2))
