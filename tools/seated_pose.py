"""049：把源坐锤接触关系移入原生动画，固定骨长；不在运行时写角色位置。"""
import math
import numpy as np
import port_math as m

def solve_arm(bones,local,side,target,hand_q):
    """离线三关节链：锁骨仅在不可达时最小转动，随后两骨IK，不修改骨长。"""
    ids={b['name']:b['id'] for b in bones};wp=m.world(bones,local)
    h=ids['Bip01 '+side+' Hand'];e=ids['Bip01 '+side+' Forearm'];u=ids['Bip01 '+side+' UpperArm'];c=ids['Bip01 '+side+' Clavicle']
    target=np.asarray(target);cp=np.asarray(wp[c][0]);lever=np.asarray(wp[u][0])-cp;toward=target-cp
    l1=np.linalg.norm(bones[e]['position']);l2=np.linalg.norm(bones[h]['position']);arm=l1+l2-1e-5
    if np.linalg.norm(target-np.asarray(wp[u][0]))>arm:
        d=np.linalg.norm(toward);l0=np.linalg.norm(lever)
        theta=math.acos(np.clip(toward@lever/max(1e-9,d*l0),-1,1))
        allowed=math.acos(np.clip((d*d+l0*l0-arm*arm)/max(1e-9,2*d*l0),-1,1))
        if theta>allowed+1e-6:
            q=m.from_to(lever,toward);angle=2*math.acos(np.clip(abs(q[0]),0,1));fraction=min(1,(theta-allowed+1e-4)/max(1e-9,angle))
            xyz=np.asarray(q[1:]);axis=xyz/max(1e-9,np.linalg.norm(xyz));turn=m.axis(axis,math.degrees(angle*fraction))
            worldq=m.qmul(turn,wp[c][1]);local[c]=m.qnorm(m.qmul(m.qi(wp[bones[c]['parent']][1]),worldq));wp=m.world(bones,local)
    shoulder=np.asarray(wp[u][0]);elbow0=np.asarray(wp[e][0]);hand0=np.asarray(wp[h][0]);ray=target-shoulder;d=np.linalg.norm(ray);direction=ray/max(d,1e-9)
    reach=min(arm,max(abs(l1-l2)+1e-5,d));pole=elbow0-shoulder;pole-=direction*(pole@direction)
    if np.linalg.norm(pole)<1e-6:pole=np.cross(direction,[0,0,1])
    pole/=max(1e-9,np.linalg.norm(pole));along=(reach*reach+l1*l1-l2*l2)/(2*reach)
    elbow=shoulder+direction*along+pole*math.sqrt(max(0,l1*l1-along*along));hand=shoulder+direction*reach
    uq=m.qmul(m.from_to(elbow0-shoulder,elbow-shoulder),wp[u][1]);eq=m.qmul(m.from_to(hand0-elbow0,hand-elbow),wp[e][1])
    local[u]=m.qnorm(m.qmul(m.qi(wp[bones[u]['parent']][1]),uq));local[e]=m.qnorm(m.qmul(m.qi(uq),eq));local[h]=m.qnorm(m.qmul(m.qi(eq),hand_q))
    return m.world(bones,local)

def seat(bones,local,source_world,source_ids,conversion,scale,weight,grip_delta):
    """枪口已抬高后，将源Pelvis相对WEAPON的接触关系还给身体，再把双手接回同一武器。
    位移仅写入动画Pelvis局部轨道；根轨道另用修正前值，不能由悬起双脚反推落地补偿。
    """
    ids={b['name']:b['id'] for b in bones};wp=m.world(bones,local);pelvis=ids['Bip01 Pelvis'];rh=ids['Bip01 R Hand']
    fixed_hand=np.asarray(wp[rh][0]);hand_q=wp[rh][1];grip=fixed_hand+grip_delta
    source_relative=conversion@(np.asarray(source_world[source_ids['NPC Pelvis [Pelv]']][0])-source_world[source_ids['Weapon']][0])*scale
    delta=(grip+source_relative-np.asarray(wp[pelvis][0]))*weight
    parent=bones[pelvis]['parent'];local_delta=np.asarray(m.rotate(m.qi(wp[parent][1]),delta))
    bones[pelvis]['position']=m.vadd(bones[pelvis]['position'],local_delta)
    wp=solve_arm(bones,local,'R',fixed_hand,hand_q)
    return local_delta.tolist(),{'weight':float(weight),'hand_error':float(np.linalg.norm(np.asarray(wp[rh][0])-fixed_hand)),
                                'pelvis_error':float(np.linalg.norm(np.asarray(wp[pelvis][0])-(grip+source_relative)))},wp
