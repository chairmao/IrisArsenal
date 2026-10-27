"""048复现实际故障：完整FCS作者重复运行必须保持047已验收字节，不放宽摘要门。"""
import copy,hashlib,json,tempfile
from pathlib import Path
from safeio import ROOT
import author_moves as author
from historical047 import assert_047_hash

def verify_icon_rebuild048():
    moves=json.loads((ROOT/'docs/eight-moves.json').read_text('utf8'))['moves']
    expected=json.loads((ROOT/'docs/authorized-delta-047.json').read_text('utf8'))['package:IrisArsenal.mod']['after']
    saved_out,saved_put=author.OUT,author.put
    # 真正调用生产者和FCS往返，只替换写入位置为一次性测试目录，避免测试修改项目或真实游戏。
    with tempfile.TemporaryDirectory(prefix='IrisFCS048-',dir='D:/CodexWorkSpace') as tmp:
        out=Path(tmp);target=out/'IrisArsenal.mod';target.write_bytes((ROOT/'package/IrisArsenal/IrisArsenal.mod').read_bytes())
        author.OUT=out
        author.put=lambda path,data,*args:Path(path).write_bytes(data)
        try:
            author.fcs_assets(copy.deepcopy(moves));first=target.read_bytes()
            author.fcs_assets(copy.deepcopy(moves));second=target.read_bytes()
        finally:author.OUT=saved_out;author.put=saved_put
    assert first==second
    # 053只允许五项明确授权的武器数值变化；完整重建仍需字节稳定并命中精确摘要链。
    assert_047_hash('package:IrisArsenal.mod',hashlib.sha256(first).hexdigest(),expected)
    # 保护本次修复：相机写在伤害/描述等既有字段之后，不能再重排同值字段而触发严格门。
    text=(ROOT/'tools/author_moves.py').read_text('utf8');body=text[text.index('def fcs_assets('):text.index('def main(')]
    assert body.index('icon_camera.apply(weapon,field)')>body.index("field(weapon,'description'")
    return {'real_FCS_producer_runs':2,'byte_identical':True,'exact_047_to_053_digest_chain':True,'roundtrip_executed':True,'game_files_written':False}
if __name__=='__main__':print(json.dumps(verify_icon_rebuild048(),ensure_ascii=False,indent=2))
