import subprocess

# 執行 WSL 內的 Python 並獲取結果
WSL_PYTHON_PATH = "/home/user/myenv/bin/python3"
cmd = f"{WSL_PYTHON_PATH} -c 'import dd.cudd; print(dd.cudd)'"

result = subprocess.run(
    ["wsl", "bash", "-c", cmd],
    capture_output=True,
    text=True
)

print("WSL 輸出:", result.stdout.strip())
print("WSL 錯誤:", result.stderr.strip())
