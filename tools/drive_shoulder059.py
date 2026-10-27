"""059极致驱动PA10的炮体轴/前握位校准；固定骨长、原生FCS播放，无运行时骨骼或角色写入。"""
import numpy as np
import port_math as m
def weight(t):return m.smooth((t-.12)/.32)*(1-m.smooth((t-4.45)/.38))
def prepare(author,bones,local,source,source_ids,qC,t):
    ids={b['name']:b['id'] for b in bones};world=m.world(bones,local)
    # 源普通WEAPON在EXanim阶段被隐藏，真正炮体轴来自NPC Root；取炮体朝向，不能沿隐藏标记斜射。
    original=m.qnorm(m.qmul(m.qmul(qC,source[source_ids['Weapon']][1]),m.qi(qC)))
    cannon=m.qnorm(m.qmul(m.qmul(qC,source[source_ids['NPC Root [Root]']][1]),m.qi(qC)))
    target=author.slerp(original,cannon,weight(t));rh=ids['Bip01 R Hand'];prop=ids['Bip01 Prop2']
    # 源手臂重定向后过度前伸，使左前握点不可达；将右掌沿炮轴收回3单位到肩前，
    # 复用固定骨长的离线两骨IK，保留右腕朝向，不伸骨也不在游戏中改位置。
    from seated_pose import solve_arm
    right=np.asarray(world[rh][0])-np.asarray(m.rotate(target,[0,0,3]))*weight(t)
    world=solve_arm(bones,local,'R',right,world[rh][1])
    delta=np.asarray(m.rotate(qC,m.vsub(source[source_ids['Weapon']][0],source[source_ids['NPC R Hand [RHnd]']][0])))*author.SCALE
    offset=np.asarray(m.rotate(m.qi(world[rh][1]),delta))-np.asarray(bones[prop]['position']);local[prop]=m.qnorm(m.qmul(m.qi(world[rh][1]),target))
    return m.world(bones,local),target,tuple(offset)
def support_target(grip,orientation,old,t):
    # 普通2.nif的枪杆前握位；炮体绑NPC Root、隐藏WEAPON不能作为源左掌握点。
    supported=np.asarray(grip)+m.rotate(orientation,[1.807138657,-.35,3.0]);w=weight(t)
    return np.asarray(old)*(1-w)+supported*w
