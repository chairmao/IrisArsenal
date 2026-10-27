"""来自已核对的JCE/Ephnel具名骨架与纯值数学；不含项目写入或运行时挂钩。"""
import math,struct
def qmul(a,b):
    w,x,y,z=a;v,r,s,t=b
    return (w*v-x*r-y*s-z*t,w*r+x*v+y*t-z*s,w*s-x*t+y*v+z*r,w*t+x*s-y*r+z*v)

def qi(q):return (q[0],-q[1],-q[2],-q[3])

def qnorm(q):
    n=math.sqrt(sum(x*x for x in q));return tuple(x/n for x in q)

def vadd(a,b):return tuple(x+y for x,y in zip(a,b))

def vsub(a,b):return tuple(x-y for x,y in zip(a,b))

def vmul(a,k):return tuple(x*k for x in a)

def dot(a,b):return sum(x*y for x,y in zip(a,b))

def cross(a,b):return(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])

def unit(v):return vmul(v,1/math.sqrt(dot(v,v)))

def rotate(q,v):return qmul(qmul(q,(0,*v)),qi(q))[1:]

def axis(v,angle):
    v=unit(v);a=math.radians(angle)/2;return(math.cos(a),*(x*math.sin(a) for x in v))

def lerp(a,b,u):return tuple(x+(y-x)*u for x,y in zip(a,b))

def smooth(u):return max(0,min(1,u))**2*(3-2*max(0,min(1,u)))

def skeleton(path):
    # Kenshi Serializer_v1.80 的骨骼 chunk 长度不计骨骼名称；不能普通按 length 跳过。
    b=path.read_bytes();i=b.index(b"\n")+1;bones=[];parents={}
    assert b[:2]==b"\x00\x10" and b"Serializer_v1.80" in b[:24]
    while i+6<=len(b):
        t,n=struct.unpack_from("<HI",b,i)
        if t==0x2000:
            e=b.index(b"\n",i+6);h=struct.unpack_from("<H",b,e+1)[0]
            p=struct.unpack_from("<3f",b,e+3);x,y,z,w=struct.unpack_from("<4f",b,e+15)
            bones.append({"id":h,"name":b[i+6:e].decode(),"position":p,"orientation":qnorm((w,x,y,z))})
            i+=n+e-(i+6)+1
        elif t==0x3000:
            c,p=struct.unpack_from("<HH",b,i+6);parents[c]=p;i+=n
        elif t==0x1010:i+=n
        else:break
    for bone in bones:bone["parent"]=parents.get(bone["id"],-1)
    assert [x["id"] for x in bones]==list(range(len(bones)))
    return bones

def world(bones,local):
    result=[]
    for b,q in zip(bones,local):
        p=b["position"];parent=b["parent"]
        if parent>=0:
            pp,pq=result[parent];result.append((vadd(pp,rotate(pq,p)),qmul(pq,q)))
        else:result.append((p,q))
    return result


def from_to(a,b):
    a=unit(a);b=unit(b);d=dot(a,b)
    if d < -.99999:
        return axis(cross(a,(1,0,0) if abs(a[0])<.8 else (0,1,0)),180)
    return qnorm((1+d,*cross(a,b)))
