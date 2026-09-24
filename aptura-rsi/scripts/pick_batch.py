import glob, json, random, re, sys

bad, good = [], []
for d in sorted(glob.glob("dataset/hackathon/tau3-bench/tasks/*/environment/runtime-server/task_config.json")):
    tid = re.search(r"task-(\d+)", d).group(1)
    tools = json.load(open(d))["task"]["user_tools"]
    (bad if "request_human_agent_transfer" in tools else good).append(tid)
tested = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else set()
pool = [t for t in good if t not in tested]
random.seed(int(sys.argv[1]))
pick = sorted(random.sample(pool, 10))
print(len(good), len(bad), len(pool))
print(" ".join(pick))
