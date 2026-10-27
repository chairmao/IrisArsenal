#pragma once
// 十招消费者只在原生AI/物理静止窗口更新。FCS播身体/根位移；本单元持有特效和按事件去重的伤害。
#include <string>
#include "IrisDiagnostics.h"
class Character;class GameWorld;class CharStats;class CombatTechniqueData;class AnimationClass;
namespace Ogre {class SceneManager;}
namespace IrisCombat {
// 安装限定物理伤害防御门，以及六招近战的格挡接管/小僵直/大踉跄反应门。
// 普通三连击保留原生防御/受击反应；三远程保留原生防御返回值，但可配置受击反应保护。
// 保护只覆盖当前原生动作窗口；伤害、死亡、昏迷仍走原生。
void InstallDefenceGate();
void Configure(const std::wstring& directory);
bool ProofOnly();
// 076：只比较原子发布的进程期私有技巧身份；不解引用技巧、不读取角色缓存，也不授予动作资格。
// 正式技巧与诊断原型在完整初始化、首次交给原生前发布；读档保留技巧身份，原角色状态照常清理。
bool OwnTechniqueIdentity(CombatTechniqueData* technique);
void PublishProofTechniqueIdentity(CombatTechniqueData* technique);
// 原生远程回调只发现能力；安全阶段按FCS范围/INI权重选择火神、脉冲或极致驱动。
// 061复用原生四项资格：盟友排除、真实昏迷排除、isEnemy(true)或当前主动目标；仅借当前调用指针。
// AI回调只读原生关系/目标，禁止在此访问Ogre/PhysX或插件容器；近远程选择各自的原生当前目标。
bool CanDamage(Character* caster,Character* victim,bool ranged,const char** reason=0);
bool HasRangedMoves();
float RangedRange();
void Observe(Character* actor);
void Tick(GameWorld* world,Ogre::SceneManager* scene,float gameDelta);
void Clear(bool sceneAlive,const char* reason);
CombatTechniqueData* Choose(CharStats* stats,float range);
float Speed(AnimationClass* animation,CombatTechniqueData* technique,float speed);
void Started(AnimationClass* animation,CombatTechniqueData* technique);
// 医疗/AI回调必须在插件锁之外；内部每批重新验证世界代数、敌我、稳定句柄，不重试已调用医疗的请求。
void Flush(GameWorld* world);
// 084仅诊断显式开启时读取插件自己的队列数量；调用内取原短锁，不返回目标/物理指针。
IrisDiagnostics::Count PendingDamageForAudit();
}
