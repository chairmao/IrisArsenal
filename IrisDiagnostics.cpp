// 104：日志身份与新源码版本一致；旧DLL身份不由此文件改写。
// 052：参照Ephnel的进程/窗口审计，保留本项目独立边界；不采样FPS/显存，不合并不同运行。
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>
#include <winver.h>
#include "IrisDiagnostics.h"
#include "native/QueryGate.h"
#include "native/IniValues.h"
#include "IrisNativeAudit.h"
#include "IrisWoundAudit.h"
#include <Debug.h>
#include <sstream>
#include <iomanip>
#include <stdexcept>
#include <exception>
#include <algorithm>
#include <cmath>
#include <float.h>
#include <cstdio>
#include <cwchar>
#include <vector>
#include <fstream>
#include <cstring>
namespace Iris {extern CRITICAL_SECTION mutex;}
namespace IrisDiagnostics {
struct Guard {Guard(){EnterCriticalSection(&Iris::mutex);}~Guard(){LeaveCriticalSection(&Iris::mutex);}};
static bool enabled=true,performance=true,resource=true,details=true,initialized=false,frameOpen=false;
// 087配置启动后只读；缺项0，关闭不做新增QPC/计数/锁操作，不改变实际战斗消费者。
static bool collisionProfile=false;
// 094只控制诊断，不控制保守近似功能；启动读取后只读。
static bool conservativeQueryLogging=false;
/* 099启动只读；诊断与调度功能分离，正常模式不执行影子医疗或额外查询。 */
static bool damageCatchupLogging=false;
/* 100功能/日志独立；启动后只读，正常旧门通过不进入新观察。 */
static bool queryGateLogging=false;
// 091启动后只读；采样计数仅本插件Tick/Flush，不经过普通角色Hook或额外扫描角色。
static bool workTraceEnabled=false;static unsigned workTraceEvery=32;
static volatile LONG workTraceSequence[WORK_DOMAIN_COUNT]={0,0};

// 092开关启动后只读；TLS只在显式深度监视开启时分配，进程期不释放，不增加引擎Hook。
static bool interfaceOption=false,probeCostOption=false,probeABOption=false,queryBoundaryOption=false;
static DWORD interfaceTLS=TLS_OUT_OF_INDEXES;static volatile LONG interfaceGeneration=0,interfaceTLSFailures=0,probeTrialSequence=0;
static double interfaceSlowMs=2,lastInterfaceSlow=0;static Count interfaceNotices=0;
static double frequency=0,summarySeconds=60,slowMs=8,processBegin=0,windowBegin=0;
static DWORD flushMillis=2000,lastFlush=0;static std::wstring filename;static std::string pending;
static bool summaryPending=false;static std::string pendingReason;
static Count summaryId=0,frameId=0,droppedBytes=0;static unsigned ioFailures=0;
// 080新增可视更新耗时/省略工作计数，只在既有摘要输出；不增加日志线程或原生Hook。
// 097新增名称与头文件尾部枚举一一对应，扇形计时沿用CollisionProfile父门。
// 098钻头球为sphere子统计；汇总按既有开关输出，未增加每形体时钟或文件IO。
static const char* names[KIND_COUNT]={"safe_tick","combat_tick","sphere","sweep","capsule","cylinder","damage_flush","native_damage","damage_queue_age","resource_group","visual_create","material_load","prewarm","asset_read","proof_query","log_flush","query_job_age","query_ready_wait","query_paused_wait","query_physics_wait","query_ai_wait","query_unavailable_wait","medical_ready_wait","medical_paused_wait","medical_physics_wait","medical_ai_wait","medical_unavailable_wait","damage_identity","damage_calculate","damage_xp_revalidate","damage_result","query_jobs","capsule_batch","capsule_batch_reference","visual_update","native_terrain_ray","native_sphere_sweep","sweep_result_finalize","capsule_candidates","capsule_exact","capsule_results","contact_collect","ranged_filter","path_build","damage_enqueue","attachment_update","trail_update","ranged_batch","ranged_batch_create","ranged_batch_rays","ranged_batch_bodies","ranged_batch_release","ranged_reuse_lookup","ranged_empty_probe","ranged_spatial_build","capsule_conservative_box_tests","sector_native_cull","drill_sphere_query","damage_catchup_flush","query_gate_refine"};
// 081只在既有摘要追加异常形体总数；不增加逐形体文件IO或线程。
static const char* counters[COUNTER_COUNT]={"safe_frames","frame_callbacks","unsafe_skips","query_calls","query_cache","query_retry","query_busy_wait","query_budget_wait","raw_shapes","contacts","initial_overlap_recovered","query_overflow","events_emitted","damage_queued","damage_applied","damage_blocked","damage_missed","damage_rejected","stale_damage","casts_started","casts_ended","fresh_visuals","pool_reuses","visual_dispose_attempts","damage_over_target","medical_time_yields","medical_count_yields","medical_safety_yields","medical_scan_yields","identity_comparisons","identity_probes","identity_duplicates","identity_tables","cylinder_buffer_growth","job_transfers","job_rotations","capsule_cache","capsule_batch_attempts","capsule_batch_successes","capsule_batch_fallbacks","capsule_batch_shadows","capsule_batch_matches","capsule_batch_mismatches","capsule_batch_candidates","capsule_batch_shape_tests","capsule_batch_logical_charge","capsule_batch_saved_calls","native_slow_hits","native_slow_notices","capsule_batch_no_headroom","capsule_batch_extra_calls","projectile_wall_skips","ranged_contact_checks","ranged_contact_reuses","visual_parameter_writes","visual_parameter_reuses","capsule_batch_skipped_identity","capsule_batch_skipped_geometry","sweep_shape_comparisons","sweep_shape_probes","sweep_shape_linear_equivalent","sweep_shape_tables","sweep_shape_index_fallbacks","ranged_memo_collisions","collect_contacts","collect_already_accepted","collect_policy_checks","collect_inserted","paths_built","curve_sample_reuses","terrain_ray_raw","sphere_sweep_raw","sweep_sorted_contacts","capsule_batch_eligible","capsule_batch_local_reservations","capsule_batch_local_blocked","ranged_batch_attempts","ranged_batch_items","ranged_batch_rays","ranged_batch_sweeps","ranged_batch_cylinders","ranged_batch_unavailable","ranged_batch_failures","ranged_batch_unused","ranged_exact_reuses","ranged_reuse_failures","ranged_empty_probes","ranged_empty_candidates","ranged_empty_characters","ranged_empty_unknown","ranged_empty_paths","ranged_empty_saved_sweeps","ranged_empty_busy","ranged_empty_no_headroom","ranged_empty_sparse","ranged_empty_small","ranged_empty_invalid","ranged_empty_window_disabled","ranged_empty_shadow_checks","ranged_empty_shadow_mismatches","ranged_spatial_batches","ranged_spatial_groups","ranged_spatial_merges","ranged_spatial_pair_tests","ranged_spatial_single_groups","ranged_spatial_multi_groups","ranged_spatial_covered_paths","ranged_spatial_skipped_singles","ranged_spatial_empty_singles","ranged_spatial_empty_multis","projectile_spawns","projectile_vector_growth","projectile_unvisited_updates","idle_pool_trims","parameter_cache_fallbacks","weapon_count_reuse_lookups","weapon_count_legacy_lookups","weapon_child_visits","approx_sphere_queries","approx_capsule_queries","approx_cylinder_queries","approx_capsule_batches","approx_raw","approx_contacts","approx_box_tests","approx_skipped_identity","approx_skipped_geometry","approx_skipped_capacity","approx_skipped_input","sector_volumes_built","sector_native_requests","sector_planes_submitted","sector_raw","sector_unique_contacts","drill_sphere_requests","drill_sphere_raw","drill_sphere_contacts","drill_sphere_cache","medical_catchup_windows","medical_catchup_calls","medical_catchup_inspected","medical_catchup_extra_hits","query_gate_single_old_false","query_gate_capsule_old_false","query_gate_ranged_old_false","query_gate_allow","query_gate_disabled","query_gate_world_invalid","query_gate_worker_busy","query_gate_bad_queue","query_gate_pending_create","query_gate_pending_destroy","query_gate_pending_terrain","query_gate_pending_other","query_gate_sdk_not_writable","query_gate_sdk_unavailable","query_gate_sdk_error","query_gate_scene_changed","query_gate_mask_create_main","query_gate_mask_create_back","query_gate_mask_hull_destroy_main","query_gate_mask_hull_destroy_back","query_gate_mask_actor_destroy_main","query_gate_mask_actor_destroy_back","query_gate_mask_terrain_main","query_gate_mask_terrain_back","query_gate_mask_group_main","query_gate_mask_group_back","query_gate_mask_impulse_main","query_gate_mask_impulse_back","query_gate_mask_tracer_add_main","query_gate_mask_tracer_add_back","query_gate_mask_tracer_remove_main","query_gate_mask_tracer_remove_back","query_gate_mask_door"};
static const char* gauges[GAUGE_COUNT]={"actors","active","reserved","projectiles","residues","idle_visuals","attached_visuals","jobs","pending_damage","warm_assets","retired_guns"};
// 16桶为毫秒上界，末桶无有限上界。分位数输出上界，绝不把它称作精确p99或FPS。
static const double bounds[15]={0,.01,.025,.05,.1,.25,.5,1,2,4,8,16,32,64,128};
struct Stats {
    Count calls,frames,activeFrames,buckets[16];double ms,maxCall,frameMax;
    Stats():calls(0),frames(0),activeFrames(0),ms(0),maxCall(0),frameMax(0){for(unsigned i=0;i<16;++i)buckets[i]=0;}
    void Sample(double value){++calls;ms+=value;maxCall=std::max(maxCall,value);}
    void Frame(double value){++frames;if(value>0)++activeFrames;frameMax=std::max(frameMax,value);unsigned b=0;while(b<15&&value>bounds[b])++b;++buckets[b];}
    double Percentile(unsigned percent)const {if(!frames)return 0;Count target=(frames*percent+99)/100,sum=0;for(unsigned i=0;i<16;++i){sum+=buckets[i];if(sum>=target)return i<15?bounds[i]:-1;}return -1;}
};
// 092每次战斗根调用结束只合计一次；所有接口都只借当前TLS栈，不跨帧缓存，不在子接口拿统计锁。
static bool InterfaceEnabled(){return interfaceOption&&DetailsEnabled()&&interfaceTLS!=TLS_OUT_OF_INDEXES;}
static void* InterfaceTLSRead(){DWORD saved=GetLastError();void* p=TlsGetValue(interfaceTLS);SetLastError(saved);return p;}
static bool InterfaceTLSWrite(void* p){DWORD saved=GetLastError();bool ok=TlsSetValue(interfaceTLS,p)!=0;if(!ok)InterlockedIncrement(&interfaceTLSFailures);SetLastError(saved);return ok;}
static unsigned InterfaceGeneration(){return unsigned(InterlockedCompareExchange(&interfaceGeneration,0,0));}
static const char* interfaceNames[IF_PART_COUNT]={"root_unwrapped","wrapper","setup","actor_ready","actor_request","actor_animation",
    "actor_pose","actor_finish","tail","weapon_lookup","source_pose","attachments","trail","blade_paths",
    "emit","blast","pool_borrow","pool_return","visual","visual_node","visual_parameters","visibility",
    "effects","shot_batch_prepare","shot_consume","shot_terminate","residues","jobs","contact_gate",
    "contact_collect","damage_enqueue","job_rotate","blade_ledger","beam_draw","physics","resource_lifecycle","prewarm","diagnostics",
    "ready_animation_scan","weapon_attachment_scan","query_submit","query_execute","query_finish","query_report","query_narrow_recovery"};
struct InterfaceStats {
    Stats total,inclusive[IF_PART_COUNT],exclusive[IF_PART_COUNT];Count calls[IF_PART_COUNT],invalid,nested,exceptions;double maxCall[IF_PART_COUNT];
    InterfaceStats():invalid(0),nested(0),exceptions(0){for(unsigned i=0;i<IF_PART_COUNT;++i){calls[i]=0;maxCall[i]=0;}}
};
static InterfaceStats interfaceRun,interfaceWindow;
CombatInterfaceFrame::CombatInterfaceFrame():active(false),sealed(false),generation(0),nested(0),badClocks(0),token(0),begin(0),endedAt(0),top(0){
    if(!InterfaceEnabled())return;const DWORD saved=GetLastError();
    CombatInterfaceFrame* parent=static_cast<CombatInterfaceFrame*>(InterfaceTLSRead());
    if(parent){++parent->nested;SetLastError(saved);return;}
    // 不另取根时钟：紧接着的原COMBAT_TICK Scope把其已有起止值借给本根，同一父边界闭合。
    generation=InterfaceGeneration();token=frameId;
    for(unsigned i=0;i<IF_PART_COUNT;++i){inclusive[i]=exclusive[i]=maxCall[i]=0;calls[i]=0;}
    active=InterfaceTLSWrite(this);SetLastError(saved);
}
CombatInterfaceFrame::~CombatInterfaceFrame(){
    if(!active)return;const DWORD saved=GetLastError();const double end=endedAt>0?endedAt:Now();InterfaceTLSWrite(0);
    try{Guard guard;InterfaceStats* rows[2]={&interfaceRun,&interfaceWindow};
        const double elapsed=end-begin;
        if(generation!=InterfaceGeneration()||badClocks||top||!sealed||begin<=0||!_finite(elapsed)||elapsed<0){
            for(unsigned r=0;r<2;++r)++rows[r]->invalid;
        }else{
            double accounted=0;for(unsigned i=1;i<IF_PART_COUNT;++i)accounted+=exclusive[i];
            inclusive[IF_ROOT]=elapsed;exclusive[IF_ROOT]=std::max(0.0,elapsed-accounted);calls[IF_ROOT]=1;maxCall[IF_ROOT]=elapsed;
            for(unsigned r=0;r<2;++r){InterfaceStats& s=*rows[r];s.total.Sample(elapsed);s.total.Frame(elapsed);s.nested+=nested;
                if(std::uncaught_exception())++s.exceptions;
                for(unsigned i=0;i<IF_PART_COUNT;++i){s.inclusive[i].Sample(inclusive[i]);s.inclusive[i].Frame(inclusive[i]);s.exclusive[i].Sample(exclusive[i]);s.exclusive[i].Frame(exclusive[i]);s.calls[i]+=calls[i];s.maxCall[i]=std::max(s.maxCall[i],maxCall[i]);}}
            // 首4个慢根样本及之后每10秒最多一行；完整全量统计仍保留，不逐接口输出。
            if(elapsed>=interfaceSlowMs&&(interfaceNotices<4||end-lastInterfaceSlow>=10000)){
                ++interfaceNotices;lastInterfaceSlow=end;std::ostringstream out;out<<std::setprecision(12)
                    <<"combat_interface_slow contract=IRIS_INTERFACE_PROBE_092 frame="<<token<<" generation="<<generation<<" root_wall_ms="<<elapsed;
                for(unsigned i=0;i<IF_PART_COUNT;++i)if(calls[i])out<<" "<<interfaceNames[i]<<"_exclusive_ms="<<exclusive[i];
                out<<" partition_error_ms="<<(elapsed-accounted-exclusive[IF_ROOT])<<" sampled_only=0 new_hooks=0 FPS_measured=0";Log(out.str());}
        }
    }catch(const std::exception&){/* 诊断失败不得改变已经完成的战斗或异常退出。 */}
    SetLastError(saved);
}
// 092关闭路径只初始化空frame；其余字段仅在成功借到根时设置，避免普通调用做数组/多字段准备。
InterfaceScope::InterfaceScope(InterfacePart value):frame(0),boundary(0){if(value<IF_PART_COUNT)Begin(value);}
InterfaceScope::~InterfaceScope(){Finish();}
void InterfaceScope::Begin(InterfacePart value,double at){
    if(value>=IF_PART_COUNT||!InterfaceEnabled())return;const DWORD saved=GetLastError();
    CombatInterfaceFrame* owner=static_cast<CombatInterfaceFrame*>(InterfaceTLSRead());
    if(owner&&!owner->sealed){const double now=at>0?at:Now();if(now>0&&_finite(now)){
        frame=owner;previous=frame->top;part=value;begin=now;children=0;frame->top=this;}}
    SetLastError(saved);
}
void InterfaceScope::Finish(double at){
    // 原父Scope结束时先封口；之后的Record/析构统计不混入已结束的父时间，根时钟无需重读。
    if(boundary){boundary->endedAt=at>0?at:Now();boundary->sealed=true;boundary=0;}
    if(!frame)return;const DWORD saved=GetLastError();const double now=at>0?at:Now();CombatInterfaceFrame* owner=frame;
    const bool mismatch=owner->top!=this;owner->top=previous;frame=0;
    const double elapsed=now-begin;
    if(mismatch||!_finite(elapsed)||elapsed<0||children>elapsed+.000001)++owner->badClocks;
    else{++owner->calls[part];owner->inclusive[part]+=elapsed;owner->exclusive[part]+=std::max(0.0,elapsed-children);owner->maxCall[part]=std::max(owner->maxCall[part],elapsed);if(previous)previous->children+=elapsed;}
    SetLastError(saved);
}
void InterfaceScope::Switch(InterfacePart value){
    if(!frame)return;const DWORD saved=GetLastError();const double now=Now();Finish(now);Begin(value,now);SetLastError(saved);
}
void InterfaceScope::FromKind(Kind value,double at){
    if(!interfaceOption)return;
    if(value==COMBAT_TICK){
        if(!InterfaceEnabled())return;const DWORD saved=GetLastError();
        CombatInterfaceFrame* owner=static_cast<CombatInterfaceFrame*>(InterfaceTLSRead());
        if(owner&&!owner->begin&&!owner->sealed){owner->begin=at;boundary=owner;}
        SetLastError(saved);return;
    }
    InterfacePart mapped=IF_PART_COUNT;
    switch(value){
    case SPHERE_QUERY:case SWEEP_QUERY:case CAPSULE_QUERY:case CYLINDER_QUERY:case CAPSULE_BATCH_QUERY:
    case NATIVE_TERRAIN_RAY:case NATIVE_SPHERE_SWEEP:case RANGED_BATCH_QUERY:mapped=IF_PHYSICS;break;
    case RESOURCE_GROUP:case VISUAL_CREATE:case MATERIAL_LOAD:case ASSET_READ:mapped=IF_RESOURCE;break;
    case PREWARM:mapped=IF_PREWARM;break;
    case VISUAL_UPDATE:mapped=IF_VISUAL;break;
    case ATTACHMENT_UPDATE:mapped=IF_ATTACHMENTS;break;
    case TRAIL_UPDATE:mapped=IF_TRAIL;break;
    case PATH_BUILD:mapped=IF_BLADE_PATH;break;
    case QUERY_JOBS:mapped=IF_JOBS;break;
    case CONTACT_COLLECT:mapped=IF_COLLECT;break;
    case DAMAGE_ENQUEUE:mapped=IF_ENQUEUE;break;
    default:break;}
    Begin(mapped,at);
}
// 关闭短路在取TLS/QPC之前；本轮不增加场景锁、SDK重放或逐形体日志。
InterfacePart QueryBoundaryPart(InterfacePart part){return queryBoundaryOption&&InterfaceEnabled()?part:IF_PART_COUNT;}
void ResetCombatInterfaceAudit(){if(interfaceOption)InterlockedIncrement(&interfaceGeneration);}
static void InterfaceSummary(Count id){
    if(!InterfaceEnabled())return;
    const InterfaceStats* rows[2]={&interfaceWindow,&interfaceRun};
    for(unsigned r=0;r<2;++r){const InterfaceStats& s=*rows[r];if(!s.total.calls&&!s.invalid)continue;
        for(unsigned i=0;i<IF_PART_COUNT;++i){if(!s.calls[i]&&i!=IF_ROOT)continue;std::ostringstream out;
            out<<std::setprecision(12)<<"audit_combat_interface id="<<id<<" scope="<<(r?"process":"window")
                <<" channel="<<interfaceNames[i]<<" root_samples="<<s.total.calls<<" stage_calls="<<s.calls[i]
                <<" inclusive_ms="<<s.inclusive[i].ms<<" exclusive_ms="<<s.exclusive[i].ms<<" max_call_ms="<<s.maxCall[i]
                <<" exclusive_frame_max_ms="<<s.exclusive[i].frameMax<<" exclusive_p95_upper_ms="<<s.exclusive[i].Percentile(95)
                <<" invalid_roots="<<s.invalid<<" nested_roots_skipped="<<s.nested<<" exception_roots="<<s.exceptions
                <<" tls_failures="<<InterlockedCompareExchange(&interfaceTLSFailures,0,0)
                <<" sample_every=1 same_root_partition=1 existing_combat_parent_clock=1 includes_observer=1 inclusive_not_additive=1 wall_not_CPU=1 FPS_measured=0";
            Log(out.str());}}
    interfaceWindow=InterfaceStats();
}
// 单段宽相A/B仅在显式试验开关及父日志全部开启时选择，不增加参考查询，不影响精确几何或事件身份。
bool RangedProbeCostEnabled(){return probeCostOption&&DetailsEnabled();}
bool SelectRangedSingleProbe(bool configured,bool eligible,unsigned& arm){
    arm=2;if(!configured||!eligible||!probeABOption||!RangedProbeCostEnabled())return configured;
    const unsigned serial=unsigned(InterlockedIncrement(&probeTrialSequence));arm=(serial-1)&1U;return arm==1;
}
struct ProbeCostStats {
    Stats total,rays,bodies,probe;Count batches,items,spheres,cylinders,commands,reuses,probes,saved,busy,unknown,failures;double distances,radii;
    ProbeCostStats():batches(0),items(0),spheres(0),cylinders(0),commands(0),reuses(0),probes(0),saved(0),busy(0),unknown(0),failures(0),distances(0),radii(0){}
};
static ProbeCostStats probeRun[3],probeWindow[3];
void RecordRangedProbeCost(const RangedProbeSample& v){
    if(!RangedProbeCostEnabled()||v.arm>2)return;InterfaceScope detail(IF_DIAGNOSTICS);Guard guard;
    ProbeCostStats* rows[2]={&probeRun[v.arm],&probeWindow[v.arm]};
    for(unsigned i=0;i<2;++i){ProbeCostStats& s=*rows[i];++s.batches;s.items+=v.items;s.spheres+=v.spheres;s.cylinders+=v.cylinders;s.commands+=v.commands;s.reuses+=v.reuses;s.probes+=v.probes;s.saved+=v.saved;s.busy+=v.busy;s.unknown+=v.unknown;s.failures+=v.failures;s.distances+=v.distanceSum;s.radii+=v.radiusSum;
        s.total.Sample(v.totalMs);s.rays.Sample(v.raysMs);s.bodies.Sample(v.bodiesMs);s.probe.Sample(v.probeMs);}
}
static void ProbeCostSummary(Count id){
    if(!RangedProbeCostEnabled())return;
    for(unsigned arm=0;arm<3;++arm){for(unsigned r=0;r<2;++r){const ProbeCostStats& s=r?probeRun[arm]:probeWindow[arm];if(!s.batches)continue;
        std::ostringstream out;out<<std::setprecision(12)<<"audit_ranged_probe_cost id="<<id<<" scope="<<(r?"process":"window")
            <<" arm="<<(arm==0?"single_off":arm==1?"single_on":"configured")<<" batches="<<s.batches<<" items="<<s.items
            <<" spheres="<<s.spheres<<" cylinders="<<s.cylinders<<" commands="<<s.commands<<" reuses="<<s.reuses<<" probes="<<s.probes
            <<" saved_sweeps="<<s.saved<<" busy="<<s.busy<<" unknown="<<s.unknown<<" failures="<<s.failures
            <<" total_ms="<<s.total.ms<<" rays_ms="<<s.rays.ms<<" bodies_ms="<<s.bodies.ms<<" probe_ms="<<s.probe.ms
            <<" max_batch_ms="<<s.total.maxCall<<" distance_sum="<<s.distances<<" radius_sum="<<s.radii
            <<" adjacent_batch_assignment=1 paired_replay=0 geometry_unchanged=1 extra_reference_queries=0 FPS_measured=0";
        Log(out.str());}probeWindow[arm]=ProbeCostStats();}
}
// 091固定统计容量；每个抽中调用只汇总一次，阶段切换只写当前栈，不在循环内格式化日志。
struct WorkStats {Stats total,parts[WORK_PART_COUNT];Count visits[WORK_PART_COUNT],exceptions;
    WorkStats():exceptions(0){for(unsigned i=0;i<WORK_PART_COUNT;++i)visits[i]=0;}};
static WorkStats workRun[WORK_DOMAIN_COUNT],workWindow[WORK_DOMAIN_COUNT];
static const char* workNames[WORK_PART_COUNT]={"setup","actor_ready","actor_request","actor_animation",
    "actor_pose","actor_visual","actor_path","actor_events","actor_finish","effects","jobs","tail",
    "medical_safety","medical_pop","medical_wait_stats","medical_identity","medical_calculate","medical_native","medical_xp","medical_result"};
WorkTrace::WorkTrace(WorkDomain value):domain(value),active(false),part(WORK_SETUP),begin(0),last(0){
    // 103：配置N=0时禁用抽样，不替用户改成1；保持关闭路径无原子/QPC。
    if(!workTraceEnabled||!workTraceEvery||!DetailsEnabled())return;
    // 无自适应调度或负载扫描；第一次及以后每N次抽样，轻负载不会启用另一套工作路径。
    const unsigned serial=unsigned(InterlockedIncrement(&workTraceSequence[domain]));
    if((serial-1)%workTraceEvery)return;
    const DWORD saved=GetLastError();begin=last=Now();SetLastError(saved);if(begin<=0)return;
    for(unsigned i=0;i<WORK_PART_COUNT;++i){elapsed[i]=0;visits[i]=0;}visits[WORK_SETUP]=1;active=true;
}
void WorkTrace::Mark(WorkPart value){
    if(!active)return;const DWORD saved=GetLastError();const double now=Now();SetLastError(saved);
    if(!_finite(now)||now<last)return;
    elapsed[part]+=now-last;last=now;part=value;++visits[value];
}
WorkTrace::~WorkTrace(){
    if(!active)return;const DWORD saved=GetLastError();
    try{
        const double now=Now();if(!_finite(now)||now<last){SetLastError(saved);return;}elapsed[part]+=now-last;
        Guard guard;WorkStats* rows[2]={&workRun[domain],&workWindow[domain]};
        for(unsigned r=0;r<2;++r){WorkStats& s=*rows[r];s.total.Sample(now-begin);s.total.Frame(now-begin);
            if(std::uncaught_exception())++s.exceptions;
            for(unsigned i=0;i<WORK_PART_COUNT;++i){s.parts[i].Sample(elapsed[i]);s.parts[i].Frame(elapsed[i]);s.visits[i]+=visits[i];}}
    }catch(const std::exception&){/* 诊断失败不改变已执行的战斗/医疗和异常展开。 */}
    SetLastError(saved);
}
static void WorkTraceSummary(Count id){
    if(!workTraceEnabled||!DetailsEnabled())return;
    // 调用方Summary已持同一递归诊断锁；只输出实际出现的阶段，零阶段不制造整页空日志。
    for(unsigned d=0;d<WORK_DOMAIN_COUNT;++d){
        for(unsigned r=0;r<2;++r){const WorkStats& s=r?workRun[d]:workWindow[d];if(!s.total.calls)continue;
            for(unsigned k=0;k<=WORK_PART_COUNT;++k){if(k<WORK_PART_COUNT&&!s.visits[k])continue;
                const Stats& v=k==WORK_PART_COUNT?s.total:s.parts[k];std::ostringstream out;
                out<<std::setprecision(12)<<"audit_work_trace id="<<id<<" scope="<<(r?"process":"window")<<" domain="<<(d?"medical":"combat")
                    <<" channel="<<(k==WORK_PART_COUNT?"total":workNames[k])<<" sampled_calls="<<s.total.calls
                    <<" visits="<<(k==WORK_PART_COUNT?s.total.calls:s.visits[k])<<" wall_ms="<<v.ms<<" max_sample_ms="<<v.maxCall
                    <<" p50_upper_ms="<<v.Percentile(50)<<" p95_upper_ms="<<v.Percentile(95)<<" p99_upper_ms="<<v.Percentile(99)
                    <<" sample_every="<<workTraceEvery<<" exception_samples="<<s.exceptions
                    <<" exclusive_sections=1 sampled_only=1 nested_old_timings_not_additive=1 wall_not_CPU=1 FPS_measured=0";
                Log(out.str());}}
        workWindow[d]=WorkStats();}
}
static Stats run[KIND_COUNT],window[KIND_COUNT];static double frameMs[KIND_COUNT]={0};
static Count runCounters[COUNTER_COUNT]={0},windowCounters[COUNTER_COUNT]={0};
static Count current[GAUGE_COUNT]={0},runPeak[GAUGE_COUNT]={0},windowPeak[GAUGE_COUNT]={0};
static bool ResourceKind(Kind k){return k==RESOURCE_GROUP||k==VISUAL_CREATE||k==MATERIAL_LOAD||k==PREWARM||k==ASSET_READ;}
static bool WaitKind(Kind k){return k==DAMAGE_WAIT||(k>=QUERY_WAIT&&k<=MEDICAL_UNAVAILABLE_WAIT);}
static bool Active(Kind k){
    // 新阶段仅在本开关下计时，旧Scope仍沿原开关；不在关闭路径中读取时钟或拿公共锁。
    if(k==QUERY_GATE_REFINE)return QueryGateLoggingEnabled();
    if(k==DAMAGE_CATCHUP_FLUSH)return DamageCatchupLoggingEnabled();
    if(k==CAPSULE_APPROX)return ConservativeQueryLoggingEnabled();
    if(k>=NATIVE_TERRAIN_RAY)return CollisionProfileEnabled();
    return enabled&&(ResourceKind(k)?resource:(performance&&(k<QUERY_WAIT||details)));
}
bool PerformanceEnabled(){return enabled&&performance;}
bool DetailsEnabled(){return enabled&&performance&&details;}
bool CollisionProfileEnabled(){return collisionProfile&&DetailsEnabled();}
bool ConservativeQueryLoggingEnabled(){return conservativeQueryLogging&&DetailsEnabled();}
bool DamageCatchupLoggingEnabled(){return damageCatchupLogging&&DetailsEnabled();}
bool QueryGateLoggingEnabled(){return queryGateLogging&&DetailsEnabled();}
void RecordConservativeQuery(unsigned kind,unsigned raw,unsigned contacts,unsigned tests,unsigned identity,unsigned geometry,unsigned capacity,unsigned input){
    if(!ConservativeQueryLoggingEnabled()||kind<1||kind>5)return;
    // 一次查询只进一次已有统计锁；SDK回调不调用本函数。不开日志无QPC/锁/统计写入。
    InterfaceScope interfaceTiming(IF_DIAGNOSTICS);Guard guard;
    const Counter counters094[]={APPROX_RAW,APPROX_CONTACTS,APPROX_TESTS,APPROX_SKIP_IDENTITY,APPROX_SKIP_GEOMETRY,APPROX_SKIP_CAPACITY,APPROX_SKIP_INPUT};
    const unsigned values[]={raw,contacts,tests,identity,geometry,capacity,input};
    // 097扇形(kind=5)的请求数有独立SECTOR_REQUESTS；这里仅合计异常/原始/去重等通用数。
    if(kind<=4){const Counter queryKind=Counter(APPROX_SPHERES+kind-1);++runCounters[queryKind];++windowCounters[queryKind];}
    for(unsigned i=0;i<7;++i){runCounters[counters094[i]]+=values[i];windowCounters[counters094[i]]+=values[i];}
}

// 097移除095内核审计存储和摘要，原生胶囊不存在旧手写内核对照。

// 082窗口诊断是固定容量的主线程观察，不是全程追踪物理线程；各字段顺序读取，并非原子场景快照。
// 新统计与旧physics合并等待归因独立，保留历史通道含义；缺项为-1，不额外读取后台队列容器。
static bool windowAuditEnabled=false,windowAuditOpen=false;
static Count windowSerial=0,windowGeneration=0,windowNotices=0,lastMedicalReject=0,rejectStreak=0;
static double rejectSince=0,lastWindowNoticeAt=0;static Count lastWindowSignature=0;static bool haveWindowSignature=false;
static const char* windowPhases[WINDOW_PHASE_COUNT]={"pre_native","post_native","pre_tick","post_tick","medical"};
struct WindowStats {
    Count samples,running,notClear,ai,paused,missing,unknownQueue,unknownAI,readErrors,ready,zeroProgress,afterProgress,maxRejectedFrames;
    // 083仅统计本窗口已完成医疗工作；pending关联来自此前POST_TICK纯值观察，不额外读取引擎。
    Count nativeCalls,inspectedRequests,progressAfterPendingQueue;
    double probeMs,probeMax,rejectedSpanMax;
    WindowStats():samples(0),running(0),notClear(0),ai(0),paused(0),missing(0),unknownQueue(0),unknownAI(0),readErrors(0),ready(0),zeroProgress(0),afterProgress(0),maxRejectedFrames(0),nativeCalls(0),inspectedRequests(0),progressAfterPendingQueue(0),probeMs(0),probeMax(0),rejectedSpanMax(0){}
    // 083医疗可在已确认命中后独立结算；其他阶段仍按查询可用性计ready，不把-1伪写为队列已空。
    void Add(const WindowState& s,double cost,bool requireQueues){++samples;if(s.physicsRunning==1)++running;if(s.queuesClear==0)++notClear;
        if(s.aiRunning==1)++ai;if(s.paused==1)++paused;if(s.unavailable==1)++missing;if(s.queuesClear<0)++unknownQueue;if(s.aiRunning<0)++unknownAI;if(s.failed)++readErrors;
        if(!s.failed&&s.unavailable==0&&s.physicsRunning==0&&(!requireQueues||s.queuesClear==1)&&s.aiRunning==0&&s.paused==0)++ready;
        probeMs+=cost;probeMax=std::max(probeMax,cost);}
};
static WindowStats windowRun[WINDOW_PHASE_COUNT],windowPeriod[WINDOW_PHASE_COUNT];
static WindowState windowStates[WINDOW_PHASE_COUNT];static bool windowSeen[WINDOW_PHASE_COUNT]={0};
static double windowAt[WINDOW_PHASE_COUNT]={0};static bool medicalBlocked=false,medicalSeen=false,windowObserved=false;
static const char* medicalReason="unobserved";static const char* medicalCause="unobserved";
static Count medicalBefore=0,medicalRemaining=0;static unsigned medicalDone=0,medicalInspected=0;static double medicalOldest=-1;
bool WindowAuditEnabled(){return windowAuditEnabled&&DetailsEnabled();}
// 只读本插件已在原锁内维护的数量快照；没有任务/弹体/动作时不增加引擎状态读取。
bool WindowAuditHasWork(){if(!WindowAuditEnabled())return false;Guard guard;return current[PENDING_DAMAGE]||current[JOBS]||current[PROJECTILES]||current[ACTIVE_ACTORS];}
bool BeginWindowAudit(){
    if(!WindowAuditEnabled())return false;Guard guard;if(windowAuditOpen)return false;windowAuditOpen=true;++windowSerial;
    for(unsigned p=0;p<WINDOW_PHASE_COUNT;++p){windowStates[p]=WindowState();windowSeen[p]=false;windowAt[p]=0;}
    medicalBlocked=medicalSeen=windowObserved=false;medicalReason=medicalCause="unobserved";
    medicalBefore=medicalRemaining=0;medicalDone=medicalInspected=0;medicalOldest=-1;
    if(!current[PENDING_DAMAGE]){lastMedicalReject=rejectStreak=0;rejectSince=0;}return true;
}
void RecordWindowAudit(WindowPhase phase,const WindowState& state,double probeMs){
    if(!WindowAuditEnabled()||phase>=WINDOW_PHASE_COUNT)return;Guard guard;if(!windowAuditOpen)return;
    const double cost=_finite(probeMs)&&probeMs>0?probeMs:0;windowStates[phase]=state;windowSeen[phase]=true;windowAt[phase]=Now();windowObserved=true;
    // 只改变纯值摘要的ready口径；不调用物理getter，也不参与实际许可。
    const bool requireQueues=phase!=WINDOW_MEDICAL;
    windowRun[phase].Add(state,cost,requireQueues);windowPeriod[phase].Add(state,cost,requireQueues);
}
void RecordMedicalWindow(const WindowState& state,const char* reason,const char* cause,Count before,Count remaining,unsigned done,unsigned inspected,double observedAt,double oldest){
    if(!WindowAuditEnabled()||(!before&&!remaining&&!inspected))return;Guard guard;if(!windowAuditOpen)return;
    RecordWindowAudit(WINDOW_MEDICAL,state,0);windowAt[WINDOW_MEDICAL]=observedAt;
    medicalSeen=true;medicalReason=reason;medicalCause=cause;medicalBefore=before;medicalRemaining=remaining;medicalDone=done;medicalInspected=inspected;medicalOldest=oldest;
    // 用户要求继续核查：复用本轮已存在的观察，统计医疗是否在此前queue未清空时仍取得进展。
    // 这是顺序观察关联，绝不是原生调用瞬间的物理状态；诊断开关在函数入口已经短路。
    WindowStats* medicalRows[2]={&windowRun[WINDOW_MEDICAL],&windowPeriod[WINDOW_MEDICAL]};
    for(unsigned i=0;i<2;++i){medicalRows[i]->nativeCalls+=done;medicalRows[i]->inspectedRequests+=inspected;
        if(done&&windowSeen[WINDOW_POST_TICK]&&windowStates[WINDOW_POST_TICK].queuesClear==0)++medicalRows[i]->progressAfterPendingQueue;}
    medicalBlocked=!strcmp(reason,"physics_busy")||!strcmp(reason,"ai_busy")||!strcmp(reason,"world_missing")||!strcmp(reason,"paused");
    // 连续数只统计连续诊断机会的医疗拒绝；外层未进入医疗或读档会中断，不冒称后台线程连续执行时间。
    if(medicalBlocked){
        if(rejectStreak&&lastMedicalReject+1==windowSerial)++rejectStreak;else{rejectStreak=1;rejectSince=Now();}lastMedicalReject=windowSerial;
        double span=std::max(0.0,Now()-rejectSince);WindowStats* rows[2]={&windowRun[WINDOW_MEDICAL],&windowPeriod[WINDOW_MEDICAL]};
        for(unsigned i=0;i<2;++i){if(!inspected)++rows[i]->zeroProgress;else ++rows[i]->afterProgress;
            rows[i]->maxRejectedFrames=std::max(rows[i]->maxRejectedFrames,rejectStreak);rows[i]->rejectedSpanMax=std::max(rows[i]->rejectedSpanMax,span);}
    }else{lastMedicalReject=rejectStreak=0;rejectSince=0;}
}
void FinishWindowAudit(){
    if(!WindowAuditEnabled())return;Guard guard;if(!windowAuditOpen)return;windowAuditOpen=false;if(!windowObserved)return;
    try{
        // 五阶段各五个三态值占50位，完整编码用于限频；不参与伤害/资格或安全判断。
        Count signature=0;bool readError=false;
        for(unsigned p=0;p<WINDOW_PHASE_COUNT;++p){const WindowState& s=windowStates[p];int values[5]={s.physicsRunning,s.queuesClear,s.aiRunning,s.paused,s.unavailable};
            for(unsigned k=0;k<5;++k)signature|=Count(values[k]+1)<<((p*5+k)*2);readError=readError||s.failed;}
        signature|=Count(medicalBlocked)<<50;signature|=Count(readError)<<51;
        const double now=Now();const bool changed=!haveWindowSignature||signature!=lastWindowSignature;
        if(windowNotices>=8&&now-lastWindowNoticeAt<10000&&(!changed||now-lastWindowNoticeAt<1000))return;
        ++windowNotices;lastWindowNoticeAt=now;lastWindowSignature=signature;haveWindowSignature=true;
        std::ostringstream out;out<<std::setprecision(12)<<"audit_window_trace contract=IRIS_WINDOW_AUDIT_082 serial="<<windowSerial<<" generation="<<windowGeneration<<" frame="<<frameId
            <<" pending_cached="<<current[PENDING_DAMAGE]<<" jobs_cached="<<current[JOBS]<<" medical_requires_queues=0 medical_seen="<<medicalSeen<<" medical_reason="<<medicalReason<<" medical_cause="<<medicalCause
            <<" queued_before="<<medicalBefore<<" remaining="<<medicalRemaining<<" native_calls="<<medicalDone<<" inspected="<<medicalInspected<<" oldest_wall_ms="<<medicalOldest<<" rejected_consecutive_frames="<<rejectStreak;
        for(unsigned p=0;p<WINDOW_PHASE_COUNT;++p){const WindowState& s=windowStates[p];const char* n=windowPhases[p];out<<" "<<n<<"_seen="<<windowSeen[p]<<" "<<n<<"_at_ms="<<windowAt[p]
            <<" "<<n<<"_physics_running="<<s.physicsRunning<<" "<<n<<"_queues_clear="<<s.queuesClear<<" "<<n<<"_ai_running="<<s.aiRunning<<" "<<n<<"_paused="<<s.paused<<" "<<n<<"_unavailable="<<s.unavailable<<" "<<n<<"_read_error="<<s.failed;}
        out<<" unknown=-1 states_read_sequentially=1 cached_work_is_observation=1 worker_runtime_measured=0 notice="<<windowNotices;Log(out.str());
    }catch(const std::exception&){/* 只丢诊断明细，不影响已完成/尚未完成的任何健康请求。 */}
}
void ResetWindowAudit(){
    if(!WindowAuditEnabled())return;Guard guard;++windowGeneration;lastMedicalReject=rejectStreak=0;rejectSince=0;medicalSeen=medicalBlocked=windowObserved=false;medicalReason=medicalCause="unobserved";
    medicalBefore=medicalRemaining=0;medicalDone=medicalInspected=0;medicalOldest=-1;haveWindowSignature=false;
    for(unsigned p=0;p<WINDOW_PHASE_COUNT;++p){windowStates[p]=WindowState();windowSeen[p]=false;windowAt[p]=0;}
}
static void WindowAuditSummary(Count id){
    if(!WindowAuditEnabled())return;
    // Summary已持原诊断锁；两套固定数组分别为窗口/进程计数，不额外取得引擎锁或读取场景。
    for(unsigned scope=0;scope<2;++scope)for(unsigned p=0;p<WINDOW_PHASE_COUNT;++p){WindowStats& a=scope?windowRun[p]:windowPeriod[p];if(!a.samples)continue;
        std::ostringstream out;out<<"audit_window_phase contract=IRIS_WINDOW_AUDIT_082 id="<<id<<" scope="<<(scope?"process":"window")<<" phase="<<windowPhases[p]<<" observations="<<a.samples
            <<" physics_running="<<a.running<<" queues_not_clear="<<a.notClear<<" ai_running="<<a.ai<<" paused="<<a.paused<<" unavailable="<<a.missing<<" queues_unobserved="<<a.unknownQueue<<" ai_unobserved="<<a.unknownAI<<" read_errors="<<a.readErrors<<" ready_observations="<<a.ready
            <<" medical_native_calls="<<a.nativeCalls<<" medical_requests_inspected="<<a.inspectedRequests<<" medical_progress_windows_after_queue_pending_observed="<<a.progressAfterPendingQueue
            <<" ready_requires_queues="<<(p!=WINDOW_MEDICAL)<<" rejected_before_first="<<a.zeroProgress<<" rejected_after_progress="<<a.afterProgress<<" max_rejected_consecutive_frames="<<a.maxRejectedFrames<<" max_rejected_observed_span_ms="<<a.rejectedSpanMax
            <<" probe_wall_ms="<<a.probeMs<<" probe_max_ms="<<a.probeMax<<" worker_runtime_measured=0 sequential_observation=1";Log(out.str());}
    for(unsigned p=0;p<WINDOW_PHASE_COUNT;++p)windowPeriod[p]=WindowStats();
}

// 078运行默认关闭；用户测试INI显式开启。十六入口只写对齐原子累计，不取得Iris锁或逐调用I/O。
// 原生线程可并发经过同一Hook，不能用普通++或为统计再加互斥量。累计不清零，摘要用差值取窗口。
static bool hookAuditEnabled=false;static unsigned hookSampleEvery=128;
enum HookField {H_CALLS,H_FAST,H_LOCKED,H_ENTRIES,H_SAMPLES,H_WAIT_US,H_WORK_US,H_WAIT_MAX_US,H_WORK_MAX_US,H_TOTAL_SAMPLES,H_TOTAL_US,H_TOTAL_MAX_US,H_NOLOCK_SAMPLES,H_NOLOCK_US,H_LOCK_TOTAL_SAMPLES,H_LOCK_TOTAL_US,H_FIELDS};
struct __declspec(align(64)) HookStats {volatile LONGLONG value[H_FIELDS];};
static HookStats hookStats[HOOK_COUNT];static Count hookPrevious[HOOK_COUNT][H_FIELDS]={0};
static const char* hookNames[HOOK_COUNT]={"choose","start","run","block","stumble","frame","safe",
    "ranged_use","ranged_has","ranged_score","ranged_within","ranged_gun","ranged_animation","ranged_shot","ranged_reload","defence"};
static LONGLONG HookRead(volatile LONGLONG* value){return InterlockedCompareExchange64(value,0,0);}
static void HookMaximum(volatile LONGLONG* target,LONGLONG value){
    LONGLONG old=HookRead(target);
    while(old<value){LONGLONG seen=InterlockedCompareExchange64(target,value,old);if(seen==old)return;old=seen;}
}
static LONGLONG HookMicroseconds(double milliseconds){
    // 仅量化诊断值；异常时钟不参与统计，绝不改变锁或战斗流程。上限防止浮点转整数溢出。
    return _finite(milliseconds)&&milliseconds>0&&milliseconds<1.e9?static_cast<LONGLONG>(milliseconds*1000.0):0;
}
// 103：采样N=0时保留已开启的调用次数统计，但不抽样计时，也不进行取模0；不钳成1。
HookAudit::HookAudit(Hook value):hook(value),active(hookAuditEnabled&&PerformanceEnabled()),sampled(false),totalSampled(false),entries(0),waitBegin(0),workBegin(0),waitTotal(0),workTotal(0),totalBegin(0){
    // 每入口按全体调用序号抽样，总计时包含原生；原锁抽样另按进锁序号，不能直接互减。
    // 关闭时不做原子/QPC；开启也不访问游戏对象、分配TLS/堆或取得插件公共锁。
    if(active){LONGLONG ordinal=InterlockedIncrement64(&hookStats[hook].value[H_CALLS]);
        totalSampled=hookSampleEvery&&(ordinal-1)%hookSampleEvery==0;if(totalSampled)totalBegin=Now();}
}
void HookAudit::BeforeLock(){
    if(!active)return;
    if(!entries){LONGLONG ordinal=InterlockedIncrement64(&hookStats[hook].value[H_LOCKED]);sampled=hookSampleEvery&&(ordinal-1)%hookSampleEvery==0;}
    ++entries;if(sampled)waitBegin=Now();
}
void HookAudit::Acquired(){if(active&&sampled){double now=Now();if(waitBegin>0&&now>=waitBegin)waitTotal+=now-waitBegin;workBegin=now;}}
void HookAudit::BeforeUnlock(){if(active&&sampled){double now=Now();if(workBegin>0&&now>=workBegin)workTotal+=now-workBegin;}}
HookAudit::~HookAudit(){
    if(!active)return;
    // 先截止回调计时再提交统计，避免把本析构的原子汇总开销算入样本。
    // RAII保留所有早退/异常退出；时间是包含原生与嵌套入口的墙钟，不是插件净耗时。
    const LONGLONG total=totalSampled?HookMicroseconds(std::max(0.0,Now()-totalBegin)):0;HookStats& stats=hookStats[hook];
    if(!entries)InterlockedIncrement64(&stats.value[H_FAST]);
    else{InterlockedExchangeAdd64(&stats.value[H_ENTRIES],entries);
        if(sampled){LONGLONG wait=HookMicroseconds(waitTotal),work=HookMicroseconds(workTotal);
            InterlockedExchangeAdd64(&stats.value[H_WAIT_US],wait);InterlockedExchangeAdd64(&stats.value[H_WORK_US],work);
            HookMaximum(&stats.value[H_WAIT_MAX_US],wait);HookMaximum(&stats.value[H_WORK_MAX_US],work);
            InterlockedIncrement64(&stats.value[H_SAMPLES]);}}
    if(totalSampled){InterlockedExchangeAdd64(&stats.value[H_TOTAL_US],total);HookMaximum(&stats.value[H_TOTAL_MAX_US],total);
        InterlockedExchangeAdd64(&stats.value[entries?H_LOCK_TOTAL_US:H_NOLOCK_US],total);
        InterlockedIncrement64(&stats.value[entries?H_LOCK_TOTAL_SAMPLES:H_NOLOCK_SAMPLES]);InterlockedIncrement64(&stats.value[H_TOTAL_SAMPLES]);}
}
static void HookSummary(Count id,double windowElapsed,double processElapsed){
    if(!hookAuditEnabled||!PerformanceEnabled())return;
    for(unsigned hook=0;hook<HOOK_COUNT;++hook){Count current[H_FIELDS];
        for(unsigned field=0;field<H_FIELDS;++field)current[field]=Count(HookRead(&hookStats[hook].value[field]));
        for(unsigned scope=0;scope<2;++scope){Count n[H_FIELDS];const double elapsed=scope?processElapsed:windowElapsed;
            for(unsigned field=0;field<H_FIELDS;++field)n[field]=scope?current[field]:current[field]-hookPrevious[hook][field];
            std::ostringstream out;out<<std::setprecision(10)<<"audit_hook id="<<id<<" scope="<<(scope?"process":"window")<<" hook="<<hookNames[hook]
                <<" elapsed_ms="<<elapsed<<" calls_per_second="<<(elapsed>0?double(n[H_CALLS])*1000.0/elapsed:0.0)<<" calls="<<n[H_CALLS]<<" fast_returns="<<n[H_FAST]<<" locked_callbacks="<<n[H_LOCKED]<<" lock_entries="<<n[H_ENTRIES]<<" sampled_callbacks="<<n[H_SAMPLES]
                <<" acquire_wall_ms_sampled="<<double(n[H_WAIT_US])/1000.0<<" protected_wall_ms_sampled="<<double(n[H_WORK_US])/1000.0
                <<" max_acquire_ms_process="<<double(current[H_WAIT_MAX_US])/1000.0<<" max_protected_ms_process="<<double(current[H_WORK_MAX_US])/1000.0
                <<" sampled_total_callbacks="<<n[H_TOTAL_SAMPLES]<<" callback_wall_ms_sampled="<<double(n[H_TOTAL_US])/1000.0
                <<" sampled_no_audited_lock_callbacks="<<n[H_NOLOCK_SAMPLES]<<" no_audited_lock_wall_ms_sampled="<<double(n[H_NOLOCK_US])/1000.0
                <<" sampled_locked_total_callbacks="<<n[H_LOCK_TOTAL_SAMPLES]<<" locked_total_wall_ms_sampled="<<double(n[H_LOCK_TOTAL_US])/1000.0
                <<" max_callback_ms_process="<<double(current[H_TOTAL_MAX_US])/1000.0
                <<" sample_every_all="<<hookSampleEvery<<" sample_every_locked="<<hookSampleEvery
                <<" independent_atomic_snapshot=1 inflight_possible=1 sampled_only=1 elapsed_includes_pause=1 includes_acquire_overhead=1 includes_original=1 total_and_lock_samples_independent=1 nested_timings_not_additive=1 FPS_measured=0";
            Log(out.str());}
        for(unsigned field=0;field<H_FIELDS;++field)hookPrevious[hook][field]=current[field];
    }
}

static WaitStamp waits;static double waitObservedAt=0;static unsigned waitState=0;
static WaitStamp ProjectWaits(double now){
    WaitStamp result=waits;double elapsed=waitObservedAt>0&&now>=waitObservedAt?now-waitObservedAt:0;
    if(waitState==1)result.pause+=elapsed;else if(waitState==2)result.physics+=elapsed;
    else if(waitState==3)result.ai+=elapsed;else if(waitState==4)result.unavailable+=elapsed;return result;
}
void ObserveWindow(bool paused,bool physicsBusy,bool aiBusy,bool unavailable){
    if(!DetailsEnabled())return;Guard guard;double now=Now();if(now<=0)return;
    waits=ProjectWaits(now);waitObservedAt=now;waitState=paused?1:physicsBusy?2:aiBusy?3:unavailable?4:0;
}
void SnapshotWaits(double now,WaitStamp& stamp){if(!DetailsEnabled()||now<=0)return;Guard guard;stamp=ProjectWaits(now);}
void RecordWait(bool query,double created,const WaitStamp& before,double now){
    if(!DetailsEnabled()||created<=0||now<created)return;WaitStamp after;SnapshotWaits(now,after);
    double total=now-created;double paused=std::max(0.0,after.pause-before.pause),physics=std::max(0.0,after.physics-before.physics);
    double ai=std::max(0.0,after.ai-before.ai),unavailable=std::max(0.0,after.unavailable-before.unavailable);
    // 两次同域快照的互斥累计不超过墙钟；浮点舍入只在余量处钳零，绝不将墙钟当CPU时间。
    if(query)Record(QUERY_WAIT,total);
    Record(query?QUERY_PAUSE_WAIT:MEDICAL_PAUSE_WAIT,paused);Record(query?QUERY_PHYSICS_WAIT:MEDICAL_PHYSICS_WAIT,physics);
    Record(query?QUERY_AI_WAIT:MEDICAL_AI_WAIT,ai);Record(query?QUERY_UNAVAILABLE_WAIT:MEDICAL_UNAVAILABLE_WAIT,unavailable);
    Record(query?QUERY_READY_WAIT:MEDICAL_READY_WAIT,std::max(0.0,total-paused-physics-ai-unavailable));
}
double Now(){LARGE_INTEGER t;if(frequency<=0||!QueryPerformanceCounter(&t))return 0;return double(t.QuadPart)*1000.0/frequency;}
// 103：日志周期/阈值/采样数不设业务上下限；只有字段类型转换需要显式校验。
static double Number(const std::wstring& ini,const wchar_t* key,double fallback){
    return IrisIni::Number(ini,L"IrisArsenal",key,fallback);
}
static bool Switch(const std::wstring& ini,const wchar_t* key,bool fallback){double n=Number(ini,key,fallback?1:0);if(n!=0&&n!=1)throw std::runtime_error(std::string("logging switch requires 0 or 1: ")+std::string(key,key+wcslen(key)));return n!=0;}
static std::string Utf8(const std::wstring& value){int n=WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,value.c_str(),int(value.size()),0,0,0,0);if(n<=0)return "unavailable";std::string result(n,'\0');WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,value.c_str(),int(value.size()),&result[0],n,0,0);return result;}
void Record(Kind kind,double ms){if(!Active(kind)||!_finite(ms)||ms<0)return;InterfaceScope interfaceTiming(IF_DIAGNOSTICS);Guard guard;run[kind].Sample(ms);window[kind].Sample(ms);if(WaitKind(kind)){run[kind].Frame(ms);window[kind].Frame(ms);}else if(frameOpen)frameMs[kind]+=ms;}
/* 086零增量不改变窗口/进程计数，摘要和读档也不依赖这次空操作。
   查询纯值经常为0；在入口短路可避免为新旧零计数反复进入共用锁，不改变非零计数原子快照。 */
/* 100纯值结果在SDK退出后一次合计；无逐形体时钟、影子查询或新增同步对象。
   计时覆盖慢路径判定，不含后续碰撞；消息位计数是重叠原因，主原因独占。 */
void RecordQueryGate(unsigned source,unsigned why,unsigned mask,unsigned exceptionCode,double ms,double at){
    if(!QueryGateLoggingEnabled()||source>=IrisQueryGate::SOURCE_COUNT||why>=IrisQueryGate::REASON_COUNT)return;
    InterfaceScope interfaceTiming(IF_DIAGNOSTICS);
    static Count notices=0;static unsigned lastWhy=0,lastMask=0,lastException=0;static double lastAt=0;
    bool notice=false;
    {Guard guard;
        const Counter src=Counter(QG_SINGLE_OLD_FALSE+source),reason=Counter(QG_ALLOW+why);
        ++runCounters[src];++windowCounters[src];++runCounters[reason];++windowCounters[reason];
        for(unsigned bit=0;bit<IrisQueryGate::QUEUE_BITS;++bit)if(mask&(1U<<bit)){
            const Counter c=Counter(QG_MASK_CREATE_MAIN+bit);++runCounters[c];++windowCounters[c];}
        if(_finite(ms)&&ms>=0){run[QUERY_GATE_REFINE].Sample(ms);window[QUERY_GATE_REFINE].Sample(ms);if(frameOpen)frameMs[QUERY_GATE_REFINE]+=ms;}
        const bool changed=why!=lastWhy||mask!=lastMask||exceptionCode!=lastException;
        notice=notices<8||(at-lastAt>=10000)||(changed&&at-lastAt>=1000);
        if(notice){++notices;lastAt=at;lastWhy=why;lastMask=mask;lastException=exceptionCode;}
    }
    if(notice)try{
        static const char* sources[]={"single","capsule_batch","ranged_batch"};
        static const char* reasons[]={"allow","disabled","world_invalid","worker_busy","bad_queue","pending_create","pending_destroy","pending_terrain","pending_other","sdk_not_writable","sdk_unavailable","sdk_error","scene_changed"};
        std::ostringstream out;out<<"query_gate_refine contract=IRIS_QUERY_GATE_100 source="<<sources[source]<<" reason="<<reasons[why]
            <<" allowed="<<(why==IrisQueryGate::ALLOW)<<" pending_mask=0x"<<std::hex<<mask<<" exception=0x"<<exceptionCode<<std::dec
            <<" gate_ms="<<ms<<" actual_queues_checked=main_and_back new_hooks=0 notice="<<notices;Log(out.str());
    }catch(const std::exception&){/* 诊断格式化失败不改变已决定的许可或使游戏业务抛出。 */}
}
void Add(Counter counter,Count amount){if(!amount||!PerformanceEnabled())return;InterfaceScope interfaceTiming(IF_DIAGNOSTICS);Guard guard;runCounters[counter]+=amount;windowCounters[counter]+=amount;}
void Set(Gauge gauge,Count value){if(!PerformanceEnabled())return;InterfaceScope interfaceTiming(IF_DIAGNOSTICS);Guard guard;current[gauge]=value;runPeak[gauge]=std::max(runPeak[gauge],value);windowPeak[gauge]=std::max(windowPeak[gauge],value);}
void Flush(bool force){
    if(!enabled)return;Guard guard;if(pending.empty())return;DWORD now=GetTickCount();if(!force&&pending.size()<16384&&DWORD(now-lastFlush)<flushMillis)return;
    double begin=PerformanceEnabled()?Now():0;HANDLE f=CreateFileW(filename.c_str(),FILE_APPEND_DATA,FILE_SHARE_READ|FILE_SHARE_WRITE,0,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,0);
    bool ok=f!=INVALID_HANDLE_VALUE;DWORD done=0;if(ok){ok=WriteFile(f,pending.data(),DWORD(pending.size()),&done,0)!=0;CloseHandle(f);if(done)pending.erase(0,std::min(size_t(done),pending.size()));}
    lastFlush=now;if(!ok||!pending.empty()){++ioFailures;ErrorLog("IrisArsenal logging write failed; bounded buffer retained");}else ioFailures=0;
    if(PerformanceEnabled()){double ms=std::max(0.0,Now()-begin);run[LOG_FLUSH].Sample(ms);window[LOG_FLUSH].Sample(ms);if(frameOpen)frameMs[LOG_FLUSH]+=ms;}
}
void Log(const std::string& message){
    if(!enabled)return;InterfaceScope interfaceTiming(IF_DIAGNOSTICS);Guard guard;
    try{SYSTEMTIME t;GetLocalTime(&t);char head[120];sprintf_s(head,"%04u-%02u-%02u %02u:%02u:%02u.%03u [IrisArsenal 0.4.54] ",t.wYear,t.wMonth,t.wDay,t.wHour,t.wMinute,t.wSecond,t.wMilliseconds);
        std::string line=std::string(head)+message+"\r\n";
        // 磁盘失败时只保留至多64KiB，记录丢失字节，不让诊断故障导致无界内存增长；不截断原文件。
        if(pending.size()+line.size()>65536)Flush(true);
        if(pending.size()+line.size()<=65536)pending+=line;else droppedBytes+=line.size();
        const bool urgent=message.find("error")!=std::string::npos||message.find("disabled")!=std::string::npos||message.find("fault")!=std::string::npos||message.find("resource_begin")==0;
        Flush(urgent);
    }catch(const std::exception&){ErrorLog("IrisArsenal diagnostic formatting failed");}
}
void Initialize(const std::wstring& directory,const std::wstring& logFile){
    filename=logFile;std::wstring ini=directory+L"IrisArsenal.ini";enabled=Switch(ini,L"EnableLogging",true);
    performance=Switch(ini,L"EnablePerformanceLogging",true);resource=Switch(ini,L"EnableResourceLogging",true);details=Switch(ini,L"EnableCombatDetailLogging",true);
    // 078复用既有专用开关，程序缺省仍0；测试包INI显式1。关闭日志/性能/本开关均不做原子或QPC。
    hookAuditEnabled=Switch(ini,L"EnableHookAuditLogging",false);
    // 087只拆既有同步消费者；无逐形体日志，摘要仍复用窗口/进程固定容量统计。
    collisionProfile=Switch(ini,L"EnableCollisionDetailProfiling",false);
    // 091缺项0；采样整数32默认，仅本地测试显式开启，发布/轻负载可完全关闭。
    workTraceEnabled=Switch(ini,L"EnableWorkPhaseProfiling",false);
    const double workEvery=Number(ini,L"WorkPhaseSampleEvery",32);
    if(floor(workEvery)!=workEvery)throw std::runtime_error("WorkPhaseSampleEvery must be an integer");
    workTraceEvery=IrisIni::Unsigned(workEvery,"WorkPhaseSampleEvery");
    // 082程序缺省0；本轮测试INI显式1，仍要求总日志/性能/明细同时开启。
    windowAuditEnabled=Switch(ini,L"EnableWindowAuditLogging",false);
    double hookEvery=Number(ini,L"HookAuditSampleEvery",128);if(floor(hookEvery)!=hookEvery)throw std::runtime_error("HookAuditSampleEvery must be an integer");hookSampleEvery=IrisIni::Unsigned(hookEvery,"HookAuditSampleEvery");
    // 103刷盘字段原为DWORD整数毫秒；只检查实际表示能力，不再按60秒业务上限截断。
    summarySeconds=Number(ini,L"LogSummarySeconds",60);flushMillis=IrisIni::Unsigned(Number(ini,L"LogFlushSeconds",2)*1000,"LogFlushSeconds in integer milliseconds");slowMs=Number(ini,L"SlowFrameThresholdMs",8);
    LARGE_INTEGER f;if(QueryPerformanceFrequency(&f)&&f.QuadPart>0)frequency=double(f.QuadPart);else{performance=false;resource=false;ErrorLog("IrisArsenal QPC unavailable; performance timing disabled");}
    interfaceOption=Switch(ini,L"EnableCombatInterfaceProfiling",false);
    probeCostOption=Switch(ini,L"EnableRangedProbeCostLogging",false);
    probeABOption=Switch(ini,L"EnableRangedSingleProbeABTest",false);
    queryBoundaryOption=Switch(ini,L"EnableQueryBoundaryProfiling",false);
    conservativeQueryLogging=Switch(ini,L"EnableConservativeQueryLogging",false);
    damageCatchupLogging=Switch(ini,L"EnableDamageCatchupLogging",false);
    queryGateLogging=Switch(ini,L"EnableQueryGateLogging",false);
    interfaceSlowMs=Number(ini,L"CombatInterfaceSlowMs",2);
    if(interfaceOption&&DetailsEnabled()){interfaceTLS=TlsAlloc();if(interfaceTLS==TLS_OUT_OF_INDEXES)InterlockedIncrement(&interfaceTLSFailures);}
    // 084程序缺省0，测试配置显式开启；总日志/性能/明细关闭时不分配诊断TLS或安装新Hook。
    IrisNativeAudit::Configure(Switch(ini,L"EnableNativeHitProfiling",false),Switch(ini,L"EnableServiceOpportunityLogging",false),Switch(ini,L"EnableNativeGapProfiling",false),workTraceEvery);
    // 085程序缺省0；总日志/性能/明细/084原生探针仍是前置条件，不默认扩大原生Hook范围。
    /* 086分支探针单独可关；父探针关闭时不安装，关闭日志不会遗留额外游戏状态查询。 */
    IrisWoundAudit::Configure(Switch(ini,L"EnableWoundDetailProfiling",false),Switch(ini,L"EnableWoundBranchProfiling",false));
    processBegin=windowBegin=Now();lastFlush=GetTickCount();pending.reserve(16384);initialized=true;
    if(!enabled)return;
    FILETIME created,exited,kernel,user;Count creation=0;if(GetProcessTimes(GetCurrentProcess(),&created,&exited,&kernel,&user))creation=(Count(created.dwHighDateTime)<<32)|created.dwLowDateTime;
    wchar_t executable[32768];DWORD n=GetModuleFileNameW(0,executable,32768);
    std::string gameVersion="unavailable",assetRevision="unavailable";
    if(n&&n<32768){DWORD ignored=0,size=GetFileVersionInfoSizeW(executable,&ignored);if(size&&size<=1048576){std::vector<unsigned char> bytes(size);VS_FIXEDFILEINFO* info=0;UINT len=0;if(GetFileVersionInfoW(executable,0,size,&bytes[0])&&VerQueryValueW(&bytes[0],L"\\",reinterpret_cast<void**>(&info),&len)&&info&&len>=sizeof(*info)){std::ostringstream v;v<<HIWORD(info->dwFileVersionMS)<<"."<<LOWORD(info->dwFileVersionMS)<<"."<<HIWORD(info->dwFileVersionLS)<<"."<<LOWORD(info->dwFileVersionLS);gameVersion=v.str();}}}
    // 仅记录实际安装清单的资源修订；不是把新源码标记误称为旧游戏资源已经升级。
    std::ifstream manifest((directory+L"IrisPackage.json").c_str());std::string line;while(std::getline(manifest,line)){size_t key=line.find("\"asset_revision\"");if(key!=std::string::npos){size_t colon=line.find(':',key),a=colon==std::string::npos?colon:line.find('"',colon),b=a==std::string::npos?a:line.find('"',a+1);if(a!=std::string::npos&&b!=std::string::npos)assetRevision=line.substr(a+1,b-a-1);break;}}
    // 062修复远程许可门，保留061资格/057几何/056合批身份；运行标记必须区分已编译旧DLL。
    std::ostringstream s;s<<"audit_run_identity contract=IRIS_RANGED_GATE_062 policy_contract=IRIS_COMBAT_POLICY_061 aim_contract=IRIS_NATIVE_AIM_060 previous_visual_contract=IRIS_DRIVE_REBUILD_059 physx_contract=IRIS_PHYSX_COMPAT_054 damage_queue_contract=IRIS_DAMAGE_QUEUE_053 audit_contract=IRIS_LONGTERM_AUDIT_052 pid="<<GetCurrentProcessId()<<" creation_filetime="<<creation<<" executable="<<(n&&n<32768?Utf8(std::wstring(executable,n)):"unavailable")<<" game_version="<<gameVersion<<" installed_asset_revision="<<assetRevision<<" dll_version=0.4.54 logging=1 combat_details="<<details<<" wait_attribution=previous_main_thread_observation performance="<<performance<<" resource="<<resource<<" summary_seconds="<<summarySeconds<<" flush_ms="<<flushMillis<<" slow_frame_ms="<<slowMs<<" counter_bits=64 histogram=frame_upper_bounds log_total_limit=0 event_detail_limit=0 FPS_measured=0 GPU_bytes_measured=0 background_thread=0 hook_audit="<<hookAuditEnabled<<" hook_sample_every_locked="<<hookSampleEvery;Log(s.str());
    Log(std::string("window_audit_ready contract=IRIS_WINDOW_AUDIT_082 enabled=")+(WindowAuditEnabled()?"1":"0")+" phases=pre_native,post_native,pre_tick,post_tick,medical gate_policy=split_query_medical_083 new_hooks=0 new_threads=0");
    // 088新阶段复用碰撞诊断总门；关闭后不创建额外QPC/摘要锁，优化功能开关独立。
    // 089独立记录实际省掉的扫掠，不能将一次额外宽相或复用的逻辑接触冒充原始物理工作。
    {std::ostringstream out;out<<"work_trace_ready contract=IRIS_WORK_TRACE_091 enabled="<<(workTraceEnabled&&DetailsEnabled())<<" sample_every="<<workTraceEvery<<" native_gap="<<Switch(ini,L"EnableNativeGapProfiling",false)<<" new_hooks=0 new_threads=0 query_medical_policy_unchanged=1";Log(out.str());}
    // 090日志不将单段宽相省掉的一次扫掠冒充减少一次总命令；额外宽相仍计真实预算。
    {std::ostringstream out;out<<"query_boundary_ready contract=IRIS_QUERY_BOUNDARY_093 enabled="<<(queryBoundaryOption&&InterfaceEnabled())<<" report=callback_blocks execution_scope=SDK_call_minus_instrumented_reports direct_ray_report_embedded=1 no_per_shape_clock=1 new_hooks=0 new_threads=0";Log(out.str());}
    {std::ostringstream out;out<<"interface_probe_ready contract=IRIS_INTERFACE_PROBE_092 interface_enabled="<<InterfaceEnabled()<<" full_roots=1 probe_cost="<<RangedProbeCostEnabled()<<" alternate_single="<<(probeABOption&&RangedProbeCostEnabled())<<" extra_reference_queries=0 new_hooks=0 new_threads=0";Log(out.str());}
    Log("conservative_diagnostics_ready contract=IRIS_CONSERVATIVE_QUERY_094 source_version=0.4.54 counters=per_query_single_merge per_shape_clock=0 extra_reference_queries=0");
    Log("spatial_projectiles_ready contract=IRIS_SPATIAL_PROJECTILES_090 group_scope=current_batch_value_only group_max=8 projectile_limit=none idle_pool_max=96 shared_probe_commands=counted original_event_order=1 async=0 new_threads=0");
    Log("ranged_work_ready contract=IRIS_RANGED_WORK_089 reuse_scope=same_batch_float_bits empty_proof=whole_union_no_character precise_sweep=original_if_possible shadow_default=0 hard_budget=64 async=0 new_threads=0");
    Log("query_batch_ready contract=IRIS_QUERY_BATCH_088 scene_query_mode=synchronous capacity=8 hard_budget=64 capsule_reservation=local fallback=exact_mode_only conservative_anomaly=skip_item async=0 new_threads=0");
    Log(std::string("contact_work_ready contract=IRIS_CONTACT_WORK_087 collision_profile=")+(CollisionProfileEnabled()?"1":"0")+" memo_slots=16 memo_collision=recheck collect_skip=already_accepted_identity shader_curve=shared_sample_position source_path_geometry_unchanged=1 character_geometry_policy=config094 medical_unchanged=1 query_budget=64 job_paths_per_visit=8 per_shape_IO=0 new_hooks=0 new_threads=0");
    Log("sweep_shape_index_ready contract=IRIS_SWEEP_SHAPE_INDEX_086 lookup=shape_pointer_equality local_query_only=1 small_linear=16 inline_slots=128 allocation_failure=linear_fallback added_queries=0 changed_geometry=0 new_threads=0");
    Log("hook_audit_ready contract=IRIS_HOOK_AUDIT_078 hooks=16 total_scope=callback_including_original samples=all_calls_and_locked_independent storage=atomic_fixed_memory per_call_file_IO=0 new_hooks=0 new_threads=0");Flush(true);
}
void BeginFrame(){if(!PerformanceEnabled())return;Guard guard;frameOpen=true;++frameId;for(unsigned i=0;i<KIND_COUNT;++i)frameMs[i]=0;Add(SAFE_FRAMES);}
void EndFrame(){
    if(!PerformanceEnabled())return;Guard guard;if(!frameOpen)return;
    for(unsigned i=0;i<KIND_COUNT;++i)if(Active(Kind(i))&&i!=DAMAGE_WAIT&&!WaitKind(Kind(i))){run[i].Frame(frameMs[i]);window[i].Frame(frameMs[i]);}
    frameOpen=false;
    // 故障/重置若发生在安全帧内部，等该帧全部计时提交后再强制摘要，避免半帧统计。
    if(summaryPending){summaryPending=false;std::string reason=pendingReason;pendingReason.clear();Summary(reason.c_str(),true);}
    if(frameMs[SAFE_TICK]>=slowMs){std::ostringstream s;s<<"audit_slow_safe_frame frame="<<frameId<<" total_ms="<<frameMs[SAFE_TICK]<<" combat_ms="<<frameMs[COMBAT_TICK]<<" medical_ms="<<frameMs[DAMAGE_FLUSH]<<" log_ms="<<frameMs[LOG_FLUSH]<<" nested_timings_not_additive=1 FPS_measured=0";Log(s.str());}
}
void Summary(const char* reason,bool force){
    if(!enabled||!initialized||(!performance&&!resource))return;Guard guard;if(force&&frameOpen){summaryPending=true;pendingReason=reason;return;}double now=Now();if(!force&&now-windowBegin<summarySeconds*1000)return;++summaryId;
    // 同id包含窗口和进程累计；进程累计读档不重置。每个通道记录全部安全帧含零查询/暂停，不能只挑慢帧。
    // 052先快照并开启下一窗口，再格式化/落盘。摘要自身引起的log_flush耗时归入下一窗口，不能在末尾清零丢掉。
    Stats snapshot[2][KIND_COUNT];Count counterSnapshot[2][COUNTER_COUNT],peakSnapshot[2][GAUGE_COUNT],resourceSnapshot[GAUGE_COUNT];
    const double windowElapsed=std::max(0.0,now-windowBegin);
    for(unsigned i=0;i<KIND_COUNT;++i){snapshot[0][i]=window[i];snapshot[1][i]=run[i];window[i]=Stats();}
    for(unsigned j=0;j<COUNTER_COUNT;++j){counterSnapshot[0][j]=windowCounters[j];counterSnapshot[1][j]=runCounters[j];windowCounters[j]=0;}
    for(unsigned j=0;j<GAUGE_COUNT;++j){resourceSnapshot[j]=current[j];peakSnapshot[0][j]=windowPeak[j];peakSnapshot[1][j]=runPeak[j];windowPeak[j]=current[j];}
    windowBegin=now;unsigned timingLines=0;
    for(unsigned scope=0;scope<2;++scope){Stats* samples=snapshot[scope];Count* totals=counterSnapshot[scope];Count* peaks=peakSnapshot[scope];
        const char* name=scope?"process":"window";std::ostringstream c;c<<"audit_counters id="<<summaryId<<" scope="<<name<<" reason="<<reason<<" frame="<<frameId<<" elapsed_ms="<<(scope?std::max(0.0,now-processBegin):windowElapsed);for(unsigned j=0;j<COUNTER_COUNT;++j)c<<" "<<counters[j]<<"="<<totals[j];c<<" dropped_log_bytes="<<droppedBytes;Log(c.str());
        for(unsigned i=0;i<KIND_COUNT;++i){const Stats& a=samples[i];if(!Active(Kind(i))||(!a.calls&&!a.frames))continue;std::ostringstream s;s<<std::setprecision(10)<<"audit_timing id="<<summaryId<<" scope="<<name<<" channel="<<names[i]<<" calls="<<a.calls<<(WaitKind(Kind(i))?" wait_ms_total=":" cpu_ms=")<<a.ms<<(WaitKind(Kind(i))?" max_wait_ms=":" max_call_ms=")<<a.maxCall<<" histogram_samples="<<a.frames<<" sample_basis="<<(WaitKind(Kind(i))?"request_wall_latency":"all_safe_frames")<<" nonzero_samples="<<a.activeFrames<<" max_histogram_sample_ms="<<a.frameMax<<" p50_upper_ms="<<a.Percentile(50)<<" p95_upper_ms="<<a.Percentile(95)<<" p99_upper_ms="<<a.Percentile(99)<<" histogram=";for(unsigned b=0;b<16;++b)s<<(b?",":"")<<a.buckets[b];s<<" CPU_side="<<(WaitKind(Kind(i))?0:1)<<" FPS_measured=0";Log(s.str());++timingLines;}
        std::ostringstream g;g<<"audit_resources id="<<summaryId<<" scope="<<name<<" frame="<<frameId;for(unsigned j=0;j<GAUGE_COUNT;++j)g<<" "<<gauges[j]<<"="<<resourceSnapshot[j]<<" "<<gauges[j]<<"_peak="<<peaks[j];g<<" shared_assets_not_bytes=1 GPU_bytes_measured=0";Log(g.str());
    }
    InterfaceSummary(summaryId);ProbeCostSummary(summaryId); // 092仅原窗口摘要输出。
    WorkTraceSummary(summaryId); // 091同一既有摘要窗口，阶段只抽样不逐帧IO。
    IrisNativeAudit::Summary(summaryId); // 084独立前缀/单笔桶，旧audit_timing按帧口径及结束标记保持。
    WindowAuditSummary(summaryId);
    HookSummary(summaryId,windowElapsed,std::max(0.0,now-processBegin)); // 078十六入口×窗口/进程=32行，不从高频Hook写日志。
    // 052离线读取器只提交有end标记且窗口/进程资源完整的摘要，崩溃/写盘失败留下的半份不冒充完整。
    {std::ostringstream end;end<<"audit_summary_end id="<<summaryId<<" frame="<<frameId<<" timing_lines="<<timingLines<<" scopes=2";Log(end.str());}
    Flush(true);
}
// 深度归因独立于旧资源/碰撞子开关：只给“实际有根且未封口”的已映射接口补时钟。
// 旧Record仍按旧门返回，资源日志关闭时也不额外输出resource_begin/end，不改变原配置语义。
bool InterfaceScope::ClockNeeded(Kind value){
    if(!InterfaceEnabled())return false;
    switch(value){
    case RESOURCE_GROUP:case VISUAL_CREATE:case MATERIAL_LOAD:case ASSET_READ:case PREWARM:
    case NATIVE_TERRAIN_RAY:case NATIVE_SPHERE_SWEEP:case RANGED_BATCH_QUERY:
    case PATH_BUILD:case CONTACT_COLLECT:case DAMAGE_ENQUEUE:case ATTACHMENT_UPDATE:case TRAIL_UPDATE:{
        CombatInterfaceFrame* owner=static_cast<CombatInterfaceFrame*>(InterfaceTLSRead());
        return owner&&!owner->sealed;
    }
    default:return false;}
}
// 092accumulate只借至当前析构；A/B开启可独立于旧碰撞明细取样，父日志关闭仍不读时钟。
Scope::Scope(Kind value,const char* text,double* accumulatedMs):kind(value),begin(0),label(text),active(Active(value)||(accumulatedMs&&RangedProbeCostEnabled())||InterfaceScope::ClockNeeded(value)),accumulate(accumulatedMs){
    if(active){if(ResourceKind(kind)&&label&&resource)Log(std::string("resource_begin channel=")+names[kind]+" name="+label);begin=Now();interfacePart.FromKind(kind,begin);}
}
Scope::~Scope(){if(!active)return;const double end=Now();double elapsed=std::max(0.0,end-begin);interfacePart.Finish(end);if(accumulate)*accumulate+=elapsed;Record(kind,elapsed);
    if(ResourceKind(kind)&&label&&resource){try{std::ostringstream s;s<<"resource_end channel="<<names[kind]<<" name="<<label<<" cpu_ms="<<elapsed<<" failed="<<(std::uncaught_exception()?1:0)<<" GPU_measured=0";Log(s.str());}catch(const std::exception&){ErrorLog("IrisArsenal resource timing format failed");}}
}
}
