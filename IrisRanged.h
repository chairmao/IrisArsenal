#pragma once
// 同一件锤枪的原生远程能力适配：不制造库存弩，不改Sword对象类型；原生AI/计时拥有远程流程。
#include <kenshi/util/hand.h>
#include <string>
#include <ogre/OgreVector3.h>
class Character;class GameWorld;
namespace IrisRanged {
enum Binding {USE_RANGED,HAS_RANGED,SCORE_RANGED,WITHIN_RANGE,GET_GUN,ANIMATION,SHOOT,RELOAD,BINDING_COUNT};
// 启动读取非负、有限的原生装填单位；改INI后重启生效。
void Configure(const std::wstring& directory);
void Install();
// Prepare/Publish/TakeRequest只从AI与物理停止的主线程调用；回调仅发布稳定句柄和普通值。
void Prepare(GameWorld* world);
void Publish(Character* actor,bool ready,float maxRange,const Ogre::Vector3& muzzle);
// 062世界坐标纯值：默认只读原生瞄准值；实际发射才按速度重算getAimPos，光炮取同源即时身体点。
// 只在已有AI/物理静止主线程调用CaptureAim；回调继续读Gun，不跨线程保存骨骼/Character指针。
struct AimFrame {
    Ogre::Vector3 muzzle,point,direction;hand target;unsigned sequence;float effectiveSpeed;bool instant;const char* source;
    AimFrame():muzzle(Ogre::Vector3::ZERO),point(Ogre::Vector3::ZERO),direction(Ogre::Vector3::UNIT_Z),sequence(0),effectiveSpeed(0),instant(false),source("native_currentAimPos"){}
};
// 062默认只读原生currentAimPos；真正Emit才指定实际弹速/即时模型，不能成为额外起手条件。
bool CaptureAim(Character* actor,const Ogre::Vector3& actualMuzzle,AimFrame& frame,float effectiveShotSpeed=0,bool instant=false);
bool TakeRequest(Character* actor,hand& target);
void Finish(const hand& actor);
bool Active(Character* actor);
bool Tracked(Character* actor);
void Reset();
}
