"""038验收：用实际翼片顶点/动画、序列化粒子和纹理检查中心/球体覆盖；不是GPU实机测试。"""
import json,math
from pathlib import Path
import numpy as np
from PIL import Image
from safeio import ROOT
from test_drill_visibility import buffers,curves,alpha_at
import verify_prototype as base

def field_coverage(layer,spec,assets,age):
    # 正交相机下按实际GPU卡片转角、尺寸、动态图集和贴图alpha采样。
    # 不考虑深度/透视/场景遮挡，检验的是空间布局是否有固有空洞，不代表游戏最终亮度。
    image=np.asarray(Image.open(assets/spec['texture']).convert('RGBA'),float)/255
    h,w=image.shape[:2];gold=math.pi*(3-math.sqrt(5));coverage=[]
    for k in range(12):
        y=1-2*(k+.5)/12;r=math.sqrt(1-y*y);forward=np.array([r*math.cos(k*gold),y,r*math.sin(k*gold)])
        right=np.cross(forward,[0,1,0]);right/=np.linalg.norm(right);up=np.cross(right,forward)
        theta=np.arange(192)*math.tau/192
        # 包括半径95%的边界和内层，不能只验证中心一个像素。
        target=np.concatenate([np.c_[np.cos(theta)*rr,np.sin(theta)*rr] for rr in (0,.25,.5,.75,.95)])
        transmission=np.ones(len(target))
        for p in layer['particles']:
            dt=age-p[6]
            if not 0<=dt<p[7]:continue
            t=dt/p[7];size=p[8]*np.interp(t,np.linspace(0,1,5),spec['size_curve'])
            center=np.asarray(p[:3])+np.asarray(p[3:6])*dt
            q=(target-[center@right,center@up])/size;c,s=math.cos(p[9]),math.sin(p[9])
            uv=np.c_[q[:,0]*c+q[:,1]*s,-q[:,0]*s+q[:,1]*c]*.5+.5
            inside=np.all((uv>=0)&(uv<=1),1);frame=min(spec['atlas']**2-1,int(t*spec['atlas']**2))
            uv=(uv+[frame%spec['atlas'],frame//spec['atlas']])/spec['atlas'];uv=uv*np.array(spec['uv'][2:])+spec['uv'][:2]
            # 材质t0默认wrap，LUT是独立clamp单元；这里只采alpha，保留相同取样地址行为。
            ix=np.minimum(w-1,(uv[:,0]%1*w).astype(int));iy=np.minimum(h-1,(uv[:,1]%1*h).astype(int))
            a=image[iy,ix,3]*alpha_at(spec,t)*spec['base_color'][3]
            a=np.minimum(1,np.maximum(0,a)**spec['profile'][0]*spec['profile'][1])*inside
            transmission*=1-a
        a=1-transmission;coverage.append({'view':k,'fraction_above_0_025':float(np.mean(a>=.025)),'minimum':float(a.min()),'p10':float(np.quantile(a,.1))})
    assert min(x['fraction_above_0_025'] for x in coverage)>.97,coverage
    assert max(x['p10'] for x in coverage)<.65,'透明蓝层不能再叠成实心白幕'
    return {'age':age,'views':12,'points_per_view':len(target),'coverage':coverage,'limitations':'正交alpha布局模型，未模拟实际GPU、深度遮挡或透视'}

def verify_r120():
    a=ROOT/'package/IrisArsenal/assets';doc=json.loads((ROOT/'docs/eight-effects.json').read_text('utf8'));burst=json.loads((ROOT/'docs/drill-burst-041.json').read_text('utf8'))
    wing=next(x for x in doc['assets'] if x['key']=='drill_wings');points,mats=base.mesh(a/'iris_fx_drill_wings.mesh',48,True)
    states,duration,_=curves(a/'effect_curves.csv','drill_wings')
    text=(a/'wing_centers.csv').read_text('utf8').splitlines();header=text.pop(0).split();assert header[:2]==['IRIS_WING_CENTERS','1']
    count=int(header[2]);begin,end=map(float,header[3:]);centers=np.array([[float(v) for v in row.split()] for row in text])
    assert centers.shape==(count,3) and count==states.shape[1] and abs(end-begin-duration)<1e-8
    errors=[]
    # 每一帧用真正序列化的十形状计算两翼完整包围中心，不只检查JSON或骨原点。
    for frame in range(count):
        grouped={}
        for p,layer,s in zip(points,wing['layers'],states):
            m=s[frame,13:].reshape(3,4);q=p@m[:,:3].T+m[:,3];lo,hi=q.min(0),q.max(0)
            name=layer['bone']
            if name in grouped:lo=np.minimum(lo,grouped[name][0]);hi=np.maximum(hi,grouped[name][1])
            grouped[name]=(lo,hi)
        expected=sum((lo+hi)*.5 for lo,hi in grouped.values())*.5
        errors.append(float(np.linalg.norm(centers[frame]-expected)))
    assert max(errors)<2e-5,max(errors)
    spec=json.loads((ROOT/'docs/eight-moves.json').read_text('utf8'))['moves'][3]
    hit=[e for e in spec['events'] if e['kind']=='heavy_shell'];assert len(hit)==1 and hit[0]['radius']==120 and hit[0]['multiplier']==5
    t=hit[0]['time'];assert begin<t<end
    cues=(a/'effect_cues.csv').read_text('utf8').splitlines()
    wing_cue=next(float(row.split()[2]) for row in cues[1:] if row.split()[:2]==['3','wing'])
    assert abs(wing_cue-begin)<1e-8

    x=(t-begin)/(end-begin)*(count-1);i=int(x);local=centers[i]*(1-(x-i))+centers[i+1]*(x-i)
    code=(ROOT/'IrisCombat.cpp').read_text('utf8')
    emit=code[code.index('if(a.move==3&&e.kind==4)'):code.index('if(e.kind==2)return Blast')]
    assert 'WingCenter(clipTime,weapon,a.origin)' in emit and 'center,e.radius,e.mult' in emit and 'return true;' in emit and 'Shot' not in emit
    blast=code[code.index('bool Blast('):code.index('void Swing(')]
    assert 'r.pos=p;r.radius=radius' in blast and 'Path(p,p,radius,true)' in blast and blast.count('PushJob(j)')==1
    assert 'r.key=="drill_blast"?r.radius:r.radius/assets[r.key].peak' in code
    assert 'wing centers timeline mismatch' in code and 'wing centers cue mismatch' in code
    assert 'scene->overlapSphereShapes(sphere,NX_ALL_SHAPES' in (ROOT/'native/NativeMultiContact.cpp').read_text('utf8')
    assert code.count('->_NV_hitByMeleeAttack(')==1
    table=dict(buffers(a/'iris_fx_drill_blast.mesh'));source_count=0
    for group in ('blue','fire'):
        source_count+=sum(len(l['particles']) for l in burst[group]['layers'])
    assert 100<source_count<1024
    coverage=burst['coverage'];assert coverage['reference_radius']==1 and coverage['particle_count']==49 and coverage['additional_draw_calls']==1
    evidence=[]
    for l in coverage['layers']:
        ps=np.array(l['particles']);actual=table[l['material']][::4,:10];assert len(actual)==49 and np.allclose(actual,ps,atol=1e-6)
        assert np.linalg.matrix_rank(ps[:,:3])==3 and np.allclose(np.linalg.norm(ps[7:,:3],axis=1),.82)
        d=doc['materials'][l['material']];assert d['coverage_field'] and d['blend']!='one zero' and 'burstProfile' in (a/'iris_eight.material').read_text('utf8')
        if d['ion_blue']:assert max(ps[:,6]+ps[:,7])<=.520001;age=.22
        else:assert min(ps[:,6])>=.56;age=1.12
        evidence.append(field_coverage(l,d,a,age))
    # 实际源电环（非包围球）在有alpha的样本上达到单位半径，对应世界R120。
    v,_,_=curves(a/'effect_curves.csv','drill_blast');reach=0
    import author_prototype as author
    source_meshes,_=author.read_nif(Path(burst['blue']['source']))
    ring_index=next(i for i,m in enumerate(source_meshes) if m['name']=='Torus01:0')
    ring_material=list(table)[ring_index]
    for (name,p),s in zip(table.items(),v):
        if name!=ring_material:continue
        for row in s:
            if row[3]<.2:continue
            m=row[13:].reshape(3,4);q=p[:,:3]@m[:,:3].T+m[:,3];reach=max(reach,float(np.linalg.norm(q[:,[0,2]],axis=1).max()))
    assert .9999<reach<1.0001,reach
    return {'contract':'IRIS_EIGHT_042','radius':120,'damage_events':1,'damage_multiplier':5,'instant':True,'projectile':False,'wing_geometry_center_samples':count,'wing_center_max_error':max(errors),'firing_center_relative_weapon':local.tolist(),'center_space':'完整源翼片几何中心中点，乘当帧武器矩阵加浮动世界原点，发射时快照','source_particles':source_count,'coverage_particles':49,'total_particles':source_count+49,'blue_coverage_draw_calls':1,'ring_visible_radius':reach*120,'coverage_models':evidence,'Cxx_or_HLSL_compiled':False,'game_verified':False}

if __name__=='__main__':print(json.dumps(verify_r120(),ensure_ascii=False,indent=2))
