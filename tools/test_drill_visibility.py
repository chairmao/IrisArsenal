"""终结可见性回归：读取实际GPU顶点/时间流/材质；不编译，不冒称实机渲染通过。"""
import json,struct
import numpy as np
from safeio import ROOT
from verify_prototype import chunks

def buffers(path):
    raw=path.read_bytes();out=[]
    for typ,s,e in chunks(raw,raw.index(b'\n')+1,len(raw)):
        assert typ==0x3000
        for typ,s,e in chunks(raw,s+1,e):
            if typ!=0x4000:continue
            nl=raw.index(b'\n',s);name=raw[s:nl].decode();shared,n,wide=struct.unpack_from('<?I?',raw,nl+1)
            assert not shared
            for typ,s,e in chunks(raw,nl+7+n*(4 if wide else 2),e):
                assert typ==0x5000
                for typ,s,e in chunks(raw,s+4,e):
                    if typ!=0x5200:continue
                    binding,stride=struct.unpack_from('<HH',raw,s);assert binding==0 and stride in (48,52)
                    for typ,s,e in chunks(raw,s+4,e):
                        assert typ==0x5210
                        out.append((name,np.frombuffer(raw[s:e],'<f4').reshape(-1,stride//4).copy()))
    return out

def curves(path,key):
    rows=path.read_text('utf8').split();at=3
    for _ in range(int(rows[2])):
        name,n,s=rows[at],int(rows[at+1]),int(rows[at+2]);dur,peak=map(float,rows[at+3:at+5]);at+=5
        values=np.array(list(map(float,rows[at:at+n*s*25]))).reshape(n,s,25);at+=n*s*25
        if name==key:return values,dur,peak
    raise AssertionError(key)

def alpha_at(d,t,old=False):
    # 用源颜色alpha端点和fade百分比独立核对寿命；RGB变化不应让中段透明度先变成零。
    c=np.asarray(d['colors']);a,b,x,y=d['intervals']
    if old:
        v=c[0]*(1-np.clip((t-a)/max(.001,b-a),0,1))+c[1]*np.clip((t-a)/max(.001,b-a),0,1) if t<b else c[1] if t<x else c[1]*(1-np.clip((t-x)/max(.001,y-x),0,1))+c[2]*np.clip((t-x)/max(.001,y-x),0,1)
        return v[3]*min(1,t/max(.001,d['fade_in']))*min(1,(1-t)/max(.001,d['fade_out']))
    if t<d['fade_in']:return np.interp(t,[0,d['fade_in']],[c[0,3],c[1,3]])
    if t>1-d['fade_out']:return np.interp(t,[1-d['fade_out'],1],[c[1,3],c[2,3]])
    return c[1,3]

def verify_visibility():
    a=ROOT/'package/IrisArsenal/assets';doc=json.loads((ROOT/'docs/eight-effects.json').read_text('utf8'));burst=json.loads((ROOT/'docs/drill-burst-041.json').read_text('utf8'))
    assert burst['visibility_revision']=='041-RangeMetal'
    v,duration,peak=curves(a/'effect_curves.csv','drill_blast');dt=duration/(v.shape[1]-1)
    active=np.max(v[:3,:,:3],2)>.01;active&=v[:3,:,3]>.02
    blue_seconds=active.any(0).sum()*dt
    assert blue_seconds>.30,(blue_seconds,'蓝闪不能在0.1秒内消失')
    raw_layers=list(buffers(a/'iris_fx_drill_blast.mesh'));table=dict(raw_layers);count=0;largest=0
    by_material={}
    for name,data in raw_layers:by_material.setdefault(name,[]).append(data)
    for group in ('blue','fire'):
        for layer in burst[group].get('render_layers',burst[group]['layers']):
            data=by_material[layer['material']].pop(0);ps=np.asarray(layer['particles']);d=doc['materials'][layer['material']]
            assert len(data)==len(ps)*4 and np.isfinite(data).all()
            assert np.allclose(data[::4,:10],ps,atol=1e-6)
            # 生产者布局到消费者COLOR四浮点约定：birth/life/radius/angle不可丢失或归一到0..1。
            assert np.allclose(data[::4,6:10],ps[:,6:10],atol=1e-6)
            assert np.allclose(np.diff(data.reshape(-1,4,12)[:,:,:10],axis=1),0)
            assert d['grey_color']==bool(d['has_palette'] and d['shader_flags'][0]&16)
            assert d['grey_alpha']==bool(d['has_palette'] and d['shader_flags'][0]&32)
            assert len(d['base_color'])==4
            assert alpha_at(d,.55)>.05,(layer['name'],'中段透明度错误归零')
            if group=='blue':assert np.all(ps[:,6]+ps[:,7]<=.520001)
            else:assert np.all(ps[:,6]>=.56-1e-6)
            count+=len(ps)
            for p in ps:
                for t in np.linspace(0,p[7],11):
                    q=p[:3]+p[3:6]*t;radius=p[8]*np.interp(t/p[7],np.linspace(0,1,5),layer['size_curve'])*np.sqrt(2)
                    largest=max(largest,float(np.linalg.norm(np.abs(q)+radius)))
    assert 100<count<1024
    scales={l['name']:l['source_parameters']['system_scale'] for l in burst['fire']['layers']}
    assert all(abs(v-1)<1e-5 for v in scales.values())
    # 039使用更清楚的原生32帧火球，单张尺度有界；不再用R86卡片填满球体。
    glare=next(l for l in burst['fire']['layers'] if l['name'].startswith('FlamesTall03'))
    assert glare['atlas_grid']==[8,4,32] and max(p[8] for p in glare['particles'])/burst['fire']['coverage_calibration']['uniform_scale']<.5
    raw=(a/'iris_fx_drill_blast.mesh').read_bytes();bound=struct.unpack('<7f',raw[-28:])
    assert largest<=bound[6]+1e-5
    shader=(a/'iris_eight.hlsl').read_text('utf8');mat=(a/'iris_eight.material').read_text('utf8')
    assert 'clip(i.c.a-.00001)' in shader and 'color.a=(t<fades.x?' in shader
    assert mat.count('param_named burstTint float4')==16 # 049新增原824火花一层，旧十五层保持
    assert mat.count('vertex_program_ref IrisBurstCardVP')==3 # 原终结两层＋原电脉Glow一层
    program=(a/'iris_eight.program').read_text('utf8')
    assert 'inverse_worldview_matrix' in program and 'param_named_auto vp viewproj_matrix' not in program
    # 源两层必须从CPU薄片变为相机卡片，包围球要覆盖中心偏移+任意转向半径。
    for (name,points),states in zip(table.items(),v):
        spec=doc['materials'][name]
        if 'burst_card_center' not in spec:continue
        for state in states:
            m=state[13:].reshape(3,4);p=points[:,:3]@m[:,:3].T+m[:,3]
            pivot=np.asarray(spec['burst_card_center'])@m[:,:3].T+m[:,3]
            radius=np.linalg.norm(pivot)+np.linalg.norm(p-pivot,axis=1).max()
            assert radius<=bound[6]+1e-5,(name,radius,bound[6])
    for name in table:
        if '/DrillBurst/' in name:
            block=mat.split('material '+name+'\n',1)[1].split('\nmaterial ',1)[0]
            assert 'tex_address_mode clamp' in block
    return {'revision':'041-RangeMetal','blue_visible_game_seconds':blue_seconds,'particles':count,'max_particle_envelope':largest,'culling_radius':bound[6],'fire_source_scales':scales,'fire_max_card_halfsize_world':max(p[8] for p in glare['particles'])*120,'Cxx_or_HLSL_compiled':False,'game_render_verified':False}
if __name__=='__main__':print(json.dumps(verify_visibility(),ensure_ascii=False,indent=2))
