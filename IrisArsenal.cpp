// 064钻天破源厚环时序与终结源爆炸修正；未改变战斗或其他九招。
// 063：仅火神大小源准星/旋转与脉冲原枪口爆发；原生战斗/远程起手/碰撞和伤害保持。
// 058：电脉范围/光柱共用原生实际枪口轴；坐锤原资产以真实人体/锤体表面验收。
// IrisArsenal 0.4.26：075正式十招各持有者独立起手；072近战复用原生肢体/姿态并保留原生回退；067三招源特效由IrisCombat消费，其他动作保持；源身体/Prop2/root由FCS播放；十招消费者独立，闭环保留为显式诊断模式。
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>
#include "IrisCombat.h"
#include "IrisRanged.h"
#include "IrisDiagnostics.h"
#include "IrisNativeAudit.h"
#include "native/IniValues.h"
#include <core/Functions.h>
#include <Debug.h>
#include <kenshi/Globals.h>
#include <kenshi/GameWorld.h>
#include <kenshi/GameData.h>
#include <kenshi/Character.h>
#include <kenshi/CharStats.h>
#include <kenshi/Gear.h>
#include <kenshi/GunClass.h>
#include <kenshi/AI/AI.h>
#include <kenshi/combat/RangedCombatClass.h>
#include <kenshi/PhysicsActual.h>
// physHit的完整定义在CharMovement.h；UtilityT只有前置声明，构造/赋值查询结果前必须包含此头。
#include <kenshi/CharMovement.h>
#include <kenshi/util/UtilityT.h>
#include <kenshi/Animation/AnimationClass.h>
#include <kenshi/combat/CombatClass.h>
#include <kenshi/combat/CombatTechniqueData.h>
#include <kenshi/Renderer.h>
#include <ogre/OgreAnimationState.h>
#include <ogre/OgreColourValue.h>
#include <ogre/OgreEntity.h>
#include <ogre/OgreSubEntity.h>
#include <ogre/OgreMesh.h>
#include <ogre/OgreOldSkeletonInstance.h>
#include <ogre/OgreTagPoint.h>
#include <ogre/OgreMatrix3.h>
#include <ogre/OgreMatrix4.h>
#include <ogre/OgreManualObject.h>
#include <ogre/OgreSceneManager.h>
#include <ogre/OgreSceneNode.h>
#include <ogre/OgreResourceGroupManager.h>
#include <algorithm>
#include <cmath>
#include <float.h>
#include <fstream>
#include <sstream>
#include <map>
#include <set>
#include <string>
#include <stdexcept>
#include <cstring>

namespace Iris {
// 093只在本次只读骨架扫描内复用子节点数量，不跨帧保留Ogre对象。
bool attachmentCountReuse=true;
using Ogre::Vector3;using Ogre::Quaternion;using Ogre::Matrix4;
const char* WEAPON="1-IrisArsenal.mod";
const char* TECH="3-IrisArsenal.mod";
const char* ANIM="IrisArsenal_DrillProof";
const char* GROUP="IrisArsenal/DrillProof/v1";
const char* CONTRACT="IRIS_EIGHT_042";
CRITICAL_SECTION mutex;
struct Lock {
    IrisDiagnostics::HookAudit* audit;
    explicit Lock(IrisDiagnostics::HookAudit* value=0):audit(value){if(audit)audit->BeforeLock();EnterCriticalSection(&mutex);if(audit)audit->Acquired();}
    ~Lock(){if(audit)audit->BeforeUnlock();LeaveCriticalSection(&mutex);}
};
volatile LONG started=0,running=0,mainThread=0;
bool enabled=true,debugDraw=false,queries=true,faulted=false,resources=false;
unsigned maxActive=1;
std::string drillMaterials[19];
std::wstring directory,logPath;
Ogre::SceneManager* scene=0;Renderer* renderer=0;
CombatTechniqueData* technique=0;
// 这一把私有技巧仅分配一次，地址可能被原生AI短暂引用；没有按施放次数增长的技巧分配。
// SDK未提供析构入口，保留至进程退出；角色/场景对象不由它持有。
struct Capsule {float a,b,r;};
struct Profile {
    float length,appear,spin,stopSpin,returnStart,hidden,end,frequency,period;
    Vector3 pivot;Capsule slices[8];
} profile;
bool Finite(float x){return _finite(x)!=0;}
bool Finite(const Vector3& p){return Finite(p.x)&&Finite(p.y)&&Finite(p.z);}
std::string Utf8(const std::wstring& w){
    int n=WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,w.c_str(),int(w.size()),0,0,0,0);
    if(n<=0)throw std::runtime_error("UTF8 path conversion failed");
    std::string s(n,'\0');WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,w.c_str(),int(w.size()),&s[0],n,0,0);return s;
}
// 052：统一日志门与缓冲落盘；EnableLogging=0关闭文件输出和新增审计，不创建监视线程。
void Log(const std::string& message){IrisDiagnostics::Log(message);}
template<class Method> intptr_t Native(Method method,const char* label){
    // 使用已有SDK成员指针。先核验桩表范围，避免GetRealAddress断言；无修饰函数签名、RVA或对象偏移。
    HMODULE lib=GetModuleHandleW(L"KenshiLib.dll");void* stub=0;
    if(!lib||sizeof(method)<sizeof(stub))throw std::runtime_error("SDK method pointer unavailable");
    std::memcpy(&stub,&method,sizeof(stub));uintptr_t p=reinterpret_cast<uintptr_t>(stub);
    uintptr_t begin=reinterpret_cast<uintptr_t>(GetProcAddress(lib,"FUNC_BEGIN")),end=reinterpret_cast<uintptr_t>(GetProcAddress(lib,"FUNC_END"));
    if(!begin||end<=begin||p<begin||p>=end)throw std::runtime_error(std::string("SDK stub range mismatch: ")+label);
    intptr_t target=KenshiLib::GetRealAddress(method);if(!target)throw std::runtime_error(std::string("SDK binding unavailable: ")+label);
    {std::ostringstream s;s<<"binding "<<label<<" target="<<std::hex<<target;Log(s.str());}return target;
}
// 所有原生入口仍经现有SDK桩范围检查和地址式解析；不写修饰签名、硬地址或对象偏移。
// 六招特效近战与三远程共用原受击反应入口；SDK成员地址解析，不增加钩子或硬编码偏移。
void* MeleeStumbleTarget(){return reinterpret_cast<void*>(Native(&Character::_startStumble,"melee_stumble_gate"));}
// 043只拦本插件六招有效近战的主动格挡检查；地址仍从SDK成员桩解析，不写函数签名或固定RVA。
void* MeleeBlockCheckTarget(){return reinterpret_cast<void*>(Native(&CombatClass::checkForNeedBlock,"melee_block_check"));}
void* VulcanDefenceTarget(){return reinterpret_cast<void*>(Native(&CombatClass::_iHitYouAreYouHit,"vulcan_defence_gate"));}
// 远程扩展沿用同一桩范围检查。只增加能力/发射适配，不伪造Crossbow指针或改变库存物品。
bool Accepting(){return InterlockedCompareExchange(&running,0,0)!=0&&enabled&&!faulted;}
void* RangedAddress(unsigned binding){
    switch(binding){
    case IrisRanged::USE_RANGED:return reinterpret_cast<void*>(Native(&Character::shouldUseRangedWeapons,"ranged_use"));
    case IrisRanged::HAS_RANGED:return reinterpret_cast<void*>(Native(&AI::hasCrossbowEquipped,"ranged_capability"));
    case IrisRanged::SCORE_RANGED:return reinterpret_cast<void*>(Native(&AI::_NV_scoreRangedAttack,"ranged_score"));
    case IrisRanged::WITHIN_RANGE:return reinterpret_cast<void*>(Native(&AI::isWithinMyBowRange,"ranged_range"));
    case IrisRanged::GET_GUN:return reinterpret_cast<void*>(Native(&RangedCombatClass::getGun,"ranged_gun"));
    case IrisRanged::ANIMATION:return reinterpret_cast<void*>(Native(&RangedCombatClass::animationUpdate,"ranged_animation"));
    case IrisRanged::SHOOT:return reinterpret_cast<void*>(Native(&GunClass::shoot,"ranged_shot"));
    case IrisRanged::RELOAD:return reinterpret_cast<void*>(Native(&RangedCombatClass::reloadCheck,"ranged_reload"));
    default:throw std::runtime_error("ranged binding index invalid");
    }
}
void ReadAssets(){
    IrisDiagnostics::Scope timing(IrisDiagnostics::ASSET_READ,"configuration_and_profiles");
    const std::wstring ini=directory+L"IrisArsenal.ini";
    enabled=IrisIni::Flag(ini,L"IrisArsenal",L"Enabled",true);
    // 常规观察默认只显示源模型；握点/胶囊线框仍可通过DebugDraw=1单独打开。
    debugDraw=IrisIni::Flag(ini,L"IrisArsenal",L"DebugDraw",false);
    attachmentCountReuse=IrisIni::Flag(ini,L"IrisArsenal",L"EnableAttachmentCountReuse",true);
    {std::ostringstream out;out<<"weapon_attachment_lookup_ready contract=IRIS_QUERY_BOUNDARY_093 child_count_reuse="<<attachmentCountReuse<<" disabled=legacy original_budgets=256,512 cross_frame_pointers=0";Log(out.str());}
    queries=IrisIni::Flag(ini,L"IrisArsenal",L"ContactQueries",true);
    // 075：此旧限制仅由下方DrillProofOnly诊断分支消费；正式十招不再共用攻击名额。
    // 103诊断原型人数直接读取unsigned，不再把配置限制为1或2；正式十招仍不消费此限制。
    maxActive=IrisIni::Unsigned(IrisIni::Number(ini,L"IrisArsenal",L"MaxActiveActors",1),"MaxActiveActors");
    std::ifstream f((directory+L"assets\\drill.csv").c_str());std::string magic,tail;unsigned version,count,submeshes;
    if(!(f>>magic>>version>>count>>submeshes)||magic!="IRIS_DRILL"||version!=2||count!=8||submeshes!=19)throw std::runtime_error("drill profile header contract");
    if(!(f>>profile.length>>profile.appear>>profile.spin>>profile.stopSpin>>profile.returnStart>>profile.hidden>>profile.end
       >>profile.pivot.x>>profile.pivot.y>>profile.pivot.z>>profile.frequency>>profile.period))throw std::runtime_error("drill profile body contract");
    if(!Finite(profile.pivot)||!Finite(profile.length)||fabsf(profile.length-5.633333333f)>.0001f||
       !(0<profile.appear&&profile.appear<profile.spin&&profile.spin<profile.stopSpin&&profile.stopSpin<profile.returnStart&&profile.returnStart<profile.hidden&&profile.hidden<profile.end)||
       profile.end!=profile.length||profile.frequency!=15||fabsf(profile.period-4.125f)>.0001f)throw std::runtime_error("drill timeline mismatch");
    for(unsigned i=0;i<8;++i){Capsule& c=profile.slices[i];
        if(!(f>>c.a>>c.b>>c.r)||!Finite(c.a)||!Finite(c.b)||!Finite(c.r)||c.b<=c.a||c.r<=0||c.r>30||
           (i&&fabsf(c.a-profile.slices[i-1].b)>.0001f))throw std::runtime_error("drill capsule contract");}
    // v2尾部逐子网格保存源材质，和序列化mesh一起校验，不能依赖实体工厂的默认材质。
    for(unsigned i=0;i<19;++i){unsigned index;
        if(!(f>>index>>drillMaterials[i])||index!=i||drillMaterials[i].find("IrisArsenal/")!=0)throw std::runtime_error("drill material binding contract");
    }
    if(f>>tail)throw std::runtime_error("drill profile trailing data");
    IrisCombat::Configure(directory);
    IrisRanged::Configure(directory);
    // 072仅记录本次近战起手合同；日志开关沿用现有配置，不新增逐帧输出或监视线程。
    Log("IRIS_NATIVE_MELEE_072 native_medical_flags=1 standing_heavy_only=1 unarmed_and_prone_preserved=1 private_ranges_preserved=1 fallback=native new_hooks=0 new_threads=0");
}
bool UsesWeapon(CharStats* stats){
    if(!stats||!stats->hasWeapon())return false;Item* item=stats->weapon.getItem();Weapon* weapon=item?item->isWeapon():0;
    GameData* data=weapon?weapon->getGameData():0;return data&&data->stringID==WEAPON;
}
bool ActorReady(Character* c){
    // 092只观察本次同步接口，子耗时由根栈扣除；不改参数、次数、返回及所有权。
    IrisDiagnostics::InterfaceScope interfaceTiming(IrisDiagnostics::IF_ACTOR_READY);
return c&&c->isValid()&&!c->isDestroyed()&&c->isHuman()&&!c->isDead()&&!c->medical.isUnconcious()&&c->stats&&c->animation&&UsesWeapon(c->stats);}
struct Visual {
    Ogre::Entity* entity;Ogre::SceneNode* anchor;Ogre::SceneNode* part;Ogre::ManualObject* debug;
    Visual():entity(0),anchor(0),part(0),debug(0){}
    void Clear(bool alive){
        // 原生武器从不隐藏或换装，清理只释放本插件对象。先清指针，失败也不二次释放同一对象。
        Ogre::Entity* e=entity;Ogre::SceneNode* a=anchor;Ogre::SceneNode* p=part;Ogre::ManualObject* d=debug;entity=0;anchor=0;part=0;debug=0;
        if(!alive||!scene)return;
        try{if(p)p->detachAllObjects();if(a)a->detachAllObjects();}catch(const std::exception& x){Log(std::string("cleanup_detach_error: ")+x.what());}
        try{if(e)scene->destroyEntity(e);}catch(const std::exception& x){Log(std::string("cleanup_entity_error: ")+x.what());}
        try{if(d)scene->destroyManualObject(d);}catch(const std::exception& x){Log(std::string("cleanup_debug_error: ")+x.what());}
        try{if(p)scene->destroySceneNode(p);}catch(const std::exception& x){Log(std::string("cleanup_part_error: ")+x.what());}
        try{if(a)scene->destroySceneNode(a);}catch(const std::exception& x){Log(std::string("cleanup_anchor_error: ")+x.what());}
    }
    void Create(){
        try{
            anchor=scene->getRootSceneNode()->createChildSceneNode();part=anchor->createChildSceneNode();
            // 本机Ogre接口前两参是网格名、资源组；实例ID由场景分配，不能套用旧版的命名实例重载。
            IrisDiagnostics::Scope timing(IrisDiagnostics::VISUAL_CREATE,"proof_drill");
            entity=scene->createEntity("iris_drill.mesh",GROUP);IrisDiagnostics::Add(IrisDiagnostics::FRESH_VISUALS);
            if(entity->getNumSubEntities()!=19)throw std::runtime_error("drill mesh submesh mismatch");
            // 沿用已验证的Ephnel材质修复：只给自建钻头逐层指定源材质，并回读确认。
            // 默认材质名存在不代表实体已绑定本包纹理；不修改共享Mesh/原生武器，也不做Renderable偏移转换。
            for(unsigned i=0;i<19;++i){Ogre::SubEntity* sub=entity->getSubEntity(i);if(!sub)throw std::runtime_error("drill subentity missing");
                std::string before=sub->getMaterialName();sub->setMaterialName(drillMaterials[i],GROUP);
                if(sub->getMaterialName()!=drillMaterials[i])throw std::runtime_error("drill material binding rejected");
                // 066：和正式消费者一致，首次绘制前初始化圆环裁剪门；只写自有实例参数。
                sub->setCustomParameter(9,Ogre::Vector4(0,0,0,0));
                {std::ostringstream out;out<<"drill_material sub="<<i<<" before="<<before<<" after="<<sub->getMaterialName();Log(out.str());}
            }
            entity->setRenderQueueGroup(83);entity->setCastShadows(false);part->attachObject(entity);entity->setVisible(false);
            if(debugDraw){debug=scene->createManualObject();debug->setDynamic(true);debug->setRenderQueueGroup(95);debug->setCastShadows(false);scene->getRootSceneNode()->attachObject(debug);}
            Log("visual_created own_entity=1 source_submeshes=19 native_equipment_untouched=1");
        }catch(...){Clear(true);throw;}
    }
};
struct Candidate {
    AnimationClass* animation;bool verified,noted,active,haveContact;float clipLength,lastTime;unsigned start,consumed,cycle,stage,contactChanges,queryCount,aborts,rejected,probeErrors;
    hand contact;Vector3 lastMid[8];bool previous;Visual visual;
    Candidate():animation(0),verified(false),noted(false),active(false),haveContact(false),clipLength(0),lastTime(0),start(0),consumed(0),cycle(0),stage(99),contactChanges(0),queryCount(0),aborts(0),rejected(0),probeErrors(0),previous(false){}
};
std::map<hand,Candidate> actors;unsigned cycleSerial=0;
void End(Candidate& a,bool alive,const char* reason){
    if(a.active){std::ostringstream s;s<<"cycle_end id="<<a.cycle<<" reason="<<reason<<" clip="<<a.lastTime<<" queries="<<a.queryCount<<" aborted="<<a.aborts<<" rejected="<<a.rejected<<" probe_errors="<<a.probeErrors<<" native_weapon_restore_required=0 damage_calls=0";Log(s.str());}
    // 安全阶段预热后在本角色上有限复用；普通收招仅隐藏，避免每次起手重新加载高面数钻头。
    if(alive&&a.visual.entity){
        // 隐藏/清线框失败也必须回收自有对象，清理异常不能从原生回调逃出。
        try{a.visual.entity->setVisible(false);if(a.visual.debug)a.visual.debug->clear();}
        catch(const std::exception& e){Log(std::string("cleanup_idle_error: ")+e.what());a.visual.Clear(true);}
    }else if(!alive)a.visual.Clear(false);
    a.active=false;a.previous=false;a.haveContact=false;a.stage=99;
}
// 052：先落盘清理开始，再在清理后输出资源现值；不能把清理前峰值误当正常退出仍泄漏。
// 092读档推进诊断代数，正在借用的栈上下文仍由RAII退出，不提前释放。
void Clear(bool alive,const char* reason){IrisDiagnostics::ResetCombatInterfaceAudit();Log(std::string("lifecycle_clear_begin reason=")+reason);IrisDiagnostics::Flush(true);IrisRanged::Reset();IrisCombat::Clear(alive,reason);for(std::map<hand,Candidate>::iterator i=actors.begin();i!=actors.end();++i){End(i->second,alive,reason);i->second.visual.Clear(alive);}actors.clear();IrisDiagnostics::Summary(reason,true);IrisDiagnostics::Flush(true);}
bool Same(const hand& a,const hand& b){return !(a<b)&&!(b<a);}
Ogre::Entity* ActualWeaponLegacy(AnimationClass* a){
    Ogre::Skeleton::BoneIterator bones=a->skeleton->getBoneIterator();unsigned boneBudget=256,childBudget=512;
    while(bones.hasMoreElements()&&boneBudget&&childBudget){--boneBudget;Ogre::OldBone* bone=bones.getNext();if(!bone)continue;
        for(unsigned short j=0;j<bone->numChildren()&&childBudget;++j){--childBudget;
            Ogre::TagPoint* p=dynamic_cast<Ogre::TagPoint*>(bone->getChild(j));if(!p||p->getParentEntity()!=a->body)continue;
            Ogre::MovableObject* object=p->getChildObject();if(!object||object->getMovableType()!="Entity"||!object->isAttached()||!object->isVisible())continue;
            Ogre::Entity* e=static_cast<Ogre::Entity*>(object);
            if(e->getMesh()->getName().find("iris_weapon.mesh")!=std::string::npos)return e;
        }}return 0;
}
// 093保留旧骨骼/子节点顺序、256/512预算及全部匹配谓词，只省重复numChildren调用。
// 扫描内仅调用只读方法，数量仅在当前骨骼局部复用；原生动画更新后必须重新扫描。
// SDK的Entity枚举不可用，OldNode迭代器返回类型又与游戏库不同，故不引入这两种接口。
// 禁用时直接走原链；不缓存Entity/TagPoint/迭代器、不新增线程或场景锁。
Ogre::Entity* ActualWeapon(Character* c){
    IrisDiagnostics::InterfaceScope interfaceTiming(IrisDiagnostics::IF_WEAPON_LOOKUP);
    AnimationClass* a=c->animation;if(!a->body||!a->skeleton)return 0;
    IrisDiagnostics::InterfaceScope scanTiming(IrisDiagnostics::IF_WEAPON_SCAN);
    const bool audit=IrisDiagnostics::CollisionProfileEnabled();
    if(!attachmentCountReuse){
        if(audit)IrisDiagnostics::Add(IrisDiagnostics::WEAPON_COUNT_FALLBACK);
        return ActualWeaponLegacy(a);
    }
    if(audit)IrisDiagnostics::Add(IrisDiagnostics::WEAPON_COUNT_REUSE);
    Ogre::Skeleton::BoneIterator bones=a->skeleton->getBoneIterator();unsigned boneBudget=256,childBudget=512,visited=0;
    while(bones.hasMoreElements()&&boneBudget&&childBudget){--boneBudget;Ogre::OldBone* bone=bones.getNext();if(!bone)continue;
        const unsigned short children=bone->numChildren();
        for(unsigned short j=0;j<children&&childBudget;++j){--childBudget;if(audit)++visited;
            Ogre::TagPoint* p=dynamic_cast<Ogre::TagPoint*>(bone->getChild(j));if(!p||p->getParentEntity()!=a->body)continue;
            Ogre::MovableObject* object=p->getChildObject();if(!object||object->getMovableType()!="Entity"||!object->isAttached()||!object->isVisible())continue;
            Ogre::Entity* e=static_cast<Ogre::Entity*>(object);
            if(e->getMesh()->getName().find("iris_weapon.mesh")!=std::string::npos){
                if(audit&&visited)IrisDiagnostics::Add(IrisDiagnostics::WEAPON_CHILD_VISITS,visited);return e;
            }
        }}
    if(audit&&visited)IrisDiagnostics::Add(IrisDiagnostics::WEAPON_CHILD_VISITS,visited);return 0;
}

float Smooth(float x){x=std::max(0.f,std::min(1.f,x));return x*x*(3-2*x);}
float Extension(float t){if(t<=profile.appear||t>=profile.hidden)return 0;
    // 展开和开始旋转是两条独立时序：80ms内恢复实体厚度，不压缩人物/旋转段，也不改变查询代理。
    const float fullAt=std::min(profile.spin,profile.appear+.08f);
    if(t<fullAt)return .02f+.98f*Smooth((t-profile.appear)/(fullAt-profile.appear));
    if(t<=profile.returnStart)return 1;return 1-Smooth((t-profile.returnStart)/(profile.hidden-profile.returnStart));}
float Angle(float t){
    // 原源Y轴三关键帧，frequency=15；换基底后旋转轴是局部Z，不能又乘角色攻速或游戏速度。
    float active=std::max(0.f,std::min(t,profile.stopSpin)-profile.spin);
    float local=fmodf(active*profile.frequency,profile.period),middle=2.041666746f;
    return local<middle?3.141592654f*local/middle:3.141592654f+3.141592654f*(local-middle)/(profile.period-middle);
}
Matrix4 SourcePose(Ogre::Entity* actual){
    // 092只观察本次同步接口，子耗时由根栈扣除；不改参数、次数、返回及所有权。
    IrisDiagnostics::InterfaceScope interfaceTiming(IrisDiagnostics::IF_SOURCE_POSE);

    // normal网格坐标为R*C*源，Prop2配套R^-1；这里只在矩阵副本右乘R恢复C*源的共同坐标。
    Matrix4 basis(1,0,0,0, 0,0,1,0, 0,-1,0,0, 0,0,0,1);return actual->_getParentNodeFullTransform()*basis;
}
Matrix4 PartPose(const Matrix4& weapon,float t,float extension){
    Quaternion q(Ogre::Radian(Angle(t)),Vector3::UNIT_Z);Matrix4 part;part.makeTransform(profile.pivot,Vector3(1,1,extension),q);return weapon*part;
}
void PositionVisual(Candidate& a,const Matrix4& weapon,float t,float extension){
    Ogre::SceneNode* root=scene->getRootSceneNode();Vector3 position,scale;Quaternion rotation;weapon.decomposition(position,scale,rotation);
    if(!Finite(position)||!Finite(scale)||scale.x<=0||scale.y<=0||scale.z<=0)throw std::runtime_error("invalid weapon affine transform");
    a.visual.anchor->setPosition(root->convertWorldToLocalPosition(position));a.visual.anchor->setOrientation(root->convertWorldToLocalOrientation(rotation));
    // 两层节点保留M*T(pivot)*Rspin*Sextension次序，非均匀角色比例不能移到旋转后的错误一侧。
    Vector3 rootScale=root->_getDerivedScaleUpdated();if(fabsf(rootScale.x)<.0001f||fabsf(rootScale.y)<.0001f||fabsf(rootScale.z)<.0001f)throw std::runtime_error("invalid scene scale");
    a.visual.anchor->setScale(scale.x/rootScale.x,scale.y/rootScale.y,scale.z/rootScale.z);
    a.visual.part->setPosition(profile.pivot);a.visual.part->setOrientation(Quaternion(Ogre::Radian(Angle(t)),Vector3::UNIT_Z));a.visual.part->setScale(1,1,extension);
    a.visual.entity->setVisible(extension>.001f);
    // 066：索引末尾0被本机Ogre忽略，不能用作隐藏。圆环改由实例custom9在投影后裁剪，
    // 与上面的Angle(t)共用profile.spin；无提前静止环，也不改变源几何/相位或共享材质。
    const bool optics=t>=profile.spin&&t<profile.returnStart&&extension>.001f;
    const bool wasVisible=a.visual.entity->getSubEntity(15)->getCustomParameter(9).x>.5f;
    for(unsigned i=0;i<19;++i)if(i==0||i>=15)
        a.visual.entity->getSubEntity(i)->setCustomParameter(9,Ogre::Vector4(optics?1.f:0.f,0,0,0));
    if(wasVisible!=optics){std::ostringstream out;out<<"proof_drill_ring_gate contract=IRIS_DRILL_RING_GATE_066 clip="<<t<<" visible="<<optics<<" angle_rad="<<Angle(t)<<" shared_pose=1 GPU_verified=0";Log(out.str());}
}
void Line(Ogre::ManualObject* d,const Vector3& a,const Vector3& b,const Ogre::ColourValue& color){
    Ogre::SceneNode* root=scene->getRootSceneNode();d->position(root->convertWorldToLocalPosition(a));d->colour(color);d->textureCoord(0,0);
    d->position(root->convertWorldToLocalPosition(b));d->colour(color);d->textureCoord(0,0);
}
void Cross(Ogre::ManualObject* d,const Vector3& p,float r,const Ogre::ColourValue& c){
    Line(d,p-Vector3(r,0,0),p+Vector3(r,0,0),c);Line(d,p-Vector3(0,r,0),p+Vector3(0,r,0),c);Line(d,p-Vector3(0,0,r),p+Vector3(0,0,r),c);
}
void DrawDebug(Candidate& a,const Matrix4& weapon,const Matrix4& part,float extension){
    Ogre::ManualObject* d=a.visual.debug;if(!d)return;d->clear();d->begin("IrisArsenal/Debug",Ogre::RenderOperation::OT_LINE_LIST,GROUP);
    const Ogre::ColourValue grip(0,1,0,1),muzzle(1,.6f,0,1),tip(1,0,1,1),capsule(0,.85f,1,.6f);
    Vector3 g=weapon*Vector3::ZERO,m=weapon*profile.pivot,p=part*Vector3(0,0,profile.slices[7].b);
    Cross(d,g,.4f,grip);Cross(d,m,.5f,muzzle);if(extension>.001f){Cross(d,p,.5f,tip);Line(d,m,p,muzzle);
        // 胶囊与实际sphereTrace使用完全相同的变换和半径；线框明确是保守代理，不冒充逐三角精确碰撞。
        Vector3 vx(part[0][0],part[1][0],part[2][0]),vy(part[0][1],part[1][1],part[2][1]);float radial=std::max(vx.length(),vy.length());
        for(unsigned n=0;n<8;++n){const Capsule& s=profile.slices[n];Vector3 a0=part*Vector3(0,0,s.a),b0=part*Vector3(0,0,s.b);float r=s.r*radial;
            Vector3 axis=b0-a0;if(axis.squaredLength()<.00001f)continue;axis.normalise();Vector3 x=axis.crossProduct(Vector3::UNIT_Y);if(x.squaredLength()<.0001f)x=axis.crossProduct(Vector3::UNIT_X);x.normalise();Vector3 y=axis.crossProduct(x);
            for(unsigned j=0;j<12;++j){float u=float(j)*6.283185307f/12,v=float(j+1)*6.283185307f/12;
                Vector3 p0=(x*cosf(u)+y*sinf(u))*r,p1=(x*cosf(v)+y*sinf(v))*r;
                Line(d,a0+p0,a0+p1,capsule);Line(d,b0+p0,b0+p1,capsule);if(j%3==0)Line(d,a0+p0,b0+p0,capsule);
                // 两个半球轮廓补全轴向端帽，避免线框像圆柱而查询实际是胶囊。
                float h=float(j)*3.141592654f/12,k=float(j+1)*3.141592654f/12;
                Line(d,a0+(x*cosf(h)-axis*sinf(h))*r,a0+(x*cosf(k)-axis*sinf(k))*r,capsule);
                Line(d,b0+(x*cosf(h)+axis*sinf(h))*r,b0+(x*cosf(k)+axis*sinf(k))*r,capsule);
            }} }
    d->end();
}
void RejectQuery(Candidate& a,const char* reason,float raw,float length,float radius){
    // 接触只是诊断；不可用的返回值既不算命中，也不能升级为永久停用整套动作。
    // 明细日志持续保留原始数值，周期收尾另报累计数；旧日志缺值时不能猜成距离单位或初始重叠。
    ++a.rejected;{std::ostringstream out;
        unsigned bits=0;std::memcpy(&bits,&raw,sizeof(raw));out.precision(9);
        out<<"contact_query_rejected id="<<a.cycle<<" reason="<<reason<<" raw_fraction="<<raw<<" raw_t_bits=0x"<<std::hex<<bits<<std::dec<<" motion_length="<<length<<" radius="<<radius<<" policy=skip_query_keep_animation_and_visual";Log(out.str());}
}
void Query(Candidate& a,Character* caster,const Vector3& start,const Vector3& end,float radius,unsigned& budget){
    if(!budget)return;
    if(!Finite(start)||!Finite(end)||!Finite(radius)||radius<=0){RejectQuery(a,"invalid_input",0,0,radius);return;}
    Vector3 motion=end-start;float length=motion.length();if(!Finite(length)){RejectQuery(a,"invalid_length",0,length,radius);return;}if(length<.0001f)return;
    Vector3 direction=motion/length;float skipped=0;physHit hit(false,false,start.y);
    // 这是无伤害闭环的closest诊断，仅找首个非自身阻挡，不是正式钻头的多目标命中器。
    // 每演员每安全更新最多24次；只记录真实返回，不把预算不足/abort/坏返回称作MISS或完整覆盖。
    // 正式多接触消费者必须另按最新经验接入完整批次、墙阻挡/贯穿和可续查预算，不能复用这里的推进近似。
    bool found=false;
    for(unsigned pass=0;pass<4&&budget;++pass){--budget;++a.queryCount;physHit result(false,false,start.y);
        {IrisDiagnostics::Scope timing(IrisDiagnostics::PROOF_QUERY);UtilityT::sphereTrace(result,start+direction*skipped,direction*(length-skipped),radius,0xffffffffU,false);}
        if(result._traceWasAborted){++a.aborts;return;}if(!result.hit)return;
        if(!Finite(result.distance)||result.distance<0||result.distance>1.001f){RejectQuery(a,"fraction_outside_segment",result.distance,length-skipped,radius);return;}
        if(result.hitObject.getCharacter()!=caster){hit=result;found=true;break;}
        skipped+=std::min(1.f,result.distance)*(length-skipped)+std::max(.25f,radius*.5f);if(skipped>=length)return;
    }
    if(!found)return;
    // 仅记录真实返回的首次接触，不能把距离筛选当命中。自身/地形遮住后方不被隐瞒成“穿透成功”。
    const bool changed=!a.haveContact||!Same(a.contact,hit.hitObject);
    if(changed&&a.contactChanges<24){++a.contactChanges;a.haveContact=true;a.contact=hit.hitObject;Character* other=hit.hitObject.getCharacter();
        // 初始重叠t=0不读取未定义point；本诊断只需稳定身份与比例，坐标仅为可选日志。
        const bool pointValid=hit.distance>0&&Finite(hit.position);
        std::ostringstream s;s<<"contact id="<<a.cycle<<" object="<<hit.hitObject.index<<":"<<hit.hitObject.serial<<" self="<<(other==caster)<<" character="<<(other!=0)
          <<" fraction="<<hit.distance<<" point_valid="<<pointValid;
        if(pointValid)s<<" pos="<<hit.position.x<<","<<hit.position.y<<","<<hit.position.z;
        s<<" radius="<<radius<<" diagnostic_only=1 exhaustive=0 damage_calls=0";Log(s.str());}
}
void Probe(Candidate& a,Character* c,const Matrix4& part,const Vector3& origin,float extension){
    if(!queries||extension<=.001f){a.previous=false;return;}unsigned budget=24;
    Vector3 vx(part[0][0],part[1][0],part[2][0]),vy(part[0][1],part[1][1],part[2][1]);float radial=std::max(vx.length(),vy.length());
    for(unsigned i=0;i<8;++i){const Capsule& s=profile.slices[i];Vector3 x=part*Vector3(0,0,s.a)+origin,y=part*Vector3(0,0,s.b)+origin,mid=(x+y)*.5f;float radius=s.r*radial;
        Query(a,c,x,y,radius,budget);if(a.previous)Query(a,c,a.lastMid[i],mid,radius,budget);a.lastMid[i]=mid;
    }a.previous=true;
}
void Ensure(GameWorld* w){
    // 092只观察本次同步接口，子耗时由根栈扣除；不改参数、次数、返回及所有权。
    IrisDiagnostics::InterfaceScope interfaceTiming(IrisDiagnostics::IF_SETUP);

    Renderer* current=static_cast<Renderer*>(w->render);Ogre::SceneManager* sm=current?current->getSceneManager():0;if(!sm)return;
    if(scene&&scene!=sm){Clear(false,"scene_changed");resources=false;}scene=sm;renderer=current;
    if(!resources){IrisDiagnostics::Scope timing(IrisDiagnostics::RESOURCE_GROUP,"IrisArsenal/DrillProof/v1");Ogre::ResourceGroupManager& r=Ogre::ResourceGroupManager::getSingleton();if(!r.resourceGroupExists(GROUP)){r.createResourceGroup(GROUP);r.addResourceLocation(Utf8(directory+L"assets"),"FileSystem",GROUP);r.initialiseResourceGroup(GROUP);}resources=true;Log("resources_ready native_equipment_kept=1 no_actor_created=1");}
    if(!technique){GameData* d=w->gamedata.getData(TECH,COMBAT_TECHNIQUE);if(!d){if(IrisDiagnostics::DetailsEnabled())Log("missing_FCS_record; enable IrisArsenal.mod manually after packaging");return;}
        technique=new CombatTechniqueData(d);
        // 只清零本插件私有值对象，绕过构造器可能的缺省回退；不改公共FCS对象或其他角色的招式。
        technique->maxTargetHits=0;
        if(technique->animation!=ANIM||technique->numImpactPoints()!=1||technique->maxTargetHits!=0||technique->gainsGround||!Finite(technique->initialDistance)||technique->initialDistance<technique->minDistanceVsStatic)throw std::runtime_error("FCS prototype contract mismatch");
        // 076：诊断原型同样在首次交给原生前发布；随后只比较身份，不改变其独立无伤害流程。
        IrisCombat::PublishProofTechniqueIdentity(technique);
        Log("technique_ready private=1 maxTargetHits=0 no_health_entry=1 direction_and_movement=native");}
}
float frameDelta=0;
void Tick(GameWorld* w){
    // 092只观察本次同步接口，子耗时由根栈扣除；不改参数、次数、返回及所有权。
    IrisDiagnostics::InterfaceScope interfaceTiming(IrisDiagnostics::IF_WRAPPER);

    if(!enabled||faulted)return;
    if(!w||!w->initialized||w->gameResetting||w->isLoadingFromASaveGame()){Clear(scene!=0,"loading");return;}
    Ensure(w);if(!resources||!technique)return;
    if(!IrisCombat::ProofOnly()){IrisCombat::Tick(w,scene,frameDelta);return;}
    const bool paused=w->isPaused();
    // 预统计已持有实例，避免map顺序导致新演员先于旧演员突破上限。
    unsigned active=0;for(std::map<hand,Candidate>::const_iterator q=actors.begin();q!=actors.end();++q)if(q->second.active)++active;
    for(std::map<hand,Candidate>::iterator i=actors.begin();i!=actors.end();){
        Character* c=i->first.getCharacter();Candidate& a=i->second;
        if(!ActorReady(c)||!c->animation->node){End(a,true,"actor_or_weapon_invalid");a.visual.Clear(true);actors.erase(i++);continue;}
        if(a.animation!=c->animation){End(a,true,"animation_owner_changed");a.animation=c->animation;a.verified=false;a.noted=false;}
        a.verified=c->animation->hasAnimation(ANIM);Ogre::AnimationState* state=a.verified?c->animation->getAnimationState(ANIM):0;
        a.clipLength=state?state->getLength():0;a.verified=a.verified&&Finite(a.clipLength)&&a.clipLength>0;
        // 首次选招前在空闲阶段预热自有实例；总候选上限8，空闲不画、不查询。
        if(a.verified&&!a.visual.entity)a.visual.Create();
        if(!a.noted){a.noted=true;std::ostringstream s;s<<"animation_probe actor="<<i->first.index<<":"<<i->first.serial<<" ready="<<a.verified<<" loaded_length="<<a.clipLength;Log(s.str());}
        CombatClass* combat=c->getCombatClass();bool live=a.verified&&combat&&combat->getCurrentTechnique()==technique&&state&&state->getEnabled()&&state->getWeight()>.001f;
        float t=live?state->getTimePosition()/a.clipLength*profile.length:0;
        if(!live||!Finite(t)||t<0||t>=profile.end){End(a,true,"native_action_ended_or_interrupted");++i;continue;}
        if(a.active&&(a.consumed!=a.start||t+.001f<a.lastTime))End(a,true,"new_native_cycle");
        if(!a.active&&paused){++i;continue;}
        if(!a.active&&active<maxActive){if(!a.visual.entity)a.visual.Create();a.active=true;++active;a.consumed=a.start;a.cycle=++cycleSerial;a.stage=99;a.contactChanges=0;a.queryCount=0;a.aborts=0;a.rejected=0;a.probeErrors=0;a.previous=false;
            std::ostringstream s;s<<"cycle_start id="<<a.cycle<<" actor="<<i->first.index<<":"<<i->first.serial<<" native_clip_time="<<t<<" source_asset_contract="<<CONTRACT;Log(s.str());}
        if(!a.active){++i;continue;}a.lastTime=t;
        Ogre::Entity* weapon=ActualWeapon(c);if(!weapon){End(a,true,"native_weapon_attachment_missing");++i;continue;}
        // 浮动原点只用于渲染↔物理坐标转换；不写角色位置、朝向、导航或Havok速度。
        Vector3 origin=c->getPosition()-c->animation->node->_getDerivedPositionUpdated();if(!Finite(origin))throw std::runtime_error("floating origin invalid");
        Matrix4 wpose=SourcePose(weapon);float extension=Extension(t);Matrix4 intended=PartPose(wpose,t,extension);
        PositionVisual(a,wpose,t,extension);
        // 查询从真正绘制节点回读变换，非均匀比例/父节点不能让“数学预期”与屏幕模型各走一套。
        Matrix4 ppose=a.visual.part->_getFullTransformUpdated();
        float transformError=(ppose*Vector3(0,0,profile.slices[7].b)-intended*Vector3(0,0,profile.slices[7].b)).length();
        DrawDebug(a,wpose,ppose,extension);
        // 最新经验要求失败只影响当前路径；诊断异常不能锁住本演员直到读档，也不设置冷却。
        // 放弃当前未完成诊断并重置跨帧中点，下次原生安全更新仍尝试；不会补造漏段接触或健康伤害。
        // 此处只捕获C++异常，不伪装硬件异常恢复；明细开启时持续记录，查询尝试不依赖日志条数。
        if(!paused){
            try{Probe(a,c,ppose,origin,extension);}catch(const std::exception& e){
                ++a.probeErrors;a.previous=false;
                if(IrisDiagnostics::DetailsEnabled()){std::ostringstream out;out<<"contact_probe_failed actor="<<i->first.index<<":"<<i->first.serial
                    <<" reason="<<e.what()<<" failure_scope=current_probe retry=next_safe_update evaluated=0 animation_and_visual_continue=1 damage_calls=0";Log(out.str());}
            }
        }
        unsigned stage=t<profile.appear?0:t<profile.spin?1:t<profile.stopSpin?2:t<profile.returnStart?3:t<profile.hidden?4:5;
        if(stage!=a.stage){a.stage=stage;Vector3 grip=wpose*Vector3::ZERO+origin,muzzle=wpose*profile.pivot+origin,tip=ppose*Vector3(0,0,profile.slices[7].b)+origin;
            std::ostringstream s;s<<"stage id="<<a.cycle<<" value="<<stage<<" clip="<<t<<" extension="<<extension<<" angle="<<Angle(t)
              <<" grip="<<grip.x<<","<<grip.y<<","<<grip.z<<" muzzle="<<muzzle.x<<","<<muzzle.y<<","<<muzzle.z<<" tip="<<tip.x<<","<<tip.y<<","<<tip.z
              <<" render_vs_intended_tip_error="<<transformError<<" basis=actual_attachment_shared draw_and_query=actual_node_matrix damage_calls=0";Log(s.str());}
        ++i;
    }
}
typedef void(__fastcall* FrameFn)(GameWorld*,float);
typedef void(__fastcall* SafeFn)(GameWorld*);
typedef CombatTechniqueData*(__fastcall* ChooseFn)(CharStats*,float,float,CombatTechniqueData*,bool);
typedef void(__fastcall* ResetFn)(GameWorld*);
typedef void(__fastcall* ShutdownFn)(Renderer*);
typedef void(__fastcall* AnimFn)(AnimationClass*,CombatTechniqueData*,float,std::string);
FrameFn originalFrame=0;SafeFn originalSafe=0;ChooseFn originalChoose=0;ResetFn originalReset=0;ShutdownFn originalShutdown=0;AnimFn originalStart=0,originalRun=0;
GameWorld* frameWorld=0;bool updateDone=false;float rawDelta=0;double deferredDelta=0;bool clockConsumed=false;
// 084真实帧身份独立于日志计数；只由原主线程FrameScope推进，嵌套退出恢复当前token。
IrisDiagnostics::Count realFrameSerial=0,realFrameToken=0;
// 只管理插件上下文；原生函数异常展开时也归还旧值。
struct FrameScope {GameWorld* old;bool done;IrisDiagnostics::Count oldToken;FrameScope(GameWorld* w):old(frameWorld),done(updateDone),oldToken(realFrameToken){frameWorld=w;updateDone=false;realFrameToken=++realFrameSerial;}~FrameScope(){frameWorld=old;updateDone=done;realFrameToken=oldToken;}};
// 055只观察原安全门已经读取的状态；采样间隔不是线程运行时间，不为日志放宽原安全条件。
bool Idle(GameWorld* w){
    if(!w||!w->initialized||w->gameResetting||w->isLoadingFromASaveGame()||!w->physics){IrisDiagnostics::ObserveWindow(false,false,false,true);return false;}
    if(w->physics->isRunning()){if(IrisDiagnostics::DetailsEnabled())IrisDiagnostics::ObserveWindow(w->isPaused(),true,false,false);return false;}
    ThreadWannabe* ai=w->AINonRenderThread();const bool busy=ai&&ai->isRunning();
    if(IrisDiagnostics::DetailsEnabled())IrisDiagnostics::ObserveWindow(w->isPaused(),false,busy,false);return !busy;
}
void __fastcall FrameHook(GameWorld* w,float dt){
    // 078仅记录含原生的总回调墙钟；不改原帧时钟或安全更新条件。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_FRAME);
    if(!InterlockedCompareExchange(&running,0,0)){originalFrame(w,dt);return;}
    LONG owner=InterlockedCompareExchange(&mainThread,LONG(GetCurrentThreadId()),0);if(owner&&DWORD(owner)!=GetCurrentThreadId()){originalFrame(w,dt);return;}
    IrisDiagnostics::Add(IrisDiagnostics::FRAME_CALLBACKS);FrameScope frame(w);IrisNativeAudit::Frame serviceFrame(realFrameToken);rawDelta=dt;clockConsumed=false;originalFrame(w,dt);
    // 未取得安全更新只累计游戏秒；帧尾没有Ogre/PhysX操作，后效不在收招时切换时钟。
    if(w&&(!w->initialized||w->gameResetting||w->isLoadingFromASaveGame()))deferredDelta=0;
    if(!clockConsumed&&w&&w->initialized&&!w->gameResetting&&!w->isLoadingFromASaveGame()&&!w->isPaused()&&Finite(dt)&&Finite(w->frameSpeedMult))deferredDelta+=std::max(0.f,dt)*std::max(0.f,w->frameSpeedMult);
    // 帧尾仅做纯值日志摘要/落盘；没有Ogre/PhysX访问，长时间无施放也保留统计。
    serviceFrame.Finish(); // 084原生帧返回后提交纯值观察；不是额外安全执行点。
    IrisDiagnostics::Summary("interval");IrisDiagnostics::Flush(false);
}
// 082阶段探测只在原主线程/当前帧上下文且有工作时读取公开状态；关闭时在QPC/引擎访问前返回。
// 物理运行时保持queue/AI未知，避免为了诊断穿过原短路保护；不读取后台容器、不修改任何状态。
struct WindowAuditSession {
    bool active;
    explicit WindowAuditSession(GameWorld* w):active(false){
        if(IrisDiagnostics::WindowAuditEnabled()&&InterlockedCompareExchange(&running,0,0)&&DWORD(InterlockedCompareExchange(&mainThread,0,0))==GetCurrentThreadId()&&frameWorld==w&&!updateDone){
            active=IrisDiagnostics::BeginWindowAudit();Probe(w,IrisDiagnostics::WINDOW_PRE_NATIVE);}
    }
    void Probe(GameWorld* w,IrisDiagnostics::WindowPhase phase){
        if(!active||!IrisDiagnostics::WindowAuditHasWork())return;
        IrisDiagnostics::WindowState state;const double begin=IrisDiagnostics::Now();
        try{if(!w||!w->initialized||w->gameResetting||w->isLoadingFromASaveGame()||!w->physics)state.unavailable=1;
            else{state.unavailable=0;state.paused=w->isPaused()?1:0;state.physicsRunning=w->physics->isRunning()?1:0;
                if(!state.physicsRunning){state.queuesClear=w->physics->queuesAreClearMT()?1:0;ThreadWannabe* ai=w->AINonRenderThread();state.aiRunning=ai&&ai->isRunning()?1:0;}}}
        catch(const std::exception&){state.failed=true;} // 诊断异常不改变原生调用/本插件的安全门。
        IrisDiagnostics::RecordWindowAudit(phase,state,std::max(0.0,IrisDiagnostics::Now()-begin));
    }
    ~WindowAuditSession(){if(active)IrisDiagnostics::FinishWindowAudit();}
private:WindowAuditSession(const WindowAuditSession&);WindowAuditSession& operator=(const WindowAuditSession&);
};
// 084额外机会只观察；没有待结算队列时不新增引擎getter，且完全不读取物理消息队列。
// 顺序观察不是可复用的许可，医疗仍在原Flush每笔重查；不把重复回调当作已证明可用的调度点。
static void ObserveServiceOpportunity(GameWorld* w,bool alreadyUpdated){
    if(!IrisNativeAudit::ServiceEnabled())return;
    IrisDiagnostics::Count pending=IrisCombat::PendingDamageForAudit();IrisDiagnostics::WindowState state;
    const double begin=pending?IrisDiagnostics::Now():0;
    if(pending)try{
        if(!w||!w->initialized||w->gameResetting||w->isLoadingFromASaveGame()||!w->physics)state.unavailable=1;
        else{state.unavailable=0;state.physicsRunning=w->physics->isRunning()?1:0;
            if(!state.physicsRunning){ThreadWannabe* ai=w->AINonRenderThread();state.aiRunning=ai&&ai->isRunning()?1:0;state.paused=w->isPaused()?1:0;}}
    }catch(const std::exception&){state.failed=true;}
    IrisNativeAudit::Callback(alreadyUpdated,pending,state,begin>0?std::max(0.0,IrisDiagnostics::Now()-begin):0);
}
void __fastcall SafeHook(GameWorld* w){
    // 078仅记录含原生的总回调墙钟；不改原帧时钟或安全更新条件。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_SAFE);
    WindowAuditSession windowAudit(w);
    originalSafe(w);if(!InterlockedCompareExchange(&running,0,0)||DWORD(InterlockedCompareExchange(&mainThread,0,0))!=GetCurrentThreadId()||frameWorld!=w)return;
    ObserveServiceOpportunity(w,updateDone);if(updateDone)return;updateDone=true;
    windowAudit.Probe(w,IrisDiagnostics::WINDOW_POST_NATIVE);
    if(!Idle(w)){IrisDiagnostics::Add(IrisDiagnostics::UNSAFE_SKIPS);if(IrisDiagnostics::DetailsEnabled())Log("physics_or_AI_running; query_and_visual_update_skipped");return;}
    const double auditBegin=IrisDiagnostics::PerformanceEnabled()?IrisDiagnostics::Now():0;
    {Lock lock(&audit);IrisDiagnostics::BeginFrame();clockConsumed=true;frameDelta=0;
        if(!w->isPaused()){double d=deferredDelta+(Finite(rawDelta)&&Finite(w->frameSpeedMult)?std::max(0.f,rawDelta)*std::max(0.f,w->frameSpeedMult):0);frameDelta=d<=FLT_MAX?float(d):0;deferredDelta=0;}
        windowAudit.Probe(w,IrisDiagnostics::WINDOW_PRE_TICK);
        // 092完整根只包住原Tick；原生回调/主线程门/已有锁及锁外医疗不移动。
        try{IrisDiagnostics::CombatInterfaceFrame interfaceFrame;IrisDiagnostics::Scope timing(IrisDiagnostics::COMBAT_TICK);Tick(w);}catch(const std::exception& e){faulted=true;Clear(scene!=0,"runtime_error");Log(std::string("plugin_disabled: ")+e.what());}
        windowAudit.Probe(w,IrisDiagnostics::WINDOW_POST_TICK);}
    // 医疗/AI会重入其他插件，必须离开自身临界区后调用；不重试已经结算过的健康请求。
    if(!faulted&&!IrisCombat::ProofOnly())try{IrisCombat::Flush(w);}catch(const std::exception& e){Lock lock(&audit);faulted=true;Clear(scene!=0,"native_damage_error");Log(std::string("plugin_disabled: ")+e.what());}
    if(IrisDiagnostics::PerformanceEnabled())IrisDiagnostics::Record(IrisDiagnostics::SAFE_TICK,std::max(0.0,IrisDiagnostics::Now()-auditBegin));
    IrisDiagnostics::EndFrame();
}
// 072：这里只决定能否起手本武器的站立双手专属招式，不改变正在播放的动作或后效。
// UsesWeapon只核对句柄/ID；肢体可用、缺肢/义肢和腿伤姿态由原生医疗维护，不另设HP阈值。
// 076按玩家要求不写死SKILL_HEAVY：类别来自原生当前武器/FCS，原生武术仍回退。
// 本轮保留已有双手演出/站姿医疗门，不改HP阈值，也不把其他武器纳入本武器专属选择。
bool NativeStandingMeleeAllowed(CharStats* stats,CombatTechniqueData* native){
    Character* c=stats?stats->me:0;if(!ActorReady(c)||stats->currentWeaponType==SKILL_UNARMED)return false;
    if(c->getProneState()!=PS_NORMAL||c->medical.isCrippled()||!c->medical.isLeftArmOk()||!c->medical.isRightArmOk())return false;
    // 原生已明确选择武术、趴地或其他武器类别时直接保留。兼容技巧同时支持武术/武器时，
    // 仅凭返回指针无法还原入选分支，也保留原生；不将它猜作可替换的纯武器招式。
    // native为空可能仅因普通招式够不到，仍允许以上原生资格通过者使用专属起手距离。
    if(native&&(native->isProne||!native->hasSkillType(stats->currentWeaponType)||native->hasSkillType(SKILL_UNARMED)))return false;
    return true;
}
CombatTechniqueData* __fastcall ChooseHook(CharStats* stats,float range,float reach,CombatTechniqueData* last,bool stationary){
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_CHOOSE);
    CombatTechniqueData* native=originalChoose(stats,range,reach,last,stationary);if(!InterlockedCompareExchange(&running,0,0))return native;
    // 076：原生已在本回调使用同一stats/当前武器句柄；这里只读SDK武器身份，不读插件容器。
    // 先排除非本武器，再进锁复核。按实际stringID而非重武器枚举筛选，允许FCS修改类别。
    if(!UsesWeapon(stats))return native;
    Lock lock(&audit);if(!enabled||!UsesWeapon(stats))return native;
    if(!IrisCombat::ProofOnly()){
        // 原函数只调用一次，range/reach/last/stationary完整传递；不为试探资格重复选招或改公共池。
        // 资格不适用、故障或私选无结果均返回已取得的原生结果（包括NULL），不再强制空等。
        if(faulted||!NativeStandingMeleeAllowed(stats,native))return native;
        CombatTechniqueData* selected=IrisCombat::Choose(stats,range);return selected?selected:native;
    }
    // 指定武器严格独占本原型。未加载/距离不满足时返回原生NULL等待分支，不以错误通用动作兜底。
    Character* c=stats->me;if(faulted||!ActorReady(c))return 0;
    std::map<hand,Candidate>::iterator i=actors.find(c->handle);if(i==actors.end()){if(actors.size()<8)actors.insert(std::make_pair(c->handle,Candidate()));return 0;}
    if(!resources||!technique||!i->second.verified||!i->second.visual.entity||i->second.animation!=c->animation||!Finite(range)||range<technique->minDistanceVsStatic||range>technique->initialDistance)return 0;
    unsigned active=0;for(std::map<hand,Candidate>::const_iterator a=actors.begin();a!=actors.end();++a)if(a->second.active)++active;
    if(!i->second.active&&active>=maxActive)return 0;return technique;
}
float Speed(AnimationClass* animation,CombatTechniqueData* selected,float nativeSpeed,IrisDiagnostics::HookAudit* audit){
    if(!InterlockedCompareExchange(&running,0,0)||!Finite(nativeSpeed)||nativeSpeed<=0)return nativeSpeed;
    if(selected!=technique){Lock lock(audit);return IrisCombat::Speed(animation,selected,nativeSpeed);}
    Lock lock(audit);for(std::map<hand,Candidate>::iterator i=actors.begin();i!=actors.end();++i){Candidate& a=i->second;
        if(a.verified&&a.animation==animation){double v=double(nativeSpeed)*a.clipLength/profile.length;return v>0&&v<=FLT_MAX?float(v):nativeSpeed;}}
    return nativeSpeed;
}
void __fastcall StartHook(AnimationClass* a,CombatTechniqueData* t,float speed,std::string extra){
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_START);
    // 076：非空且明确非私有技巧直接转发；NULL沿用旧路，不能改变原型尚未初始化时的边界。
    if(t&&!IrisCombat::OwnTechniqueIdentity(t)){originalStart(a,t,speed,extra);return;}
    originalStart(a,t,Speed(a,t,speed,&audit),extra);
    if(InterlockedCompareExchange(&running,0,0)){Lock lock(&audit);IrisCombat::Started(a,t);}
    if(InterlockedCompareExchange(&running,0,0)&&t==technique){Lock lock(&audit);for(std::map<hand,Candidate>::iterator i=actors.begin();i!=actors.end();++i)if(i->second.animation==a)++i->second.start;}
}
void __fastcall RunHook(AnimationClass* a,CombatTechniqueData* t,float speed,std::string extra){
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_RUN);
    if(t&&!IrisCombat::OwnTechniqueIdentity(t)){originalRun(a,t,speed,extra);return;}
    originalRun(a,t,Speed(a,t,speed,&audit),extra);
}
void __fastcall ResetHook(GameWorld* w){{Lock lock;Clear(scene!=0,"world_reset");deferredDelta=0;}originalReset(w);}
void __fastcall ShutdownHook(Renderer* r){{Lock lock;if(r==renderer){Clear(scene!=0,"renderer_shutdown");scene=0;renderer=0;resources=false;}IrisDiagnostics::Flush(true);}originalShutdown(r);}
} // namespace Iris

// RE_Kenshi需要C++无参导出；不能改为extern C，也不能在DllMain做资源加载。
__declspec(dllexport) void startPlugin(){
    using namespace Iris;if(InterlockedCompareExchange(&started,1,0))return;InitializeCriticalSection(&mutex);Lock lock;
    HMODULE self=0;wchar_t path[32768];if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<LPCWSTR>(&startPlugin),&self))return;
    DWORD n=GetModuleFileNameW(self,path,32768);if(!n||n>=32768)return;directory.assign(path,n);directory=directory.substr(0,directory.find_last_of(L"\\/")+1);
    CreateDirectoryW((directory+L"logs").c_str(),0);SYSTEMTIME t;GetLocalTime(&t);wchar_t name[160];swprintf_s(name,L"logs\\IrisArsenal-%04u%02u%02u-%02u%02u%02u-%03u-%lu.log",t.wYear,t.wMonth,t.wDay,t.wHour,t.wMinute,t.wSecond,t.wMilliseconds,GetCurrentProcessId());logPath=directory+name;
    try{
        IrisDiagnostics::Initialize(directory,logPath);
        ReadAssets();Log(std::string("startup contract=")+CONTRACT+" log_total_limit=0 mode=ten_or_explicit_proof damage_policy=native_medical event_dedup=1 diagnostic_query=proof_only query_failure_scope=current_probe query_auto_disable=0 query_cooldown=0");if(!enabled){IrisDiagnostics::Flush(true);return;}
        intptr_t f=Native(&GameWorld::_NV_mainLoop_GPUSensitiveStuff,"frame"),u=Native(&GameWorld::charsUpdateUT,"safe_update"),c=Native(&CharStats::chooseAttack,"choose"),r=Native(&GameWorld::resetGame,"reset"),s=Native(&Renderer::shutDown,"shutdown"),a=Native(&AnimationClass::startCombatAnimation,"start"),b=Native(&AnimationClass::runCombatAnimation,"run");
        // 近战配置允许的物理命中才启用同步TLS防御适配；三远程不改防御结果。初始化失败不开放私有选招。
        IrisCombat::InstallDefenceGate();
        IrisNativeAudit::Install(); // 084仅显式开启且总日志/性能/明细有效才安装两处诊断Hook。
        IrisRanged::Install();
        // 生命周期和安全更新先安装，选招最后安装。部分失败时running保持0；行为钩子转发，重置/关闭仍执行自有清理。
        if(KenshiLib::AddHook(f,reinterpret_cast<void*>(&FrameHook),&originalFrame)!=KenshiLib::SUCCESS||
           KenshiLib::AddHook(u,reinterpret_cast<void*>(&SafeHook),&originalSafe)!=KenshiLib::SUCCESS||
           KenshiLib::AddHook(r,reinterpret_cast<void*>(&ResetHook),&originalReset)!=KenshiLib::SUCCESS||
           KenshiLib::AddHook(s,reinterpret_cast<void*>(&ShutdownHook),&originalShutdown)!=KenshiLib::SUCCESS||
           KenshiLib::AddHook(a,reinterpret_cast<void*>(&StartHook),&originalStart)!=KenshiLib::SUCCESS||
           KenshiLib::AddHook(b,reinterpret_cast<void*>(&RunHook),&originalRun)!=KenshiLib::SUCCESS||
           KenshiLib::AddHook(c,reinterpret_cast<void*>(&ChooseHook),&originalChoose)!=KenshiLib::SUCCESS||
           !originalFrame||!originalSafe||!originalReset||!originalShutdown||!originalStart||!originalRun||!originalChoose)throw std::runtime_error("hook installation incomplete");
        Log("hook_fast_ready contract=IRIS_HOOK_FAST_076 technique_identity=atomic_immutable_snapshot actor_cache_added=0 player_only=0 weapon_filter=actual_identity native_category=runtime_FCS original_calls_preserved=1 new_hooks=0 new_threads=0");
        InterlockedExchange(&running,1);Log("hooks_ready native_action=1 native_motion_untouched=1 native_attack_speed_preserved=1 ten_consumer_ready=1");IrisDiagnostics::Flush(true);
    }catch(const std::exception& e){faulted=true;Log(std::string("plugin_disabled: ")+e.what());ErrorLog(std::string("IrisArsenal: ")+e.what());}
}
