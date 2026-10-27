#pragma once
/* 100查询精细门的纯值规则；不保存引擎地址，不读取时钟/容器，不分配、不同步。
   位0..15依次为八类消息的主/后台，位16为门任务；任何非空或未知位均拒绝。
   只有旧门false的分支使用本规则；原门true不增加检查。 */
namespace IrisQueryGate {
enum Source {SINGLE,CAPSULE_BATCH,RANGED_BATCH,SOURCE_COUNT};
enum Reason {ALLOW,DISABLED,WORLD_INVALID,WORKER_BUSY,BAD_QUEUE,PENDING_CREATE,PENDING_DESTROY,
    PENDING_TERRAIN,PENDING_OTHER,SDK_NOT_WRITABLE,SDK_UNAVAILABLE,SDK_ERROR,SCENE_CHANGED,REASON_COUNT};
const unsigned QUEUE_BITS=17;
const unsigned ALL_MASK=(1U<<QUEUE_BITS)-1U;
inline Reason PendingReason(unsigned mask,bool invalid){
    if(invalid||(mask&~ALL_MASK))return BAD_QUEUE;
    if(mask&0x3cU)return PENDING_DESTROY;
    if(mask&0xc0U)return PENDING_TERRAIN;
    if(mask&3U)return PENDING_CREATE;
    if(mask)return PENDING_OTHER;
    return ALLOW;
}
}
