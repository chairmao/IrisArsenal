"""原生远程030静态合同：能力发现→原生射击许可→整套动作→原生可配置单位装填间隔；不编译/模拟宣称实机。"""
from pathlib import Path
import json,re,configparser
from safeio import ROOT

def verify_ranged():
    main=(ROOT/'IrisArsenal.cpp').read_text('utf-8');combat=(ROOT/'IrisCombat.cpp').read_text('utf-8');source=(ROOT/'IrisRanged.cpp').read_text('utf-8');header=(ROOT/'IrisRanged.h').read_text('utf-8')
    assert main.count('KenshiLib::AddHook(')==7 and combat.count('KenshiLib::AddHook(')==3 and source.count('KenshiLib::AddHook(')==8
    for name in ['&Character::shouldUseRangedWeapons','&AI::hasCrossbowEquipped','&AI::_NV_scoreRangedAttack','&AI::isWithinMyBowRange','&RangedCombatClass::getGun','&RangedCombatClass::animationUpdate','&GunClass::shoot','&RangedCombatClass::reloadCheck']:
        assert 'Native('+name in main
    # 近战池的两个加权分支都排除5/6/7；远程只能由原生ShotHook许可进入，不自设找人/发射轮询。
    choose=combat[combat.index('CombatTechniqueData* Choose('):combat.index('int PickRanged(')]
    assert choose.count('!RangedMove(i)&&')==2 and 'return i==5||i==6||i==7;' in combat
    assert 'for(unsigned i=5;i<=7;++i)' in combat
    assert 'c->stats->rangedMode' in source and 'new Crossbow' not in source
    assert not re.search(r'(reinterpret_cast|static_cast)\s*<\s*(Crossbow|Sword)',source)
    assert 'inventory->getPrimaryWeapon()' in source and 'inventory->getSecondaryWeapon()' in source
    assert 'c->drawWeapon(item,item->inventorySection)' in source
    assert 's->gun->maxRange=IrisCombat::RangedRange()' in source
    assert 's->gun->barrel=c->getPosition();s->gun->position=s->gun->barrel;' in source
    assert 'rangedWeapon&&canShoot&&inMoveRange&&!paused' in combat
    assert 's->gun->ready=s->available&&s->published' in source
    # 真实GunClass派生，纯虚函数完整实现；没有把近战物品变成弩或创建库存/渲染替身。
    assert 'class HybridGun : public GunClass' in source
    for method in ['scoreTarget','getAimCloseness','getAudioObject','getDamageMin','getDamageMax','getParentNode']:
        assert re.search(r'virtual[^;{]+\b'+method+r'\(',source),method
    for bad in ['setPosition(', 'setOrientation(', 'createEntity(', 'setUserContactReport(', 'Sleep(', 'GetTickCount', 'QueryPerformanceCounter', 'chrono::', 'Item::create', 'rangedCombat->updateT(', 'rangedCombat->updateMT(']:assert bad not in source,bad
    assert 'GameDataCopyStandalone*' in source and 'd->clearList("ammo");d->clearList("reload anim")' in source
    # 原生shoot只对真实其他枪执行；自有适配器在故障/退役时也不能产生原生弩箭或额外伤害。
    shot=source[source.index('void __fastcall ShotHook'):source.index('bool __fastcall ReloadHook')]
    assert 'if(!own&&originalShot)originalShot(' in shot and 'Private(gun)' in shot and 's->pending=true;s->busy=true;s->gun->ready=false' in shot
    assert 'numShotsCurrent=0' not in shot and 'hitBy' not in shot and 'Ogre::' not in shot
    finish=source[source.index('void Finish('):source.index('bool Active(')]
    assert 's->gun->numShotsCurrent=0;' in finish and 'ReloadHook(ranged)' in finish
    reload=source[source.index('bool __fastcall ReloadHook'):source.index('void Install(')]
    assert 'bool result=originalReload?originalReload(ranged):false;' in reload and 'reloadTimer-=' not in source
    assert 'float actionInterval=1.0f;' in source and 'reloadTimeMin=reloadTimeMax=actionInterval' in source
    assert 'numShotsMax=numShotsCurrent=1;' in source and 'ammoType=0;reloadAnimation=0;' in source
    assert 'if(before&&!ranged->_isReloading)ranged->aimTimer=0;' in reload
    # 原生计算返回值钳在[min,max]内，两个端点皆配置值时，任何熟练度/插值/随机结果都只能是配置值。
    for interval in [0,.1,1,2,3600]:
        for value in [-1e30,-1,0,.2,1,2,20,1e30]:assert max(interval,min(interval,value))==interval
    assert 'if(!a.active&&!paused&&IrisRanged::TakeRequest(c,requested))' in combat
    assert 'a.rangedWait+=gameDelta' in combat and 'if(!paused)a.rangedWait' in combat
    assert 'IrisRanged::Active(c)?c->rangedCombat->_getAttackTarget()' in combat
    assert 'if(a.ranged)IrisRanged::Finish(a.owner)' in combat
    assert 'IrisRanged::Reset();IrisCombat::Clear' in main
    assert 's->available=false;s->gun->ready=false;' in source
    assert 'GunClass::_NV_destroyPhysical();' in source
    assert 'retired.size()+slots.size()>=16' in source
    assert 'c->medical.isRightArmOk()&&c->medical.isLeftArmOk()' in source
    assert 'queuesAreClearMT()' in source and 'retired.pop_back();delete gun;' in source
    # 核对本机SDK声明与实际链接库符号；仍不是MSVC类型/链接或游戏调用链实证。
    deps=Path('E:/KenshiProject/1.Dependencies/KenshiLib_0.5.0');lib=(deps/'Libraries/KenshiLib.lib').read_bytes()
    for file,method in [('GunClass.h','GunClass'),('GameData.h','GameDataCopyStandalone'),('GameData.h','initialise'),('combat/RangedCombatClass.h','reloadCheck'),('combat/RangedCombatClass.h','scoreTargetRange'),('AI/AI.h','hasCrossbowEquipped'),('AI/AI.h','isWithinGivenRange'),('MedicalSystem.h','hasAnArmToFightWith'),('CharStats.h','getAttackSpeed'),('CharacterHuman.h','drawWeapon')]:
        assert method in (deps/'Include/kenshi'/file).read_text('utf-8-sig'),method
        assert (method+'@').encode() in lib,method
    moves=json.loads((ROOT/'docs/eight-moves.json').read_text('utf-8'));assert moves['contract']=='IRIS_EIGHT_042'
    assert len(moves['moves'][5]['events'])==20 and len(moves['moves'][6]['events'])==3
    assert all(x['radius']==36 for x in moves['moves'][6]['events'])
    assert len(moves['moves'][7]['events'])==4 and all(x['radius']==9 for x in moves['moves'][7]['events'])
    assert moves['routing']['ranged_checkbox_only']==['vulcan','pulse','drive','electro_cannon','hammer_combo']
    return {'hooks_total':18,'extra_hooks_scoped_to_hybrid':8,'weapon_item_unchanged':True,'ammunition':'native ammoType=NULL, no inventory/ammo object','ranged_moves':['vulcan','pulse','drive','electro_cannon','hammer_combo'],'other_five':'native melee selector','interval':{'native_reload_min':'RangedActionInterval','native_reload_max':'RangedActionInterval','default':1,'starts':'whole action end/interrupt','timer_owner':'original RangedCombatClass::reloadCheck; no wall clock or per-event reload'},'forwarding':'native other crossbows/turrets unchanged','source_action_events':[20,3,4],'SDK_symbols_checked':10,'config_key':'RangedActionInterval','grammar_only':True,'C++_compiled':False,'native_runtime_verified':False,'remaining':'原生GOAP整链/实际拔枪/视线和远程模式切换/暂停变速/反复读档与析构需实机'}
if __name__=='__main__':print(json.dumps(verify_ranged(),ensure_ascii=False,indent=2))
