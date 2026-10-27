#pragma once
// 084：纯观察原生同步子树与主线程服务机会，不授予许可、不持有引擎对象、不调度伤害。
#include "IrisDiagnostics.h"
namespace IrisNativeAudit {
typedef IrisDiagnostics::Count Count;
enum Part {DEFENCE,WOUND,REACTION,EFFECT,PART_COUNT};
// 091间隙跟踪复用已有PartScope时间戳，不加引擎Hook；N只影响观察采样，不影响原生调用。
void Configure(bool nativeProfile,bool serviceProfile,bool gapProfile,unsigned sampleEvery);
void Install();bool Enabled();bool ServiceEnabled();void Reset();void Summary(Count id);
class PartScope;
class Hit {
    friend class PartScope;
    bool active;unsigned generation,cast,event,move,ordinal,nested;
    double begin,inclusive[PART_COUNT],exclusive[PART_COUNT];unsigned calls[PART_COUNT];PartScope* top;
    // 只借用本次同步栈，按顶层已知探针之间的空白归属“下一探针前/最后探针后”，不猜函数名。
    bool gapActive;double gapCursor,gaps[PART_COUNT+1];
public:
    Hit(unsigned castId,unsigned eventId,unsigned moveIndex,unsigned flushOrdinal);~Hit();
private:Hit(const Hit&);Hit& operator=(const Hit&);
};
class PartScope {
    friend class Hit;
    Hit* hit;PartScope* previous;Part part;double begin,children;
public:
    explicit PartScope(Part value);~PartScope();
private:PartScope(const PartScope&);PartScope& operator=(const PartScope&);
};
// Frame只拥有值；TLS按调用栈保存前驱，嵌套帧退出恢复，读档只变代数、不释放正在借用的栈地址。
class Frame {
    friend void Callback(bool,Count,const IrisDiagnostics::WindowState&,double);
    friend void Medical(Count,Count,unsigned,unsigned,const char*,double);
    Frame* previous;bool active,finished,sawPending;unsigned generation;
    Count token,callbacks,repeated,waiting,repeatReady,flushes,progress,nativeCalls,inspected;
    double begin;
public:
    explicit Frame(Count actualFrameToken);~Frame();void Finish();
private:Frame(const Frame&);Frame& operator=(const Frame&);
};
void Callback(bool alreadyUpdated,Count pending,const IrisDiagnostics::WindowState& observed,double probeMs);
void Medical(Count before,Count remaining,unsigned nativeCalls,unsigned inspected,const char* reason,double elapsedMs);
}
