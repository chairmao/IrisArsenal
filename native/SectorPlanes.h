#pragma once
#include <cmath>
#include <float.h>
#include <algorithm>

/* v100/CP936兼容：维持UTF-8无BOM及LF；中文注释用ASCII块注释闭合，避免多字节行尾吞掉下一行声明。 */
/* 097：这里只构造给NxScene::cullShapes的平面，不自行检测角色/盒子相交。 */
/* XZ为水平面，Y为高度；所有平面负半空间为内部。SDK允许多收，正式名单直接采用。 */
namespace IrisSector {
const double PI=3.14159265358979323846;
const unsigned MAX_PLANES=16; /* 实际最多13，始终小于SDK的32平面限制。 */
struct Plane {float x,y,z,d;};
struct Volume {unsigned count;Plane planes[MAX_PLANES];double first,last;float radius,bottom,top;};
inline bool Finite(double v){return v==v&&v>=-DBL_MAX&&v<=DBL_MAX;}

/* 每刀固定同一个水平圆心；front是已经查询到的角度，observed只用来解开atan2的±pi。 */
/* 慢扫只提交[旧front,新front]；回摆不重查旧区域，下一刀独立重置。 */
struct Progress {
    bool ready;int direction;double x,z,front,observed,unwrapped,extreme;
    Progress():ready(false),direction(0),x(0),z(0),front(0),observed(0),unwrapped(0),extreme(0){}
    void Reset(){ready=false;direction=0;}
    void Begin(double cx,double cz,double raw){ready=true;direction=0;x=cx;z=cz;front=observed=unwrapped=extreme=raw;}
    void Observe(double raw){
        const double delta=atan2(sin(raw-observed),cos(raw-observed));observed=raw;unwrapped+=delta;
        if(!direction&&fabs(delta)>1e-8)direction=delta>0?1:-1;
        /* 同一次安全更新内先扫到极值再回摆，也要覆盖已经发生的前进角度。 */
        extreme=direction>0?std::max(extreme,unwrapped):direction<0?std::min(extreme,unwrapped):front;
    }
    double Next()const{return direction>0?std::max(front,extreme):direction<0?std::min(front,extreme):front;}
};

inline void Add(Volume& v,float x,float y,float z,double d){
    Plane& p=v.planes[v.count++];p.x=x;p.y=y;p.z=z;p.d=float(d);
}
inline void Side(Volume& v,double cx,double cz,double angle,float sign){
    /* 先舍入法线再计算常数；同一边界的两侧仅取反，不能每片向角度外侧加厚而重复查询。 */
    const float x=float(sin(angle)),z=float(-cos(angle));
    const float d=float(-(double(x)*cx+double(z)*cz));Add(v,sign*x,0,sign*z,sign*d);
}
inline unsigned Parts(double first,double last){return std::max(1U,unsigned(ceil(fabs(last-first)/(PI*.5))));}
inline bool Build(double cx,double cz,double first,double last,double radius,double bottom,double top,Volume& v){
    v.count=0;
    if(!Finite(cx)||!Finite(cz)||!Finite(first)||!Finite(last)||!Finite(radius)||!Finite(bottom)||!Finite(top)||
       radius<=0||bottom>top||fabs(last-first)>PI*.5+1e-12)return false;
    /* 高度方向留有限float向外余量，避免top/bottom舍入把切触的趴地形体排除；不扩角边界。 */
    const double heightPad=std::max(1.0,std::max(fabs(bottom),fabs(top)))*(8*FLT_EPSILON);
    bottom-=heightPad;top+=heightPad;
    v.first=first;v.last=last;v.radius=float(radius);v.bottom=float(bottom);v.top=float(top);
    const double lo=std::min(first,last),hi=std::max(first,last),middle=(lo+hi)*.5;
    Side(v,cx,cz,lo,1);Side(v,cx,cz,hi,-1);
    /* 零角度退化为有限径向线，背面平面防止退化查询延伸到圆心后方。 */
    const float bx=float(-cos(middle)),bz=float(-sin(middle));
    Add(v,bx,0,bz,-(double(bx)*cx+double(bz)*cz));
    Add(v,0,-1,0,bottom);Add(v,0,1,0,-top);
    /* 圆弧用间距<=15度的切平面外接；不使用内接弦，避免在两条采样射线之间挖空。 */
    /* 只给圆弧方向留浮点向外余量，角边界不扩张；相邻角片的侧平面严格共用并取反。 */
    const unsigned arcs=std::max(1U,unsigned(ceil((hi-lo)/(PI/12))));
    const double scale=std::max(1.0,std::max(radius,std::max(fabs(cx),fabs(cz))));
    for(unsigned i=0;i<=arcs;++i){const double a=lo+(hi-lo)*double(i)/arcs;
        const float x=float(cos(a)),z=float(sin(a));
        const double support=radius*sqrt(double(x)*x+double(z)*z)+scale*(8*FLT_EPSILON);
        Add(v,x,0,z,-(double(x)*cx+double(z)*cz+support));
    }
    if(v.count>MAX_PLANES)return false;
    for(unsigned i=0;i<v.count;++i)if(!Finite(v.planes[i].x)||!Finite(v.planes[i].y)||!Finite(v.planes[i].z)||!Finite(v.planes[i].d))return false;
    return true;
}
}
