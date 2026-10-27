"""097只读已导出的身体动画，生成碰撞用Prop2轨道文本；不重建动画/特效，不编译。"""
from pathlib import Path
import hashlib,json,math
from safeio import ROOT,put
NAME='blade_poses097.csv'

def collect(root=ROOT):
    # 以实际OGRE二进制为依据，不从旧proof表或主观180度假设生成刀路。
    import scene_geometry as geo
    import port_math as m
    spec=next(v for v in json.loads((root/'docs/eight-moves.json').read_text('utf8'))['moves'] if v['key']=='full_burst')
    rows=['IRIS_BLADE_POSES 1 2']
    for track,sex in enumerate(('male','female')):
        path=root/('package/IrisArsenal/assets/iris_action_full_burst_'+sex+'.skeleton')
        ids,frames,_=geo.actual_frames(path,spec)
        rows.append(f'{track} {len(frames)} {spec["duration"]:.9g} {hashlib.sha256(path.read_bytes()).hexdigest()}')
        for i,frame in enumerate(frames):
            p,q=frame[ids['Bip01 Prop2']]
            # 与运行时Iris::SourcePose同一右乘Rx(-90)；不另乘根运动或改握点。
            q=m.qnorm(m.qmul(q,m.axis((1,0,0),-90)))
            values=(spec['duration']*i/(len(frames)-1),*p,*q)
            assert all(math.isfinite(v) for v in values)
            rows.append(' '.join(f'{v:.9g}' for v in values))
    return '\n'.join(rows)+'\n'

def validate(root=ROOT):
    path=root/'package/IrisArsenal/assets'/NAME
    lines=path.read_text('utf8').splitlines();assert lines[0]=='IRIS_BLADE_POSES 1 2','097碰撞轨道头错误'
    cursor=1
    for track,sex in enumerate(('male','female')):
        index,count,duration,digest=lines[cursor].split();cursor+=1;count=int(count);duration=float(duration)
        assert int(index)==track and 2<=count<=4096 and math.isfinite(duration) and duration>0
        source=root/('package/IrisArsenal/assets/iris_action_full_burst_'+sex+'.skeleton')
        assert hashlib.sha256(source.read_bytes()).hexdigest()==digest,'097碰撞轨道与身体动画不一致，请执行 tools/blade_pose097.py 重新导出'
        for i in range(count):
            row=[float(v) for v in lines[cursor].split()];cursor+=1
            assert len(row)==8 and all(math.isfinite(v) for v in row)
            assert abs(row[0]-duration*i/(count-1))<2e-5
            assert abs(sum(v*v for v in row[4:8])-1)<1e-4
    assert cursor==len(lines)

def main():
    put(ROOT/'package/IrisArsenal/assets'/NAME,collect(),'097动画时序碰撞轨道','只从现有男女全力爆发骨骼导出Prop2纯值轨道；用于跨帧快扫完整重建，不改身体/美术')
    validate()

if __name__=='__main__':main()
