#pragma once
// 精确兼容模式：有限平端圆柱与真实PhysX凸碰撞体的只读窄相位。094保守模式明确绕过本文件，使用包围体候选。
// PhysX 2.8无圆柱查询：原生OBB给候选，支持函数读取原生球/胶囊/盒/凸网格；GJK只计算这些形体。
// 坐标以柱体中心为原点使用double，避免大世界坐标差损失；迭代上限失败返回UNRESOLVED，禁止猜成HIT。
#include <cmath>
#include <vector>
namespace IrisCylinder {
struct V {double x,y,z;V(double a=0,double b=0,double c=0):x(a),y(b),z(c){} V operator+(const V& b)const{return V(x+b.x,y+b.y,z+b.z);}V operator-(const V& b)const{return V(x-b.x,y-b.y,z-b.z);}V operator-()const{return V(-x,-y,-z);}V operator*(double s)const{return V(x*s,y*s,z*s);}double dot(const V& b)const{return x*b.x+y*b.y+z*b.z;}V cross(const V& b)const{return V(y*b.z-z*b.y,z*b.x-x*b.z,x*b.y-y*b.x);}double norm2()const{return dot(*this);}};
struct Body {std::vector<V> points;double rounding;Body():rounding(0){points.reserve(8);}V Support(const V& d)const{V p=points[0];for(size_t i=1;i<points.size();++i)if(points[i].dot(d)>p.dot(d))p=points[i];double n=sqrt(d.norm2());return n>1e-15?p+d*(rounding/n):p;}};
struct Cylinder {V axis;double half,radius;V Support(const V& d)const{double h=d.dot(axis);V radial=d-axis*h;double n=sqrt(radial.norm2());return axis*(h>=0?half:-half)+(n>1e-15?radial*(radius/n):V());}};
enum Result {MISS,HIT,UNRESOLVED};
inline V Triple(const V& a,const V& b,const V& c){return a.cross(b).cross(c);}
inline bool Line(V* s,unsigned& n,V& d){V a=s[n-1],b=s[n-2],ab=b-a,ao=-a;if(ab.dot(ao)>0){s[0]=b;s[1]=a;n=2;d=Triple(ab,ao,ab);}else{s[0]=a;n=1;d=ao;}return d.norm2()<1e-14;}
inline bool Triangle(V* s,unsigned& n,V& d){
    V a=s[2],b=s[1],c=s[0],ab=b-a,ac=c-a,ao=-a,abc=ab.cross(ac);
    if(abc.cross(ac).dot(ao)>0){if(ac.dot(ao)>0){s[0]=c;s[1]=a;n=2;d=Triple(ac,ao,ac);return d.norm2()<1e-14;}s[0]=b;s[1]=a;n=2;return Line(s,n,d);}
    if(ab.cross(abc).dot(ao)>0){s[0]=b;s[1]=a;n=2;return Line(s,n,d);}
    if(abc.dot(ao)>0)d=abc;else{s[0]=b;s[1]=c;s[2]=a;d=-abc;}return d.norm2()<1e-14;
}
inline bool Tetra(V* s,unsigned& n,V& d){
    V a=s[3],b=s[2],c=s[1],e=s[0],ao=-a;V faces[3][3]={{b,c,e},{c,e,b},{e,b,c}};
    for(unsigned i=0;i<3;++i){V u=faces[i][0],v=faces[i][1],opposite=faces[i][2],normal=(u-a).cross(v-a);if(normal.dot(opposite-a)>0)normal=-normal;
        if(normal.dot(ao)>0){s[0]=v;s[1]=u;s[2]=a;n=3;return Triangle(s,n,d);}}
    return true;
}
inline Result Overlap(const Cylinder& cylinder,const Body& body){
    if(body.points.empty()||cylinder.half<=0||cylinder.radius<=0)return UNRESOLVED;
    // 球与平端圆柱有精确距离式，优先走解析分支，避免曲面GJK在擦边时反复迭代。
    if(body.points.size()==1){V p=body.points[0];double h=p.dot(cylinder.axis),z=fabs(h)-cylinder.half;
        if(z<0)z=0;double r=sqrt((p-cylinder.axis*h).norm2())-cylinder.radius;if(r<0)r=0;
        return z*z+r*r<=body.rounding*body.rounding?HIT:MISS;}
    V d(1,.37,.19),s[4];unsigned n=1;s[0]=cylinder.Support(d)-body.Support(-d);d=-s[0];
    for(unsigned i=0;i<64;++i){if(d.norm2()<1e-14)return HIT;V a=cylinder.Support(d)-body.Support(-d);
        if(a.dot(d)<-1e-8*sqrt(d.norm2()))return MISS;
        bool repeated=false;for(unsigned j=0;j<n;++j)if((a-s[j]).norm2()<1e-20)repeated=true;
        if(repeated)return UNRESOLVED;s[n++]=a;
        if(n==2){if(Line(s,n,d))return HIT;}else if(n==3){if(Triangle(s,n,d))return HIT;}else if(Tetra(s,n,d))return HIT;
    }return UNRESOLVED;
}
}
