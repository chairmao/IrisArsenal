// 054：沿用PhysX 2.8.4的公开Nx接口，允许最低2.8.4.6起的后续修订尝试；不手写虚表或修改共享接触报告。
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>
#include <winver.h>
#include "NativeMultiContact.h"
#include "../IrisDiagnostics.h"
#include <kenshi/util/hand.h>
#include <NxScene.h>
#include <NxSceneQuery.h> // 088只用官方同步批量接口，不启用后台线程。
#include <NxPhysicsSDK.h>
#include <NxShape.h>
#include <NxCapsule.h>
#include <NxSphere.h>
#include <NxRay.h>
#include <NxUserRaycastReport.h>
#include <NxBox.h>
#include <NxBounds3.h>
#include <NxPlane.h> // 097官方平面裁剪接口；不造Actor或改场景碰撞组。
#include <NxSphereShape.h>
#include <NxCapsuleShape.h>
#include <NxBoxShape.h>
#include <NxConvexShape.h>
#include <NxConvexMesh.h>
#include "FiniteCylinder.h"
#include <algorithm>
#include <vector>
#include <float.h>
#include <cmath>
#include <cstddef>
#include <cstring>
#include <sstream>
#include <new>
#include <stdexcept>
#include <limits>

namespace IrisNative {
// 094仅在启动时配置；同原查询在安全主线程窗口调用，无新锁/后台SDK操作。
static bool conservativeQueries=true;
void ConfigureConservativeQueries(bool enabled){conservativeQueries=enabled;}
bool ConservativeQueriesEnabled(){return conservativeQueries;}

// 081：内联结果只在超出旧常见规模后扩容；倍增摊销，永不按第257项截断。
// Append分配失败返回false；精确模式保留重试语义，094近似模式仅跳过该项，不跨SDK回调抛分配异常。
Contacts::Contacts():items(local),count(0){Diagnostic empty={ISSUE_NONE,0,0,0,0,0,{0,0,0},0,0,0};diagnostic=empty;}
Contacts::Contacts(const Contacts& other):items(local),count(0){*this=other;}
bool Contacts::Ensure(unsigned required){
    if(required<=(storage.empty()?size_t(CONTACT_INLINE_CAPACITY):storage.size()))return true;
    try{size_t target=storage.empty()?CONTACT_INLINE_CAPACITY:storage.size();
        while(target<required){if(target>storage.max_size()/2){target=required;break;}target*=2;}
        const bool inlineBefore=storage.empty();storage.resize(target);
        if(inlineBefore)for(unsigned i=0;i<count;++i)storage[i]=local[i];
        items=&storage[0];return true;
    }catch(const std::bad_alloc&){return false;}catch(const std::length_error&){return false;}
}
Contacts& Contacts::operator=(const Contacts& other){
    if(this!=&other){if(!Ensure(other.count))throw std::bad_alloc();
        for(unsigned i=0;i<other.count;++i)items[i]=other.items[i];count=other.count;diagnostic=other.diagnostic;}
    return *this;
}
bool Contacts::Append(const Contact& value){
    if(count==std::numeric_limits<unsigned>::max()||!Ensure(count+1))return false;
    items[count++]=value;return true;
}
// 来自正式头的编译期布局约束，和本机原生包装反汇编交叉核对；不是通过偏移调用引擎。
typedef char Require64Bit[(sizeof(void*)==8)?1:-1];
typedef char RequireSweepHit64[(sizeof(NxSweepQueryHit)==64)?1:-1];
typedef char RequireHand32[(sizeof(hand)==32)?1:-1];
typedef char RequireFractionAtStart[(offsetof(NxSweepQueryHit,t)==0)?1:-1];
typedef char RequirePhysX284[(NX_SDK_VERSION_NUMBER==284)?1:-1];
// 禁止裁掉官方接口功能：这些宏改变虚方法声明顺序；不同配置必须编译失败而非运行时错槽。
typedef char RequireFullSceneAPI[(NX_USE_FLUID_API&&NX_USE_CLOTH_API&&NX_USE_SOFTBODY_API&&NX_SUPPORT_SWEEP_API)?1:-1];
#ifndef NX_ENABLE_SCENE_STATS2
#error PhysX 2.8.4.6 full scene interface required
#endif
static int availability=0;
static const char* reason="not_initialized";
typedef NxPhysicsSDK* (__cdecl* GetSdkFunction)();
static GetSdkFunction getSdk=0;

// 054：四段文件版本用于最低版本比较，不能把系统PhysX安装包9.x当作本进程Core的Nx接口版本。
// 编译仍使用已核对的2.8.4完整接口；末段修订不再要求等于6，新修订只获得“可尝试”资格。
struct RuntimeVersion {
    unsigned major,minor,bugfix,revision;bool known;
    RuntimeVersion():major(0),minor(0),bugfix(0),revision(0),known(false){}
};
static bool AtLeastMinimum(const RuntimeVersion& v){
    return v.major>2||(v.major==2&&(v.minor>8||(v.minor==8&&(v.bugfix>4||(v.bugfix==4&&v.revision>=6)))));
}
static const char* RuntimeVersionGate(const RuntimeVersion& v){
    if(!v.known)return "runtime_version_unavailable";
    if(!AtLeastMinimum(v))return "runtime_below_minimum_2_8_4_6";
    // 版本号更高不能证明C++虚接口布局一致。NxScene/NxShape和回调都按2.8.4声明，
    // 跨SDK接口族需要独立适配；不能先调用未知虚表，再把一次未崩溃称作ABI校验。
    if(v.major!=2||v.minor!=8||v.bugfix!=4)return "runtime_sdk_family_not_supported";
    return 0;
}
static bool RuntimeDecision(const RuntimeVersion& v,const char* failure,bool sdkExport){
    const bool accepted=failure==0;
    if(accepted){availability=1;reason="physx_2_8_4_patch_candidate";}else{availability=-1;reason=failure;}
    // 初始化永久结果只记录一次；模块尚未加载的暂态在下方不进入此函数，不刷每帧日志。
    // accepted仅证明文件版本及C导出符合尝试条件，不表示未知新修订已获实机/ABI认证。
    std::ostringstream out;out<<"physx_compatibility contract=IRIS_PHYSX_COMPAT_054 minimum=2.8.4.6 api_family=2.8.4 runtime=";
    if(v.known)out<<v.major<<"."<<v.minor<<"."<<v.bugfix<<"."<<v.revision;else out<<"unavailable";
    out<<" accepted="<<accepted<<" sdk_export="<<sdkExport<<" reason="<<reason
       <<" revision_mode="<<(accepted?(v.revision==6?"baseline":"newer_patch_attempt"):"rejected")
       <<" validation=file_version_and_export_only scene_sdk_check=per_query runtime_verified=0";
    IrisDiagnostics::Log(out.str());return accepted;
}
bool Initialize(){
    if(availability)return availability>0;
    HMODULE core=GetModuleHandleW(L"PhysXCore64.dll"),loader=GetModuleHandleW(L"PhysXLoader64.dll");
    // RE_Kenshi插件可能早于游戏创建SDK。模块未加载是暂态，不缓存为永久不支持。
    if(!core||!loader){reason="runtime_not_loaded";return false;}
    RuntimeVersion version;availability=-1;
    wchar_t filename[32768];DWORD n=GetModuleFileNameW(core,filename,32768);
    if(!n||n>=32768)return RuntimeDecision(version,"runtime_path_unavailable",false);
    DWORD ignored=0,size=GetFileVersionInfoSizeW(filename,&ignored);
    if(!size||size>1024*1024)return RuntimeDecision(version,"runtime_version_unavailable",false);
    std::vector<unsigned char> bytes(size);
    if(!GetFileVersionInfoW(filename,0,size,&bytes[0]))return RuntimeDecision(version,"runtime_version_unavailable",false);
    VS_FIXEDFILEINFO* info=0;UINT length=0;
    if(!VerQueryValueW(&bytes[0],L"\\",reinterpret_cast<void**>(&info),&length)||!info||length<sizeof(*info)||info->dwSignature!=0xFEEF04BDUL)
        return RuntimeDecision(version,"runtime_version_invalid",false);
    version.major=HIWORD(info->dwFileVersionMS);version.minor=LOWORD(info->dwFileVersionMS);
    version.bugfix=HIWORD(info->dwFileVersionLS);version.revision=LOWORD(info->dwFileVersionLS);version.known=true;
    const char* failure=RuntimeVersionGate(version);if(failure)return RuntimeDecision(version,failure,false);
    // C导出仅取得当前SDK实例；不创建第二份SDK、不加载/替换游戏运行时。
    // 继续沿用每次查询的SDK未就绪和scene->getPhysicsSDK同实例检查，不吞异常或假造命中。
    getSdk=reinterpret_cast<GetSdkFunction>(GetProcAddress(loader,"NxGetPhysicsSDK"));
    if(!getSdk)return RuntimeDecision(version,"runtime_sdk_export_missing",false);
    return RuntimeDecision(version,0,true);
}
const char* AvailabilityReason(){return reason;}
/* 100隔离SEH与C++对象析构；复用既有运行时版本/SDK实例核对，不新建Scene或SDK。
   isWritable仅确认SDK状态，游戏线程/消息/句柄生命周期仍由调用方先后两次核验。 */
static SceneReadiness ReadSceneReadiness(NxScene* scene,unsigned& exceptionCode){
    __try{
        NxPhysicsSDK* sdk=getSdk?getSdk():0;
        if(!scene||!sdk||&scene->getPhysicsSDK()!=sdk)return SCENE_UNAVAILABLE;
        return scene->isWritable()?SCENE_WRITABLE:SCENE_NOT_WRITABLE;
    }__except(EXCEPTION_EXECUTE_HANDLER){exceptionCode=GetExceptionCode();return SCENE_STATE_ERROR;}
}
SceneReadiness InspectSceneReadiness(void* scene,unsigned& exceptionCode){
    exceptionCode=0;
    if(!Initialize()||!scene)return SCENE_UNAVAILABLE;
    return ReadSceneReadiness(static_cast<NxScene*>(scene),exceptionCode);
}
static bool Finite(float f){return _finite(f)!=0;}
static bool ReadObjectKey(NxShape* shape,ObjectKey* out,unsigned& exceptionCode){
    // 原生sphereTrace/traceAll把NxShape::userData作为hand读取；这里只按SDK类型复制五个值，
    // 不调用外部对象的虚函数、不持有原地址。这里只返回读取结果；合批/重叠由调用者跳过该形体，扫掠仍保留原失败语义。
    __try{
        const hand* object=static_cast<const hand*>(shape->userData);
        out->present=object!=0;
        if(object){out->type=unsigned(object->type);out->container=object->container;out->containerSerial=object->containerSerial;
            out->index=object->index;out->serial=object->serial;}
        else{out->type=out->container=out->containerSerial=out->index=out->serial=0;}
        return true;
    }__except(EXCEPTION_EXECUTE_HANDLER){exceptionCode=GetExceptionCode();return false;}
}
// 接触点不是每个消费者的必需数据：巨神只消费形体和t，爆炸才需要球内接触坐标。
// 不放宽形体/比例/身份的有效性，不把NaN坐标补成起点，也不消费失败批次的部分名单。
const char* IssueReason(QueryIssue issue){
    switch(issue){
    case ISSUE_NONE:return "none";
    case ISSUE_INPUT_SCENE:return "input_scene_missing";
    case ISSUE_INPUT_RADIUS:return "input_radius_invalid";
    case ISSUE_INPUT_ORIGIN:return "input_origin_nonfinite";
    case ISSUE_INPUT_MOTION:return "input_motion_nonfinite";
    case ISSUE_ZERO_MOTION:return "input_motion_zero";
    case ISSUE_HIT_SHAPE:return "hit_shape_null";
    case ISSUE_HIT_FRACTION:return "hit_fraction_nonfinite";
    case ISSUE_HIT_RANGE:return "hit_fraction_out_of_range";
    case ISSUE_KEY_READ:return "hit_identity_unreadable";
    case ISSUE_CAPACITY:return "contact_capacity";
    case ISSUE_POINT_REQUIRED:return "blast_point_required";
    case ISSUE_CYLINDER_GEOMETRY:return "cylinder_shape_unresolved";
    case ISSUE_BATCH_INPUT:return "batch_input_invalid";
    case ISSUE_BATCH_CANDIDATES:return "batch_candidate_capacity";
    case ISSUE_BATCH_WORK:return "batch_shape_work_limit";
    case ISSUE_BATCH_SHAPE:return "batch_shape_not_adapted";
    case ISSUE_RAY_FIELDS:return "ray_required_fields_missing";
    default:return "unknown_issue";
    }
}
// 057：只查询当前有限中心路径的地形/非角色阻挡。raycastClosestShape不能直接用于
// “跳过角色”后继续找墙，因此用ALL回调流式保留最近墙；不假定角色独占某个碰撞组。
// 回调只复制身份/距离值，不重入场景、医疗或日志，不跨帧保存shape/userData地址。
// 077本机Steam 1.0.65实际弩箭飞行：GunClass::shoot RVA 0x43A680及
// Harpoon单步0x437E30均写0x087FDE47，worker把此组传raycastClosestShape。
// 开火前GunClass::trace/trace2的0x087F9E07/04是另一用途，不能拿来替代飞行组。
// 这里只对环境有限射线取原生组交集；角色球扫掠/光炮圆柱仍用调用者原组。
static const unsigned NATIVE_BOLT_GROUPS=0x087FDE47U;
// 093批量射线由外层RangedReport按报告块计时；单条直接射线的onHit仍嵌在execute里。
// 不为每个形体读取时钟，故execute余量不能声称是纯SDK耗时；摘要须按覆盖范围解释。
class TerrainRayCollector : public NxUserRaycastReport {
public:
    Contacts& output;QueryStatus status;float length;bool inspect;
    TerrainRayCollector(Contacts& out,float distance,bool details):output(out),status(QUERY_COMPLETE),length(distance),inspect(details){}
    bool Reject(QueryIssue issue,unsigned index,float fraction){
        output.diagnostic.issue=issue;output.diagnostic.hitIndex=index;output.diagnostic.rawFraction=fraction;
        std::memcpy(&output.diagnostic.fractionBits,&fraction,sizeof(fraction));status=QUERY_INVALID;return false;
    }
    virtual bool onHit(const NxRaycastHit& hit){
        const unsigned index=output.diagnostic.received++;
        if(!(hit.flags&NX_RAYCAST_SHAPE))return Reject(ISSUE_RAY_FIELDS,index,0);
        if(!hit.shape)return Reject(ISSUE_HIT_SHAPE,index,0);
        ObjectKey key;if(!ReadObjectKey(hit.shape,&key,output.diagnostic.identityException))return Reject(ISSUE_KEY_READ,index,0);
        if(key.present&&key.type==unsigned(CHARACTER))return true;
        if(!(hit.flags&NX_RAYCAST_DISTANCE))return Reject(ISSUE_RAY_FIELDS,index,0);
        if(!Finite(hit.distance))return Reject(ISSUE_HIT_FRACTION,index,hit.distance);
        const float fraction=hit.distance/length;
        if(hit.distance<0||hit.distance>length+std::max(.001f,length*.000001f))return Reject(ISSUE_HIT_RANGE,index,fraction);
        if(!output.count||fraction<output.items[0].fraction){
            Contact value;value.object=key;value.fraction=std::min(1.f,fraction);value.sourceIndex=index;
            value.point.x=value.point.y=value.point.z=0;value.pointValid=false;output.items[0]=value;output.count=1;
            // 仅复制同次同步查询中的标量；明细关闭不读取形体附加字段，回调不写日志/重入场景。
            TerrainInfo& info=output.diagnostic.terrain;info.hit=1;info.distance=hit.distance;
            if(inspect){info.shapeType=unsigned(hit.shape->getType());info.shapeGroup=unsigned(hit.shape->getGroup());
                info.trigger=hit.shape->getFlag(NX_TRIGGER_ENABLE)?1U:0U;info.metadata=1;}
        }
        return true; // 返回次序不保证按距离，不能在第一个墙或角色处提前结束。
    }
};
static QueryStatus RayBlocker(void* world,const Point& from,const Point& motion,unsigned groups,Contacts& result,unsigned& queryCalls){
    result.count=0;queryCalls=0;Diagnostic empty={ISSUE_NONE,0,0,0,0,0,{0,0,0},0,0,0};result.diagnostic=empty;
    if(!Initialize())return availability<0?QUERY_UNSUPPORTED:QUERY_NOT_READY;
    if(!world){result.diagnostic.issue=ISSUE_INPUT_SCENE;return QUERY_NOT_READY;}
    if(!Finite(from.x)||!Finite(from.y)||!Finite(from.z)){result.diagnostic.issue=ISSUE_INPUT_ORIGIN;return QUERY_INVALID;}
    if(!Finite(motion.x)||!Finite(motion.y)||!Finite(motion.z)){result.diagnostic.issue=ISSUE_INPUT_MOTION;return QUERY_INVALID;}
    NxVec3 travel(motion.x,motion.y,motion.z);const float length=travel.magnitude();
    if(!Finite(length)||length<=0){result.diagnostic.issue=ISSUE_ZERO_MOTION;return QUERY_INVALID;}
    NxScene* scene=static_cast<NxScene*>(world);NxPhysicsSDK* sdk=getSdk();
    if(!sdk){reason="runtime_sdk_not_ready";return QUERY_NOT_READY;}
    if(&scene->getPhysicsSDK()!=sdk){reason="scene_sdk_mismatch";return QUERY_UNSUPPORTED;}
    // 原生弩箭也使用NX_ALL_SHAPES和空groupsMask。SDK自行处理形体射线标记；
    // 不另外猜测trigger策略，不忽略合法零距离实体阻挡，有限长度仍对应本次移动步长。
    const unsigned terrainGroups=groups&NATIVE_BOLT_GROUPS;
    result.diagnostic.terrain.groups=terrainGroups;result.diagnostic.terrain.distance=-1;
    NxRay ray(NxVec3(from.x,from.y,from.z),travel/length);TerrainRayCollector collector(result,length,IrisDiagnostics::DetailsEnabled());
    // 087Scope析构只在SDK同步调用返回后提交统计；回调中仍只收纯值，不拿Iris锁/写日志。
    ++queryCalls;{IrisDiagnostics::Scope timing(IrisDiagnostics::NATIVE_TERRAIN_RAY);{IrisDiagnostics::InterfaceScope executeTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_EXECUTE));scene->raycastAllShapes(ray,collector,NX_ALL_SHAPES,terrainGroups,length,NX_RAYCAST_SHAPE|NX_RAYCAST_DISTANCE,0);}}
    if(IrisDiagnostics::CollisionProfileEnabled())IrisDiagnostics::Add(IrisDiagnostics::TERRAIN_RAW,result.diagnostic.received);
    if(collector.status!=QUERY_COMPLETE){result.count=0;return collector.status;}
    result.diagnostic.uniqueBeforeFailure=result.count;return QUERY_COMPLETE;
}
class Collector : public NxUserEntityReport<NxSweepQueryHit> {
public:
    Contacts& output;NxShape* shapes[CONTACT_INLINE_CAPACITY];std::vector<NxShape*> extraShapes;QueryStatus status;bool charactersOnly;NxSphere initial;
    NxShape* ShapeAt(unsigned i)const{return i<CONTACT_INLINE_CAPACITY?shapes[i]:extraShapes[i-CONTACT_INLINE_CAPACITY];}
    /* 086仅加速同一次同步回调中的同形体查找；仍按NxShape*完全相等判重，不能按人物合并。
       小于16条沿用原线性路径；表只存现有shapes下标，半载扩容，碰撞继续探测。
       表分配失败只退回本查询原线性查找，不使原本可成功的查询失败/漏人。
       所有NxShape*仍只借用到本Collector析构，不缓存跨帧，不增加锁或SDK调用。 */
    unsigned localIndex[128];std::vector<unsigned> indexStorage;unsigned* indexSlots;unsigned indexCapacity;
    bool indexReady,indexDisabled,indexAudit;
    explicit Collector(Contacts& out,const NxSphere& start,bool characters=false):output(out),status(QUERY_COMPLETE),charactersOnly(characters),initial(start),
        indexSlots(localIndex),indexCapacity(128),indexReady(false),indexDisabled(false),indexAudit(IrisDiagnostics::DetailsEnabled()){}
    static unsigned ShapeHash(NxShape* shape){
        ULONG_PTR value=reinterpret_cast<ULONG_PTR>(shape);unsigned h=unsigned(value)^unsigned(value>>32);
        h^=h>>16;h*=0x7feb352dU;h^=h>>15;return h;
    }
    unsigned LinearShape(NxShape* shape){
        unsigned at=0;while(at<output.count){if(indexAudit)++output.diagnostic.sweepShapeComparisons;if(ShapeAt(at)==shape)break;++at;}return at;
    }
    void InsertShape(unsigned index){
        unsigned at=ShapeHash(ShapeAt(index))&(indexCapacity-1);
        while(indexSlots[at]!=std::numeric_limits<unsigned>::max()){if(indexAudit)++output.diagnostic.sweepShapeProbes;at=(at+1U)&(indexCapacity-1);}
        if(indexAudit)++output.diagnostic.sweepShapeProbes;indexSlots[at]=index;
    }
    void DisableIndex(){
        indexDisabled=true;if(indexAudit)++output.diagnostic.sweepShapeIndexFallbacks;
    }
    bool PrepareIndex(){
        if(indexDisabled)return false;if(indexReady&&output.count<indexCapacity/2)return true;
        if(indexReady){
            if(indexCapacity>std::numeric_limits<unsigned>::max()/2){DisableIndex();return false;}
            try{indexStorage.resize(size_t(indexCapacity)*2);}
            catch(const std::bad_alloc&){DisableIndex();return false;}
            catch(const std::length_error&){DisableIndex();return false;}
            indexCapacity*=2;indexSlots=&indexStorage[0];
        }
        std::fill(indexSlots,indexSlots+indexCapacity,std::numeric_limits<unsigned>::max());indexReady=true;
        for(unsigned i=0;i<output.count;++i)InsertShape(i);if(indexAudit)++output.diagnostic.sweepShapeTables;return true;
    }
    unsigned FindShape(NxShape* shape){
        if(output.count<16||!PrepareIndex())return LinearShape(shape);
        unsigned at=ShapeHash(shape)&(indexCapacity-1);
        for(unsigned probes=0;probes<indexCapacity;++probes){
            if(indexAudit)++output.diagnostic.sweepShapeProbes;
            unsigned index=indexSlots[at];if(index==std::numeric_limits<unsigned>::max())return output.count;
            if(indexAudit)++output.diagnostic.sweepShapeComparisons;if(ShapeAt(index)==shape)return index;
            at=(at+1U)&(indexCapacity-1);
        }
        /* 防御性退路：即使表内部不变量失效，也使用当前原名单查找，不产生部分命中或额外物理重试。 */
        DisableIndex();return LinearShape(shape);
    }
    bool Reject(QueryIssue issue,QueryStatus failure,unsigned index,float fraction){
        output.diagnostic.issue=issue;output.diagnostic.uniqueBeforeFailure=output.count;
        output.diagnostic.hitIndex=index;output.diagnostic.rawFraction=fraction;
        std::memcpy(&output.diagnostic.fractionBits,&fraction,sizeof(fraction));status=failure;return false;
    }
    virtual bool onEvent(NxU32 count,NxSweepQueryHit* hits){
        // 093按SDK报告块计时，不逐形体取时钟；纯值汇总仍等物理调用退出。
        IrisDiagnostics::InterfaceScope reportTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_REPORT));
        for(NxU32 i=0;i<count;++i){const NxSweepQueryHit& hit=hits[i];unsigned index=output.diagnostic.received++;
            if(!hit.hitShape)return Reject(ISSUE_HIT_SHAPE,QUERY_INVALID,index,hit.t);
            // 057远程角色扫掠不让墙体占接触容量，也不拿墙体的球扫掠比例冒充地形射线。
            // 普通近战/翻滚仍消费全部形体；仅启用本参数的两招飞弹排除非角色。
            ObjectKey characterKey;if(charactersOnly){
                if(!ReadObjectKey(hit.hitShape,&characterKey,output.diagnostic.identityException))return Reject(ISSUE_KEY_READ,QUERY_INVALID,index,hit.t);
                if(!characterKey.present||characterKey.type!=unsigned(CHARACTER))continue;
            }
            if(!Finite(hit.t))return Reject(ISSUE_HIT_FRACTION,QUERY_INVALID,index,hit.t);
            float fraction=std::min(1.f,hit.t);
            if(hit.t<0||hit.t>1.001f){
                // 初始相交时老PhysX扫掠可能不给可用TOI；只有该真实shape的精确球相交再次证明，
                // 才消费明确的起点命中t=0。非相交、NaN、身份错误仍拒绝整批，绝不盲目钳位坏比例。
                bool overlap;
                {IrisDiagnostics::InterfaceScope recoveryTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_NARROW));overlap=hit.hitShape->checkOverlapSphere(initial);}
                if(!overlap)return Reject(ISSUE_HIT_RANGE,QUERY_INVALID,index,hit.t);
                fraction=0;++output.diagnostic.recoveredInitial;
            }
            unsigned at=FindShape(hit.hitShape);
            if(indexAudit)output.diagnostic.sweepShapeLinearEquivalent+=at<output.count?at+1:output.count;
            if(at<output.count&&output.items[at].fraction<=fraction)continue;
            Contact value;value.sourceIndex=index;value.fraction=fraction;value.point.x=value.point.y=value.point.z=0;value.pointValid=false;
            // 初始重叠不读取未定义point；非初始point无效仅记事实，是否回退由消费者的需求决定。
            if(fraction>0){value.point.x=hit.point.x;value.point.y=hit.point.y;value.point.z=hit.point.z;
                value.pointValid=Finite(hit.point.x)&&Finite(hit.point.y)&&Finite(hit.point.z);}
            if(charactersOnly)value.object=characterKey;
            else if(!ReadObjectKey(hit.hitShape,&value.object,output.diagnostic.identityException))return Reject(ISSUE_KEY_READ,QUERY_INVALID,index,hit.t);
            // 081形体地址只存在本次Collector；小名单仍用内联数组，超出时随实际接触增长。
            if(at==output.count){
                if(at>=CONTACT_INLINE_CAPACITY){try{extraShapes.push_back(hit.hitShape);}
                    catch(const std::bad_alloc&){return Reject(ISSUE_CAPACITY,QUERY_OVERFLOW,index,hit.t);}
                    catch(const std::length_error&){return Reject(ISSUE_CAPACITY,QUERY_OVERFLOW,index,hit.t);}}
                else shapes[at]=hit.hitShape;
                if(!output.Append(value))return Reject(ISSUE_CAPACITY,QUERY_OVERFLOW,index,hit.t);
                if(indexReady&&!indexDisabled)InsertShape(at);
            }else output.items[at]=value;
        }
        return true; // 继续收集下一批；不在回调里扣血、销毁物体、记录日志或修改SDK状态。
    }
};
struct EarlierContact {bool operator()(const Contact& a,const Contact& b)const{return a.fraction<b.fraction;}};
// 088单条与同步批量共用同一最终整理，保证比例/缺坐标/排序和失败清空逐值一致。
static QueryStatus FinalizeSweep(Contacts& result,QueryStatus status){
    if(IrisDiagnostics::CollisionProfileEnabled())IrisDiagnostics::Add(IrisDiagnostics::SWEEP_RAW,result.diagnostic.received);
    if(status!=QUERY_COMPLETE){result.count=0;return status;}
    IrisDiagnostics::Scope finalizeTiming(IrisDiagnostics::SWEEP_RESULT_FINALIZE);
    if(IrisDiagnostics::CollisionProfileEnabled())IrisDiagnostics::Add(IrisDiagnostics::SWEEP_SORTED,result.count);
    // 去重完成后再统计缺少坐标的唯一接触，避免被后续更近的同形体接触替换后仍误判失败。
    for(unsigned i=0;i<result.count;++i)if(result.items[i].fraction>0&&!result.items[i].pointValid){
        // 仅记录第一条最终仍缺坐标的接触；无效坐标从不参与球形命中或医疗。
        if(!result.diagnostic.missingPoints){result.diagnostic.hitIndex=result.items[i].sourceIndex;
            result.diagnostic.rawFraction=result.items[i].fraction;result.diagnostic.rawPoint=result.items[i].point;
            std::memcpy(&result.diagnostic.fractionBits,&result.items[i].fraction,sizeof(float));}
        ++result.diagnostic.missingPoints;}
    result.diagnostic.uniqueBeforeFailure=result.count;
    std::sort(result.items,result.items+result.count,EarlierContact());return QUERY_COMPLETE;
}
QueryStatus SweepAll(void* world,const Point& from,const Point& motion,float radius,unsigned groups,Contacts& result,unsigned& queryCalls,bool charactersOnly){
    result.count=0;queryCalls=0;Diagnostic empty={ISSUE_NONE,0,0,0,0,0,{0,0,0},0,0,0};result.diagnostic=empty;
    if(!Initialize())return availability<0?QUERY_UNSUPPORTED:QUERY_NOT_READY;
    if(!world){result.diagnostic.issue=ISSUE_INPUT_SCENE;return QUERY_NOT_READY;}
    if(!Finite(radius)||radius<=0){result.diagnostic.issue=ISSUE_INPUT_RADIUS;return QUERY_INVALID;}
    if(!Finite(from.x)||!Finite(from.y)||!Finite(from.z)){result.diagnostic.issue=ISSUE_INPUT_ORIGIN;return QUERY_INVALID;}
    if(!Finite(motion.x)||!Finite(motion.y)||!Finite(motion.z)){result.diagnostic.issue=ISSUE_INPUT_MOTION;return QUERY_INVALID;}
    if(motion.x==0&&motion.y==0&&motion.z==0){result.diagnostic.issue=ISSUE_ZERO_MOTION;return QUERY_INVALID;}
    NxScene* scene=static_cast<NxScene*>(world);NxPhysicsSDK* sdk=getSdk();
    if(!sdk){reason="runtime_sdk_not_ready";return QUERY_NOT_READY;}
    if(&scene->getPhysicsSDK()!=sdk){reason="scene_sdk_mismatch";return QUERY_UNSUPPORTED;}
    NxCapsule capsule;capsule.p0.set(from.x,from.y,from.z);capsule.p1=capsule.p0;capsule.radius=radius;
    NxVec3 travel(motion.x,motion.y,motion.z);NxSweepQueryHit batch[64];NxSphere initial;initial.center=capsule.p0;initial.radius=radius;Collector collector(result,initial,charactersOnly);
    // 与原包装同一退化胶囊和静态/动态组，只增加ALL_HITS。回调分块64不是结果上限；
    // 容量/必需字段失败时false停止收集并清空结果；只保留诊断值，不能使用半份名单。
    ++queryCalls;
    // 087仅分开SDK扫掠(包含纯值回调)和之后结果整理；原参数/完整位移/ALL_HITS逐值不变。
    {IrisDiagnostics::Scope timing(IrisDiagnostics::NATIVE_SPHERE_SWEEP);{IrisDiagnostics::InterfaceScope executeTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_EXECUTE));scene->linearCapsuleSweep(capsule,travel,NX_SF_STATICS|NX_SF_DYNAMICS|NX_SF_ALL_HITS,0,64,batch,&collector,groups,0);}}
    return FinalizeSweep(result,collector.status);
}
// 057：两份名单共同提交。射线与球扫掠沿同一完整位移，保留统一TOI供消费者比较，
// 不先截短球扫掠再改变fraction尺度；同一安全窗口同步完成，任何失败都不留下可消费半份结果。
QueryStatus ProjectileAll(void* world,const Point& from,const Point& motion,float radius,unsigned groups,Contacts& characters,Contacts& terrain,unsigned& queryCalls){
    characters.count=0;QueryStatus status=RayBlocker(world,from,motion,groups,terrain,queryCalls);
    characters.diagnostic=terrain.diagnostic;if(status!=QUERY_COMPLETE)return status;
    // 080：原消费者在完全同距时环境优先；合法角色TOI都>=0。
    // 只有精确t=0且半径合法时可证明任何角色都无法抢在墙前，省掉无效角色扫掠。
    // 不使用epsilon、不裁短其余motion/重标fraction；非法半径仍走原SweepAll错误路径。
    // RayBlocker失败仍整批重试；此处不保存NxShape/NxActor，也不进入医疗/游戏回调。
    if(terrain.count&&terrain.items[0].fraction==0.f&&Finite(radius)&&radius>0){
        characters.diagnostic.uniqueBeforeFailure=0;return QUERY_COMPLETE;
    }
    unsigned swept=0;status=SweepAll(world,from,motion,radius,groups,characters,swept,true);queryCalls+=swept;
    // 角色扫掠会独立清空自己的诊断，随后只复制环境标量；两名单失败仍一起作废。
    characters.diagnostic.terrain=terrain.diagnostic.terrain;
    characters.diagnostic.received+=terrain.diagnostic.received;
    if(status!=QUERY_COMPLETE){characters.count=terrain.count=0;return status;}
    return QUERY_COMPLETE;
}
// 官方球形重叠给真实相交形体，不依赖初始接触point；趴地/高低差采用同一个三维球。
// 081：小名单仍线性；512只是内联哈希槽数。超过半装载率时倍增并重建，
// 空槽使用UINT_MAX，不能再用256作哨兵（合法结果下标现在可以超过256）。
// 完整比较六个身份值；索引只保存自有结果下标，不存形体/角色指针，冲突沿探测链继续。
class IdentityIndex {
    Contacts& output;unsigned local[512];std::vector<unsigned> storage;unsigned* slots;unsigned capacity;bool ready,audit;
    static unsigned Hash(const ObjectKey& k){
        unsigned h=2166136261U;h=(h^k.type)*16777619U;h=(h^k.container)*16777619U;
        h=(h^k.containerSerial)*16777619U;h=(h^k.index)*16777619U;h=(h^k.serial)*16777619U;
        return (h^unsigned(k.present))*16777619U;
    }
    bool Equal(const ObjectKey& a,const ObjectKey& b){
        if(audit)++output.diagnostic.identityComparisons;
        return a.present==b.present&&a.type==b.type&&a.container==b.container&&a.containerSerial==b.containerSerial&&a.index==b.index&&a.serial==b.serial;
    }
    void Insert(unsigned index){
        unsigned at=Hash(output.items[index].object)&(capacity-1);
        while(slots[at]!=std::numeric_limits<unsigned>::max()){if(audit)++output.diagnostic.identityProbes;at=(at+1U)&(capacity-1);}
        if(audit)++output.diagnostic.identityProbes;slots[at]=index;
    }
    bool Prepare(){
        if(ready&&output.count<capacity/2)return true;
        if(ready){
            if(capacity>std::numeric_limits<unsigned>::max()/2)return false; // 表示能力/分配边界，不是人为命中上限。
            try{storage.resize(size_t(capacity)*2);}catch(const std::bad_alloc&){return false;}catch(const std::length_error&){return false;}
            capacity*=2;slots=&storage[0];
        }
        std::fill(slots,slots+capacity,std::numeric_limits<unsigned>::max());ready=true;
        for(unsigned i=0;i<output.count;++i)Insert(i);if(audit)++output.diagnostic.identityTables;return true;
    }
public:
    explicit IdentityIndex(Contacts& out):output(out),slots(local),capacity(512),ready(false),audit(IrisDiagnostics::DetailsEnabled()){}
    unsigned Find(const ObjectKey& key){
        if(!ready&&output.count<8){
            for(unsigned i=0;i<output.count;++i)if(Equal(output.items[i].object,key)){if(audit)++output.diagnostic.identityDuplicates;return i;}
            return output.count;
        }
        if(!Prepare())return std::numeric_limits<unsigned>::max();
        unsigned at=Hash(key)&(capacity-1);
        for(unsigned probes=0;probes<capacity;++probes){if(audit)++output.diagnostic.identityProbes;
            unsigned index=slots[at];if(index==std::numeric_limits<unsigned>::max())return output.count;
            if(Equal(output.items[index].object,key)){if(audit)++output.diagnostic.identityDuplicates;return index;}
            at=(at+1U)&(capacity-1);
        }
        return std::numeric_limits<unsigned>::max();
    }
    void Committed(){if(ready)Insert(output.count-1);}
};
// 094：公开依据是本机PhysX 2.8.4 NxScene.h overlapSphere/Capsule/OBBShapes的
// accurateCollision=false（查形体AABB）；不是把角色根位置当碰撞体，也不放大整条刀路AABB。
// 设真实形体S包含于B(S)，则Q与S相交必然Q与B(S)相交。这里只改变形体判定，不改原伤害半径。
static void MapExactSphereToAABBQuery(const Point& center,float radius,NxSphere& mapped){
    mapped.center.set(center.x,center.y,center.z);mapped.radius=radius;
}
static void MapExactCapsuleToAABBQuery(const Point& from,const Point& to,float radius,NxCapsule& mapped){
    mapped.p0.set(from.x,from.y,from.z);mapped.p1.set(to.x,to.y,to.z);mapped.radius=radius;
}
// 平端圆柱 Q={c+tu+xv+yw:|t|<=h,x²+y²<=r²}包含于同向OBB(|x|,|y|<=r)。
// 沿用原OBB方向/中心/墙前长度；16ε余量覆盖float基向量/中心舍入，不用整条世界轴对齐大盒子。
static bool MapExactCylinderToConservativeOBB(const NxBox& exact,NxBox& mapped){
    // 借已有紧凑OBB，不能重复构造/归一化基向量；允许输入输出为同一对象。
    mapped=exact;float scale=1;for(unsigned k=0;k<3;++k)scale=std::max(scale,std::max(fabsf(mapped.center[k]),mapped.extents[k]));
    const float pad=scale*(16*FLT_EPSILON);for(unsigned k=0;k<3;++k){mapped.extents[k]+=pad;
        if(!Finite(mapped.center[k])||!Finite(mapped.extents[k])||mapped.extents[k]<=0)return false;}return true;
}
class OverlapCollector : public NxUserEntityReport<NxShape*> {
public:
    Contacts& output;QueryStatus status;IdentityIndex identities;bool approximate;
    explicit OverlapCollector(Contacts& out,bool loose=false):output(out),status(QUERY_COMPLETE),identities(out),approximate(loose){}
    virtual bool onEvent(NxU32 count,NxShape** shapes){
        IrisDiagnostics::InterfaceScope reportTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_REPORT));
        for(NxU32 i=0;i<count;++i){unsigned index=output.diagnostic.received++;NxShape* shape=shapes[i];
            if(!shape){output.diagnostic.issue=ISSUE_HIT_SHAPE;if(approximate)++output.diagnostic.skippedGeometry;continue;}
            ObjectKey key;if(!ReadObjectKey(shape,&key,output.diagnostic.identityException)){output.diagnostic.issue=ISSUE_KEY_READ;if(approximate)++output.diagnostic.skippedIdentity;continue;}
            if(!key.present||key.type!=unsigned(CHARACTER))continue;
            // 查询已接纳该形体；同一角色多形体只输出一个稳定身份，避免额外医疗事件。
            // 不按不同爆炸合并健康事件，也不把无身份的世界物体假装角色。
            // 094近似模式内存异常仅跳过当前项，保留有效前缀且继续流式回调，不重查；精确模式兼容旧语义。
            unsigned found=identities.Find(key);if(found==std::numeric_limits<unsigned>::max()){output.diagnostic.issue=ISSUE_CAPACITY;if(approximate){++output.diagnostic.skippedCapacity;continue;}status=QUERY_OVERFLOW;return false;}
            if(found<output.count)continue;
            Contact c;c.object=key;c.fraction=0;c.point.x=c.point.y=c.point.z=0;c.pointValid=false;c.sourceIndex=index;if(!output.Append(c)){output.diagnostic.issue=ISSUE_CAPACITY;if(approximate){++output.diagnostic.skippedCapacity;continue;}status=QUERY_OVERFLOW;return false;}identities.Committed();
        }return true;
    }
};
QueryStatus OverlapSphere(void* world,const Point& center,float radius,unsigned groups,Contacts& result,unsigned& queryCalls,bool boundsOnly){
    // 098钻头显式强制AABB；其他球boundsOnly默认false，完整保留既有全局配置语义。
    const bool approximate=conservativeQueries||boundsOnly;
    result.count=0;queryCalls=0;Diagnostic empty={ISSUE_NONE,0,0,0,0,0,{0,0,0},0,0,0};result.diagnostic=empty;
    if(!Initialize())return availability<0?QUERY_UNSUPPORTED:QUERY_NOT_READY;
    if(!world){result.diagnostic.issue=ISSUE_INPUT_SCENE;return QUERY_NOT_READY;}
    if(!Finite(radius)||radius<=0){result.diagnostic.issue=ISSUE_INPUT_RADIUS;if(approximate){result.diagnostic.approximateKind=1;++result.diagnostic.skippedInput;return QUERY_COMPLETE;}return QUERY_INVALID;}
    if(!Finite(center.x)||!Finite(center.y)||!Finite(center.z)){result.diagnostic.issue=ISSUE_INPUT_ORIGIN;if(approximate){result.diagnostic.approximateKind=1;++result.diagnostic.skippedInput;return QUERY_COMPLETE;}return QUERY_INVALID;}
    NxScene* scene=static_cast<NxScene*>(world);NxPhysicsSDK* sdk=getSdk();if(!sdk)return QUERY_NOT_READY;
    if(&scene->getPhysicsSDK()!=sdk){reason="scene_sdk_mismatch";return QUERY_UNSUPPORTED;}
    NxSphere sphere;MapExactSphereToAABBQuery(center,radius,sphere);NxShape* batch[64];OverlapCollector collector(result,approximate);
    if(approximate)result.diagnostic.approximateKind=1;
    ++queryCalls;{IrisDiagnostics::InterfaceScope executeTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_EXECUTE));scene->overlapSphereShapes(sphere,NX_ALL_SHAPES,64,batch,&collector,groups,0,!approximate);}
    if(collector.status!=QUERY_COMPLETE){result.count=0;return collector.status;}
    result.diagnostic.uniqueBeforeFailure=result.count;return QUERY_COMPLETE;
}

QueryStatus OverlapCapsule(void* world,const Point& from,const Point& to,float radius,unsigned groups,Contacts& result,unsigned& queryCalls){
    // 球沿有限线段扫过的几何并集就是胶囊。静态伤害体只消费“是否相交”，不需要TOI或接触point。
    // 与真实投射物/墙体查询分开：后两者仍须扫掠排序；这不是取消物理或距离兜底扣血。
    result.count=0;queryCalls=0;Diagnostic empty={ISSUE_NONE,0,0,0,0,0,{0,0,0},0,0,0};result.diagnostic=empty;
    if(!Initialize())return availability<0?QUERY_UNSUPPORTED:QUERY_NOT_READY;
    if(!world){result.diagnostic.issue=ISSUE_INPUT_SCENE;return QUERY_NOT_READY;}
    if(!Finite(radius)||radius<=0){result.diagnostic.issue=ISSUE_INPUT_RADIUS;result.diagnostic.approximateKind=2;++result.diagnostic.skippedInput;return QUERY_COMPLETE;}
    if(!Finite(from.x)||!Finite(from.y)||!Finite(from.z)||!Finite(to.x)||!Finite(to.y)||!Finite(to.z)){result.diagnostic.issue=ISSUE_INPUT_ORIGIN;result.diagnostic.approximateKind=2;++result.diagnostic.skippedInput;return QUERY_COMPLETE;}
    NxScene* scene=static_cast<NxScene*>(world);NxPhysicsSDK* sdk=getSdk();if(!sdk)return QUERY_NOT_READY;
    if(&scene->getPhysicsSDK()!=sdk){reason="scene_sdk_mismatch";return QUERY_UNSUPPORTED;}
    NxCapsule capsule;MapExactCapsuleToAABBQuery(from,to,radius,capsule);
    // 097只有严格零长度才等价为球；不能用阈值吞掉一段很短但非零的胶囊。
    const bool sphere=from.x==to.x&&from.y==to.y&&from.z==to.z;
    NxSphere ball;ball.center=capsule.p0;ball.radius=radius;
    NxShape* batch[64];OverlapCollector collector(result,true);result.diagnostic.approximateKind=2;++queryCalls;
    {IrisDiagnostics::InterfaceScope executeTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_EXECUTE));if(sphere)scene->overlapSphereShapes(ball,NX_ALL_SHAPES,64,batch,&collector,groups,0,false);
        else scene->overlapCapsuleShapes(capsule,NX_ALL_SHAPES,64,batch,&collector,groups,0,false);}
    if(collector.status!=QUERY_COMPLETE){result.count=0;return collector.status;}
    result.diagnostic.uniqueBeforeFailure=result.count;return QUERY_COMPLETE;
}

// 097：复合提交逐条使用原生overlapCapsuleShapes(false)，没有自写扩盒/线段测试。
// 每条结果独立去重；先前成功前缀可以消费，场景暂态只保留未完成后缀，绝不整批重查。
QueryStatus OverlapCapsules(void* world,const CapsuleInput* paths,unsigned count,unsigned groups,Contacts* results,BatchDiagnostic& diagnostic,unsigned& queryCalls){
    queryCalls=0;BatchDiagnostic empty={ISSUE_NONE,0,0,0,0};diagnostic=empty;diagnostic.conservative=1;
    if(!paths||!results||count<2||count>CAPSULE_BATCH_CAPACITY){diagnostic.issue=ISSUE_BATCH_INPUT;return QUERY_INVALID;}
    for(unsigned i=0;i<count;++i){results[i].count=0;Diagnostic clean={ISSUE_NONE,0,0,0,0,0,{0,0,0},0,0,0};results[i].diagnostic=clean;}
    for(unsigned i=0;i<count;++i){unsigned calls=0;
        const QueryStatus status=OverlapCapsule(world,paths[i].from,paths[i].to,paths[i].radius,groups,results[i],calls);
        queryCalls+=calls;const Diagnostic& d=results[i].diagnostic;
        diagnostic.candidates+=d.received;diagnostic.characters+=results[i].count;
        diagnostic.skippedIdentity+=d.skippedIdentity;diagnostic.skippedGeometry+=d.skippedGeometry;
        diagnostic.skippedCapacity+=d.skippedCapacity;diagnostic.skippedInput+=d.skippedInput;
        if(d.identityException)diagnostic.identityException=d.identityException;
        if(d.issue!=ISSUE_NONE)diagnostic.issue=d.issue;
        if(status!=QUERY_COMPLETE)return status;++diagnostic.completed;
    }return QUERY_COMPLETE;
}

QueryStatus OverlapSector(void* world,const IrisSector::Volume& volume,unsigned groups,Contacts& result,unsigned& queryCalls){
    result.count=0;queryCalls=0;Diagnostic empty={ISSUE_NONE,0,0,0,0,0,{0,0,0},0,0,0};result.diagnostic=empty;
    result.diagnostic.approximateKind=5;
    if(!Initialize())return availability<0?QUERY_UNSUPPORTED:QUERY_NOT_READY;
    if(!world){result.diagnostic.issue=ISSUE_INPUT_SCENE;return QUERY_NOT_READY;}
    if(volume.count<5||volume.count>IrisSector::MAX_PLANES){result.diagnostic.issue=ISSUE_BATCH_INPUT;++result.diagnostic.skippedInput;return QUERY_COMPLETE;}
    NxPlane planes[IrisSector::MAX_PLANES];
    for(unsigned i=0;i<volume.count;++i){const IrisSector::Plane& p=volume.planes[i];
        if(!Finite(p.x)||!Finite(p.y)||!Finite(p.z)||!Finite(p.d)||double(p.x)*p.x+double(p.y)*p.y+double(p.z)*p.z<.5){
            result.diagnostic.issue=ISSUE_BATCH_INPUT;++result.diagnostic.skippedInput;return QUERY_COMPLETE;}
        planes[i].set(p.x,p.y,p.z,p.d);
    }
    NxScene* scene=static_cast<NxScene*>(world);NxPhysicsSDK* sdk=getSdk();if(!sdk)return QUERY_NOT_READY;
    if(&scene->getPhysicsSDK()!=sdk){reason="scene_sdk_mismatch";return QUERY_UNSUPPORTED;}
    NxShape* batch[64];OverlapCollector collector(result,true);++queryCalls;
    // 只由SDK裁剪形体AABB。用户明确允许额外命中，故不再读取bounds或自行做圆弧/三角形窄相。
    // 回调只产稳定身份，原敌我/主动目标资格、逐刀名单、医疗结算仍由原消费者负责。
    {IrisDiagnostics::InterfaceScope timing(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_EXECUTE));
        scene->cullShapes(volume.count,planes,NX_ALL_SHAPES,64,batch,&collector,groups,0);}
    if(collector.status!=QUERY_COMPLETE){result.count=0;return collector.status;}
    result.diagnostic.uniqueBeforeFailure=result.count;return QUERY_COMPLETE;
}

static IrisCylinder::V Local(const NxVec3& p,const NxVec3& center){return IrisCylinder::V(double(p.x)-center.x,double(p.y)-center.y,double(p.z)-center.z);}
static bool BodyGeometry(NxShape* shape,const NxVec3& center,IrisCylinder::Body& body){
    if(const NxSphereShape* sphere=shape->isSphere()){NxSphere s;sphere->getWorldSphere(s);body.points.push_back(Local(s.center,center));body.rounding=s.radius;}
    else if(const NxCapsuleShape* capsule=shape->isCapsule()){NxCapsule s;capsule->getWorldCapsule(s);body.points.push_back(Local(s.p0,center));body.points.push_back(Local(s.p1,center));body.rounding=s.radius;}
    else if(const NxBoxShape* box=shape->isBox()){NxBox b;box->getWorldOBB(b);for(unsigned i=0;i<8;++i){NxVec3 q((i&1)?b.extents.x:-b.extents.x,(i&2)?b.extents.y:-b.extents.y,(i&4)?b.extents.z:-b.extents.z);body.points.push_back(Local(b.center+b.rot*q,center));}}
    else if(const NxConvexShape* convex=shape->isConvexMesh()){
        const NxConvexMesh& mesh=convex->getConvexMesh();NxU32 count=mesh.getCount(0,NX_ARRAY_VERTICES),stride=mesh.getStride(0,NX_ARRAY_VERTICES);
        if(!count||count>4096||stride<12||mesh.getFormat(0,NX_ARRAY_VERTICES)!=NX_FORMAT_FLOAT)return false;
        const unsigned char* vertices=static_cast<const unsigned char*>(mesh.getBase(0,NX_ARRAY_VERTICES));if(!vertices)return false;NxMat34 pose=shape->getGlobalPose();body.points.reserve(count);
        for(NxU32 i=0;i<count;++i){NxVec3 q;std::memcpy(&q,vertices+i*stride,12);body.points.push_back(Local(pose*q,center));}
    }else return false;
    if(!Finite(float(body.rounding))||body.rounding<0)return false;
    for(size_t i=0;i<body.points.size();++i)if(!Finite(float(body.points[i].x))||!Finite(float(body.points[i].y))||!Finite(float(body.points[i].z)))return false;
    return !body.points.empty();
}
class CylinderCollector : public NxUserEntityReport<NxShape*> {
public:
    Contacts& out;QueryStatus status;NxVec3 center;IrisCylinder::Cylinder cylinder;IdentityIndex identities;IrisCylinder::Body scratch;
    // 单次查询内复用points容量；每个形体仍重新读取几何/位姿并清空rounding，不缓存形体裸指针。
    CylinderCollector(Contacts& r,const NxVec3& p,const NxVec3& axis,float half,float radius):out(r),status(QUERY_COMPLETE),center(p),identities(r){cylinder.axis=IrisCylinder::V(axis.x,axis.y,axis.z);cylinder.axis=cylinder.axis*(1.0/sqrt(cylinder.axis.norm2()));cylinder.half=half;cylinder.radius=radius;}
    virtual bool onEvent(NxU32 count,NxShape** shapes){
        // 几何读取/自有圆柱窄相均归入报告块；不能把这段记作SDK独占执行。
        IrisDiagnostics::InterfaceScope reportTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_REPORT));
        for(NxU32 i=0;i<count;++i){++out.diagnostic.received;ObjectKey key;
            if(!shapes[i]||!ReadObjectKey(shapes[i],&key,out.diagnostic.identityException)){out.diagnostic.issue=ISSUE_KEY_READ;status=QUERY_INVALID;return false;}
            if(!key.present||key.type!=unsigned(CHARACTER))continue;
            unsigned found=identities.Find(key);if(found==std::numeric_limits<unsigned>::max()){out.diagnostic.issue=ISSUE_CAPACITY;status=QUERY_OVERFLOW;return false;}if(found<out.count)continue;
            scratch.points.clear();scratch.rounding=0;const size_t capacity=scratch.points.capacity();
            if(!BodyGeometry(shapes[i],center,scratch)){out.diagnostic.issue=ISSUE_CYLINDER_GEOMETRY;status=QUERY_UNSUPPORTED;return false;}
            if(IrisDiagnostics::DetailsEnabled()&&scratch.points.capacity()!=capacity)++out.diagnostic.bodyBufferGrowth;
            IrisCylinder::Result hit=IrisCylinder::Overlap(cylinder,scratch);
            if(hit==IrisCylinder::UNRESOLVED){out.diagnostic.issue=ISSUE_CYLINDER_GEOMETRY;status=QUERY_INVALID;return false;}if(hit==IrisCylinder::MISS)continue;
            Contact c;c.object=key;c.point.x=c.point.y=c.point.z=0;c.pointValid=false;c.fraction=0;c.sourceIndex=out.diagnostic.received-1;if(!out.Append(c)){out.diagnostic.issue=ISSUE_CAPACITY;status=QUERY_OVERFLOW;return false;}identities.Committed();
        }return true;
    }
};
QueryStatus CylinderAll(void* world,const Point& from,const Point& motion,float radius,unsigned groups,Contacts& result,float& actualLength,unsigned& queryCalls){
    // 057：光炮环境只查有限中心射线，墙前有效长度继续同时驱动绘制和原平端圆柱。
    // 094仅角色判定可选保守OBB；环境有限射线/墙前长度保持，不传radius=0到胶囊扫掠接口。
    actualLength=0;queryCalls=0;result.count=0;Diagnostic initial={ISSUE_NONE,0,0,0,0,0,{0,0,0},0,0,0};result.diagnostic=initial;
    if(!Finite(radius)||radius<=0){result.diagnostic.issue=ISSUE_INPUT_RADIUS;if(conservativeQueries){result.diagnostic.approximateKind=3;++result.diagnostic.skippedInput;return QUERY_COMPLETE;}return QUERY_INVALID;}
    if(conservativeQueries&&(!Finite(from.x)||!Finite(from.y)||!Finite(from.z)||!Finite(motion.x)||!Finite(motion.y)||!Finite(motion.z))){
        result.diagnostic.issue=ISSUE_INPUT_MOTION;result.diagnostic.approximateKind=3;++result.diagnostic.skippedInput;return QUERY_COMPLETE;}
    // 094先复用本来就要计算的长度，坏零位移/溢出在提交射线前跳过，避免无效事件永久重试。
    NxVec3 delta(motion.x,motion.y,motion.z);float length=delta.magnitude();
    if(conservativeQueries&&(!Finite(length)||length<=0)){result.diagnostic.issue=ISSUE_INPUT_MOTION;result.diagnostic.approximateKind=3;++result.diagnostic.skippedInput;return QUERY_COMPLETE;}
    Contacts obstruction;QueryStatus status=RayBlocker(world,from,motion,groups,obstruction,queryCalls);result=obstruction;result.count=0;
    if(status!=QUERY_COMPLETE)return status;
    if(!Finite(length)||length<=0){if(conservativeQueries){result.diagnostic.issue=ISSUE_INPUT_MOTION;result.diagnostic.approximateKind=3;++result.diagnostic.skippedInput;return QUERY_COMPLETE;}return QUERY_INVALID;}NxVec3 axis=delta/length;float limit=1;
    for(unsigned i=0;i<obstruction.count;++i){const Contact& c=obstruction.items[i];if(!c.object.present||c.object.type!=unsigned(CHARACTER))limit=std::min(limit,c.fraction);}
    actualLength=length*limit;if(actualLength<=.0001f)return QUERY_COMPLETE;
    NxVec3 begin(from.x,from.y,from.z),center=begin+axis*(actualLength*.5f),side;
    side.cross(axis,fabsf(axis.y)<.9f?NxVec3(0,1,0):NxVec3(1,0,0));side.normalize();NxVec3 up;up.cross(axis,side);
    NxBox box;box.center=center;box.extents.set(radius,radius,actualLength*.5f);box.rot.setColumn(0,side);box.rot.setColumn(1,up);box.rot.setColumn(2,axis);
    Diagnostic empty={ISSUE_NONE,0,0,0,0,0,{0,0,0},0,0,0};empty.terrain=obstruction.diagnostic.terrain;result.diagnostic=empty;
    // 原环境裁短结果按值带回；094仅省掉可选角色窄相，原groups和两次预算保持。
    NxShape* batch[64];++queryCalls;QueryStatus bodyStatus=QUERY_COMPLETE;
    if(conservativeQueries){result.diagnostic.approximateKind=3;
        if(!MapExactCylinderToConservativeOBB(box,box)){--queryCalls;result.diagnostic.issue=ISSUE_INPUT_MOTION;++result.diagnostic.skippedInput;return QUERY_COMPLETE;}
        OverlapCollector collector(result,true);
        {IrisDiagnostics::InterfaceScope executeTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_EXECUTE));static_cast<NxScene*>(world)->overlapOBBShapes(box,NX_ALL_SHAPES,64,batch,&collector,groups,0,false);}
        bodyStatus=collector.status;
    }else{CylinderCollector collector(result,center,axis,actualLength*.5f,radius);
        {IrisDiagnostics::InterfaceScope executeTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_EXECUTE));static_cast<NxScene*>(world)->overlapOBBShapes(box,NX_ALL_SHAPES,64,batch,&collector,groups,0,true);}bodyStatus=collector.status;}
    result.diagnostic.received+=obstruction.diagnostic.received;
    if(bodyStatus!=QUERY_COMPLETE){result.count=0;return bodyStatus;}result.diagnostic.uniqueBeforeFailure=result.count;return QUERY_COMPLETE;
}


// 089只复用当前同场景、同groups的一批完整纯值；按每个float的位比较，不能用近似坐标或半径合并弹体。
static bool SameRangedFloat(float a,float b){return std::memcmp(&a,&b,sizeof(float))==0;}
static bool SameRangedInput(const RangedInput& a,const RangedInput& b){
    return a.cylinder==b.cylinder&&SameRangedFloat(a.radius,b.radius)&&
        SameRangedFloat(a.from.x,b.from.x)&&SameRangedFloat(a.from.y,b.from.y)&&SameRangedFloat(a.from.z,b.from.z)&&
        SameRangedFloat(a.motion.x,b.motion.x)&&SameRangedFloat(a.motion.y,b.motion.y)&&SameRangedFloat(a.motion.z,b.motion.z);
}
// 宽相只证明“整个联合包围盒没有任何角色形体”，不拿getter当前姿态逐路径剔除：
// SDK场景查询有双缓冲，getWorldBounds与查询快照不能无依据地当作同一份几何。
// 回调只读完整身份；遇到角色/坏身份即停止并保留原扫掠，不缓存形体、不分配候选名单。
class RangedEmptyReport : public NxUserEntityReport<NxShape*> {
public:
    unsigned candidates,characters,unknown,exception;RangedEmptyReport():candidates(0),characters(0),unknown(0),exception(0){}
    virtual bool onEvent(NxU32 count,NxShape** shapes){
        IrisDiagnostics::InterfaceScope reportTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_REPORT));
        for(NxU32 i=0;i<count;++i){++candidates;ObjectKey key;
            if(!shapes[i]||!ReadObjectKey(shapes[i],&key,exception)){++unknown;return false;}
            if(key.present&&key.type==unsigned(CHARACTER)){++characters;return false;}
        }return true;
    }
};
// 覆盖起点球以及原Collector可接收的t<=1.001f；双精度构造、向外余量后才转float。
// 几何只用于省略可证明空的查询，原motion/radius/TOI从不改写。非有限/极端坐标只禁用此项优化。
static bool RangedSweepBounds(const RangedInput& p,NxBounds3& box){
    const float start[3]={p.from.x,p.from.y,p.from.z},motion[3]={p.motion.x,p.motion.y,p.motion.z};
    for(unsigned axis=0;axis<3;++axis){double a=start[axis],b=a+double(motion[axis])*double(1.001f);
        double lo=std::min(a,b)-double(p.radius),hi=std::max(a,b)+double(p.radius);
        const double pad=std::max(1.,std::max(fabs(lo),fabs(hi)))*(8.*FLT_EPSILON);
        lo-=pad;hi+=pad;if(!_finite(lo)||!_finite(hi)||lo < -double(FLT_MAX)||hi>double(FLT_MAX))return false;
        box.min[axis]=float(lo);box.max[axis]=float(hi);
    }return true;
}
static double RangedBoundsVolume(const NxBounds3& box){
    return (double(box.max.x)-box.min.x)*(double(box.max.y)-box.min.y)*(double(box.max.z)-box.min.z);
}
static bool ProbeRangedEmpty(NxScene* scene,const RangedInput* paths,unsigned count,unsigned mask,unsigned groups,
    unsigned& calls,RangedPolicy& policy,RangedAudit& audit){
    unsigned pathsCount=0;NxBounds3 joined;joined.setEmpty();double separate=0;
    for(unsigned i=0;i<count;++i)if(mask&(1U<<i)){++pathsCount;NxBounds3 box;
        if(!RangedSweepBounds(paths[i],box)){++audit.probeInvalid;return false;}
        joined.combine(box);separate+=RangedBoundsVolume(box);
    }
    if(pathsCount<3){++audit.probeSmall;return false;}
    // 不为稀疏远离的弹体扩大搜索空间；无交叠密度收益时直接原查询，无额外SDK命令。
    if(RangedBoundsVolume(joined)>separate){++audit.probeSparse;return false;}
    // 额外宽相连同最坏情况下全部原查询都计入现有硬预算，不能靠积压伪装省时。
    if(policy.maxCalls<count*2U+1U){++audit.probeHeadroom;return false;}
    RangedEmptyReport report;NxShape* chunk[64];NxU32 reported=0;
    {IrisDiagnostics::Scope timing(IrisDiagnostics::RANGED_EMPTY_PROBE,0,&audit.probeMs);++calls;++audit.probeCalls;
        {IrisDiagnostics::InterfaceScope executeTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_EXECUTE));reported=scene->overlapAABBShapes(joined,NX_ALL_SHAPES,64,chunk,&report,groups,0,false);}}
    audit.probeCandidates+=report.candidates;audit.probeCharacters+=report.characters;
    // 回调与返回计数不完整时不能宣布为空；64是SDK流式缓冲，不是候选总量上限。
    if(!report.characters&&!report.unknown&&reported!=report.candidates)++report.unknown;
    audit.probeUnknown+=report.unknown;if(report.exception)audit.probeException=report.exception;
    if(report.characters||report.unknown){++audit.probeBusy;policy.allowEmpty=false;return false;}
    audit.emptyPaths+=pathsCount;return true;
}

// 092各批成本沿既有Scope计时回传，未添加参考查询或改变原输入/返回集合。
// 090最多8项的纯值聚组：只合并联合体积不超过两组体积之和的邻近组，选择最紧凑的一对。
// 分组只改变宽相试探的范围，原paths/slots/source和逐发消费顺序不动；没有堆分配或几何getter。
struct RangedSpatialGroup {NxBounds3 bounds;unsigned mask,paths;};
static void BuildRangedSpatialGroups(const RangedInput* paths,unsigned count,unsigned mask,RangedSpatialGroup* groups,RangedAudit& audit){
    for(unsigned i=0;i<count;++i){groups[i].mask=groups[i].paths=0;
        if(!(mask&(1U<<i)))continue;
        if(!RangedSweepBounds(paths[i],groups[i].bounds)){++audit.probeInvalid;continue;}
        groups[i].mask=1U<<i;groups[i].paths=1;
    }
    for(;;){unsigned bestA=count,bestB=count;double bestRatio=1.;
        for(unsigned a=0;a<count;++a)if(groups[a].mask)for(unsigned b=a+1;b<count;++b)if(groups[b].mask){
            ++audit.spatialPairs;NxBounds3 joined=groups[a].bounds;joined.combine(groups[b].bounds);
            const double separate=RangedBoundsVolume(groups[a].bounds)+RangedBoundsVolume(groups[b].bounds);
            const double ratio=RangedBoundsVolume(joined)/separate;
            if(ratio<=1.&&(bestA==count||ratio<bestRatio)){bestA=a;bestB=b;bestRatio=ratio;}
        }
        if(bestA==count)break;
        groups[bestA].bounds.combine(groups[bestB].bounds);groups[bestA].mask|=groups[bestB].mask;
        groups[bestA].paths+=groups[bestB].paths;groups[bestB].mask=groups[bestB].paths=0;++audit.spatialMerges;
    }
}
// 返回的位只来自完整流式宽相的“无角色”证明；有角色组单独走原扫掠，不污染其他组。
// worst保留所有原查询及失败别名重试的最坏命令数；成功省掉的扫掠才能抵扣下一组试探预算。
// 显式shadow不抵扣，因为之后仍要执行原扫掠；额外试探始终计入64硬预算。
static unsigned ProbeRangedSpatial(NxScene* scene,const RangedInput* paths,unsigned count,unsigned mask,unsigned groups,
    unsigned& calls,RangedPolicy& policy,RangedAudit& audit){
    ++audit.spatialBatches;
    // 最坏原查询已占满预算时不可能再试探，先短路，避免无收益的聚组计算。
    if(policy.maxCalls<=count*2U){++audit.probeHeadroom;return 0;}
    RangedSpatialGroup clusters[RANGED_BATCH_CAPACITY];
    {IrisDiagnostics::Scope timing(IrisDiagnostics::RANGED_SPATIAL_BUILD);BuildRangedSpatialGroups(paths,count,mask,clusters,audit);}
    unsigned emptyMask=0,worst=count*2U;
    for(unsigned i=0;i<count;++i){const RangedSpatialGroup& group=clusters[i];if(!group.mask)continue;
        if(group.paths==1&&!policy.single){++audit.spatialSkippedSingles;continue;}
        if(worst>=policy.maxCalls){++audit.probeHeadroom;continue;}
        ++worst;++audit.spatialGroups;audit.spatialCovered+=group.paths;
        if(group.paths==1)++audit.spatialSingles;else ++audit.spatialMultis;
        RangedEmptyReport report;NxShape* chunk[64];NxU32 reported=0;
        {IrisDiagnostics::Scope timing(IrisDiagnostics::RANGED_EMPTY_PROBE,0,&audit.probeMs);++calls;++audit.probeCalls;
            {IrisDiagnostics::InterfaceScope executeTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_EXECUTE));reported=scene->overlapAABBShapes(group.bounds,NX_ALL_SHAPES,64,chunk,&report,groups,0,false);}}
        audit.probeCandidates+=report.candidates;audit.probeCharacters+=report.characters;
        if(!report.characters&&!report.unknown&&reported!=report.candidates)++report.unknown;
        audit.probeUnknown+=report.unknown;if(report.exception)audit.probeException=report.exception;
        if(report.unknown){policy.allowEmpty=false;break;} // 只禁后续试探；所有尚未证明的路径仍执行原查询。
        if(report.characters){++audit.probeBusy;continue;}
        emptyMask|=group.mask;audit.emptyPaths+=group.paths;
        if(group.paths==1)++audit.spatialEmptySingles;else ++audit.spatialEmptyMultis;
        if(!policy.shadow)worst-=group.paths;
    }
    return emptyMask;
}

// 088每项回调只委托原收集器，用户标签只在当前调用栈内有效；不重排或合并各项命中。
// 显式内联placement存储避免每条射线/扫掠新建堆对象。Collector的动态部分仍按真实结果增长。
struct RangedSlot {
    TerrainRayCollector* ray;Collector* sweep;NxRay rayValue;NxCapsule capsule;NxVec3 travel,axis;float distance;unsigned leader;bool skipInput;
    __declspec(align(16)) unsigned char rayStorage[sizeof(TerrainRayCollector)];
    __declspec(align(16)) unsigned char sweepStorage[sizeof(Collector)];
    RangedSlot():ray(0),sweep(0),distance(0),skipInput(false){}
    ~RangedSlot(){if(sweep)sweep->~Collector();if(ray)ray->~TerrainRayCollector();}
private:RangedSlot(const RangedSlot&);RangedSlot& operator=(const RangedSlot&);
};
class RangedReport : public NxSceneQueryReport {
    RangedSlot* slots;unsigned count;
    RangedSlot* Find(void* tag){for(unsigned i=0;i<count;++i)if(tag==&slots[i])return &slots[i];bad=true;return 0;}
public:
    bool bad;RangedReport(RangedSlot* p,unsigned n):slots(p),count(n),bad(false){}
    virtual NxQueryReportResult onBooleanQuery(void*,bool){bad=true;return NX_SQR_ABORT_ALL_QUERIES;}
    virtual NxQueryReportResult onShapeQuery(void*,NxU32,NxShape**){bad=true;return NX_SQR_ABORT_ALL_QUERIES;}
    virtual NxQueryReportResult onRaycastQuery(void* tag,NxU32 n,const NxRaycastHit* hits){
        IrisDiagnostics::InterfaceScope reportTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_REPORT));
        RangedSlot* s=Find(tag);if(!s||!s->ray){bad=true;return NX_SQR_ABORT_ALL_QUERIES;}
        for(NxU32 i=0;i<n;++i)if(!s->ray->onHit(hits[i]))return NX_SQR_ABORT_QUERY;return NX_SQR_CONTINUE;
    }
    virtual NxQueryReportResult onSweepQuery(void* tag,NxU32 n,NxSweepQueryHit* hits){
        IrisDiagnostics::InterfaceScope reportTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_REPORT));
        RangedSlot* s=Find(tag);if(!s||!s->sweep){bad=true;return NX_SQR_ABORT_ALL_QUERIES;}
        return s->sweep->onEvent(n,hits)?NX_SQR_CONTINUE:NX_SQR_ABORT_QUERY;
    }
};
// 所有SDK对象在栈报告/收集器之前释放；同步finish(true)之后才读取名单。
// 异常展开也先结束已提交工作，不让SDK保留栈标签；不跨帧缓存scene/query/shape。
struct RangedQueryOwner {
    NxScene* scene;NxSceneQuery* query;bool pending;
    RangedQueryOwner(NxScene* s):scene(s),query(0),pending(false){}
    void Finish(){
        // execute同步触发报告；子回调由同一根扣除，不重放查询、不改阻塞语义。
        {IrisDiagnostics::InterfaceScope executeTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_EXECUTE));query->execute();}
        {IrisDiagnostics::InterfaceScope finishTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_FINISH));query->finish(true);}pending=false;
    }
    ~RangedQueryOwner(){if(query){if(pending)Finish();
        IrisDiagnostics::Scope timing(IrisDiagnostics::RANGED_BATCH_RELEASE);scene->releaseSceneQuery(*query);}}
private:RangedQueryOwner(const RangedQueryOwner&);RangedQueryOwner& operator=(const RangedQueryOwner&);
};
bool RangedBatch(void* world,const RangedInput* paths,unsigned count,unsigned groups,RangedResult* results,unsigned& queryCalls,RangedPolicy& policy,RangedAudit& audit){
    RangedAudit clean={0};audit=clean;queryCalls=0;
    if(!paths||!results||count<2||count>RANGED_BATCH_CAPACITY||policy.maxCalls<count*2U||!world||!Initialize())return false;
    NxScene* scene=static_cast<NxScene*>(world);NxPhysicsSDK* sdk=getSdk();if(!sdk||&scene->getPhysicsSDK()!=sdk)return false;
    RangedSlot slots[RANGED_BATCH_CAPACITY];RangedReport report(slots,count);RangedQueryOwner owner(scene);
    // 先验证全部纯值，尚未提交时才能整批回旧路；提交以后每项失败独立交给下一安全窗口重试。
    for(unsigned i=0;i<count;++i){const RangedInput& p=paths[i];RangedSlot& s=slots[i];s.leader=i;
        if(!Finite(p.radius)||p.radius<=0||!Finite(p.from.x)||!Finite(p.from.y)||!Finite(p.from.z)||
           !Finite(p.motion.x)||!Finite(p.motion.y)||!Finite(p.motion.z)){
            // 094仅独立光柱坏输入跳过；其余合法项继续，不触发整批旧查询。飞弹失败语义原样保留。
            if(p.cylinder&&conservativeQueries){s.skipInput=true;continue;}return false;}
        s.travel.set(p.motion.x,p.motion.y,p.motion.z);s.distance=s.travel.magnitude();if(!Finite(s.distance)||s.distance<=0){if(p.cylinder&&conservativeQueries){s.skipInput=true;continue;}return false;}
        s.axis=s.travel/s.distance;s.rayValue=NxRay(NxVec3(p.from.x,p.from.y,p.from.z),s.axis);
    }
    if(policy.reuse){IrisDiagnostics::Scope timing(IrisDiagnostics::RANGED_REUSE_LOOKUP);
        for(unsigned i=0;i<count;++i)if(!paths[i].cylinder)for(unsigned k=0;k<i;++k)
            if(slots[k].leader==k&&SameRangedInput(paths[i],paths[k])){slots[i].leader=k;break;}}
    {IrisDiagnostics::Scope timing(IrisDiagnostics::RANGED_BATCH_CREATE);NxSceneQueryDesc desc;desc.report=&report;desc.executeMode=NX_SQE_SYNCHRONOUS;
        owner.query=scene->createSceneQuery(desc);}
    if(!owner.query)return false;
    Diagnostic empty={ISSUE_NONE,0,0,0,0,0,{0,0,0},0,0,0};
    {IrisDiagnostics::Scope timing(IrisDiagnostics::RANGED_BATCH_RAYS,0,&audit.raysMs);
    {IrisDiagnostics::InterfaceScope submitTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_SUBMIT));
    for(unsigned i=0;i<count;++i){RangedResult& r=results[i];RangedSlot& s=slots[i];r.characters.count=r.terrain.count=0;
        r.characters.diagnostic=r.terrain.diagnostic=empty;r.length=0;r.bodyCalls=r.rayCalls=0;r.source=i;r.status=QUERY_COMPLETE;
        if(s.skipInput){r.characters.diagnostic.approximateKind=3;r.characters.diagnostic.issue=ISSUE_INPUT_MOTION;++r.characters.diagnostic.skippedInput;continue;}
        if(s.leader!=i)continue; // 完全相同项尚不产生别名，必须等原查询成功；失败则单独走原路。
        r.terrain.diagnostic.terrain.groups=groups&NATIVE_BOLT_GROUPS;r.terrain.diagnostic.terrain.distance=-1;
        s.ray=new(s.rayStorage)TerrainRayCollector(r.terrain,s.distance,IrisDiagnostics::DetailsEnabled());
        owner.pending=true;++queryCalls;++r.rayCalls;
        owner.query->raycastAllShapes(s.rayValue,NX_ALL_SHAPES,groups&NATIVE_BOLT_GROUPS,s.distance,NX_RAYCAST_SHAPE|NX_RAYCAST_DISTANCE,0,&s);
    }}owner.Finish();}
    unsigned possible=0,emptyMask=0;
    for(unsigned i=0;i<count;++i)if(slots[i].leader==i){RangedResult& r=results[i];
        if(slots[i].skipInput)continue;
        r.status=report.bad?QUERY_INVALID:slots[i].ray->status;r.characters.diagnostic=r.terrain.diagnostic;
        if(IrisDiagnostics::CollisionProfileEnabled())IrisDiagnostics::Add(IrisDiagnostics::TERRAIN_RAW,r.terrain.diagnostic.received);
        if(!paths[i].cylinder&&r.status==QUERY_COMPLETE&&!(r.terrain.count&&r.terrain.items[0].fraction==0.f))possible|=1U<<i;
    }
    // 090空间策略只为原独立球段分组证明空区；0仍可回到089整批策略做对照。
    if(policy.empty&&policy.allowEmpty&&possible){
        if(policy.spatial)emptyMask=ProbeRangedSpatial(scene,paths,count,possible,groups,queryCalls,policy,audit);
        else if(ProbeRangedEmpty(scene,paths,count,possible,groups,queryCalls,policy,audit))emptyMask=possible;
    }
    {IrisDiagnostics::Scope timing(IrisDiagnostics::RANGED_BATCH_BODIES,0,&audit.bodiesMs);
    unsigned sweeps=0;
    {IrisDiagnostics::InterfaceScope submitTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_SUBMIT));
    for(unsigned i=0;i<count;++i){const RangedInput& p=paths[i];RangedResult& r=results[i];RangedSlot& s=slots[i];
        if(s.leader!=i||s.skipInput)continue;
        if(r.status!=QUERY_COMPLETE){r.characters.count=r.terrain.count=0;continue;}
        r.terrain.diagnostic.uniqueBeforeFailure=r.terrain.count;
        if(p.cylinder){
            // 官方批量overlapOBBShapes没有accurateCollision参数，不能直接替换原true接口。
            // 094只合批环境射线；角色由同名映射选择保守OBB或原精确体积，不新增场景查询。
            const float limit=r.terrain.count?r.terrain.items[0].fraction:1.f;r.length=s.distance*limit;
            if(r.length<=.0001f)continue;
            NxVec3 begin(p.from.x,p.from.y,p.from.z),center=begin+s.axis*(r.length*.5f),side;
            side.cross(s.axis,fabsf(s.axis.y)<.9f?NxVec3(0,1,0):NxVec3(1,0,0));side.normalize();NxVec3 up;up.cross(s.axis,side);
            NxBox box;box.center=center;box.extents.set(p.radius,p.radius,r.length*.5f);box.rot.setColumn(0,side);box.rot.setColumn(1,up);box.rot.setColumn(2,s.axis);
            r.characters.diagnostic=empty;r.characters.diagnostic.terrain=r.terrain.diagnostic.terrain;
            NxShape* buffer[64];++queryCalls;++r.bodyCalls;
            if(conservativeQueries){r.characters.diagnostic.approximateKind=3;
                if(!MapExactCylinderToConservativeOBB(box,box)){--queryCalls;--r.bodyCalls;r.characters.diagnostic.issue=ISSUE_INPUT_MOTION;++r.characters.diagnostic.skippedInput;continue;}
                OverlapCollector collector(r.characters,true);
                {IrisDiagnostics::InterfaceScope executeTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_EXECUTE));scene->overlapOBBShapes(box,NX_ALL_SHAPES,64,buffer,&collector,groups,0,false);}r.status=collector.status;
            }else{CylinderCollector collector(r.characters,center,s.axis,r.length*.5f,p.radius);
                {IrisDiagnostics::InterfaceScope executeTiming(IrisDiagnostics::QueryBoundaryPart(IrisDiagnostics::IF_QUERY_EXECUTE));scene->overlapOBBShapes(box,NX_ALL_SHAPES,64,buffer,&collector,groups,0,true);}r.status=collector.status;}
            r.characters.diagnostic.received+=r.terrain.diagnostic.received;
            r.characters.diagnostic.uniqueBeforeFailure=r.characters.count;
        }else{
            // 地形仍为完整原生组有限射线；只有精确t=0墙或联合区域已证明无角色时才省查。
            if(r.terrain.count&&r.terrain.items[0].fraction==0.f)continue;
            r.characters.diagnostic=empty;
            if((emptyMask&(1U<<i))&&!policy.shadow){
                r.characters.diagnostic.terrain=r.terrain.diagnostic.terrain;r.characters.diagnostic.received=r.terrain.diagnostic.received;
                ++audit.savedSweeps;continue;}
            s.capsule.p0.set(p.from.x,p.from.y,p.from.z);s.capsule.p1=s.capsule.p0;s.capsule.radius=p.radius;
            NxSphere initial;initial.center=s.capsule.p0;initial.radius=p.radius;
            s.sweep=new(s.sweepStorage)Collector(r.characters,initial,true);
            owner.pending=true;++queryCalls;++r.bodyCalls;++sweeps;
            // 2.8.4官方注释：ALL_HITS返回数恒0，只有onSweepQuery名单和collector.status有意义。
            owner.query->linearCapsuleSweep(s.capsule,s.travel,NX_SF_STATICS|NX_SF_DYNAMICS|NX_SF_ALL_HITS,groups,0,&s);
        }
    }}if(sweeps)owner.Finish();}
    for(unsigned i=0;i<count;++i)if(slots[i].leader==i){RangedResult& r=results[i];RangedSlot& s=slots[i];
        if(report.bad){r.status=QUERY_INVALID;r.characters.diagnostic.issue=ISSUE_BATCH_INPUT;}
        else if(s.sweep){r.status=FinalizeSweep(r.characters,s.sweep->status);r.characters.diagnostic.terrain=r.terrain.diagnostic.terrain;
            r.characters.diagnostic.received+=r.terrain.diagnostic.received;}
        if(r.status!=QUERY_COMPLETE)r.characters.count=r.terrain.count=0;
        // 测试开关默认0；开启只验证“可省略的名单为空”，实际仍消费原完整扫掠，不掺入正式伤害对照。
        if(policy.shadow&&(emptyMask&(1U<<i))){++audit.shadowChecks;
            if(r.status!=QUERY_COMPLETE||r.characters.count){++audit.shadowMismatches;policy.allowEmpty=false;}}
    }
    // 同批引用只对成功结果生效，不改变cast/event/敌我判定；失败别名拥有独立原查询和重试状态。
    for(unsigned i=0;i<count;++i)if(slots[i].leader!=i){RangedResult& r=results[i];const unsigned leader=slots[i].leader;
        if(results[leader].status==QUERY_COMPLETE){r.source=leader;++audit.reused;}
        else{++audit.reuseFailed;unsigned calls=0;
            r.status=ProjectileAll(world,paths[i].from,paths[i].motion,paths[i].radius,groups,r.characters,r.terrain,calls);
            r.rayCalls=std::min(1U,calls);r.bodyCalls=calls-r.rayCalls;queryCalls+=calls;}
    }
    return true;
}

}
