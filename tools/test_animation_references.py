"""动画引用回归：不编译、不写游戏；故障用内存FCS副本，覆盖曾漏过的跨层合同。"""
import copy,json
from pathlib import Path
import verify_moves as v
from author_prototype import field,refs

def main():
    moves=json.loads((v.ROOT/'docs/eight-moves.json').read_text('utf-8'))['moves']
    current=v.base.records(v.P/'IrisArsenal.mod');results={}
    assert len(v.animation_references(moves,current))==20
    results['valid_20_references']='passed'
    def reject(name,change):
        records=copy.deepcopy(current);change(records)
        try:v.animation_references(moves,records)
        except (AssertionError,FileNotFoundError):results[name]='rejected';return
        raise AssertionError('错误FCS没有被拒绝: '+name)
    def edit(records,key,name,value):
        field(next(r for r in records if r['key']==key),name,'filename',value)
    reject('old_missing_filename',lambda rs:edit(rs,'30-IrisArsenal.mod','female animation','./mods/IrisArsenal/assets/iris_fire_roll_female.skeleton'))
    # 旧钻头文件确实存在，却只含DrillProof；这个用例防止“文件存在”掩盖动画身份错误。
    reject('existing_legacy_drill_wrong_clip',lambda rs:edit(rs,'33-IrisArsenal.mod','male animation','./mods/IrisArsenal/assets/iris_drill_male.skeleton'))
    reject('existing_other_move_wrong_clip',lambda rs:edit(rs,'30-IrisArsenal.mod','male animation','./mods/IrisArsenal/assets/iris_action_spiral_male.skeleton'))
    reject('outside_mod_path',lambda rs:edit(rs,'30-IrisArsenal.mod','male animation','./mods/IrisArsenal/../../outside.skeleton'))
    def remove_race_ref(rs):
        race=next(r for r in rs if r['type']==7)
        ids=[x for x in v.category_ids(race,'animation files') if x!='30-IrisArsenal.mod']
        race['cats']=[refs('animation files',[(x,0,0,0) for x in ids])]
    reject('missing_race_animation_reference',remove_race_ref)
    print(json.dumps(results,ensure_ascii=False,indent=2))
    return results
if __name__=='__main__':main()
