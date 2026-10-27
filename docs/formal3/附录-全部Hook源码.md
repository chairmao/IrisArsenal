# 全部Hook源码摘录（104源码快照）

这是当前源码中实际Hook定义，不是新实现或伪代码。保留完整条件/转发/参数；行为目标表见02。原路径/行号可对照同归档project目录。没有执行这些函数。

## FrameHook — IrisArsenal.cpp:455

```cpp
void __fastcall FrameHook(GameWorld* w,float dt){
    // 078仅记录含原生的总回调墙钟；不改原帧时钟或安全更新条件。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_FRAME);
    if(!InterlockedCompareExchange(&running,0,0)){originalFrame(w,dt);return;}
    LONG owner=InterlockedCompareExchange(&mainThread,LONG(GetCurrentThreadId()),0);if(owner&&DWORD(owner)!=GetCurrentThreadId()){originalFrame(w,dt);return;}
    IrisDiagnostics::Add(IrisDiagnostics::FRAME_CALLBACKS);FrameScope frame(w);IrisNativeAudit::Frame serviceFrame(realFrameToken);rawDelta=dt;clockConsumed=false;originalFrame(w,dt);
    // 未取得安全更新只累计游戏秒；帧尾没有Ogre/PhysX操作，后效不在收招时切换时钟。
    if(w&&(!w->initialized||w->gameResetting||w->isLoadingFromASaveGame()))deferredDelta=0;
    if(!clockConsumed&&w&&w->initialized&&!w->gameResetting&&!w->isLoadingFromASaveGame()&&!w->isPaused()&&Finite(dt)&&Finite(w->frameSpeedMult))deferredDelta+=std::max(0.f,dt)*std::max(0.f,w->frameSpeedMult);
    // 帧尾仅做纯值日志摘要/落盘；没有Ogre/PhysX访问，长时间无施放也保留统计。
    serviceFrame.Finish(); // 084原生帧返回后提交纯值观察；不是额外安全执行点。
    IrisDiagnostics::Summary("interval");IrisDiagnostics::Flush(false);
}
```

## SafeHook — IrisArsenal.cpp:501

```cpp
void __fastcall SafeHook(GameWorld* w){
    // 078仅记录含原生的总回调墙钟；不改原帧时钟或安全更新条件。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_SAFE);
    WindowAuditSession windowAudit(w);
    originalSafe(w);if(!InterlockedCompareExchange(&running,0,0)||DWORD(InterlockedCompareExchange(&mainThread,0,0))!=GetCurrentThreadId()||frameWorld!=w)return;
    ObserveServiceOpportunity(w,updateDone);if(updateDone)return;updateDone=true;
    windowAudit.Probe(w,IrisDiagnostics::WINDOW_POST_NATIVE);
    if(!Idle(w)){IrisDiagnostics::Add(IrisDiagnostics::UNSAFE_SKIPS);if(IrisDiagnostics::DetailsEnabled())Log("physics_or_AI_running; query_and_visual_update_skipped");return;}
    const double auditBegin=IrisDiagnostics::PerformanceEnabled()?IrisDiagnostics::Now():0;
    {Lock lock(&audit);IrisDiagnostics::BeginFrame();clockConsumed=true;frameDelta=0;
        if(!w->isPaused()){double d=deferredDelta+(Finite(rawDelta)&&Finite(w->frameSpeedMult)?std::max(0.f,rawDelta)*std::max(0.f,w->frameSpeedMult):0);frameDelta=d<=FLT_MAX?float(d):0;deferredDelta=0;}
        windowAudit.Probe(w,IrisDiagnostics::WINDOW_PRE_TICK);
        // 092完整根只包住原Tick；原生回调/主线程门/已有锁及锁外医疗不移动。
        try{IrisDiagnostics::CombatInterfaceFrame interfaceFrame;IrisDiagnostics::Scope timing(IrisDiagnostics::COMBAT_TICK);Tick(w);}catch(const std::exception& e){faulted=true;Clear(scene!=0,"runtime_error");Log(std::string("plugin_disabled: ")+e.what());}
        windowAudit.Probe(w,IrisDiagnostics::WINDOW_POST_TICK);}
    // 医疗/AI会重入其他插件，必须离开自身临界区后调用；不重试已经结算过的健康请求。
    if(!faulted&&!IrisCombat::ProofOnly())try{IrisCombat::Flush(w);}catch(const std::exception& e){Lock lock(&audit);faulted=true;Clear(scene!=0,"native_damage_error");Log(std::string("plugin_disabled: ")+e.what());}
    if(IrisDiagnostics::PerformanceEnabled())IrisDiagnostics::Record(IrisDiagnostics::SAFE_TICK,std::max(0.0,IrisDiagnostics::Now()-auditBegin));
    IrisDiagnostics::EndFrame();
}
```

## ChooseHook — IrisArsenal.cpp:534

```cpp
CombatTechniqueData* __fastcall ChooseHook(CharStats* stats,float range,float reach,CombatTechniqueData* last,bool stationary){
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_CHOOSE);
    CombatTechniqueData* native=originalChoose(stats,range,reach,last,stationary);if(!InterlockedCompareExchange(&running,0,0))return native;
    // 076：原生已在本回调使用同一stats/当前武器句柄；这里只读SDK武器身份，不读插件容器。
    // 先排除非本武器，再进锁复核。按实际stringID而非重武器枚举筛选，允许FCS修改类别。
    if(!UsesWeapon(stats))return native;
    Lock lock(&audit);if(!enabled||!UsesWeapon(stats))return native;
    if(!IrisCombat::ProofOnly()){
        // 原函数只调用一次，range/reach/last/stationary完整传递；不为试探资格重复选招或改公共池。
        // 资格不适用、故障或私选无结果均返回已取得的原生结果（包括NULL），不再强制空等。
        if(faulted||!NativeStandingMeleeAllowed(stats,native))return native;
        CombatTechniqueData* selected=IrisCombat::Choose(stats,range);return selected?selected:native;
    }
    // 指定武器严格独占本原型。未加载/距离不满足时返回原生NULL等待分支，不以错误通用动作兜底。
    Character* c=stats->me;if(faulted||!ActorReady(c))return 0;
    std::map<hand,Candidate>::iterator i=actors.find(c->handle);if(i==actors.end()){if(actors.size()<8)actors.insert(std::make_pair(c->handle,Candidate()));return 0;}
    if(!resources||!technique||!i->second.verified||!i->second.visual.entity||i->second.animation!=c->animation||!Finite(range)||range<technique->minDistanceVsStatic||range>technique->initialDistance)return 0;
    unsigned active=0;for(std::map<hand,Candidate>::const_iterator a=actors.begin();a!=actors.end();++a)if(a->second.active)++active;
    if(!i->second.active&&active>=maxActive)return 0;return technique;
}
```

## StartHook — IrisArsenal.cpp:561

```cpp
void __fastcall StartHook(AnimationClass* a,CombatTechniqueData* t,float speed,std::string extra){
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_START);
    // 076：非空且明确非私有技巧直接转发；NULL沿用旧路，不能改变原型尚未初始化时的边界。
    if(t&&!IrisCombat::OwnTechniqueIdentity(t)){originalStart(a,t,speed,extra);return;}
    originalStart(a,t,Speed(a,t,speed,&audit),extra);
    if(InterlockedCompareExchange(&running,0,0)){Lock lock(&audit);IrisCombat::Started(a,t);}
    if(InterlockedCompareExchange(&running,0,0)&&t==technique){Lock lock(&audit);for(std::map<hand,Candidate>::iterator i=actors.begin();i!=actors.end();++i)if(i->second.animation==a)++i->second.start;}
}
```

## RunHook — IrisArsenal.cpp:569

```cpp
void __fastcall RunHook(AnimationClass* a,CombatTechniqueData* t,float speed,std::string extra){
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_RUN);
    if(t&&!IrisCombat::OwnTechniqueIdentity(t)){originalRun(a,t,speed,extra);return;}
    originalRun(a,t,Speed(a,t,speed,&audit),extra);
}
```

## ResetHook — IrisArsenal.cpp:574

```cpp
void __fastcall ResetHook(GameWorld* w){{Lock lock;Clear(scene!=0,"world_reset");deferredDelta=0;}originalReset(w);}
```

## ShutdownHook — IrisArsenal.cpp:575

```cpp
void __fastcall ShutdownHook(Renderer* r){{Lock lock;if(r==renderer){Clear(scene!=0,"renderer_shutdown");scene=0;renderer=0;resources=false;}IrisDiagnostics::Flush(true);}originalShutdown(r);}
```

## VulcanDefenceHook — IrisCombat.cpp:1745

```cpp
HitMaterialType __fastcall VulcanDefenceHook(CombatClass* self,CutDirection dir,Damages& damage,Character* who){
    // 078此全局防御入口也可能高频；仅抽样原回调总耗时，TLS与防御结果保持。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_DEFENCE);
    IrisNativeAudit::PartScope nativePart(IrisNativeAudit::DEFENCE); // 084同步子树观察，原返回值不改。
    VulcanHitContext* context=defenceTLS==TLS_OUT_OF_INDEXES?0:static_cast<VulcanHitContext*>(TlsGetValue(defenceTLS));
    bool matches=context&&context->pending&&context->combat==self&&context->damage==&damage&&context->caster==who;
    // 必须在调用原链之前消费；原函数引起的嵌套攻击不能借用本次“已物理命中”的许可。
    if(matches)context->pending=false;
    HitMaterialType result=originalDefence(self,dir,damage,who);
    if(matches){context->seen=true;context->original=result;if(result==HIT_MISSED||result==HIT_SWORD)return HIT_FLESH;}
    return result;
}
```

## MeleeStumbleHook — IrisCombat.cpp:1813

```cpp
void __fastcall MeleeStumbleHook(Character* self,CutDirection dir,Damages& damage,GameData* part,Character* attacker){
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_STUMBLE);
    IrisNativeAudit::PartScope nativePart(IrisNativeAudit::REACTION); // 084包括已有插件保护与原反应链。
    bool candidate=true;
    try{candidate=MayNeedTechniqueGuard(self?self->getCombatClass():0,true);}catch(const std::exception&){/* 无法确认时保留旧锁内异常回退。 */}
    if(!candidate){originalMeleeStumble(self,dir,damage,part,attacker);return;}
    bool suppress=false;CombatClass* combat=0;
    try{Guard guard(&audit);combat=self?self->getCombatClass():0;int move=ProtectedMeleeMove(combat);if(move<0)move=ProtectedRangedMove(combat);
        // 原生近战和弩弹都先addWound再调用此反应入口；只跳过新反应的选择/播放/任务取消，
        // 不改伤害数据，不再次医疗。所有有限反应强度均免疫，不再区分小僵直与大踉跄阈值。
        // 047覆盖六招特效近战和三招远程当前片段；普通三连击/后效、死亡/昏迷/已倒地及读档走原逻辑。
        // 045：禁用受击免疫时立即走原生；格挡保护开关不影响这里的医疗隔离。
        suppress=move>=0&&moves[move].immuneReactions&&Finite(damage.cut)&&Finite(damage.blunt)&&Finite(damage.pierce)&&Finite(damage.extraStun);
        if(suppress){Actor& actor=actors.find(self->handle)->second;++actor.stumbles;
            if(IrisDiagnostics::DetailsEnabled()){std::ostringstream out;out<<(RangedMove(move)?"ranged_stumble_guard cast=":"melee_stumble_guard cast=")<<(actor.active&&actor.move==move?actor.id:0)<<" move="<<moves[move].key<<" count="<<actor.stumbles<<" small=immune large=immune medical=unchanged";Log(out.str());}}
    }catch(const std::exception&){suppress=false;}
    // _getHit(false)保留原生退出潜行、deadTime及技巧检查计时；true才安排STUMBLE和反应强度。
    // 离开插件缓存锁后恰好调用一次，不扣第二次血、不回写战斗状态、不强播或重启动作。
    if(suppress){combat->_getHit(dir,damage,attacker,false);return;}
    originalMeleeStumble(self,dir,damage,part,attacker);
}
```

## MeleeBlockCheckHook — IrisCombat.cpp:1834

```cpp
bool __fastcall MeleeBlockCheckHook(CombatClass* self,float myAttack,float incomingAttack){
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_BLOCK);
    if(!MayNeedTechniqueGuard(self,false))return originalBlockCheck(self,myAttack,incomingAttack);
    bool suppress=false;
    try{Guard guard(&audit);const int move=ProtectedMeleeMove(self);
        // 045：只决定是否跳过主动格挡检查，不能把受击免疫当成主动格挡保护。
        suppress=move>=0&&moves[move].preventBlock;
        if(suppress){Actor& actor=actors.find(self->me->handle)->second;
            // 这是跳过防御评估的次数，不冒称每次都原本会格挡；明细开关开启时持续记录，不再按角色前三次截断。
            if(IrisDiagnostics::DetailsEnabled()){std::ostringstream out;out<<"melee_defence_check_skipped move="<<moves[move].key<<" actor="<<actor.owner.index<<":"<<actor.owner.serial<<" would_block=not_evaluated medical=unchanged";Log(out.str());}}
    }catch(const std::exception&){suppress=false;}
    // 原函数会直接修改战斗状态，因此受保护时在调用前返回false；正常对象原样转交。
    // 不持插件互斥量进入原生检查，不给死亡/昏迷/受击反应增加免疫。
    if(suppress)return false;return originalBlockCheck(self,myAttack,incomingAttack);
}
```

## UseHook — IrisRanged.cpp:152

```cpp
bool __fastcall UseHook(Character* c){
    // 078仅观察当前回调；普通角色原样转原生，没有新增能力/选招/开火资格。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_RANGED_USE);
    if(Eligible(c)){Guard lock(&audit);Discover(c);Slot* s=Find(c);return s&&s->published;}
    return originalUse?originalUse(c):false;
}
```

## HasHook — IrisRanged.cpp:158

```cpp
bool __fastcall HasHook(AI* ai,const hand& target,const Vector3& pos){
    // 078仅观察当前回调；普通角色原样转原生，没有新增能力/选招/开火资格。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_RANGED_HAS);
    // 079：只有实际拿着本锤枪才替代“当前装备弩”。收起/换持原生武器时转发原函数，
    // 使hasAnythingEquipped及工作前的空手要求得到真实结果；原参数和原函数调用次数保持。
    Character* c=ai?ai->me:0;if(Eligible(c)){const bool held=Held(c);
        Guard lock(&audit);Discover(c);Slot* s=Find(c);if(held)return s&&s->published;}
    return originalHas?originalHas(ai,target,pos):false;
}
```

## ScoreHook — IrisRanged.cpp:167

```cpp
float __fastcall ScoreHook(AI* ai,const hand& target,const Vector3& pos){
    // 078仅观察当前回调；普通角色原样转原生，没有新增能力/选招/开火资格。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_RANGED_SCORE);
    Character* c=ai?ai->me:0;if(Eligible(c)){
        bool ready=false;{Guard lock(&audit);Discover(c);Slot* s=Find(c);ready=s&&s->published;}
        if(!ready)return 0;
        // 对照原生scoreRangedAttack，仅补上本枪能力识别；保留近战压制0.1及队形完整1/0.5的评分。
        Character* other=target.getCharacter();if(other&&(!other->isValid()||other->isDestroyed()||other->isDead()||!c->isEnemy(other,false)))return 0;
        if(c->isLiterallyUnderMeleeAttackRightNowForSure())return .1f;
        Platoon* p=ai->getPlatoon();return p&&p->isIntact()?1.f:.5f;
    }return originalScore?originalScore(ai,target,pos):0;
}
```

## WithinHook — IrisRanged.cpp:179

```cpp
bool __fastcall WithinHook(AI* ai,const hand& target,const Vector3& pos){
    // 078仅观察当前回调；普通角色原样转原生，没有新增能力/选招/开火资格。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_RANGED_WITHIN);
    Character* c=ai?ai->me:0;float range=0;
    if(Eligible(c)){Guard lock(&audit);Slot* s=Find(c);if(s&&s->published)range=s->gun->maxRange;}
    if(range>0)return ai->isWithinGivenRange(target,pos,range);
    return originalWithin?originalWithin(ai,target,pos):false;
}
```

## GunHook — IrisRanged.cpp:187

```cpp
GunClass* __fastcall GunHook(RangedCombatClass* ranged){
    // 078仅观察当前回调；普通角色原样转原生，没有新增能力/选招/开火资格。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_RANGED_GUN);
    // 079：原生getGun也只认当前手持物。库存中的锤枪不能接管手里的真弩/炮台，
    // 更不能在已收武器进行工作时继续把私有Gun交给原生。槽的创建/销毁仍留在安全窗口。
    Character* c=ranged?ranged->me:0;if(Eligible(c)&&Held(c)){Guard lock(&audit);Discover(c);Slot* s=Find(c);return s&&s->published?s->gun:0;}
    return originalGun?originalGun(ranged):0;
}
```

## AnimationHook — IrisRanged.cpp:195

```cpp
void __fastcall AnimationHook(RangedCombatClass* ranged,float dt,const Vector3& aim,RootObject* target){
    // 078仅观察当前回调；普通角色原样转原生，没有新增能力/选招/开火资格。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_RANGED_ANIMATION);
    if(!ranged||!PrivateFast(ranged->gun)){if(originalAnimation)originalAnimation(ranged,dt,aim,target);return;}
    bool own=false;Character* c=ranged->me;const bool allowed=Eligible(c);
    {Guard lock(&audit);if(ranged&&Private(ranged->gun)){own=true;Slot* s=Find(ranged->gun);if(!s)c=0;
        // 原生弩的CB aim/reload动画不适用于本枪；保留它的完整状态机，只替换这一处动画适配。
        if(s){
            // 062恢复原适配的就绪条件。原生reAssessTargeting先于此回调，不能用上一安全帧的
            // aim.target相等或haveAim再否决新目标；真正发射仍刷新快照，原生视线/计时门不绕过。
            s->gun->ready=s->available&&s->published&&!s->busy&&!s->pending&&allowed;
            const bool sameTarget=target&&s->haveAim&&s->aim.target==target->handle;
            unsigned gate=(s->available?1:0)|(s->published?2:0)|(s->busy?4:0)|(s->pending?8:0)|(allowed?16:0)|(target?32:0)|(s->haveAim?64:0)|(sameTarget?128:0)|(s->gun->ready?256:0);
            if(gate!=s->lastAnimationGate){s->lastAnimationGate=gate;if(IrisDiagnostics::DetailsEnabled()){
                std::ostringstream out;out<<"ranged_animation_gate actor="<<s->actor.index<<":"<<s->actor.serial<<" ready="<<s->gun->ready<<" available="<<s->available<<" published="<<s->published<<" busy="<<s->busy<<" pending="<<s->pending<<" eligible="<<allowed<<" target_present="<<(target!=0)<<" aim_cached="<<s->haveAim<<" cached_target_matches="<<sameTarget<<" cache_match_required=0"<<" aim_timer="<<ranged->aimTimer;Iris::Log(out.str());}}
        }}}
    if(!own){if(originalAnimation)originalAnimation(ranged,dt,aim,target);return;}
    if(c&&target&&Iris::Finite(aim))c->lookatPosition(aim,true);
}
```

## ShotHook — IrisRanged.cpp:214

```cpp
void __fastcall ShotHook(GunClass* gun,Character* c,RootObject* target,StatsEnumerated stat,const Vector3& aim){
    // 078仅观察当前回调；普通角色原样转原生，没有新增能力/选招/开火资格。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_RANGED_SHOT);
    if(!PrivateFast(gun)){if(originalShot)originalShot(gun,c,target,stat,aim);return;}
    bool own=false;const bool allowed=Eligible(c);Character* victim=target?target->handle.getCharacter():0;
    const bool targetValid=victim&&victim->isValid()&&!victim->isDestroyed();
    {Guard lock(&audit);if(Private(gun)){own=true;Slot* s=Find(gun);
        if(s&&s->actor==c&&s->published&&!s->busy&&!s->pending&&allowed&&targetValid){
            // 一次原生射击许可对应一整套20发/3发/四脉冲动作；此回调不碰Ogre/健康，不生成额外弩箭。
            s->target=victim->handle;s->pending=true;s->busy=true;s->gun->ready=false;
            if(IrisDiagnostics::DetailsEnabled()){std::ostringstream o;o<<"ranged_action_requested actor="<<s->actor.index<<":"<<s->actor.serial<<" target="<<s->target.index<<":"<<s->target.serial<<" native_shot_suppressed=1";Iris::Log(o.str());}
        }}}
    // 故障/切换后的退役适配器也绝不落入原生shoot，防止双弹体和双伤害。真正原生枪全部原样转发。
    if(!own&&originalShot)originalShot(gun,c,target,stat,aim);
}
```

## ReloadHook — IrisRanged.cpp:229

```cpp
bool __fastcall ReloadHook(RangedCombatClass* ranged){
    // 078仅观察当前回调；普通角色原样转原生，没有新增能力/选招/开火资格。
    IrisDiagnostics::HookAudit audit(IrisDiagnostics::HOOK_RANGED_RELOAD);
    if(!ranged||!PrivateFast(ranged->gun))return originalReload?originalReload(ranged):false;
    bool own=false,before=false;
    {Guard lock(&audit);own=ranged&&Private(ranged->gun);if(own)before=ranged->_isReloading;}
    bool result=originalReload?originalReload(ranged):false;
    {Guard lock(&audit);if(own&&ranged&&Private(ranged->gun)){
        // 不用墙钟或自制冷却器；原生reloadCheck消耗同一游戏时间。完成后去掉它额外重设的0.4瞄准等待。
        if(before&&!ranged->_isReloading)ranged->aimTimer=0;
        if(before!=ranged->_isReloading&&IrisDiagnostics::DetailsEnabled()){std::ostringstream o;o<<"ranged_interval state="<<(ranged->_isReloading?"begin":"complete")<<" native_duration="<<ranged->reloadTimerMax<<" remaining="<<ranged->reloadTimer<<" ammo_type_null=1";Iris::Log(o.str());}
    }}return result;
}
```

## WoundHook — IrisNativeAudit.cpp:57

```cpp
static GameData* __fastcall WoundHook(MedicalSystem* self,bool low,CutDirection dir,Damages& damage,int& material,RootObject* attacker,AttackDirection::Enum& direction,Harpoon* harpoon){
    // 085来源只看现存TLS；新开关关闭时不读TLS/伤害字段，所有原参数/引用和返回值保持。
    IrisWoundAudit::Scope detail(IrisWoundAudit::Enabled()&&ReadTLS(hitTLS)!=0,damage);
    PartScope part(WOUND);return originalWound(self,low,dir,damage,material,attacker,direction,harpoon);
}
```

## EffectHook — IrisNativeAudit.cpp:62

```cpp
static void __fastcall EffectHook(GameData* data,const hand& who,const std::string& bone,const Ogre::Vector3& position,const Ogre::Quaternion& rotation){
    PartScope part(EFFECT);originalEffect(data,who,bone,position,rotation);
}
```

## ApplyHook — IrisWoundAudit.cpp:99

```cpp
static void __fastcall ApplyHook(MedicalSystem* self,MedicalSystem::HealthPartStatus* part,const Damages& damage,bool loading,bool sever,const Ogre::Vector3& force){Part timing(APPLY);originalApply(self,part,damage,loading,sever,force);}
```

## AppearanceHook — IrisWoundAudit.cpp:100

```cpp
static void __fastcall AppearanceHook(AppearanceBase* self,Wound* wound){Part timing(APPEARANCE);originalAppearance(self,wound);}
```

## LabelHook — IrisWoundAudit.cpp:101

```cpp
static ScreenLabel* __fastcall LabelHook(ForgottenGUI* self,const std::string& text,const MyGUI::Colour& color,ScreenLabel::LabelSize size,ScreenLabel::RisingSpeed speed){Part timing(LABEL);return originalLabel(self,text,color,size,speed);}
```

## BloodHook — IrisWoundAudit.cpp:102

```cpp
static void __fastcall BloodHook(MedicalSystem* self,const Damages& damage,CutDirection dir,AttackDirection::Enum from){Part timing(BLOOD);originalBlood(self,damage,dir,from);}
```

## AmputateHook — IrisWoundAudit.cpp:114

```cpp
static void __fastcall AmputateHook(MedicalSystem* self,RobotLimbs::Limb limb,bool create,const Ogre::Vector3& force){Part timing(AMPUTATE);originalAmputate(self,limb,create,force);}
```

## CreateHook — IrisWoundAudit.cpp:115

```cpp
static Item* __fastcall CreateHook(RootObjectFactory* self,GameData* data,const hand& identity,GameData* mesh,GameData* material,int level,Faction* faction){Part timing(ITEM_CREATE);return originalCreate(self,data,identity,mesh,material,level,faction);}
```

## SetupHook — IrisWoundAudit.cpp:116

```cpp
static void __fastcall SetupHook(SeveredLimbItem* self,Character* who,int limb,const Ogre::Vector3& force){Part timing(LIMB_SETUP);originalSetup(self,who,limb,force);}
```

## StateHook — IrisWoundAudit.cpp:117

```cpp
static void __fastcall StateHook(MedicalSystem* self){Part timing(UPDATE_STATE);originalState(self);}
```

## CollapseHook — IrisWoundAudit.cpp:118

```cpp
static void __fastcall CollapseHook(MedicalSystem* self,MedicalSystem::HealthPartStatus* part){Part timing(PART_COLLAPSE);originalCollapse(self,part);}
```

## RagdollHook — IrisWoundAudit.cpp:119

```cpp
static void __fastcall RagdollHook(Character* self,bool on,RagdollPart::Enum part){Part timing(RAGDOLL);originalRagdoll(self,on,part);}
```
