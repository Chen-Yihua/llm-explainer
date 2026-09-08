import sys
import os
# 讓實驗入口找得到 python/lib 底下的共用模組
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from tee import Tee
from diss.experiment.planner import GridWorldPlanner
from diss.concept_classes.dfa_concept import DFAConcept
import diss
import automaton_learning
import dfa_utils
import create_test_dataset
import Client

def robot_test_with_diss():
    """
    Example automaton from L∗LM paper.

    alphabet: 
    test_datasize_size: 
    test_data_size: 
    model_name: 
    automaton_type: 
    cex_processing: 
    selected_algorithm: 
    max_completion_tokens: 
    temperature: 
    question: 
    definition_problem: 

    :return: learned DFA
    """

    # 打開檔案，覆蓋舊內容
    with open("log/run_lstar_dfa_diss_1.txt", "w", encoding="utf-8") as log_file:
        sys.stdout = Tee(sys.stdout, log_file) # 同時輸出到終端和檔案

        # 設定 prompt
        # 成員查詢問題
        question = (f"""
        Please answer the following questions to show your work. 
        - Do not answer any other question. 
        - The empty sequence is denoted by '#'
                    
        Output format:
        FINAL_ANSWER: <true, false>
        
        Question:
        - Is the following sequence a positive example? :  
        """)
        # 任務定義
        definition_problem = ("""
        A robot is operating in a grid world and can visit four types of tiles: {red, yellow, blue, green}.
        They correspond to lava (red), recharging (yellow), water (blue), and drying (green) tiles.
        The robot is to visit tiles according to some set of rules. This will be recorded as a sequence of colors.
        
        Rules:
         1. The sequence must contain at least one yellow tile, i.e., eventually recharge.
         2. The sequence must not contain any red tiles, i.e., lava must be avoided at all costs.
         3. If blue is visited, then you must visit green *before* yellow, i.e., the robot must dry off before recharging.
        
        A positive example must conform to all rules.
        Further note that repeated sequential colors can be replaced with a single instance.
        
        For example:
         1. [yellow,yellow,blue] => [yellow, blue]
         2. [red,red,blue,green,green,red] => [red,blue,green,red]
         3. [blue,blue,blue] => [blue]
        """)
        mq_prompt = definition_problem + question

        # 設定 LLM 參數
        model_name = "o1-mini"  # 使用的 GPT 模型名稱
        client = Client.ChatGPTClient(model_name = model_name)
        params = {
                    "max_completion_tokens": 800,
                    "temperature": 1,
                }
        
        # 生成測試問題
        example_types = ['Positive', 'Negative']        
        test_datasize_size = 5 # 資料集大小限制
        test_data_size = 5      # 單筆資料個數限制
        for example_type in example_types:
            test_data_prompt = (f"""
            For example:
            - [blue,green,yellow]、[yellow,green,blue] is Positive examples.
            - [green,blue,yellow] is Negative examples.
            
            Provide {test_datasize_size} {example_type} examples.
            - Each example has 1–{test_data_size} elements.

            Output format:
            {example_type} examples:
            - [color1]
            - [color1, color2]
            """)
            test_data_prompt = definition_problem + test_data_prompt

        # 設定 diss 參數
        # 生成真實路徑分布 (格子世界, 起始點, 滑動機率, 規劃長度, 快取檔案位置)
        planner = GridWorldPlanner.from_string(
        buff="""y....g..
            ........
            .b.b...r
            .b.b...r
            .b.b....
            .b.b....
            rrrrrr.r
            g.y.....""",
            start=(3, 5),
            slip_prob=1/32,
            horizon=15,
            policy_cache='cache/diss_experiment.shelve',
            ) 

        # 手刻兩條 demonstration 
        TRC4 = [
            (3, 5),
            {'a': '↑', 'c': 0},
            {'a': '↑', 'c': 1},
            {'a': '↑', 'c': 1},
            {'a': '→', 'c': 1},
            {'a': '↑', 'c': 1},
            {'a': '↑', 'c': 1},
            {'a': '→', 'c': 1},
            {'a': '→', 'c': 1},
            {'a': '→', 'c': 1},
            {'a': '←', 'c': 1},
            {'a': '←', 'c': 1},
            {'a': '←', 'c': 1},
            {'a': '←', 'c': 1},
            {'a': '←', 'c': 1, 'EOE_ego': 1},
        ]

        TRC5 = [
            (3, 5),
            {'a': '↑', 'c': 1},
            {'a': '↑', 'c': 1},
            {'a': '↑', 'c': 1},
            {'a': '←', 'c': 1},
            {'a': '←', 'c': 1, 'EOE_ego': 1},
        ]
        # Binary encode demonstrations for BDD based planner.
        to_demo = planner.to_demo # 轉成 DISS 可用的格式
        demos = [to_demo(TRC4), to_demo(TRC5)] # 初始學習 demonstration
        max_diss_iters = 4
        path_to_colors = planner.lift_path # 還原剛剛 to_demo 的路徑 (做 DFA 用)

        # 設定 membership query 變數
        alphabet = ['red', 'yellow', 'blue', 'green']
        automaton_type = 'dfa'  # 自動機類型
        positive_examples = []
        negative_examples = []
        sul = automaton_learning.LLMAutomatonSUL(None, client, mq_prompt, params, positive_examples, negative_examples) # 將 DFA 包裝為被學習系統（System Under Learning，SUL）

        # 生成機器人路徑
        def to_chain(c, t, psat):
            return planner.plan(c, t, psat, monolithic=True, use_rationality=True)
        
        # 生成 concept
        def llm_identifier(proposed_examples, concept):
            eq_oracle = automaton_learning.ChatGPTEqOracle(alphabet, sul, client, automaton_type)
            if concept is not None:
                new_examples = sul.get_proposed_examples() # 取得舊的 label 集合
                samples = proposed_examples @ new_examples # 將舊的 label 與 diss 生成的測試路徑合併
                create_test_dataset.write_proposed_examples(samples)

            concept = automaton_learning.robot.learning(client, params, mq_prompt, alphabet, automaton_type, sul, eq_oracle)
            concept = dfa_utils.aalpy_dfa_to_dict(concept) # 轉換成 diss 需要的格式
            concept = DFAConcept.from_dfa(concept) # 轉換 dfa to DFAConcept
               
            print("DFAConcept : ", concept)
            return concept 

        # 排序 energy
        def analyze(search):
            concept2energy = {}    # Explored concepts + associated energy
            # Run Search and collect concepts, energy, and POI.
            for data, concept, metadata in search:
                concept2energy[concept] = metadata['energy']
            return sorted(list(concept2energy), key=concept2energy.get)
        
        diss_params = {
            "demos": demos,
            "sgs_temp": 0.01, # 用於控制樣本生成的多樣性
            "n_iters": max_diss_iters, 
            "surprise_weight": 1, # 控制樣本的驚喜程度，影響探索的優先順序
            "reset_period": 30, # 每 30 次迭代會重設內部狀態，防止過度偏向某些樣本
            "size_weight": 1/80,
            "example_drop_prob": 1/20, # 有 1/20 機率隨機丟棄範例，以提升模型的穩健性
            "synth_timeout": 1800,
            "competency": lambda *_: 10,
            "to_chain": to_chain,
            "to_concept": llm_identifier,
            "lift_path": path_to_colors,
        }
        
        result = analyze(diss.diss(**diss_params))
        sys.stdout = sys.__stdout__ # 恢復 stdout
    return(result)

if __name__ == '__main__':
    learned_dfa = robot_test_with_diss()
    print("Learned DFA:", learned_dfa)
