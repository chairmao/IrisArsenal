// 084诊断单元：原生受击在原线程、原参数、原次数下执行，新增Hook仅在显式诊断开启时安装。
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>
#include "IrisNativeAudit.h"
#include "IrisWoundAudit.h"
#include <core/Functions.h>
#include <kenshi/MedicalSystem.h>
#include <kenshi/combat/CombatClass.h>
#include <algorithm>
#include <cstring>
#include <sstream>
#include <iomanip>
#include <exception>
#include <float.h>
namespace Iris {extern CRITICAL_SECTION mutex;}
namespace IrisNativeAudit {
static bool nativeOption=false,serviceOption=false,woundInstalled=false,effectInstalled=false;
static bool gapOption=false;static unsigned gapEvery=32;static volatile LONG gapSequence=0;
static DWORD hitTLS=TLS_OUT_OF_INDEXES,frameTLS=TLS_OUT_OF_INDEXES;
static volatile LONG generation=0,tlsFailures=0;
struct Guard {Guard(){EnterCriticalSection(&Iris::mutex);}~Guard(){LeaveCriticalSection(&Iris::mutex);}};
// 诊断不得把TlsGetValue清除的LastError传给原链；每次读取/设置后恢复调用方值。
static void* ReadTLS(DWORD slot){DWORD saved=GetLastError();void* p=slot==TLS_OUT_OF_INDEXES?0:TlsGetValue(slot);SetLastError(saved);return p;}
static bool WriteTLS(DWORD slot,void* p){DWORD saved=GetLastError();bool ok=slot!=TLS_OUT_OF_INDEXES&&TlsSetValue(slot,p)!=0;if(!ok)InterlockedIncrement(&tlsFailures);SetLastError(saved);return ok;}
static unsigned Generation(){return unsigned(InterlockedCompareExchange(&generation,0,0));}
bool Enabled(){return nativeOption&&IrisDiagnostics::DetailsEnabled()&&hitTLS!=TLS_OUT_OF_INDEXES;}
bool ServiceEnabled(){return serviceOption&&IrisDiagnostics::DetailsEnabled()&&frameTLS!=TLS_OUT_OF_INDEXES;}
static const double bounds[15]={0,.01,.025,.05,.1,.25,.5,1,2,4,8,16,32,64,128};
struct Stat {
    Count n,buckets[16];double sum,max;
    Stat():n(0),sum(0),max(0){for(unsigned i=0;i<16;++i)buckets[i]=0;}
    void Add(double ms){if(!_finite(ms)||ms<0)return;++n;sum+=ms;max=std::max(max,ms);unsigned b=0;while(b<15&&ms>bounds[b])++b;++buckets[b];}
    double Percent(unsigned p)const {if(!n)return 0;Count target=(n*p+99)/100,total=0;for(unsigned i=0;i<16;++i){total+=buckets[i];if(total>=target)return i<15?bounds[i]:-1;}return -1;}
};
struct NativeStats {
    Stat total,unattributed,inclusive[PART_COUNT],exclusive[PART_COUNT],gaps[PART_COUNT+1];Count calls[PART_COUNT],nested,invalidated,exceptional;
    NativeStats():nested(0),invalidated(0),exceptional(0){for(unsigned i=0;i<PART_COUNT;++i)calls[i]=0;}
};
struct ServiceStats {
    Count frames,callbacks,repeated,waiting,repeatReady,noFlush,flushes,progress,nativeCalls,inspected,lastFrameToken;
    Count timeYield,countYield,scanYield,physics,ai,paused,world,readErrors,unknown;
    Stat callbackGap,progressGap,frameWall,flushWall,probe;
    ServiceStats():frames(0),callbacks(0),repeated(0),waiting(0),repeatReady(0),noFlush(0),flushes(0),progress(0),nativeCalls(0),inspected(0),lastFrameToken(0),timeYield(0),countYield(0),scanYield(0),physics(0),ai(0),paused(0),world(0),readErrors(0),unknown(0){}
};
static NativeStats nativeRun,nativeWindow;static ServiceStats serviceRun,serviceWindow;
static double lastWaitingCallback=0,lastProgress=0;static Count lastRemaining=0,sequence=0,notices=0;static double lastNotice=0;
void Configure(bool nativeProfile,bool serviceProfile,bool gapProfile,unsigned sampleEvery){
    nativeOption=nativeProfile;serviceOption=serviceProfile;gapOption=gapProfile;gapEvery=sampleEvery; // 103直接保留配置，0禁用抽样，不静默钳成1。
    // 进程期TLS槽不在读档时释放；已安装Hook可能继续转发，不允许复用槽制造悬空上下文。
    if(nativeOption&&IrisDiagnostics::DetailsEnabled())hitTLS=TlsAlloc();
    if(serviceOption&&IrisDiagnostics::DetailsEnabled())frameTLS=TlsAlloc();
}
typedef GameData*(__fastcall* WoundFn)(MedicalSystem*,bool,CutDirection,Damages&,int&,RootObject*,AttackDirection::Enum&,Harpoon*);
typedef void(__fastcall* EffectFn)(GameData*,const hand&,const std::string&,const Ogre::Vector3&,const Ogre::Quaternion&);
static WoundFn originalWound=0;static EffectFn originalEffect=0;
static GameData* __fastcall WoundHook(MedicalSystem* self,bool low,CutDirection dir,Damages& damage,int& material,RootObject* attacker,AttackDirection::Enum& direction,Harpoon* harpoon){
    // 085来源只看现存TLS；新开关关闭时不读TLS/伤害字段，所有原参数/引用和返回值保持。
    IrisWoundAudit::Scope detail(IrisWoundAudit::Enabled()&&ReadTLS(hitTLS)!=0,damage);
    PartScope part(WOUND);return originalWound(self,low,dir,damage,material,attacker,direction,harpoon);
}
static void __fastcall EffectHook(GameData* data,const hand& who,const std::string& bone,const Ogre::Vector3& position,const Ogre::Quaternion& rotation){
    PartScope part(EFFECT);originalEffect(data,who,bone,position,rotation);
}
void Install(){
    if(Enabled()){
        // 只使用KenshiLib本机实际版本映射，不采用SDK注释RVA，不改变已有防御/反应Hook的安装。
        const intptr_t wound=KenshiLib::GetRealAddress(&MedicalSystem::addWound),effect=KenshiLib::GetRealAddress(&CombatClass::addEffect);
        if(wound)woundInstalled=KenshiLib::AddHook(wound,reinterpret_cast<void*>(&WoundHook),&originalWound)==KenshiLib::SUCCESS&&originalWound;
        if(effect)effectInstalled=KenshiLib::AddHook(effect,reinterpret_cast<void*>(&EffectHook),&originalEffect)==KenshiLib::SUCCESS&&originalEffect;
    }
    IrisWoundAudit::Install(woundInstalled); // 085根探针成功后才安装子阶段；失败不阻断正常动作。
    // 缺失诊断入口只表示覆盖不完整，不应让正常武器或私有选招被禁用；未覆盖时间明确归入余量。
    std::ostringstream out;out<<"native_profile_ready contract=IRIS_NATIVE_PROFILE_084 enabled="<<Enabled()<<" service="<<ServiceEnabled()<<" wound_hook="<<woundInstalled<<" effect_hook="<<effectInstalled<<" existing_defence_reaction=1 new_diagnostic_hooks="<<(static_cast<unsigned>(woundInstalled)+static_cast<unsigned>(effectInstalled))<<" tls_failures="<<tlsFailures<<" policy=observe_only callbacks_forward_once=1 unknown_time=unattributed new_threads=0";IrisDiagnostics::Log(out.str());
}
Hit::Hit(unsigned c,unsigned e,unsigned m,unsigned o):active(false),generation(0),cast(c),event(e),move(m),ordinal(o),nested(0),begin(0),top(0),gapActive(false),gapCursor(0){
    if(!Enabled())return;DWORD saved=GetLastError();Hit* parent=static_cast<Hit*>(ReadTLS(hitTLS));
    // 同线程嵌套的Iris受击纳入外层同步子树，不再创建重叠根样本；单独计数，避免累计耗时重复相加。
    if(parent){++parent->nested;SetLastError(saved);return;}
    for(unsigned i=0;i<PART_COUNT;++i){inclusive[i]=exclusive[i]=0;calls[i]=0;}
    generation=Generation();active=WriteTLS(hitTLS,this);if(active)begin=IrisDiagnostics::Now();
    // 091已建立的根按N抽样，复用既有时钟；关闭无额外QPC/TLS/锁，嵌套根不重复记录。
    if(active&&begin>0&&gapOption&&gapEvery){
        const unsigned serial=unsigned(InterlockedIncrement(&gapSequence));
        if((serial-1)%gapEvery==0){gapActive=true;gapCursor=begin;for(unsigned i=0;i<=PART_COUNT;++i)gaps[i]=0;}}
    SetLastError(saved);
}
Hit::~Hit(){
    if(!active)return;DWORD saved=GetLastError();const double end=IrisDiagnostics::Now();double elapsed=end-begin;WriteTLS(hitTLS,0);
    if(gapActive&&end>=gapCursor)gaps[PART_COUNT]+=end-gapCursor;
    try{Guard guard;if(generation!=Generation()){++nativeRun.invalidated;++nativeWindow.invalidated;}
        else if(begin>0&&elapsed>=0&&_finite(elapsed)){
            double accounted=0;for(unsigned i=0;i<PART_COUNT;++i)accounted+=exclusive[i];
            NativeStats* rows[2]={&nativeRun,&nativeWindow};
            for(unsigned row=0;row<2;++row){rows[row]->total.Add(elapsed);rows[row]->unattributed.Add(std::max(0.0,elapsed-accounted));rows[row]->nested+=nested;if(std::uncaught_exception())++rows[row]->exceptional;
                for(unsigned i=0;i<PART_COUNT;++i){rows[row]->inclusive[i].Add(inclusive[i]);rows[row]->exclusive[i].Add(exclusive[i]);rows[row]->calls[i]+=calls[i];}
                if(gapActive)for(unsigned i=0;i<=PART_COUNT;++i)rows[row]->gaps[i].Add(gaps[i]);}
            ++sequence;
            // 仅首次4笔慢样本/之后每10秒一笔带分项明细；所有调用仍进固定桶，日志限频不截断统计。
            double now=IrisDiagnostics::Now();if(elapsed>=1&&(notices<4||now-lastNotice>=10000)){
                ++notices;lastNotice=now;std::ostringstream out;out<<std::setprecision(10)<<"native_profile_slow contract=IRIS_NATIVE_PROFILE_084 call="<<sequence<<" generation="<<generation<<" cast="<<cast<<" event="<<event<<" move="<<move<<" flush_ordinal="<<ordinal<<" wall_ms="<<elapsed<<" defence_exclusive_ms="<<exclusive[DEFENCE]<<" wound_exclusive_ms="<<exclusive[WOUND]<<" reaction_exclusive_ms="<<exclusive[REACTION]<<" effect_exclusive_ms="<<exclusive[EFFECT]<<" unattributed_ms="<<std::max(0.0,elapsed-accounted)<<" nested_roots_skipped="<<nested<<" wall_not_CPU=1 hooks_included=1 internal_remainder_cause=unconfirmed gap_sampled="<<gapActive;
                // 沿用原慢样本限频，不额外增加逐笔IO；未抽中明确标0，不伪造间隙数据。
                if(gapActive)for(unsigned i=0;i<=PART_COUNT;++i)out<<" gap"<<i<<"_ms="<<gaps[i];IrisDiagnostics::Log(out.str());}
        }
    }catch(const std::exception&){/* 纯诊断格式化失败不能改变已经完成的原生受击。 */}
    SetLastError(saved);
}
PartScope::PartScope(Part p):hit(0),previous(0),part(p),begin(0),children(0){
    if(!Enabled())return;DWORD saved=GetLastError();hit=static_cast<Hit*>(ReadTLS(hitTLS));
    if(hit){previous=hit->top;hit->top=this;begin=IrisDiagnostics::Now();
        // 只在顶层Part之间分割余量；嵌套Part已计入父范围，不能把同段时间再计成间隙。
        if(!previous&&hit->gapActive&&begin>=hit->gapCursor)hit->gaps[part]+=begin-hit->gapCursor;}SetLastError(saved);
}
PartScope::~PartScope(){
    if(!hit)return;DWORD saved=GetLastError();double elapsed=IrisDiagnostics::Now()-begin;hit->top=previous;
    if(!previous&&hit->gapActive&&begin>0&&elapsed>=0&&_finite(elapsed))hit->gapCursor=begin+elapsed;
    if(begin>0&&elapsed>=0&&_finite(elapsed)){++hit->calls[part];hit->inclusive[part]+=elapsed;hit->exclusive[part]+=std::max(0.0,elapsed-children);if(previous)previous->children+=elapsed;}
    SetLastError(saved);
}
Frame::Frame(Count frame):previous(0),active(false),finished(false),sawPending(false),generation(0),token(frame),callbacks(0),repeated(0),waiting(0),repeatReady(0),flushes(0),progress(0),nativeCalls(0),inspected(0),begin(0){
    if(!ServiceEnabled())return;DWORD saved=GetLastError();previous=static_cast<Frame*>(ReadTLS(frameTLS));generation=Generation();active=WriteTLS(frameTLS,this);if(active)begin=IrisDiagnostics::Now();SetLastError(saved);
}
Frame::~Frame(){Finish();}
void Frame::Finish(){
    if(!active||finished)return;finished=true;DWORD saved=GetLastError();double elapsed=IrisDiagnostics::Now()-begin;WriteTLS(frameTLS,previous);
    {Guard guard;if(generation==Generation()){ServiceStats* rows[2]={&serviceRun,&serviceWindow};for(unsigned i=0;i<2;++i){ServiceStats& s=*rows[i];++s.frames;s.lastFrameToken=token;s.callbacks+=callbacks;s.repeated+=repeated;s.waiting+=waiting;s.repeatReady+=repeatReady;s.flushes+=flushes;s.progress+=progress;s.nativeCalls+=nativeCalls;s.inspected+=inspected;if(sawPending&&!flushes)++s.noFlush;if(begin>0)s.frameWall.Add(std::max(0.0,elapsed));}}}
    SetLastError(saved);
}
void Callback(bool done,Count pending,const IrisDiagnostics::WindowState& state,double probeMs){
    if(!ServiceEnabled())return;DWORD saved=GetLastError();Frame* f=static_cast<Frame*>(ReadTLS(frameTLS));if(!f){SetLastError(saved);return;}
    ++f->callbacks;if(done)++f->repeated;if(!pending){{Guard guard;if(f->generation==Generation())lastWaitingCallback=0;}SetLastError(saved);return;}f->sawPending=true;++f->waiting;
    const bool ready=!state.failed&&state.unavailable==0&&state.physicsRunning==0&&state.aiRunning==0&&state.paused==0;
    if(done&&ready)++f->repeatReady;
    {Guard guard;if(f->generation==Generation()){double now=IrisDiagnostics::Now();ServiceStats* rows[2]={&serviceRun,&serviceWindow};
        for(unsigned i=0;i<2;++i){ServiceStats& s=*rows[i];s.probe.Add(probeMs);if(state.failed)++s.readErrors;else if(state.unavailable==1)++s.world;else if(state.physicsRunning==1)++s.physics;else if(state.aiRunning==1)++s.ai;else if(state.paused==1)++s.paused;else if(!ready)++s.unknown;
            if(lastWaitingCallback>0&&now>=lastWaitingCallback)s.callbackGap.Add(now-lastWaitingCallback);}lastWaitingCallback=now;}}
    SetLastError(saved);
}
void Medical(Count before,Count remaining,unsigned done,unsigned checked,const char* reason,double elapsed){
    if(!ServiceEnabled()||(!before&&!remaining&&!checked))return;DWORD saved=GetLastError();Frame* f=static_cast<Frame*>(ReadTLS(frameTLS));if(!f){SetLastError(saved);return;}
    f->sawPending=true;++f->flushes;f->nativeCalls+=done;f->inspected+=checked;if(done)++f->progress;
    {Guard guard;if(f->generation==Generation()){double now=IrisDiagnostics::Now();ServiceStats* rows[2]={&serviceRun,&serviceWindow};
        for(unsigned i=0;i<2;++i){ServiceStats& s=*rows[i];s.flushWall.Add(elapsed);if(!strcmp(reason,"time_budget"))++s.timeYield;else if(!strcmp(reason,"count_budget"))++s.countYield;else if(!strcmp(reason,"scan_budget"))++s.scanYield;
            // 上一批仍有积压时才统计服务间隔；包含暂停的墙钟，不将隔了很久的下一场战斗当积压。
            if(done&&lastRemaining&&lastProgress>0&&now>=lastProgress)s.progressGap.Add(now-lastProgress);}
        if(done)lastProgress=now;if(!remaining)lastProgress=0;lastRemaining=remaining;}}
    SetLastError(saved);
}
void Reset(){
    IrisWoundAudit::Reset(); // 085读档只推进代数，绝不释放正在借用的栈上下文。
    if(!Enabled()&&!ServiceEnabled())return;Guard guard;InterlockedIncrement(&generation);lastWaitingCallback=lastProgress=0;lastRemaining=0;
    // 不清理TLS中的栈上下文；原生重入读档时由其RAII自然退出，代数失效样本不会混进新世界。
}
static void WriteStat(std::ostringstream& out,const Stat& s){
    out<<std::setprecision(12)<<" samples="<<s.n<<" wall_ms="<<s.sum<<" max_ms="<<s.max<<" p50_upper_ms="<<s.Percent(50)<<" p95_upper_ms="<<s.Percent(95)<<" p99_upper_ms="<<s.Percent(99)<<" histogram=";for(unsigned i=0;i<16;++i)out<<(i?",":"")<<s.buckets[i];
}
void Summary(Count id){
    IrisWoundAudit::Summary(id); // 085复制纯值后离开专用锁再日志，不形成新锁序环。
    if(!Enabled()&&!ServiceEnabled())return;Guard guard;
    static const char* parts[PART_COUNT]={"defence","add_wound","reaction","add_effect"};
    static const char* gapNames[PART_COUNT+1]={"before_defence","before_add_wound","before_reaction","before_add_effect","after_last_part"};
    for(unsigned scope=0;scope<2;++scope){const char* label=scope?"process":"window";
        if(Enabled()){const NativeStats& n=scope?nativeRun:nativeWindow;
            for(unsigned k=0;k<2+PART_COUNT*2;++k){std::ostringstream out;out<<"audit_native_profile id="<<id<<" scope="<<label<<" generation="<<Generation()<<" tls_failures="<<InterlockedCompareExchange(&tlsFailures,0,0)<<" channel="<<(k==0?"native_call":k==1?"unattributed":parts[(k-2)/2])<<" measure="<<(k<2?"root":(k-2)%2?"exclusive":"inclusive");
                WriteStat(out,k==0?n.total:k==1?n.unattributed:(k-2)%2?n.exclusive[(k-2)/2]:n.inclusive[(k-2)/2]);
                out<<" sample_basis=native_root_scope_exits zero_stage_samples_included=1 stage_invocations="<<(k<2?n.total.n:n.calls[(k-2)/2])<<" nested_roots_skipped="<<n.nested<<" exception_exits="<<n.exceptional<<" invalidated_calls="<<n.invalidated<<" wound_hook="<<woundInstalled<<" effect_hook="<<effectInstalled<<" wall_not_CPU=1 nested_inclusive_not_additive=1 FPS_measured=0";IrisDiagnostics::Log(out.str());}}
        // 091间隙名称只说明时间位置；含调度/其他插件与未探测链，不能据此认定某原生函数慢。
        if(Enabled()&&gapOption){const NativeStats& n=scope?nativeRun:nativeWindow;
            for(unsigned k=0;k<=PART_COUNT;++k){if(!n.gaps[k].n)continue;std::ostringstream out;
                out<<"audit_native_gap id="<<id<<" scope="<<label<<" channel="<<gapNames[k];WriteStat(out,n.gaps[k]);
                out<<" sample_every="<<gapEvery<<" boundary=top_level_probe sampled_only=1 unknown_callee=1 existing_clocks_reused=1 new_hooks=0 FPS_measured=0";IrisDiagnostics::Log(out.str());}}
        if(ServiceEnabled()){const ServiceStats& s=scope?serviceRun:serviceWindow;
            std::ostringstream out;out<<"audit_service id="<<id<<" scope="<<label<<" generation="<<Generation()<<" tls_failures="<<InterlockedCompareExchange(&tlsFailures,0,0)<<" frames="<<s.frames<<" last_actual_frame_token="<<s.lastFrameToken<<" callbacks="<<s.callbacks<<" already_updated_callbacks="<<s.repeated<<" pending_callbacks="<<s.waiting<<" already_updated_ready_observations="<<s.repeatReady<<" pending_frames_without_flush="<<s.noFlush<<" queued_flushes="<<s.flushes<<" progress_flushes="<<s.progress<<" native_calls="<<s.nativeCalls<<" inspected="<<s.inspected<<" time_yields="<<s.timeYield<<" count_yields="<<s.countYield<<" scan_yields="<<s.scanYield<<" observed_physics_running="<<s.physics<<" observed_ai_running="<<s.ai<<" observed_paused="<<s.paused<<" observed_world_invalid="<<s.world<<" probe_failures="<<s.readErrors<<" unknown="<<s.unknown<<" diagnostic_getters_only=1 queues_not_read=1 eligibility_is_observation=1 flush_schedule_unchanged=1 frame_token_independent_of_logging=1";IrisDiagnostics::Log(out.str());
            const Stat* stats[5]={&s.callbackGap,&s.progressGap,&s.frameWall,&s.flushWall,&s.probe};const char* names[5]={"pending_callback_gap","backlog_progress_gap","frame_callback_wall","queued_flush_wall","probe_cost"};
            for(unsigned k=0;k<5;++k){std::ostringstream row;row<<"audit_service_timing id="<<id<<" scope="<<label<<" generation="<<Generation()<<" tls_failures="<<InterlockedCompareExchange(&tlsFailures,0,0)<<" channel="<<names[k];WriteStat(row,*stats[k]);row<<" includes_pause=1 wall_not_CPU=1 FPS_measured=0";IrisDiagnostics::Log(row.str());}}
    }
    nativeWindow=NativeStats();serviceWindow=ServiceStats();
}
}
