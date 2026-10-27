"""052沙盒事务和真实离线解析器测试；无编译/游戏/轮询。"""
from pathlib import Path
import json,tempfile,unittest
from unittest.mock import patch
import test_update_mod as original
import read_audit052 as reader
from safeio import ROOT
TASK=original.TASK # 本轮测试产物留在当前任务目录，不混入052历史任务。
class CleanupTests(unittest.TestCase):
    def setUp(self):
        original.TASK=TASK;self.case=original.UpdateTests('test_fresh_install_and_hashes');self.case.setUp();self.case.before()
        self.retired=json.loads((ROOT/'docs/retired-runtime-052.json').read_text('utf8'))['files'];self.case.man['retired_files']=self.retired
        (self.case.pkg/'IrisPackage.json').write_text(json.dumps(self.case.man),encoding='utf8')
        for name in self.retired:
            p=self.case.target/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'old-retired-'+name.encode())
    def test_clean_replace_retires_all_old_files(self):
        unknown=self.case.target/'assets/unknown-user.png';unknown.write_bytes(b'keep')
        log=self.case.target/'logs/user.log';log.parent.mkdir();log.write_bytes(b'keep log')
        old=self.case.inventory();result=self.case.deploy()
        for name in self.retired:
            self.assertFalse((self.case.target/name).exists())
            for root in result['backup_roots']:
                copies=list(Path(root).rglob(Path(name).name));self.assertEqual(len(copies),1);self.assertEqual(copies[0].read_bytes(),old[name])
        self.assertFalse(unknown.exists());self.assertFalse(log.exists());self.assertEqual(original.u.tree_state(self.case.target),original.u.tree_state(self.case.pkg))
    def test_retirement_rollback(self):
        old=self.case.inventory()
        def fail(i,row):
            if row['name']=='IrisPackage.json':raise OSError('after exact retirements')
        with self.assertRaises(RuntimeError):self.case.deploy(inject=fail)
        self.assertEqual(self.case.inventory(),old)
    def test_retirement_metadata_not_used_as_delete_paths(self):
        # 全量替换不执行旧退役路径白名单；恶意元数据也不能指向目录外删除。
        outside=self.case.root/'outside.log';outside.write_bytes(b'untouched')
        self.case.man['retired_files']=['../../outside.log'];(self.case.pkg/'IrisPackage.json').write_text(json.dumps(self.case.man),encoding='utf8')
        self.case.deploy();self.assertEqual(outside.read_bytes(),b'untouched')
    def test_logging_comes_from_complete_package(self):
        ini=self.case.target/'IrisArsenal.ini';ini.write_bytes(b'[IrisArsenal]\r\nEnableLogging=0\r\nEnableResourceLogging=0\r\n')
        # 新要求明确覆盖配置，旧关闭日志的设置仅留在备份，不能继续合并。
        self.case.deploy();self.assertEqual(ini.read_bytes(),self.case.data['IrisArsenal.ini'])
    def test_prune_rejects_referenced_model(self):
        import prune_package052 as prune
        root=self.case.root/'referenced-project';(root/'docs').mkdir(parents=True);assets=root/'package/IrisArsenal/assets';assets.mkdir(parents=True)
        (root/'docs/retired-runtime-052.json').write_text(json.dumps({'files':['assets/iris_fx_heavy.mesh']}),encoding='utf8')
        (assets/'effects.csv').write_text('IRIS_FX 4 1\nheavy iris_fx_heavy.mesh 2\n',encoding='utf8')
        with patch.object(prune,'ROOT',root),patch.object(prune,'retire') as retire:
            with self.assertRaisesRegex(AssertionError,'仍在效果清单'):prune.main()
            retire.assert_not_called()
class ReaderTests(unittest.TestCase):
    def parse(self,text):
        with tempfile.TemporaryDirectory(dir=TASK) as temp:
            path=Path(temp)/'synthetic.log';path.write_text(text,encoding='utf8');return reader.read_log(path)
    def summary(self,identifier=1):
        return ''.join('audit_counters id=%d scope=%s frame=9 safe_frames=9\naudit_resources id=%d scope=%s frame=9 actors=1 active=0 projectiles=0 residues=0 idle_visuals=3 attached_visuals=2 jobs=0 pending_damage=0\n'%(identifier,scope,identifier,scope) for scope in ('window','process'))+'audit_timing id=%d scope=process channel=safe_tick calls=9\naudit_summary_end id=%d frame=9 timing_lines=1 scopes=2\n'%(identifier,identifier)
    def test_complete_and_partial(self):
        text='audit_run_identity pid=22 creation_filetime=111 executable=D:/A Game/kenshi.exe game_version=1.0.65\n'+self.summary()+'audit_counters id=2 scope=process frame=10\n'
        value=self.parse(text);self.assertEqual(value['complete_summaries'],1);self.assertEqual(value['incomplete_summaries'],1);self.assertEqual(value['latest_complete']['end']['id'],'1');self.assertEqual(value['identity']['executable'],'D:/A Game/kenshi.exe')
    def test_incomplete_even_with_footer(self):
        value=self.parse(self.summary().replace('timing_lines=1','timing_lines=2'));self.assertIsNone(value['latest_complete']);self.assertEqual(value['incomplete_summaries'],1)
    def test_resource_stage_failure(self):
        value=self.parse('resource_begin channel=material_load name=one\nresource_end channel=material_load name=one failed=1\nresource_begin channel=visual_create name=two\n');self.assertEqual(len(value['warnings']),1);self.assertEqual(value['incomplete_resource_stages'][0]['name'],'two')
    def test_cumulative_not_summed(self):
        value=self.parse(self.summary(1)+self.summary(2));self.assertEqual(value['complete_summaries'],2);self.assertEqual(value['latest_complete']['counters']['process']['safe_frames'],'9')
if __name__=='__main__':unittest.main(verbosity=2)
