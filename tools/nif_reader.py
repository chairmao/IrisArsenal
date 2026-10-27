"""Iris专用只读NIF参数解码：保留严格块边界，不携带其他项目的作者主程序。"""
from pathlib import Path
import struct,hashlib
SOURCE=Path("E:/skyrimspecialedition/mods/soulworker_Iris")
class Reader:
    # 所有长度都以当前块边界限制。未知块只记类型/大小，不猜测其字段含义。
    def __init__(self,data):self.data=data;self.pos=0
    def read(self,fmt):
        n=struct.calcsize('<'+fmt)
        if self.pos+n>len(self.data):raise ValueError('Truncated block')
        v=struct.unpack_from('<'+fmt,self.data,self.pos);self.pos+=n
        return v[0] if len(v)==1 else list(v)
    def string(self,fmt='I'):
        n=self.read(fmt)
        if n>65536 or self.pos+n>len(self.data):raise ValueError('Invalid string size')
        s=self.data[self.pos:self.pos+n].decode('utf8').rstrip('\0');self.pos+=n;return s
    def done(self):
        if self.pos!=len(self.data):raise ValueError('Unsupported trailing fields')

def parse(path):
    # 本轮Iris beam/charge3使用LE83；已消费的shader/float/sequence布局与100一致，其余块仍明确不解析。
    raw=path.read_bytes();end=raw.index(b'\n')+1;r=Reader(raw[end:])
    version=r.read('I');endian=r.read('B');user=r.read('I');count=r.read('I');bs=r.read('I')
    if (version,endian,user)!=(0x14020007,1,12) or bs not in (83,100):raise ValueError('Only known Iris LE83/SSE100 layouts supported')
    if count>10000:raise ValueError('Too many blocks')
    for _ in range(3):r.string('B')
    num=r.read('H');types=[r.string() for _ in range(num)]
    indices=[r.read('H') for _ in range(count)];sizes=[r.read('I') for _ in range(count)]
    ns=r.read('I');r.read('I')
    if ns>100000:raise ValueError('Too many strings')
    strings=[r.string() for _ in range(ns)]
    groups=r.read('I')
    for _ in range(groups):r.read('I')
    def name(i):
        if i==0xffffffff:return ''
        if i>=len(strings):raise ValueError('Bad string index')
        return strings[i]
    blocks=[];unknown={}
    for i,(ti,size) in enumerate(zip(indices,sizes)):
        if ti>=len(types) or size>len(r.data)-r.pos:raise ValueError('Block range')
        t=types[ti];q=Reader(r.data[r.pos:r.pos+size]);r.pos+=size
        item={'index':i,'type':t,'bytes':size}
        if t=='BSEffectShaderProperty':
            item['name']=name(q.read('I'));n=q.read('I')
            if n>10000:raise ValueError('Extra data overflow')
            item['extra_data']=[q.read('i') for _ in range(n)];item['controller']=q.read('i')
            item['shader_flags']=q.read('2I');item['uv_offset']=q.read('2f');item['uv_scale']=q.read('2f')
            item['source_texture']=q.string();item['clamp_and_lighting']=q.read('4B')
            item['falloff']=q.read('4f');item['base_color']=q.read('4f')
            item['base_color_scale']=q.read('f');item['soft_falloff_depth']=q.read('f');item['palette_texture']=q.string()
            q.done()
        elif t in ('BSEffectShaderPropertyFloatController','BSEffectShaderPropertyColorController','BSLightingShaderPropertyFloatController'):
            # 先读继承的NiTimeController/NiSingleInterpController，再读控制变量；
            # sequence持有实际插值器，不能把控制器中的blend插值器当原始关键帧。
            item['next']=q.read('i');item['flags']=q.read('H')
            item['frequency']=q.read('f');item['phase']=q.read('f')
            item['start']=q.read('f');item['stop']=q.read('f');item['target']=q.read('i')
            item['interpolator']=q.read('i');item['variable']=q.read('I');q.done()
        elif t=='NiControllerSequence':
            item['name']=name(q.read('I'));n=q.read('I');item['grow']=q.read('I')
            if n>10000:raise ValueError('Too many controlled blocks')
            item['controlled_blocks']=[]
            for _ in range(n):
                c={'interpolator':q.read('i'),'controller':q.read('i'),'priority':q.read('B')}
                for field in ['node','property','controller_type','controller_id','interpolator_id']:c[field]=name(q.read('I'))
                item['controlled_blocks'].append(c)
            item['weight']=q.read('f');item['text_keys']=q.read('i');item['cycle']=q.read('I')
            item['frequency']=q.read('f');item['start']=q.read('f');item['stop']=q.read('f')
            item['manager']=q.read('i');item['root']=name(q.read('I'));n=q.read('H')
            if n>10000:raise ValueError('Too many animation notes')
            item['notes']=[q.read('i') for _ in range(n)];q.done()
        elif t=='NiPoint3Interpolator':
            item['constant']=q.read('3f');item['data']=q.read('i');q.done()
        elif t in ('NiPSysMeshEmitter','BSPSysSimpleColorModifier'):
            item['name']=name(q.read('I'));item['order']=q.read('I');item['target']=q.read('i');item['active']=bool(q.read('B'))
            if t=='NiPSysMeshEmitter':
                for field in ['speed','speed_variation','declination','declination_variation','planar_angle','planar_angle_variation']:item[field]=q.read('f')
                item['initial_color']=q.read('4f')
                for field in ['initial_radius','radius_variation','life_span','life_span_variation']:item[field]=q.read('f')
                n=q.read('I')
                if n>10000:raise ValueError('Emitter mesh overflow')
                item['emitter_meshes']=[q.read('i') for _ in range(n)]
                item['velocity_type']=q.read('I');item['emission_type']=q.read('I');item['emission_axis']=q.read('3f')
            else:
                item['fade_in_percent']=q.read('f');item['fade_out_percent']=q.read('f')
                item['color_intervals']=q.read('4f');item['colors']=[q.read('4f') for _ in range(3)]
            q.done()
        elif t in ('NiFloatData','NiPosData','NiBoolData'):
            n=q.read('I');dim={'NiFloatData':1,'NiPosData':3,'NiBoolData':1}[t];itype=q.read('I') if n else 0
            if n>10000 or (n and itype not in (1,2,3,5)):raise ValueError('Unsupported key group')
            item['interpolation']=itype;item['keys']=[]
            for _ in range(n):
                key={'time':q.read('f'),'value':q.read('B' if t=='NiBoolData' else str(dim)+'f')}
                if itype==2:
                    key['forward']=q.read(str(dim)+'f');key['backward']=q.read(str(dim)+'f')
                if itype==3:key['tbc']=q.read('3f')
                item['keys'].append(key)
            q.done()
        elif t=='NiFloatInterpolator':
            item['constant']=q.read('f');item['data']=q.read('i');q.done()
        elif t=='BSShaderTextureSet':
            n=q.read('I')
            if n>32:raise ValueError('Texture array overflow')
            item['textures']=[q.string() for _ in range(n)];q.done()
        else:
            unknown[t]=unknown.get(t,0)+1
            continue
        blocks.append(item)
    # Footer仍由格式自带根节点表承载；块表已精确消费，不能称为全部NiAVObject/粒子行为解析。
    footer=len(r.data)-r.pos
    tex=sorted({x for item in blocks for x in ([item.get('source_texture',''),item.get('palette_texture','')]+item.get('textures',[])) if x})
    textures=[]
    for t in tex:
        file=SOURCE/t.replace('\\','/')
        textures.append({'reference':t,'exists':file.is_file(),'sha256':hashlib.sha256(file.read_bytes()).hexdigest() if file.is_file() else None})
    return {'file':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'version':[version,user,bs],'block_count':count,
            'parsed_blocks':blocks,'unparsed_types':unknown,'footer_bytes':footer,'textures':textures}
