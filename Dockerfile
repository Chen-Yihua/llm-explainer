# 使用官方 Python image
FROM python:3.10-slim

# 建立工作目錄
WORKDIR /app

# 複製整個專案進 container
COPY . .

# 安裝必要套件
RUN pip install diss networkx==3.4.2 dfa==4.6.3 dfa_identify==3.11.0 pydot==3.0.4 py-aiger==6.2.0 py-aiger-bv==4.7.6 py-aiger-dfa==0.4.2 parsimonious==0.10.0 py-aiger-gridworld==0.4.3 py-aiger-bdd==3.1.1 aalpy==1.4.0 openai==1.61.1 google-generativeai==0.8.4
# RUN pip install --no-cache-dir -r requirements.txt || true
# RUN pip install -U pip


# 加入 PYTHONPATH，讓 Python 找得到 python/lib 的共用模組
ENV PYTHONPATH=/app/python/lib


# 預設執行 test 程式（實驗入口）
CMD ["python", "python/experiments/robot_test_with_diss.py"]
