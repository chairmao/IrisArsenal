"""原生武器图标相机：按实际模型取景，不能依赖武器分支忽略的自定义PNG。"""
H=.059155464;V=-.05018258;ZOOM=2.29
def apply(weapon,field):
    # Steam1.0.65武器固定LOCAL pitch-90/yaw-180/roll90；FOV45，摄距zoom*5。
    # 10x2逻辑格宽高比5；模型全部顶点投影在±0.88内。仅改FCS，不安装运行时图标钩子。
    field(weapon,'auto icon image','bool',True)
    for k,v in [('icon offset H',H),('icon offset V',V),('icon zoom',ZOOM)]:field(weapon,k,'f32',v)
