"""052仅清理精确退役白名单；不按mtime/文件名猜测删除源资产、骨架或历史证据。"""
import json,re
from safeio import ROOT,retire
def main():
    doc=json.loads((ROOT/'docs/retired-runtime-052.json').read_text('utf8'));package=ROOT/'package/IrisArsenal'
    references=set()
    for file in (package/'assets').glob('*.material'):references.update(re.findall(r'\btexture\s+(\S+)',file.read_text('utf8')))
    for name in doc['files']:
        assert name.startswith('assets/') and '..' not in name and '\\' not in name
        assert name.split('/')[-1] not in references,'退役资源仍被材质调用：'+name
        assert (package/name).name not in (package/'assets/effects.csv').read_text('utf8'),'退役模型仍在效果清单'
        retire(package/name,'052已确认的无消费者资源；禁止重新混入运行包')
if __name__=='__main__':main()
