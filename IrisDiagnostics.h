#pragma once
// 052：固定内存的长期审计，只有插件回调触发；不创建线程、不轮询、不读取或改写游戏状态。
#include <string>
namespace IrisDiagnostics {
typedef unsigned __int64 Count;
// 089新通道为原ranged_batch的子阶段；既有碰撞明细总门关闭后无新增QPC/计数锁。
// 090空间构组计时与纯值计数沿用碰撞明细门；每弹结束汇总另有独立INI门。
// 097末尾追加sector_query及工作量；父日志门关闭不读新增QPC，不改旧索引。
// 098末尾只追加钻头球形查询子统计；索引/旧通道保持，不能将子耗时再次加总。
enum Kind {SAFE_TICK,COMBAT_TICK,SPHERE_QUERY,SWEEP_QUERY,CAPSULE_QUERY,CYLINDER_QUERY,
    DAMAGE_FLUSH,NATIVE_DAMAGE,DAMAGE_WAIT,RESOURCE_GROUP,VISUAL_CREATE,MATERIAL_LOAD,PREWARM,ASSET_READ,PROOF_QUERY,LOG_FLUSH,QUERY_WAIT,QUERY_READY_WAIT,QUERY_PAUSE_WAIT,QUERY_PHYSICS_WAIT,QUERY_AI_WAIT,QUERY_UNAVAILABLE_WAIT,MEDICAL_READY_WAIT,MEDICAL_PAUSE_WAIT,MEDICAL_PHYSICS_WAIT,MEDICAL_AI_WAIT,MEDICAL_UNAVAILABLE_WAIT,DAMAGE_IDENTITY,DAMAGE_CALCULATE,DAMAGE_XP,DAMAGE_RESULT,QUERY_JOBS,CAPSULE_BATCH_QUERY,CAPSULE_BATCH_REFERENCE,VISUAL_UPDATE,NATIVE_TERRAIN_RAY,NATIVE_SPHERE_SWEEP,SWEEP_RESULT_FINALIZE,CAPSULE_CANDIDATES,CAPSULE_EXACT,CAPSULE_RESULTS,CONTACT_COLLECT,RANGED_FILTER,PATH_BUILD,DAMAGE_ENQUEUE,ATTACHMENT_UPDATE,TRAIL_UPDATE,RANGED_BATCH_QUERY,RANGED_BATCH_CREATE,RANGED_BATCH_RAYS,RANGED_BATCH_BODIES,RANGED_BATCH_RELEASE,RANGED_REUSE_LOOKUP,RANGED_EMPTY_PROBE,RANGED_SPATIAL_BUILD,CAPSULE_APPROX,SECTOR_QUERY,DRILL_SPHERE_QUERY,DAMAGE_CATCHUP_FLUSH,QUERY_GATE_REFINE,KIND_COUNT};
// 056在末尾追加批量/慢调用计数；CAPSULE_CACHE保留旧索引，缓存已退役，值保持0。
// 081末尾追加异常形体跳过数，既有日志总开关关闭后不累计，不新增逐形体日志。
// 080末尾追加省略工作量，不移动旧索引；visual_update需明细开启，计数沿用性能总开关。
/* 086索引计数只追加；关闭明细后不累计，旧计数索引/消费者保持。 */
enum Counter {SAFE_FRAMES,FRAME_CALLBACKS,UNSAFE_SKIPS,QUERY_CALLS,QUERY_CACHE,QUERY_RETRY,QUERY_BUSY_WAIT,QUERY_BUDGET_WAIT,
    QUERY_RAW,QUERY_CONTACTS,QUERY_RECOVERED,QUERY_OVERFLOW,EVENTS_EMITTED,DAMAGE_QUEUED,DAMAGE_APPLIED,DAMAGE_BLOCKED,
    DAMAGE_MISSED,DAMAGE_REJECTED,STALE_DAMAGE,CASTS_STARTED,CASTS_ENDED,FRESH_VISUALS,POOL_REUSES,DISPOSED_VISUALS,DAMAGE_OVER_TARGET,MEDICAL_TIME_YIELDS,MEDICAL_COUNT_YIELDS,MEDICAL_SAFETY_YIELDS,MEDICAL_SCAN_YIELDS,IDENTITY_COMPARISONS,IDENTITY_PROBES,IDENTITY_DUPLICATES,IDENTITY_TABLES,CYLINDER_BUFFER_GROWTH,JOB_TRANSFERS,JOB_ROTATIONS,CAPSULE_CACHE,BATCH_ATTEMPTS,BATCH_SUCCESSES,BATCH_FALLBACKS,BATCH_SHADOWS,BATCH_MATCHES,BATCH_MISMATCHES,BATCH_CANDIDATES,BATCH_SHAPE_TESTS,BATCH_LOGICAL_CHARGE,BATCH_SAVED_CALLS,NATIVE_SLOW_HITS,NATIVE_SLOW_NOTICES,BATCH_NO_HEADROOM,BATCH_EXTRA_CALLS,PROJECTILE_WALL_SKIPS,RANGED_CONTACT_CHECKS,RANGED_CONTACT_REUSES,VISUAL_PARAMETER_WRITES,VISUAL_PARAMETER_REUSES,BATCH_SKIPPED_IDENTITY,BATCH_SKIPPED_GEOMETRY,SWEEP_SHAPE_COMPARISONS,SWEEP_SHAPE_PROBES,SWEEP_SHAPE_LINEAR_EQUIVALENT,SWEEP_SHAPE_TABLES,SWEEP_SHAPE_INDEX_FALLBACKS,RANGED_MEMO_COLLISIONS,COLLECT_CONTACTS,COLLECT_DUPLICATES,COLLECT_CHECKS,COLLECT_INSERTS,PATHS_BUILT,CURVE_SAMPLE_REUSES,TERRAIN_RAW,SWEEP_RAW,SWEEP_SORTED,BATCH_ELIGIBLE,BATCH_LOCAL_RESERVATION,BATCH_LOCAL_BLOCKED,RANGED_BATCH_ATTEMPTS,RANGED_BATCH_ITEMS,RANGED_BATCH_RAYS_COUNT,RANGED_BATCH_SWEEPS_COUNT,RANGED_BATCH_CYLINDERS_COUNT,RANGED_BATCH_UNAVAILABLE,RANGED_BATCH_FAILURES,RANGED_BATCH_UNUSED,RANGED_EXACT_REUSES,RANGED_REUSE_FAILURES,RANGED_EMPTY_PROBES,RANGED_EMPTY_CANDIDATES,RANGED_EMPTY_CHARACTERS,RANGED_EMPTY_UNKNOWN,RANGED_EMPTY_PATHS,RANGED_EMPTY_SAVED,RANGED_EMPTY_BUSY,RANGED_EMPTY_HEADROOM,RANGED_EMPTY_SPARSE,RANGED_EMPTY_SMALL,RANGED_EMPTY_INVALID,RANGED_EMPTY_DISABLED,RANGED_EMPTY_SHADOWS,RANGED_EMPTY_MISMATCHES,RANGED_SPATIAL_BATCHES,RANGED_SPATIAL_GROUPS,RANGED_SPATIAL_MERGES,RANGED_SPATIAL_PAIRS,RANGED_SPATIAL_SINGLES,RANGED_SPATIAL_MULTIS,RANGED_SPATIAL_COVERED,RANGED_SPATIAL_SKIPPED_SINGLES,RANGED_SPATIAL_EMPTY_SINGLES,RANGED_SPATIAL_EMPTY_MULTIS,PROJECTILE_SPAWNS,PROJECTILE_VECTOR_GROWTH,PROJECTILE_UNVISITED,IDLE_POOL_TRIMS,PARAMETER_CACHE_FALLBACKS,WEAPON_COUNT_REUSE,WEAPON_COUNT_FALLBACK,WEAPON_CHILD_VISITS,APPROX_SPHERES,APPROX_CAPSULES,APPROX_CYLINDERS,APPROX_CAPSULE_BATCHES,APPROX_RAW,APPROX_CONTACTS,APPROX_TESTS,APPROX_SKIP_IDENTITY,APPROX_SKIP_GEOMETRY,APPROX_SKIP_CAPACITY,APPROX_SKIP_INPUT,SECTOR_VOLUMES_BUILT,SECTOR_REQUESTS,SECTOR_PLANES,SECTOR_RAW,SECTOR_CONTACTS,DRILL_SPHERE_REQUESTS,DRILL_SPHERE_RAW,DRILL_SPHERE_CONTACTS,DRILL_SPHERE_CACHE,MEDICAL_CATCHUP_WINDOWS,MEDICAL_CATCHUP_CALLS,MEDICAL_CATCHUP_INSPECTED,MEDICAL_CATCHUP_EXTRA_HITS,QG_SINGLE_OLD_FALSE,QG_CAPSULE_OLD_FALSE,QG_RANGED_OLD_FALSE,QG_ALLOW,QG_DISABLED,QG_WORLD_INVALID,QG_WORKER_BUSY,QG_BAD_QUEUE,QG_PENDING_CREATE,QG_PENDING_DESTROY,QG_PENDING_TERRAIN,QG_PENDING_OTHER,QG_SDK_NOT_WRITABLE,QG_SDK_UNAVAILABLE,QG_SDK_ERROR,QG_SCENE_CHANGED,QG_MASK_CREATE_MAIN,QG_MASK_CREATE_BACK,QG_MASK_HULL_DESTROY_MAIN,QG_MASK_HULL_DESTROY_BACK,QG_MASK_ACTOR_DESTROY_MAIN,QG_MASK_ACTOR_DESTROY_BACK,QG_MASK_TERRAIN_MAIN,QG_MASK_TERRAIN_BACK,QG_MASK_GROUP_MAIN,QG_MASK_GROUP_BACK,QG_MASK_IMPULSE_MAIN,QG_MASK_IMPULSE_BACK,QG_MASK_TRACER_ADD_MAIN,QG_MASK_TRACER_ADD_BACK,QG_MASK_TRACER_REMOVE_MAIN,QG_MASK_TRACER_REMOVE_BACK,QG_MASK_DOOR,COUNTER_COUNT};
enum Gauge {ACTORS,ACTIVE_ACTORS,RESERVED_ACTORS,PROJECTILES,RESIDUES,IDLE_VISUALS,ATTACHED_VISUALS,JOBS,PENDING_DAMAGE,WARM_ASSETS,RETIRED_GUNS,GAUGE_COUNT};
void Initialize(const std::wstring& directory,const std::wstring& logFile);
bool PerformanceEnabled();bool DetailsEnabled();double Now();
// 087仅当日志/性能/明细及本开关同时开启才计时；原物理回调返回后汇总，不在其中取得诊断锁。
// 新通道是已有父计时的子阶段，不能直接相加；开关只停诊断，不关闭优化/查询/原预算时钟。
bool CollisionProfileEnabled();
// 094关闭门后无新计时/锁/逐形体输出；查询退出后单次汇总纯值，旧计数索引保持。
bool ConservativeQueryLoggingEnabled();
/* 099仅控制新增追赶子统计/有界样本；父日志关闭时不读新时钟、不拿新增统计锁。
   damage_catchup_flush是damage_flush子集，不能再次加总为CPU总量。 */
bool DamageCatchupLoggingEnabled();
/* 100只观察旧门拒绝后的细分，关闭时不新增QPC、统计锁或IO。
   source区分单条/胶囊/远程批次；位计数可重叠，不可相加冒充独立请求数。 */
bool QueryGateLoggingEnabled();
void RecordQueryGate(unsigned source,unsigned reason,unsigned mask,unsigned exceptionCode,double ms,double at);
void RecordConservativeQuery(unsigned kind,unsigned raw,unsigned contacts,unsigned tests,unsigned identity,unsigned geometry,unsigned capacity,unsigned input);
// 097旧自写胶囊内核已退役，其同输入微测接口一并移除；只保留真实查询工作量。

// 092全量接口归因只围住现有安全线程的一次战斗调用，TLS仅借用栈地址，不存引擎指针。
// 缺项关闭；关闭不读TLS/QPC，子接口不加统计锁，根退出后一次合计。inclusive不可直接相加。
enum InterfacePart {IF_ROOT,IF_WRAPPER,IF_SETUP,IF_ACTOR_READY,IF_ACTOR_REQUEST,IF_ACTOR_ANIMATION,
    IF_ACTOR_POSE,IF_ACTOR_FINISH,IF_TAIL,IF_WEAPON_LOOKUP,IF_SOURCE_POSE,IF_ATTACHMENTS,IF_TRAIL,IF_BLADE_PATH,
    IF_EMIT,IF_BLAST,IF_POOL_BORROW,IF_POOL_RETURN,IF_VISUAL,IF_VISUAL_NODE,IF_VISUAL_PARAMETERS,IF_VISIBILITY,
    IF_EFFECTS,IF_SHOT_BATCH,IF_SHOT_CONSUME,IF_SHOT_TERMINATE,IF_RESIDUES,IF_JOBS,IF_CONTACT_GATE,
    IF_COLLECT,IF_ENQUEUE,IF_JOB_ROTATE,IF_LEDGER,IF_BEAM_DRAW,IF_PHYSICS,IF_RESOURCE,IF_PREWARM,IF_DIAGNOSTICS,
    IF_READY_ANIMATIONS,IF_WEAPON_SCAN,IF_QUERY_SUBMIT,IF_QUERY_EXECUTE,IF_QUERY_FINISH,IF_QUERY_REPORT,IF_QUERY_NARROW,IF_PART_COUNT};
class CombatInterfaceFrame;
class InterfaceScope {
    friend class CombatInterfaceFrame;
    CombatInterfaceFrame* frame;CombatInterfaceFrame* boundary;InterfaceScope* previous;InterfacePart part;double begin,children;
public:
    explicit InterfaceScope(InterfacePart value=IF_PART_COUNT);~InterfaceScope();
    void Begin(InterfacePart value,double at=0);void Finish(double at=0);void Switch(InterfacePart value);
    void FromKind(Kind kind,double at);static bool ClockNeeded(Kind kind);
private:InterfaceScope(const InterfaceScope&);InterfaceScope& operator=(const InterfaceScope&);
};
class CombatInterfaceFrame {
    friend class InterfaceScope;
    bool active,sealed;unsigned generation,nested,badClocks;Count token;
    double begin,endedAt,inclusive[IF_PART_COUNT],exclusive[IF_PART_COUNT],maxCall[IF_PART_COUNT];
    Count calls[IF_PART_COUNT];InterfaceScope* top;
public:
    CombatInterfaceFrame();~CombatInterfaceFrame();
private:CombatInterfaceFrame(const CombatInterfaceFrame&);CombatInterfaceFrame& operator=(const CombatInterfaceFrame&);
};
void ResetCombatInterfaceAudit();
// 093仅显式开启且完整接口根有效时分解同步查询；回调只写当前栈，SDK退出后才合计。
// IF_QUERY_EXECUTE的exclusive扣除报告回调；并不等于纯CPU/硬件采样，不能当作引擎极限证明。
InterfacePart QueryBoundaryPart(InterfacePart part);
// 092A/B仅交替单段空区门，不改原精确体积/地形/命中；每批只执行一个策略，不重放额外查询。
// arm=0无单段宽相、1有单段宽相、2仅观察原配置。配对按相邻合格批，实际输入仍需日志核对。
bool RangedProbeCostEnabled();
bool SelectRangedSingleProbe(bool configured,bool eligible,unsigned& arm);
struct RangedProbeSample {
    unsigned arm,items,spheres,cylinders,commands,reuses,probes,saved,busy,unknown,failures;
    double totalMs,raysMs,bodiesMs,probeMs,distanceSum,radiusSum;
};
void RecordRangedProbeCost(const RangedProbeSample& value);

// 091仅本插件Tick/Flush按调用抽样，固定栈数组；关闭/未抽中不读时钟、不分配、不进统计锁。
// 阶段互斥，重复阶段累计；析构包含continue/return/异常退出，摘要不能与旧父计时直接相加。
enum WorkDomain {WORK_COMBAT,WORK_MEDICAL,WORK_DOMAIN_COUNT};
enum WorkPart {WORK_SETUP,WORK_ACTOR_READY,WORK_ACTOR_REQUEST,WORK_ACTOR_ANIMATION,
    WORK_ACTOR_POSE,WORK_ACTOR_VISUAL,WORK_ACTOR_PATH,WORK_ACTOR_EVENTS,WORK_ACTOR_FINISH,
    WORK_EFFECTS,WORK_JOBS,WORK_TAIL,WORK_MEDICAL_SAFETY,WORK_MEDICAL_POP,WORK_MEDICAL_WAIT,
    WORK_MEDICAL_IDENTITY,WORK_MEDICAL_CALCULATE,WORK_MEDICAL_NATIVE,WORK_MEDICAL_XP,WORK_MEDICAL_RESULT,WORK_PART_COUNT};
class WorkTrace {
    WorkDomain domain;bool active;WorkPart part;double begin,last,elapsed[WORK_PART_COUNT];unsigned visits[WORK_PART_COUNT];
public:
    explicit WorkTrace(WorkDomain value);~WorkTrace();void Mark(WorkPart value);
private:WorkTrace(const WorkTrace&);WorkTrace& operator=(const WorkTrace&);
};
// 078：仅显式开启时做原子累计与抽样QPC；关闭不计时/计数，不拿诊断锁、不分配内存。
// BeforeLock/Acquired/BeforeUnlock夹住已有锁，采样只记录获取锁及受保护段墙钟，不能当FPS或锁竞争证明。
// 078覆盖十六个实际已安装入口；没有增加Hook。总回调含原生调用/嵌套耗时，
// 与原锁计时独立抽样，不可将各入口相加当作模组净CPU或呈现FPS。
enum Hook {HOOK_CHOOSE,HOOK_START,HOOK_RUN,HOOK_BLOCK,HOOK_STUMBLE,
    HOOK_FRAME,HOOK_SAFE,HOOK_RANGED_USE,HOOK_RANGED_HAS,HOOK_RANGED_SCORE,HOOK_RANGED_WITHIN,
    HOOK_RANGED_GUN,HOOK_RANGED_ANIMATION,HOOK_RANGED_SHOT,HOOK_RANGED_RELOAD,HOOK_DEFENCE,HOOK_COUNT};
class HookAudit {
    Hook hook;bool active,sampled,totalSampled;unsigned entries;double waitBegin,workBegin,waitTotal,workTotal,totalBegin;
public:
    explicit HookAudit(Hook value);~HookAudit();
    void BeforeLock();void Acquired();void BeforeUnlock();
private:HookAudit(const HookAudit&);HookAudit& operator=(const HookAudit&);
};
// 082所有状态均为本次同步读取的纯值：-1表示未读取，不能把未知当作false；不携带引擎地址。
// 只有总日志/性能/明细/窗口审计全部开启才观察；只复用主线程原Hook，不新增线程或锁对象。
enum WindowPhase {WINDOW_PRE_NATIVE,WINDOW_POST_NATIVE,WINDOW_PRE_TICK,WINDOW_POST_TICK,WINDOW_MEDICAL,WINDOW_PHASE_COUNT};
struct WindowState {
    int physicsRunning,queuesClear,aiRunning,paused,unavailable;bool failed;
    WindowState():physicsRunning(-1),queuesClear(-1),aiRunning(-1),paused(-1),unavailable(-1),failed(false){}
};
bool WindowAuditEnabled();bool WindowAuditHasWork();bool BeginWindowAudit();
void RecordWindowAudit(WindowPhase phase,const WindowState& state,double probeMs);
void RecordMedicalWindow(const WindowState& state,const char* reason,const char* cause,Count before,Count remaining,unsigned done,unsigned inspected,double observedAt,double oldest);
void FinishWindowAudit();void ResetWindowAudit();
// 055按主线程相邻观察点的“上次状态”分摊等待，不冒充线程精确运行时间；优先暂停/物理/AI/世界无效。
// 不访问游戏指针。累计时钟为进程纯值；请求复制快照后求差，读档丢弃旧请求而不混入新代次。
struct WaitStamp {double pause,physics,ai,unavailable;WaitStamp():pause(0),physics(0),ai(0),unavailable(0){}};
void ObserveWindow(bool paused,bool physicsBusy,bool aiBusy,bool unavailable);
void SnapshotWaits(double now,WaitStamp& stamp);
void RecordWait(bool query,double created,const WaitStamp& before,double now);
void Log(const std::string& message);void Flush(bool force);
void Add(Counter counter,Count amount=1);void Set(Gauge gauge,Count value);
void Record(Kind kind,double milliseconds);void BeginFrame();void EndFrame();
void Summary(const char* reason,bool force=false);
// 053队列计数分别记录墙钟超目标、时间/次数/安全窗口/扫描上限让出；累计不改变伤害事件。
// label只借用到析构；资源阶段记录begin/end，异常展开也记录failed=1，不能把失败加载记为成功。
class Scope {
    Kind kind;double begin;const char* label;bool active;double* accumulate;InterfaceScope interfacePart;
public:
    explicit Scope(Kind value,const char* resourceLabel=0,double* accumulatedMs=0);~Scope();
private:Scope(const Scope&);Scope& operator=(const Scope&);
};
}
