#pragma once
/* 085：只记录当前线程addWound子树的纯值，普通受击与Iris桥接同口径，不写引擎状态。 */
#include "IrisDiagnostics.h"
class Damages;
namespace IrisWoundAudit {
/* 086四个原阶段后追加六个医疗分支；保持固定栈空间，无对象缓存或异步医疗。 */
enum {STAGE_COUNT=10};
class Part;
class Scope {
    friend class Part;
    bool active,bridge;unsigned generation,nested,mixed;
    double begin,amount,inclusive[STAGE_COUNT],exclusive[STAGE_COUNT];unsigned calls[STAGE_COUNT];Part* top;
public:
    Scope(bool irisBridge,const Damages& damage);~Scope();
private:Scope(const Scope&);Scope& operator=(const Scope&);
};
bool Enabled();void Configure(bool enabled,bool branches);void Install(bool woundHookAvailable);
void Reset();void Summary(IrisDiagnostics::Count id);
}
