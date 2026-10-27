"""080只读NVIDIA全卡采样；不附加游戏、不创建常驻任务，不把GPU利用率当帧时间。"""
from pathlib import Path
import argparse,csv,datetime,json,shutil,subprocess,time
FIELDS='timestamp,index,name,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.total,clocks.current.graphics,power.draw'
def sample(executable):
    # 仅查询现有驱动工具；不安装依赖、不改电源/时钟/温控，N/A原样保留。
    result=subprocess.run([executable,'--query-gpu='+FIELDS,'--format=csv,noheader,nounits'],capture_output=True,text=True,encoding='utf8',errors='strict',timeout=10,check=True)
    return list(csv.reader(result.stdout.splitlines(),skipinitialspace=True))
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--label',required=True);p.add_argument('--samples',type=int,default=30);p.add_argument('--interval',type=float,default=1);a=p.parse_args()
    if not 1<=a.samples<=3600 or not 0<=a.interval<=60:p.error('samples须1..3600，interval须0..60秒')
    exe=shutil.which('nvidia-smi.exe') or shutil.which('nvidia-smi')
    if not exe:raise SystemExit('未找到现有nvidia-smi；没有安装依赖。')
    # 输出目录必须全新，防止覆盖既有测量或原日志。
    a.out.mkdir(parents=True,exist_ok=False)
    metadata={'label':a.label,'tool_revision_date':'2026-10-23','capture_start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'whole GPU, all processes and driver','game_frame_time_measured':False,'per_process_gpu_time_measured':False,'gpu_memory_is_not_Iris_memory':True,'shader_optimization_applied':False,'samples_requested':a.samples,'interval_seconds':a.interval,'tool':exe}
    with (a.out/'metadata.json').open('x',encoding='utf8') as f:json.dump(metadata,f,ensure_ascii=False,indent=2)
    with (a.out/'gpu.csv').open('x',encoding='utf8',newline='') as f:
        writer=csv.writer(f);writer.writerow(['sample','capture_utc']+FIELDS.split(','))
        for i in range(a.samples):
            if i:time.sleep(a.interval)
            stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
            for row in sample(exe):writer.writerow([i,stamp]+row)
            f.flush()
    # 原样附带温控状态文本；部分驱动字段不支持时保留错误，不伪造热降频结论。
    q=subprocess.run([exe,'-q','-d','PERFORMANCE,TEMPERATURE,MEMORY,CLOCK'],capture_output=True,text=True,encoding='utf8',errors='strict',timeout=10)
    with (a.out/'driver-details.txt').open('x',encoding='utf8') as f:f.write(q.stdout+'\n'+q.stderr)
    print(json.dumps({'output':str(a.out),'samples':a.samples,'frame_time_measured':False,'driver_details_exit_code':q.returncode},ensure_ascii=False))
if __name__=='__main__':main()
