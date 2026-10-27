"""本地SSE105档案只读解压；不安装环境、不改游戏。"""
import struct,os,sys
from pathlib import Path
def lz4_block(data,expected):
    # SSE BSA105 使用裸 LZ4 块：严格检查输入边界、回溯距离和解压后长度，仅解码数据。
    out=bytearray();i=0
    def length(n):
        nonlocal i
        if n==15:
            while True:
                assert i<len(data);v=data[i];i+=1;n+=v
                if v!=255:break
        return n
    while i<len(data):
        token=data[i];i+=1;n=length(token>>4);assert i+n<=len(data)
        out.extend(data[i:i+n]);i+=n
        if i==len(data):break
        assert i+2<=len(data);offset=struct.unpack_from('<H',data,i)[0];i+=2
        assert 0<offset<=len(out);n=length(token&15)+4
        assert len(out)+n<=expected
        for _ in range(n):out.append(out[-offset])
    assert len(out)<=expected;return bytes(out)

def lz4_frame(data,expected):
    # Bethesda105 使用LZ4 frame；独立块沿用原解析，关联块交给固定版本的局部lz4依赖，避免丢失跨块字典。
    assert data[:4]==b'\x04\x22\x4d\x18'
    flags,bd=data[4:6];assert flags>>6==1 and not flags&1
    if not flags&32:
        # 仅作者工具导入，不进入游戏包或全局解释器；允许其他机器用环境变量指定同版本局部目录。
        local=Path(os.environ.get('IRIS_LZ4_PATH','D:/CodexWorkSpace/Tools/IrisArsenal-lz4'))
        if str(local) not in sys.path:sys.path.insert(0,str(local))
        import lz4,lz4.frame
        assert lz4.__version__=='4.4.5','请在工作区局部安装lz4==4.4.5'
        out=lz4.frame.decompress(data);assert len(out)==expected;return out
    i=6
    if flags&8:i+=8
    i+=1;out=bytearray()
    while True:
        assert i+4<=len(data);n=struct.unpack_from('<I',data,i)[0];i+=4
        if not n:break
        raw=bool(n&0x80000000);n&=0x7fffffff;assert i+n<=len(data)
        block=data[i:i+n];i+=n
        out.extend(block if raw else lz4_block(block,expected-len(out)))
        if flags&16:i+=4
        assert len(out)<=expected
    if flags&4:i+=4
    assert i==len(data) and len(out)==expected;return bytes(out)

def archive_file(path,wanted):
    # 只定位指定文件，不整包解压，也不写游戏目录；105 的 folder record 是24字节。
    wanted=wanted.replace('/','\\').lower()
    with path.open('rb') as f:
        magic,version,offset,flags,nfolders,nfiles,folderlen,filelen,types=struct.unpack('<4s8I',f.read(36))
        assert magic==b'BSA\0' and version==105 and flags&3==3
        f.seek(offset);folders=[struct.unpack('<QIIQ',f.read(24)) for _ in range(nfolders)]
        entries=[]
        for _,count,_,_ in folders:
            n=f.read(1)[0];folder=f.read(n).rstrip(b'\0').decode('utf8').lower()
            for _ in range(count):
                _,size,position=struct.unpack('<QII',f.read(16));entries.append((folder,size,position))
        assert len(entries)==nfiles
        filenames=f.read(filelen).split(b'\0');assert len(filenames)==nfiles+1
        for (folder,size,pos),filename in zip(entries,filenames):
            name=folder+'\\'+filename.decode('utf8').lower()
            if name!=wanted:continue
            compressed=bool(flags&4)^bool(size&0x40000000);size&=0x3fffffff;f.seek(pos);data=f.read(size);assert len(data)==size
            if flags&0x100:data=data[1+data[0]:]
            if compressed:expected=struct.unpack_from('<I',data)[0];data=lz4_frame(data[4:],expected)
            return data
    return None
