// IrisArsenal 0.4.9：同一锤枪的GunClass适配；远程选敌/走位/视线/装填计时仍由原生状态机执行。
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>
#include "IrisRanged.h"
#include "IrisCombat.h"
#include "IrisDiagnostics.h"
#include "native/IniValues.h"
#include <core/Functions.h>
#include <kenshi/Character.h>
#include <kenshi/CharStats.h>
#include <kenshi/CharBody.h>
#include <kenshi/Tasker.h>
#include <kenshi/GameWorld.h>
#include <kenshi/GameData.h>
#include <kenshi/GunClass.h>
#include <kenshi/Gear.h>
#include <kenshi/Inventory.h>
#include <kenshi/PhysicsActual.h>
#include <kenshi/AI/AI.h>
#include <kenshi/Platoon.h>
#include <kenshi/Animation/AnimationClass.h>
#include <kenshi/combat/RangedCombatClass.h>
#include <ogre/OgreSceneNode.h>
#include <algorithm>
#include <map>
#include <set>
#include <vector>
#include <sstream>
#include <stdexcept>
#include <cstdlib>
#include <cwchar>
#include <float.h>
#include <cmath>
namespace Iris {
extern CRITICAL_SECTION mutex;
bool Accepting();bool ActorReady(Character*);bool UsesWeapon(CharStats*);bool Finite(float);bool Finite(const Ogre::Vector3&);
void* RangedAddress(unsigned binding);void Log(const std::string&);
}
namespace IrisRanged {
using Ogre::Vector3;
// 078只围住既有临界区观察等待与保护段；默认NULL的非Hook调用保持原锁和生命周期。
struct Guard {IrisDiagnostics::HookAudit* audit;
    explicit Guard(IrisDiagnostics::HookAudit* value=0):audit(value){if(audit)audit->BeforeLock();EnterCriticalSection(&Iris::mutex);if(audit)audit->Acquired();}
    ~Guard(){if(audit)audit->BeforeUnlock();LeaveCriticalSection(&Iris::mutex);}};
// 配置值只在启动阶段写一次；回调仍由原生reloadCheck推进，不能乘每发子弹次数。
float actionInterval=1.0f;
void Configure(const std::wstring& directory){
    const std::wstring ini=directory+L"IrisArsenal.ini";
    // 103原生装填单位直接取INI，不限制0..3600；仅拒绝无法存入实际float字段的数值。
    actionInterval=IrisIni::Float(IrisIni::Number(ini,L"IrisArsenal",L"RangedActionInterval",1),"RangedActionInterval");std::ostringstream out;out<<"ranged_interval_config native_units="<<actionInterval<<" read_on_startup=1";Iris::Log(out.str());
}
// 数据是插件独占的GunClass参数，不加入游戏物品注册表、不序列化；所有实例共用这一份进程期常量。
GameDataCopyStandalone* data=0;
// 原生getAimDir与特效快照共用同一归一化规则；只算值，不启动射线或推进瞄准/装填计时。
Vector3 AimDirection(const Vector3& from,const Vector3& target){
    Vector3 d=target-from;if(!Iris::Finite(d)||!Iris::Finite(d.squaredLength())||d.squaredLength()<=.000001f)return Vector3::UNIT_Z;
    d.normalise();return d;
}
const char* SHARED_AIM_CONTRACT="IRIS_NATIVE_AIM_060";
// 与已核对的原生getAimPos身体点分支一致：动物Spine1、人形Spine2，按原生年龄比例取骨点。
// 即时光炮没有飞行提前量；只在AI/物理静止主线程调用，零骨点沿用原生根位置回退。
Vector3 NativeBodyPoint(Character* target){
    Vector3 point=target->animation?target->animation->getBoneWorldPosition(target->isAnimal()?"Bip01 Spine1":"Bip01 Spine2",target->getAge()):Vector3::ZERO;
    return point==Vector3::ZERO?target->getPosition():point;
}
class HybridGun : public GunClass {
public:
    bool ready;Vector3 barrel;
    HybridGun(GameData* d):GunClass(d),ready(false),barrel(Vector3::ZERO){
        ammoType=0;reloadAnimation=0;reloadTimeMin=reloadTimeMax=actionInterval;
        numShotsMax=numShotsCurrent=1;gunBarrelOffsetPos=Vector3::ZERO;
        // 真实模型仍为原生装备附件；本适配器不创建第二把枪、弩弦或假弹药的Ogre对象。
        active=true;visible=false;liveAmmoMesh.clear();
    }
    virtual void setVisible(bool on){visible=on;}
    virtual void update(const Vector3& fallback){position=barrel;}
    virtual bool createPhysical(Ogre::SceneNode*,const std::string&){active=true;return true;}
    // 原生destroyPhysical还负责注销异步Tracer，不能只关active造成查询对象泄漏。
    virtual void destroyPhysical(){GunClass::_NV_destroyPhysical();}
    virtual void aimAt(const Vector3&){ }
    virtual Vector3 getBarrelPos(){return barrel;}
    virtual Vector3 getBarrelPosForTrace(float){return barrel;}
    // 062原生检查原样使用原生传入目标点；不依赖插件上一帧身体点缓存决定能否起手。
    virtual Vector3 getAimDir(const Vector3& target){return AimDirection(barrel,target);}
    virtual float scoreTarget(Character* me,Character* target){
        if(!me||!target||!me->isEnemy(target,false))return 0;
        return RangedCombatClass::scoreTargetRange(me->getPosition(),target->getPosition(),maxRange,0);
    }
    // 物理弹道按选定瞄准点精确发出，角度误差为0；是否能开火仍要通过原生动画/视线/友军/计时检查。
    virtual float getAimCloseness(){return 0;}
    virtual bool isAnimationReadyToShoot(){return ready;}
    virtual void setAnimationReadyToShoot(bool on){ready=on;}
    virtual unsigned __int64 getAudioObject() const {Character* c=user.getCharacter();return c?c->getAudioObject():0;}
    virtual int getDamageMin(){return 0;}
    virtual int getDamageMax(){return 0;}
protected:
    virtual Ogre::SceneNode* getParentNode(){return 0;}
};
struct Slot {
    hand actor,target;HybridGun* gun;bool published,available,busy,pending;unsigned lastGate,lastAnimationGate;
    AimFrame aim;bool haveAim;unsigned aimSerial;
    Slot():gun(0),published(false),available(false),busy(false),pending(false),lastGate(~0U),lastAnimationGate(~0U),haveAim(false),aimSerial(0){}
};
std::map<hand,Slot*> slots;std::set<hand> pendingActors;std::vector<HybridGun*> retired;
// 061诊断由配置开关控制，不再以进程前N条耗尽后永久静默。
Slot* Find(Character* c){if(!c)return 0;std::map<hand,Slot*>::iterator i=slots.find(c->handle);return i==slots.end()?0:i->second;}
Slot* Find(GunClass* gun){for(std::map<hand,Slot*>::iterator i=slots.begin();i!=slots.end();++i)if(i->second->gun==gun)return i->second;return 0;}
bool Private(GunClass* gun){if(Find(gun))return true;for(size_t i=0;i<retired.size();++i)if(retired[i]==gun)return true;return false;}
Weapon* Equipped(Character* c){
    // 远程能力发现不能依赖“已经拔出”的stats.weapon，否则背负状态下永远无法进入拔枪流程。
    // 只读原生两个武器槽；不扫描背包，不制造/替换任何物品，不把Sword强转成Crossbow。
    if(!c||!c->isValid()||c->isDestroyed())return 0;Inventory* inventory=c->getInventory();if(!inventory)return 0;
    Weapon* w=inventory->getPrimaryWeapon();GameData* d=w?w->getGameData():0;if(d&&d->stringID=="1-IrisArsenal.mod")return w;
    w=inventory->getSecondaryWeapon();d=w?w->getGameData():0;return d&&d->stringID=="1-IrisArsenal.mod"?w:0;
}
// 079：库存里有锤枪属于远程能力，不能冒充手里已经拿着枪。原生hasAnythingEquipped
// 会调用hasCrossbowEquipped，工作/家具的收武器流程也消费此值；收起后必须恢复原生假值。
// 只读当前回调已有角色的实际武器/FCS身份，不按武器类别、玩家身份或动画名称猜测。
bool Held(Character* c){
    Weapon* weapon=c?c->getCurrentWeapon():0;GameData* current=weapon?weapon->getGameData():0;
    return current&&current->stringID=="1-IrisArsenal.mod";
}
// 原生EQUIP_CROSSBOW尚未进入RangedCombatClass.combatMode；安全窗口在这一明确任务中
// 完成同件锤枪的拔出，避免修正“已装备”谓词后冷起手一直等待。能力发现仍允许背负状态。
// 只读当前正在执行的身体任务，不以永久工作列表/远程开关代替它；不新增Hook或修改任务。
bool Equipping(Character* c){
    CharBody* body=c?c->getBody():0;Tasker* task=body?body->getCurrentAction():0;
    return task&&task->key()==EQUIP_CROSSBOW;
}
// 与原生shouldUseRangedWeapons的双臂/站姿条件一致；义肢是否可用仍交给MedicalSystem判断。
bool Eligible(Character* c){
    // 非本枪/未勾远程先直接转发，避免普通NPC也竞争自有状态锁。只读游戏值，不在这里进入Ogre。
    return Iris::Accepting()&&!IrisCombat::ProofOnly()&&c&&c->isValid()&&!c->isDestroyed()&&c->stats&&c->stats->rangedMode&&IrisCombat::HasRangedMoves()&&Equipped(c)&&
           c->isHuman()&&!c->isDead()&&!c->medical.isUnconcious()&&c->animation&&c->getProneState()==PS_NORMAL&&
           !c->isCrippled()&&c->medical.hasAnArmToFightWith()&&c->medical.isRightArmOk()&&c->medical.isLeftArmOk()&&c->rangedCombat;
}
// 构造/销毁和数据发布都在AI停止的安全阶段；独占gunData身份也覆盖已退役对象，普通枪不碰自有容器锁。
bool PrivateFast(GunClass* gun){return data&&gun&&gun->gunData==data;}
// 104：正式持有者使用动态map/set，保留身份去重；发现阶段不再按人数拒绝。
// 仍从既有受mutex保护的入口调用，不在此创建Gun或提前取得开火许可。
void Discover(Character* c){if(c&&!Find(c))pendingActors.insert(c->handle);}
// 原生getGun每帧会刷新gun；只有已准备的本枪能力对象才能交给它，其他所有角色/弩/炮台转发原链。
typedef bool(__fastcall* UseFn)(Character*);
typedef bool(__fastcall* HasFn)(AI*,const hand&,const Vector3&);
typedef float(__fastcall* ScoreFn)(AI*,const hand&,const Vector3&);
typedef GunClass*(__fastcall* GunFn)(RangedCombatClass*);
typedef void(__fastcall* AnimFn)(RangedCombatClass*,float,const Vector3&,RootObject*);
typedef void(__fastcall* ShotFn)(GunClass*,Character*,RootObject*,StatsEnumerated,const Vector3&);
typedef bool(__fastcall* ReloadFn)(RangedCombatClass*);
UseFn originalUse=0;HasFn originalHas=0,originalWithin=0;ScoreFn originalScore=0;GunFn originalGun=0;AnimFn originalAnimation=0;ShotFn originalShot=0;ReloadFn originalReload=0;
bool __fastcall UseHook(Character* c){
    // 078仅观察当前回调；普通角色原样转原生，没有新增能力/选招/开火资格。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_RANGED_USE);
    if(Eligible(c)){Guard lock(&audit);Discover(c);Slot* s=Find(c);return s&&s->published;}
    return originalUse?originalUse(c):false;
}
bool __fastcall HasHook(AI* ai,const hand& target,const Vector3& pos){
    // 078仅观察当前回调；普通角色原样转原生，没有新增能力/选招/开火资格。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_RANGED_HAS);
    // 079：只有实际拿着本锤枪才替代“当前装备弩”。收起/换持原生武器时转发原函数，
    // 使hasAnythingEquipped及工作前的空手要求得到真实结果；原参数和原函数调用次数保持。
    Character* c=ai?ai->me:0;if(Eligible(c)){const bool held=Held(c);
        Guard lock(&audit);Discover(c);Slot* s=Find(c);if(held)return s&&s->published;}
    return originalHas?originalHas(ai,target,pos):false;
}
float __fastcall ScoreHook(AI* ai,const hand& target,const Vector3& pos){
    // 078仅观察当前回调；普通角色原样转原生，没有新增能力/选招/开火资格。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_RANGED_SCORE);
    Character* c=ai?ai->me:0;if(Eligible(c)){
        bool ready=false;{Guard lock(&audit);Discover(c);Slot* s=Find(c);ready=s&&s->published;}
        if(!ready)return 0;
        // 对照原生scoreRangedAttack，仅补上本枪能力识别；保留近战压制0.1及队形完整1/0.5的评分。
        Character* other=target.getCharacter();if(other&&(!other->isValid()||other->isDestroyed()||other->isDead()||!c->isEnemy(other,false)))return 0;
        if(c->isLiterallyUnderMeleeAttackRightNowForSure())return .1f;
        Platoon* p=ai->getPlatoon();return p&&p->isIntact()?1.f:.5f;
    }return originalScore?originalScore(ai,target,pos):0;
}
bool __fastcall WithinHook(AI* ai,const hand& target,const Vector3& pos){
    // 078仅观察当前回调；普通角色原样转原生，没有新增能力/选招/开火资格。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_RANGED_WITHIN);
    Character* c=ai?ai->me:0;float range=0;
    if(Eligible(c)){Guard lock(&audit);Slot* s=Find(c);if(s&&s->published)range=s->gun->maxRange;}
    if(range>0)return ai->isWithinGivenRange(target,pos,range);
    return originalWithin?originalWithin(ai,target,pos):false;
}
GunClass* __fastcall GunHook(RangedCombatClass* ranged){
    // 078仅观察当前回调；普通角色原样转原生，没有新增能力/选招/开火资格。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_RANGED_GUN);
    // 079：原生getGun也只认当前手持物。库存中的锤枪不能接管手里的真弩/炮台，
    // 更不能在已收武器进行工作时继续把私有Gun交给原生。槽的创建/销毁仍留在安全窗口。
    Character* c=ranged?ranged->me:0;if(Eligible(c)&&Held(c)){Guard lock(&audit);Discover(c);Slot* s=Find(c);return s&&s->published?s->gun:0;}
    return originalGun?originalGun(ranged):0;
}
void __fastcall AnimationHook(RangedCombatClass* ranged,float dt,const Vector3& aim,RootObject* target){
    // 078仅观察当前回调；普通角色原样转原生，没有新增能力/选招/开火资格。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_RANGED_ANIMATION);
    if(!ranged||!PrivateFast(ranged->gun)){if(originalAnimation)originalAnimation(ranged,dt,aim,target);return;}
    bool own=false;Character* c=ranged->me;const bool allowed=Eligible(c);
    {Guard lock(&audit);if(ranged&&Private(ranged->gun)){own=true;Slot* s=Find(ranged->gun);if(!s)c=0;
        // 原生弩的CB aim/reload动画不适用于本枪；保留它的完整状态机，只替换这一处动画适配。
        if(s){
            // 062恢复原适配的就绪条件。原生reAssessTargeting先于此回调，不能用上一安全帧的
            // aim.target相等或haveAim再否决新目标；真正发射仍刷新快照，原生视线/计时门不绕过。
            s->gun->ready=s->available&&s->published&&!s->busy&&!s->pending&&allowed;
            const bool sameTarget=target&&s->haveAim&&s->aim.target==target->handle;
            unsigned gate=(s->available?1:0)|(s->published?2:0)|(s->busy?4:0)|(s->pending?8:0)|(allowed?16:0)|(target?32:0)|(s->haveAim?64:0)|(sameTarget?128:0)|(s->gun->ready?256:0);
            if(gate!=s->lastAnimationGate){s->lastAnimationGate=gate;if(IrisDiagnostics::DetailsEnabled()){
                std::ostringstream out;out<<"ranged_animation_gate actor="<<s->actor.index<<":"<<s->actor.serial<<" ready="<<s->gun->ready<<" available="<<s->available<<" published="<<s->published<<" busy="<<s->busy<<" pending="<<s->pending<<" eligible="<<allowed<<" target_present="<<(target!=0)<<" aim_cached="<<s->haveAim<<" cached_target_matches="<<sameTarget<<" cache_match_required=0"<<" aim_timer="<<ranged->aimTimer;Iris::Log(out.str());}}
        }}}
    if(!own){if(originalAnimation)originalAnimation(ranged,dt,aim,target);return;}
    if(c&&target&&Iris::Finite(aim))c->lookatPosition(aim,true);
}
void __fastcall ShotHook(GunClass* gun,Character* c,RootObject* target,StatsEnumerated stat,const Vector3& aim){
    // 078仅观察当前回调；普通角色原样转原生，没有新增能力/选招/开火资格。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_RANGED_SHOT);
    if(!PrivateFast(gun)){if(originalShot)originalShot(gun,c,target,stat,aim);return;}
    bool own=false;const bool allowed=Eligible(c);Character* victim=target?target->handle.getCharacter():0;
    const bool targetValid=victim&&victim->isValid()&&!victim->isDestroyed();
    {Guard lock(&audit);if(Private(gun)){own=true;Slot* s=Find(gun);
        if(s&&s->actor==c&&s->published&&!s->busy&&!s->pending&&allowed&&targetValid){
            // 一次原生射击许可对应一整套20发/3发/四脉冲动作；此回调不碰Ogre/健康，不生成额外弩箭。
            s->target=victim->handle;s->pending=true;s->busy=true;s->gun->ready=false;
            if(IrisDiagnostics::DetailsEnabled()){std::ostringstream o;o<<"ranged_action_requested actor="<<s->actor.index<<":"<<s->actor.serial<<" target="<<s->target.index<<":"<<s->target.serial<<" native_shot_suppressed=1";Iris::Log(o.str());}
        }}}
    // 故障/切换后的退役适配器也绝不落入原生shoot，防止双弹体和双伤害。真正原生枪全部原样转发。
    if(!own&&originalShot)originalShot(gun,c,target,stat,aim);
}
bool __fastcall ReloadHook(RangedCombatClass* ranged){
    // 078仅观察当前回调；普通角色原样转原生，没有新增能力/选招/开火资格。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_RANGED_RELOAD);
    if(!ranged||!PrivateFast(ranged->gun))return originalReload?originalReload(ranged):false;
    bool own=false,before=false;
    {Guard lock(&audit);own=ranged&&Private(ranged->gun);if(own)before=ranged->_isReloading;}
    bool result=originalReload?originalReload(ranged):false;
    {Guard lock(&audit);if(own&&ranged&&Private(ranged->gun)){
        // 不用墙钟或自制冷却器；原生reloadCheck消耗同一游戏时间。完成后去掉它额外重设的0.4瞄准等待。
        if(before&&!ranged->_isReloading)ranged->aimTimer=0;
        if(before!=ranged->_isReloading&&IrisDiagnostics::DetailsEnabled()){std::ostringstream o;o<<"ranged_interval state="<<(ranged->_isReloading?"begin":"complete")<<" native_duration="<<ranged->reloadTimerMax<<" remaining="<<ranged->reloadTimer<<" ammo_type_null=1";Iris::Log(o.str());}
    }}return result;
}
void Install(){
    // 八个能力边界均通过成员指针解析，安装完前Accepting=false。没有改虚表、代码偏移或对象布局。
    if(KenshiLib::AddHook(Iris::RangedAddress(USE_RANGED),reinterpret_cast<void*>(&UseHook),&originalUse)!=KenshiLib::SUCCESS||
       KenshiLib::AddHook(Iris::RangedAddress(HAS_RANGED),reinterpret_cast<void*>(&HasHook),&originalHas)!=KenshiLib::SUCCESS||
       KenshiLib::AddHook(Iris::RangedAddress(SCORE_RANGED),reinterpret_cast<void*>(&ScoreHook),&originalScore)!=KenshiLib::SUCCESS||
       KenshiLib::AddHook(Iris::RangedAddress(WITHIN_RANGE),reinterpret_cast<void*>(&WithinHook),&originalWithin)!=KenshiLib::SUCCESS||
       KenshiLib::AddHook(Iris::RangedAddress(GET_GUN),reinterpret_cast<void*>(&GunHook),&originalGun)!=KenshiLib::SUCCESS||
       KenshiLib::AddHook(Iris::RangedAddress(ANIMATION),reinterpret_cast<void*>(&AnimationHook),&originalAnimation)!=KenshiLib::SUCCESS||
       KenshiLib::AddHook(Iris::RangedAddress(SHOOT),reinterpret_cast<void*>(&ShotHook),&originalShot)!=KenshiLib::SUCCESS||
       KenshiLib::AddHook(Iris::RangedAddress(RELOAD),reinterpret_cast<void*>(&ReloadHook),&originalReload)!=KenshiLib::SUCCESS||
       !originalUse||!originalHas||!originalScore||!originalWithin||!originalGun||!originalAnimation||!originalShot||!originalReload)throw std::runtime_error("ranged adapter hook installation incomplete");
    // 079一次运行标识区分实际DLL；不增加逐帧日志/锁/线程，现有Hook审计开关继续有效。
    Iris::Log("ranged_equipment_ready contract=IRIS_EQUIPMENT_STATE_079 capability=inventory equipped=actual_hands get_gun=actual_hands equip_task=native_EQUIP_CROSSBOW new_hooks=0 new_threads=0");
    Iris::Log("ranged_gate_ready contract=IRIS_RANGED_GATE_062 native_reassessment_cache_match_required=0 selection_after_native_permission=1 request_move_snapshot=0 no_new_hooks=1");
    Iris::Log("ranged_model_ready contract=IRIS_COMBAT_POLICY_061 prediction=emit_only_effective_speed beam=emit_only_instant_body log_detail_limit=0 new_hooks=0 new_threads=0");
    Iris::Log(std::string("ranged_aim_ready contract=")+SHARED_AIM_CONTRACT+" origin=actual_attachment_world point=native_getAimPos_or_body source_shared=1 origin_offset_changed=0 new_queries=0 new_threads=0");
    std::ostringstream status;status<<"ranged_hooks_ready capability_adapter=GunClass same_inventory_weapon=1 native_target_movement_LOS_reload=1 interval_native_units="<<actionInterval;Iris::Log(status.str());
}
void Config(){
    if(data)return;GameDataCopyStandalone* d=new GameDataCopyStandalone();
    try{d->initialise(GUN_DATA,false);d->name="Iris private ranged parameters";d->stringID="IrisArsenal/runtime-ranged";
        // GunClass::maxRange之外，原生辅助分支仍可能读取私有GUN_DATA；不能残留360使FCS10000与能力数据冲突。
        float range=IrisCombat::RangedRange();if(!Iris::Finite(range)||range<=0||double(range)>2147483646.0)throw std::runtime_error("private ranged FCS range not ready");
        d->idata["range"]=int(ceilf(range));d->idata["accuracy perfect skill"]=100;d->idata["num shots"]=1;
        d->fdata["accuracy deviation at 0 skill"]=0;d->fdata["aim speed"]=1;d->fdata["shot speed"]=320; // 062恢复原适配的起手参数；发射瞄准单独按该发实际速度计算。
        d->fdata["reload time min"]=d->fdata["reload time max"]=actionInterval;
        d->fdata["barrel pos Z"]=d->fdata["barrel pos Y"]=0;d->filesdata["live ammo"]="";
        // 独占记录的ammo/reload anim引用表为空，原生因此不查背包也不播弩装填；不改任何共享FCS记录。
        d->clearList("ammo");d->clearList("reload anim");data=d;
    }catch(...){delete d;throw;}
}
void Prepare(GameWorld* world){
    IrisDiagnostics::Set(IrisDiagnostics::RETIRED_GUNS,retired.size());
    // 只从已确认AI/物理静止阶段进入。换世界时先保留对象，等原生队列清空后才走标准GunClass析构。
    if(world&&world->physics&&world->physics->queuesAreClearMT()){
        while(!retired.empty()){HybridGun* gun=retired.back();retired.pop_back();delete gun;}
    }
    for(std::map<hand,Slot*>::iterator i=slots.begin();i!=slots.end();){Slot* s=i->second;Character* c=i->first.getCharacter();
        // 每个安全窗口重新发布许可；模型/动画暂不可用或演员未被消费时，不沿用上一帧“可开火”。
        s->available=false;s->gun->ready=false;
        if(!Eligible(c)){
            Finish(s->actor);
            if(c&&c->isValid()&&!c->isDestroyed()&&c->rangedCombat&&c->rangedCombat->gun==s->gun){
                if(c->animation&&c->rangedCombat->combatMode)c->rangedCombat->end();c->rangedCombat->gun=0;
            }
            retired.push_back(s->gun);delete s;slots.erase(i++);
        }else{
            Weapon* item=Equipped(c);
            // 079：已装备状态必须等实际拔出后才为真；在原生EQUIP_CROSSBOW任务中完成
            // 旧适配缺失的拔枪阶段。研究/耕作不是该任务，不因勾选远程就拔枪；既有远程
            // combatMode路径保持。仍使用原生drawWeapon与实际槽名，不直接写附件或身体姿态。
            const bool equipping=Equipping(c);
            if(item&&(c->rangedCombat->combatMode||equipping)&&c->getCurrentWeapon()!=item)c->drawWeapon(item,item->inventorySection);
            if(Iris::ActorReady(c))IrisCombat::Observe(c);++i;
        }
    }
    if(!pendingActors.empty())Config();
    for(std::set<hand>::iterator i=pendingActors.begin();i!=pendingActors.end();++i){Character* c=i->getCharacter();
        // 104：去掉正式8人及含待回收实例16个的间接人数门，仍逐个重验资格和重复身份。
        // retired继续等原生队列清空后析构，不以提前释放在用Gun换取容量。
        if(!Eligible(c)||Find(c))continue;
        Slot* s=new Slot();try{s->actor=*i;s->gun=new HybridGun(data);s->gun->user=*i;
            // 枪口尚未就绪时，原生移动阶段的视线查询也先使用真实角色位置，不能从世界零点发起。
            // available仍关闭，只有安全阶段Publish实际附件枪口后才可能生成攻击。
            s->gun->barrel=c->getPosition();s->gun->position=s->gun->barrel;
            s->gun->maxRange=IrisCombat::RangedRange();s->published=s->gun->maxRange>0;
            // 尚无真实附件也先发布能力，原生可开始选敌/拔枪；available仍为false，不会从脚底发射。
            slots.insert(std::make_pair(*i,s));if(Iris::ActorReady(c))IrisCombat::Observe(c);
            if(IrisDiagnostics::DetailsEnabled()){std::ostringstream o;o<<"ranged_capability_ready actor="<<i->index<<":"<<i->serial<<" inventory_item_type_unchanged=1 ammo=none reload_min="<<actionInterval<<" reload_max="<<actionInterval;Iris::Log(o.str());}
        }catch(...){slots.erase(*i);delete s->gun;delete s;throw;}
    }pendingActors.clear();IrisDiagnostics::Set(IrisDiagnostics::RETIRED_GUNS,retired.size());
}
bool CaptureAim(Character* c,const Vector3& muzzle,AimFrame& frame,float effectiveShotSpeed,bool instant){
    Slot* s=Find(c);RangedCombatClass* rc=c?c->rangedCombat:0;
    if(!s||!s->published||!rc||!rc->combatMode||rc->gun!=s->gun||!Iris::Finite(muzzle))return false;
    // 062真实炮口保持；默认发布只读原生点，不重算原生流程或写入currentAimPos。
    s->gun->barrel=muzzle;s->gun->position=muzzle;
    const bool firing=Iris::Finite(effectiveShotSpeed)&&effectiveShotSpeed>0;
    Character* target=rc->_getAttackTarget().getCharacter();
    if(target&&target->isValid()&&!target->isDestroyed()){
        Vector3 point=rc->currentAimPos;
        if(firing){
            if(instant)point=NativeBodyPoint(target);
            else{
                // 原生getAimPos的速度参数来自私有Gun字段；仅在既有安全主线程临时传值，
                // 离开本次计算就恢复Gun与提前量字段。异常也恢复，不改变下一轮原生起手判断。
                struct PredictionInput {
                    GunClass* gun;RangedCombatClass* ranged;float speed,ahead;
                    PredictionInput(GunClass* g,RangedCombatClass* r,float value):gun(g),ranged(r),speed(g->shotSpeed),ahead(r->_lastAimAheadAmount){gun->shotSpeed=value;}
                    ~PredictionInput(){gun->shotSpeed=speed;ranged->_lastAimAheadAmount=ahead;}
                } input(s->gun,rc,effectiveShotSpeed);
                point=rc->getAimPos(target);
            }
        }
        if(!Iris::Finite(point))return false;
        s->aim.point=point;s->aim.target=target->handle;s->aim.source=!firing?"native_currentAimPos":instant?"native_body_instant":"native_getAimPos_speed_matched";s->haveAim=true;
    }else{if(!s->busy||!s->haveAim)return false;s->aim.source="last_native_aim";}
    Vector3 delta=s->aim.point-muzzle;
    if(!Iris::Finite(delta)||!Iris::Finite(delta.squaredLength())||delta.squaredLength()<=.000001f)return false;
    s->aim.muzzle=muzzle;s->aim.direction=AimDirection(muzzle,s->aim.point);s->aim.effectiveSpeed=firing&&!instant?effectiveShotSpeed:0.f;s->aim.instant=firing&&instant;
    s->aim.sequence=++s->aimSerial;frame=s->aim;return true;
}
void Publish(Character* c,bool ready,float range,const Vector3& muzzle){
    Slot* s=Find(c);if(!s)return;s->published=Iris::Finite(range)&&range>0&&Iris::Finite(muzzle);
    if(s->published){s->gun->maxRange=range;s->gun->barrel=muzzle;s->gun->position=muzzle;}
    // 062恢复原适配发布合同，不预选技能、不用预测模型或目标快照一致性增加开火门。
    AimFrame aim;const bool aimReady=s->published&&CaptureAim(c,muzzle,aim);
    s->available=ready&&aimReady;s->gun->ready=s->available&&s->published&&!s->busy&&!s->pending&&Eligible(c);
    // 在安全主线程记录真正远程关口，只读原生状态；不调用takeTheShotCheck做诊断，不跳过视线/友军检查。
    // 旧日志没有目标距离，不能倒推那次空等一定由FCS造成；新日志持续记录状态变化，区分范围与原生尚未许可。
    RangedCombatClass* rc=c?c->rangedCombat:0;Character* target=rc?rc->_getAttackTarget().getCharacter():0;
    if(rc&&rc->combatMode&&target&&target->isValid()&&!target->isDestroyed()){
        float distance=(target->getPosition()-c->getPosition()).length();bool inRange=Iris::Finite(distance)&&distance<=range;
        unsigned gate=(ready?1:0)|(inRange?2:0)|(s->busy?4:0)|(s->pending?8:0)|(rc->_isReloading?16:0)|(static_cast<unsigned>(rc->state)<<5)|(rc->takeAShotMsg?256:0)|(aimReady?512:0);
        if(gate!=s->lastGate){s->lastGate=gate;if(IrisDiagnostics::DetailsEnabled()){std::ostringstream out;out<<"ranged_gate actor="<<s->actor.index<<":"<<s->actor.serial<<" target="<<target->handle.index<<":"<<target->handle.serial<<" distance="<<distance<<" FCS_max="<<range<<" plugin_ready="<<ready<<" native_aim_ready="<<aimReady<<" effective_shot_speed="<<s->gun->shotSpeed<<" prediction_model=original_native_gate"<<" gun_ready="<<s->gun->ready<<" state="<<int(rc->state)<<" busy="<<s->busy<<" pending="<<s->pending<<" take_shot="<<rc->takeAShotMsg<<" aim_timer="<<rc->aimTimer<<" reload="<<rc->_isReloading<<" reason="<<(!inRange?"outside_FCS_range":s->pending?"queued_for_action":s->busy?"action_in_progress":!ready?"plugin_not_ready":rc->_isReloading?"native_reload":"waiting_native_shot_gate")<<" native_LOS_and_friendly_checks=preserved";Iris::Log(out.str());}}
    }

}
bool TakeRequest(Character* c,hand& target){Slot* s=Find(c);if(!s||!s->pending||!Eligible(c))return false;s->pending=false;target=s->target;return true;}
void Finish(const hand& actor){
    std::map<hand,Slot*>::iterator i=slots.find(actor);if(i==slots.end())return;Slot* s=i->second;
    if(!s->busy&&!s->pending)return;s->busy=false;s->pending=false;s->gun->ready=false;s->haveAim=false;
    // 整套动作结束/中断才耗掉这一次“射击许可”；下一次原生reloadCheck据此开始配置间隔。
    s->gun->numShotsCurrent=0;
    // 在收尾这一刻用原生入口建立装填计时，避免切换远程开关就丢失间隔；不手工递减/换算计时器。
    Character* c=actor.getCharacter();RangedCombatClass* ranged=c&&c->isValid()&&!c->isDestroyed()&&c->stats&&c->animation?c->rangedCombat:0;
    if(ranged&&ranged->gun==s->gun&&!ranged->_isReloading)ReloadHook(ranged);
}
bool Active(Character* c){Slot* s=Find(c);return s&&s->published&&Eligible(c)&&c->rangedCombat->combatMode&&c->rangedCombat->gun==s->gun;}
bool Tracked(Character* c){return Find(c)!=0;}
void Reset(){
    // 读档/关闭回调不假定AI已经停下；保留Gun及其原生异步Tracer到下一安全阶段，避免悬空指针。
    for(std::map<hand,Slot*>::iterator i=slots.begin();i!=slots.end();++i){i->second->gun->ready=false;retired.push_back(i->second->gun);delete i->second;}
    slots.clear();pendingActors.clear();IrisDiagnostics::Set(IrisDiagnostics::RETIRED_GUNS,retired.size());
}
}
