"""从模板和只读源素材恢复完整资源；不编译、不写游戏目录。"""
import json
from safeio import ROOT,put

def main():
    out=ROOT/'package/IrisArsenal';templates=ROOT/'distribution'
    # 生成失败的半包不能继续沿用旧ready标记。
    put(out/'IrisPackage.json',json.dumps({'ready':False,'reason':'资源正在重建，尚未校验/组包'},ensure_ascii=False,indent=2),'组包状态','资源重建时撤销旧ready')
    if not (out/'IrisArsenal.mod').is_file():
        put(out/'IrisArsenal.mod',(templates/'IrisArsenal.base.mod').read_bytes(),'FCS恢复','仅用模板引导，随后强制运行当前十招作者')
    for name in ('RE_Kenshi.json','IrisArsenal.ini','_IrisArsenal.info'):
        # 包内配置来自distribution；全量更新会覆盖旧配置，不再合并个人设置。
        put(out/name,(templates/name).read_text('utf-8'),'运行入口恢复','从package外模板恢复注册/默认配置/元数据')
    import author_prototype as prototype
    # 只复用基础模型与旧诊断动画函数，不运行旧mod_assets/main覆盖十招FCS。
    print('[1/4] 重建普通武器、钻头、图标和基础纹理',flush=True)
    prototype.visual_assets();prototype.body_assets()
    # 049原生图标缓存键预制图必须随完整重建生成，否则再次UpdateMod会丢失修复。
    import inventory_icon049;inventory_icon049.main()
    print('[2/4] 重建十招身体动画、握点、FCS与事件流',flush=True)
    import author_moves
    author_moves.main()
    # 097碰撞轨道必须跟随刚导出的身体动画，不重造视觉或在运行时遍历骨骼。
    import blade_pose097;blade_pose097.main()
    print('[3/4] 重建十招分层特效、材质与碰撞资源',flush=True)
    import author_effects
    author_effects.main()
    print('[4/4] 应用钻头材质兼容修正',flush=True)
    from prepare_drill_optics import prepare
    prepare()
    # 052生成器不再导出heavy；同时移除旧package遗留的精确无引用文件。
    import prune_package052;prune_package052.main()
    # 070在全部作者/材质兼容步骤后按最终引用图裁剪，避免完整重建恢复旧声明。
    import prune_runtime070;prune_runtime070.main()
    print('资源已恢复；尚未编译、尚未部署。',flush=True)

if __name__=='__main__':main()
