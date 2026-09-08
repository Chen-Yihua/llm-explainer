import re
import time
import pickle
from typing import Optional, List

from aalpy.base import Automaton, SUL
from aalpy.base.CacheTree import CacheDict
from aalpy.base.Oracle import Oracle
from aalpy.learning_algs import (
    run_Lstar, run_KV, run_non_det_Lstar,
    run_stochastic_Lstar, run_abstracted_ONFSM_Lstar, run_Alergia,
    run_JAlergia, run_active_Alergia, run_RPNI, run_active_RPNI
)
from diss import LabeledExamples

import create_test_dataset


class LLMAutomatonSUL(SUL):
    def __init__(self, automaton: Automaton, client, mq_prompt, params, positive_examples, negative_examples):
        super().__init__()
        self.client = client # LLM 客戶端
        self.params = params # LLM 參數
        self.current_sequence = [] # 當前序列
        self.mq_prompt = mq_prompt # 成員查詢問題
        self.cache = CacheDict()
        self.cache_file = "cache/cache.pkl"  # pickle 檔案
        self.cache = self.load_cache()  # 載入 cache
        self.positive_examples = positive_examples
        self.negative_examples = negative_examples

    def add_cache(self, input_sequence, output_result):
        self.cache[input_sequence] = output_result
        self.save_cache()  # 每次更新都存檔

    def in_cache(self, input_seq: tuple):
        self.cache = self.load_cache()  # 重新載入最新的 pickle 檔案
        return self.cache.get(input_seq, None)

    def load_cache(self):
        """嘗試從 pickle 載入 cache，若無則創建新檔案"""
        try:
            with open(self.cache_file, "rb") as f:
                return pickle.load(f)
        except (FileNotFoundError, EOFError):  # 檔案不存在或損壞
            # 若檔案不存在，則建立一個新的空字典並存入 pickle
            empty_cache = {}
            with open(self.cache_file, "wb") as f:
                pickle.dump(empty_cache, f)
            return empty_cache

    def save_cache(self):
        """將 cache 存入 pickle"""
        with open(self.cache_file, "wb") as f:
            pickle.dump(self.cache, f)

    # 取得 sul 中的所有正例與反例
    def get_proposed_examples(self):
        return(LabeledExamples(
                positive = self.positive_examples,
                negative = self.negative_examples,
        ))

    def pre(self): # 重置
        self.current_sequence = []

    def step(self, letter = None): # 向 LLM 發送序列並獲取回應 (membership query)
        # 暫存字母
        if letter is None:
            letter = '""'
        else:
            self.current_sequence.append(letter)

        cached_query = self.in_cache(tuple(self.current_sequence)) # 查看序列是否被問過
        if cached_query != None:
            return cached_query

        # 詢問 LLM
        full_seq = ','.join(self.current_sequence)
        if not full_seq:  # 處理空字串
            full_seq = '#'
        query = self.mq_prompt + full_seq
        print("-----------------------------")
        print("membership query : ", full_seq)

        full_response = ""
        while len(full_response) == 0:
            full_response = self.client.execute_query(query, **self.params)
            time.sleep(2)

        # 取出回答
        response = ""
        response_cleaned = full_response.replace('\n', '').replace('**', '').replace('<', '').replace('>', '').replace('\_', '_')
        pattern = r"FINAL_ANSWER\s*:\s*(.*?)[\s.]*$"
        print("LLM response : ",response_cleaned)
        match = re.search(pattern, response_cleaned)
        if match:
            response = match.group(1).lower()
        else:
            raise ValueError(f"No match: {response}")

        # 確認回答是否符合格式
        if response not in {"true","false"}:
            raise ValueError(f"Unexpected LLM response: {response}")
        if response == "true":
            self.add_cache(tuple(self.current_sequence), True)
            self.positive_examples.append(tuple(self.current_sequence))
            return True
        else:
            self.add_cache(tuple(self.current_sequence), False)
            self.negative_examples.append(tuple(self.current_sequence))
            return False
    def post(self): # 清理
        pass

MealySUL = OnfsmSUL = StochasticMealySUL = DfaSUL = MooreSUL = MdpSUL = McSUL = SevpaSUL = LLMAutomatonSUL


class ChatGPTEqOracle(Oracle):
    def __init__(self, alphabet: List[str], sul: SUL, client, automaton_type):
        super().__init__(alphabet, sul)
        self.client = client
        self.automaton_type = automaton_type
        # 讀取 Positive
        with open("data/Positive_examples.txt", "r", encoding="utf-8") as f:
            positive_examples = f.read()
            self.positive_examples = create_test_dataset.extract_lists(positive_examples)
        # 讀取 Negative
        with open("data/Negative_examples.txt", "r", encoding="utf-8") as f:
            negative_examples = f.read()
            self.negative_examples = create_test_dataset.extract_lists(negative_examples)

    # 判斷假設模型 hypothesis 是否接受給定的輸入字串
    def accept_dfa_vpa(self, hypothesis, word, is_positive):
        hypothesis.reset_to_initial()
        temp_state = hypothesis.current_state
        for letter in word:
            temp_state = temp_state.transitions[letter]
        if temp_state.is_accepting != is_positive: # 若有 element 不被自動機接受就回傳
            print("fail eq_query")
            return False
        print("pass eq_query")
        return True

    def accept_moore(self, hypothesis, word, is_positive):
        hypothesis.reset_to_initial()
        temp_state = hypothesis.current_state
        for letter in word:
            temp_state = temp_state.transitions[letter]
        if temp_state.output != is_positive: # 若有 element 不被自動機接受就回傳
            return False
        return True

    def accept_mealy_smm(self, hypothesis, word, expected_output):
        hypothesis.reset_to_initial()
        current_state = hypothesis.initial_state
        for letter in word:
            # 取得對應的輸出和下一個狀態
            output = current_state.output_fun[letter]
            current_state = current_state.transitions[letter]
        if output != expected_output:
            return False
        return True

    def accept_stochastic(self, automaton, sequence, is_positive):
        probability = self.calculate_probability(automaton, sequence)
        threshold = 0.5 if is_positive else 0.1
        return probability >= threshold

    def accept_onfsm(self, automaton, sequence, is_positive):
        return any(self.accept_dfa_moore(automaton, seq, is_positive) for seq in self.get_all_possible_paths(automaton, sequence))


    # 測試正反例
    def find_cex(self, hypothesis) -> Optional[List[str]]: # 檢查假設模型是否等價於目標系統，若不等價，返回一個反例
        # hypothesis.visualize()

        print("****************************")
        print("測試正反例")

        for sequence in reversed(self.positive_examples):
            print("test positive example (eq_query): ", sequence)
            if self.automaton_type in ["mealy", "smm"]:
                if not self.accept_mealy_smm(hypothesis, sequence, expected_output = True):
                    return list(sequence)
            elif self.automaton_type in ["dfa", "vpa"]:
                if not self.accept_dfa_vpa(hypothesis, sequence, is_positive = True):
                    return list(sequence)
            elif self.automaton_type in ["moore"]:
                if not self.accept_moore(hypothesis, sequence, is_positive = True):
                    return list(sequence)
            elif self.automaton_type in ["mc", "mdp"]:
                if not self.accept_stochastic(hypothesis, sequence, is_positive = True):
                    return list(sequence)
            elif self.automaton_type == "onfsm":
                if not self.accept_onfsm(hypothesis, sequence, is_positive = True):
                    return list(sequence)
            self.positive_examples.pop()

        for sequence in reversed(self.negative_examples):
            print("test negative example (eq_query): ", sequence)
            if self.automaton_type in ["mealy", "smm"]:
                if not self.accept_mealy_smm(hypothesis, sequence, expected_output = False):
                    return list(sequence)
            elif self.automaton_type in ["dfa", "vpa"]:
                if not self.accept_dfa_vpa(hypothesis, sequence, is_positive = False):
                    return list(sequence)
            elif self.automaton_type in ["moore"]:
                if not self.accept_moore(hypothesis, sequence, is_positive = False):
                    return list(sequence)
            elif self.automaton_type in ["mc", "mdp"]:
                if not self.accept_stochastic(hypothesis, sequence, is_positive = False):
                    return list(sequence)
            elif self.automaton_type == "onfsm":
                if not self.accept_onfsm(hypothesis, sequence, is_positive = False):
                    return list(sequence)
            self.negative_examples.pop()

        print("****************************")

        return None # 未發現反例


class robot:
    def learning(client, params, mq_prompt, alphabet, automaton_type, sul, eq_oracle):
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

        counterexample_processing_strategy = [None, 'rs', 'longest_prefix', 'linear_fwd', 'linear_bwd', 'exponential_fwd','exponential_bwd']
        api_dict = {
            "Lstar": run_Lstar,
            "KV": run_KV,
            "non_det_Lstar": run_non_det_Lstar,
            "stochastic_Lstar": run_stochastic_Lstar,
            "abstracted_ONFSM_Lstar": run_abstracted_ONFSM_Lstar,
            "Alergia": run_Alergia,
            "JAlergia": run_JAlergia,
            "active_Alergia": run_active_Alergia,
            "RPNI": run_RPNI,
            "active_RPNI": run_active_RPNI
        }

        # 設定變數
        cex_processing = None   # 反例處理策略
        selected_algorithm = "Lstar" # 選擇學習算法
        learner = api_dict[selected_algorithm]

        learned_dfa = learner(
            alphabet = alphabet,
            sul = sul,
            eq_oracle = eq_oracle,
            automaton_type = automaton_type,
            cex_processing = cex_processing,
            cache_and_non_det_check = True,
        )

        return learned_dfa
