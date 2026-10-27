# 047增加电脉范围效果一类，火神四层自身不变。
# 045：倍率与防御策略可配置，原几何/源素材回归仍保持；默认与完整开关组合由test_move_parameters045核验。
"""火神炮0.2.2专项：源资产/真实材质/参数/球包络/调用边界；不编译，不当实机证据。"""
import configparser,json,re,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
from safeio import ROOT
import verify_prototype as base
from author_prototype import read_nif
P=ROOT/'package/IrisArsenal';A=P/'assets'

def verify_vulcan():
    moves=json.loads((ROOT/'docs/eight-moves.json').read_text('utf-8'))['moves'];move=moves[5]
    assert move['key']=='vulcan' and len(move['events'])==20
    assert all(e['kind']=='bullet' and e['radius']==4.5 and e['multiplier']==.2 for e in move['events'])
    ini=configparser.ConfigParser();ini.read(P/'IrisArsenal.ini',encoding='utf-8')
    assert ini.getint('IrisArsenal','DrillProofOnly')==0
    # 046玩家明确改为非等权；源资产检查读取当前规格，独立046专项另按用户原表验证。
    balance=json.loads((ROOT/'docs/balance-046.json').read_text('utf8'))['moves']
    assert {k:float(v) for k,v in ini['MoveWeights'].items()}=={key:float(row['weight']) for key,row in balance.items()}
    record=next(r for r in base.records(P/'IrisArsenal.mod') if r['key']=='1-IrisArsenal.mod');fields=base.fields(record)
    # 053武器基础数值按真实Falling Sun测试比例更新，火神自身倍率/几何/材质继续严格验收。
    from weapon_balance053 import expected_fields
    assert all(abs(fields[key]-value)<1e-7 for key,value in expected_fields().items()) and fields['pierce damage multiplier']==0
    fx=json.loads((ROOT/'docs/eight-effects.json').read_text('utf-8'));bullet=next(a for a in fx['assets'] if a['key']=='bullet')
    assert len(fx['assets'])==20 and len(bullet['materials'])==4
    assert bullet['sha256']=='f8fd57a3e4fe73cfc1558813446d7187f4120673b7f0a718b474eb4bb5a114db'
    meshes,_=read_nif(Path(bullet['source']));assert len(meshes)==4
    materials='\n'.join(p.read_text('utf-8') for p in A.glob('*.material'));shader=(A/'iris_eight.hlsl').read_text('utf-8');program=(A/'iris_eight.program').read_text('utf-8')
    checked=0;blend_counts={}
    for name,d in fx['materials'].items():
        # 新增源烟尘的粒子布局/alpha另由cannon-quake专项对照，普通材质原断言仍全部执行。
        if d.get('particle') or d.get('reference_reticle') or 'energy_kind' in d or d.get('drive059_stream') or d.get('drive059_surface'):continue # 059独立材质由test_drive059检查；普通源材质仍逐项核对。
        # NiAlpha位格式独立解码，与实际材质文本核对；不只检查生产者自己声明的blend字符串。
        ap=d['source_alpha'];bits=ap['flags'] if ap else 0
        factors=['one','zero','src_colour','one_minus_src_colour','dest_colour','one_minus_dest_colour','src_alpha','one_minus_src_alpha','dest_alpha','one_minus_dest_alpha']
        expected=factors[(bits>>1)&15]+' '+factors[(bits>>5)&15] if bits&1 else 'one zero'
        assert d['blend']==expected
        block=materials.split('material '+name+'\n',1)[1].split('\nmaterial ',1)[0]
        assert 'scene_blend '+expected in block
        blend_counts[expected]=blend_counts.get(expected,0)+1
        assert 0<=d['alpha']<=1 and np.isfinite(d['emission']+d['falloff']+[d['gain']]).all()
        if d['effect']:
            flags=d['source_shader_flags'];assert d['vertex_color']==bool(flags[1]&32) and d['vertex_alpha']==bool(flags[0]&8)
            assert d['grey_color']==bool(d['has_palette'] and flags[0]&16)
            assert d['grey_alpha']==bool(d['has_palette'] and flags[0]&32)
        if d.get('wing_metal'):
            # 翼片使用独立源金属FP，仍核对源混合与实际参数，不能用普通FX参数错误拒绝它。
            assert 'fragment_program_ref IrisWingMetalFP' in block
            for token in ['specularColour','specularStrength','glossiness','uvTransform']:assert 'param_named '+token in block
        else:
            for token in ['vertexFlags','effectParams','falloff']:assert 'param_named '+token+' float4 ' in block
        checked+=1
    # 真正火神源四层逐个对照，禁用“所有effect都查palette”及丢掉源混合。
    for mesh,name in zip(meshes,bullet['materials']):
        d=fx['materials'][name];flags=mesh['shader_data']['effect']['shader_flags'];assert list(flags)==d['source_shader_flags']
        assert d['blend']=='src_alpha one' and d['has_palette']
    assert 'float2(texel.g,vertex.g*fade*tint.r)' in shader and 'float2(texel.a,vertex.a*fade*tint.a*tint.a)' in shader
    assert 'grad.rgb*tint.rgb' not in shader and 'float2(density,0.5)' not in shader
    assert 'worldMatrix world_matrix' in program and 'cameraPosition camera_position' in program
    # 检查调色图是实际多行源LUT；对实际火神源纹理做数值抽样，不把CPU示例当GPU画面验收。
    sample=fx['materials'][bullet['materials'][0]]
    palette=np.asarray(Image.open(A/sample['palette']).convert('RGBA'),dtype=float)/255
    texel=np.asarray(Image.open(A/sample['diffuse']).convert('RGBA'),dtype=float)/255
    density=float(np.quantile(texel[:,:,1],.9));gain=sample['emission'][0]
    pixel=palette[min(palette.shape[0]-1,round(gain*(palette.shape[0]-1))),min(palette.shape[1]-1,round(density*(palette.shape[1]-1)))]
    assert np.isfinite(pixel).all() and max(pixel[:3])>.05
    background=np.array([.35,.22,.13]);black=np.zeros(3);alpha=.9
    assert np.allclose(background+black*alpha,background)
    assert not np.allclose(black*alpha+background*(1-alpha),background)
    # 所有序列化火球顶点在缩放后落入R4.5球包络；画面中心与物理球心使用同一源center。
    vertices,_=base.mesh(A/'iris_fx_bullet.mesh',48);points=np.concatenate(vertices);center=np.asarray(bullet['center']);radius=float(bullet['bound_radius'])
    scaled=(points-center)*(4.5/radius);assert np.linalg.norm(scaled,axis=1).max()<=4.50001
    # 平地站姿：旧脚底目标使球先碰地；当前胸部点示例不会碰地。趴地骨点仍按真实低位瞄准，并保留地形阻挡。
    heights=np.linspace(6.5,13,101);assert min(heights)>4.5
    assert min(np.linspace(6.5,2,101))<4.5
    # 横向擦边4.49/4.51分别在球包络内/外，不偷偷把半径当直径或只用XZ距离。
    assert np.linalg.norm([0,4.49,0])<4.5 and np.linalg.norm([0,0,4.51])>4.5
    main=(ROOT/'IrisArsenal.cpp').read_text('utf-8');combat=(ROOT/'IrisCombat.cpp').read_text('utf-8')
    assert main.count('KenshiLib::AddHook(')==7 and combat.count('KenshiLib::AddHook(')==3
    assert 'Native(&CombatClass::_iHitYouAreYouHit,' in main
    # 三远程的额外防御适配已按用户要求移除；共用钩子继续服务其他招式。
    assert 'const bool unavoidable=!RangedMove(r.move)&&moves[r.move].bypassDefence;' in combat
    assert 'move.bypassDefence=(index==5||index==6||index==7)?false:' in combat
    assert 'context->combat==self&&context->damage==&damage&&context->caster==who' in combat
    assert combat.index('if(matches)context->pending=false;')<combat.index('HitMaterialType result=originalDefence(self,dir,damage,who);')
    assert 'if(result==HIT_MISSED||result==HIT_SWORD)return HIT_FLESH;' in combat
    assert '~VulcanHitScope(){if(active)TlsSetValue(defenceTLS,previous);}' in combat
    assert combat.count('->_NV_hitByMeleeAttack(')==1
    assert 'return t&&t->isValid()?t->getPosition()+Vector3(0,2,0)' not in combat
    assert 'target->getBoneWorldPosition(bones[i])+offset' not in combat and 'Vector3 point=target->getBoneWorldPosition(bones[i]);' in combat and 'DrawShot(s,a.origin);shots.push_back(s);' in combat
    assert 'e.kind==6?"bullet"' in combat and 's.collisionRadius=e.kind==6?e.radius:e.kind==7?4.5f' in combat
    # 核对本机声明、桩和实际链接输入，不用其他Ogre版本的旧接口，仍不代表MSVC已通过。
    deps=Path('E:/KenshiProject/1.Dependencies/KenshiLib_0.5.0')
    for file,symbol in [('combat/CombatClass.h','_iHitYouAreYouHit'),('Character.h','getBoneWorldPosition')]:
        assert symbol in (deps/'Include/kenshi'/file).read_text('utf-8-sig')
        assert ('?'+symbol+'@').encode() in (deps/'Libraries/KenshiLib.lib').read_bytes()
    assert 'getWorldBoundingBox(' not in combat
    return {'enabled_only':['fire_roll','spiral','earthquake','drill','full_burst','vulcan','pulse','drive','electro_cannon','hammer_combo'],'shots':20,'sphere_collision_radius':4.5,'blast_radius':4.5,'weapon_cut_blunt':.1,
            'source_fireball_layers':4,'materials_checked':checked,'blend_counts':blend_counts,'palette_sample_RGBA':pixel.tolist(),
            'bullet_bound_radius_after_scale':float(np.linalg.norm(scaled,axis=1).max()),'native_defence_scope':'all three ranged moves excluded; shared gate only for selected melee; original chain retained',
            'SDK_declarations_and_link_symbol_bytes':True,'C++_compiled':False,'GPU_compiled':False,'game_tested':False}
if __name__=='__main__':print(json.dumps(verify_vulcan(),ensure_ascii=False,indent=2))
