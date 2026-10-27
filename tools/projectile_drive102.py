"""102：只编辑既有序列化动画的时间字段/FCS射程；不编译、不转换骨架、不部署。"""
from pathlib import Path
import copy,json,struct
import kenshi_mod_writer as fcs

ROOT=Path(__file__).resolve().parents[1]
CONTRACT='IRIS_PROJECTILE_TIMELINE_102'
SOURCE_FIRE=3.1665399074554443
SOURCE_END=5.5
FIRE=SOURCE_FIRE/2
END=SOURCE_END-FIRE

def action_time(source):
    # 单位均为“倍率为1时的动作秒”；只压缩首次发射前，发射后差值严格保持。
    return source/2 if source<=SOURCE_FIRE else source-FIRE

def source_time(action):
    # 与C++ DriveEffectTime同一逆映射；原ion/准星/蓝火的美术曲线不重新采样。
    return action*2 if action<=FIRE else action+FIRE

def skeleton_times(blob):
    # 本项目Serializer_v1.80骨骼名称不计入bone chunk长度；严格走实际格式，拒绝未知数据。
    assert blob.startswith(b'\x00\x10[Serializer_v1.80]\n')
    p=blob.index(b'\n')+1;length_at=None;tracks=[]
    while p<len(blob):
        kind,size=struct.unpack_from('<HI',blob,p);assert size>=6
        if kind==0x2000:
            name_end=blob.index(b'\n',p+6);p+=size+name_end-(p+6)+1;continue
        assert p+size<=len(blob)
        if kind==0x4000:
            assert length_at is None
            name_end=blob.index(b'\n',p+6)
            assert blob[p+6:name_end]==b'IrisArsenal_drive'
            length_at=name_end+1;q=length_at+4
            while q<p+size:
                track_kind,track_size=struct.unpack_from('<HI',blob,q)
                assert track_kind==0x4100 and q+track_size<=p+size
                key=q+8;offsets=[]
                while key<q+track_size:
                    key_kind,key_size=struct.unpack_from('<HI',blob,key)
                    assert key_kind==0x4110 and key_size==38 and key+key_size<=q+track_size
                    offsets.append(key+6);key+=key_size
                assert key==q+track_size;tracks.append(offsets);q+=track_size
            assert q==p+size
        p+=size
    assert p==len(blob) and length_at is not None and len(tracks)==24
    return length_at,tracks

def retime_skeleton(blob):
    length_at,tracks=skeleton_times(blob);length=struct.unpack_from('<f',blob,length_at)[0]
    if abs(length-END)<1e-5:return blob
    assert abs(length-SOURCE_END)<1e-6
    out=bytearray(blob);struct.pack_into('<f',out,length_at,END)
    for offsets in tracks:
        times=[struct.unpack_from('<f',blob,k)[0] for k in offsets]
        assert len(times)==331 and times[0]==0 and abs(times[-1]-SOURCE_END)<1e-6
        assert all(a<b for a,b in zip(times,times[1:]))
        for k,t in zip(offsets,times):struct.pack_into('<f',out,k,action_time(t))
    # 不改任一旋转、位移、骨骼、绑定、名称和chunk尺寸；这不是动画重导出或编译。
    return bytes(out)

def records(blob):
    p=fcs.find_records_start(blob);out=[]
    while p<len(blob):
        r=fcs.read_record(blob,p,len(blob));assert r is not None
        out.append(r);p=r['end']
    assert p==len(blob);return out

def value(record,name):
    found=[(kind,raw) for section in record['sections'] for key,kind,raw in section if key==name]
    assert len(found)==1
    kind,raw=found[0];assert kind=='f32';return struct.unpack('<f',raw)[0]

def range_fcs(blob):
    rows=records(blob);out=bytearray(blob[:fcs.find_records_start(blob)]);found=0
    for r in rows:
        if r['key'] in ('15-IrisArsenal.mod','16-IrisArsenal.mod'):
            found+=1;assert value(r,'attack distance') in (5000,10000)
            # 原字段位置/文件头/工坊分类/引用/其它记录全部保留，不使用重建FCS的历史模板。
            r=copy.deepcopy(r)
            r['sections'][1]=[(name,kind,struct.pack('<f',5000) if name=='attack distance' else raw)
                              for name,kind,raw in r['sections'][1]]
        if r['key']=='17-IrisArsenal.mod':
            # 动画数据已分段变速，不能再把FCS总速率设2，否则射击段也会翻倍。
            assert value(r,'anim speed mult')==1
        out.extend(fcs.write_record(r))
    assert found==2;return bytes(out)

def retime_doc(doc):
    doc=copy.deepcopy(doc);moves=doc['moves'];assert len(moves)==10
    for i in (5,6):moves[i]['attack_max']=5000
    drive=moves[7];assert drive['key']=='drive'
    if drive.get('timing102',{}).get('contract')==CONTRACT:return doc
    assert drive['duration']==SOURCE_END and abs(drive['events'][0]['time']-SOURCE_FIRE)<1e-8
    drive['duration']=END
    for event in drive['events']:event['time']=action_time(event['time'])
    for event in drive['source_events']:
        # source_time仍保留原HKX身份；time表示当前重定向后的动作时间。
        event['time']=action_time(event['time'])
    drive['motion']=[[action_time(t),distance] for t,distance in drive['motion']]
    drive['timing102']={'contract':CONTRACT,'source_fire':SOURCE_FIRE,'source_end':SOURCE_END,
        'action_fire':FIRE,'action_end':END,'pre_fire_rate':2,'post_fire_rate':1,
        'FCS_anim_speed_mult':1,'effect_clock':'source_time(action_time)',
        'pose_keys':'original pose values; only serialized key times changed'}
    return doc

def retime_moves(text):
    lines=text.splitlines();out=[lines[0]];i=1
    for move in range(10):
        head=lines[i].split();count=int(head[4]);assert int(head[0])==move;i+=1
        old=float(head[3]);retime=move==7 and abs(old-SOURCE_END)<1e-6
        if move in (5,6):head[6]='5000.000000000'
        if move==7:
            assert retime or abs(old-END)<1e-6;head[3]='%.9f'%END
        out.append(' '.join(head))
        for _ in range(count):
            row=lines[i].split();i+=1
            if retime:row[0]='%.9f'%action_time(float(row[0]))
            out.append(' '.join(row))
    assert i==len(lines);return '\n'.join(out)+'\n'

def retime_cues(text):
    lines=text.splitlines();out=[lines[0]]
    for line in lines[1:]:
        row=line.split()
        if row[0]=='7':
            # 当前源唯一drive cue为首次点火；逐项识别新旧，重复执行不再次压缩。
            assert row[1]=='ignition'
            t=float(row[2]);assert min(abs(t-SOURCE_FIRE),abs(t-FIRE))<1e-8
            row[2]='%.9f'%FIRE
        out.append(' '.join(row))
    return '\n'.join(out)+'\n'

def prepare(root=ROOT,putter=None):
    root=Path(root);package=root/'package/IrisArsenal';assets=package/'assets'
    if putter is None:
        from safeio import put as putter
    def save(path,data,role,change):putter(path,data,role,change)
    for sex in ('male','female'):
        path=assets/('iris_action_drive_'+sex+'.skeleton')
        save(path,retime_skeleton(path.read_bytes()),'极致驱动既有动画数据',
             '只重排首次发射前时间键为二分之一，开火后等间隔平移；姿势和绑定字节保持')
    path=root/'docs/eight-moves.json'
    save(path,json.dumps(retime_doc(json.loads(path.read_text('utf-8-sig'))),ensure_ascii=False,indent=2),
         '动作/事件规格','源证据身份保持；极致驱动动作/四段伤害同步映射，两弹道最远5000')
    for name,fn in [('moves.csv',retime_moves),('effect_cues.csv',retime_cues)]:
        path=assets/name;save(path,fn(path.read_text('utf-8-sig')),'运行时动作/事件时序',
              '动作与四次独立伤害及点火使用同一分段映射，开火后0.25动作秒间隔保持')
    for path in [package/'IrisArsenal.mod',root/'distribution/IrisArsenal.base.mod']:
        save(path,range_fcs(path.read_bytes()),'FCS两招射程',
             '只改15/16两条attack distance为5000，drive整招anim speed mult仍为1；保留纯净本体/分类/引用')
    return validate(root)

def validate(root=ROOT):
    root=Path(root);package=root/'package/IrisArsenal';assets=package/'assets'
    doc=json.loads((root/'docs/eight-moves.json').read_text('utf-8-sig'));spec=doc['moves'][7]
    assert spec['timing102']['contract']==CONTRACT and abs(spec['duration']-END)<1e-8
    assert all(abs(e['time']-(FIRE+i*.25))<1e-8 for i,e in enumerate(spec['events']))
    lines=(assets/'moves.csv').read_text('utf-8-sig').splitlines();i=1
    for index,move in enumerate(doc['moves']):
        h=lines[i].split();i+=1;assert int(h[0])==index and abs(float(h[3])-move['duration'])<1e-8
        assert float(h[6])==move['attack_max']
        for event in move['events']:
            row=lines[i].split();i+=1;assert abs(float(row[0])-event['time'])<1e-8
    assert i==len(lines)
    for path in [package/'IrisArsenal.mod',root/'distribution/IrisArsenal.base.mod']:
        rows={r['key']:r for r in records(path.read_bytes())}
        for index in (15,16):assert value(rows[str(index)+'-IrisArsenal.mod'],'attack distance')==5000
        assert value(rows['17-IrisArsenal.mod'],'attack distance')==10000
        assert value(rows['17-IrisArsenal.mod'],'anim speed mult')==1
    shapes=[]
    for sex in ('male','female'):
        blob=(assets/('iris_action_drive_'+sex+'.skeleton')).read_bytes();length_at,tracks=skeleton_times(blob)
        assert abs(struct.unpack_from('<f',blob,length_at)[0]-END)<1e-5
        for track in tracks:
            ts=[struct.unpack_from('<f',blob,k)[0] for k in track]
            assert len(ts)==331 and ts[0]==0 and abs(ts[-1]-END)<1e-5
            assert all(a<b for a,b in zip(ts,ts[1:]))
        shapes.append({'sex':sex,'tracks':len(tracks),'keys_per_track':len(tracks[0])})
    cue=[r.split() for r in (assets/'effect_cues.csv').read_text('utf-8-sig').splitlines()[1:] if r.startswith('7 ')]
    assert len(cue)==1 and cue[0][1]=='ignition' and abs(float(cue[0][2])-FIRE)<1e-8
    return {'contract':CONTRACT,'first_shot':FIRE,'duration':END,'pulse_interval':.25,
            'FCS_anim_speed_mult':1,'projectile_ranges':[5000,5000],'drive_range':10000,
            'skeletons':shapes,'compiled':False,'game_tested':False}

if __name__=='__main__':
    # 显式运行才修改数据；stage_package只调用上面的只读validate。
    print(json.dumps(prepare(),ensure_ascii=False,indent=2))
