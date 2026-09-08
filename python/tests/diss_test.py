import subprocess
import json

# 執行 WSL 內的 Python 並獲取結果
WSL_PYTHON_PATH = "/home/user/myenv/bin/python3"

def get_demos():
    buff = """y....g..
        ........
        .b.b...r
        .b.b...r
        .b.b....
        .b.b....
        rrrrrr.r
        g.y....."""
    buff_json = json.dumps(buff)

    cmd = f"""{WSL_PYTHON_PATH} -c 'import json; from diss.experiment.planner import GridWorldPlanner;
planner = GridWorldPlanner.from_string(
    buff=json.loads({buff_json}),
    start=(3, 5),
    slip_prob=1/32,
    horizon=15,
    policy_cache="diss_experiment.shelve",
);
TRC4 = [
    (3, 5),
    {{"a": "↑", "c": 0}},
    {{"a": "↑", "c": 1}},
    {{"a": "↑", "c": 1}},
    {{"a": "→", "c": 1}},
    {{"a": "↑", "c": 1}},
    {{"a": "↑", "c": 1}},
    {{"a": "→", "c": 1}},
    {{"a": "→", "c": 1}},
    {{"a": "→", "c": 1}},
    {{"a": "←", "c": 1}},
    {{"a": "←", "c": 1}},
    {{"a": "←", "c": 1}},
    {{"a": "←", "c": 1}},
    {{"a": "←", "c": 1, "EOE_ego": 1}},
];
TRC5 = [
    (3, 5),
    {{"a": "↑", "c": 1}},
    {{"a": "↑", "c": 1}},
    {{"a": "↑", "c": 1}},
    {{"a": "←", "c": 1}},
    {{"a": "←", "c": 1, "EOE_ego": 1}},
];
demos = [planner.to_demo(TRC4), planner.to_demo(TRC5)];
print(json.dumps(demos))'"""

    result = subprocess.run(
        ["wsl", "bash", "-c", cmd],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        print("Error in WSL execution:", result.stderr)
        return None

# def get_to_chain(c, t, psat):

#     return planner.plan(c, t, psat, monolithic=True, use_rationality=True)

# def get_path_to_colors():
#     return planner.lift_path



get_demos()