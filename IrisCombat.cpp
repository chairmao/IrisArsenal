// 104：可关闭的动作片尾审计；正式持有者动态注册，不设人数门槛。
// 102：弹体使用独立游戏秒与固定速度；极致驱动仅蓄力段重排时间键，动作攻速保留。
// 098钻天破前11段使用源钻头与外环的紧包围球；其余097物理和医疗流程保持。
// 历史实现摘要（不是当前DLL身份）：095冗余删除/同输入成本与名单测试；094公开AABB与Minkowski/slab保守映射；093查询执行/回调边界、骨架子节点数量复用和精确参数分组复用；092全量接口归因及单段空区A/B；091同次动画长度查找与可关闭抽样阶段诊断；090空间空区分组/单段成本测试、活动弹体无数量门、可关逐弹终止汇总；历史068独立爆炸使用游戏秒，三处源粒子语义隔离校正；067三招源特效与原事件同步；066圆环使用实例Shader门，原索引末尾0并不隐藏；062恢复原生许可后选招，预测仅在Emit计算；061原生资格/直接接触/弹道与完整日志；060共享原生瞄准；059极致驱动源站姿/红蓝准星/枪口蓝火与R9光流工作版，正式版1.0保留内部0.4.11。没有动作/移动拦截锁、瞬移、共享招式改写或全局contact回调。
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>
#include "IrisCombat.h"
#include "native/DamageCatchup.h"
#include "native/IniValues.h"
#include "native/QueryGate.h"
#include "IrisDiagnostics.h"
#include "IrisNativeAudit.h"
#include "IrisRanged.h"
#include "native/NativeMultiContact.h"
#include <core/Functions.h>
#include <ogre/OgreOldSkeletonInstance.h>
#include <kenshi/Globals.h>
#include <kenshi/GameWorld.h>
#include <kenshi/GameData.h>
#include <kenshi/Character.h>
#include <kenshi/CharStats.h>
#include <kenshi/Gear.h>
#include <kenshi/Damages.h>
#include <kenshi/PhysicsActual.h>
#include <kenshi/CharMovement.h>
#include <kenshi/util/UtilityT.h>
#include <kenshi/Animation/AnimationClass.h>
#include <kenshi/combat/CombatClass.h>
#include <kenshi/combat/RangedCombatClass.h>
#include <kenshi/combat/CombatTechniqueData.h>
#include <ogre/OgreAnimationState.h>
#include <ogre/OgreEntity.h>
#include <ogre/OgreSubEntity.h>
#include <ogre/OgreSceneManager.h>
#include <ogre/OgreSceneNode.h>
#include <ogre/OgreMatrix4.h>
#include <ogre/OgreManualObject.h>
#include <ogre/OgreColourValue.h>
#include <ogre/OgreMaterialManager.h>
#include <ogre/OgreMaterial.h>
#include <ogre/OgreVector4.h>
#include <algorithm>
#include <cmath>
#include <float.h>
#include <cstdlib>
#include <cstring>
#include <cwchar>
#include <deque>
#include <list>
#include <fstream>
#include <map>
#include <set>
#include <sstream>
#include <iomanip>
#include <new>
#include <stdexcept>
#include <vector>
namespace Iris {
extern CRITICAL_SECTION mutex;extern const char* GROUP;
bool Finite(float);bool Finite(const Ogre::Vector3&);bool ActorReady(Character*);
void* VulcanDefenceTarget();void* MeleeStumbleTarget();void* MeleeBlockCheckTarget();bool Accepting();
void Log(const std::string&);Ogre::Entity* ActualWeapon(Character*);Ogre::Matrix4 SourcePose(Ogre::Entity*);
}
namespace IrisCombat {
using Ogre::Vector3;using Ogre::Quaternion;using Ogre::Matrix4;using Iris::Finite;using Iris::Log;
const char* CONTRACT="IRIS_EIGHT_042"; // 十招事件格式沿用042；052审计和20类效果清单由独立代码合同校验。
const char* BLOCK_GUARD_CONTRACT="IRIS_MELEE_BLOCK_043";
// 044扩展六招受击反应保护；资源仍为042，格挡保护仍为043，组包需核验此新代码标记。
const char* REACTION_GUARD_CONTRACT="IRIS_MELEE_REACTION_044";
struct Guard {
    IrisDiagnostics::HookAudit* audit;
    explicit Guard(IrisDiagnostics::HookAudit* value=0):audit(value){if(audit)audit->BeforeLock();EnterCriticalSection(&Iris::mutex);if(audit)audit->Acquired();}
    ~Guard(){if(audit)audit->BeforeUnlock();LeaveCriticalSection(&Iris::mutex);}
};
struct Event {float time,mult,radius;unsigned kind;};
// 源HKX视觉触发点只控制附件时钟，和健康事件分开，绝不因补特效重复扣血。
struct FxCue {std::string key;float time;};
// 045只把战斗数值放入启动配置；半径、落点、事件时间与源特效仍共用原资产，不能分开漂移。
// 起手距离-1表示沿用FCS；只写私有技巧副本，不改公共重武器动作或其他角色。
// 046三远程不干预防御结果，独立代码标记用于拒绝仍强制脉冲/光炮命中的旧DLL。
const char* PARAMETER_CONTRACT="IRIS_HEIGHT_REACTION_CANNON_ICON_047";
struct Move {std::string key,animation;float seconds,attackMin,attackMax;double weight;bool bypassDefence,preventBlock,immuneReactions;CombatTechniqueData* technique;std::vector<Event> events;std::vector<FxCue> cues;Move():seconds(0),attackMin(-1),attackMax(-1),weight(1),bypassDefence(false),preventBlock(false),immuneReactions(false),technique(0){}};
struct FxState {float value[25];};
struct Asset {float duration,peak;unsigned samples;std::vector<std::vector<FxState> > tracks;std::vector<unsigned char> constantGroups;Vector3 center;float bound;std::string mesh;std::vector<std::string> materials;Asset():duration(0),peak(1),samples(0),center(Vector3::ZERO),bound(1){}};
struct WeaponCapsule {float x,y,a,b,r;};WeaponCapsule weaponCapsules[8];
/* 098：基于实际19层钻头网格（含0/15..18外环）的完整Z轴旋转包络；半径不是AABB对角线。
   tools/drill_sphere098.py给出紧球及下界证书；组包必须核对源资源。运行时不扫描顶点。
   mesh SHA256 aa9d80e8e7c13e10807d1f5aa764f03e6bf92297cb21b5dd1a2066d9726a1dcc；球心在局部旋转轴上，旋转不会改变其位置。 */
const float DRILL_SPHERE_CENTER_Z=0.210085988f;
const float DRILL_SPHERE_RADIUS=32.9765282f;
const char* DRILL_SPHERE_CONTRACT="IRIS_DRILL_SPHERE_098";
const unsigned MOVE_COUNT=10; // 042仅扩展招式表；代理/并发/队列预算保持。
Move moves[MOVE_COUNT];std::map<std::string,Asset> assets;std::wstring directory;
// 097同包身体骨骼的只读轨道，不是跨帧物理缓存，也不保存SDK指针。
struct BladePose {float time;Vector3 position;Quaternion rotation;};
std::vector<BladePose> bladePoses[2];
// 076：11份不可变快照对应十招+原型至多11次首次发布；旧快照不覆盖、不释放。
// 所有发布者已持原有锁。读者只原子读取一次快照地址，再比较普通地址值，避免每槽一次原子RMW。
// 不保存角色/场景指针、不解引用技巧；技巧自身沿用进程期生命周期，读档只清原有Actor状态。
struct TechniqueIdentities {CombatTechniqueData* item[MOVE_COUNT+1];};
static TechniqueIdentities identitySnapshots[MOVE_COUNT+1];
static PVOID volatile publishedIdentities=0;static unsigned identityVersions=0;
static void PublishTechniqueIdentity(unsigned slot,CombatTechniqueData* technique){
    TechniqueIdentities* old=static_cast<TechniqueIdentities*>(InterlockedCompareExchangePointer(&publishedIdentities,0,0));
    if(slot>MOVE_COUNT||!technique)throw std::runtime_error("private technique identity invalid");
    if(old&&old->item[slot]==technique)return;
    if((old&&old->item[slot])||identityVersions>=MOVE_COUNT+1)throw std::runtime_error("private technique identity lifetime changed");
    TechniqueIdentities* next=&identitySnapshots[identityVersions++];
    for(unsigned i=0;i<=MOVE_COUNT;++i)next->item[i]=i==slot?technique:(old?old->item[i]:0);
    InterlockedExchangePointer(&publishedIdentities,next);
}
bool OwnTechniqueIdentity(CombatTechniqueData* technique){
    if(!technique)return false;
    const TechniqueIdentities* snapshot=static_cast<TechniqueIdentities*>(InterlockedCompareExchangePointer(&publishedIdentities,0,0));
    if(!snapshot)return false;
    for(unsigned i=0;i<=MOVE_COUNT;++i)if(snapshot->item[i]==technique)return true;
    return false;
}
void PublishProofTechniqueIdentity(CombatTechniqueData* technique){PublishTechniqueIdentity(MOVE_COUNT,technique);}
// 两翼中心和翼片动画共用源时钟；只读一次离线中点，不在运行时遍历高模顶点或改角色骨骼。
const float FULL_BURST_REACH=90.f; // 与两次横扫同一伸距；终结球半径也取此值，不把扫掠胶囊厚度当攻击范围。
std::vector<Vector3> wingCenters;float wingCenterBegin=0,wingCenterEnd=0;// 061逐事件诊断不再设进程条数上限。
// 080诊断开关只在启动配置；仅隐藏插件自有特效，动画、查询、伤害和资源预热仍执行。
// Visual/Trail只在既有安全主线程使用，不发布到AI回调，不增加跨线程写者。
bool diagnosticHideEffects=false;
// 104仅控制审计，缺项关闭；正式发行关闭日志不改变事件消费或持有者容量。
bool actionEndLogging=false;
// 093功能开关独立于诊断；只省略本实例完全相同的已提交参数，不改变年龄/轨道/Shader。
bool parameterGroupReuse=true;
bool proofOnly=false,damageEnabled=true,warmReady=false;std::set<std::string> warmed;unsigned serial=0,epoch=0;
const char* COMBAT_POLICY_CONTRACT="IRIS_COMBAT_POLICY_061";
Vector3 lastOrigin=Vector3::ZERO;bool originKnown=false;
Ogre::SceneManager* scene=0;unsigned randomState=0x149AC137;
// 067：翻滚/全力源组合已把各自出生、寿命与运动一起烘焙到录像时钟，不能再统一乘2。
// 保持其他效果年龄/寿命和原生动作、伤害时点；064钻天破的独立源烘焙也原样保留。
// 064钻天破各源层的视觉加速已在作者端统一烘焙：蓝相0..0.52秒，火相0.56秒开始。
// 不再用“前5层”推测材质类型；避免新增源层后把蓝光也加速或让CPU/GPU生存期错开。
float VisualLayerAge(const std::string& key,unsigned layer,float age){
    return age;
}
float VisualLifetime(const std::string& key,float duration){
    return duration;
}
// 093资源加载时找出可能不变的七组轨道参数；运行时仍与“上次成功提交值”逐位比较，
// 因为相同源键的浮点插值也可能有舍入差异，绝不能直接把源常量当作输出永久常量。
void BuildParameterGroups(Asset& asset){
    static const unsigned begin[7]={0,4,8,9,13,17,21},width[7]={4,4,1,4,4,4,4};
    asset.constantGroups.assign(asset.tracks.size(),0);
    for(unsigned layer=0;layer<asset.tracks.size();++layer){unsigned mask=0;
        for(unsigned group=0;group<7;++group){bool same=true;
            for(unsigned frame=1;frame<asset.samples&&same;++frame)
                same=std::memcmp(asset.tracks[layer][0].value+begin[group],asset.tracks[layer][frame].value+begin[group],width[group]*sizeof(float))==0;
            if(same)mask|=1U<<group;
        }asset.constantGroups[layer]=static_cast<unsigned char>(mask);
    }
}
typedef char ParameterVectorWidth[(sizeof(Ogre::Vector4)==4*sizeof(float))?1:-1];
struct ParameterLayer {
    unsigned mask,valid;Ogre::Vector4 values[7];ParameterLayer():mask(0),valid(0){}
};
struct ParameterCache {
    std::vector<ParameterLayer> layers;
    explicit ParameterCache(const std::vector<unsigned char>& masks):layers(masks.size()){
        for(unsigned i=0;i<masks.size();++i)layers[i].mask=masks[i];
    }
    bool Same(unsigned layer,unsigned group,const Ogre::Vector4& value)const{
        const ParameterLayer& row=layers[layer];unsigned bit=1U<<group;
        return (row.mask&bit)&&(row.valid&bit)&&std::memcmp(&row.values[group],&value,sizeof(value))==0;
    }
    void Store(unsigned layer,unsigned group,const Ogre::Vector4& value){
        ParameterLayer& row=layers[layer];unsigned bit=1U<<group;if(!(row.mask&bit))return;
        row.values[group]=value;row.valid|=bit;
    }
};
// 缓存随Visual的entity/node一起按现有手动所有权转移，池/Shot复制只复制指针，不复制大数组。
// Clear先删除自有缓存并清指针，alive=false也释放纯CPU缓存；缓存分配失败只回原提交路径。
// 仅setCustomParameter成功后Store，抛异常不会把未提交值记成有效；不写共享材质、不新增线程。
bool SubmitParameter(Ogre::SubEntity* sub,ParameterCache* cache,unsigned layer,unsigned group,unsigned index,const Ogre::Vector4& value){
    if(cache&&cache->Same(layer,group,value))return false;
    sub->setCustomParameter(index,value);if(cache)cache->Store(layer,group,value);return true;
}
struct Visual {
    Ogre::Entity* entity;Ogre::SceneNode* node;std::string key;
    // 080只缓存本实例最近一次已提交的三个纯值；asset/key只由Create/Clear改变。
    // 不缓存人物/PhysX指针，不近似时间；按位比较保留-0和NaN差异。池按值转移时一并转移此状态。
    float parameterInputs[3];bool parametersValid;ParameterCache* parameterCache;
    Visual():entity(0),node(0),parametersValid(false),parameterCache(0){parameterInputs[0]=parameterInputs[1]=parameterInputs[2]=0;}
    // 092分离实例销毁/创建，仍遵守原scene/alive生命周期。
    void Clear(bool alive){IrisDiagnostics::InterfaceScope interfaceTiming(IrisDiagnostics::IF_RESOURCE);Ogre::Entity* e=entity;Ogre::SceneNode* n=node;entity=0;node=0;key.clear();parametersValid=false;delete parameterCache;parameterCache=0;if(!alive||!scene)return;
        if(e)IrisDiagnostics::Add(IrisDiagnostics::DISPOSED_VISUALS);
        try{if(n)n->detachAllObjects();if(e)scene->destroyEntity(e);if(n)scene->destroySceneNode(n);}catch(const std::exception& x){Log(std::string("effect_cleanup_error: ")+x.what());}}
    void Create(const std::string& name){
        if(entity&&key==name)return;
        IrisDiagnostics::Scope timing(IrisDiagnostics::VISUAL_CREATE,name.c_str());Clear(true);std::map<std::string,Asset>::const_iterator a=assets.find(name);
        if(a==assets.end())throw std::runtime_error("effect asset missing: "+name);
        try{node=scene->getRootSceneNode()->createChildSceneNode();entity=scene->createEntity(a->second.mesh,Iris::GROUP);key=name;IrisDiagnostics::Add(IrisDiagnostics::FRESH_VISUALS);
            if(entity->getNumSubEntities()!=a->second.materials.size())throw std::runtime_error("effect submesh count mismatch");
            // 引擎工厂可能覆写材质，必须逐层绑定回读；只调编译器提供的SubEntity this，不手工加Renderable偏移。
            for(unsigned i=0;i<entity->getNumSubEntities();++i){Ogre::SubEntity* s=entity->getSubEntity(i);s->setMaterialName(a->second.materials[i],Iris::GROUP);if(s->getMaterialName()!=a->second.materials[i])throw std::runtime_error("effect material binding rejected");s->setCustomParameter(1,Ogre::Vector4(0,0,0,0));
                // 即使静态效果也初始化Shader声明的所有custom参数，避免首次绑定读取不存在的自动常量。
                for(unsigned c=2;c<=8;++c)s->setCustomParameter(c,Ogre::Vector4(0,0,0,0));
                // 066：钻头圆环的投影裁剪门在首次绘制前初始化；其他资源不消费custom9。
                if(name=="drill")s->setCustomParameter(9,Ogre::Vector4(0,0,0,0));
                // 用户运行时由引擎正常加载GPU材质；起招前完成，避免第一发才触发纹理/程序冷加载。
                Ogre::MaterialPtr material=Ogre::MaterialManager::getSingleton().getByName(a->second.materials[i],Iris::GROUP);if(material.isNull())throw std::runtime_error("effect material resource missing");{IrisDiagnostics::Scope loading(IrisDiagnostics::MATERIAL_LOAD,a->second.materials[i].c_str());material->load();}}
            entity->setRenderQueueGroup(83);entity->setCastShadows(false);node->attachObject(entity);entity->setVisible(false);
            if(parameterGroupReuse&&a->second.samples){
                bool eligible=false;for(unsigned i=0;i<a->second.constantGroups.size();++i)if(a->second.constantGroups[i]){eligible=true;break;}
                if(eligible){try{parameterCache=new ParameterCache(a->second.constantGroups);}
                    catch(const std::bad_alloc&){IrisDiagnostics::Add(IrisDiagnostics::PARAMETER_CACHE_FALLBACKS);}}
            }
        }catch(...){Clear(true);throw;}
    }
    void Draw(const Matrix4& pose,float age,float opacity,float extent=0){
        if(!node||!entity)return;IrisDiagnostics::Scope visualTiming(IrisDiagnostics::VISUAL_UPDATE);IrisDiagnostics::InterfaceScope visualPhase(IrisDiagnostics::IF_VISUAL_NODE);Vector3 p,s;Quaternion q;pose.decomposition(p,s,q);if(!Finite(p)||!Finite(s))throw std::runtime_error("effect transform nonfinite");
        Ogre::SceneNode* root=scene->getRootSceneNode();Vector3 rs=root->_getDerivedScaleUpdated();if(rs.x<=0||rs.y<=0||rs.z<=0)throw std::runtime_error("scene scale invalid");
        node->setPosition(root->convertWorldToLocalPosition(p));node->setOrientation(root->convertWorldToLocalOrientation(q));node->setScale(s.x/rs.x,s.y/rs.y,s.z/rs.z);
        visualPhase.Switch(IrisDiagnostics::IF_VISUAL_PARAMETERS);
        const Asset& asset=assets.find(key)->second;
        const float inputs[3]={age,opacity,extent};
        const bool updateParameters=!parametersValid||std::memcmp(parameterInputs,inputs,sizeof(inputs))!=0;
        // 参数相同也必须更新节点/显隐；只跳过本实例相同轨道插值和custom1..8写入。
        // custom9是钻头独立显隐门，仍由ShowParts正常更新，不能放进本缓存。
        // 087源采样位置只与年龄/资产采样数有关；同年龄层共用lo/hi/u，25维轨道和custom参数仍逐层计算。
        // 比较真实layerAge；不同层时钟不一致时退回原表达式，不能以近似年龄合并视觉。
        float sampleAge=VisualLayerAge(key,0,age),sampleU=0;unsigned sampleLo=0,sampleHi=0,sharedSamples=0,parameterWrites=0;
        if(updateParameters&&asset.samples){float x=std::max(0.f,std::min(1.f,sampleAge/asset.duration))*(asset.samples-1);sampleLo=unsigned(x);sampleHi=std::min(asset.samples-1,sampleLo+1);sampleU=x-sampleLo;}
        if(updateParameters)for(unsigned i=0;i<entity->getNumSubEntities();++i){Ogre::SubEntity* sub=entity->getSubEntity(i);float layerAge=VisualLayerAge(key,i,age);
            if(asset.samples){
                // 只插值一次离线源采样；每层有自己的颜色/UV/扩散矩阵，不能统一取峰值画一团球。
                unsigned lo=sampleLo,hi=sampleHi;float u=sampleU;
                if(layerAge!=sampleAge){float x=std::max(0.f,std::min(1.f,layerAge/asset.duration))*(asset.samples-1);lo=unsigned(x);hi=std::min(asset.samples-1,lo+1);u=x-lo;}
                else ++sharedSamples;
                float v[25];
                for(unsigned k=0;k<25;++k)v[k]=asset.tracks[i][lo].value[k]*(1-u)+asset.tracks[i][hi].value[k]*u;
                if(parameterCache){
                    parameterWrites+=SubmitParameter(sub,parameterCache,i,0,2,Ogre::Vector4(v[0],v[1],v[2],v[3]));
                    parameterWrites+=SubmitParameter(sub,parameterCache,i,1,3,Ogre::Vector4(v[4],v[5],v[6],v[7]));
                    parameterWrites+=SubmitParameter(sub,parameterCache,i,2,4,Ogre::Vector4(v[8],0,0,0));
                    parameterWrites+=SubmitParameter(sub,parameterCache,i,3,8,Ogre::Vector4(v[9],v[10],v[11],v[12]));
                    for(unsigned row=0;row<3;++row)parameterWrites+=SubmitParameter(sub,parameterCache,i,4+row,5+row,Ogre::Vector4(v[13+row*4],v[14+row*4],v[15+row*4],v[16+row*4]));
                }else{
                    // 未启用/无可复用组/分配失败完全沿原路；动态资源不承担逐组缓存维护。
                    sub->setCustomParameter(2,Ogre::Vector4(v[0],v[1],v[2],v[3]));sub->setCustomParameter(3,Ogre::Vector4(v[4],v[5],v[6],v[7]));sub->setCustomParameter(4,Ogre::Vector4(v[8],0,0,0));sub->setCustomParameter(8,Ogre::Vector4(v[9],v[10],v[11],v[12]));
                    for(unsigned row=0;row<3;++row)sub->setCustomParameter(5+row,Ogre::Vector4(v[13+row*4],v[14+row*4],v[15+row*4],v[16+row*4]));parameterWrites+=7;
                }
            }
            sub->setCustomParameter(1,Ogre::Vector4(layerAge,opacity,asset.samples?1.f:0.f,extent));++parameterWrites;
        }
        if(sharedSamples>1&&IrisDiagnostics::CollisionProfileEnabled())IrisDiagnostics::Add(IrisDiagnostics::CURVE_SAMPLE_REUSES,sharedSamples-1);
        if(updateParameters){std::memcpy(parameterInputs,inputs,sizeof(inputs));parametersValid=true;
            const unsigned expected=entity->getNumSubEntities()*(asset.samples?8U:1U);
            IrisDiagnostics::Add(IrisDiagnostics::VISUAL_PARAMETER_WRITES,parameterWrites);
            if(parameterWrites<expected)IrisDiagnostics::Add(IrisDiagnostics::VISUAL_PARAMETER_REUSES,expected-parameterWrites);}
        else IrisDiagnostics::Add(IrisDiagnostics::VISUAL_PARAMETER_REUSES,entity->getNumSubEntities()*(asset.samples?8U:1U));
        // 080对照只改变Ogre可见位；仍执行同样的CPU变换/曲线和生命周期，不能据此声称纯GPU计时。
        visualPhase.Switch(IrisDiagnostics::IF_VISIBILITY);entity->setVisible(opacity>.001f&&!diagnosticHideEffects);
    }
    void Hide(){IrisDiagnostics::InterfaceScope interfaceTiming(IrisDiagnostics::IF_VISIBILITY);if(entity)entity->setVisible(false);}
};
// 借用角色/武器指针仅限当前窗口；跨帧只存hand与插件自己的可视、矩阵和值类型事件。
struct TrailPoint {Vector3 a,b;float age;};
// 097每刀只记录已扫过角度/固定圆心等纯值；不缓存形体或角色裸指针。
struct Actor {
    IrisSector::Progress bladeProgress[2];bool bladeFemale;Vector3 bladePreviousOrigin,drillPreviousOrigin;
    hand owner;AnimationClass* animation;bool ready,active,reserved,havePose,ranged;unsigned start,consumed,id,next,stumbles;int move;float last,rate,rangedWait;Vector3 origin,ground,aim;Matrix4 previous;
    Ogre::ManualObject* trail;std::deque<TrailPoint> trailPoints;Quaternion heading;float lengths[MOVE_COUNT],rates[MOVE_COUNT];Visual drill,gun,blade,exhaust,flash,ion,halo,ignition,wings,muzzleFire,cannon;
    Actor():bladeFemale(false),animation(0),ready(false),active(false),reserved(false),havePose(false),ranged(false),start(0),consumed(0),id(0),next(0),stumbles(0),move(-1),last(0),rate(1),rangedWait(0),trail(0){for(unsigned i=0;i<MOVE_COUNT;++i){lengths[i]=0;rates[i]=1;}}
};
std::map<hand,Actor> actors;
struct Path {Vector3 from,to;float radius;bool sphere,cylinder,volume;Path(const Vector3& a,const Vector3& b,float r,bool s=false,bool c=false,bool v=false):from(a),to(b),radius(r),sphere(s),cylinder(c),volume(v){}};
// 055：任务只拥有值和自有容器；初始化转移/队尾轮转不复制路径或命中名单。
// 单个任务仍至多8路径/轮；splice保持查询作业的轮转/重试。
// 已入队健康请求保持FIFO；查询作业本身不承诺全局事件串行或历史场景回放。
struct Job {hand caster,directVictim;bool haveDirect;unsigned cast,event,move;float mult;std::vector<Path> paths;std::vector<IrisSector::Volume> sectors;size_t cursor;std::set<hand> victims;bool blade;unsigned failures;double createdAt;IrisDiagnostics::WaitStamp waits;
    Job():haveDirect(false),cast(0),event(0),move(0),mult(1),cursor(0),blade(false),failures(0),createdAt(IrisDiagnostics::DetailsEnabled()?IrisDiagnostics::Now():0){IrisDiagnostics::SnapshotWaits(createdAt,waits);}
    void Swap(Job& other){std::swap(caster,other.caster);std::swap(directVictim,other.directVictim);std::swap(haveDirect,other.haveDirect);std::swap(cast,other.cast);std::swap(event,other.event);std::swap(move,other.move);std::swap(mult,other.mult);
        paths.swap(other.paths);sectors.swap(other.sectors);std::swap(cursor,other.cursor);victims.swap(other.victims);std::swap(blade,other.blade);std::swap(failures,other.failures);std::swap(createdAt,other.createdAt);std::swap(waits,other.waits);}
};
// 090诊断字段只存本弹体纯值，关闭日志时不更新；生命周期/碰撞/伤害仍使用原字段。
struct Shot {unsigned auditUpdates,auditAttempts,auditEmpty,auditWaits,auditNoCommands,auditCommands,auditBudget,auditBlast;
    float auditAge,auditMaxPending;
    hand caster;unsigned cast,event,move,retries;float mult,radius,collisionRadius,visualRadius,speed,travel,range,rate,pending;Vector3 pos,direction,target;bool destination;Visual visual;Shot():auditUpdates(0),auditAttempts(0),auditEmpty(0),auditWaits(0),auditNoCommands(0),auditCommands(0),auditBudget(0),auditBlast(0),auditAge(0),auditMaxPending(0),cast(0),event(0),move(0),retries(0),mult(1),radius(1),collisionRadius(1),visualRadius(1),speed(200),travel(0),range(200),rate(1),pending(0),destination(false){}};
struct Residue {unsigned cast;hand caster;Visual visual;Vector3 pos,direction;Quaternion orientation;float age,life,radius,rate,length;std::string key;Residue():cast(0),orientation(Quaternion::IDENTITY),age(0),life(.7f),radius(1),rate(1),length(0){direction=Vector3::UNIT_Z;}};
// 053 queuedAt为独立于日志开关的QPC墙钟毫秒；0表示时钟不可用，不伪造零等待。
struct Hurt {hand caster,victim;bool direct;unsigned move,cast,event,generation;float mult;double queuedAt;IrisDiagnostics::WaitStamp waits;};
const char* DAMAGE_QUEUE_CONTRACT="IRIS_DAMAGE_QUEUE_053";
double damageFlushBudgetMs=2.5,damageQueueTargetMs=40;unsigned damageFlushMaxHits=12;
/* 099仅超龄大积压使用额外有界额度；不新增服务回调/线程/全局锁，不提高普通批额度。 */
/* 100仅旧队列门拒绝时核验实际空消息；不是轮询线程或跨帧许可缓存。 */
bool queryGateRefinement=true;
bool damageCatchupEnabled=true;double damageCatchupBudgetMs=5;unsigned damageCatchupMaxHits=64;
/* 099队列压力沿旧门记录；实际普通/追赶额度来自INI，103不再另设业务钳制。
   此处不表示追赶已启用，也不是固定32笔；当前是否启用由启动配置决定。 */
// 前两段光刃各有独立命中集合，跨采样帧共享；动作/请求均结束后回收，读档立即清空。
typedef std::pair<unsigned,unsigned> StrikeKey;
std::map<StrikeKey,std::set<hand> > bladeVictims;
struct BladeWindow {float begin,end;};BladeWindow bladeWindows[3];
struct DamageStat {unsigned pending,applied,blocked,missed,rejected;DamageStat():pending(0),applied(0),blocked(0),missed(0),rejected(0){}};
std::map<StrikeKey,DamageStat> damageStats;
unsigned shotCursor=0; // 弹体在有界查询预算间轮转，不能总是从第一发优先。
std::list<Job> jobs;std::deque<Hurt> hurts;std::vector<Shot> shots;std::vector<Residue> residues;
// 容器空节点+交换，不在每次队列轮转时重新分配路径/set；不转移角色或PhysX对象所有权。
void PushJob(Job& job){jobs.push_back(Job());jobs.back().Swap(job);IrisDiagnostics::Add(IrisDiagnostics::JOB_TRANSFERS);}
const char* COLLISION_DAMAGE_CONTRACT="IRIS_RANGED_RAY_057";
const char* FIRE_CANNON_CONTRACT="IRIS_FIRE_CANNON_058";
// 059仅重做极致驱动；保留058修正和其余九招，交付门禁止旧DLL混用新附件/时钟。
const char* DRIVE_REBUILD_CONTRACT="IRIS_DRIVE_REBUILD_059";
// 同一安全Tick只缓存完整球形查询的值事实，最多16份；每次爆炸仍独立按原生四项资格筛选和医疗结算。
// 跨帧/读档清空，不存NxShape、角色指针或失败名单；物理队列安全检查始终先于缓存命中。
struct SphereFact {Vector3 center;float radius;IrisNative::Contacts contacts;};
std::vector<SphereFact> sphereFacts;
// 056移除零命中的胶囊缓存；批量工作区仅含值，ResolveJobs在原Tick互斥区内独占。
// 081常见规模内联，超出后自有容量保留复用；只重置有效count，绝不缓存跨帧物理事实。
IrisNative::Contacts capsuleBatchResults[IrisNative::CAPSULE_BATCH_CAPACITY];
// 089功能开关与日志独立：同批事实只读复用，联合区域为空才省略球扫掠；测试对照默认关闭。
bool rangedQueryReuse=true,rangedEmptyPruning=true,rangedEmptyShadow=false;
// 090程序缺项时单段宽相/逐弹汇总关闭；本地测试INI显式开启。功能与诊断是独立开关。
bool rangedSpatialPruning=true,rangedSingleProbe=false,projectileWorkLogging=false;
bool rangedBatchEnabled=true; // 088功能开关独立于诊断，重启读取；无新线程/场景锁。
bool capsuleBatchEnabled=true; // 097只控制逐胶囊复合提交；两条路径均使用原生AABB overlap。
double nativeHitSlowMs=1;
// 052：旧120查询帧摘要已由全部安全帧的窗口/进程审计替换；同帧物理事实缓存继续保留。
// 090只限制已结束且闲置的实例缓存；活动弹体/后效不计入空闲池容量，不能以此阻塞发射。
std::vector<Visual> pool;size_t resourcePeak=0;
bool Borrow(Visual& v,const std::string& key){
    // 092只观察本次同步接口，子耗时由根栈扣除；不改参数、次数、返回及所有权。
    IrisDiagnostics::InterfaceScope interfaceTiming(IrisDiagnostics::IF_POOL_BORROW);

    for(size_t i=0;i<pool.size();++i)if(pool[i].key==key){v=pool[i];pool.erase(pool.begin()+i);IrisDiagnostics::Add(IrisDiagnostics::POOL_REUSES);return true;}
    // 没有匹配闲置实例时按需创建；取消原活动shots+residues+pool合计96门。
    // 实例仍只由原安全主线程持有，内存/引擎创建失败保留原异常处理，不假造成功。
    v.Create(key);return true;
}
void Return(Visual& v){
    // 092只观察本次同步接口，子耗时由根栈扣除；不改参数、次数、返回及所有权。
    IrisDiagnostics::InterfaceScope interfaceTiming(IrisDiagnostics::IF_POOL_RETURN);

    v.Hide();if(v.entity){
        // 96仅是空闲缓存上限。活动数不受限制，多余已结束实例正常释放，避免峰值后永久囤积。
        if(pool.size()>=96){v.Clear(true);if(IrisDiagnostics::CollisionProfileEnabled())IrisDiagnostics::Add(IrisDiagnostics::IDLE_POOL_TRIMS);}
        else{pool.push_back(v);v=Visual();}
    }
}
// 每个自然命中/射程终止仅汇总一次；无逐帧IO/QPC，shared宽相由批次摘要计费而不重复分摊到每发。
void LogShotWork(const Shot& s,const char* outcome,float travel){
    if(!projectileWorkLogging||!IrisDiagnostics::DetailsEnabled())return;
    std::ostringstream out;out<<"projectile_work cast="<<s.cast<<" event="<<s.event<<" move="<<s.move<<" outcome="<<outcome
        <<" updates="<<s.auditUpdates<<" attempts="<<s.auditAttempts<<" empty_results="<<s.auditEmpty<<" waits="<<s.auditWaits
        <<" waits_without_command="<<s.auditNoCommands<<" owned_ray_body_commands="<<s.auditCommands
        <<" budget_defers_observed="<<s.auditBudget<<" blast_defers="<<s.auditBlast<<" game_seconds="<<s.auditAge
        <<" travel="<<travel<<" max_travel="<<s.range<<" pending_motion_seconds="<<s.pending<<" max_pending_motion_seconds="<<s.auditMaxPending
        <<" shared_probes_in_batch_summary=1 empty_before_policy_filter=1 FPS_measured=0";Log(out.str());
}
bool AssetRequired(const std::string& key){
    // 权重为0的招式不会被本插件选中，预热也只覆盖已启用招式的真实消费者；
    // 材质定义仍可解析，但不主动加载未用网格/纹理。以后启用其他招式时按同一依赖表预热。
    const char* eventAsset[10]={"","shell","shock","drill","drill_blast","blade","bullet","shell","beam","electro_burst"};
    for(unsigned i=0;i<MOVE_COUNT;++i)if(moves[i].weight>0){
        if((i==8&&key=="electro_area")||(i==7&&key=="ion")||(i!=9&&key=="exhaust")||(i==5&&(key=="gun"||key=="vulcan_body"||key=="muzzle_fire"))||(i==6&&key=="pulse_muzzle")||(i==7&&key=="muzzle")||(i==6&&key=="pulse_blast")||(i==3&&(key=="drill_blast"||key=="drill_wings"))||(i==0&&(key=="fire_blast"||key=="roll_blast"))||(i==4&&(key=="charge_halo"||key=="full_blast")))return true;
        for(size_t j=0;j<moves[i].events.size();++j){unsigned k=moves[i].events[j].kind;
            if(key==eventAsset[k]||(key=="blast"&&(k==1||k==4||k==6||k==7)))return true;}
    }return false;
}
void WarmNext(){
    // 每个安全更新最多预热一类自有实例；空闲不绘制、不做伤害。只借一次共享资源，不按每发复制纹理。
    if(warmReady||!scene)return;
    for(std::map<std::string,Asset>::const_iterator i=assets.begin();i!=assets.end();++i)if(AssetRequired(i->first)&&!warmed.count(i->first)){
        IrisDiagnostics::Scope timing(IrisDiagnostics::PREWARM,i->first.c_str());Visual v;v.Create(i->first);Return(v);warmed.insert(i->first);return;}
    warmReady=true;std::ostringstream status;status<<"ten_resources_warmed assets="<<warmed.size()<<" available="<<assets.size()<<" keys=";
    for(std::set<std::string>::const_iterator i=warmed.begin();i!=warmed.end();++i)status<<*i<<",";
    status<<" enabled_only=1 bounded_instance_pool=1 first_cast_material_load_deferred=0";Log(status.str());
}
bool Same(const hand& a,const hand& b){return !(a<b)&&!(b<a);}
// 061复用本机原生近战的四项资格顺序；这是关系/状态筛选，不是重新测试几何。
// 所有借用指针仅活在当前原生允许的调用内；只用原生函数，不保存人物/shape或修改阵营。
const char* DamagePolicyReason(Character* caster,Character* victim,bool ranged){
    if(!caster||!victim||caster==victim||!caster->isValid()||caster->isDestroyed()||!victim->isValid()||victim->isDestroyed())return "invalid_or_self";
    if(victim->isDead())return "dead";
    if(caster->isAlly(victim,false))return "ally";
    if(victim->isLiterallyUnconciousNotPretending())return "true_unconscious";
    if(caster->isEnemy(victim,true))return 0;
    Character* active=0;
    if(ranged){RangedCombatClass* rc=caster->rangedCombat;if(rc&&rc->combatMode)active=rc->_getAttackTarget().getCharacter();}
    else{CombatClass* cc=caster->getCombatClass();if(cc&&cc->_isInCombatMode())active=cc->_getAttackTarget().getCharacter();}
    return active==victim?0:"neutral_not_active_target";
}
bool CanDamage(Character* caster,Character* victim,bool ranged,const char** reason){
    const char* why=DamagePolicyReason(caster,victim,ranged);if(reason)*reason=why?why:"eligible";return why==0;
}
bool DamageTarget(Character* caster,Character* victim,unsigned move){return CanDamage(caster,victim,move==5||move==6||move==7);}
// 远程角色接触与伤害共用资格：中立旁观者、盟友、真正昏迷/死亡角色均透明；环境射线照常阻挡。
// 不能先选最近角色再过滤，否则会吞掉后方真正可伤害目标；三招光炮的Collect也使用同一资格。
bool IgnoreRangedContact(Character* caster,Character* victim){return !CanDamage(caster,victim,true);}
// 每游戏秒有效弹速在许可前及发射时共用；光炮即时命中，不通过虚构极高弹速近似。
// 102速度单位为游戏单位/游戏秒；攻击速率只控制演员动作与发射节拍，不再缩放飞行。
// 发射预测和实际位移共用此函数；原地形有限射线/带半径角色碰撞及枪口位置不变。
const char* PROJECTILE_TIMELINE_CONTRACT="IRIS_PROJECTILE_TIMELINE_102";
const float DRIVE_SOURCE_FIRE=3.166539907f;
float ProjectileSpeed(unsigned move){return move==5?1500.f:move==6?1000.f:220.f;}
// 身体时间键与伤害节点已按F(t)=t/2(t<=fire)、t-fire/2(t>fire)重排。
// ion仍保留原素材曲线；只反解显示年龄，保持蓝相/火相/准星与同一姿势对应，不重采样美术资源。
float DriveEffectTime(float t){const float fire=DRIVE_SOURCE_FIRE*.5f;return t<fire?t*2.f:t+fire;}
Matrix4 Pose(const Vector3& p,const Quaternion& q,const Vector3& s){Matrix4 m;m.makeTransform(p,s,q);return m;}
Matrix4 Relative(const Matrix4& w,const Vector3& p,const Quaternion& q,const Vector3& s){return w*Pose(p,q,s);}
Vector3 Muzzle(const Matrix4& w){return w*Vector3(1.807138657f,0,8.534358047f);}
// 058：方向只读当帧原生持械矩阵；原生战斗负责朝目标转向，不另写角色/骨骼或锁方向。
// 枪口、光束、范围球共用同一条轴。20仍表示相对角色根点的轴向伸距，R25由事件提供。
struct CannonFrame {Vector3 muzzle,axis,center;Quaternion orientation;float reach;};
bool ElectroFrame(const Matrix4& weapon,const Vector3& origin,const Vector3& root,float radius,CannonFrame& frame){
    frame.muzzle=Muzzle(weapon)+origin;frame.axis=Vector3(weapon[0][2],weapon[1][2],weapon[2][2]);
    if(!Finite(frame.muzzle)||!Finite(root)||!Finite(frame.axis)||!Finite(radius)||radius<=0||frame.axis.squaredLength()<.0001f)return false;
    float axisLength=frame.axis.length();if(!Finite(axisLength)||axisLength<.01f)return false;frame.axis/=axisLength;frame.orientation=Vector3::UNIT_Z.getRotationTo(frame.axis);
    frame.center=frame.muzzle+frame.axis*(20.f-(frame.muzzle-root).dotProduct(frame.axis));
    frame.reach=(frame.center-frame.muzzle).dotProduct(frame.axis)+radius;
    return Finite(frame.center)&&Finite(frame.reach)&&frame.reach>0;
}
struct AimEvidence {
    Vector3 root,raw;hand target;const char* source;
    AimEvidence():root(Vector3::ZERO),raw(Vector3::ZERO),source("snapshot_fallback"){}
};
Vector3 Target(Character* c,const Vector3& fallback,AimEvidence* evidence=0){
    CombatClass* cc=c?c->getCombatClass():0;
    // 真正远程模式从RangedCombatClass取目标，不再借用近战的攻击对象；失去目标仍返回本次快照。
    Character* target=IrisRanged::Active(c)?c->rangedCombat->_getAttackTarget().getCharacter():(cc?cc->_getAttackTarget().getCharacter():0);
    if(!target||!target->isValid()||target->isDestroyed())return fallback;
    Vector3 root=target->getPosition();if(evidence){evidence->root=root;evidence->target=target->handle;}
    AnimationClass* animation=target->animation;
    // Character::getBoneWorldPosition已返回游戏世界坐标：原生内部用node的position加旋转/比例后的骨点。
    // 旧瞄准路径又加(getPosition-derivedPosition)导致大坐标处原点叠加，附近目标被算到三万单位外。
    // 此处直接消费原生骨点；渲染附件枪口仍须单独加a.origin，绘制再减origin，不能一并删掉。
    if(animation&&animation->isActivated&&animation->node&&animation->skeleton){
        const char* bones[]={"Bip01 Spine2","Bip01 Pelvis","Bip01 Head"};
        for(unsigned i=0;i<3;++i)if(animation->skeleton->hasBone(bones[i])){
            Vector3 point=target->getBoneWorldPosition(bones[i]);if(Finite(point)){
                if(evidence){evidence->raw=point;evidence->source=bones[i];}return point;
            }
        }
        // 非标准骨架缺少上述名字时才用兼容中位点，不冒称已找到真实胸部，也不修改角色姿态。
    }
    Vector3 point=root+Vector3(0,8,0);if(!Finite(point))return fallback;
    if(evidence){evidence->raw=point;evidence->source="root_height_fallback";}return point;
}
// 弹体自出生即有正确位置、源材质与不透明度；物理预算延期时仍显示上一真实位置，不能出生隐藏。
void DrawShot(Shot& shot,const Vector3& origin){
    // 火神可视包围球仍严格等于碰撞R4.5；脉冲的源ShockRing/光筒是装饰包络，不能缩成4.5的碰撞核心。
    // 两者共用真实球心/方向。脉冲保留源作者已换算的大小，其4.5核心不变，爆炸按用户要求为火神两倍半径R36。
    const Asset& asset=assets[shot.visual.key];float k=shot.visualRadius/asset.bound;
    Quaternion q=Vector3::UNIT_Z.getRotationTo(shot.direction);
    shot.visual.Draw(Pose(shot.pos-origin-q*(asset.center*k),q,Vector3(k,k,k)),shot.travel/shot.speed,1);
}
void ClearActor(Actor& a,bool alive){
    Ogre::ManualObject* trail=a.trail;a.trail=0;a.trailPoints.clear();
    if(alive&&scene&&trail)try{scene->destroyManualObject(trail);}catch(const std::exception& x){Log(std::string("trail_cleanup_error: ")+x.what());}
    a.drill.Clear(alive);a.gun.Clear(alive);a.blade.Clear(alive);a.exhaust.Clear(alive);a.flash.Clear(alive);a.ion.Clear(alive);a.halo.Clear(alive);a.ignition.Clear(alive);a.wings.Clear(alive);a.muzzleFire.Clear(alive);a.cannon.Clear(alive);a.active=false;a.havePose=false;}
// 104片尾审计只观察本次原生快照，不补发事件、不移动查询或医疗，也不把剩余事件全称作漏发。
// 仅在总日志/性能/明细与独立开关均开启时读取已有AnimationState；不再查角色、动画或物理。
// snapshot_same_move=0时不能用新招时间判断旧招漏发；禁用/低权重状态仍输出其保留的时间并明确标志。
// 每类前32条及每256次输出累计数，避免大量持有者持续刷屏；关闭时无计时、遍历、分配或新增锁。
void AuditActionEnd(const Actor& a,const char* why,int observedMove,Ogre::AnimationState* state,bool paused){
    if(!actionEndLogging||!IrisDiagnostics::DetailsEnabled()||!a.active||a.move<0||a.move>=int(MOVE_COUNT))return;
    try{
        const Move& m=moves[a.move];const float raw=state?state->getTimePosition():0,length=state?state->getLength():0;
        const bool known=state&&observedMove==a.move&&Finite(raw)&&Finite(length)&&length>0&&Finite(m.seconds)&&m.seconds>0;
        const float observed=known?raw/length*m.seconds:0;
        const bool timeKnown=known&&Finite(observed);unsigned remaining=0,due=0,dueMarkers=0;
        for(size_t n=a.next;n<m.events.size();++n){++remaining;if(timeKnown&&m.events[n].time<=observed){++due;if(m.events[n].kind==5)++dueMarkers;}}
        float bladeGap=0;
        if(timeKnown&&a.move==4&&Finite(a.last))for(unsigned n=0;n<2;++n)
            bladeGap+=std::max(0.f,std::min(observed,bladeWindows[n].end)-std::max(a.last,bladeWindows[n].begin));
        const unsigned category=!timeKnown?0:due||bladeGap>0?1:remaining?2:3;
        static unsigned long long counts[4]={0,0,0,0};const unsigned long long count=++counts[category];
        if(count>32&&count%256!=0)return;
        std::ostringstream out;out<<"action_end_audit cast="<<a.id<<" actor="<<a.owner.index<<":"<<a.owner.serial
            <<" move="<<m.key<<" reason="<<why<<" observed_move="<<observedMove<<" snapshot_same_move="<<(observedMove==a.move)
            <<" state_present="<<(state!=0)<<" state_enabled="<<(state&&state->getEnabled())<<" state_weight="<<(state?state->getWeight():0)
            <<" time_known="<<timeKnown<<" raw_clip_seconds="<<raw<<" raw_length_seconds="<<length<<" action_seconds="<<observed
            <<" action_length_seconds="<<m.seconds<<" last_sample_seconds="<<a.last<<" action_rate="<<a.rate<<" paused="<<paused
            <<" next="<<a.next<<" total="<<m.events.size()<<" remaining="<<remaining<<" due_pending="<<due
            <<" due_marker_only="<<dueMarkers<<" blade_sample_gap_seconds="<<bladeGap
            <<" next_event_seconds="<<(a.next<m.events.size()?m.events[a.next].time:-1.f)
            <<" category="<<category<<" category_count="<<count<<" sampled=first32_then256"
            <<" emitted_jobs_unchanged=1 replay=0 missed_confirmed=0";Log(out.str());
    }catch(...){/* 诊断失败不得阻止End原有的收招、远程许可归还和附件隐藏。 */}
}
void End(Actor& a,const char* why,int observedMove=-1,Ogre::AnimationState* state=0,bool paused=false){
    AuditActionEnd(a,why,observedMove,state,paused);if(a.active){IrisDiagnostics::Add(IrisDiagnostics::CASTS_ENDED);std::ostringstream o;o<<"action_end cast="<<a.id<<" move="<<a.move<<" time="<<a.last<<" reason="<<why<<" drill_stumbles_suppressed="<<(a.move==3?a.stumbles:0)<<" melee_stumbles_suppressed="<<a.stumbles<<" emitted_effects_continue=1";Log(o.str());}
    else if(a.ranged&&a.reserved&&IrisDiagnostics::DetailsEnabled()){std::ostringstream o;o<<"ranged_action_not_started actor="<<a.owner.index<<":"<<a.owner.serial<<" move="<<a.move<<" wait_game_seconds="<<a.rangedWait<<" reason="<<why;Log(o.str());}
    if(a.ranged)IrisRanged::Finish(a.owner);a.ranged=false;a.active=false;a.reserved=false;a.havePose=false;a.drill.Hide();a.gun.Hide();a.blade.Hide();a.exhaust.Hide();a.flash.Hide();a.ion.Hide();a.halo.Hide();a.ignition.Hide();a.wings.Hide();a.muzzleFire.Hide();a.cannon.Hide();}
void Clear(bool alive,const char* reason){
    IrisNativeAudit::Reset(); // 084仅使旧世界诊断样本失效，不释放TLS栈上下文、不清原医疗请求以外的对象。
    IrisDiagnostics::ResetWindowAudit(); // 082读档/换场景清除阶段事实及连续拒绝，不清进程累计；不接触引擎对象。
    ++epoch;sphereFacts.clear();originKnown=false;warmReady=false;warmed.clear();resourcePeak=0;for(std::map<hand,Actor>::iterator i=actors.begin();i!=actors.end();++i)ClearActor(i->second,alive);actors.clear();
    for(size_t i=0;i<shots.size();++i)shots[i].visual.Clear(alive);shots.clear();for(size_t i=0;i<residues.size();++i)residues[i].visual.Clear(alive);residues.clear();
    for(size_t i=0;i<pool.size();++i)pool[i].Clear(alive);pool.clear();jobs.clear();hurts.clear();bladeVictims.clear();damageStats.clear();shotCursor=0;for(unsigned gauge=0;gauge<IrisDiagnostics::GAUGE_COUNT;++gauge)if(gauge!=IrisDiagnostics::RETIRED_GUNS)IrisDiagnostics::Set(IrisDiagnostics::Gauge(gauge),0);Log(std::string("ten_clear reason=")+reason);
}
// 103：启动只读INI，不设置Damage/距离/预算/阈值的业务上下限。
// 缺项仍用原默认；解析、有限值和目标类型错误明确报告，不钳制用户数值。
double MoveNumber(const std::wstring& ini,const std::string& section,const std::string& key,double fallback){
    const std::wstring ws(section.begin(),section.end()),wk(key.begin(),key.end());
    return IrisIni::Number(ini,ws.c_str(),wk.c_str(),fallback);
}
bool MoveSwitch(const std::wstring& ini,const std::string& section,const char* key,bool fallback){
    const double value=MoveNumber(ini,section,key,fallback?1:0);
    if(value!=0&&value!=1)throw std::runtime_error("move config must be Boolean 0 or 1: "+section+"."+key);return value!=0;
}
// 六招特效近战参与主动格挡保护；普通三连击排除。三远程的受击反应保护在后面单独配置。
bool BlockGuardMove(unsigned move){return move==0||move==1||move==2||move==3||move==4||move==8;}
// 本轮新增火焰翻滚两段破防/破闪避；其余近战原策略保持。
bool DefaultBypass(unsigned move){return move==0||move==2||move==3||move==4||move==8;}
void ConfigureMove(unsigned index,const std::wstring& ini){
    Move& move=moves[index];const std::string section="Move."+move.key;
    // 事件序号面向玩家从1开始；允许0关闭该段扣血，视觉/投射物/后效仍按原寿命处理。
    for(size_t event=0;event<move.events.size();++event){std::ostringstream key;key<<"Damage"<<event+1;
        move.events[event].mult=IrisIni::Float(MoveNumber(ini,section,key.str(),move.events[event].mult),key.str().c_str());}
    // 玩家要实测三招远程是否可能被格挡/闪避：三者都不注册额外防御上下文，
    // 不读取对应INI开关，不把HIT_SWORD/HIT_MISSED改成HIT_FLESH。七近战仍按配置。
    // 伤害入口保持原样；这不是迁移iShotYou，也不能在测试前预设必然格挡或必然命中。
    move.bypassDefence=(index==5||index==6||index==7)?false:MoveSwitch(ini,section,"BypassBlockDodge",DefaultBypass(index));
    // 远程光炮的FCS上限同时决定可视/物理长度，因此三招远程不增设独立距离覆盖。
    if(index!=5&&index!=6&&index!=7){
        // 先用double校验-1哨兵，再收窄到引擎float；防极小负数舍入成-0后被误收为合法距离。
        double low=MoveNumber(ini,section,"AttackMin",-1),high=MoveNumber(ini,section,"AttackMax",-1);
        if((low<0&&low!=-1)||(high<0&&high!=-1)||(low>=0&&high>=0&&low>high))throw std::runtime_error("move distance invalid: "+section);
        move.attackMin=IrisIni::Float(low,"AttackMin");move.attackMax=IrisIni::Float(high,"AttackMax");
    }
    // 六招特效近战分别配置主动格挡接管和受击反应保护；两开关独立。三远程只在下一分支配置受击保护。
    if(BlockGuardMove(index)){move.preventBlock=MoveSwitch(ini,section,"PreventBlockInterrupt",true);move.immuneReactions=MoveSwitch(ini,section,"ImmuneHitReactions",true);}
    // 047：三远程仅开放自身受击反应保护；不开放转格挡保护，更不改变对敌伤害的防御结果。
    if(index==5||index==6||index==7)move.immuneReactions=MoveSwitch(ini,section,"ImmuneHitReactions",true);
    std::ostringstream out;out<<"move_parameters move="<<move.key<<" damage=";
    for(size_t n=0;n<move.events.size();++n)out<<(n?",":"")<<move.events[n].mult;
    out<<" attack_min_override="<<move.attackMin<<" attack_max_override="<<move.attackMax<<" bypass_block_dodge="<<move.bypassDefence<<" prevent_block="<<move.preventBlock<<" immune_reactions="<<move.immuneReactions<<" geometry=source_locked";Log(out.str());
}
// 097轨道来自同包男女身体动画的Prop2全局变换并右乘SourcePose的同一换基。
// 源轨道不含场景/角色指针；运行时用本帧真实附件反解角色锚点，避免首尾接近时丢掉整圈刀路。
void LoadBladePoses(){
    std::ifstream file((directory+L"assets\\blade_poses097.csv").c_str());std::string magic;unsigned version,tracks;
    if(!(file>>magic>>version>>tracks)||magic!="IRIS_BLADE_POSES"||version!=1||tracks!=2)throw std::runtime_error("097 blade pose header");
    for(unsigned sex=0;sex<2;++sex){unsigned index,count;float duration;std::string hash;
        if(!(file>>index>>count>>duration>>hash)||index!=sex||count<2||count>4096||!Finite(duration)||fabsf(duration-moves[4].seconds)>.0001f||hash.size()!=64)throw std::runtime_error("097 blade pose shape");
        bladePoses[sex].clear();bladePoses[sex].reserve(count);
        for(unsigned i=0;i<count;++i){BladePose p;
            if(!(file>>p.time>>p.position.x>>p.position.y>>p.position.z>>p.rotation.w>>p.rotation.x>>p.rotation.y>>p.rotation.z)||
                !Finite(p.time)||!Finite(p.position)||fabsf(p.time-duration*float(i)/float(count-1))>.00002f)throw std::runtime_error("097 blade pose value");
            const double norm=double(p.rotation.w)*p.rotation.w+double(p.rotation.x)*p.rotation.x+double(p.rotation.y)*p.rotation.y+double(p.rotation.z)*p.rotation.z;
            if(!IrisSector::Finite(norm)||fabs(norm-1)>.0001)throw std::runtime_error("097 blade pose rotation");
            bladePoses[sex].push_back(p);
        }
    }std::string tail;if(file>>tail)throw std::runtime_error("097 blade pose trailing");
}
Matrix4 BladePoseAt(unsigned sex,float t){
    const std::vector<BladePose>& track=bladePoses[sex];const float x=std::max(0.f,std::min(float(track.size()-1),t/moves[4].seconds*float(track.size()-1)));
    const unsigned lo=unsigned(x),hi=std::min(unsigned(track.size()-1),lo+1);const float u=x-lo;
    return Pose(track[lo].position+(track[hi].position-track[lo].position)*u,
        Quaternion::Slerp(u,track[lo].rotation,track[hi].rotation,true),Vector3::UNIT_SCALE);
}

void Configure(const std::wstring& dir){
    Log(std::string("fire_cannon_ready contract=")+FIRE_CANNON_CONTRACT+" roll_full_visual_clock=source_baked067 drill_visual_clock=source_baked064 fire_begin=.56 electro_axis=actual_native_muzzle damage_timing_unchanged=1 new_threads=0");
    IrisDiagnostics::Scope timing(IrisDiagnostics::ASSET_READ,"ten_move_assets_and_curves");
    Log(PARAMETER_CONTRACT);
    // 063视觉合同仅标记两招附件；062原生许可/选招/Emit与057碰撞体原样保留。
    Log("IRIS_SOURCE_MUZZLE_063 vulcan=anim+anim1 small_spin=source_frequency5_cycle4.125 pulse=source_824_fire generic_reticle=removed new_threads=0 combat_unchanged=1");
    directory=dir;std::wstring ini=directory+L"IrisArsenal.ini";
    actionEndLogging=MoveSwitch(ini,"IrisArsenal","EnableActionEndLogging",false);
    {std::ostringstream out;out<<"IRIS_HOLDER_TIMELINE_104 formal_holder_limit=none action_end_logging="<<(actionEndLogging&&IrisDiagnostics::DetailsEnabled())<<" event_replay=0 gun_retirement=original_safe_queue";Log(out.str());}
    queryGateRefinement=MoveSwitch(ini,"IrisArsenal","EnableQueryGateRefinement",true);
    {std::ostringstream out;out<<"query_gate_ready contract=IRIS_QUERY_GATE_100 enabled="<<queryGateRefinement
        <<" logging="<<IrisDiagnostics::QueryGateLoggingEnabled()<<" policy=empty_actual_queues_and_sdk_writable"
        <<" existing_safe_callback=1 main_and_back=1 no_cross_frame_permit=1 no_forced_flush=1 new_hooks=0 new_threads=0";Log(out.str());}
    // 053启动读取：预算是一次安全窗口的处理时间，不是冷却；目标是观察阈值，不是超时丢弃。
    // 103：20ms只存在于INI；此处直接读取，不再设10/20ms硬编码边界。
    // 原每轮128笔配置、256扫描及FIFO/逐笔安全门保持，原生单次调用仍不可抢占。
    damageFlushBudgetMs=MoveNumber(ini,"IrisArsenal","DamageFlushBudgetMs",2.5);
    Log("IRIS_INI_DIRECT_103 numeric_business_bounds=none budget_source=INI schedule_unchanged=1 new_threads=0");
    damageQueueTargetMs=MoveNumber(ini,"IrisArsenal","DamageQueueTargetMs",40);
    const double maxHits=MoveNumber(ini,"IrisArsenal","DamageFlushMaxHits",12);
    if(floor(maxHits)!=maxHits)throw std::runtime_error("move config requires integer: IrisArsenal.DamageFlushMaxHits");
    damageFlushMaxHits=IrisIni::Unsigned(maxHits,"DamageFlushMaxHits");
    /* 103追赶额度同样直接来自INI；保持旧启用/年龄门，只在请求值高于普通额度时增加。 */
    damageCatchupEnabled=MoveSwitch(ini,"IrisArsenal","EnableDamageBacklogCatchup",true);
    damageCatchupBudgetMs=MoveNumber(ini,"IrisArsenal","DamageCatchupBudgetMs",5);
    const double catchupHits=MoveNumber(ini,"IrisArsenal","DamageCatchupMaxHits",64);
    if(floor(catchupHits)!=catchupHits)throw std::runtime_error("move config requires integer: IrisArsenal.DamageCatchupMaxHits");
    damageCatchupMaxHits=IrisIni::Unsigned(catchupHits,"DamageCatchupMaxHits");
    {std::ostringstream out;out<<"damage_catchup_ready contract=IRIS_DAMAGE_CATCHUP_099 enabled="<<damageCatchupEnabled
        <<" logging="<<IrisDiagnostics::DamageCatchupLoggingEnabled()<<" base_budget_ms="<<damageFlushBudgetMs<<" base_max_hits="<<damageFlushMaxHits
        <<" requested_budget_ms="<<damageCatchupBudgetMs<<" requested_max_hits="<<damageCatchupMaxHits<<" age_target_ms="<<damageQueueTargetMs
        <<" requested_values_direct=1 oldest_first=1 ordinary_path_unchanged=1 same_native_safe_callback=1 per_request_gates=retained new_hooks=0 new_threads=0";Log(out.str());}
    // 056启动配置：关闭合批即回到原逐路径查询；慢受击阈值只控制诊断，不改医疗预算/伤害。
    // 094只在原安全Tick加载资产时配置；过滤/逐段去重/医疗FIFO仍由原消费者负责。
    IrisNative::ConfigureConservativeQueries(MoveSwitch(ini,"IrisArsenal","EnableConservativeDamageQueries",true));
    // 097旧扩盒内核和自动对照已退役；只记录原生策略，不把局部接口替换伪称必然性能提升。
    {std::ostringstream out;out<<"native_sector_ready contract=IRIS_NATIVE_SECTOR_097 sphere_contract=IRIS_CONSERVATIVE_QUERY_094 capsule=native_overlap_false zero_capsule=native_sphere_false sector=native_cull_AABB max_degrees=90 incremental=1 shared_boundary=1 extra_hits=accepted same_strike_dedup=1 manual_box_capsule=retired proof095=retired new_threads=0";Log(out.str());}
    rangedBatchEnabled=MoveSwitch(ini,"IrisArsenal","EnableRangedQueryBatching",true);
    rangedQueryReuse=MoveSwitch(ini,"IrisArsenal","EnableRangedQueryReuse",true);
    rangedEmptyPruning=MoveSwitch(ini,"IrisArsenal","EnableRangedEmptyPruning",true);
    rangedEmptyShadow=MoveSwitch(ini,"IrisArsenal","EnableRangedEmptyShadow",false);
    rangedSpatialPruning=MoveSwitch(ini,"IrisArsenal","EnableRangedSpatialPruning",true);
    rangedSingleProbe=MoveSwitch(ini,"IrisArsenal","EnableRangedSingleEmptyProbe",false);
    projectileWorkLogging=MoveSwitch(ini,"IrisArsenal","EnableProjectileWorkLogging",false);
    {std::ostringstream out;out<<"IRIS_SPATIAL_PROJECTILES_090 spatial="<<rangedSpatialPruning<<" single_probe="<<rangedSingleProbe<<" projectile_work="<<projectileWorkLogging
        <<" projectile_count_limit=none active_visual_limit=none idle_pool_max=96 query_budget=64 job_capacity_unchanged=256 group_max=8 order=original_cast_event new_threads=0";Log(out.str());}
    {std::ostringstream out;out<<"IRIS_RANGED_WORK_089 exact_reuse="<<rangedQueryReuse<<" empty_pruning="<<rangedEmptyPruning<<" empty_shadow="<<rangedEmptyShadow<<" empty_proof=whole_AABB_no_character budget=64 extra_probe_reserved=1 scope=same_batch unknown=original_sweep";Log(out.str());}
    capsuleBatchEnabled=MoveSwitch(ini,"IrisArsenal","EnableCapsuleBatching",true);
    // 097复合提交不再有自写替代算法，旧EnableCapsuleBatchShadow不读取、不执行额外查询。
    nativeHitSlowMs=MoveNumber(ini,"IrisArsenal","NativeHitSlowMs",1);
    {std::ostringstream out;out<<COLLISION_DAMAGE_CONTRACT<<" capsule_batch="<<capsuleBatchEnabled<<" batch_contract=IRIS_CAPSULE_POLICY_081 ranged_batch="<<rangedBatchEnabled<<" query_contract=IRIS_QUERY_BATCH_088 strategy=native_capsule_each paths_max=8 query_budget=64 charge=actual_sdk_commands no_shadow=1 no_manual_batch=1 native_slow_ms="<<nativeHitSlowMs<<" new_threads=0";Log(out.str());}
    {std::ostringstream out;out<<DAMAGE_QUEUE_CONTRACT<<" budget_ms="<<damageFlushBudgetMs<<" target_wall_ms="<<damageQueueTargetMs<<" max_native_hits="<<damageFlushMaxHits<<" max_inspections=256 order=FIFO target_is_soft=1 wall_includes_pause=1 no_timeout_drop=1";Log(out.str());}
    // 083按职责区分查询与医疗安全门；只记录启动配置，不在热路径新增诊断getter或同步对象。
    {std::ostringstream out;out<<"medical_gate_ready contract=IRIS_MEDICAL_GATE_083 medical_requires_queues=0 query_queue_gate=retained world_recheck=each_request physics_recheck=each_request ai_recheck=each_request order=FIFO budget_ms="<<damageFlushBudgetMs<<" max_native_hits="<<damageFlushMaxHits<<" native_outside_plugin_lock=1 new_hooks=0 new_threads=0";Log(out.str());}
    proofOnly=IrisIni::Flag(ini,L"IrisArsenal",L"DrillProofOnly",false);damageEnabled=IrisIni::Flag(ini,L"IrisArsenal",L"DamageEnabled",true);
    // 080默认0，正常演出不变；仅供两次相同场景对照，需重启读取，不在逐帧/Hook中访问INI。
    diagnosticHideEffects=MoveSwitch(ini,"IrisArsenal","DiagnosticHideEffects",false);
    parameterGroupReuse=MoveSwitch(ini,"IrisArsenal","EnableVisualParameterGroupReuse",true);
    {std::ostringstream out;out<<"parameter_group_reuse_ready contract=IRIS_QUERY_BOUNDARY_093 enabled="<<parameterGroupReuse<<" equality=float_bits cache_owner=visual successful_submit_only=1 allocation_failure=original";Log(out.str());}
    {std::ostringstream out;out<<"performance_ready contract=IRIS_PERFORMANCE_080 terrain_zero_only=1 full_sweep_else=1 contact_memo=query_adjacent_full_identity visual_parameters=instance_bitwise beam_draw=after_queries hide_effects="<<diagnosticHideEffects<<" default_hide=0 medical_policy=split_gate_083 new_hooks=0 new_locks=0 new_threads=0 GPU_measured=0";Log(out.str());}
    std::ifstream windows((directory+L"assets\\blade_windows.csv").c_str());std::string windowMagic;unsigned windowVersion,windowCount;
    if(!(windows>>windowMagic>>windowVersion>>windowCount)||windowMagic!="IRIS_BLADE_WINDOWS"||windowVersion!=1||windowCount!=3)throw std::runtime_error("blade windows contract");
    for(unsigned n=0;n<3;++n){unsigned index;if(!(windows>>index>>bladeWindows[n].begin>>bladeWindows[n].end)||index!=n||!Finite(bladeWindows[n].begin)||!Finite(bladeWindows[n].end)||bladeWindows[n].begin>=bladeWindows[n].end)throw std::runtime_error("blade window invalid");}
    // 061本次明确采用原生“真实昏迷即排除”；旧DamageUnconsciousTargets不再覆盖此规则。
    Log(std::string("damage_target_config contract=")+COMBAT_POLICY_CONTRACT+" policy=native_melee_four_checks ally=false enemy_disguises=true current_active_target_exception=1 true_unconscious=skip legacy_unconscious_option=ignored ranged_non_damageable=transparent detail_line_limit=0");
    // 075：正式十招按各自Actor/原生战斗状态起手，不再让其他持有者占用全局攻击名额。
    // MaxActiveActors仅保留给DrillProofOnly诊断原型；查询64次及既有容量保持，医疗额度直接读取INI。
    Log("IRIS_MULTI_ACTOR_075 formal_global_start_gate=0 actor_state=per_handle tracked_capacity=8 query_budget=64 medical_budget_unchanged=1 proof_limit_unchanged=1 new_threads=0 new_hooks=0");
    std::ifstream f((directory+L"assets\\moves.csv").c_str());std::string magic,tail;unsigned version,count;
    if(!(f>>magic>>version>>count)||magic!="IRIS_EIGHT"||version!=1||count!=MOVE_COUNT)throw std::runtime_error("ten profile header");
    const unsigned expected[MOVE_COUNT]={2,3,4,12,3,20,3,4,4,3};
    for(unsigned i=0;i<MOVE_COUNT;++i){unsigned index,events;float min,max;
        if(!(f>>index>>moves[i].key>>moves[i].animation>>moves[i].seconds>>events>>min>>max)||index!=i||events!=expected[i]||!Finite(moves[i].seconds)||moves[i].seconds<=0)throw std::runtime_error("eight move contract");
        wchar_t key[64];MultiByteToWideChar(CP_UTF8,0,moves[i].key.c_str(),-1,key,64);
        // 权重直接读取；沿用消费者中<=0不参与选招的规则，不再硬编码10000上限。
        moves[i].weight=IrisIni::Number(ini,L"MoveWeights",key,1);
        for(unsigned j=0;j<events;++j){Event e;if(!(f>>e.time>>e.kind>>e.mult>>e.radius)||!Finite(e.time)||!Finite(e.mult)||!Finite(e.radius)||e.time<0||e.time>=moves[i].seconds||e.kind>9||e.mult<=0||e.radius<0||(j&&e.time<moves[i].events.back().time))throw std::runtime_error("eight event contract");moves[i].events.push_back(e);}
        ConfigureMove(i,ini);
    }if(f>>tail)throw std::runtime_error("eight trailing data");
    // 102防止新DLL配旧5.5秒动作表；FCS仍为1倍，分段加速由动画数据完成，禁止整招再次乘2。
    if(fabsf(moves[7].seconds-(5.5f-DRIVE_SOURCE_FIRE*.5f))>.00002f||
       fabsf(moves[7].events.front().time-DRIVE_SOURCE_FIRE*.5f)>.00002f)
        throw std::runtime_error("102 drive timeline mismatch; update complete mod package");
    {std::ostringstream out;out<<PROJECTILE_TIMELINE_CONTRACT<<" vulcan_speed=1500 pulse_speed=1000 flight_clock=game_seconds attack_rate_affects_flight=0 drive_pre_fire_multiplier=2 drive_post_fire_multiplier=1 drive_first_shot="<<moves[7].events.front().time<<" drive_duration="<<moves[7].seconds<<" new_threads=0";Log(out.str());}
    LoadBladePoses(); // 097先校验同包轨道，再接受招式；启动读取，无逐帧文件I/O。
    std::ifstream cueFile((directory+L"assets\\effect_cues.csv").c_str());unsigned cueCount;
    if(!(cueFile>>magic>>version>>cueCount)||magic!="IRIS_FX_CUES"||version!=1||cueCount>64)throw std::runtime_error("effect cue header");
    for(unsigned n=0;n<cueCount;++n){unsigned index;FxCue cue;
        if(!(cueFile>>index>>cue.key>>cue.time)||index>=MOVE_COUNT||!Finite(cue.time)||cue.time<0||cue.time>=moves[index].seconds||
           (cue.key!="backfire"&&cue.key!="gun"&&cue.key!="off"&&cue.key!="ignition"&&cue.key!="charge_halo"&&cue.key!="wing"&&cue.key!="wing_off"))throw std::runtime_error("effect cue shape");
        moves[index].cues.push_back(cue);
    }if(cueFile>>tail)throw std::runtime_error("effect cue trailing data");
    // 先读窗口、再按实际moves流核对时间/段数；不允许旧资产或越过动作长度的窗口进入运行。
    if(windows>>tail)throw std::runtime_error("blade windows trailing data");
    for(unsigned n=0;n<3;++n)if(bladeWindows[n].begin<0||bladeWindows[n].end>moves[4].seconds||bladeWindows[n].begin>moves[4].events[n].time||bladeWindows[n].end<moves[4].events[n].time||(n&&bladeWindows[n].begin<bladeWindows[n-1].end))throw std::runtime_error("blade windows timing mismatch");
    std::ifstream fx((directory+L"assets\\effects.csv").c_str());if(!(fx>>magic>>version>>count)||magic!="IRIS_FX"||version!=4||count!=22)throw std::runtime_error("effect profile header");
    for(unsigned i=0;i<count;++i){std::string key;Asset a;unsigned subs;if(!(fx>>key>>a.mesh>>subs>>a.center.x>>a.center.y>>a.center.z>>a.bound)||!Finite(a.center)||!Finite(a.bound)||a.bound<=0||!subs||subs>32)throw std::runtime_error("effect asset contract");for(unsigned j=0;j<subs;++j){std::string m;if(!(fx>>m)||m.find("IrisArsenal/")!=0)throw std::runtime_error("effect material contract");a.materials.push_back(m);}assets[key]=a;}
    // 047分层时间流：13类、32子层、241采样、25个有限浮点；读入后进程内共享，实例仅保存年龄。
    std::ifstream curves((directory+L"assets\\effect_curves.csv").c_str());
    // 063仅新增gun/vulcan_body/pulse_muzzle三份源时钟，由14增为17；效果表20增为22，保持32层/241样本上限。
    if(!(curves>>magic>>version>>count)||magic!="IRIS_FX_CURVES"||version!=1||count!=17)throw std::runtime_error("effect curve header");
    std::set<std::string> seenCurves;
    for(unsigned i=0;i<count;++i){std::string key;unsigned subs,samples;float duration,peak;
        if(!(curves>>key>>subs>>samples>>duration>>peak)||!assets.count(key)||!seenCurves.insert(key).second||subs!=assets[key].materials.size()||subs>32||samples<2||samples>241||!Finite(duration)||duration<=0||duration>8||!Finite(peak)||peak<=0)throw std::runtime_error("effect curve shape");
        Asset& a=assets[key];a.duration=duration;a.peak=peak;a.samples=samples;a.tracks.resize(subs);
        for(unsigned sub=0;sub<subs;++sub){a.tracks[sub].resize(samples);for(unsigned frame=0;frame<samples;++frame)for(unsigned k=0;k<25;++k){float& v=a.tracks[sub][frame].value[k];if(!(curves>>v)||!Finite(v)||fabsf(v)>1000000)throw std::runtime_error("effect curve value");}}
    }if(curves>>tail)throw std::runtime_error("effect curve trailing data");
    // 仅加载时分析自有轨道，不新增逐帧扫描；掩码是候选，实际提交始终逐位核对。
    for(std::map<std::string,Asset>::iterator i=assets.begin();i!=assets.end();++i)if(i->second.samples)BuildParameterGroups(i->second);
    // 038中心流由同一组源翼片逐帧包围中心生成，单位为相对真实WEAPON的Kenshi单位。
    // header不匹配/非有限坐标立即拒绝新合同，不能用武器枪口或目标位置猜球心。
    std::ifstream centers((directory+L"assets\\wing_centers.csv").c_str());
    if(!(centers>>magic>>version>>count>>wingCenterBegin>>wingCenterEnd)||magic!="IRIS_WING_CENTERS"||version!=1||count<2||count>241||!Finite(wingCenterBegin)||!Finite(wingCenterEnd)||wingCenterBegin<0||wingCenterEnd<=wingCenterBegin||wingCenterEnd>moves[3].seconds)throw std::runtime_error("wing centers header");
    // 中心和可见翼片必须是同一采样/同一起止时钟；即使文件可解析，也不能接受来自别版的中心流。
    if(count!=assets["drill_wings"].samples||fabsf(wingCenterEnd-wingCenterBegin-assets["drill_wings"].duration)>.001f)throw std::runtime_error("wing centers timeline mismatch");
    bool centerClockKnown=false;for(size_t n=0;n<moves[3].cues.size();++n)if(moves[3].cues[n].key=="wing"&&fabsf(moves[3].cues[n].time-wingCenterBegin)<.001f)centerClockKnown=true;
    if(!centerClockKnown)throw std::runtime_error("wing centers cue mismatch");
    wingCenters.clear();for(unsigned n=0;n<count;++n){Vector3 p;if(!(centers>>p.x>>p.y>>p.z)||!Finite(p)||p.squaredLength()>1000000)throw std::runtime_error("wing center value");wingCenters.push_back(p);}
    if(centers>>tail)throw std::runtime_error("wing centers trailing data");
    // 钻头复用上一轮已验证的19层源模型与金属/光学材质，不能退回绿色线框或黑剪影。
    std::ifstream df((directory+L"assets\\drill.csv").c_str());std::string line;std::getline(df,line);std::getline(df,line);
    // 098保留既有drill.csv v2读取位置；八段历史拟合仅校验格式，不再保留运行时胶囊数组。
    // 伤害改为真实钻头+外环的单球，不改材质、源网格、动作或此资源格式。
    for(unsigned i=0;i<8;++i){float from,to,radius;if(!(df>>from>>to>>radius)||!Finite(from)||!Finite(to)||!Finite(radius)||to<=from||radius<=0)throw std::runtime_error("drill capsule list");}
    Asset drill;drill.mesh="iris_drill.mesh";
    for(unsigned i=0;i<19;++i){unsigned sub;std::string mat;if(!(df>>sub>>mat)||sub!=i)throw std::runtime_error("drill material list");drill.materials.push_back(mat);}assets["drill"]=drill;
    {std::ostringstream out;out<<"drill_sphere_ready contract="<<DRILL_SPHERE_CONTRACT<<" local_center_z="<<DRILL_SPHERE_CENTER_Z<<" local_radius="<<DRILL_SPHERE_RADIUS<<" layers=19 events=11 query=native_sphere_AABB source=mesh_full_spin new_threads=0";Log(out.str());}
    Log("ranged_collision_ready contract=IRIS_RANGED_RAY_057 terrain=finite_ray characters=vulcan_pulse_sphere_sweep_drive_flat_cylinder wall_tie=terrain first_hit_after_friendly_filter=1 query_pair_atomic=1 safe_window=existing background_thread=0");
    // 077明确区别原生开火检查与弩箭飞行组；旧DLL不含此标记，不能以源码/INI冒充部署。
    Log("ranged_terrain_ready contract=IRIS_NATIVE_TERRAIN_077 terrain_groups=0x087FDE47 source=native_Harpoon_flight terrain=finite_ray characters=original_radius_and_groups zero_distance=preserved trigger_policy=SDK_native new_hooks=0 new_threads=0");
    // 064记录源环体及终结资源合同；只改自有可视实例，不新增Hook/物理体/线程。
    Log("IRIS_BURST_CALIBRATION_068 detached_clock=game_seconds quake_and_electro=animation_rate source_fade=out_start full_scale_keys=1 source_rotation=1 shared_shader_changed=0 damage_unchanged=1 new_threads=0");
    Log("IRIS_THREE_SOURCE_FX_067 roll=439C0+6051F+824 full=824+3F9ED electro=886+824 clocks=source_baked beam_restart=per_successful_event damage_unchanged=1 new_threads=0");
    Log("IRIS_DRILL_RING_GATE_066 gate=instance_custom9 clip_before_spin=1 ring_and_drill_shared_pose=1 index_zero_not_hide=1 new_threads=0");
    Log("IRIS_DRILL_FINISHER_064 center=source_wing_midpoint trigger=launch_no_projectile sphere_radius=120 burst=source_ALS+Stokes+DragonRend_then_FireWave ring_on=1.633268 red_arcs=source_four_planes collar=source_mesh clock=source_baked064");
    std::ifstream wc((directory+L"assets\\weapon_collision.csv").c_str());
    if(!(wc>>magic>>version>>count)||magic!="IRIS_WEAPON_CAPSULES"||version!=1||count!=8)throw std::runtime_error("weapon capsule header");
    for(unsigned i=0;i<8;++i){WeaponCapsule& c=weaponCapsules[i];if(!(wc>>c.x>>c.y>>c.a>>c.b>>c.r)||!Finite(c.x)||!Finite(c.y)||!Finite(c.a)||!Finite(c.b)||!Finite(c.r)||c.b<=c.a||c.r<=0)throw std::runtime_error("weapon capsule input");}
    Log("IRIS_SEAT_SURFACE_CANNON_050 electro_center=source_muzzle_height forward=20 radius=25 native_health_events=4");
    Log(std::string("ten_config contract=")+CONTRACT+" fire_roll=2 spiral=3 earthquake=4 drill=12 full_burst=3 vulcan=20 pulse=3 drive=4 electro_cannon=4 hammer_combo=3 public_FCS_chance=0; native_damage_and_armour=1");
}
bool ProofOnly(){return proofOnly;}
bool HasRangedMoves(){return moves[5].weight>0||moves[6].weight>0||moves[7].weight>0;}
float RangedRange(){float range=0;for(unsigned i=5;i<=7;++i)if(moves[i].weight>0&&moves[i].technique)range=std::max(range,moves[i].technique->initialDistance);return range;}

void Observe(Character* c){
    // 104：map按完整hand去重；新持有者不因其他角色已注册而被拒绝。
    // 仍由原入口持有既有mutex；离场/读档沿用原清理，不扩大医疗或查询额度。
    if(!c||actors.count(c->handle))return;
    Actor a;a.owner=c->handle;actors.insert(std::make_pair(c->handle,a));
}
bool RangedMove(unsigned i){return i==5||i==6||i==7;}

int Index(CombatTechniqueData* t){for(int i=0;i<int(MOVE_COUNT);++i)if(t&&t==moves[i].technique)return i;return -1;}
// 091同一次就绪检查只取一次状态/长度；不跨帧缓存，也不越过start/run等原生动画更新复用。
// 原Loaded包装在正式路径已无调用，旧版对照仅由091测试临时重建；本函数仍保留原生hasAnimation资格。
// 保留原hasAnimation资格和缺失/非有限/非正长度回退，义肢/种族/骨架逻辑不改。
float AnimationLength(Character* c,int i){
    if(!c||!c->animation||!c->animation->hasAnimation(moves[i].animation))return 0;
    Ogre::AnimationState* s=c->animation->getAnimationState(moves[i].animation);
    const float length=s?s->getLength():0;return Finite(length)&&length>0?length:0;
}
CombatTechniqueData* Choose(CharStats* stats,float range){
    Character* c=stats?stats->me:0;if(!Iris::ActorReady(c)||!Finite(range))return 0;
    std::map<hand,Actor>::iterator it=actors.find(c->handle);if(it==actors.end()){Observe(c);return 0;}
    Actor& actor=it->second;if(!warmReady||!actor.ready||actor.animation!=c->animation)return 0;double sum=0;
    // 075：只检查当前角色的动画/资源和距离；reserved仍属于该Actor，不可阻止别的角色起手。
    // 原生持械/医疗判断由调用者保留；不为并发改FCS距离、权重或引擎移动锁。
    for(unsigned i=0;i<MOVE_COUNT;++i){CombatTechniqueData* t=moves[i].technique;if(!RangedMove(i)&&t&&moves[i].weight>0&&range>=t->minDistanceVsStatic&&range<=t->initialDistance&&actor.lengths[i]>0)sum+=moves[i].weight;}
    if(sum<=0)return 0;randomState^=randomState<<13;randomState^=randomState>>17;randomState^=randomState<<5;double pick=(double(randomState)/4294967296.0)*sum;
    for(unsigned i=0;i<MOVE_COUNT;++i){CombatTechniqueData* t=moves[i].technique;if(!RangedMove(i)&&t&&moves[i].weight>0&&range>=t->minDistanceVsStatic&&range<=t->initialDistance&&actor.lengths[i]>0){pick-=moves[i].weight;if(pick<0){actor.reserved=true;return t;}}}return 0;
}
int PickRanged(Actor& actor,float range){
    // 075：原生许可已经按角色产生；一人的active/reserved不能拒绝另一人的这次射击。
    if(!warmReady||!actor.ready)return -1;double sum=0;
    // 仍只读各招私有FCS起手区间与INI权重，一次原生射击许可播放整套20发/3发/4脉冲，不按每个健康事件重新装填。
    for(unsigned i=5;i<=7;++i){CombatTechniqueData* t=moves[i].technique;if(t&&moves[i].weight>0&&actor.lengths[i]>0&&range>=t->minDistanceVsStatic&&range<=t->initialDistance)sum+=moves[i].weight;}
    if(sum<=0)return -1;randomState^=randomState<<13;randomState^=randomState>>17;randomState^=randomState<<5;double pick=(double(randomState)/4294967296.0)*sum;
    for(unsigned i=5;i<=7;++i){CombatTechniqueData* t=moves[i].technique;if(t&&moves[i].weight>0&&actor.lengths[i]>0&&range>=t->minDistanceVsStatic&&range<=t->initialDistance){pick-=moves[i].weight;if(pick<0)return int(i);}}return -1;
}
float Speed(AnimationClass* a,CombatTechniqueData* t,float speed){
    // AI回调只消费主线程缓存，不在AI线程进入Ogre；保存动作倍率用于动作/发射节拍，弹体飞行独立。
    int n=Index(t);if(n<0||!a||!Finite(speed)||speed<=0)return speed;
    for(std::map<hand,Actor>::iterator i=actors.begin();i!=actors.end();++i)if(i->second.animation==a&&i->second.ready&&i->second.lengths[n]>0){
        i->second.rates[n]=speed;double v=double(speed)*i->second.lengths[n]/moves[n].seconds;return v>0&&v<=FLT_MAX?float(v):speed;}
    return speed;
}
void Started(AnimationClass* a,CombatTechniqueData* t){if(Index(t)<0)return;for(std::map<hand,Actor>::iterator i=actors.begin();i!=actors.end();++i)if(i->second.animation==a)++i->second.start;}

hand Handle(const IrisNative::ObjectKey& k){return k.present?hand(k.index,k.serial,itemType(k.type),k.container,k.containerSerial):hand();}
// 087仅保存本次连续接触消费中的完整稳定身份和资格结果；不保存角色/PhysX地址、不跨查询/帧。
// 相邻重复仍先走旧快路；16槽直接映射只减非相邻重复。哈希冲突完整比较，不同身份重新调用原规则。
// 无堆分配/锁；槽被覆盖只失去复用机会，绝不把碰撞当同一目标。医疗前依旧重新检查资格。
bool SameContactIdentity(const IrisNative::ObjectKey& a,const IrisNative::ObjectKey& b){
    return a.present==b.present&&a.type==b.type&&a.container==b.container&&a.containerSerial==b.containerSerial&&a.index==b.index&&a.serial==b.serial;
}
unsigned ContactMemoSlot(const IrisNative::ObjectKey& key){
    unsigned h=2166136261U;h=(h^key.type)*16777619U;h=(h^key.container)*16777619U;
    h=(h^key.containerSerial)*16777619U;h=(h^key.index)*16777619U;h=(h^key.serial)*16777619U;h=(h^unsigned(key.present))*16777619U;
    return h&15U;
}
struct RangedContactMemo {
    struct Entry {IrisNative::ObjectKey key;bool ignored;};Entry slots[16];unsigned occupied;
    IrisNative::ObjectKey previous;bool valid,ignored;unsigned checks,reuses,collisions;
    RangedContactMemo():occupied(0),valid(false),ignored(false),checks(0),reuses(0),collisions(0){}
    bool Ignore(Character* caster,const IrisNative::ObjectKey& key,const hand& identity){
        if(valid&&SameContactIdentity(previous,key)){++reuses;return ignored;}
        unsigned slot=ContactMemoSlot(key),bit=1U<<slot;
        if((occupied&bit)&&SameContactIdentity(slots[slot].key,key)){ignored=slots[slot].ignored;++reuses;}
        else{
            if(occupied&bit)++collisions;
            Character* candidate=identity.getCharacter();ignored=candidate==caster||IgnoreRangedContact(caster,candidate);++checks;
            slots[slot].key=key;slots[slot].ignored=ignored;occupied|=bit;
        }
        previous=key;valid=true;return ignored;
    }
};
// 094只在SDK完全返回后观察纯值；正常查询无逐项日志，异常首8条/异常码变化或10秒最多一条。
// 容量异常不是正常漏选；明确记入摘要且不整批重算。总门或此门关闭时不读新时钟/加统计锁。
void ObserveConservativeQuery(unsigned kind,unsigned raw,unsigned contacts,unsigned tests,unsigned identity,unsigned geometry,unsigned capacity,unsigned input,unsigned exception){
    if(!kind||!IrisDiagnostics::ConservativeQueryLoggingEnabled())return;
    IrisDiagnostics::RecordConservativeQuery(kind,raw,contacts,tests,identity,geometry,capacity,input);
    if(!identity&&!geometry&&!capacity&&!input)return;
    static unsigned notices=0,lastCode=0;static double lastAt=0;const double now=IrisDiagnostics::Now();
    if(notices>=8&&now-lastAt<10000&&(exception==lastCode||now-lastAt<1000))return;
    ++notices;lastAt=now;lastCode=exception;
    std::ostringstream out;out<<"conservative_query_skipped contract=IRIS_CONSERVATIVE_QUERY_094 kind="<<kind<<" raw="<<raw<<" contacts="<<contacts
        <<" skipped_identity="<<identity<<" skipped_geometry="<<geometry<<" skipped_capacity="<<capacity<<" skipped_input="<<input
        <<" exception=0x"<<std::hex<<exception<<std::dec<<" action=skip_item valid_results_retained=1 requery=0 notice="<<notices;Log(out.str());
}
void ObserveConservativeContacts(const IrisNative::Contacts& result){
    const IrisNative::Diagnostic& d=result.diagnostic;
    ObserveConservativeQuery(d.approximateKind,d.received,result.count,0,d.skippedIdentity,d.skippedGeometry,d.skippedCapacity,d.skippedInput,d.identityException);
}
/* 100实测结论（2026-10-26，0.4.50压力测试）：1876次复核、额外放行0次，
   本轮几乎没有优化效果；检查本体累计0.417ms，未发现明显性能损失，并非绝对零开销。
   按用户要求保留实现及当前开关，不回退；不得将其描述为已改善FPS或查询等待。
   真实阻挡主要为后台创建/销毁消息，不是仅clear快照滞后；详见本会话性能分析100。 */
/* 100旧clear快照可以滞后于后台完成；只在原门false时检查真实消息。
   容器元数据只在原生安全主线程、physics/AI停止阶段读取；不解引用任何队列元素。
   活跃hulls/constantTracers不是待处理队列，不能要求活跃世界为空。 */
template<typename T> bool QueryVectorState(lektor<T>& values,unsigned bit,unsigned& mask){
    if(values.count>values.maxSize||(values.count&&!values.stuff))return false;
    if(values.count)mask|=1U<<bit;return true;
}
template<typename T> bool QueryChainState(MessageChain<T>& chain,unsigned bit,unsigned& mask){
    const bool main=QueryVectorState(chain.mainThreadData,bit,mask);
    const bool back=QueryVectorState(chain.backThreadData,bit+1,mask);return main&&back;
}
IrisQueryGate::Reason QueryPending(PhysicsInterface* physics,unsigned& mask){
    mask=0;bool valid=true;
    valid=QueryChainState(physics->hullsToMake,0,mask)&&valid;
    valid=QueryChainState(physics->hullsToDestroy,2,mask)&&valid;
    valid=QueryChainState(physics->actorsToDestroy,4,mask)&&valid;
    valid=QueryChainState(physics->terrainToLoad,6,mask)&&valid;
    valid=QueryChainState(physics->hullsToChangeGroup,8,mask)&&valid;
    valid=QueryChainState(physics->impulse,10,mask)&&valid;
    valid=QueryChainState(physics->newConstantTracers,12,mask)&&valid;
    valid=QueryChainState(physics->removeConstantTracers,14,mask)&&valid;
    valid=QueryVectorState(physics->doorsToSetup,16,mask)&&valid;
    return IrisQueryGate::PendingReason(mask,!valid);
}
struct QueryGateAudit {
    unsigned source,mask,exceptionCode;IrisQueryGate::Reason why;bool enabled;double begin;
    explicit QueryGateAudit(unsigned value):source(value),mask(0),exceptionCode(0),why(IrisQueryGate::DISABLED),
        enabled(IrisDiagnostics::QueryGateLoggingEnabled()),begin(enabled?IrisDiagnostics::Now():0){}
    ~QueryGateAudit(){if(enabled){const double at=IrisDiagnostics::Now();
        IrisDiagnostics::RecordQueryGate(source,why,mask,exceptionCode,begin>0&&at>=begin?at-begin:0,at);}}
};
IrisQueryGate::Reason QueryContext(GameWorld* w,PhysicsInterface* physics,void* scene){
    if(!w||!w->initialized||w->gameResetting||w->isLoadingFromASaveGame()||w->isPaused()||
        !physics||w->physics!=physics||!scene)return IrisQueryGate::WORLD_INVALID;
    if(physics->nWorld!=scene)return IrisQueryGate::SCENE_CHANGED;
    if(physics->isRunning())return IrisQueryGate::WORKER_BUSY;
    ThreadWannabe* ai=w->AINonRenderThread();
    return ai&&ai->isRunning()?IrisQueryGate::WORKER_BUSY:IrisQueryGate::ALLOW;
}
/* 慢分支单独保留RAII审计；正常查询不为它承担构造/析构或异常清理栈对象。 */
bool RefineQueryAvailable(GameWorld* w,unsigned source,bool* refined){
    QueryGateAudit audit(source);if(!queryGateRefinement)return false;
    PhysicsInterface* physics=w?w->physics:0;void* scene=physics?physics->nWorld:0;
    audit.why=QueryContext(w,physics,scene);if(audit.why!=IrisQueryGate::ALLOW)return false;
    audit.why=QueryPending(physics,audit.mask);if(audit.why!=IrisQueryGate::ALLOW)return false;
    const IrisNative::SceneReadiness ready=IrisNative::InspectSceneReadiness(scene,audit.exceptionCode);
    if(ready!=IrisNative::SCENE_WRITABLE){audit.why=ready==IrisNative::SCENE_NOT_WRITABLE?IrisQueryGate::SDK_NOT_WRITABLE:
        ready==IrisNative::SCENE_STATE_ERROR?IrisQueryGate::SDK_ERROR:IrisQueryGate::SDK_UNAVAILABLE;return false;}
    /* SDK检查后再核验世界/线程/消息，许可仅服务紧随其后的同步查询；不主动刷新原生标志。
       回调只复制稳定身份，不医疗/重入游戏；新分支不复用此前的球结果缓存。 */
    audit.why=QueryContext(w,physics,scene);if(audit.why!=IrisQueryGate::ALLOW)return false;
    audit.why=QueryPending(physics,audit.mask);if(audit.why!=IrisQueryGate::ALLOW)return false;
    if(refined)*refined=true;return true;
}
/* 100快路只有原getter及可选输出初始化；SDK/队列核验和诊断全部留在独立慢分支。 */
inline bool QueryAvailable(GameWorld* w,unsigned source,bool* refined=0){
    if(refined)*refined=false;
    if(w&&w->physics&&w->physics->queuesAreClearMT())return true;
    return RefineQueryAvailable(w,source,refined);
}
bool Contacts(GameWorld* w,const Path& path,IrisNative::Contacts& result,unsigned& budget,float* cylinderLength=0,IrisNative::Contacts* terrain=0,const IrisSector::Volume* sector=0,bool drillSphere=false){
    // 092只观察本次同步接口，子耗时由根栈扣除；不改参数、次数、返回及所有权。
    IrisDiagnostics::InterfaceScope interfaceTiming(IrisDiagnostics::IF_CONTACT_GATE);

    result.count=0;IrisNative::Diagnostic empty={IrisNative::ISSUE_NONE,0,0,0,0,0,{0,0,0},0,0,0};result.diagnostic=empty;
    if(terrain){terrain->count=0;terrain->diagnostic=empty;} // 057两份结果在暂态/失败时均为空，不能沿用上一帧墙。
    // 暂态或预算等待也必须有确定诊断值，不能把栈上未初始化内容记为接触失败。
    /* 100原门通过才可沿用球缓存；精细放行只执行新查询，不消费/填充旧球缓存。 */
    bool refined=false;if(!QueryAvailable(w,IrisQueryGate::SINGLE,&refined)){IrisDiagnostics::Add(IrisDiagnostics::QUERY_BUSY_WAIT);return false;}
    // 081大名单复制可能需要扩容。缓存分配失败只放弃该次缓存，继续真实查询，不传播到游戏回调。
    if(!refined&&path.sphere)for(size_t i=0;i<sphereFacts.size();++i){const SphereFact& f=sphereFacts[i];if(f.radius==path.radius&&f.center==path.from){
        try{result=f.contacts;IrisDiagnostics::Add(IrisDiagnostics::QUERY_CACHE);if(drillSphere)IrisDiagnostics::Add(IrisDiagnostics::DRILL_SPHERE_CACHE);return true;}catch(const std::bad_alloc&){break;}}}
    unsigned required=(path.cylinder||terrain)?2U:1U;if(budget<required){IrisDiagnostics::Add(IrisDiagnostics::QUERY_BUDGET_WAIT);return false;}
    IrisNative::Point p={path.from.x,path.from.y,path.from.z};unsigned calls=0;float reach=0;IrisNative::QueryStatus status;
    const bool audit=IrisDiagnostics::PerformanceEnabled();double begin=audit?IrisDiagnostics::Now():0;
    IrisDiagnostics::InterfaceScope physicalTiming(IrisDiagnostics::IF_PHYSICS);
    if(sector)status=IrisNative::OverlapSector(w->physics->nWorld,*sector,0xffffffffU,result,calls);
    else if(path.sphere)status=IrisNative::OverlapSphere(w->physics->nWorld,p,path.radius,0xffffffffU,result,calls,drillSphere);
    else{Vector3 d=path.to-path.from;IrisNative::Point motion={d.x,d.y,d.z};
        IrisNative::Point to={path.to.x,path.to.y,path.to.z};
        if(path.cylinder)status=IrisNative::CylinderAll(w->physics->nWorld,p,motion,path.radius,0xffffffffU,result,reach,calls);
        else if(terrain)status=IrisNative::ProjectileAll(w->physics->nWorld,p,motion,path.radius,0xffffffffU,result,*terrain,calls);
        else if(path.volume)status=IrisNative::OverlapCapsule(w->physics->nWorld,p,to,path.radius,0xffffffffU,result,calls);
        else status=IrisNative::SweepAll(w->physics->nWorld,p,motion,path.radius,0xffffffffU,result,calls);}
    physicalTiming.Finish();
    ObserveConservativeContacts(result);
    if(sector){IrisDiagnostics::Add(IrisDiagnostics::SECTOR_REQUESTS,calls);IrisDiagnostics::Add(IrisDiagnostics::SECTOR_PLANES,sector->count*calls);
        IrisDiagnostics::Add(IrisDiagnostics::SECTOR_RAW,result.diagnostic.received);IrisDiagnostics::Add(IrisDiagnostics::SECTOR_CONTACTS,result.count);}
    // 098独立通道复用已有起止时钟；它是sphere的子统计，分析时不能重复加进物理总耗时。
    if(audit){double elapsed=std::max(0.0,IrisDiagnostics::Now()-begin);IrisDiagnostics::Record(sector?IrisDiagnostics::SECTOR_QUERY:path.sphere?IrisDiagnostics::SPHERE_QUERY:path.cylinder?IrisDiagnostics::CYLINDER_QUERY:path.volume?IrisDiagnostics::CAPSULE_QUERY:IrisDiagnostics::SWEEP_QUERY,elapsed);if(drillSphere&&IrisDiagnostics::DetailsEnabled())IrisDiagnostics::Record(IrisDiagnostics::DRILL_SPHERE_QUERY,elapsed);}
    if(drillSphere&&IrisDiagnostics::DetailsEnabled()){IrisDiagnostics::Add(IrisDiagnostics::DRILL_SPHERE_REQUESTS,calls);IrisDiagnostics::Add(IrisDiagnostics::DRILL_SPHERE_RAW,result.diagnostic.received);IrisDiagnostics::Add(IrisDiagnostics::DRILL_SPHERE_CONTACTS,result.count);}
    IrisDiagnostics::Add(IrisDiagnostics::QUERY_CALLS,calls);IrisDiagnostics::Add(IrisDiagnostics::QUERY_RAW,result.diagnostic.received);IrisDiagnostics::Add(IrisDiagnostics::QUERY_CONTACTS,result.count);IrisDiagnostics::Add(IrisDiagnostics::QUERY_RECOVERED,result.diagnostic.recoveredInitial);
    // 计数在原生回调返回后提交，回调内不加插件锁、不写日志；命中缓存不重复统计原始工作。
    if(IrisDiagnostics::DetailsEnabled()){IrisDiagnostics::Add(IrisDiagnostics::IDENTITY_COMPARISONS,result.diagnostic.identityComparisons);IrisDiagnostics::Add(IrisDiagnostics::IDENTITY_PROBES,result.diagnostic.identityProbes);
        IrisDiagnostics::Add(IrisDiagnostics::IDENTITY_DUPLICATES,result.diagnostic.identityDuplicates);IrisDiagnostics::Add(IrisDiagnostics::IDENTITY_TABLES,result.diagnostic.identityTables);IrisDiagnostics::Add(IrisDiagnostics::CYLINDER_BUFFER_GROWTH,result.diagnostic.bodyBufferGrowth);
        /* 086仅在同步查询结束后提交纯值；不在PhysX回调拿插件锁，不执行额外旧查询。 */
        IrisDiagnostics::Add(IrisDiagnostics::SWEEP_SHAPE_COMPARISONS,result.diagnostic.sweepShapeComparisons);IrisDiagnostics::Add(IrisDiagnostics::SWEEP_SHAPE_PROBES,result.diagnostic.sweepShapeProbes);
        IrisDiagnostics::Add(IrisDiagnostics::SWEEP_SHAPE_LINEAR_EQUIVALENT,result.diagnostic.sweepShapeLinearEquivalent);IrisDiagnostics::Add(IrisDiagnostics::SWEEP_SHAPE_TABLES,result.diagnostic.sweepShapeTables);IrisDiagnostics::Add(IrisDiagnostics::SWEEP_SHAPE_INDEX_FALLBACKS,result.diagnostic.sweepShapeIndexFallbacks);}
    budget-=std::min(budget,calls);
    if(status==IrisNative::QUERY_COMPLETE){
        // 080只统计实际省掉的第二次调用；预留2次预算的保守入口和64次硬上限保持。
        if(terrain&&calls==1&&terrain->count&&terrain->items[0].fraction==0.f)IrisDiagnostics::Add(IrisDiagnostics::PROJECTILE_WALL_SKIPS);
        // 081缓存是可选副本；分配失败时保留本次真实查询成功结果，不能因此漏掉伤害或重放查询。
        if(!refined&&path.sphere&&!result.diagnostic.skippedIdentity&&!result.diagnostic.skippedGeometry&&!result.diagnostic.skippedCapacity&&!result.diagnostic.skippedInput&&sphereFacts.size()<16){try{SphereFact f;f.center=path.from;f.radius=path.radius;f.contacts=result;sphereFacts.push_back(f);}catch(const std::bad_alloc&){}}
        if(cylinderLength)*cylinderLength=reach;return true;}
    IrisDiagnostics::Add(IrisDiagnostics::QUERY_RETRY);if(status==IrisNative::QUERY_OVERFLOW)IrisDiagnostics::Add(IrisDiagnostics::QUERY_OVERFLOW);
    // 失败整批不消费，事件游标不移动。下一安全窗口重查原路径，绝不永久关闭整个演员/世界查询。
    if(IrisDiagnostics::DetailsEnabled()){std::ostringstream o;o<<"eight_query_retry status="<<status<<" issue="<<IrisNative::IssueReason(result.diagnostic.issue)<<" raw_fraction="<<result.diagnostic.rawFraction<<" fraction_bits="<<result.diagnostic.fractionBits<<" hit_index="<<result.diagnostic.hitIndex<<" from="<<path.from.x<<","<<path.from.y<<","<<path.from.z<<" to="<<path.to.x<<","<<path.to.y<<","<<path.to.z<<" radius="<<path.radius<<" reason="<<IrisNative::AvailabilityReason()<<" consumed=0 automatic_disable=0";Log(o.str());}return false;
}
// 052：所有正式作业均未启用旧wall开关；删除不可达墙体分支，保持原先完整相交名单与enemy门。
void Collect(Job& j,const IrisNative::Contacts& hits){
    IrisDiagnostics::Scope timing(IrisDiagnostics::CONTACT_COLLECT);const bool audit=IrisDiagnostics::CollisionProfileEnabled();
    Character* caster=j.caster.getCharacter();unsigned duplicates=0,checks=0,inserted=0;
    for(unsigned k=0;k<hits.count;++k){hand h=Handle(hits.items[k].object);
        // 087本攻击段已接受的身份原本就留在victims，后续相交不会撤销；不必再解引用/判敌我/重复插入。
        // 不缓存拒绝结果，不跨攻击段；目标后来失效/改关系仍由既有入队后医疗资格门重新拒绝。
        if(j.victims.find(h)!=j.victims.end()){if(audit)++duplicates;continue;}
        Character* victim=h.getCharacter();if(audit)++checks;
        if(DamageTarget(caster,victim,j.move)){j.victims.insert(h);if(audit)++inserted;}
    }
    if(audit){IrisDiagnostics::Add(IrisDiagnostics::COLLECT_CONTACTS,hits.count);IrisDiagnostics::Add(IrisDiagnostics::COLLECT_DUPLICATES,duplicates);
        IrisDiagnostics::Add(IrisDiagnostics::COLLECT_CHECKS,checks);IrisDiagnostics::Add(IrisDiagnostics::COLLECT_INSERTS,inserted);}
}
void QueryWait(Job& j,const Path& path,const IrisNative::Contacts& contacts){
    // 092只观察本次同步接口，子耗时由根栈扣除；不改参数、次数、返回及所有权。
    IrisDiagnostics::InterfaceScope interfaceTiming(IrisDiagnostics::IF_DIAGNOSTICS);

    if(++j.failures==1||j.failures%120==0){std::ostringstream out;out<<"damage_query_wait cast="<<j.cast<<" event="<<j.event<<" move="<<j.move<<" path="<<j.cursor<<" failures="<<j.failures<<" issue="<<IrisNative::IssueReason(contacts.diagnostic.issue)<<" raw_fraction="<<contacts.diagnostic.rawFraction<<" fraction_bits="<<contacts.diagnostic.fractionBits<<" received="<<contacts.diagnostic.received<<" radius="<<path.radius<<" other_jobs_continue=1";Log(out.str());}
}
// 081异常明细只在合批回调和所有SDK访问结束后输出，受既有战斗明细开关控制。
// 首8条、异常码变化且间隔1秒、或持续异常每10秒保留一次；数量在每份长期摘要完整累计。
// 静态纯值只由原有安全Tick互斥区访问；不保存形体地址，不新建线程/锁，不在SDK回调写文件。
void LogCapsuleSkips(const Job& job,unsigned count,const IrisNative::BatchDiagnostic& d){
    if(!IrisDiagnostics::DetailsEnabled()||(!d.skippedIdentity&&!d.skippedGeometry))return;
    static unsigned notices=0,lastIdentity=0,lastGeometry=0;static double lastAt=0;
    const double now=IrisDiagnostics::Now();const bool changed=lastIdentity!=d.identityException||lastGeometry!=d.geometryException;
    if(notices>=8&&now-lastAt<10000&&(!changed||now-lastAt<1000))return;
    ++notices;lastAt=now;lastIdentity=d.identityException;lastGeometry=d.geometryException;
    std::ostringstream out;out<<"capsule_batch_shape_skipped contract=IRIS_CAPSULE_POLICY_081 cast="<<job.cast<<" event="<<job.event<<" move="<<job.move
        <<" path_begin="<<job.cursor<<" paths="<<count<<" candidates="<<d.candidates<<" characters="<<d.characters
        <<" skipped_identity="<<d.skippedIdentity<<" skipped_geometry="<<d.skippedGeometry<<" identity_exception=0x"<<std::hex<<d.identityException
        <<" geometry_exception=0x"<<d.geometryException<<std::dec<<" geometry_zero_code=nonfinite_or_null_or_invalid_bounds action=skip_bad_shape continue_valid=1 notice="<<notices;Log(out.str());
}
bool TryCapsuleBatch(GameWorld* w,Job& job,unsigned& budget,unsigned& used,bool& failed){
    failed=false;
    if(!capsuleBatchEnabled||!job.sectors.empty()||used>=7||budget<2)return false;
    unsigned count=0,limit=std::min(8U-used,budget);IrisNative::CapsuleInput input[IrisNative::CAPSULE_BATCH_CAPACITY];
    while(count<limit&&job.cursor+count<job.paths.size()){
        const Path& path=job.paths[job.cursor+count];if(!path.volume||path.sphere||path.cylinder)break;
        IrisNative::CapsuleInput& p=input[count++];p.from.x=path.from.x;p.from.y=path.from.y;p.from.z=path.from.z;
        p.to.x=path.to.x;p.to.y=path.to.y;p.to.z=path.to.z;p.radius=path.radius;
    }if(count<2)return false;
    /* 100先确认确有可提交的复合胶囊，避免球/单路径先做无效精细检查再走Contacts。
       count构造只读自有路径，实际SDK查询及预算仍在统一许可之后，正常合格批工作量不增加。 */
    if(!QueryAvailable(w,IrisQueryGate::CAPSULE_BATCH))return false;
    // 097每个逻辑胶囊对应最多一次真实SDK overlap；预算按实际调用扣，不再保留手写合批或自动影子重查。
    unsigned calls=0;IrisNative::BatchDiagnostic d;IrisNative::QueryStatus status;
    {IrisDiagnostics::Scope timing(IrisDiagnostics::CAPSULE_BATCH_QUERY);
        status=IrisNative::OverlapCapsules(w->physics->nWorld,input,count,0xffffffffU,capsuleBatchResults,d,calls);}
    budget-=std::min(budget,calls);IrisDiagnostics::Add(IrisDiagnostics::QUERY_CALLS,calls);
    IrisDiagnostics::Add(IrisDiagnostics::BATCH_ATTEMPTS);IrisDiagnostics::Add(IrisDiagnostics::BATCH_CANDIDATES,d.candidates);
    IrisDiagnostics::Add(IrisDiagnostics::BATCH_SKIPPED_IDENTITY,d.skippedIdentity);IrisDiagnostics::Add(IrisDiagnostics::BATCH_SKIPPED_GEOMETRY,d.skippedGeometry);
    LogCapsuleSkips(job,count,d);
    for(unsigned i=0;i<d.completed;++i){const IrisNative::Contacts& values=capsuleBatchResults[i];
        ObserveConservativeContacts(values);Collect(job,values);
        IrisDiagnostics::Add(IrisDiagnostics::QUERY_RAW,values.diagnostic.received);IrisDiagnostics::Add(IrisDiagnostics::QUERY_CONTACTS,values.count);
        if(IrisDiagnostics::DetailsEnabled()){const IrisNative::Diagnostic& a=values.diagnostic;
            IrisDiagnostics::Add(IrisDiagnostics::IDENTITY_COMPARISONS,a.identityComparisons);IrisDiagnostics::Add(IrisDiagnostics::IDENTITY_PROBES,a.identityProbes);
            IrisDiagnostics::Add(IrisDiagnostics::IDENTITY_DUPLICATES,a.identityDuplicates);IrisDiagnostics::Add(IrisDiagnostics::IDENTITY_TABLES,a.identityTables);}
        ++job.cursor;++used;
    }
    if(status!=IrisNative::QUERY_COMPLETE){
        // 只重试失败位置；已成功的前缀游标已前进，不能因后项未就绪而重复查询或重复收费。
        QueryWait(job,job.paths[job.cursor],capsuleBatchResults[d.completed]);failed=true;IrisDiagnostics::Add(IrisDiagnostics::QUERY_RETRY);
    }else{job.failures=0;IrisDiagnostics::Add(IrisDiagnostics::BATCH_SUCCESSES);}
    return true;
}

// 088预取只存稳定cast/event/路径游标及自有结果；不保存Shot/Job引用或引擎裸指针。
// 工作区在原Tick互斥区独占，每次调用只消费当前窗口；水位提前终止的余项直接丢弃，绝不跨帧缓存。
struct RangedTag {unsigned cast,event;size_t cursor;};
struct RangedWorkspace {
    IrisNative::RangedInput inputs[IrisNative::RANGED_BATCH_CAPACITY];
    IrisNative::RangedResult results[IrisNative::RANGED_BATCH_CAPACITY];RangedTag tags[IrisNative::RANGED_BATCH_CAPACITY];
};
RangedWorkspace shotBatchWork,beamBatchWork;
void RangedPath(const Path& p,bool cylinder,IrisNative::RangedInput& input){
    input.from.x=p.from.x;input.from.y=p.from.y;input.from.z=p.from.z;Vector3 motion=p.to-p.from;
    input.motion.x=motion.x;input.motion.y=motion.y;input.motion.z=motion.z;input.radius=p.radius;input.cylinder=cylinder;
}
// 只借本批自有名单，所有别名均指向较早成功项；下批覆盖前已按原顺序消费，不跨窗保存。
const IrisNative::RangedResult& RangedValue(const RangedWorkspace& work,unsigned index){return work.results[work.results[index].source];}
bool RunRangedBatch(GameWorld* w,RangedWorkspace& work,unsigned count,unsigned& budget,bool* allowEmpty=0){
    if(!rangedBatchEnabled||count<2||budget<count*2||!QueryAvailable(w,IrisQueryGate::RANGED_BATCH))return false;
    unsigned calls=0;bool submitted;IrisNative::RangedPolicy policy;
    policy.reuse=rangedQueryReuse;policy.empty=rangedEmptyPruning;policy.shadow=rangedEmptyShadow;
    policy.allowEmpty=allowEmpty?*allowEmpty:true;policy.maxCalls=budget;
    policy.spatial=rangedSpatialPruning;policy.single=rangedSingleProbe;IrisNative::RangedAudit audit;
    // 092实验只替换单段宽相开关；相邻合格批交替，各批仍只执行一个原算法，不重放参考查询。
    // 关闭监视/实验或首项为圆柱、显式shadow时沿原配置；输入次序、射线/扫掠体和命中消费保持。
    unsigned probeArm=2;policy.single=IrisDiagnostics::SelectRangedSingleProbe(policy.single,
        policy.spatial&&policy.empty&&policy.allowEmpty&&!policy.shadow&&!work.inputs[0].cylinder,probeArm);
    // 下一批只共享本次AdvanceEffects的无收益标志，不共享任何几何/名单/引擎指针。
    if(policy.empty&&!policy.allowEmpty&&IrisDiagnostics::CollisionProfileEnabled())IrisDiagnostics::Add(IrisDiagnostics::RANGED_EMPTY_DISABLED);
    // 父通道保持原sweep/cylinder口径；新阶段是其子计时，不能相加当成净CPU。
    {IrisDiagnostics::Scope oldTiming(work.inputs[0].cylinder?IrisDiagnostics::CYLINDER_QUERY:IrisDiagnostics::SWEEP_QUERY);
     IrisDiagnostics::Scope timing(IrisDiagnostics::RANGED_BATCH_QUERY,0,&audit.totalMs);
     submitted=IrisNative::RangedBatch(w->physics->nWorld,work.inputs,count,0xffffffffU,work.results,calls,policy,audit);}
    if(allowEmpty)*allowEmpty=policy.allowEmpty;
    if(!submitted){if(IrisDiagnostics::CollisionProfileEnabled())IrisDiagnostics::Add(IrisDiagnostics::RANGED_BATCH_UNAVAILABLE);return false;} // 保证尚未提交查询，旧路不重复结算。
    budget-=std::min(budget,calls);IrisDiagnostics::Add(IrisDiagnostics::QUERY_CALLS,calls);
    const bool detail=IrisDiagnostics::DetailsEnabled(),profile=IrisDiagnostics::CollisionProfileEnabled();unsigned sweeps=0,cylinders=0,failures=0,rays=0;
    IrisDiagnostics::RangedProbeSample probeSample={0};const bool probeCost=IrisDiagnostics::RangedProbeCostEnabled();
    if(probeCost){probeSample.arm=probeArm;probeSample.items=count;probeSample.totalMs=audit.totalMs;probeSample.raysMs=audit.raysMs;probeSample.bodiesMs=audit.bodiesMs;probeSample.probeMs=audit.probeMs;
        probeSample.commands=calls;probeSample.reuses=audit.reused;probeSample.probes=audit.probeCalls;probeSample.saved=audit.savedSweeps;probeSample.busy=audit.probeBusy;probeSample.unknown=audit.probeUnknown;}
    for(unsigned i=0;i<count;++i){const IrisNative::RangedResult& own=work.results[i];const IrisNative::RangedResult& r=RangedValue(work,i);
        const IrisNative::Diagnostic& d=own.characters.diagnostic; // 别名不重复累计SDK原始报告及索引成本。
        ObserveConservativeContacts(own.characters);
        IrisDiagnostics::Add(IrisDiagnostics::QUERY_RAW,d.received);IrisDiagnostics::Add(IrisDiagnostics::QUERY_CONTACTS,r.characters.count);IrisDiagnostics::Add(IrisDiagnostics::QUERY_RECOVERED,d.recoveredInitial);
        if(r.status!=IrisNative::QUERY_COMPLETE){++failures;IrisDiagnostics::Add(IrisDiagnostics::QUERY_RETRY);if(r.status==IrisNative::QUERY_OVERFLOW)IrisDiagnostics::Add(IrisDiagnostics::QUERY_OVERFLOW);}
        else if(own.source==i&&!own.bodyCalls&&r.terrain.count&&r.terrain.items[0].fraction==0.f)IrisDiagnostics::Add(IrisDiagnostics::PROJECTILE_WALL_SKIPS);
        rays+=own.rayCalls;if(work.inputs[i].cylinder)cylinders+=own.bodyCalls;else sweeps+=own.bodyCalls;
        if(probeCost){const IrisNative::RangedInput& input=work.inputs[i];
            if(input.cylinder)++probeSample.cylinders;else ++probeSample.spheres;
            probeSample.distanceSum+=sqrt(double(input.motion.x)*input.motion.x+double(input.motion.y)*input.motion.y+double(input.motion.z)*input.motion.z);
            probeSample.radiusSum+=input.radius;}
        if(detail){IrisDiagnostics::Add(IrisDiagnostics::IDENTITY_COMPARISONS,d.identityComparisons);IrisDiagnostics::Add(IrisDiagnostics::IDENTITY_PROBES,d.identityProbes);
            IrisDiagnostics::Add(IrisDiagnostics::IDENTITY_DUPLICATES,d.identityDuplicates);IrisDiagnostics::Add(IrisDiagnostics::IDENTITY_TABLES,d.identityTables);IrisDiagnostics::Add(IrisDiagnostics::CYLINDER_BUFFER_GROWTH,d.bodyBufferGrowth);
            IrisDiagnostics::Add(IrisDiagnostics::SWEEP_SHAPE_COMPARISONS,d.sweepShapeComparisons);IrisDiagnostics::Add(IrisDiagnostics::SWEEP_SHAPE_PROBES,d.sweepShapeProbes);
            IrisDiagnostics::Add(IrisDiagnostics::SWEEP_SHAPE_LINEAR_EQUIVALENT,d.sweepShapeLinearEquivalent);IrisDiagnostics::Add(IrisDiagnostics::SWEEP_SHAPE_TABLES,d.sweepShapeTables);IrisDiagnostics::Add(IrisDiagnostics::SWEEP_SHAPE_INDEX_FALLBACKS,d.sweepShapeIndexFallbacks);}
    }
    if(profile){IrisDiagnostics::Add(IrisDiagnostics::RANGED_BATCH_ATTEMPTS);IrisDiagnostics::Add(IrisDiagnostics::RANGED_BATCH_ITEMS,count);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_BATCH_RAYS_COUNT,rays);IrisDiagnostics::Add(IrisDiagnostics::RANGED_BATCH_SWEEPS_COUNT,sweeps);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_BATCH_CYLINDERS_COUNT,cylinders);IrisDiagnostics::Add(IrisDiagnostics::RANGED_BATCH_FAILURES,failures);
        // 单批只汇总纯值，物理回调内不取诊断锁/不写日志。
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_EXACT_REUSES,audit.reused);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_REUSE_FAILURES,audit.reuseFailed);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_EMPTY_PROBES,audit.probeCalls);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_EMPTY_CANDIDATES,audit.probeCandidates);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_EMPTY_CHARACTERS,audit.probeCharacters);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_EMPTY_UNKNOWN,audit.probeUnknown);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_EMPTY_PATHS,audit.emptyPaths);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_EMPTY_SAVED,audit.savedSweeps);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_EMPTY_BUSY,audit.probeBusy);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_EMPTY_HEADROOM,audit.probeHeadroom);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_EMPTY_SPARSE,audit.probeSparse);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_EMPTY_SMALL,audit.probeSmall);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_EMPTY_INVALID,audit.probeInvalid);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_EMPTY_SHADOWS,audit.shadowChecks);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_EMPTY_MISMATCHES,audit.shadowMismatches);
        // 090所有分组/命令纯值返回后才汇总，SDK回调里没有新锁/文件写入。
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_SPATIAL_BATCHES,audit.spatialBatches);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_SPATIAL_GROUPS,audit.spatialGroups);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_SPATIAL_MERGES,audit.spatialMerges);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_SPATIAL_PAIRS,audit.spatialPairs);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_SPATIAL_SINGLES,audit.spatialSingles);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_SPATIAL_MULTIS,audit.spatialMultis);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_SPATIAL_COVERED,audit.spatialCovered);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_SPATIAL_SKIPPED_SINGLES,audit.spatialSkippedSingles);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_SPATIAL_EMPTY_SINGLES,audit.spatialEmptySingles);
        IrisDiagnostics::Add(IrisDiagnostics::RANGED_SPATIAL_EMPTY_MULTIS,audit.spatialEmptyMultis);
        static unsigned lastException=0;static bool mismatchNotice=false;
        if(audit.probeException&&audit.probeException!=lastException){lastException=audit.probeException;std::ostringstream out;
            out<<"ranged_empty_identity_unreadable exception=0x"<<std::hex<<audit.probeException<<std::dec<<" action=original_sweep no_empty_result=1";Log(out.str());}
        if(audit.shadowMismatches&&!mismatchNotice){mismatchNotice=true;Log("ranged_empty_shadow_mismatch action=consume_original_sweep empty_pruning_suspended_this_update=1 see_summary_counters=1");}
    }
    if(probeCost){probeSample.failures=failures;IrisDiagnostics::RecordRangedProbeCost(probeSample);}
    return true;
}
// 只预取队首连续、各剩一条光炮路径的作业；跨攻击段的名单/资格/医疗入队绝不合并。
// 一般作业和多路径作业仍按旧每作业8条轮转。最多消耗当前预算，不为凑批等待下一帧。
unsigned PrepareBeamBatch(GameWorld* w,size_t visits,unsigned& budget){
    if(!rangedBatchEnabled||budget<4||visits<2)return 0;unsigned count=0,limit=std::min(IrisNative::RANGED_BATCH_CAPACITY,budget/2);
    for(std::list<Job>::const_iterator j=jobs.begin();j!=jobs.end()&&count<limit&&count<visits;++j){
        if(j->cursor+1!=j->paths.size()||!j->paths[j->cursor].cylinder)break;
        RangedTag& tag=beamBatchWork.tags[count];tag.cast=j->cast;tag.event=j->event;tag.cursor=j->cursor;
        RangedPath(j->paths[j->cursor],true,beamBatchWork.inputs[count]);++count;
    }return RunRangedBatch(w,beamBatchWork,count,budget)?count:0;
}

void ResolveJobs(GameWorld* w,unsigned& budget){
    IrisDiagnostics::Scope queryJobsTiming(IrisDiagnostics::QUERY_JOBS);
    // 一条坏路径只能等待自己的事件，不能卡住整个FIFO。每轮最多访问本轮已有请求各一次，
    // 每请求最多8条路径，仍受全帧64次预算与2048医疗入队软水位约束；失败批次不消费/不删掉。
    size_t visits=jobs.size();unsigned ready=0,next=0;
    while(visits--&&!jobs.empty()&&(budget||next<ready)&&hurts.size()<2048){
        if(next==ready){next=0;ready=PrepareBeamBatch(w,visits+1,budget);}
        Job& j=jobs.front();unsigned used=0;
        while(j.cursor<j.paths.size()&&(budget||next<ready)&&used<8){
            bool batchFailed=false;if(TryCapsuleBatch(w,j,budget,used,batchFailed)){if(batchFailed)break;continue;}
            IrisNative::Contacts local;float length=0;const Path& path=j.paths[j.cursor];const IrisNative::Contacts* hitValues=&local;bool complete;
            // 已提交项即使刚好用完预算也必须消费；失败只保留自己的游标，不能重复提交同项。
            if(next<ready){const RangedTag& tag=beamBatchWork.tags[next];
                if(tag.cast!=j.cast||tag.event!=j.event||tag.cursor!=j.cursor){if(IrisDiagnostics::CollisionProfileEnabled())IrisDiagnostics::Add(IrisDiagnostics::RANGED_BATCH_UNUSED,ready-next);next=ready;}
            }
            if(next<ready){const IrisNative::RangedResult& r=RangedValue(beamBatchWork,next++);hitValues=&r.characters;length=r.length;complete=r.status==IrisNative::QUERY_COMPLETE;}
            else{if(budget<(path.cylinder?2U:1U)){IrisDiagnostics::Add(IrisDiagnostics::QUERY_BUDGET_WAIT);break;}
                complete=Contacts(w,path,local,budget,&length,0,j.sectors.empty()?0:&j.sectors[j.cursor],j.move==3&&j.event<11&&path.sphere);}
            const IrisNative::Contacts& contacts=*hitValues;
            if(!complete){QueryWait(j,path,contacts);break;}
            j.failures=0;Collect(j,contacts);
            // 097真实返回后才输出扇形样本；查询等待和角色去重分开，关闭明细不读此处QPC。
            if(!j.sectors.empty()&&IrisDiagnostics::DetailsEnabled()){
                static unsigned notices=0;static double logged=0;const double at=IrisDiagnostics::Now();
                if(notices<8||at-logged>=10000){++notices;logged=at;const IrisSector::Volume& v=j.sectors[j.cursor];std::ostringstream out;
                    out<<"sector_native_query contract=IRIS_NATIVE_SECTOR_097 cast="<<j.cast<<" event="<<j.event<<" piece="<<j.cursor<<" pieces="<<j.paths.size()
                        <<" first_degrees="<<v.first*180/IrisSector::PI<<" last_degrees="<<v.last*180/IrisSector::PI<<" planes="<<v.count
                        <<" raw="<<contacts.diagnostic.received<<" unique="<<contacts.count<<" eligible_so_far="<<j.victims.size()
                        <<" job_age_ms="<<(j.createdAt>0?std::max(0.0,at-j.createdAt):-1)<<" native_cull_only=1 notice="<<notices;Log(out.str());}
            }
            // 077在原查询返回后按既有明细开关留证；length是实际裁短长度，不能用起手10000冒充。
            if(path.cylinder&&IrisDiagnostics::DetailsEnabled()){const IrisNative::TerrainInfo& t=contacts.diagnostic.terrain;
                std::ostringstream out;out<<"beam_collision cast="<<j.cast<<" event="<<j.event<<" move="<<j.move<<" radius="<<path.radius<<" actual_length="<<length
                    <<" requested_length="<<(path.to-path.from).length()<<" terrain_mask=0x"<<std::hex<<t.groups<<std::dec<<" terrain_hit="<<t.hit<<" terrain_distance="<<t.distance
                    <<" terrain_metadata="<<t.metadata<<" terrain_shape_type="<<t.shapeType<<" terrain_group="<<t.shapeGroup<<" terrain_trigger="<<t.trigger;Log(out.str());}
            if(path.cylinder)for(size_t n=0;n<residues.size();++n)if(residues[n].key=="beam"&&residues[n].cast==j.cast){Residue& r=residues[n];r.pos=path.from;r.direction=path.to-path.from;r.direction.normalise();r.length=length;}
            ++j.cursor;++used;
        }
        IrisDiagnostics::InterfaceScope rotateTiming(IrisDiagnostics::IF_JOB_ROTATE);
        // 081结果不再限256：单批本身超过2048时，旧“必须整批装入”门会永久轮转。
        // 2048仍限制有积压时继续接收；空队列允许一次完整大批入队，再由原FIFO及INI时间/笔数额度分帧。
        // 不截断名单、不拆独立攻击段、不越过已有伤害，普通<=2048的入队条件逐值不变。
        if(j.cursor<j.paths.size()||(!hurts.empty()&&hurts.size()+j.victims.size()>2048)){jobs.splice(jobs.end(),jobs,jobs.begin());IrisDiagnostics::Add(IrisDiagnostics::JOB_ROTATIONS);continue;}
        // 作业等待只记一次，不按敌人数重复放大；医疗等待从真正入队另起算。
        if(IrisDiagnostics::DetailsEnabled())IrisDiagnostics::RecordWait(true,j.createdAt,j.waits,IrisDiagnostics::Now());
        unsigned accepted=0;StrikeKey key(j.cast,j.event);
        {IrisDiagnostics::Scope timing(IrisDiagnostics::DAMAGE_ENQUEUE); // 087只分开入队开销；逐目标身份/queuedAt/顺序与FIFO保持。
        for(std::set<hand>::const_iterator h=j.victims.begin();h!=j.victims.end();++h){
            if(j.blade&&!bladeVictims[key].insert(*h).second)continue;
            Hurt r;r.caster=j.caster;r.victim=*h;r.move=j.move;r.cast=j.cast;r.event=j.event;r.generation=epoch;r.mult=j.mult;r.direct=j.haveDirect&&Same(*h,j.directVictim);r.queuedAt=IrisDiagnostics::Now();IrisDiagnostics::SnapshotWaits(r.queuedAt,r.waits);hurts.push_back(r);IrisDiagnostics::Add(IrisDiagnostics::DAMAGE_QUEUED);++damageStats[key].pending;++accepted;
        }}
        if(!j.blade||accepted){std::ostringstream out;out<<"damage_query_complete cast="<<j.cast<<" event="<<j.event<<" move="<<j.move<<" paths="<<j.paths.size()<<" enemies="<<j.victims.size()<<" queued="<<accepted<<" blade_window_dedup="<<j.blade<<" eligible_targets="<<j.victims.size()<<" target_policy=native_melee_four_checks direct_contact_seed="<<j.haveDirect<<" direct="<<(j.haveDirect?j.directVictim.index:0)<<":"<<(j.haveDirect?j.directVictim.serial:0);Log(out.str());}
        jobs.pop_front();
    }
    // 水位/安全边界停止时，未消费预取项不跨窗保留；已收费查询如实记入unused供压测核查。
    if(next<ready)if(IrisDiagnostics::CollisionProfileEnabled())IrisDiagnostics::Add(IrisDiagnostics::RANGED_BATCH_UNUSED,ready-next);
}
void CollectBladeLedgers(){
    // 092只观察本次同步接口，子耗时由根栈扣除；不改参数、次数、返回及所有权。
    IrisDiagnostics::InterfaceScope interfaceTiming(IrisDiagnostics::IF_LEDGER);

    for(std::map<StrikeKey,std::set<hand> >::iterator k=bladeVictims.begin();k!=bladeVictims.end();){bool live=false;
        for(std::map<hand,Actor>::const_iterator a=actors.begin();a!=actors.end();++a)if(a->second.active&&a->second.id==k->first.first)live=true;
        for(std::list<Job>::const_iterator j=jobs.begin();j!=jobs.end()&&!live;++j)if(j->cast==k->first.first)live=true;
        for(size_t n=0;n<hurts.size()&&!live;++n)if(hurts[n].cast==k->first.first)live=true;
        if(live)++k;else bladeVictims.erase(k++);
    }
}

bool Blast(const hand& caster,unsigned cast,unsigned event,unsigned move,const Vector3& p,float radius,float mult,float rate,bool shock=false,const Quaternion& facing=Quaternion::IDENTITY,const hand* direct=0){
    // 092只观察本次同步接口，子耗时由根栈扣除；不改参数、次数、返回及所有权。
    IrisDiagnostics::InterfaceScope interfaceTiming(IrisDiagnostics::IF_BLAST);

    // 原火浪有前向结构：仅快照本次演员朝向，收招/读档清理沿既有后效所有权；不追踪或修改角色。
    // 041翻滚使用独立roll_blast显示资产，防止范围校准影响全力爆发；物理球仍只用原radius。
    // 068：用户要求独立爆炸统一游戏秒，包括翻滚/终结/全力/火神命中/脉冲；不能再乘持有者攻速。
    // 地震shock仍与连续击打同步，电脉electro_area在其原入口保持攻速；光炮/弹体/附件不走此分支。
    // 只改Residue可视年龄；起爆时点、命中队列、原球心/半径与倍率不改，不新增线程或共享状态写入。
    if(jobs.size()>=256)return false;Residue r;r.caster=caster;r.pos=p;r.radius=radius;r.orientation=(move==0||move==3||move==4)?facing:Quaternion::IDENTITY;r.rate=shock?rate:1.f;r.key=shock?"shock":move==0?"roll_blast":move==4?"full_blast":move==3?"drill_blast":move==6?"pulse_blast":"blast";r.life=(shock||move==0||move==3||move==4||move==6)?assets[r.key].duration:1.1f;r.life=VisualLifetime(r.key,r.life);if(!Borrow(r.visual,r.key))return false;
    residues.push_back(r);Job j;j.caster=caster;j.cast=cast;j.event=event;j.move=move;j.mult=mult;j.paths.push_back(Path(p,p,radius,true));
    // 已成功的扫掠接触是独立物理证据。只复制稳定身份到本事件，不能让随后球查询漏掉直接受击者。
    // 与范围名单共用set去重；本次资格和最终医疗资格仍重新核对，绝不重复扣血或保存NxShape指针。
    if(direct){Character* c=caster.getCharacter();Character* v=direct->getCharacter();
        if(DamageTarget(c,v,move)){j.haveDirect=true;j.directVictim=*direct;j.victims.insert(*direct);}}
    PushJob(j);return true;
}
Matrix4 Between(const Matrix4& from,const Matrix4& to,float t){
    Vector3 p0,s0,p1,s1;Quaternion q0,q1;from.decomposition(p0,s0,q0);to.decomposition(p1,s1,q1);
    return Pose(p0+(p1-p0)*t,Quaternion::Slerp(t,q0,q1,true),s0+(s1-s0)*t);
}
bool Swing(Job& j,const Matrix4& baseNow,const Matrix4& baseBefore,const Vector3& origin,float length,float radius,
           float floorY,IrisSector::Progress& progress,float begin,float end,float frameBegin,float frameEnd,unsigned sex){
    IrisDiagnostics::Scope timing(IrisDiagnostics::PATH_BUILD);
    const Vector3 localTip(1.807138657f,0,8.534358047f+length);
    Matrix4 pose=Between(baseBefore,baseNow,(begin-frameBegin)/(frameEnd-frameBegin))*BladePoseAt(sex,begin);
    Vector3 root=Muzzle(pose)+origin,tip=pose*localTip+origin;
    if(!Finite(root)||!Finite(tip))return false;
    if(!progress.ready)progress.Begin(root.x,root.z,atan2(double(tip.z-root.z),double(tip.x-root.x)));
    const double first=progress.front;double reach=0,bottom=floorY,top=floorY;
    const std::vector<BladePose>& track=bladePoses[sex];
    unsigned key=std::min(unsigned(track.size()-1),unsigned(std::max(0.f,begin/moves[4].seconds*float(track.size()-1)))+1);
    while(key<track.size()&&track[key].time<=begin)++key;
    // 按当前已经经过的动画时间访问同包轨道关键帧，而不是对整段武器首尾姿态走最短旋转。
    // 快扫即使首尾相同，中间整圈仍会被解开；慢扫只访问[begin,end]，从不预查未来关键帧。
    // 中间姿态只构造平面数据，不查询角色。查询数只由新增角度/90度上限决定。
    float clip=begin;
    for(;;){
        pose=Between(baseBefore,baseNow,(clip-frameBegin)/(frameEnd-frameBegin))*BladePoseAt(sex,clip);
        const Vector3 a=Muzzle(pose)+origin,b=pose*localTip+origin;
        const Vector3 sx(pose[0][0],pose[1][0],pose[2][0]),sy(pose[0][1],pose[1][1],pose[2][1]);
        const double thick=radius*std::max(sx.length(),sy.length());
        if(!Finite(a)||!Finite(b)||!IrisSector::Finite(thick))return false;
        const double dx=double(b.x)-progress.x,dz=double(b.z)-progress.z;
        reach=std::max(reach,sqrt(dx*dx+dz*dz)+thick);
        bottom=std::min(bottom,double(std::min(a.y,b.y))-thick);top=std::max(top,double(std::max(a.y,b.y))+thick);
        if(dx*dx+dz*dz>1e-12)progress.Observe(atan2(dz,dx));
        if(clip>=end)break;
        clip=key<track.size()&&track[key].time<end?track[key++].time:end;
    }
    const double last=progress.Next();if(first==last)return true;
    const unsigned count=IrisSector::Parts(first,last);j.paths.reserve(count);j.sectors.reserve(count);double edge=first;
    for(unsigned i=0;i<count;++i){const double next=i+1==count?last:first+(last-first)*double(i+1)/count;IrisSector::Volume volume={0};
        if(!IrisSector::Build(progress.x,progress.z,edge,next,reach,bottom,top,volume))return false;
        j.sectors.push_back(volume);j.paths.push_back(Path(root,tip,float(reach)));edge=next;
    }progress.front=last;
    if(IrisDiagnostics::CollisionProfileEnabled()){IrisDiagnostics::Add(IrisDiagnostics::PATHS_BUILT,count);IrisDiagnostics::Add(IrisDiagnostics::SECTOR_VOLUMES_BUILT,count);}
    if(IrisDiagnostics::DetailsEnabled()){
        static unsigned notices=0;static double logged=0;const double at=IrisDiagnostics::Now();
        if(notices<8||at-logged>=10000){++notices;logged=at;std::ostringstream out;
            out<<"sector_path contract=IRIS_NATIVE_SECTOR_097 cast="<<j.cast<<" event="<<j.event<<" clip_begin="<<begin<<" clip_end="<<end
                <<" first_degrees="<<first*180/IrisSector::PI<<" last_degrees="<<last*180/IrisSector::PI<<" pieces="<<count
                <<" max_piece_degrees="<<fabs(last-first)*180/IrisSector::PI/count<<" radius="<<reach<<" bottom="<<bottom<<" top="<<top
                <<" incremental=1 angular_overlap=boundary_only source_body_curve=1 target=AABB native_cull=1 extra_hits=accepted notice="<<notices;Log(out.str());}
    }return true;
}
bool TraceBladeWindows(const hand& owner,Actor& a,const Matrix4& weapon,float t){
    if(a.move!=4||t<=a.last)return true;
    unsigned needed=0;for(unsigned n=0;n<2;++n)if(std::max(a.last,bladeWindows[n].begin)<std::min(t,bladeWindows[n].end))++needed;
    if(!needed)return true;if(jobs.size()+needed>256)return false;
    const unsigned sex=a.bladeFemale?1U:0U;
    // 源姿态逆矩阵只用于提取本帧/上帧角色锚点；不移动角色或武器，也不改射击位置。
    // 场景原点仍由origin加回，跨帧只有自有值；完整源轨道解决低帧率/高攻速的转圈混叠。
    const Matrix4 baseNow=weapon*BladePoseAt(sex,t).inverseAffine();
    Matrix4 previous=weapon;
    if(a.havePose){previous=a.previous;
        // 浮动原点改变时，把上帧自有矩阵换到当前渲染原点后再求锚点；世界扇形圆心始终不变。
        const Vector3 shift=a.bladePreviousOrigin-a.origin;previous[0][3]+=shift.x;previous[1][3]+=shift.y;previous[2][3]+=shift.z;
    }
    const Matrix4 baseBefore=a.havePose?previous*BladePoseAt(sex,a.last).inverseAffine():baseNow;
    std::list<Job> staged;IrisSector::Progress progress[2]={a.bladeProgress[0],a.bladeProgress[1]};
    for(unsigned n=0;n<2;++n){float lo=std::max(a.last,bladeWindows[n].begin),hi=std::min(t,bladeWindows[n].end);if(lo>=hi)continue;
        Job j;j.caster=owner;j.cast=a.id;j.event=n;j.move=4;j.mult=moves[4].events[n].mult;j.blade=true;
        if(!Swing(j,baseNow,baseBefore,a.origin,FULL_BURST_REACH,moves[4].events[n].radius,a.ground.y,progress[n],lo,hi,a.last,t,sex)){
            // 坏姿态仅跳过本段并计数，不整批重算；正常数据不走此分支，容量等待仍留在上方独立处理。
            progress[n]=a.bladeProgress[n];IrisDiagnostics::Add(IrisDiagnostics::APPROX_SKIP_INPUT);
            if(IrisDiagnostics::DetailsEnabled()){
                static unsigned notices=0;static double logged=0;const double at=IrisDiagnostics::Now();
                if(notices<8||at-logged>=10000){++notices;logged=at;std::ostringstream out;out<<"sector_pose_skipped cast="<<a.id<<" event="<<n<<" clip_begin="<<lo<<" clip_end="<<hi<<" action=skip_interval requery=0 notice="<<notices;Log(out.str());}
            }continue;
        }
        if(!j.paths.empty()){staged.push_back(Job());staged.back().Swap(j);}
    }
    const unsigned added=unsigned(staged.size());jobs.splice(jobs.end(),staged);
    a.bladeProgress[0]=progress[0];a.bladeProgress[1]=progress[1];IrisDiagnostics::Add(IrisDiagnostics::JOB_TRANSFERS,added);return true;
}

Vector3 WingCenter(float clipTime,const Matrix4& weapon,const Vector3& origin){
    if(wingCenters.size()<2)throw std::runtime_error("wing center unavailable");
    float x=std::max(0.f,std::min(1.f,(clipTime-wingCenterBegin)/(wingCenterEnd-wingCenterBegin)))*float(wingCenters.size()-1);
    unsigned lo=unsigned(x),hi=std::min(unsigned(wingCenters.size()-1),lo+1);float u=x-lo;
    Vector3 p=weapon*(wingCenters[lo]*(1-u)+wingCenters[hi]*u)+origin;
    if(!Finite(p))throw std::runtime_error("wing center world nonfinite");return p;
}
// 098每个伤害段独立取球位置；只在当前帧两份已知姿态之间插值，不重放历史PhysX场景。
// 完整球包裹实际绘制的钻头和旋转外环；沿用Visual::Draw的分解/缩放语义，异常只跳过本事件。
bool DrillSphereFrame(const Actor& a,const Matrix4& weapon,float eventTime,float observedTime,Vector3& center,float& radius,bool& interpolated){
    Matrix4 hitWeapon=weapon;interpolated=false;
    if(a.havePose&&observedTime>a.last&&eventTime>=a.last&&eventTime<observedTime){
        Matrix4 previous=a.previous;Vector3 shift=a.drillPreviousOrigin-a.origin;
        previous[0][3]+=shift.x;previous[1][3]+=shift.y;previous[2][3]+=shift.z;
        hitWeapon=Between(previous,weapon,(eventTime-a.last)/(observedTime-a.last));interpolated=true;
    }
    // 前11段发生时钻头已经完全伸出；旋转角与ShowParts同源。轴上球心不因自转偏移。
    const float spin=std::max(0.f,eventTime-1.633267999f)*15.f*6.283185307f/4.125f;
    Matrix4 pose=Relative(hitWeapon,Vector3(1.807138657f,0,8.534358047f),Quaternion(Ogre::Radian(spin),Vector3::UNIT_Z),Vector3::UNIT_SCALE);
    Vector3 p,scale;Quaternion q;pose.decomposition(p,scale,q);
    if(!Finite(p)||!Finite(scale))return false;
    center=p+q*Vector3(0,0,scale.z*DRILL_SPHERE_CENTER_Z)+a.origin;
    const float largest=std::max(fabsf(scale.x),std::max(fabsf(scale.y),fabsf(scale.z)));
    // 非均匀比例使用球的最大轴伸缩界；再留有限float舍入余量，不按前进距离扩大半径。
    radius=DRILL_SPHERE_RADIUS*largest;
    const float magnitude=std::max(1.f,std::max(radius,std::max(fabsf(center.x),std::max(fabsf(center.y),fabsf(center.z)))));
    radius+=magnitude*(16*FLT_EPSILON);
    return Finite(center)&&Finite(radius)&&largest>0&&radius>0;
}
bool Emit(Character* c,const hand& key,Actor& a,const Event& e,const Matrix4& weapon,float clipTime){
    // 092只观察本次同步接口，子耗时由根栈扣除；不改参数、次数、返回及所有权。
    IrisDiagnostics::InterfaceScope interfaceTiming(IrisDiagnostics::IF_EMIT);

    if(e.kind==5)return true; // 光刃由源有效区间消费者持续检测，不能再额外HitFrame扣血。
    if(jobs.size()>=256)return false;Vector3 muzzle=Muzzle(weapon)+a.origin;
    // 三远程保留当帧附件炮口；弹体按实际速度取原生getAimPos，光炮取同源即时身体点，组成纯值快照。
    // 原生许可仍是整套动作的起手门；此处不重调射击检查，不解决许可到发射之间的受阻走位问题。
    const bool nativeRanged=RangedMove(a.move);IrisRanged::AimFrame rangedAim;AimEvidence nativeEvidence;
    if(nativeRanged){
        if(!IrisRanged::CaptureAim(c,muzzle,rangedAim,ProjectileSpeed(a.move),a.move==7))return false;muzzle=rangedAim.muzzle;
        const float expected=ProjectileSpeed(a.move);
        if(!rangedAim.instant&&(!Finite(expected)||fabsf(rangedAim.effectiveSpeed-expected)>std::max(.001f,expected*.00001f)))return false;
        nativeEvidence.target=rangedAim.target;nativeEvidence.raw=rangedAim.point;nativeEvidence.source=rangedAim.source;
        Character* target=rangedAim.target.getCharacter();if(target&&target->isValid()&&!target->isDestroyed())nativeEvidence.root=target->getPosition();
    }
    // 058：每次IrisBeam消费当前原生锤枪轴；后效只保留成功出手时的值快照，不追踪敌人。
    // 独立四段球内接触、原R25/前20及enemy/医疗安全窗口保持，光束不追加伤害。
    if(e.kind==9){CannonFrame frame;if(!ElectroFrame(weapon,a.origin,c->getPosition(),e.radius,frame))return false;
        Job j;j.caster=key;j.cast=a.id;j.event=a.next;j.move=a.move;j.mult=e.mult;Vector3 center=frame.center;
        Residue r;r.cast=a.id;r.caster=key;r.pos=center;r.orientation=frame.orientation;r.radius=e.radius;r.rate=a.rate;r.key="electro_area";r.life=assets[r.key].duration;
        if(!Borrow(r.visual,r.key))return false;residues.push_back(r);
        j.paths.push_back(Path(center,center,e.radius,true));PushJob(j);
        // 明细开启时每次出手留证；不做额外目标查询或逐帧重复记录。
        if(IrisDiagnostics::DetailsEnabled()){std::ostringstream out;out<<"electro_muzzle_axis cast="<<a.id<<" event="<<a.next<<" muzzle="<<frame.muzzle.x<<","<<frame.muzzle.y<<","<<frame.muzzle.z<<" axis="<<frame.axis.x<<","<<frame.axis.y<<","<<frame.axis.z<<" center="<<center.x<<","<<center.y<<","<<center.z<<" radius="<<e.radius<<" beam_reach="<<frame.reach<<" native_aim=1 shared_barrel_axis=1";Log(out.str());}return true;}
    if(e.kind==0||e.kind==3||e.kind==8){
        Job j;j.caster=key;j.cast=a.id;j.event=a.next;j.move=a.move;j.mult=e.mult;
        if(e.kind==3){
            // 098每段只生成一个球，完整包含钻头+外环；11个cast/event仍独立去重和结算。
            // 球心取本段姿态，不能缓存第一段位置；跨过多个到期点时分别插值，仍是离散事件而非持续窗口。
            Vector3 center;float radius=0;bool interpolated=false;
            if(!DrillSphereFrame(a,weapon,e.time,clipTime,center,radius,interpolated)){
                IrisDiagnostics::Add(IrisDiagnostics::APPROX_SKIP_INPUT);
                if(IrisDiagnostics::DetailsEnabled()){static unsigned failures=0;static double lastFailure=0;const double now=IrisDiagnostics::Now();
                    if(failures<8||now-lastFailure>=10000){++failures;lastFailure=now;std::ostringstream out;out<<"drill_sphere_invalid cast="<<a.id<<" event="<<a.next<<" source_time="<<e.time<<" observed_time="<<clipTime<<" action=skip_event requery=0 notice="<<failures;Log(out.str());}}
                return true;
            }
            j.paths.push_back(Path(center,center,radius,true));
            if(IrisDiagnostics::DetailsEnabled()){
                static unsigned notices=0;static double logged=0;const double now=IrisDiagnostics::Now();
                if(notices<8||now-logged>=10000){++notices;logged=now;std::ostringstream out;out<<"drill_sphere_emit contract="<<DRILL_SPHERE_CONTRACT<<" cast="<<a.id<<" event="<<a.next<<" source_time="<<e.time<<" observed_time="<<clipTime<<" center="<<center.x<<","<<center.y<<","<<center.z<<" radius="<<radius<<" interpolated="<<interpolated<<" native_queries=1 independent_event=1 notice="<<notices;Log(out.str());}
            }
        }else if(e.kind==8){
            // 061：光炮消费同源身体点（即时无提前量）；实际枪口/可视方向/角色柱体共用快照。
            AimEvidence aim=nativeEvidence;Vector3 target=rangedAim.point,d=rangedAim.direction;
            const float reach=moves[a.move].technique->initialDistance;j.paths.push_back(Path(muzzle,muzzle+d*reach,e.radius,false,true));
            if(IrisDiagnostics::DetailsEnabled()){std::ostringstream out;out<<"drive_barrel_contract="<<DRIVE_REBUILD_CONTRACT<<" cast="<<a.id<<" event="<<a.next<<" muzzle="<<muzzle.x<<","<<muzzle.y<<","<<muzzle.z<<" axis="<<d.x<<","<<d.y<<","<<d.z<<" radius="<<e.radius<<" length="<<reach<<" aim_mode=native_body_instant target="<<aim.target.index<<":"<<aim.target.serial<<" aim="<<target.x<<","<<target.y<<","<<target.z<<" aim_source="<<aim.source<<" aim_frame="<<rangedAim.sequence<<" origin_offset_changed=0 same_barrel_axis=0 terrain=center_ray character=flat_cylinder";Log(out.str());}
            // 四次原生伤害脉冲各自独立；同一cast只有一份连续洪流可视，不能四层重复叠亮或每次重置UV。
            Residue* beam=0;for(size_t n=0;n<residues.size();++n)if(residues[n].key=="beam"&&residues[n].cast==a.id){beam=&residues[n];break;}
            if(beam){/* 保留上一成功的柱体快照；新健康脉冲查询完成后统一更新。 */}
            else{Residue r;r.cast=a.id;r.caster=key;r.pos=muzzle;r.direction=d;r.radius=e.radius;r.life=assets["beam"].duration;r.rate=a.rate;r.key="beam";
                if(!Borrow(r.visual,r.key))return false;residues.push_back(r);}
        }else if(e.kind==0){
            // 实体武器走源正常模型的八段代理；并发的特效伤害是其他独立事件，不能从枪口虚构更长实体。
            Vector3 sx(weapon[0][0],weapon[1][0],weapon[2][0]),sy(weapon[0][1],weapon[1][1],weapon[2][1]);float radial=std::max(sx.length(),sy.length());
            for(unsigned n=0;n<8;++n){const WeaponCapsule& c=weaponCapsules[n];Vector3 x=weapon*Vector3(c.x,c.y,c.a)+a.origin,y=weapon*Vector3(c.x,c.y,c.b)+a.origin;float radius=c.r*radial;j.paths.push_back(Path(x,y,radius,false,false,true));
                if(a.havePose){Vector3 old=a.previous*Vector3(c.x,c.y,(c.a+c.b)*.5f)+a.origin,now=weapon*Vector3(c.x,c.y,(c.a+c.b)*.5f)+a.origin;if((now-old).squaredLength()>.000001f)j.paths.push_back(Path(old,now,radius,false,false,true));}}
        } // 光刃由TraceBladeWindows独立消费，不能残留不可达的旧单帧Swing分支。
        PushJob(j);return true;
    }
    // 用户指定终结无弹道：在当前张开两翼的中点立即引爆，伤害与蓝/火后效共用同一世界坐标快照。
    // 成功只推进一次事件；不能再进入Shot队列，目标/演员随后移动也不会把球心拖走。
    if(a.move==3&&e.kind==4){Vector3 center=WingCenter(clipTime,weapon,a.origin);
        if(!Blast(key,a.id,a.next,a.move,center,e.radius,e.mult,a.rate,false,c->getOrientation()))return false;
        if(IrisDiagnostics::DetailsEnabled()){std::ostringstream out;out<<"drill_finisher_detonate cast="<<a.id<<" event="<<a.next<<" center="<<center.x<<","<<center.y<<","<<center.z<<" radius="<<e.radius<<" source=wing_midpoint instant=1 projectile=0 visual_and_damage_center_shared=1";Log(out.str());}return true;}
    // 040：第三刀从持续刃线改为一次球形爆炸；球心是该刀当前枪口，和前两刀的伸距起点一致。
    // 事件序号仍为2，沿既有一次消费/原生医疗/敌我门，不再叠加第三刀Swing。
    if(e.kind==2)return Blast(key,a.id,a.next,a.move,a.move==4?muzzle:c->getPosition(),e.radius,e.mult,a.rate,a.move!=4,a.move==4?c->getOrientation():Quaternion::IDENTITY);
    // 090移除活动弹体64门；vector按需增长，不因人为弹数上限延后本攻击段的发射。
    Shot s;s.caster=key;s.cast=a.id;s.event=a.next;s.move=a.move;s.mult=e.mult;s.radius=e.radius;
    // 只有火神弹按需求“弹体半径=爆炸半径”；其他炮弹的碰撞小于爆炸范围，不能出生即和地面重叠。
    // 火神与脉冲均为R4.5弹体；脉冲独立爆炸R36，装饰环仍不进入碰撞。
    s.collisionRadius=e.kind==6?e.radius:e.kind==7?4.5f:.7f;s.rate=a.rate;s.pos=muzzle;
    AimEvidence aim;if(e.kind==1){s.target=a.ground;aim.source="intentional_ground_snapshot";}else if(nativeRanged){s.target=rangedAim.point;aim=nativeEvidence;}else s.target=Target(c,a.aim,&aim);s.destination=e.kind==1;
    s.direction=s.target-s.pos;if(s.direction.squaredLength()<.0001f)s.direction=Vector3::UNIT_Z;s.range=s.direction.length();if(nativeRanged)s.direction=rangedAim.direction;else s.direction.normalise();
    // 061三远程实际飞行上限直接使用该招私有FCS，不再在瞄准点后40单位强制空爆。
    s.range=nativeRanged?moves[a.move].technique->initialDistance:(s.destination?s.range:std::max(s.range+40.f,120.f));s.speed=ProjectileSpeed(a.move); // 102固定飞行速度；range沿用各招私有FCS（火神/脉冲5000，光炮不改）。
    // 火神使用源ESP指定Fireball四层；其余炮弹保留各自模型。碰撞为单个球，不把尾焰当命中。
    if(!Borrow(s.visual,e.kind==6?"bullet":"shell"))return false;
    // PlasmaBall三层源模型已做Skyrim→Kenshi统一比例转换，保持该尺寸；尾环不进入弹体碰撞。
    s.visualRadius=e.kind==7?assets[s.visual.key].bound:s.collisionRadius;
    // 临时可视在入容器失败时仍由本层释放；成功后沿用原按值转移所有权，不新增引擎线程。
    const size_t oldCapacity=shots.capacity();
    try{DrawShot(s,a.origin);shots.push_back(s);}catch(...){s.visual.Clear(true);throw;}
    if(IrisDiagnostics::CollisionProfileEnabled()){
        IrisDiagnostics::Add(IrisDiagnostics::PROJECTILE_SPAWNS);if(shots.capacity()!=oldCapacity)IrisDiagnostics::Add(IrisDiagnostics::PROJECTILE_VECTOR_GROWTH);
    }
    if(IrisDiagnostics::DetailsEnabled()){std::ostringstream out;out<<"projectile_spawn cast="<<s.cast<<" move="<<s.move<<" event="<<s.event<<" origin="<<s.pos.x<<","<<s.pos.y<<","<<s.pos.z<<" aim="<<s.target.x<<","<<s.target.y<<","<<s.target.z<<" direction="<<s.direction.x<<","<<s.direction.y<<","<<s.direction.z<<" target="<<aim.target.index<<":"<<aim.target.serial<<" target_root="<<aim.root.x<<","<<aim.root.y<<","<<aim.root.z<<" raw_bone="<<aim.raw.x<<","<<aim.raw.y<<","<<aim.raw.z<<" aim_source="<<aim.source<<" aim_distance="<<(s.target-s.pos).length()<<" effective_speed_game_units="<<rangedAim.effectiveSpeed<<" rate="<<s.rate<<" flight_rate=1 action_rate="<<s.rate<<" max_travel="<<s.range<<" speed_game_units="<<s.speed<<" sphere_radius="<<s.collisionRadius<<" visual_radius="<<s.visualRadius<<" blast_radius="<<s.radius<<" asset="<<s.visual.key<<" shared_world_bone_aim="<<(!nativeRanged&&e.kind!=1)<<" native_aim_shared="<<nativeRanged<<" aim_frame="<<rangedAim.sequence<<" origin_offset_changed=0 non_damageable_transparent="<<RangedMove(s.move);Log(out.str());}
    return true;
}

void TrailVertex(Ogre::ManualObject* out,const Vector3& p,const Vector3& origin,float u,float v,float alpha){
    out->position(scene->getRootSceneNode()->convertWorldToLocalPosition(p-origin));out->normal(Vector3::UNIT_Y);out->colour(Ogre::ColourValue(1,1,1,alpha));out->textureCoord(u,v);
}
void UpdateTrail(Actor& a,const Matrix4* weapon,float t,float dt){
    // 087只量测原附件/刀光更新，不改变显隐、寿命、变换或生命周期。
    IrisDiagnostics::Scope timing(IrisDiagnostics::TRAIL_UPDATE);
    // 普通三连没有装饰特效；隐藏自有刀光，不改普通武器材质。
    if(a.move==9){a.trailPoints.clear();if(a.trail)a.trail->setVisible(false);return;}
    for(size_t i=0;i<a.trailPoints.size();++i)a.trailPoints[i].age+=dt*a.rate;
    while(!a.trailPoints.empty()&&a.trailPoints.front().age>.16f)a.trailPoints.pop_front();
    // 螺旋的连续旋转刀光覆盖三次源HitFrame之间的真实武器轨迹；仍只有三个健康事件。
    bool swing=weapon&&a.active&&a.move==1&&t>=.42f&&t<=1.56f;float length=0;
    if(weapon&&a.active)for(size_t i=0;i<moves[a.move].events.size();++i){const Event& e=moves[a.move].events[i];if((e.kind==0||e.kind==5)&&t>=e.time-.16f&&t<=e.time+.1f){swing=true;length=e.kind==5?90.f:0.f;break;}}
    if(swing){TrailPoint p;p.age=0;
        p.a=(*weapon)*Vector3(1.65f,0,length?8.534358047f:-5.f)+a.origin;
        p.b=(*weapon)*Vector3(1.65f,0,length?98.534358047f:8.325f)+a.origin;
        // 历史点最多16个，静止时不堆重合三角；拖尾仅装饰，没有独立健康/物理命中。
        if(a.trailPoints.empty()||(a.trailPoints.back().b-p.b).squaredLength()>.001f)a.trailPoints.push_back(p);
        while(a.trailPoints.size()>16)a.trailPoints.pop_front();
    }
    // 没有三角时清空一次；不向Ogre提交零顶点的beginUpdate段。
    if(a.trailPoints.size()<2){if(a.trail&&a.trail->getNumSections())a.trail->clear();return;}
    if(!a.trail){a.trail=scene->createManualObject();a.trail->setDynamic(true);a.trail->setRenderQueueGroup(83);a.trail->setCastShadows(false);scene->getRootSceneNode()->attachObject(a.trail);}
    if(a.trail->getNumSections())a.trail->beginUpdate(0);else a.trail->begin("IrisArsenal/Eight/WeaponTrail",Ogre::RenderOperation::OT_TRIANGLE_LIST,Iris::GROUP);
    for(size_t i=1;i<a.trailPoints.size();++i){const TrailPoint& p=a.trailPoints[i-1];const TrailPoint& q=a.trailPoints[i];float u=float(i-1)/15,v=float(i)/15,pa=std::max(0.f,1-p.age/.16f),qa=std::max(0.f,1-q.age/.16f);
        TrailVertex(a.trail,p.a,a.origin,u,0,pa);TrailVertex(a.trail,p.b,a.origin,u,1,pa);TrailVertex(a.trail,q.b,a.origin,v,1,qa);
        TrailVertex(a.trail,p.a,a.origin,u,0,pa);TrailVertex(a.trail,q.b,a.origin,v,1,qa);TrailVertex(a.trail,q.a,a.origin,v,0,qa);
    }a.trail->end();
    // 080仅诊断隐藏：正常模式不写额外显隐状态，保留既有普通三连的刀光行为。
    if(diagnosticHideEffects)a.trail->setVisible(false);
}
float CueAge(const Actor& a,const char* key,float t){
    float age=-1;for(size_t n=0;n<moves[a.move].cues.size();++n){const FxCue& cue=moves[a.move].cues[n];if(cue.key==key&&t>=cue.time&&(age<0||t-cue.time<age))age=t-cue.time;}return age;
}
void ShowParts(Character* c,Actor& a,const Matrix4& w,float t){
    // 087只量测原附件/刀光更新，不改变显隐、寿命、变换或生命周期。
    IrisDiagnostics::Scope timing(IrisDiagnostics::ATTACHMENT_UPDATE);
    // 普通三连只保留武器动作，不复用尾焰、刀光或爆炸。
    if(a.move==9)return;
    // 坐锤炮击复用一份原beam.nif五层附件，各次成功发射重置其源效果年龄。
    // 四次球形健康事件独立；不叠四份光束、不重启角色动画，不改远程光炮。
    // 067：源每次IrisBeam生成新的光束；只按已成功消费的四个事件重启UV/形态年龄，
    // 不把四次扣血再播放一遍，也不在失败重试或暂停时凭空重启。方向仍取当前实际枪口。
    float cannonAge=-1.f;
    if(a.move==8)for(unsigned n=0;n<a.next&&n<moves[8].events.size();++n)
        if(moves[8].events[n].kind==9)cannonAge=t-moves[8].events[n].time;
    if(cannonAge>=0&&t<moves[8].events.back().time+.12f){
        if(!a.cannon.entity)Borrow(a.cannon,"electro_burst");
        // 原生锤枪随演员转向，不能再沿起手heading发射；和球形事件共用实际枪口轴。
        CannonFrame frame;bool valid=ElectroFrame(w,a.origin,c->getPosition(),moves[8].events.front().radius,frame);
        if(a.cannon.entity&&valid)a.cannon.Draw(Pose(frame.muzzle-a.origin,frame.orientation,Vector3(1,1,frame.reach)),cannonAge,1.f);else a.cannon.Hide();
    }else a.cannon.Hide();
    // 原PROJ.NAM1 -> SW_MagMuzzle -> AddOnNode09 -> MPSFireBoltImpact01。
    // 离线按20个源射击点展开、按源容量保留存活粒子；运行时只有一份附件，枪口同武器矩阵，不附加伤害。
    float muzzleAge=a.move==5&&!moves[5].events.empty()?t-moves[5].events.front().time:-1.f;
    if(muzzleAge>=0&&muzzleAge<assets["muzzle_fire"].duration){
        if(!a.muzzleFire.entity)Borrow(a.muzzleFire,"muzzle_fire");
        if(a.muzzleFire.entity)a.muzzleFire.Draw(Relative(w,Vector3(1.807138657f,0,8.534358047f),Quaternion::IDENTITY,Vector3::UNIT_SCALE),muzzleAge,1.f);
    }else a.muzzleFire.Hide();
    // 原backfire拥有独立mSprayShort曲线。使用最近源触发的局部年龄，暂停/变速仍跟随身体时间。
    float exhaustAge=CueAge(a,"backfire",t);bool sourceBackfire=false;
    for(size_t n=0;n<moves[a.move].cues.size();++n)if(moves[a.move].cues[n].key=="backfire")sourceBackfire=true;
    if(!sourceBackfire)for(size_t n=0;n<moves[a.move].events.size();++n){float age=t-moves[a.move].events[n].time;if(age>=0&&(exhaustAge<0||age<exhaustAge))exhaustAge=age;}
    float exhaustLife=assets["exhaust"].duration;
    if(exhaustAge>=0&&exhaustAge<exhaustLife){if(!a.exhaust.entity)Borrow(a.exhaust,"exhaust");if(a.exhaust.entity)a.exhaust.Draw(w,exhaustAge,1.f);}else a.exhaust.Hide();
    // 翻滚原$IrisExplosion在发射时点火；这是无伤害前导小火柱，主爆炸仍由弹体真实落点单独生成。
    float igniteAge=CueAge(a,"ignition",t);
    if(a.move==0&&igniteAge>=0&&igniteAge<.55f){if(!a.ignition.entity)Borrow(a.ignition,"fire_blast");
        if(a.ignition.entity)a.ignition.Draw(Pose(a.ground-a.origin,Quaternion::IDENTITY,Vector3(6,6,6)),igniteAge*4.f,std::min(1.f,(.55f-igniteAge)/.12f));}else a.ignition.Hide();
    // 全力爆发漏掉的charge3真实五层能量流，轴与90长光刃一致；只补视觉，不增加健康/物理事件。
    float chargeAge=CueAge(a,"charge_halo",t),offAge=CueAge(a,"off",t);
    if(a.move==4&&chargeAge>=0&&(offAge<0||offAge>chargeAge)){if(!a.halo.entity)Borrow(a.halo,"charge_halo");float local=fmodf(chargeAge,assets["charge_halo"].duration);
        if(a.halo.entity)a.halo.Draw(Relative(w,Vector3(1.807138657f,0,8.534358047f),Quaternion::IDENTITY,Vector3(4,4,90)),local,t<3.18f?1.f:std::max(0.f,1-(t-3.18f)/.35f));}else a.halo.Hide();
    // 063源IrisAnim同时启用武器小准星anim与角色根大准星anim1；两份源控制器各自取样。
    // 小组跟原生Prop2，大组只读当前角色渲染根矩阵，不跟随枪管旋转而绕人物乱翻；不写角色或骨骼。
    // 复用原flash自有实例；换招换资源前归还旧类型，End/Clear仍走原隐藏/释放路径，不增加线程或对象槽。
    float gunAge=CueAge(a,"gun",t),gunOff=CueAge(a,"off",t);
    // 原INI84B保留2.4秒、85C保留2.2秒；各自收尾，不把短寿命大组拖到动作末尾。
    bool gunLive=a.move==5&&gunAge>=0&&gunAge<2.4f&&(gunOff<0||gunOff>gunAge);
    bool bodyLive=gunLive&&gunAge<2.2f;
    float pulseAge=a.move==6&&!moves[6].events.empty()?t-moves[6].events.front().time:-1.f;
    const char* attachment=bodyLive?"vulcan_body":pulseAge>=0&&pulseAge<assets["pulse_muzzle"].duration?"pulse_muzzle":0;
    if(attachment){
        if(a.flash.entity&&a.flash.key!=attachment)Return(a.flash);
        if(!a.flash.entity)Borrow(a.flash,attachment);
        if(a.flash.entity){
            if(bodyLive)a.flash.Draw(c->animation->node->_getFullTransformUpdated(),gunAge,1.f);
            // 脉冲原824火焰统一挂在实际枪口，三次发射各自源时钟已离线展开；显示标尺6不参与伤害。
            else a.flash.Draw(Relative(w,Vector3(1.807138657f,0,8.534358047f),Quaternion::IDENTITY,Vector3(6,6,6)),pulseAge,1.f);
        }
    }else a.flash.Hide();
    // 059真实EXanim1九组红形体/两组蓝准星与源蓝光、FireWave已烘焙到同一武器局部系。
    // 传PA10原始素材秒给各层；102用下方逆映射匹配加速后的身体，准星/蓝相/火相共用原曲线。
    // 102只对极致驱动反解原素材时钟；其它九招不进入映射，也不让发射后特效继续加倍。
    const float ionTime=a.move==7?DriveEffectTime(t):0.f;
    if(a.move==7&&ionTime>=.30f&&ionTime<assets["ion"].duration){
        if(!a.ion.entity)Borrow(a.ion,"ion");if(a.ion.entity)a.ion.Draw(w,ionTime,1.f);
    }else a.ion.Hide();
    // 终结形态不再丢失：源EXDrill2的AnimObjectA/B已烘焙成相对WEAPON矩阵。
    // 展开/射击后合拢均由源轨道决定，只绘制自有实体；不写角色、TagPoint或共享武器。
    float wingAge=CueAge(a,"wing",t),wingOff=CueAge(a,"wing_off",t);
    if(a.move==3&&wingAge>=0&&wingAge<assets["drill_wings"].duration&&(wingOff<0||wingOff>wingAge)){
        if(!a.wings.entity)Borrow(a.wings,"drill_wings");if(a.wings.entity)a.wings.Draw(w,wingAge,1.f);
    }else a.wings.Hide();
    if(a.move==3){
        if(!a.drill.entity&&!Borrow(a.drill,"drill"))return;float ext=t<.416666667f||wingAge>=0?0:std::min(1.f,(t-.416666667f)/.08f);
        // 066：本机Ogre的setIndexDataEndIndex(0)直接返回，不会隐藏；原064门实际无效。
        // 改用自有SubEntity custom9控制圆环/小箍的投影裁剪。0、15..18与钻头共用同一pose和时钟，
        // 旋转前整组三角在裁剪体外；到同一spinBegin才恢复真实顶点，不改共享材质、物理或线程。
        const float spinBegin=1.633267999f;float spin=std::max(0.f,t-spinBegin)*15.f*6.283185307f/4.125f;
        Matrix4 pose=Relative(w,Vector3(1.807138657f,0,8.534358047f),Quaternion(Ogre::Radian(spin),Vector3::UNIT_Z),Vector3(1,1,std::max(.02f,ext)));a.drill.Draw(pose,t,ext>0?1.f:0.f);
        const bool spinning=t>=spinBegin&&ext>0;
        const bool wasVisible=a.drill.entity->getSubEntity(15)->getCustomParameter(9).x>.5f;
        for(unsigned layer=0;layer<19;++layer)if(layer==0||layer>=15)
            a.drill.entity->getSubEntity(layer)->setCustomParameter(9,Ogre::Vector4(spinning?1.f:0.f,0,0,0));
        // 仅门状态改变时记一次，不逐帧写入；日志证明传参，不冒充GPU已绘制。
        if(wasVisible!=spinning){std::ostringstream out;out<<"drill_ring_gate contract=IRIS_DRILL_RING_GATE_066 cast="<<a.id<<" clip="<<t<<" visible="<<spinning<<" angle_rad="<<spin<<" gate=custom9 shared_pose=1 GPU_verified=0";Log(out.str());}
    }
    if(a.move==5){if(!a.gun.entity&&!Borrow(a.gun,"gun"))return;a.gun.Draw(w,std::max(0.f,gunAge),gunLive?1.f:0.f);}
    if(a.move==4){if(!a.blade.entity&&!Borrow(a.blade,"blade"))return;
        // 源2级光刃核心z=46.13..366.74，实际刃长320.61；扣掉刃根后缩放为90，避免以前按maxZ缩放而短12。
        float grow=std::min(1.f,t/.888853333f),fade=t<3.18f?1.f:std::max(0.f,1-(t-3.18f)/.35f);
        Matrix4 pose=Relative(w,Vector3(1.807138657f,0,8.534358047f),Quaternion::IDENTITY,Vector3(.32f,.32f,(90.f/320.61f)*std::max(.01f,grow)))*Pose(Vector3(-10.3f,0,-46.13f),Quaternion::IDENTITY,Vector3::UNIT_SCALE);
        a.blade.Draw(pose,t,fade*grow);
    }
}
void DrawBeam(Residue& r,const Vector3& origin){
    // 092只观察本次同步接口，子耗时由根栈扣除；不改参数、次数、返回及所有权。
    IrisDiagnostics::InterfaceScope interfaceTiming(IrisDiagnostics::IF_BEAM_DRAW);

    if(r.length<=.0001f){r.visual.Hide();return;}
    float alpha=std::min(1.f,r.age/.05f)*std::min(1.f,(r.life-r.age)/.25f);Quaternion q=Vector3::UNIT_Z.getRotationTo(r.direction);
    // 059独立CC0纹理的三层共轴光流均r<=1、z=0..1；外层半径严格匹配R9角色查询。
    // 中心地形射线裁短后的同一长度驱动平端网格；extent按实际长度重复UV，不把10000射程拉成一张糊图。
    r.visual.Draw(Pose(r.pos-origin,q,Vector3(r.radius,r.radius,r.length)),r.age,alpha,r.length);
}
unsigned PrepareShotBatch(GameWorld* w,size_t visits,unsigned& budget,bool& allowEmpty){
    // 092只观察本次同步接口，子耗时由根栈扣除；不改参数、次数、返回及所有权。
    IrisDiagnostics::InterfaceScope interfaceTiming(IrisDiagnostics::IF_SHOT_BATCH);

    if(!rangedBatchEnabled||budget<4||visits<2||shots.size()<2)return 0;
    unsigned count=0,limit=std::min(IrisNative::RANGED_BATCH_CAPACITY,budget/2);size_t start=shotCursor%shots.size();
    while(count<limit&&count<visits&&count<shots.size()){const Shot& s=shots[(start+count)%shots.size()];
        float step=std::min(s.range-s.travel,s.speed*s.pending);if(!RangedMove(s.move)||step<=.000001f)break;
        RangedTag& tag=shotBatchWork.tags[count];tag.cast=s.cast;tag.event=s.event;tag.cursor=0;
        RangedPath(Path(s.pos,s.pos+s.direction*step,s.collisionRadius),false,shotBatchWork.inputs[count]);++count;
    }return RunRangedBatch(w,shotBatchWork,count,budget,&allowEmpty)?count:0;
}

void AdvanceEffects(GameWorld* w,float dt,const Vector3& origin,unsigned& budget){
    // 092只观察本次同步接口，子耗时由根栈扣除；不改参数、次数、返回及所有权。
    IrisDiagnostics::InterfaceScope interfaceTiming(IrisDiagnostics::IF_EFFECTS);

    // 未获得查询预算的飞弹累积各自游戏秒；不会丢弃这一帧时间，也不因为动作收尾换时钟。
    const bool shotAudit=projectileWorkLogging&&IrisDiagnostics::DetailsEnabled();
    const size_t initialShots=shots.size();size_t visitedShots=0;
    // 102：dt已经是含游戏倍速的游戏秒；暂停仍由外层阻止推进。
    // pending保留预算未访问的路程时间，不再乘攻击速率；整段连续碰撞/失败重试和FIFO保持。
    for(size_t i=0;i<shots.size();++i){Shot& s=shots[i];s.pending+=dt;
        if(shotAudit){++s.auditUpdates;s.auditAge+=dt;s.auditMaxPending=std::max(s.auditMaxPending,s.pending);}}
    size_t visits=shots.size();unsigned ready=0,next=0;bool allowEmpty=true; // 090空间模式遇异常才停后续试探；089旧模式另在无收益时停。均只在本安全更新有效。
    // 只访问本轮已有飞弹各一次；预算不足的每发保留pending游戏秒，下一帧从未访问者继续。
    // 弹体数量不再封顶；和范围碰撞作业共享64查询预算并轮转，剩余弹体保留pending及完整轨迹。
    while(visits--&&!shots.empty()&&(budget||next<ready)){
        IrisDiagnostics::InterfaceScope shotConsume(IrisDiagnostics::IF_SHOT_CONSUME);
        ++visitedShots;
        if(next==ready){next=0;ready=PrepareShotBatch(w,visits+1,budget,allowEmpty);}
        size_t i=shotCursor%shots.size();Shot& s=shots[i];float step=std::min(s.range-s.travel,s.speed*s.pending);if(step<=.000001f){++shotCursor;continue;}
        // 057三远程分离地形和角色，火焰翻滚仍走原单次扫掠。预算不足只让出本轮，
        // 不计物理失败、不消耗pending、不移动弹体；两查询在现有同一安全窗口完成。
        const bool split=RangedMove(s.move);const unsigned required=split?2U:1U;
        Vector3 end=s.pos+s.direction*step;IrisNative::Contacts localHits,localTerrain;const IrisNative::Contacts* hitValues=&localHits;const IrisNative::Contacts* terrainValues=&localTerrain;bool complete;unsigned issued=0;
        if(next<ready&&(shotBatchWork.tags[next].cast!=s.cast||shotBatchWork.tags[next].event!=s.event)){
            if(IrisDiagnostics::CollisionProfileEnabled())IrisDiagnostics::Add(IrisDiagnostics::RANGED_BATCH_UNUSED,ready-next);next=ready;}
        if(next<ready){if(shotAudit)issued=shotBatchWork.results[next].rayCalls+shotBatchWork.results[next].bodyCalls;const IrisNative::RangedResult& r=RangedValue(shotBatchWork,next++);hitValues=&r.characters;terrainValues=&r.terrain;complete=r.status==IrisNative::QUERY_COMPLETE;}
        else{if(budget<required){IrisDiagnostics::Add(IrisDiagnostics::QUERY_BUDGET_WAIT);if(shotAudit)++s.auditBudget;++shotCursor;continue;}
            const unsigned before=budget;complete=Contacts(w,Path(s.pos,end,s.collisionRadius),localHits,budget,0,split?&localTerrain:0);issued=before-budget;}
        const IrisNative::Contacts& hits=*hitValues;const IrisNative::Contacts& terrain=*terrainValues;
        if(shotAudit){++s.auditAttempts;s.auditCommands+=issued;
            if(!complete){++s.auditWaits;if(!issued)++s.auditNoCommands;}
            else if(!hits.count&&!terrain.count)++s.auditEmpty;}
        if(!complete){
            // 每条飞弹独立报告连续失败，不能依赖全进程最初16条日志；不丢pending游戏秒或重置位置。
            if(++s.retries==1||s.retries%120==0){std::ostringstream out;out<<"projectile_query_wait cast="<<s.cast<<" event="<<s.event<<" move="<<s.move<<" retries="<<s.retries<<" issue="<<IrisNative::IssueReason(hits.diagnostic.issue)<<" raw_fraction="<<hits.diagnostic.rawFraction<<" fraction_bits="<<hits.diagnostic.fractionBits<<" radius="<<s.collisionRadius<<" other_shots_continue=1";Log(out.str());}
            ++shotCursor;continue;}
        s.retries=0;
        bool hit=terrain.count!=0;float f=hit?terrain.items[0].fraction:1;Character* caster=s.caster.getCharacter();unsigned ignored=0;
        hand blocker=hit?Handle(terrain.items[0].object):hand();bool worldBlocker=hit&&!terrain.items[0].object.present;
        RangedContactMemo contactMemo;
        {IrisDiagnostics::Scope timing(IrisDiagnostics::RANGED_FILTER); // 087在PhysX回调外消费，保留排序/最近阻挡和墙同距优先。
        for(unsigned k=0;k<hits.count;++k){hand h=Handle(hits.items[k].object);
            // 三招远程共用原生资格筛选，先跳过不能受伤角色再找最近阻挡，不能先吞弹再排除伤害。
            // 已完整取得的ALL_HITS仍按距离排序；不因忽略前一个友军而吞掉后面的墙或敌人。
            if(split?contactMemo.Ignore(caster,hits.items[k].object,h):h.getCharacter()==caster){++ignored;continue;}
            // 两种fraction均以同一完整步长计算；先忽略友军，再取更早接触，完全同距由墙阻挡。
            // 不按回调到达次序判断；非远程的第一条有效ALL_HITS仍按原次序消费。
            if(!hit||hits.items[k].fraction<f){hit=true;blocker=h;worldBlocker=!hits.items[k].object.present;f=hits.items[k].fraction;}break;}}
        if(IrisDiagnostics::CollisionProfileEnabled())IrisDiagnostics::Add(IrisDiagnostics::RANGED_MEMO_COLLISIONS,contactMemo.collisions);
        // 080只汇总本查询的实际复用；日志关闭时Add不计时/加锁，资格复用本身仍有效。
        if(contactMemo.checks)IrisDiagnostics::Add(IrisDiagnostics::RANGED_CONTACT_CHECKS,contactMemo.checks);
        if(contactMemo.reuses)IrisDiagnostics::Add(IrisDiagnostics::RANGED_CONTACT_REUSES,contactMemo.reuses);
        end=s.pos+s.direction*(step*f);bool ended=hit||s.travel+step>=s.range;
        if(ended){
            IrisDiagnostics::InterfaceScope shotTerminate(IrisDiagnostics::IF_SHOT_TERMINATE);
            // 061远程到达FCS射程但没有碰撞时自然消退，日志明确区别；没有物理命中就不凭空播放爆炸/扣血。
            if(split&&!hit){
                if(IrisDiagnostics::DetailsEnabled()){std::ostringstream out;out<<"projectile_expire cast="<<s.cast<<" move="<<s.move<<" event="<<s.event<<" contact=0 reason=range_limit travel="<<s.range<<" max_travel="<<s.range<<" damage_job=0";Log(out.str());}
                LogShotWork(s,"range_limit",s.range);Return(s.visual);shots.erase(shots.begin()+i);shotCursor=unsigned(i);continue;
            }
            // 翻滚源爆炸保持发射朝向；脉冲/火神保留既有特效朝向，直接命中身份一并交给Blast。
            Vector3 forward(s.direction.x,0,s.direction.z);if(forward.squaredLength()<.0001f)forward=Vector3::UNIT_Z;forward.normalise();
            Quaternion facing=s.move==0?Vector3::UNIT_Z.getRotationTo(forward):Quaternion::IDENTITY;
            if(!Blast(s.caster,s.cast,s.event,s.move,end,s.radius,s.mult,s.rate,false,facing,hit&&!worldBlocker?&blocker:0)){if(shotAudit)++s.auditBlast;++shotCursor;continue;}
            // 077只纠正日志标签：有hand的建筑仍是环境；不改变上方既有Blast/直接身份处理。
            // split为false的翻滚没有环境射线，不能读取未初始化的terrain诊断。
            if(IrisDiagnostics::DetailsEnabled()){std::ostringstream out;out<<"projectile_impact cast="<<s.cast<<" move="<<s.move<<" event="<<s.event<<" contact="<<hit<<" fraction="<<f<<" point="<<end.x<<","<<end.y<<","<<end.z<<" sphere_radius="<<s.collisionRadius<<" blocker_type="<<int(blocker.type)<<" blocker="<<blocker.index<<":"<<blocker.serial<<" direct_contact="<<(hit&&!worldBlocker&&blocker.type==CHARACTER)<<" travel="<<s.travel+step*f<<" max_travel="<<s.range<<" world_geometry="<<(hit&&(worldBlocker||blocker.type!=CHARACTER))<<" ignored_non_damageable_shapes="<<ignored<<" terrain_query="<<(split?"ray":"sphere_sweep")<<" character_query=sphere_sweep terrain_contact="<<terrain.count
                    <<" blocker_container="<<blocker.container<<" blocker_container_serial="<<blocker.containerSerial
                    <<" terrain_mask=0x"<<std::hex<<(split?terrain.diagnostic.terrain.groups:0U)<<std::dec
                    <<" terrain_distance="<<(split?terrain.diagnostic.terrain.distance:-1.f)<<" terrain_metadata="<<(split?terrain.diagnostic.terrain.metadata:0U)
                    <<" terrain_shape_type="<<(split?terrain.diagnostic.terrain.shapeType:0U)<<" terrain_group="<<(split?terrain.diagnostic.terrain.shapeGroup:0U)
                    <<" terrain_trigger="<<(split?terrain.diagnostic.terrain.trigger:0U);Log(out.str());}
            LogShotWork(s,"impact",s.travel+step*f);Return(s.visual);shots.erase(shots.begin()+i);shotCursor=unsigned(i);continue;}
        s.pos=end;s.travel+=step;s.pending=std::max(0.f,s.pending-step/s.speed);
        // 沿真实有限球扫掠位置显示源火球。包围球按源几何中心校准为R4.5，不能让图形与碰撞偏心。
        DrawShot(s,origin);++shotCursor;
    }
    if(next<ready)if(IrisDiagnostics::CollisionProfileEnabled())IrisDiagnostics::Add(IrisDiagnostics::RANGED_BATCH_UNUSED,ready-next);
    // 只计本轮未访问的原有弹体数；不遍历补加时钟/日志，不把它误称SDK失败或丢弹。
    if(initialShots>visitedShots&&IrisDiagnostics::CollisionProfileEnabled())IrisDiagnostics::Add(IrisDiagnostics::PROJECTILE_UNVISITED,initialShots-visitedShots);
    // 092逐后效的寿命/归还/擦除与Draw分开；不改变年龄或迭代顺序。
    for(size_t i=0;i<residues.size();){IrisDiagnostics::InterfaceScope residueUpdate(IrisDiagnostics::IF_RESIDUES);Residue& r=residues[i];r.age+=dt*r.rate;if(r.age>=r.life){Return(r.visual);residues.erase(residues.begin()+i);continue;}
        float t=r.age/r.life,k=r.radius/17.f*(.35f+.65f*std::min(1.f,t*4));float alpha=std::min(1.f,t*20)*std::max(0.f,1-t);
        // 038钻天破资产以单位球=真实伤害半径制作；保守裁剪包围球只供Ogre裁剪，不能反过来缩小可见范围。
        if(r.key=="pulse_blast"||r.key=="drill_blast"){float size=r.key=="drill_blast"?r.radius:r.radius/assets[r.key].peak;
            // 064钻天破源轨道和粒子都使用同一已烘焙年龄；不再以固定子层5推算末端年龄。
            float left=r.life-r.age;
            r.visual.Draw(Pose(r.pos-origin,r.orientation,Vector3(size,size,size)),r.age,std::min(1.f,left/.15f));}
        // 067范围层按源alpha/纹理可见尺度归一；和该次球形判定共用中心、朝向和R25，不用裁剪包围半径再缩小。
        else if(r.key=="electro_area")r.visual.Draw(Pose(r.pos-origin,r.orientation,Vector3(r.radius,r.radius,r.radius)),r.age,1.f);
        // 080光炮年龄照常推进；可视统一由本Tick既有ResolveJobs后的遍历更新一次，
        // 消费最新墙前长度。该函数唯一调用者就是下方Tick，暂停和无原点时的旧门保持。
        else if(r.key=="beam"){/* 仅延后本帧参数提交，不延后查询、伤害或年龄。 */}
        else if(r.key=="shock"||r.key=="fire_blast"||r.key=="roll_blast"||r.key=="full_blast"){// shock作者已按各层XZ半径归一为1；不可再次除整段3D包围半径，否则火焰与R36球形AOE再度不符。
            float size=r.radius;r.visual.Draw(Pose(r.pos-origin+Vector3(0,r.key=="shock"?.8f:0.f,0),r.orientation,Vector3(size,size,size)),r.age,1.f);}
        else r.visual.Draw(Pose(r.pos-origin,Quaternion::IDENTITY,Vector3(k,k,k)),r.age,alpha);++i;
    }
}
void EnsureMoves(GameWorld* w){
    for(unsigned i=0;i<MOVE_COUNT;++i)if(!moves[i].technique){std::ostringstream id;id<<10+i<<"-IrisArsenal.mod";GameData* d=w->gamedata.getData(id.str(),COMBAT_TECHNIQUE);if(!d)continue;
        CombatTechniqueData* t=new CombatTechniqueData(d);t->maxTargetHits=0;
        if(t->animation!=moves[i].animation||!Finite(t->initialDistance)||!Finite(t->minDistanceVsStatic)||t->initialDistance<t->minDistanceVsStatic)throw std::runtime_error("private move FCS mismatch");
        // 距离覆盖发生在私有FCS副本内；-1继承实际加载FCS，而非复制CSV的旧值。
        // 上限仅影响选招，不延长武器/爆炸；玩家扩大上限时仍可能因真实几何不足而空放。
        if(moves[i].attackMin>=0)t->minDistanceVsStatic=moves[i].attackMin;
        if(moves[i].attackMax>=0)t->initialDistance=moves[i].attackMax;
        if(t->initialDistance<t->minDistanceVsStatic){delete t;throw std::runtime_error("move distance conflicts with loaded FCS: "+moves[i].key);}
        std::ostringstream distance;distance<<"move_start_distance move="<<moves[i].key<<" min="<<t->minDistanceVsStatic<<" max="<<t->initialDistance<<" source=private_FCS_with_optional_INI";Log(distance.str());
        if(BlockGuardMove(i)&&moves[i].preventBlock){
            // 原生attackState另有wantsToBlock分支：到motionStopsAnimationFrame才提前退出攻击。
            // 只在本插件新建的私有副本中，将每段的此门延到归一化片尾1.0；不清wantsToBlock、
            // 不覆盖combatState/nextMove，也不改公共FCS或原伤害帧。正常acceptableEndTime仍负责收招。
            const int count=t->numImpactPoints();if(count<=0||count>64||!Finite(t->acceptableEndTime01)||t->acceptableEndTime01<=0||t->acceptableEndTime01>1||t->isBlock||t->isDodge)throw std::runtime_error("private melee block window invalid");
            for(int point=0;point<count;++point){CombatTechniqueData::ImpactPoint* impact=t->impactPoint(point);if(!impact||!Finite(impact->motionStopsAnimationFrame)||impact->motionStopsAnimationFrame<0||impact->motionStopsAnimationFrame>1)throw std::runtime_error("private melee impact stop invalid");impact->motionStopsAnimationFrame=1.f;}
        }
        // 076：对象完全初始化后先发布身份，再使正式消费者可取得该指针；后续原生回调不会漏认。
        PublishTechniqueIdentity(i,t);moves[i].technique=t;
    }
}
void Tick(GameWorld* w,Ogre::SceneManager* sm,float gameDelta){
    // 091抽样器只围住现有同步顺序；Mark不读取引擎/申请许可，不改变continue与事件消费。
    // 092全量阶段与下层接口共用同一根栈；旧WorkTrace仍按原N抽样，不拿其样本估算全量。
    IrisDiagnostics::InterfaceScope interfacePhase(IrisDiagnostics::IF_SETUP);
    IrisDiagnostics::WorkTrace workTrace(IrisDiagnostics::WORK_COMBAT);
    sphereFacts.clear(); // 只复用本安全帧；任何下一帧/物理状态变化都重新查询。
    if(scene&&scene!=sm)Clear(false,"scene_changed");scene=sm;EnsureMoves(w);IrisRanged::Prepare(w);WarmNext();bool paused=w->isPaused();Vector3 origin=Vector3::ZERO;bool haveOrigin=false;
    for(std::map<hand,Actor>::iterator i=actors.begin();i!=actors.end();){workTrace.Mark(IrisDiagnostics::WORK_ACTOR_READY);interfacePhase.Switch(IrisDiagnostics::IF_ACTOR_READY);Actor& a=i->second;Character* c=i->first.getCharacter();
        if(!Iris::ActorReady(c)||!c->animation->node){End(a,"actor_invalid");ClearActor(a,true);actors.erase(i++);continue;}
        if(a.animation!=c->animation){End(a,"animation_changed");a.animation=c->animation;a.ready=false;}
        a.origin=c->getPosition()-c->animation->node->_getDerivedPositionUpdated();if(!Finite(a.origin))throw std::runtime_error("origin nonfinite");origin=a.origin;haveOrigin=true;
        {IrisDiagnostics::InterfaceScope animationScan(IrisDiagnostics::IF_READY_ANIMATIONS);
        // 093先独立量测十招就绪扫描；不缓存跨帧长度，不跳过骨架缺失或原生资格。
        a.ready=true;for(unsigned j=0;j<MOVE_COUNT;++j){a.lengths[j]=AnimationLength(c,j);if(moves[j].weight>0&&!a.lengths[j])a.ready=false;}}
        if(!a.ready){if(a.ranged)End(a,"ranged_animation_unavailable");if(IrisDiagnostics::DetailsEnabled())Log("ten_animation_wait: FCS/source skeleton not loaded");++i;continue;}
        // 只有原生射击回调已发来许可，才能在安全主线程启动整套动作；不在帧循环里自动找人开火。
        workTrace.Mark(IrisDiagnostics::WORK_ACTOR_REQUEST);interfacePhase.Switch(IrisDiagnostics::IF_ACTOR_REQUEST);
        if(IrisRanged::Tracked(c)){
        float rangeMax=0;bool canShoot=warmReady&&a.ready;
        Character* rangedTarget=c->rangedCombat?c->rangedCombat->_getAttackTarget().getCharacter():0;
        float targetRange=rangedTarget?(rangedTarget->getPosition()-c->getPosition()).length():-1;bool inMoveRange=false;
        for(unsigned j=5;j<=7;++j)if(moves[j].weight>0&&moves[j].technique){CombatTechniqueData* mt=moves[j].technique;rangeMax=std::max(rangeMax,mt->initialDistance);if(targetRange>=mt->minDistanceVsStatic&&targetRange<=mt->initialDistance)inMoveRange=true;}
        Ogre::Entity* rangedWeapon=Iris::ActualWeapon(c);Vector3 barrel=rangedWeapon?Muzzle(Iris::SourcePose(rangedWeapon))+a.origin:c->getPosition();
        // 062恢复原先顺序：先由原生决定是否射击，再按该目标距离/INI权重选招。
        // 075：就绪只由此Actor的武器、资源、距离、暂停及当前动作决定；其他持有者不参与。
        // Slot自己的busy/pending、TakeRequest和原生许可继续防止同一角色重复起手，不新增跨线程访问。
        IrisRanged::Publish(c,rangedWeapon&&canShoot&&inMoveRange&&!paused&&!a.active,rangeMax,barrel);
        hand requested;
        if(!a.active&&!paused&&IrisRanged::TakeRequest(c,requested)){
            Character* victim=requested.getCharacter();int selected=victim&&CanDamage(c,victim,true)?PickRanged(a,(victim->getPosition()-c->getPosition()).length()):-1;
            if(selected>=0){
                a.move=selected;a.ranged=true;a.reserved=true;a.rangedWait=0;float speed=c->stats->getAttackSpeed();if(!Finite(speed)||speed<=0)speed=1;
                // 走同一FCS身体/道具动画入口，攻速仍来自角色；远程状态不伪装为近战CombatClass当前招式。
                c->animation->startCombatAnimation(moves[selected].technique,speed,"");
            }else IrisRanged::Finish(c->handle);
        }}
        workTrace.Mark(IrisDiagnostics::WORK_ACTOR_ANIMATION);interfacePhase.Switch(IrisDiagnostics::IF_ACTOR_ANIMATION);
        if(a.ranged&&!IrisRanged::Active(c)){c->animation->stopAnimation(moves[a.move].animation);End(a,"ranged_mode_ended");}
        CombatClass* cc=c->getCombatClass();int move=a.ranged?a.move:(cc?Index(cc->getCurrentTechnique()):-1);Ogre::AnimationState* state=move>=0?c->animation->getAnimationState(moves[move].animation):0;
        // 原生远程动画适配只续播仍有效的本次片段；已禁用/自然到尾不重新启动，不强锁移动或忽略受击。
        if(a.ranged&&state&&state->getEnabled()&&state->getTimePosition()<state->getLength())
            c->animation->runCombatAnimation(moves[move].technique,a.rates[move],"");
        bool live=state&&state->getEnabled()&&state->getWeight()>.001f;float t=live?state->getTimePosition()/state->getLength()*moves[move].seconds:0;
        // startCombatAnimation在本安全窗口发出，权重可能要到下帧原生动画更新才出现，不能立即判作失败。
        // 只等待本次起手最多2个游戏秒；不重启片段、不无限占用本角色起手状态；暂停不累计。
        if(a.ranged&&a.reserved&&!live&&state&&Finite(t)&&t<moves[move].seconds){
            if(!paused)a.rangedWait+=gameDelta;if(a.rangedWait<2.f){++i;continue;}
        }
        if(!live||!Finite(t)||t<0||t>=moves[move].seconds){End(a,"native_action_end_or_interrupt",move,state,paused);UpdateTrail(a,0,0,paused?0:gameDelta);++i;continue;}
        // 039：startCombatAnimation通知可能先于真实片段回零。038把计数变化当新周期，
        // 会在旧8秒尾帧重置next=0并一帧重放全部事件。周期只认真实片段切换/回退，不能认通知本身。
        if(a.active&&(a.move!=move||t+.0001f<a.last)){
            // 104：stopAnimation之后不再借用此前的state；该分支只记录回退原因，时间标作未知。
            if(a.ranged){c->animation->stopAnimation(moves[move].animation);End(a,"ranged_clip_reset",move,0,paused);++i;continue;}
            End(a,"native_new_cycle",move,state,paused);
        }
        if(!a.active&&!paused){
            // 不在遗留尾帧/中途挂接时追补整套历史伤害。起手观察窗由首个源事件和本帧实际游戏时步组成，
            // 不是墙钟冷却；正常变速/低帧率第一帧仍可启动。真正下一轮回到开头后自然重新认领。
            float opening=moves[move].events.front().time+std::max(0.f,gameDelta*a.rates[move]);
            if(t>opening){if(a.start!=a.consumed){a.consumed=a.start;std::ostringstream out;out<<"action_tail_ignored move="<<move<<" clip="<<t<<" opening="<<opening<<" native_start_serial="<<a.start<<" historical_events_replayed=0";Log(out.str());}++i;continue;}
            IrisDiagnostics::Add(IrisDiagnostics::CASTS_STARTED);a.active=true;a.reserved=false;a.move=move;a.consumed=a.start;a.id=++serial;a.next=0;a.stumbles=0;a.last=0;a.havePose=false;a.bladeProgress[0].Reset();a.bladeProgress[1].Reset();if(move==4)a.bladeFemale=c->isFemale();a.rate=a.rates[move];a.heading=c->getOrientation();a.ground=c->getPosition();a.aim=Target(c,a.ground+Vector3(0,0,80));std::ostringstream out;out<<"action_start cast="<<a.id<<" move="<<moves[move].key<<" events="<<moves[move].events.size()<<" native_root=1";Log(out.str());}
        workTrace.Mark(IrisDiagnostics::WORK_ACTOR_POSE);interfacePhase.Switch(IrisDiagnostics::IF_ACTOR_POSE);
        if(!a.active){++i;continue;}Ogre::Entity* actual=Iris::ActualWeapon(c);if(!actual){End(a,"native_attachment_missing");++i;continue;}Matrix4 weapon=Iris::SourcePose(actual);
        // 已出手按原生动画继续；目标消失不单独停招。缓存倍率继续控制动作，已发弹体不再乘此倍率。
        a.rate=a.rates[move];
        workTrace.Mark(IrisDiagnostics::WORK_ACTOR_VISUAL);interfacePhase.Switch(IrisDiagnostics::IF_ATTACHMENTS);
        ShowParts(c,a,weapon,t);UpdateTrail(a,&weapon,t,paused?0:gameDelta);
        workTrace.Mark(IrisDiagnostics::WORK_ACTOR_PATH);interfacePhase.Switch(IrisDiagnostics::IF_BLADE_PATH);
        if(!paused&&!TraceBladeWindows(i->first,a,weapon,t)){++i;continue;}
        workTrace.Mark(IrisDiagnostics::WORK_ACTOR_EVENTS);interfacePhase.Switch(IrisDiagnostics::IF_EMIT);
        if(!paused)while(a.next<moves[move].events.size()&&moves[move].events[a.next].time<=t){if(!Emit(c,i->first,a,moves[move].events[a.next],weapon,t))break;
            std::ostringstream out;out<<"event_emit cast="<<a.id<<" move="<<moves[move].key<<" event="<<a.next<<" type="<<moves[move].events[a.next].kind<<" clip="<<t;Log(out.str());IrisDiagnostics::Add(IrisDiagnostics::EVENTS_EMITTED);++a.next;}
        workTrace.Mark(IrisDiagnostics::WORK_ACTOR_FINISH);interfacePhase.Switch(IrisDiagnostics::IF_ACTOR_FINISH);
        a.previous=weapon;if(a.move==4)a.bladePreviousOrigin=a.origin;if(a.move==3)a.drillPreviousOrigin=a.origin;a.havePose=true;a.last=t;++i;
    }
    // 没有持枪演员仍可能有已发出的投射物。浮动原点只借当前有效角色；无法取得时保留后效而非错坐标查询。
    workTrace.Mark(IrisDiagnostics::WORK_TAIL);interfacePhase.Switch(IrisDiagnostics::IF_TAIL);
    if(!haveOrigin)for(size_t i=0;i<shots.size();++i){Character* c=shots[i].caster.getCharacter();if(c&&c->isValid()&&c->animation&&c->animation->node){origin=c->getPosition()-c->animation->node->_getDerivedPositionUpdated();haveOrigin=Finite(origin);if(haveOrigin)break;}}
    if(haveOrigin){lastOrigin=origin;originKnown=true;}
    // 演员已失效时仅用最后同场景原点完成短尾烟，不留下永不回收的自有实例；读档/换场景会清空该值。
    else if(originKnown){origin=lastOrigin;haveOrigin=true;}
    unsigned budget=64;if(!paused){
        // 已有伤害作业时至少留16次场景调用，剩余预算仍可借给作业；全帧合计始终不超过64。
        // 这是请求调度，不改弹速/伤害/敌人筛选，也不以超预算补查或丢弃事件换吞吐。
        workTrace.Mark(IrisDiagnostics::WORK_EFFECTS);interfacePhase.Switch(IrisDiagnostics::IF_EFFECTS);
        if(haveOrigin){unsigned shotBudget=budget-(jobs.empty()?0U:16U),before=shotBudget;AdvanceEffects(w,gameDelta,origin,shotBudget);budget-=before-shotBudget;}
        workTrace.Mark(IrisDiagnostics::WORK_JOBS);interfacePhase.Switch(IrisDiagnostics::IF_JOBS);
        ResolveJobs(w,budget);CollectBladeLedgers();
        // 查询后再刷新一次光炮，不推进年龄，避免新墙前长度晚一帧才生效；暂停不推进任何后效。
        workTrace.Mark(IrisDiagnostics::WORK_TAIL);interfacePhase.Switch(IrisDiagnostics::IF_TAIL);
        if(haveOrigin)for(size_t i=0;i<residues.size();++i)if(residues[i].key=="beam")DrawBeam(residues[i],origin);
}
    // 自有实例只记录递增高水位，不把实体数冒称显存字节；共享网格/纹理与实例分开解释。
    // 诊断最多随有界池/演员达到新峰值时一行，便于实机区分资源预热与持续无界增长。
    workTrace.Mark(IrisDiagnostics::WORK_TAIL);interfacePhase.Switch(IrisDiagnostics::IF_TAIL);
    size_t attached=0;for(std::map<hand,Actor>::const_iterator i=actors.begin();i!=actors.end();++i){
        const Actor& a=i->second;attached+=(a.drill.entity?1:0)+(a.gun.entity?1:0)+(a.blade.entity?1:0)+(a.exhaust.entity?1:0)+(a.flash.entity?1:0)+(a.ion.entity?1:0)+(a.halo.entity?1:0)+(a.ignition.entity?1:0)+(a.wings.entity?1:0)+(a.muzzleFire.entity?1:0)+(a.cannon.entity?1:0);}
    unsigned activeActors=0,reservedActors=0;for(std::map<hand,Actor>::const_iterator i=actors.begin();i!=actors.end();++i){if(i->second.active)++activeActors;if(i->second.reserved)++reservedActors;}
    IrisDiagnostics::Set(IrisDiagnostics::ACTORS,actors.size());IrisDiagnostics::Set(IrisDiagnostics::ACTIVE_ACTORS,activeActors);IrisDiagnostics::Set(IrisDiagnostics::RESERVED_ACTORS,reservedActors);IrisDiagnostics::Set(IrisDiagnostics::PROJECTILES,shots.size());IrisDiagnostics::Set(IrisDiagnostics::RESIDUES,residues.size());IrisDiagnostics::Set(IrisDiagnostics::IDLE_VISUALS,pool.size());IrisDiagnostics::Set(IrisDiagnostics::ATTACHED_VISUALS,attached);IrisDiagnostics::Set(IrisDiagnostics::JOBS,jobs.size());IrisDiagnostics::Set(IrisDiagnostics::PENDING_DAMAGE,hurts.size());IrisDiagnostics::Set(IrisDiagnostics::WARM_ASSETS,warmed.size());
    size_t total=attached+pool.size()+shots.size()+residues.size();if(total>resourcePeak){resourcePeak=total;
        std::ostringstream out;out<<"own_visual_highwater total="<<total<<" actor_parts="<<attached<<" pool="<<pool.size()<<" shots="<<shots.size()<<" residues="<<residues.size()<<" warmed_assets="<<warmed.size()<<" GPU_bytes_measured=0";Log(out.str());}

}
// 兼容保留Vulcan历史标识；当前仅近战按配置注册TLS，三远程不改防御。TLS只借用本次同步调用的地址，不跨帧保存角色/伤害。每线程一个槽，退出时由系统回收；
// 已安装钩子仍可能被调用，因此读档不释放/复用TLS槽。未匹配的任何原版/其他招式完全原样转发。
DWORD defenceTLS=TLS_OUT_OF_INDEXES;
typedef HitMaterialType(__fastcall* DefenceFn)(CombatClass*,CutDirection,Damages&,Character*);
DefenceFn originalDefence=0;
struct VulcanHitContext {
    CombatClass* combat;Damages* damage;Character* caster;bool pending,seen;HitMaterialType original;
    VulcanHitContext(CombatClass* c,Damages* d,Character* a):combat(c),damage(d),caster(a),pending(true),seen(false),original(HIT_MISSED){}
};
HitMaterialType __fastcall VulcanDefenceHook(CombatClass* self,CutDirection dir,Damages& damage,Character* who){
    // 078此全局防御入口也可能高频；仅抽样原回调总耗时，TLS与防御结果保持。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_DEFENCE);
    IrisNativeAudit::PartScope nativePart(IrisNativeAudit::DEFENCE); // 084同步子树观察，原返回值不改。
    VulcanHitContext* context=defenceTLS==TLS_OUT_OF_INDEXES?0:static_cast<VulcanHitContext*>(TlsGetValue(defenceTLS));
    bool matches=context&&context->pending&&context->combat==self&&context->damage==&damage&&context->caster==who;
    // 必须在调用原链之前消费；原函数引起的嵌套攻击不能借用本次“已物理命中”的许可。
    if(matches)context->pending=false;
    HitMaterialType result=originalDefence(self,dir,damage,who);
    if(matches){context->seen=true;context->original=result;if(result==HIT_MISSED||result==HIT_SWORD)return HIT_FLESH;}
    return result;
}
typedef bool(__fastcall* BlockCheckFn)(CombatClass*,float,float);
BlockCheckFn originalBlockCheck=0;
int ProtectedMeleeMove(CombatClass* self){
    // 格挡与044受击反应共用同一六招窗口，避免一个门已退出而另一个仍保护。
    // 此回调属于原生战斗更新，不能进入Ogre场景/物理查询或操作动画；只查已准备的技巧、
    // 角色句柄缓存和原生动画层的当前身份/进度。角色/世界失效立即放行原生处理。
    if(!self||!Iris::Accepting()||proofOnly)return -1;
    CombatTechniqueData* technique=self->getCurrentTechnique();const int move=Index(technique);
    if(move<0||!BlockGuardMove(unsigned(move))||self->getCombatState()!=CHOP_WEAPON||self->currentTechniqueHasFinished)return -1;
    GameWorld* world=ou;if(!world||!world->initialized||world->gameResetting||world->isLoadingFromASaveGame())return -1;
    Character* c=self->me;
    if(!Iris::ActorReady(c)||c->getCombatClass()!=self||c->isRagdoll()||c->_NV_getProneState()!=PS_NORMAL||c->getChainedModeShackles()||c->animation->currentlyStumbling())return -1;
    std::map<hand,Actor>::const_iterator actor=actors.find(c->handle);
    if(actor==actors.end()||!actor->second.ready||actor->second.animation!=c->animation||c->animation->animationRequirements._currentCombatTechnique!=technique)return -1;
    // 不依赖特效消费者的active标记，避免起手先于安全Tick时漏保护；也不靠start通知重播动画。
    // 原生仲裁只在stillPlayingAnActionOrSomething为false时把在播攻击直接改为防御启动。
    // 必须使用相同原生谓词；片段已停止/正常收尾则不拦截，后效仍存在也不会延长保护。
    const float progress=c->animation->getAnimationProgress(technique);
    if(!Finite(progress)||progress<0||progress>=technique->acceptableEndTime01||progress>=1.f||!c->animation->stillPlayingAnActionOrSomething())return -1;
    return move;
}
int ProtectedRangedMove(CombatClass* self){
    // 远程适配器不伪造CombatClass.currentTechnique，必须查本次远程预约及原生动画要求身份。
    // 回调中只读缓存与原生动画谓词，不访问Ogre，不因飞行弹/后效存活而延长霸体。
    if(!self||!Iris::Accepting()||proofOnly)return -1;
    GameWorld* world=ou;if(!world||!world->initialized||world->gameResetting||world->isLoadingFromASaveGame())return -1;
    Character* c=self->me;
    if(!Iris::ActorReady(c)||c->getCombatClass()!=self||c->isRagdoll()||c->_NV_getProneState()!=PS_NORMAL||c->getChainedModeShackles()||c->animation->currentlyStumbling())return -1;
    std::map<hand,Actor>::const_iterator it=actors.find(c->handle);
    if(it==actors.end())return -1;const Actor& a=it->second;
    if(!a.ready||!a.ranged||(!a.active&&!a.reserved)||!RangedMove(a.move)||a.animation!=c->animation||!IrisRanged::Active(c))return -1;
    CombatTechniqueData* technique=moves[a.move].technique;
    if(!technique||c->animation->animationRequirements._currentCombatTechnique!=technique)return -1;
    const float progress=c->animation->getAnimationProgress(technique);
    if(!Finite(progress)||progress<0||progress>=technique->acceptableEndTime01||progress>=1.f||!c->animation->stillPlayingAnActionOrSomething())return -1;
    return a.move;
}
// 076：只消费原生当前回调已有的技巧/动画要求身份，不查Actor容器、不触碰Ogre/PhysX。
// 远程当前技巧不在CombatClass内，因此受击入口必须同时看动画要求；这里只作否定预筛，
// 进入候选后仍在原有锁内完整检查姿态、进度、配置、角色句柄及世界状态，不在锁外授予保护。
static bool MayNeedTechniqueGuard(CombatClass* combat,bool includeRanged){
    if(!combat)return false;
    try{
        if(OwnTechniqueIdentity(combat->getCurrentTechnique()))return true;
        if(!includeRanged)return false;
        Character* actor=combat->me;
        if(!actor||!actor->isValid()||actor->isDestroyed())return false;
        AnimationClass* animation=actor->animation;
        return animation&&OwnTechniqueIdentity(animation->animationRequirements._currentCombatTechnique);
    }catch(const std::exception&){
        // 预筛无法确认时回到原有加锁/异常回退，不能由优化额外中止保护或跳过原生调用。
        return true;
    }
}
typedef void(__fastcall* StumbleFn)(Character*,CutDirection,Damages&,GameData*,Character*);
StumbleFn originalMeleeStumble=0;
void __fastcall MeleeStumbleHook(Character* self,CutDirection dir,Damages& damage,GameData* part,Character* attacker){
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_STUMBLE);
    IrisNativeAudit::PartScope nativePart(IrisNativeAudit::REACTION); // 084包括已有插件保护与原反应链。
    bool candidate=true;
    try{candidate=MayNeedTechniqueGuard(self?self->getCombatClass():0,true);}catch(const std::exception&){/* 无法确认时保留旧锁内异常回退。 */}
    if(!candidate){originalMeleeStumble(self,dir,damage,part,attacker);return;}
    bool suppress=false;CombatClass* combat=0;
    try{Guard guard(&audit);combat=self?self->getCombatClass():0;int move=ProtectedMeleeMove(combat);if(move<0)move=ProtectedRangedMove(combat);
        // 原生近战和弩弹都先addWound再调用此反应入口；只跳过新反应的选择/播放/任务取消，
        // 不改伤害数据，不再次医疗。所有有限反应强度均免疫，不再区分小僵直与大踉跄阈值。
        // 047覆盖六招特效近战和三招远程当前片段；普通三连击/后效、死亡/昏迷/已倒地及读档走原逻辑。
        // 045：禁用受击免疫时立即走原生；格挡保护开关不影响这里的医疗隔离。
        suppress=move>=0&&moves[move].immuneReactions&&Finite(damage.cut)&&Finite(damage.blunt)&&Finite(damage.pierce)&&Finite(damage.extraStun);
        if(suppress){Actor& actor=actors.find(self->handle)->second;++actor.stumbles;
            if(IrisDiagnostics::DetailsEnabled()){std::ostringstream out;out<<(RangedMove(move)?"ranged_stumble_guard cast=":"melee_stumble_guard cast=")<<(actor.active&&actor.move==move?actor.id:0)<<" move="<<moves[move].key<<" count="<<actor.stumbles<<" small=immune large=immune medical=unchanged";Log(out.str());}}
    }catch(const std::exception&){suppress=false;}
    // _getHit(false)保留原生退出潜行、deadTime及技巧检查计时；true才安排STUMBLE和反应强度。
    // 离开插件缓存锁后恰好调用一次，不扣第二次血、不回写战斗状态、不强播或重启动作。
    if(suppress){combat->_getHit(dir,damage,attacker,false);return;}
    originalMeleeStumble(self,dir,damage,part,attacker);
}
bool __fastcall MeleeBlockCheckHook(CombatClass* self,float myAttack,float incomingAttack){
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_BLOCK);
    if(!MayNeedTechniqueGuard(self,false))return originalBlockCheck(self,myAttack,incomingAttack);
    bool suppress=false;
    try{Guard guard(&audit);const int move=ProtectedMeleeMove(self);
        // 045：只决定是否跳过主动格挡检查，不能把受击免疫当成主动格挡保护。
        suppress=move>=0&&moves[move].preventBlock;
        if(suppress){Actor& actor=actors.find(self->me->handle)->second;
            // 这是跳过防御评估的次数，不冒称每次都原本会格挡；明细开关开启时持续记录，不再按角色前三次截断。
            if(IrisDiagnostics::DetailsEnabled()){std::ostringstream out;out<<"melee_defence_check_skipped move="<<moves[move].key<<" actor="<<actor.owner.index<<":"<<actor.owner.serial<<" would_block=not_evaluated medical=unchanged";Log(out.str());}}
    }catch(const std::exception&){suppress=false;}
    // 原函数会直接修改战斗状态，因此受保护时在调用前返回false；正常对象原样转交。
    // 不持插件互斥量进入原生检查，不给死亡/昏迷/受击反应增加免疫。
    if(suppress)return false;return originalBlockCheck(self,myAttack,incomingAttack);
}
void InstallDefenceGate(){
    if(originalDefence)return;defenceTLS=TlsAlloc();
    if(defenceTLS==TLS_OUT_OF_INDEXES)throw std::runtime_error("vulcan defence TLS unavailable");
    if(KenshiLib::AddHook(Iris::VulcanDefenceTarget(),reinterpret_cast<void*>(&VulcanDefenceHook),&originalDefence)!=KenshiLib::SUCCESS||!originalDefence)
        throw std::runtime_error("vulcan defence hook unavailable");
    if(KenshiLib::AddHook(Iris::MeleeStumbleTarget(),reinterpret_cast<void*>(&MeleeStumbleHook),&originalMeleeStumble)!=KenshiLib::SUCCESS||!originalMeleeStumble)throw std::runtime_error("melee stumble hook unavailable");
    if(KenshiLib::AddHook(Iris::MeleeBlockCheckTarget(),reinterpret_cast<void*>(&MeleeBlockCheckHook),&originalBlockCheck)!=KenshiLib::SUCCESS||!originalBlockCheck)throw std::runtime_error("melee block check hook unavailable");
    Log(std::string("melee_block_guard_ready build=")+BLOCK_GUARD_CONTRACT+" scope=fire_roll,spiral,earthquake,drill,full_burst,electro_cannon excluded=hammer_combo,ranged private_stop=1 native_damage=1");
    Log(std::string("melee_reaction_guard_ready build=")+REACTION_GUARD_CONTRACT+" scope=fire_roll,spiral,earthquake,drill,full_burst,electro_cannon excluded=hammer_combo ranged=vulcan,pulse,drive small=immune large=immune medical=unchanged death_and_unconscious=native");
    // 046启动诊断必须与实际策略一致，不能继续把火神标成强制命中，误导本次对照测试。
    Log("physical_defence_ready melee_policy=per_move_config ranged_override=0 ranged_moves=vulcan,pulse,drive original_results=preserved armour=native");
}
struct VulcanHitScope {
    void* previous;bool active;
    VulcanHitScope(VulcanHitContext* context):previous(0),active(false){
        if(!context)return;
        if(defenceTLS==TLS_OUT_OF_INDEXES||!originalDefence||!context->combat)throw std::runtime_error("vulcan defence context unavailable");
        previous=TlsGetValue(defenceTLS);if(!TlsSetValue(defenceTLS,context))throw std::runtime_error("vulcan defence scope unavailable");active=true;
    }
    ~VulcanHitScope(){if(active)TlsSetValue(defenceTLS,previous);}
private:VulcanHitScope(const VulcanHitScope&);VulcanHitScope& operator=(const VulcanHitScope&);
};
void DamageOutcome(const Hurt& r,int outcome){
    IrisDiagnostics::Scope outcomeTiming(IrisDiagnostics::DAMAGE_RESULT);
    IrisDiagnostics::Add(outcome<0?IrisDiagnostics::DAMAGE_REJECTED:outcome==int(HIT_MISSED)?IrisDiagnostics::DAMAGE_MISSED:outcome==int(HIT_SWORD)?IrisDiagnostics::DAMAGE_BLOCKED:IrisDiagnostics::DAMAGE_APPLIED);
    Guard guard;StrikeKey key(r.cast,r.event);std::map<StrikeKey,DamageStat>::iterator p=damageStats.find(key);if(p==damageStats.end())return;
    DamageStat& x=p->second;if(outcome<0)++x.rejected;else if(outcome==int(HIT_MISSED))++x.missed;else if(outcome==int(HIT_SWORD))++x.blocked;else ++x.applied;
    if(x.pending)--x.pending;if(!x.pending){std::ostringstream out;out<<"damage_result cast="<<r.cast<<" event="<<r.event<<" move="<<r.move<<" applied="<<x.applied<<" blocked="<<x.blocked<<" missed="<<x.missed<<" rejected="<<x.rejected<<" medical_retry=0";Log(out.str());damageStats.erase(p);}
}
// 061所有退出路径都记录剩余队列；医疗本体仍不持插件锁。压力文本按配置持续，累计数由周期摘要保留。
// 仅记录纯值，不缓存角色/PhysX指针；异常展开也能显示reason=exception，不能误报为成功排空。
struct DamageQueueSnapshot {
    double begin,maxWait,flushMs;size_t before;unsigned done,inspected,overTarget;const char* reason;
    // 083只记录医疗实际读取的状态；queuesClear保持-1表示医疗不依赖此状态，不能伪写成已清空。
    IrisDiagnostics::WindowState gate;double gateAt;const char* gateCause;
    /* 099计划只借当前锁内的FIFO头时间。普通队列不读头、不取新时钟，原短锁直接复用。 */
    IrisMedical::ServicePlan plan;
    DamageQueueSnapshot():begin(IrisDiagnostics::Now()),maxWait(-1),flushMs(0),before(0),done(0),inspected(0),overTarget(0),reason("exception"),gateAt(0),gateCause("unobserved"),plan(damageFlushBudgetMs,damageFlushMaxHits){
        Guard guard;before=hurts.size();
        if(damageCatchupEnabled&&before>damageFlushMaxHits)plan=IrisMedical::SelectService(true,before,begin,hurts.front().queuedAt,
            damageQueueTargetMs,damageFlushBudgetMs,damageFlushMaxHits,damageCatchupBudgetMs,damageCatchupMaxHits);
    }
    ~DamageQueueSnapshot(){
        try{Guard guard;IrisDiagnostics::Set(IrisDiagnostics::PENDING_DAMAGE,hurts.size());
            const size_t after=hurts.size();const double now=IrisDiagnostics::Now();
            if(after&&(!strcmp(reason,"physics_busy")||!strcmp(reason,"ai_busy")||!strcmp(reason,"paused")||!strcmp(reason,"world_missing")))
                IrisDiagnostics::ObserveWindow(!strcmp(reason,"paused"),!strcmp(reason,"physics_busy"),!strcmp(reason,"ai_busy"),!strcmp(reason,"world_missing"));
            if(after){
                if(!strcmp(reason,"time_budget"))IrisDiagnostics::Add(IrisDiagnostics::MEDICAL_TIME_YIELDS);
                else if(!strcmp(reason,"count_budget"))IrisDiagnostics::Add(IrisDiagnostics::MEDICAL_COUNT_YIELDS);
                else if(!strcmp(reason,"scan_budget"))IrisDiagnostics::Add(IrisDiagnostics::MEDICAL_SCAN_YIELDS);
                else if(!strcmp(reason,"physics_busy")||!strcmp(reason,"ai_busy")||!strcmp(reason,"paused")||!strcmp(reason,"world_missing"))IrisDiagnostics::Add(IrisDiagnostics::MEDICAL_SAFETY_YIELDS);
            }
            // FIFO头就是最早入队请求；40ms含暂停的墙钟等待，只报警而不抢跑物理/AI或突破预算。
            const double oldest=after&&hurts.front().queuedAt>0&&now>=hurts.front().queuedAt?now-hurts.front().queuedAt:-1;
            IrisDiagnostics::RecordMedicalWindow(gate,reason,gateCause,before,after,done,inspected,gateAt,oldest);
            // 084仅复用当前退出快照，记录哪一批取得进展；不因此重试、重排或提前结算。
            IrisNativeAudit::Medical(before,after,done,inspected,reason,begin>0&&now>=begin?now-begin:0);
            /* 099只在真实追赶且显式日志门开启时汇总；复用本析构已有now，不加逐目标时钟。
               同根子耗时包含在DAMAGE_FLUSH内；计数记录实际工作，不把扩大额度冒称额外机会。 */
            if(plan.catchup&&IrisDiagnostics::DamageCatchupLoggingEnabled()){
                const double elapsed=begin>0&&now>=begin?now-begin:0;
                IrisDiagnostics::Record(IrisDiagnostics::DAMAGE_CATCHUP_FLUSH,flushMs);
                IrisDiagnostics::Add(IrisDiagnostics::MEDICAL_CATCHUP_WINDOWS);
                IrisDiagnostics::Add(IrisDiagnostics::MEDICAL_CATCHUP_CALLS,done);
                IrisDiagnostics::Add(IrisDiagnostics::MEDICAL_CATCHUP_INSPECTED,inspected);
                if(done>damageFlushMaxHits)IrisDiagnostics::Add(IrisDiagnostics::MEDICAL_CATCHUP_EXTRA_HITS,done-damageFlushMaxHits);
                static unsigned notices=0;static double lastAt=0;
                if(notices<8||now-lastAt>=10000){++notices;lastAt=now;std::ostringstream out;
                    out<<"damage_service_plan contract=IRIS_DAMAGE_CATCHUP_099 catchup=1 queued_before="<<before<<" start_age_ms="<<plan.startAgeMs
                        <<" base_budget_ms="<<damageFlushBudgetMs<<" effective_budget_ms="<<plan.budgetMs<<" base_max_hits="<<damageFlushMaxHits
                        <<" effective_max_hits="<<plan.maxHits<<" native_calls="<<done<<" inspected="<<inspected<<" remaining="<<after
                        <<" elapsed_ms="<<elapsed<<" flush_ms="<<flushMs<<" reason="<<reason<<" gate_cause="<<gateCause<<" notice="<<notices<<" new_service_opportunity=0";Log(out.str());}
            }
            const bool pressure=after||overTarget;
            if(IrisDiagnostics::PerformanceEnabled()&&pressure){
                std::ostringstream out;
                out<<"damage_queue_pressure reason="<<reason<<" queued_before="<<before<<" remaining="<<after<<" native_calls="<<done<<" inspected="<<inspected<<" budget_ms="<<plan.budgetMs<<" base_budget_ms="<<damageFlushBudgetMs<<" catchup="<<plan.catchup<<" start_age_ms="<<plan.startAgeMs<<" elapsed_ms="<<(begin>0&&now>=begin?now-begin:-1)<<" target_wall_ms="<<damageQueueTargetMs<<" oldest_wall_ms="<<oldest<<" max_popped_wait_ms="<<maxWait<<" popped_over_target="<<overTarget<<" max_native_hits="<<plan.maxHits<<" base_max_native_hits="<<damageFlushMaxHits<<" order=FIFO wall_includes_pause=1 target_is_soft=1 no_timeout_drop=1";
                if(IrisDiagnostics::WindowAuditEnabled())out<<std::setprecision(12)<<" gate_cause="<<gateCause<<" gate_physics_running="<<gate.physicsRunning<<" gate_queues_clear="<<gate.queuesClear<<" gate_ai_running="<<gate.aiRunning<<" gate_paused="<<gate.paused<<" gate_at_ms="<<gateAt<<" medical_requires_queues=0 unknown=-1";Log(out.str());
            }
        }catch(const std::exception&){/* 诊断异常不能从医疗退出路径逃出；原生异常由上层既有故障门处理。 */}
    }
};
// 056只观察现有原生受击调用的墙钟，不加新Hook、不持锁进入医疗、不缓存Character。
// 每次慢调用均累计并可记录；不设进程条数限制。阈值和明细开关不影响命中/护甲/经验。
void SlowNativeHit(const Hurt& r,double poppedAt,double begin,double elapsed,HitMaterialType result,unsigned ordinal,bool unavoidable,bool defenceSeen){
    if(!IrisDiagnostics::DetailsEnabled()||begin<=0||elapsed<nativeHitSlowMs)return;
    IrisDiagnostics::Add(IrisDiagnostics::NATIVE_SLOW_HITS);IrisDiagnostics::Add(IrisDiagnostics::NATIVE_SLOW_NOTICES);
    std::ostringstream out;out<<"native_hit_slow cast="<<r.cast<<" event="<<r.event<<" move="<<moves[r.move].key<<" target="<<unsigned(r.victim.type)<<":"<<r.victim.container<<":"<<r.victim.containerSerial<<":"<<r.victim.index<<":"<<r.victim.serial
       <<" caster="<<unsigned(r.caster.type)<<":"<<r.caster.container<<":"<<r.caster.containerSerial<<":"<<r.caster.index<<":"<<r.caster.serial
       <<" native_wall_ms="<<elapsed<<" threshold_ms="<<nativeHitSlowMs<<" queue_wall_ms="<<(r.queuedAt>0&&poppedAt>=r.queuedAt?poppedAt-r.queuedAt:-1)<<" pre_native_ms="<<(begin>=poppedAt?begin-poppedAt:-1)<<" flush_ordinal="<<ordinal<<" mult="<<r.mult<<" result="<<int(result)<<" bypass="<<unavoidable<<" defence_seen="<<defenceSeen<<" calls=1 internal_cause=unconfirmed FPS_measured=0";Log(out.str());
}
IrisDiagnostics::Count PendingDamageForAudit(){Guard guard;return IrisDiagnostics::Count(hurts.size());}
void Flush(GameWorld* w){
    /* 099普通批使用INI实际预算/笔数；仅在追赶启用且旧积压超过目标/普通次数时选择追赶计划。
       仍只由原charsUpdateUT安全回调进入；每笔原生状态重查/锁外受击/原FIFO保持。
       调整的是同一安全机会的有界吞吐量，不绕过引擎物理节拍、不添加渲染帧医疗。 */
    IrisDiagnostics::WorkTrace workTrace(IrisDiagnostics::WORK_MEDICAL);
    DamageQueueSnapshot queueSnapshot;
    /* 099追赶子计时借原Scope的相同起止值；普通批/关闭新日志传空指针，
       没有额外QPC。析构前该Scope先结束，子统计不能把Snapshot诊断开销混入父项。 */
    IrisDiagnostics::Scope timing(IrisDiagnostics::DAMAGE_FLUSH,0,
        queueSnapshot.plan.catchup&&IrisDiagnostics::DamageCatchupLoggingEnabled()?&queueSnapshot.flushMs:0);
    // 医疗触发其他插件/AI时不得持插件互斥锁；只用短锁按FIFO弹出一条值请求。
    /* 本次计划的软预算在每次取出前检查：已开始的单次原生调用不能抢占。 */
    // 无效请求也消耗检查预算，避免大量失效目标在continue分支绕过时间门；QPC不可用时仍有次数/256扫描上限。
    while(queueSnapshot.done<queueSnapshot.plan.maxHits&&queueSnapshot.inspected<256){
        workTrace.Mark(IrisDiagnostics::WORK_MEDICAL_SAFETY);
        const double now=IrisDiagnostics::Now();
        if(queueSnapshot.inspected&&queueSnapshot.begin>0&&now>=queueSnapshot.begin&&now-queueSnapshot.begin>=queueSnapshot.plan.budgetMs){queueSnapshot.gateCause="time_budget";queueSnapshot.reason="time_budget";return;}
        // 083：这里只结算已完成碰撞并保存稳定身份的请求，不再等待全局物理消息全部清空。
        // 原生updateUT刚移交后台的新建/销毁/地形消息也会使queuesAreClearMT为假，并不表示线程正在运行。
        // 100查询端另设实际空消息及SDK状态门；医疗每笔重查世界/物理/AI/暂停，原生受击重入后下一笔不能沿用旧许可。
        queueSnapshot.gate=IrisDiagnostics::WindowState();queueSnapshot.gateAt=now;
        if(!w||!w->physics){queueSnapshot.gate.unavailable=1;queueSnapshot.gateCause="world_missing";queueSnapshot.reason="world_missing";return;}
        if(!w->initialized||w->gameResetting||w->isLoadingFromASaveGame()){queueSnapshot.gate.unavailable=1;queueSnapshot.gateCause="world_invalid";queueSnapshot.reason="world_missing";return;}
        queueSnapshot.gate.unavailable=0;
        const bool physicsRunning=w->physics->isRunning();queueSnapshot.gate.physicsRunning=physicsRunning?1:0;
        if(physicsRunning){queueSnapshot.gateCause="physics_running";queueSnapshot.reason="physics_busy";return;}
        ThreadWannabe* ai=w->AINonRenderThread();const bool aiBusy=ai&&ai->isRunning();queueSnapshot.gate.aiRunning=aiBusy?1:0;
        if(aiBusy){queueSnapshot.gateCause="ai_running";queueSnapshot.reason="ai_busy";return;}
        queueSnapshot.gateCause="ready";
        workTrace.Mark(IrisDiagnostics::WORK_MEDICAL_POP);
        Hurt r;{Guard guard;const bool paused=w->isPaused();queueSnapshot.gate.paused=paused?1:0;if(paused){queueSnapshot.gateCause="paused";queueSnapshot.reason="paused";return;}if(hurts.empty()){queueSnapshot.gateCause="empty";queueSnapshot.reason="empty";return;}
            r=hurts.front();hurts.pop_front();++queueSnapshot.inspected;if(r.generation!=epoch){IrisDiagnostics::Add(IrisDiagnostics::STALE_DAMAGE);continue;}}
        workTrace.Mark(IrisDiagnostics::WORK_MEDICAL_WAIT);
        const double poppedAt=IrisDiagnostics::Now();
        if(r.queuedAt>0&&poppedAt>=r.queuedAt){const double age=poppedAt-r.queuedAt;queueSnapshot.maxWait=std::max(queueSnapshot.maxWait,age);IrisDiagnostics::Record(IrisDiagnostics::DAMAGE_WAIT,age);IrisDiagnostics::RecordWait(false,r.queuedAt,r.waits,poppedAt);
            if(age>=damageQueueTargetMs){++queueSnapshot.overTarget;IrisDiagnostics::Add(IrisDiagnostics::DAMAGE_OVER_TARGET);}}
        // 下面重查本次原生四项资格，再进入原生伤害、护甲和经验链；超40ms有效请求仍只结算一次。
        workTrace.Mark(IrisDiagnostics::WORK_MEDICAL_IDENTITY);
        Character* caster=0;Character* victim=0;bool eligible=false;const char* eligibilityReason="not_checked";
        {IrisDiagnostics::Scope identityTiming(IrisDiagnostics::DAMAGE_IDENTITY);caster=r.caster.getCharacter();victim=r.victim.getCharacter();eligible=CanDamage(caster,victim,RangedMove(r.move),&eligibilityReason)&&caster->stats&&damageEnabled;
            if(caster&&!caster->stats)eligibilityReason="caster_stats_missing";}
        if(!eligible){workTrace.Mark(IrisDiagnostics::WORK_MEDICAL_RESULT);if(IrisDiagnostics::DetailsEnabled()){std::ostringstream out;out<<"damage_rejected cast="<<r.cast<<" event="<<r.event<<" move="<<r.move<<" target="<<r.victim.index<<":"<<r.victim.serial<<" direct="<<r.direct<<" reason="<<(damageEnabled?eligibilityReason:"damage_disabled");Log(out.str());}DamageOutcome(r,-1);continue;}
        // 单一原生受击入口负责护甲、部位、流血和反应，不手写health、不同时addWound/_getHit二次结算。
        // 不额外构造或缓存Damages：目标相关原生计算和乘法保持原样，仅明细开关开启时取两次时钟。
        workTrace.Mark(IrisDiagnostics::WORK_MEDICAL_CALCULATE);
        const bool detail=IrisDiagnostics::DetailsEnabled();const double calculateBegin=detail?IrisDiagnostics::Now():0;
        Damages damage=caster->stats->getTotalAttackDamageFor(victim);damage.multiply(r.mult);
        if(detail)IrisDiagnostics::Record(IrisDiagnostics::DAMAGE_CALCULATE,std::max(0.0,IrisDiagnostics::Now()-calculateBegin));
        if(!Finite(damage.total())||damage.total()<=0){workTrace.Mark(IrisDiagnostics::WORK_MEDICAL_RESULT);if(IrisDiagnostics::DetailsEnabled()){std::ostringstream out;out<<"damage_rejected cast="<<r.cast<<" event="<<r.event<<" move="<<r.move<<" direct="<<r.direct<<" reason=nonpositive_or_invalid_damage";Log(out.str());}DamageOutcome(r,-1);continue;}
        // 近战按配置决定本次物理命中是否破防；046三远程一律保留原链返回值，供玩家对照测试。
        // 单次TLS绑定combat+damage+caster，其他招式/角色转发原生；护甲、部位、医疗与经验不绕过。
        // 仍只进入一次原生受击/护甲/医疗，TLS不包住经验回调；未观察到原生门时不补扣伤害。
        // 配置仅改变已经物理命中的这一次原生防御决策；护甲、部位、医疗和敌我保护保持原生。
        // 消费端再次排除远程，即使缓存/配置以后扩展，也不能把本次测试策略意外加回。
        // 日志的护甲前总量必须在原生受击可能改写Damages之前快照，不将提交量冒称实际扣血量。
        workTrace.Mark(IrisDiagnostics::WORK_MEDICAL_NATIVE);
        const float submittedTotal=damage.total();
        const bool unavoidable=!RangedMove(r.move)&&moves[r.move].bypassDefence;VulcanHitContext context(victim->getCombatClass(),&damage,caster);HitMaterialType result;
        const double nativeBegin=detail?IrisDiagnostics::Now():0;
        {IrisDiagnostics::Scope nativeTiming(IrisDiagnostics::NATIVE_DAMAGE);VulcanHitScope scope(unavoidable?&context:0);IrisNativeAudit::Hit nativeProfile(r.cast,r.event,r.move,queueSnapshot.done+1);result=victim->_NV_hitByMeleeAttack(CUT_DEFAULT,damage,caster,moves[r.move].technique,0);}
        const double nativeElapsed=detail?std::max(0.0,IrisDiagnostics::Now()-nativeBegin):0;
        // 原生可因目标刚失效等原因在防御门前返回。不得重放医疗、猜测补血伤害，也不能永久关闭其他攻击。
        if(unavoidable&&!context.seen&&IrisDiagnostics::DetailsEnabled()){std::ostringstream out;out<<"native_defence_not_observed cast="<<r.cast<<" move="<<r.move<<" event="<<r.event<<" result="<<int(result)<<" medical_retry=0 other_events_continue=1";Log(out.str());}
        workTrace.Mark(IrisDiagnostics::WORK_MEDICAL_XP);
        {IrisDiagnostics::Scope xpTiming(IrisDiagnostics::DAMAGE_XP);caster=r.caster.getCharacter();victim=r.victim.getCharacter();if(caster&&victim&&caster->isValid()&&victim->isValid()&&caster->stats){CharStats::DeadTimeState outcome=result==HIT_MISSED?CharStats::ATTACK_MISSED:result==HIT_SWORD?CharStats::ATTACK_WAS_BLOCKED:CharStats::ATTACK_HIT;caster->stats->xpMelee(outcome,victim,damage);}}
        workTrace.Mark(IrisDiagnostics::WORK_MEDICAL_RESULT);
        DamageOutcome(r,int(result));
        if(detail)SlowNativeHit(r,poppedAt,nativeBegin,nativeElapsed,result,queueSnapshot.done+1,unavoidable,context.seen);
        if(IrisDiagnostics::DetailsEnabled()){std::ostringstream o;o<<"native_hit cast="<<r.cast<<" event="<<r.event<<" move="<<r.move<<" target="<<r.victim.index<<":"<<r.victim.serial<<" mult="<<r.mult<<" result="<<int(result)<<" direct="<<r.direct<<" damage_total_pre_armour="<<submittedTotal<<" target_policy=native_melee_four_checks armour=native defence="<<(unavoidable?"physical_no_block_no_dodge":"native")<<" original_defence="<<(unavoidable?int(context.original):-1);Log(o.str());}
        ++queueSnapshot.done;
    }
    queueSnapshot.reason=queueSnapshot.done>=queueSnapshot.plan.maxHits?"count_budget":"scan_budget";
    {Guard guard;if(hurts.empty())queueSnapshot.reason="empty";
    }
    queueSnapshot.gateCause=queueSnapshot.reason;
}
}
