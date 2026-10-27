#pragma once
#include <vector>
#include "SectorPlanes.h"
// 正式PhysX头只在独立翻译单元使用，避免与KenshiLib中重声明的NxVec3/NxShapeFlag相互覆盖。
// 接口只传值：scene仅在当前物理/AI静止窗口借用，结果不携带NxShape/NxActor或userData地址。
namespace IrisNative {
struct Point {float x,y,z;};
struct ObjectKey {unsigned type,container,containerSerial,index,serial;bool present;};
struct Contact {ObjectKey object;Point point;float fraction;bool pointValid;unsigned sourceIndex;};
// 081：256只作为常见规模的内联存储，不再是结果上限；更大名单按需倍增，094近似模式分配异常仅跳过该项。
const unsigned CONTACT_INLINE_CAPACITY=256;
// 精确记录拒绝发生在哪个字段；历史invalid_contact日志无法区分输入、比例、身份及坐标。
// 诊断只有值，不外传形体地址；保留t的原始位型、坏point和身份读取异常码，以区分数值/读取失败。
// sourceIndex是原回调结果序号，排序和同形体替换后仍可准确定位缺失坐标的那条接触。
enum QueryIssue {ISSUE_NONE,ISSUE_INPUT_SCENE,ISSUE_INPUT_RADIUS,ISSUE_INPUT_ORIGIN,ISSUE_INPUT_MOTION,
    ISSUE_ZERO_MOTION,ISSUE_HIT_SHAPE,ISSUE_HIT_FRACTION,ISSUE_HIT_RANGE,ISSUE_KEY_READ,ISSUE_CAPACITY,ISSUE_POINT_REQUIRED,ISSUE_CYLINDER_GEOMETRY,ISSUE_BATCH_INPUT,ISSUE_BATCH_CANDIDATES,ISSUE_BATCH_WORK,ISSUE_BATCH_SHAPE,ISSUE_RAY_FIELDS};
// 077仅传回本次原生环境射线的纯值事实。没有命中时hit=0、distance=-1；
// metadata=1才可解释shapeType/shapeGroup/trigger，关闭战斗明细不读取这些额外SDK字段。
// 不传shape/actor地址，不跨帧保留场景所有权，也不把诊断字段用于伤害资格。
struct TerrainInfo {unsigned groups,hit,shapeType,shapeGroup,trigger,metadata;float distance;};
struct Diagnostic {QueryIssue issue;unsigned received,uniqueBeforeFailure,missingPoints,hitIndex;float rawFraction;Point rawPoint;unsigned fractionBits,identityException,recoveredInitial;
    // 055仅记录本次查询的纯值工作量；字段随结果按值传递，不属于游戏/PhysX ABI。
    unsigned identityComparisons,identityProbes,identityDuplicates,identityTables,bodyBufferGrowth;TerrainInfo terrain;
    /* 086只追加本次同步扫掠的纯值；旧aggregate初始化会把尾字段清零，不改变PhysX/游戏ABI。
       linearEquivalent由最终下标推导旧线性查找的比较数，不额外执行旧查询或旧扫描。 */
    unsigned __int64 sweepShapeComparisons,sweepShapeProbes,sweepShapeLinearEquivalent,sweepShapeTables,sweepShapeIndexFallbacks;
    // 094仅追加纯值，原aggregate将尾部清零；异常项跳过，不能用整批重查掩盖异常。
    unsigned approximateKind,skippedIdentity,skippedGeometry,skippedCapacity,skippedInput;};
// 081：items始终指向本对象自有连续内存。复制只复制有效count，不复制指针所有权；
// 常见<=256结果零额外堆分配，超过后保留扩容容量供同一工作区复用，不缓存任何SDK指针。
struct Contacts {
    Contact* items;unsigned count;Diagnostic diagnostic;
    Contacts();Contacts(const Contacts& other);Contacts& operator=(const Contacts& other);
    bool Append(const Contact& value);
private:
    Contact local[CONTACT_INLINE_CAPACITY];std::vector<Contact> storage;
    bool Ensure(unsigned required);
};
enum QueryStatus {QUERY_COMPLETE,QUERY_UNSUPPORTED,QUERY_OVERFLOW,QUERY_INVALID,QUERY_NOT_READY};
// 094启动配置只在既有安全Tick锁内写入；查询只读，不新增线程或场景同步对象。
void ConfigureConservativeQueries(bool enabled);
bool ConservativeQueriesEnabled();
// 097胶囊使用原生AABB overlap，不再配置已退役的自写扩盒内核/影子审计。
bool Initialize();
/* 100只在原主线程安全点、实际消息全部为空后调用；检查同一SDK及公开isWritable。
   这是场景状态查询，不是锁/等待/清队列；未知或异常一律不授予许可。 */
enum SceneReadiness {SCENE_WRITABLE,SCENE_NOT_WRITABLE,SCENE_UNAVAILABLE,SCENE_STATE_ERROR};
SceneReadiness InspectSceneReadiness(void* scene,unsigned& exceptionCode);
const char* AvailabilityReason();
const char* IssueReason(QueryIssue issue);
// 同一条原有球扫掠：NxCapsule两端重合，motion仍是完整有限位移；ALL_HITS一次收集所有接触。
// 必需形体/比例/身份或容量失败时整批无效；坐标单列pointValid，由真正需要坐标的爆炸消费者判定。
// QUERY_NOT_READY只表示SDK暂未建立，不能缓存为接口永久不支持；回调不进入伤害或生命周期函数。
QueryStatus SweepAll(void* scene,const Point& from,const Point& motion,float radius,unsigned groups,Contacts& result,unsigned& queryCalls,bool charactersOnly=false);
// 077：环境沿用本机原生Harpoon飞行组0x087FDE47，并与调用者groups取交集；
// 角色球扫掠仍使用原groups。ALL射线只为跳过角色后继续找同组的最近环境，
// 不额外跳过建筑/触发器/t=0，也不更改原完整motion或原生SDK形体精确查询。
// 057：三远程的飞弹把有限地形射线与角色连续球扫掠分开；terrain最多一个最近非角色阻挡。
// 两次查询均完整成功才返回名单；失败清空两份输出。各自fraction都以完整motion归一，
// 消费者先过滤友军再与墙比较，墙与角色同距时墙优先；两份名单独立存储，环境不挤占角色结果。
// 所有SDK形体仅借当前同步调用栈；不新建线程、锁、Actor，不修改任何共享碰撞组。
QueryStatus ProjectileAll(void* scene,const Point& from,const Point& motion,float radius,unsigned groups,Contacts& characters,Contacts& terrain,unsigned& queryCalls);
// 球形爆炸保留094开关：查询球不变，开启时用公开false模式检测形体AABB；胶囊规则见下。
// 098 boundsOnly只由钻头球事件显式启用；默认false保持其他球按既有INI选择，不改游戏ABI。
QueryStatus OverlapSphere(void* scene,const Point& center,float radius,unsigned groups,Contacts& result,unsigned& queryCalls,bool boundsOnly=false);

// 097静态刀刃/钻头统一原生overlapCapsuleShapes(false)；零长胶囊用overlapSphereShapes(false)。
// 不负责弹体停止点；真实弹体的带半径扫掠和地形射线保持。
QueryStatus OverlapCapsule(void* scene,const Point& from,const Point& to,float radius,unsigned groups,Contacts& result,unsigned& queryCalls);

// 056只合批同一安全窗口内2～8条静态胶囊，不合并独立攻击段，也不接受弹道/墙阻挡查询。
// 081输入输出都为插件自有值；单个身份/几何异常只跳过该形体，其余继续。
// 097复合调用逐胶囊提交原生接口；不做联合AABB/自写扩盒/影子重查，已成功前缀独立消费。
const unsigned CAPSULE_BATCH_CAPACITY=8;
struct CapsuleInput {Point from,to;float radius;};
struct BatchDiagnostic {QueryIssue issue;unsigned candidates,characters,shapeTests,shapeTypes,skippedIdentity,skippedGeometry,identityException,geometryException;
    // completed为已成功前缀数；失败后保留未完成后缀，不重查成功项。
    unsigned conservative,skippedCapacity,skippedInput,completed;};
QueryStatus OverlapCapsules(void* scene,const CapsuleInput* paths,unsigned count,unsigned groups,Contacts* results,BatchDiagnostic& diagnostic,unsigned& queryCalls);

// 097厚扇形外接平面体：直接采用原生cullShapes的AABB裁剪结果，允许多收，只做稳定身份去重。
QueryStatus OverlapSector(void* scene,const IrisSector::Volume& volume,unsigned groups,Contacts& result,unsigned& queryCalls);

// 057有限射线取最近非角色阻挡；094角色使用保守OBB/AABB，关闭后保留原平端圆柱窄相；只返回角色。
// actualLength回传墙前有效长度，渲染必须消费同一值；原生调用最多两次，形体地址不外传。
QueryStatus CylinderAll(void* scene,const Point& from,const Point& motion,float radius,unsigned groups,Contacts& result,float& actualLength,unsigned& queryCalls);
// 088：同一安全窗口集中提交2～8条远程查询。每项仍为完整有限地形射线 + 原角色体积。
// bool=false只表示尚未提交SDK查询，可由调用者安全走旧路；true后逐项status决定消费/下轮重试，
// 不能把ALL_HITS接口返回的0当作空名单。结果/长度只有值，不保存SDK查询对象或shape地址。
const unsigned RANGED_BATCH_CAPACITY=8;
struct RangedInput {Point from,motion;float radius;bool cylinder;};
// 089别名只引用本次results较早的成功项，不复制命中数组、不跨批保存；消费者仍逐cast/event结算。
// 失败项不共享：别名逐条走原ProjectileAll重试。ray/bodyCalls只计实际SDK命令，source==自身表示独立结果。
struct RangedResult {Contacts characters,terrain;QueryStatus status;float length;unsigned bodyCalls,rayCalls,source;};
// 090空间分组只重组当前8项自有包围盒，不重排输入/结果/伤害；single为独立宽相测试门。
// 开关启动读取；allowEmpty在空间模式只因异常/显式对照失败停本次更新，普通有角色组不阻止其他空组。
struct RangedPolicy {bool reuse,empty,shadow,allowEmpty,spatial,single;unsigned maxCalls;};
struct RangedAudit {unsigned reused,reuseFailed,probeCalls,probeCandidates,probeCharacters,probeUnknown,probeException,
    emptyPaths,savedSweeps,probeBusy,probeHeadroom,probeSparse,probeSmall,probeInvalid,shadowChecks,shadowMismatches,
    spatialBatches,spatialGroups,spatialMerges,spatialPairs,spatialSingles,spatialMultis,spatialCovered,spatialSkippedSingles,spatialEmptySingles,spatialEmptyMultis;
    // 092仅借既有Scope时钟累计本批成本，根/子阶段分开；不参与几何、名单或预算。
    double totalMs,raysMs,bodiesMs,probeMs;};
bool RangedBatch(void* scene,const RangedInput* paths,unsigned count,unsigned groups,RangedResult* results,unsigned& queryCalls,RangedPolicy& policy,RangedAudit& audit);
}