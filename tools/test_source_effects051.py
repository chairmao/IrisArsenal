"""051源几何/纹理/原颜色边界/实际CPU产物回归；不编译或启动游戏。"""
from pathlib import Path
import json,hashlib
import numpy as np
from safeio import ROOT
from historical047 import assert_047_hash,package_hash052
from test_drill_visibility import buffers,curves

def color_update(t,colors,intervals,fadein,fadeout):
    # 独立按本机原Update的分支顺序表达，包含零宽第二颜色段与fadeOut=0；不是修正后的Shader源码解析器。
    c0,c1,c2=np.asarray(colors);a,b,c,d=intervals
    if b!=a and t<b:rgb=c0[:3] if t<a else c0[:3]+(c1[:3]-c0[:3])*(t-a)/(b-a)
    elif d!=c and t>c:rgb=c2[:3] if t>d else c1[:3]+(c2[:3]-c1[:3])*(t-c)/(d-c)
    else:rgb=c1[:3]
    alpha=c1[3]
    if fadeout!=0 and t>fadeout:alpha=c1[3]+(c2[3]-c1[3])*(t-fadeout)/(1-fadeout)
    elif fadein!=0 and t<fadein:alpha=c0[3]+(c1[3]-c0[3])*t/fadein
    return np.r_[rgb,alpha]

def verify_source051():
    A=ROOT/'package/IrisArsenal/assets';e=json.loads((ROOT/'docs/source-effects-051-evidence.json').read_text('utf8'));doc=json.loads((ROOT/'docs/eight-effects.json').read_text('utf8'))
    sha=lambda p:package_hash052(p) if p.resolve().is_relative_to((ROOT/"package/IrisArsenal").resolve()) else hashlib.sha256(p.read_bytes()).hexdigest()
    # 原native的零宽区间失败负例：旧shader在0.5处跳亮橙，原Update必须保持中暗色。
    muzzle=json.loads((ROOT/'docs/muzzle-fire-042.json').read_text('utf8'));glow=next(l for l in muzzle['layers'] if l['name']=='pFireGlow');d=doc['materials'][glow['material']]
    assert d['intervals']==[0.0,.30000001192092896,0.0,0.0]
    for t in (.31,.5,.9):assert np.allclose(color_update(t,d['colors'],d['intervals'],d['fade_in'],d['fade_out'])[:3],d['colors'][1][:3])
    assert abs(color_update(.5,d['colors'],d['intervals'],d['fade_in'],d['fade_out'])[3]-(.5/(1-d['fade_out'])))<1e-7
    assert np.allclose(color_update(.8,d['colors'],d['intervals'],0,0),d['colors'][1])
    assert not np.allclose(d['colors'][1][:3],d['colors'][2][:3])
    shader=(A/'iris_eight.hlsl').read_text('utf8');body=__import__('test_melee_block043').function(shader,'iris_muzzle_vp')
    assert 'intervals.w!=intervals.z' in body and '(fades.y>0 && t>fades.y)?alphaOut' in body
    assert '(t-fades.y)/max(.001,1-fades.y)' in body and 't>1-fades.y?alphaOut' not in body
    assert len(muzzle['trigger_times'])==20 and len(muzzle['layers'])==5
    for rel,digest in e['preserved_files'].items():assert_047_hash('root:'+rel,sha(ROOT/rel),digest)
    for rel,digest in e['preview_inputs'].items():assert_047_hash('root:'+rel,sha(ROOT/rel),digest)
    for rel,digest in e['preview_outputs'].items():assert sha(ROOT/rel)==digest,rel
    coverage=json.loads((ROOT/'docs/electro-source-049.json').read_text('utf8'))['coverage051'];factor=coverage['old_geometric_radius']/coverage['reference_radius'];assert 1.4<factor<1.7
    assert '64 deterministic barycentric' in coverage['method'] and coverage['added_textures'] is False and coverage['geometry_rearranged'] is False
    # 独立读旧版本快照和新序列化buffer：源形体只允许整套相似缩放，颜色/UV/出生/寿命严格相同。
    old=json.loads((ROOT/'docs/source-effects-051-before.json').read_text('utf8'));now=buffers(A/'iris_fx_electro_area.mesh')
    for i,((name,values),before) in enumerate(zip(now,old['electro_buffers'])):
        assert name==before['name'];b=np.asarray(before['values']);assert b.shape==values.shape
        assert np.allclose(values[:,:3],b[:,:3]*factor,atol=5e-6)
        if i<3:assert np.allclose(values[:,3:],b[:,3:],atol=5e-6)
        else:
            assert np.allclose(values[:,3:6],b[:,3:6]*factor,atol=5e-6) and np.allclose(values[:,8],b[:,8]*factor,atol=5e-6)
            assert np.allclose(values[:,[6,7,9,10,11]],b[:,[6,7,9,10,11]],atol=5e-6)
    states,_,_=curves(A/'effect_curves.csv','electro_area');previous=np.asarray(old['electro_curves']);assert states.shape==previous.shape==(4,151,25)
    assert np.allclose(states[:,:,:13],previous[:,:,:13],atol=1e-8)
    for k in (16,20,24):assert np.allclose(states[:,:,k],previous[:,:,k]*factor,atol=5e-6)
    pixels=json.loads((ROOT/'docs/previews051/pixel-evidence.json').read_text('utf8'))
    oldmu=[r for r in pixels['muzzle'] if not r['native_fade']];newmu=[r for r in pixels['muzzle'] if r['native_fade']]
    for oldrow,newrow in zip(oldmu[1:],newmu[1:]):assert newrow['layers'][-1]['energy']<oldrow['layers'][-1]['energy']*.5
    oldarea=[r for r in pixels['electro'] if r['revision']==50];newarea=[r for r in pixels['electro'] if r['revision']==51]
    for oldrow,newrow in zip(oldarea[:3],newarea[:3]):assert newrow['visible_pixel_count']>oldrow['visible_pixel_count']*1.7
    assert pixels['GPU_tested'] is False
    return {'source_files_unchanged':True,'native_colour_zero_width_case':True,'native_fade_out_start':d['fade_out'],'source_layers_preserved':True,'electro_uniform_scale':factor,'electro_frames':151,'muzzle_shots':20,'051_visual_contract_preserved_with_052_instrumentation':True,'actual_CPU_preview':True,'compiled':False,'GPU_tested':False}
if __name__=='__main__':print(json.dumps(verify_source051(),ensure_ascii=False,indent=2))
