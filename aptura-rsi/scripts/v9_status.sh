cd "$(dirname "$0")"
for f in runs/tau-v9-*/attempts.jsonl; do t=${f%/attempts.jsonl}; t=${t##*-}
  python3 -c "
import json,sys,glob
a=json.loads(open('$f').readline()); st=a['status']; sc=a['score']
n=0;deaths='';srch=0
for p in glob.glob('$f'.replace('attempts.jsonl','harbor-jobs/*/*/agent/trajectory.json')):
    try: tr=json.load(open(p))
    except: continue
    msgs=tr if isinstance(tr,list) else tr.get('messages',tr.get('events',[]))
    s=json.dumps(msgs); srch=s.count('\"KB_search\"'); n=len(msgs)
print(f'$t score={sc} status={st} traj_msgs={n} KB_search~{srch}')
"
done
