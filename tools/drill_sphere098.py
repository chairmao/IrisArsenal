"""098只读真实钻头19层网格，核对完整旋转包络的紧球；不改资源、不编译。"""
from pathlib import Path
import hashlib,json,math,re
import numpy as np
from safeio import ROOT

def collect(root=ROOT):
    import scene_geometry as geo
    path=root/'package/IrisArsenal/assets/iris_drill.mesh'
    parts=geo.mesh(path);assert len(parts)==19 and all(len(p['weights'])==0 for p in parts)
    # 金属1..14与弧光0/15..18都参与。球心约束在源Z旋转轴上；完整旋转包络的最小球必有轴上球心。
    # 不取AABB对角线，也不把角色前进路径并入半径；三角形内部是顶点凸组合，顶点包含即可覆盖整个面。
    points=np.vstack([p['p'].astype(float) for p in parts]);assert np.isfinite(points).all()
    z=points[:,2];radial=(points[:,:2]**2).sum(axis=1)
    low,high=float(z.min()),float(z.max())
    def value(c):return float(np.max(radial+(z-c)**2))
    for _ in range(100):
        a=low+(high-low)/3;b=high-(high-low)/3
        if value(a)<value(b):high=b
        else:low=a
    center=(low+high)/2
    # 两个活动圆环约束的极小值是全体约束最优值的下界；用该证书验证数值搜索没有悄悄扩大球。
    i=int(np.argmax(radial+(z-center+1e-5)**2));j=int(np.argmax(radial+(z-center-1e-5)**2))
    if z[i]==z[j]:w=float(z[i])
    else:w=float(np.clip((radial[j]+z[j]**2-radial[i]-z[i]**2)/(2*(z[j]-z[i])),min(z[i],z[j]),max(z[i],z[j])))
    lower=math.sqrt(max(radial[i]+(z[i]-w)**2,radial[j]+(z[j]-w)**2))
    center=float(np.float32(center));exact=math.sqrt(value(center))
    radius=float(np.nextafter(np.float32(exact),np.float32(np.inf)))
    assert radius>=exact and radius-lower<2e-5
    return {'mesh_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'vertices':len(points),'submeshes':19,'center_z':center,'radius':radius,'exact_radius_at_float_center':exact,'optimal_radius_lower_bound':float(lower),'radius_slack':radius-float(lower),'source':'all 19 real mesh layers; full Z spin; no skin/no vertex displacement','points':points}

def validate(root=ROOT):
    data=collect(root);cpp=(root/'IrisCombat.cpp').read_text('utf-8-sig')
    for name,key in [('DRILL_SPHERE_CENTER_Z','center_z'),('DRILL_SPHERE_RADIUS','radius')]:
        m=re.search(r'const float '+name+r'=([0-9.eE+-]+)f;',cpp);assert m,'098球包络常量缺失：'+name
        assert float(np.float32(float(m[1])))==data[key],'098球包络与实际网格不一致：'+name
    assert data['mesh_sha256'] in cpp,'098源网格哈希已变，须重新核对球包络'
    return {k:v for k,v in data.items() if k!='points'}

if __name__=='__main__':print(json.dumps(validate(),ensure_ascii=False,indent=2))
