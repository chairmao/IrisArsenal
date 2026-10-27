#pragma once
#include <cstddef>
#include <float.h>
/* 099只计算本次服务额度，不保存角色/世界指针，不读时钟，不加锁或分配内存。
   原生安全窗口仍由调用者选择；提高额度不代表可以跨过物理/AI/暂停/读档门。 */
namespace IrisMedical {
struct ServicePlan {
    double budgetMs,startAgeMs;unsigned maxHits;bool catchup;
    ServicePlan(double budget,unsigned hits):budgetMs(budget),startAgeMs(-1),maxHits(hits),catchup(false){}
};
/* 普通队列或关闭功能首先返回：轻负载只增加常数分支，不读FIFO头或调用引擎。
   只有队列超原次数上限且最老请求已达到原40ms目标才追赶；更早处理不重排FIFO。
   103：预算/次数直接采用INI请求，不再钳制为两倍/10ms/256次；仍只在高于普通额度时追赶。
   原调用者256项扫描和逐笔安全检查保持。单次原生受击不可抢占，预算是软上限。 */
inline ServicePlan SelectService(bool enabled,std::size_t queued,double now,double oldest,
    double targetMs,double baseMs,unsigned baseHits,double requestedMs,unsigned requestedHits){
    ServicePlan plan(baseMs,baseHits);
    if(!enabled||queued<=baseHits)return plan;
    if(!_finite(now)||!_finite(oldest)||!_finite(targetMs)||oldest<=0||now<oldest)return plan;
    plan.startAgeMs=now-oldest;if(plan.startAgeMs<targetMs)return plan;
    if(_finite(requestedMs)&&requestedMs>baseMs)plan.budgetMs=requestedMs;
    if(requestedHits>baseHits)plan.maxHits=requestedHits;
    plan.catchup=plan.budgetMs>baseMs||plan.maxHits>baseHits;return plan;
}
}
