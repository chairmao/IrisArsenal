/* 085只观察同一个原生addWound入口；不补医疗、不改变参数/返回/异常、不启动线程。 */
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>
#include "IrisWoundAudit.h"
#include "IrisNativeAudit.h"
#include <core/Functions.h>
#include <kenshi/MedicalSystem.h>
#include <kenshi/Damages.h>
#include <kenshi/Appearance.h>
#include <kenshi/Character.h>
#include <kenshi/RootObjectFactory.h>
#include <kenshi/Item.h>
#include <kenshi/gui/ForgottenGUI.h>
#include <algorithm>
#include <sstream>
#include <iomanip>
#include <exception>
#include <float.h>
namespace IrisWoundAudit {
typedef IrisDiagnostics::Count Count;
enum Stage {APPLY,APPEARANCE,LABEL,BLOOD,AMPUTATE,ITEM_CREATE,LIMB_SETUP,UPDATE_STATE,PART_COLLAPSE,RAGDOLL,STAGES};
typedef char StageCountMatches[(STAGES==STAGE_COUNT)?1:-1];
static bool option=false,branchOption=false,lockReady=false,rootAvailable=false;
static DWORD slot=TLS_OUT_OF_INDEXES;static volatile LONG epoch=0,tlsFailures=0,tlsFault=0;
static CRITICAL_SECTION statsMutex;static bool installed[STAGES]={0};
/* 新锁只保护本单元固定值统计；锁内绝不进入游戏、旧插件锁或日志。发布/读取不反向持锁。 */
struct Lock {Lock(){EnterCriticalSection(&statsMutex);}~Lock(){LeaveCriticalSection(&statsMutex);}};
bool Enabled(){return option&&lockReady&&slot!=TLS_OUT_OF_INDEXES&&rootAvailable&&IrisNativeAudit::Enabled()&&InterlockedCompareExchange(&tlsFault,0,0)==0;}
static unsigned Epoch(){return unsigned(InterlockedCompareExchange(&epoch,0,0));}
/* TLS写入失败时全局关闭本诊断，后续Enabled在ReadTLS前返回，避免失败恢复留下的借用地址被再次读取。 */
static Scope* Current(){DWORD saved=GetLastError();Scope* p=slot==TLS_OUT_OF_INDEXES?0:static_cast<Scope*>(TlsGetValue(slot));SetLastError(saved);return p;}
static bool SetCurrent(Scope* p){DWORD saved=GetLastError();bool ok=slot!=TLS_OUT_OF_INDEXES&&TlsSetValue(slot,p)!=0;if(!ok){InterlockedIncrement(&tlsFailures);InterlockedExchange(&tlsFault,1);}SetLastError(saved);return ok;}
static const double bounds[15]={0,.01,.025,.05,.1,.25,.5,1,2,4,8,16,32,64,128};
struct Stat {
    Count n,buckets[16];double sum,max;
    Stat():n(0),sum(0),max(0){for(unsigned i=0;i<16;++i)buckets[i]=0;}
    void Add(double ms){if(!_finite(ms)||ms<0)return;++n;sum+=ms;max=std::max(max,ms);unsigned k=0;while(k<15&&ms>bounds[k])++k;++buckets[k];}
    double Percent(unsigned percent)const {if(!n)return 0;Count target=(n*percent+99)/100,count=0;for(unsigned i=0;i<16;++i){count+=buckets[i];if(count>=target)return i<15?bounds[i]:-1;}return -1;}
};
struct Stats {
    Stat root,rest,inclusive[STAGES],exclusive[STAGES],amounts[5];
    Count calls[STAGES],nested,mixed,invalidated,exceptions;double maximumStage[STAGES],maximumRest;
    Stats():nested(0),mixed(0),invalidated(0),exceptions(0),maximumRest(0){for(unsigned i=0;i<STAGES;++i){calls[i]=0;maximumStage[i]=0;}}
};
static Stats run[2],window[2];
void Configure(bool value,bool branches){
    option=value;branchOption=branches;
    /* 程序缺省关闭，且沿用084总日志/性能/明细门；失败只关闭诊断，不阻断正常战斗。 */
    if(!option||!IrisNativeAudit::Enabled())return;DWORD saved=GetLastError();
    lockReady=InitializeCriticalSectionAndSpinCount(&statsMutex,0)!=0;
    if(lockReady)slot=TlsAlloc();SetLastError(saved);
    /* 已安装Hook会持续转发，TLS和统计锁保留到进程退出，读档不释放或复用槽。 */
}
class Part {
    Scope* owner;Part* previous;Stage stage;double begin,children;
public:
    explicit Part(Stage value):owner(0),previous(0),stage(value),begin(0),children(0){
        if(!Enabled())return;DWORD saved=GetLastError();owner=Current();
        if(owner){previous=owner->top;owner->top=this;begin=IrisDiagnostics::Now();}SetLastError(saved);
    }
    ~Part(){
        if(!owner)return;DWORD saved=GetLastError();double elapsed=IrisDiagnostics::Now()-begin;owner->top=previous;
        if(begin>0&&elapsed>=0&&_finite(elapsed)){++owner->calls[stage];owner->inclusive[stage]+=elapsed;owner->exclusive[stage]+=std::max(0.0,elapsed-children);if(previous)previous->children+=elapsed;}
        SetLastError(saved);
    }
private:Part(const Part&);Part& operator=(const Part&);
};
Scope::Scope(bool irisBridge,const Damages& damage):active(false),bridge(irisBridge),generation(0),nested(0),mixed(0),begin(0),amount(0),top(0){
    if(!Enabled())return;DWORD saved=GetLastError();Scope* parent=Current();
    /* 同线程嵌套addWound只归入最外层子树，避免时间重复相加；混合来源重入单列，不能当纯原版对照。 */
    if(parent){++parent->nested;if(parent->bridge!=bridge)++parent->mixed;SetLastError(saved);return;}
    amount=double(damage.cut)+double(damage.blunt)+double(damage.pierce);
    for(unsigned i=0;i<STAGES;++i){inclusive[i]=exclusive[i]=0;calls[i]=0;}
    generation=Epoch();active=SetCurrent(this);if(active)begin=IrisDiagnostics::Now();SetLastError(saved);
}
Scope::~Scope(){
    if(!active)return;DWORD saved=GetLastError();double elapsed=IrisDiagnostics::Now()-begin;SetCurrent(0);
    /* 原生返回后才提交纯值，无字符串分配/逐笔IO；不读取Character、部位、后台容器或保留裸指针。 */
    {Lock lock;Stats* rows[2]={&run[bridge?0:1],&window[bridge?0:1]};
        for(unsigned k=0;k<2;++k){Stats& s=*rows[k];
            if(generation!=Epoch()){++s.invalidated;continue;}
            if(begin<=0||elapsed<0||!_finite(elapsed))continue;
            double accounted=0;for(unsigned i=0;i<STAGES;++i)accounted+=exclusive[i];
            const double rest=std::max(0.0,elapsed-accounted);bool maximum=elapsed>s.root.max;
            s.root.Add(elapsed);s.rest.Add(rest);s.nested+=nested;s.mixed+=mixed;if(std::uncaught_exception())++s.exceptions;
            /* 伤害分层只用入口cut+blunt+pierce纯值，不额外调用伤害计算或改写Damages。 */
            unsigned bucket=!_finite(amount)||amount<0?4:amount<=50?0:amount<=200?1:amount<=1000?2:3;s.amounts[bucket].Add(elapsed);
            for(unsigned i=0;i<STAGES;++i){s.calls[i]+=calls[i];s.inclusive[i].Add(inclusive[i]);s.exclusive[i].Add(exclusive[i]);if(maximum)s.maximumStage[i]=exclusive[i];}
            if(maximum)s.maximumRest=rest;
        }}SetLastError(saved);
}
typedef void(__fastcall* ApplyFn)(MedicalSystem*,MedicalSystem::HealthPartStatus*,const Damages&,bool,bool,const Ogre::Vector3&);
typedef void(__fastcall* AppearanceFn)(AppearanceBase*,Wound*);
typedef ScreenLabel*(__fastcall* LabelFn)(ForgottenGUI*,const std::string&,const MyGUI::Colour&,ScreenLabel::LabelSize,ScreenLabel::RisingSpeed);
typedef void(__fastcall* BloodFn)(MedicalSystem*,const Damages&,CutDirection,AttackDirection::Enum);
static ApplyFn originalApply=0;static AppearanceFn originalAppearance=0;static LabelFn originalLabel=0;static BloodFn originalBlood=0;
/* 所有引用/枚举/返回值原样同步转发一次；没有addWound上下文时只做轻量转发，不统计普通GUI调用。 */
static void __fastcall ApplyHook(MedicalSystem* self,MedicalSystem::HealthPartStatus* part,const Damages& damage,bool loading,bool sever,const Ogre::Vector3& force){Part timing(APPLY);originalApply(self,part,damage,loading,sever,force);}
static void __fastcall AppearanceHook(AppearanceBase* self,Wound* wound){Part timing(APPEARANCE);originalAppearance(self,wound);}
static ScreenLabel* __fastcall LabelHook(ForgottenGUI* self,const std::string& text,const MyGUI::Colour& color,ScreenLabel::LabelSize size,ScreenLabel::RisingSpeed speed){Part timing(LABEL);return originalLabel(self,text,color,size,speed);}
static void __fastcall BloodHook(MedicalSystem* self,const Damages& damage,CutDirection dir,AttackDirection::Enum from){Part timing(BLOOD);originalBlood(self,damage,dir,from);}
/* 086按本机真实原生调用链分别观察高伤分支。ABI严格跟随SDK，所有参数/返回/引用与异常原样转发。
   Part只在既有addWound根TLS中计时；普通造物/布娃娃调用不建根、不保存对象、不做每击IO。
   子分支会从父exclusive扣除，比较085的apply总量应读inclusive；嵌套inclusive不能相加。 */
typedef void(__fastcall* AmputateFn)(MedicalSystem*,RobotLimbs::Limb,bool,const Ogre::Vector3&);
typedef Item*(__fastcall* CreateFn)(RootObjectFactory*,GameData*,const hand&,GameData*,GameData*,int,Faction*);
typedef void(__fastcall* SetupFn)(SeveredLimbItem*,Character*,int,const Ogre::Vector3&);
typedef void(__fastcall* StateFn)(MedicalSystem*);
typedef void(__fastcall* CollapseFn)(MedicalSystem*,MedicalSystem::HealthPartStatus*);
typedef void(__fastcall* RagdollFn)(Character*,bool,RagdollPart::Enum);
static AmputateFn originalAmputate=0;static CreateFn originalCreate=0;static SetupFn originalSetup=0;
static StateFn originalState=0;static CollapseFn originalCollapse=0;static RagdollFn originalRagdoll=0;
static void __fastcall AmputateHook(MedicalSystem* self,RobotLimbs::Limb limb,bool create,const Ogre::Vector3& force){Part timing(AMPUTATE);originalAmputate(self,limb,create,force);}
static Item* __fastcall CreateHook(RootObjectFactory* self,GameData* data,const hand& identity,GameData* mesh,GameData* material,int level,Faction* faction){Part timing(ITEM_CREATE);return originalCreate(self,data,identity,mesh,material,level,faction);}
static void __fastcall SetupHook(SeveredLimbItem* self,Character* who,int limb,const Ogre::Vector3& force){Part timing(LIMB_SETUP);originalSetup(self,who,limb,force);}
static void __fastcall StateHook(MedicalSystem* self){Part timing(UPDATE_STATE);originalState(self);}
static void __fastcall CollapseHook(MedicalSystem* self,MedicalSystem::HealthPartStatus* part){Part timing(PART_COLLAPSE);originalCollapse(self,part);}
static void __fastcall RagdollHook(Character* self,bool on,RagdollPart::Enum part){Part timing(RAGDOLL);originalRagdoll(self,on,part);}
void Install(bool available){
    rootAvailable=available;
    if(Enabled()){
        const intptr_t apply=KenshiLib::GetRealAddress(&MedicalSystem::applyDamage),appearance=KenshiLib::GetRealAddress(&AppearanceBase::addWound);
        const intptr_t label=KenshiLib::GetRealAddress(&ForgottenGUI::createScreenLabel),blood=KenshiLib::GetRealAddress(&MedicalSystem::splatBlood);
        if(apply)installed[APPLY]=KenshiLib::AddHook(apply,reinterpret_cast<void*>(&ApplyHook),&originalApply)==KenshiLib::SUCCESS&&originalApply;
        if(appearance)installed[APPEARANCE]=KenshiLib::AddHook(appearance,reinterpret_cast<void*>(&AppearanceHook),&originalAppearance)==KenshiLib::SUCCESS&&originalAppearance;
        if(label)installed[LABEL]=KenshiLib::AddHook(label,reinterpret_cast<void*>(&LabelHook),&originalLabel)==KenshiLib::SUCCESS&&originalLabel;
        if(blood)installed[BLOOD]=KenshiLib::AddHook(blood,reinterpret_cast<void*>(&BloodHook),&originalBlood)==KenshiLib::SUCCESS&&originalBlood;
    }
    /* 独立开关默认关闭；四阶段探针与根有效后才扩展。失败只表示未覆盖，不阻止正常伤害。
       createItem重载由SDK精确成员指针选择，再交KenshiLib实际映射；不用硬编码RVA。 */
    if(Enabled()&&branchOption&&installed[APPLY]){
        typedef Item*(RootObjectFactory::* CreateMember)(GameData*,const hand&,GameData*,GameData*,int,Faction*);
        CreateMember createMember=static_cast<CreateMember>(&RootObjectFactory::createItem);
        const intptr_t a=KenshiLib::GetRealAddress(&MedicalSystem::amputate),c=KenshiLib::GetRealAddress(createMember);
        const intptr_t s=KenshiLib::GetRealAddress(&SeveredLimbItem::setupFromCharacter),u=KenshiLib::GetRealAddress(&MedicalSystem::updateDamageState);
        const intptr_t p=KenshiLib::GetRealAddress(&MedicalSystem::ragdollPartCollapse),r=KenshiLib::GetRealAddress(&Character::ragdollMode);
        if(a)installed[AMPUTATE]=KenshiLib::AddHook(a,reinterpret_cast<void*>(&AmputateHook),&originalAmputate)==KenshiLib::SUCCESS&&originalAmputate;
        if(c)installed[ITEM_CREATE]=KenshiLib::AddHook(c,reinterpret_cast<void*>(&CreateHook),&originalCreate)==KenshiLib::SUCCESS&&originalCreate;
        if(s)installed[LIMB_SETUP]=KenshiLib::AddHook(s,reinterpret_cast<void*>(&SetupHook),&originalSetup)==KenshiLib::SUCCESS&&originalSetup;
        if(u)installed[UPDATE_STATE]=KenshiLib::AddHook(u,reinterpret_cast<void*>(&StateHook),&originalState)==KenshiLib::SUCCESS&&originalState;
        if(p)installed[PART_COLLAPSE]=KenshiLib::AddHook(p,reinterpret_cast<void*>(&CollapseHook),&originalCollapse)==KenshiLib::SUCCESS&&originalCollapse;
        if(r)installed[RAGDOLL]=KenshiLib::AddHook(r,reinterpret_cast<void*>(&RagdollHook),&originalRagdoll)==KenshiLib::SUCCESS&&originalRagdoll;
    }
    std::ostringstream branch;branch<<"medical_branch_ready contract=IRIS_MEDICAL_BRANCH_086 enabled="<<(Enabled()&&branchOption)<<" amputate_hook="<<installed[AMPUTATE]<<" item_create_hook="<<installed[ITEM_CREATE]<<" limb_setup_hook="<<installed[LIMB_SETUP]<<" update_state_hook="<<installed[UPDATE_STATE]<<" part_collapse_hook="<<installed[PART_COLLAPSE]<<" ragdoll_hook="<<installed[RAGDOLL]<<" parent_apply_compare=inclusive stage_chain_coverage=probe_to_saved_original later_wrappers_may_be_unattributed=1 policy=observe_only native_calls_unchanged=1";IrisDiagnostics::Log(branch.str());
    /* 各探针覆盖单列；失败阶段仍属于余量。后装插件可能在探针外层包装同一入口， */
    /* 子阶段不是“干净原版”或“完整插件链”的保证；未覆盖的包装仍在addWound根的余量内。 */
    std::ostringstream out;out<<"wound_profile_ready contract=IRIS_WOUND_PROFILE_085 enabled="<<Enabled()<<" root_hook="<<rootAvailable<<" apply_hook="<<installed[APPLY]<<" appearance_hook="<<installed[APPEARANCE]<<" label_hook="<<installed[LABEL]<<" blood_hook="<<installed[BLOOD]<<" tls_failures="<<tlsFailures<<" tls_slot_available="<<(slot!=TLS_OUT_OF_INDEXES)<<" stats_lock_ready="<<lockReady<<" source_comparison=iris_bridge,outside_bridge outside_is_not_clean_vanilla=1 stage_chain_coverage=probe_to_saved_original later_wrappers_may_be_unattributed=1 policy=observe_only new_threads=0 per_hit_IO=0";IrisDiagnostics::Log(out.str());
}
void Reset(){if(!option||!lockReady)return;Lock lock;InterlockedIncrement(&epoch);/* 不释放当前线程或其他线程尚在使用的栈上下文。 */}
static void Write(std::ostringstream& out,const Stat& s){out<<std::setprecision(12)<<" samples="<<s.n<<" wall_ms="<<s.sum<<" max_ms="<<s.max<<" p50_upper_ms="<<s.Percent(50)<<" p95_upper_ms="<<s.Percent(95)<<" p99_upper_ms="<<s.Percent(99)<<" histogram=";for(unsigned i=0;i<16;++i)out<<(i?",":"")<<s.buckets[i];}
void Summary(Count id){
    if(!option||!lockReady||!IrisDiagnostics::DetailsEnabled())return;
    if(!Enabled()){std::ostringstream out;out<<"wound_profile_status id="<<id<<" enabled=0 tls_failures="<<InterlockedCompareExchange(&tlsFailures,0,0)<<" tls_fault="<<InterlockedCompareExchange(&tlsFault,0,0)<<" root_hook="<<rootAvailable;IrisDiagnostics::Log(out.str());return;}
    /* 独立锁内仅拷贝固定值，离锁后才格式化和进入既有日志锁，杜绝statsMutex→Iris::mutex锁序。 */
    Stats snapshot[2][2];{Lock lock;for(unsigned source=0;source<2;++source){snapshot[0][source]=window[source];snapshot[1][source]=run[source];window[source]=Stats();}}
    static const char* names[STAGES]={"apply_damage","appearance_wound","screen_label","splat_blood","amputate","item_create","limb_setup","update_damage_state","part_collapse","ragdoll_mode"};
    static const char* buckets[5]={"le50","le200","le1000","gt1000","invalid"};
    for(unsigned period=0;period<2;++period)for(unsigned source=0;source<2;++source){const Stats& s=snapshot[period][source];
        for(unsigned k=0;k<2+STAGES*2;++k){std::ostringstream out;
            out<<"audit_wound_profile id="<<id<<" scope="<<(period?"process":"window")<<" source="<<(source?"outside_bridge":"iris_bridge")<<" channel="<<(k==0?"add_wound":k==1?"unattributed":names[(k-2)/2])<<" measure="<<(k<2?"root":(k-2)%2?"exclusive":"inclusive");
            Write(out,k==0?s.root:k==1?s.rest:(k-2)%2?s.exclusive[(k-2)/2]:s.inclusive[(k-2)/2]);
            out<<" stage_invocations="<<(k<2?s.root.n:s.calls[(k-2)/2])<<" nested_wounds_skipped="<<s.nested<<" mixed_source_nesting="<<s.mixed<<" invalidated_calls="<<s.invalidated<<" exception_exits="<<s.exceptions<<" tls_failures="<<InterlockedCompareExchange(&tlsFailures,0,0)<<" apply_hook="<<installed[APPLY]<<" appearance_hook="<<installed[APPEARANCE]<<" label_hook="<<installed[LABEL]<<" blood_hook="<<installed[BLOOD]<<" wall_not_CPU=1 zero_stage_samples_included=1 nested_inclusive_not_additive=1 FPS_measured=0";IrisDiagnostics::Log(out.str());
        }
        /* 按入口伤害量分层，避免将Iris高倍率群伤与普通低伤单击直接混成同场景性能对照。 */
        for(unsigned k=0;k<5;++k){std::ostringstream out;out<<"audit_wound_damage_bucket id="<<id<<" scope="<<(period?"process":"window")<<" source="<<(source?"outside_bridge":"iris_bridge")<<" input_damage="<<buckets[k];Write(out,s.amounts[k]);out<<" input_is_pre_armour=1 not_controlled_AB=1";IrisDiagnostics::Log(out.str());}
        std::ostringstream out;out<<std::setprecision(12)<<"audit_wound_max_sample id="<<id<<" scope="<<(period?"process":"window")<<" source="<<(source?"outside_bridge":"iris_bridge")<<" root_ms="<<s.root.max<<" apply_exclusive_ms="<<s.maximumStage[APPLY]<<" appearance_exclusive_ms="<<s.maximumStage[APPEARANCE]<<" label_exclusive_ms="<<s.maximumStage[LABEL]<<" blood_exclusive_ms="<<s.maximumStage[BLOOD]<<" unattributed_ms="<<s.maximumRest<<" same_root_sample=1";
        /* 最慢根的六项也来自同一次样本，不把不同命中的最大值拼接。 */
        for(unsigned k=AMPUTATE;k<STAGES;++k)out<<" "<<names[k]<<"_exclusive_ms="<<s.maximumStage[k];
        out<<" branch_contract=IRIS_MEDICAL_BRANCH_086 exclusive_basis=all_installed_stages";IrisDiagnostics::Log(out.str());
    }
}
}
