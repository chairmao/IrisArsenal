"""在隔离mods目录验证全量清空/双备份/恢复，不编译、不写实际游戏目录。"""
from pathlib import Path
import json,os,tempfile,unittest
from unittest.mock import patch
import update_mod as u
from stage_package import HOLDER_TIMELINE_CONTRACT,INTERFACE_PROBE_CONTRACT,WORK_TRACE_CONTRACT,SPATIAL_PROJECTILES_CONTRACT,RANGED_WORK_CONTRACT,QUERY_BATCH_CONTRACT,CONTACT_WORK_CONTRACT,MEDICAL_BRANCH_CONTRACT,SWEEP_INDEX_CONTRACT,WOUND_PROFILE_CONTRACT,NATIVE_PROFILE_CONTRACT,validate_dll,BUILD_CONTRACT,MELEE_CONTRACT,ACTOR_CONTRACT,HOOK_CONTRACT,TERRAIN_CONTRACT,AUDIT_HOOK_CONTRACT,EQUIPMENT_CONTRACT,PERFORMANCE_CONTRACT,MEDICAL_GATE_CONTRACT
from safeio import ROOT
TASK=Path(os.environ.get('IRIS_UPDATE_TEST_ROOT','D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-Iris-CleanUpdate-20261019-221148-ff950c'))
TASK.mkdir(parents=True,exist_ok=True)

class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='test-',dir=TASK));self.pkg=self.root/'package'
        self.target=self.root/'mods/IrisArsenal';self.pkg.mkdir()
        # 完整原路径保存在备份中；测试目录用Windows扩展路径，避免传统260字符限制。
        self.bases=tuple(Path('\\\\?\\'+str(self.root/name)) for name in ('backupD','backupE'))
        self.data={'IrisArsenal.dll':b'dll-current','IrisArsenal.mod':b'fcs-current',
                   'IrisArsenal.ini':(ROOT/'distribution/IrisArsenal.ini').read_bytes(),
                   'RE_Kenshi.json':b'{"Plugins":["IrisArsenal.dll"]}',
                   '_IrisArsenal.info':b'<id>0</id>','assets/effect.csv':b'new-event'}
        self.manifest()
    def manifest(self):
        for name,data in self.data.items():
            p=self.pkg/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        self.man={'ready':True,'version':'0.3.6','contract':'IRIS_EIGHT_036','files':{name:u.digest(data) for name,data in self.data.items()}}
        (self.pkg/'IrisPackage.json').write_text(json.dumps(self.man),encoding='utf-8')
    def deploy(self,**kwargs):
        return u.deploy_package(self.pkg,self.target,self.bases,guard=lambda:None,audit_root=self.root/'audits',**kwargs)
    def before(self):
        self.target.mkdir(parents=True,exist_ok=True)
        for name in self.data:
            p=self.target/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'old-'+name.encode())
        (self.target/'IrisArsenal.ini').write_bytes(b'[IrisArsenal]\r\nEnabled=0\r\n')
        return self.inventory()
    def inventory(self):
        return {p.relative_to(self.target).as_posix():p.read_bytes() for p in self.target.rglob('*') if p.is_file()}
    def test_fresh_install_and_hashes(self):
        result=self.deploy();self.assertTrue(result['success']);self.assertEqual(result['files_verified'],7)
        self.assertFalse(result['compiled_by_script']);self.assertEqual(u.tree_state(self.target),u.tree_state(self.pkg))
    def test_complete_replace_backs_up_unknown_and_config(self):
        self.before();extra=self.target/'logs/user.log';extra.parent.mkdir();extra.write_bytes(b'old log')
        unknown=self.target/'old-user.bin';unknown.write_bytes(b'unknown');(self.target/'old-empty').mkdir()
        old=u.tree_state(self.target);result=self.deploy()
        self.assertEqual(u.tree_state(self.target),u.tree_state(self.pkg));self.assertFalse(extra.exists());self.assertFalse(unknown.exists())
        self.assertEqual((self.target/'IrisArsenal.ini').read_bytes(),self.data['IrisArsenal.ini'])
        self.assertEqual((self.target/'_IrisArsenal.info').read_bytes(),self.data['_IrisArsenal.info'])
        self.assertEqual(result['old_files_removed'],2)
        for base in self.bases:
            snapshots=list(base.glob('*/'+self.target.drive.rstrip(':')+'/'+('/'.join(self.target.parts[1:]))))
            self.assertEqual(len(snapshots),1);self.assertEqual(u.tree_state(snapshots[0]),old)
    def test_all_package_components_including_credits_are_copied(self):
        # 不再依赖手写文件白名单；新署名、图标或子目录在清单中均完整复制。
        for name in ('CREDITS-drive059.txt','CREDITS-new.txt','icons/new.png','new-components/data.bin'):self.data[name]=name.encode()
        self.manifest();self.deploy();self.assertEqual(u.tree_state(self.target),u.tree_state(self.pkg))
    def test_missing_installed_assets_are_repaired(self):
        self.target.mkdir(parents=True);(self.target/'IrisArsenal.dll').write_bytes(b'old DLL')
        self.deploy();self.assertEqual(u.tree_state(self.target),u.tree_state(self.pkg))
    def test_empty_existing_directory(self):
        self.target.mkdir(parents=True);self.deploy();self.assertEqual(u.tree_state(self.target),u.tree_state(self.pkg))
    def test_package_is_not_consumed(self):
        before=u.tree_state(self.pkg);self.deploy();self.assertEqual(before,u.tree_state(self.pkg))
    def test_repeat_update_is_identical(self):
        self.deploy();before=u.tree_state(self.target);self.deploy();self.assertEqual(before,u.tree_state(self.target))
    def test_package_ini_bytes_are_preserved_in_all_encodings(self):
        # 全量复制不解码/改写配置：BOM、中文与换行都必须逐字节保持。
        for enc,bom in [('utf-8',b''),('utf-8',b'\xef\xbb\xbf'),('gb18030',b''),('utf-16-le',b'\xff\xfe'),('utf-16-be',b'\xfe\xff')]:
            raw=bom+'; 中文配置\r\n[IrisArsenal]\r\nEnabled=1\r\n'.encode(enc)
            self.data['IrisArsenal.ini']=raw;self.manifest();self.deploy();self.assertEqual((self.target/'IrisArsenal.ini').read_bytes(),raw)
    def test_partial_copy_restores_entire_old_directory(self):
        self.before();(self.target/'logs').mkdir();(self.target/'logs/unknown.log').write_bytes(b'keep in rollback');(self.target/'empty').mkdir()
        old=u.tree_state(self.target)
        def fail(i,row):
            if i==3:raise OSError('模拟第四次写入失败')
        with self.assertRaisesRegex(RuntimeError,r'恢复错误：\[\]'):self.deploy(inject=fail)
        self.assertEqual(u.tree_state(self.target),old)
    def test_failed_fresh_install_restores_absence(self):
        def fail(i,row):raise OSError('模拟首次写入失败')
        with self.assertRaisesRegex(RuntimeError,'更新失败'):self.deploy(inject=fail)
        self.assertFalse(self.target.exists())
    def test_backup_failure_never_clears_target(self):
        self.before();old=u.tree_state(self.target);bad=self.root/'bad-backup';bad.write_bytes(b'file')
        with self.assertRaises(OSError):u.deploy_package(self.pkg,self.target,(self.bases[0],bad),guard=lambda:None,audit_root=self.root/'audits')
        self.assertEqual(u.tree_state(self.target),old)
    def test_second_guard_failure_keeps_target(self):
        self.before();old=u.tree_state(self.target);calls=[]
        def guard():
            calls.append(1)
            if len(calls)>1:raise RuntimeError('游戏刚启动')
        with self.assertRaisesRegex(RuntimeError,'游戏刚启动'):u.deploy_package(self.pkg,self.target,self.bases,guard=guard,audit_root=self.root/'audits')
        self.assertEqual(u.tree_state(self.target),old)
    def test_bad_hash_writes_nothing(self):
        (self.pkg/'IrisArsenal.dll').write_bytes(b'changed')
        with self.assertRaisesRegex(RuntimeError,'哈希'):self.deploy()
        self.assertFalse(self.target.exists())
    def test_unlisted_package_file_rejected_before_clear(self):
        self.before();old=u.tree_state(self.target);(self.pkg/'unlisted').write_bytes(b'new')
        with self.assertRaisesRegex(RuntimeError,'与清单不一致'):self.deploy()
        self.assertEqual(u.tree_state(self.target),old)
    def test_path_escape_writes_nothing(self):
        self.man['files']['assets/../../escape']=u.digest(b'x');(self.pkg/'IrisPackage.json').write_text(json.dumps(self.man),encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError,'非法清单路径'):self.deploy()
        self.assertFalse(self.target.exists())
    def test_case_collision_rejected(self):
        self.man['files']['IRISARSENAL.dll']=u.digest(b'x');(self.pkg/'IrisPackage.json').write_text(json.dumps(self.man),encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError,'路径重复'):self.deploy()
        self.assertFalse(self.target.exists())
    def test_wrong_target_and_overlap_rejected(self):
        for target in (self.root/'mods/OtherMod',self.pkg/'mods/IrisArsenal'):
            with self.assertRaises(RuntimeError):u.deploy_package(self.pkg,target,self.bases,guard=lambda:None)
        self.assertFalse(self.target.exists())
    def test_package_empty_directories_are_copied(self):
        (self.pkg/'assets/empty').mkdir();self.deploy();self.assertEqual(u.tree_state(self.target),u.tree_state(self.pkg))
    def test_running_game_and_process_query_failure(self):
        import subprocess
        with patch.object(u.subprocess,'run',return_value=subprocess.CompletedProcess([],0,b'[{"ProcessId":9}]',b'')):
            with self.assertRaisesRegex(RuntimeError,'仍在运行'):u.game_stopped()
        with patch.object(u.subprocess,'run',return_value=subprocess.CompletedProcess([],1,b'',b'CIM error')):
            with self.assertRaisesRegex(RuntimeError,'无法查询'):u.game_stopped()
    def test_link_inside_old_target_never_clears_outside(self):
        self.before();outside=self.root/'outside';outside.mkdir();(outside/'keep.txt').write_bytes(b'keep')
        link=self.target/'assets/link'
        try:os.symlink(outside,link,target_is_directory=True)
        except OSError as error:self.skipTest('系统未允许创建测试符号链接：'+str(error))
        with self.assertRaisesRegex(RuntimeError,'重解析点|符号链接'):self.deploy()
        self.assertEqual((outside/'keep.txt').read_bytes(),b'keep');self.assertTrue(link.is_symlink())
    def test_actual_user_dll_safely_classified(self):
        # 072源码可能先于用户DLL；真实旧产物必须被明确拒绝，不能要求它冒充新合同。
        # 后续用户编译后仍验证正常路径，不伪造PE/合同或调用编译器。
        existing=(ROOT.parent/'bin/Release/IrisArsenal.dll').read_bytes()
        # 104优先验证当前合同门；不通过伪造新DLL或放宽实际部署校验来满足测试。
        if HOLDER_TIMELINE_CONTRACT.encode('ascii') not in existing:
            with self.assertRaisesRegex(RuntimeError,'104正式人数无限制与片尾审计'):validate_dll()
        elif MELEE_CONTRACT.encode('ascii') not in existing:
            with self.assertRaisesRegex(RuntimeError,'072原生近战资格与回退'):validate_dll()
        elif ACTOR_CONTRACT.encode('ascii') not in existing:
            # 075现有072用户产物仍须明确拒绝，不能为了让更新测试通过而放宽部署门。
            with self.assertRaisesRegex(RuntimeError,'075多持有者独立起手'):validate_dll()
        elif HOOK_CONTRACT.encode('ascii') not in existing:
            # 076旧075用户DLL应在合同门拒绝，不能为测试放宽部署校验。
            with self.assertRaisesRegex(RuntimeError,'076通用Hook预筛'):validate_dll()
        elif TERRAIN_CONTRACT.encode('ascii') not in existing:
            # 077仍拒绝旧076用户DLL；隔离部署测试不允许为了通过而放宽实际合同。
            with self.assertRaisesRegex(RuntimeError,'077原生环境射线组修复'):validate_dll()
        elif AUDIT_HOOK_CONTRACT.encode('ascii') not in existing:
            # 078旧077用户DLL也要明确拒绝，不能声称具有尚未编译的16入口诊断。
            with self.assertRaisesRegex(RuntimeError,'078高频Hook抽样'):validate_dll()
        elif EQUIPMENT_CONTRACT.encode('ascii') not in existing:
            # 079工作修复不能由旧DLL冒充；测试只读取/拒绝，不生成产物。
            with self.assertRaisesRegex(RuntimeError,'079实际手持/家具工作修复'):validate_dll()
        elif PERFORMANCE_CONTRACT.encode('ascii') not in existing:
            # 080仍只读取用户DLL；旧产物应拒绝，不为通过隔离测试放宽合同。
            with self.assertRaisesRegex(RuntimeError,'080同窗性能优化'):validate_dll()
        elif MEDICAL_GATE_CONTRACT.encode('ascii') not in existing:
            # 083只读取并拒绝旧用户DLL；不伪造PE或编译产物来绕过实际更新门。
            with self.assertRaisesRegex(RuntimeError,'083医疗安全门修复'):validate_dll()
        elif NATIVE_PROFILE_CONTRACT.encode('ascii') not in existing:
            # 084仍只读取用户现有产物；旧083不得标成新诊断已经加载。
            with self.assertRaisesRegex(RuntimeError,'084原生受击/服务机会诊断'):validate_dll()
        elif WOUND_PROFILE_CONTRACT.encode('ascii') not in existing:
            # 085只验证拒绝旧084，不生成假DLL或触发编译。
            with self.assertRaisesRegex(RuntimeError,'085伤口细分/原生对照诊断'):validate_dll()
        elif MEDICAL_BRANCH_CONTRACT.encode('ascii') not in existing:
            # 086只拒绝实际旧085产物，不伪造PE或触发编译；对应生产新增合同。
            with self.assertRaisesRegex(RuntimeError,'086医疗分支诊断'):validate_dll()
        elif SWEEP_INDEX_CONTRACT.encode('ascii') not in existing:
            with self.assertRaisesRegex(RuntimeError,'086同步扫掠索引'):validate_dll()
        elif CONTACT_WORK_CONTRACT.encode('ascii') not in existing:
            # 087只检查真实旧DLL被新合同拒绝，不生成假PE或执行编译。
            with self.assertRaisesRegex(RuntimeError,'087查询消费优化'):validate_dll()
        elif QUERY_BATCH_CONTRACT.encode('ascii') not in existing:
            # 088只验证真实旧DLL拒绝门，不生成假产物、不代编译。
            with self.assertRaisesRegex(RuntimeError,'088同步批量查询'):validate_dll()
        elif RANGED_WORK_CONTRACT.encode('ascii') not in existing:
            # 089只读检查真实旧产物，不制作假DLL、不代编译。
            with self.assertRaisesRegex(RuntimeError,'089远程查询省查'):validate_dll()
        elif SPATIAL_PROJECTILES_CONTRACT.encode('ascii') not in existing:
            # 090不构造假二进制，只验证真实旧DLL拒绝门。
            with self.assertRaisesRegex(RuntimeError,'090空间查询和无弹体上限'):validate_dll()
        elif WORK_TRACE_CONTRACT.encode('ascii') not in existing:
            # 091只测试真实090 DLL的拒绝门，不生成假产物、不触发编译。
            with self.assertRaisesRegex(RuntimeError,'091抽样阶段追踪'):validate_dll()
        elif INTERFACE_PROBE_CONTRACT.encode('ascii') not in existing:
            # 092不生成假DLL，仅验证真实091产物不能冒充本轮监视。
            with self.assertRaisesRegex(RuntimeError,'092全量接口和宽相成本监视'):validate_dll()
        elif b'IRIS_QUERY_BOUNDARY_093' not in existing:
            # 093只核对真实092产物的拒绝门，不生成二进制或执行编译。
            with self.assertRaisesRegex(RuntimeError,'093查询边界和实例精确复用'):validate_dll()
        elif b'IRIS_CONSERVATIVE_QUERY_094' not in existing:
            # 094仅确认真实093旧产物被拒绝；不构造DLL或执行编译。
            with self.assertRaisesRegex(RuntimeError,'094保守范围映射'):validate_dll()
        else:
            # 3.0验收：095证明合同已随后续原生查询方案退役，生产validate_dll不再要求它。
            # 新DLL必须由当前完整合同/PE/资源/源码时间门决定，不能被已废弃测试误判；这里仍真实调用验证器。
            path,data=validate_dll();self.assertIn(BUILD_CONTRACT.encode('ascii'),data);self.assertEqual(path.name,'IrisArsenal.dll')

if __name__=='__main__':unittest.main(verbosity=2)
