"""041从实际序列化数据核对可见范围、独立材质和源灰金属，不把离线模型当游戏实测。"""
import json,hashlib,types
from pathlib import Path
import numpy as np
from PIL import Image
from safeio import ROOT
from test_drill_visibility import buffers
from fire_coverage import measure

def verify_range041():
    A=ROOT/'package/IrisArsenal/assets'
    fx=json.loads((ROOT/'docs/eight-effects.json').read_text('utf8'));base=json.loads((ROOT/'docs/fire-burst-040.json').read_text('utf8'));drill=json.loads((ROOT/'docs/drill-burst-041.json').read_text('utf8'));roll=json.loads((ROOT/'docs/fire-roll-041.json').read_text('utf8'))
    ctx=types.SimpleNamespace(MATS=fx['materials'],TEXTURES={p.name:p.read_bytes() for p in A.iterdir() if p.suffix in ('.png','.dds')})
    # 更新校验只依赖项目保存的058历史基线和源素材，不读取待清空的游戏mod目录。
    # 两份网格到059仍与历史基线逐字节一致，既保持原断言，又支持空目录/缺文件修复。
    baseline=json.loads((ROOT/'docs/fire-cannon-058-baseline.json').read_text('utf8'))['runtime']
    for name in ('iris_fx_fire_blast.mesh','iris_fx_drill_blast.mesh'):
        assert hashlib.sha256((A/name).read_bytes()).hexdigest()==baseline['assets/'+name],name+'偏离项目历史基线'
    result={}
    for key,record,start in [('drill_blast',drill['fire'],.56),('roll_blast',roll,0)]:
        calibration=record['coverage_calibration'];scale=calibration['uniform_scale'];assert 1<scale<16
        serialized=list(buffers(A/('iris_fx_'+key+'.mesh')));layers=[]
        for (name,data),layer in zip(serialized[-2:],record['render_layers']):
            assert name==layer['material'];p=data[::4,:10];assert np.allclose(p,layer['particles'],atol=1e-6)
            layer=dict(layer);layer['particles']=p.tolist();layers.append(layer)
            assert np.allclose(ctx.MATS[name]['acceleration'],layer['acceleration'])
        for old,new in zip(base['layers'],record['layers']):
            b=np.asarray(old['particles']);q=np.asarray(new['particles']);assert np.allclose(q[:,[0,1,2,3,4,5,8]],b[:,[0,1,2,3,4,5,8]]*scale,atol=1e-6)
            assert np.allclose(q[:,6],b[:,6]+start) and np.allclose(q[:,[7,9]],b[:,[7,9]])
            assert np.allclose(new['acceleration'],np.array(old['acceleration'])*scale)
            assert old['material']!=new['material'] and old['source_world_matrix']==new['source_world_matrix']
        end=calibration['source_body_window'][1];fire=[l for l in layers if l['name'].startswith('FlamesTall03')]
        observed=measure(ctx,fire,np.linspace(start+.05,start+end,28));before=np.asarray(calibration['before']['radius95_by_view']);actual=np.asarray(observed['radius95_by_view']);reference=np.asarray(calibration['reference']['radius95_by_view'])
        assert np.allclose(actual,before*scale,atol=1e-5) and np.min(actual/reference)>=calibration['required_ratio']-1e-6
        result[key]={'uniform_scale':scale,'radius95_by_view':actual.tolist(),'reference':reference.tolist(),'minimum_ratio':float(np.min(actual/reference)),'world_radius95':(actual*(120 if key=='drill_blast' else 24)).tolist(),'GPU_measured':False}
    # 上述整文件历史哈希已覆盖蓝相几何/有限粒子，不能缩小蓝场来满足火焰3/4。
    import author_prototype as author
    from iris_wings import read_meshes
    meshes,_=author.read_nif(author.SOURCE/'Meshes/SW/Iris/EXDrill1.nif');wings=read_meshes(author.SOURCE/'Meshes/SW/Iris/EXDrill2.nif')
    texture=author.SOURCE/'Textures/Soulworker/Iris/002.dds';rgb=np.array(Image.open(texture).convert('RGB'));assert int(rgb.min())==40 and int(rgb.max())==49
    assert all(m['shader_data']['specular']==[1.,1.,1.] for m in wings)
    assert sorted(m['shader_data']['specular_strength'] for m in wings)==[1.]+[10.]*9
    shader=(A/'iris_drill_optics.hlsl').read_text('utf8');shared=(A/'iris_eight.hlsl').read_text('utf8')
    for s in (shader,shared):
        assert 'base*(1.0+ambient*0.45+sun*ndl*0.65)' in s and 'reflected*specularColour*max(specularStrength,0)' in s
        assert 'base*(0.18+' not in s
    # 参数/源贴图不被重染；修复只发生在自有光照适配。实体原emissive为0，仍不伪造发光。
    optics=json.loads((ROOT/'docs/drill-optics.json').read_text('utf8'))
    for m,binding in zip(meshes,optics['bindings']):assert m['shader_data']==binding['source_shader']
    for m in wings:
        assert not any(m['shader_data']['emissive'])
    c=(ROOT/'IrisCombat.cpp').read_text('utf8');assert 'move==0?"roll_blast":move==4?"full_blast"' in c
    assert 'Path(p,p,radius,true)' in c and c.count('->_NV_hitByMeleeAttack(')==1 and c.count('KenshiLib::AddHook(')==3
    moves=json.loads((ROOT/'docs/eight-moves.json').read_text('utf8'))['moves'];assert moves[3]['events'][-1]['radius']==120 and moves[0]['events'][-1]['radius']==24
    return {'range':result,'blue_geometry_unchanged':True,'full_burst_fire_asset_unchanged':True,'source_metal_RGB':[40,49],'wing_specular_strengths':[1.]+[10.]*9,'source_textures_and_colours_unchanged':True,'damage_unchanged':True,'Cxx_HLSL_compiled':False,'game_tested':False}

if __name__=='__main__':print(json.dumps(verify_range041(),ensure_ascii=False,indent=2))
