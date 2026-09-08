import sys
import os
# 讓實驗入口找得到 python/lib 底下的共用模組
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))

import re
import time
from lstar.learn import _learn_dfa, learn_dfa
from lstar import iterative_deeping_ce

import Client

BASE_PROMPT = """
Tomita Grammar is a language that can only be made up of "0" and "1".

Your task is to answer the following questions using step-by-step reasoning to
show your work. Do not answer any other question. When you arrive at a
conclusion, please state it as FINAL_ANSWER: <yes, no>
"""

def _word_to_str(word):
    """lstar 傳入的 word 是 0/1 組成的 tuple（例如 (0, 1, 0)），轉成 "010" 這種字串才能用字串比對／嵌入 prompt。"""
    return "".join(str(c) for c in word)

def tomita_1(word):
    return "0" not in _word_to_str(word)

def tomita_1_llm(word):
    prompt = BASE_PROMPT + "\n\n" + \
        f"Does the following word contain a 0: {_word_to_str(word)}?\n"

    return prompt

def tomita_1_ce(dfa):
    count = len(dfa.states())
    if count == 2: # minimal DFA
        return None
    else:
        # I need to return a counterexample
        return "1"*(count//2)

def tomita_2(word):
    word = _word_to_str(word)
    return word=="10"*(int(len(word)/2))

def tomita_2_llm(word):
    prompt = BASE_PROMPT + "\n\n" + \
        f'Does the following word repeat EXACTLY as alternating "0" and "1" \
        without breaking the pattern? In other words, is every 0 followed by \
        a 1 and every 1 followed by a 0? {_word_to_str(word)}?\n'

    return prompt

def tomita_2_ce(dfa):
    count = len(dfa.states())
    if count == 3: # minimal DFA
        return None
    else:
        # I need to return a counterexample
        return "10"*(count//2)

_not_tomita_3 = re.compile("((0|1)*0)*1(11)*(0(0|1)*1)*0(00)*(1(0|1)*)*$") 
# *not* tomita 3: words containing an odd series of consecutive ones and then later an odd series of consecutive zeros
# tomita 3: opposite of that
def tomita_3(w):
    return None is _not_tomita_3.match(_word_to_str(w)) #complement of _not_tomita_3

def tomita_3_llm(word):
    prompt = BASE_PROMPT + "\n\n" + \
        f"Does the following word contain an odd consecutive series of 0's \
        followed by an odd consecutive series of 1's: {_word_to_str(word)}?\n"

    return prompt

def tomita_3_ce(dfa):
    count = len(dfa.states())
    if count == 5: # minimal DFA
        return None
    else:
        # I need to return a counterexample
        return "0"*(count//2) + "1"*(count//2)

def tomita_4(word):
    return "000" not in _word_to_str(word)

def tomita_4_llm(word):
    prompt = BASE_PROMPT + "\n\n" + \
        f"Does the following word contain a exactly 3 consecutive '0': {_word_to_str(word)}?\n"

    return prompt

def tomita_4_ce(dfa):
    count = len(dfa.states())
    if count == 4: # minimal DFA
        return None
    else:
        # I need to return a counterexample
        return "000"*(count//3)

def tomita_5(word):
    word = _word_to_str(word)
    return (word.count("0")%2 == 0) and (word.count("1")%2 == 0)

def tomita_5_llm(word):
    prompt = BASE_PROMPT + "\n\n" + \
        f"Does the following word contain an even number of 0's and an even number of 1's: {_word_to_str(word)}?\n"

    return prompt

def tomita_5_ce(dfa):
    count = len(dfa.states())
    if count == 4: # minimal DFA
        return None
    else:
        # I need to return a counterexample
        even_count = count//2 + 1 if count%2 == 1 else count//2
        return "0"*even_count + "1"*even_count

def tomita_6(word):
    word = _word_to_str(word)
    return ((word.count("0")-word.count("1"))%3) == 0

def tomita_6_llm(word):
    prompt = BASE_PROMPT + "\n\n" + \
        f"Does the number of 0's minus the number of 1's divide by 3 evenly: {_word_to_str(word)}?\n"

    return prompt

def tomita_6_ce(dfa):
    count = len(dfa.states())
    if count == 3: # minimal DFA
        return None
    else:
        # I need to return a counterexample
        return "0"*(count//3) + "1"*(count//3)

def tomita_7(word):
    return _word_to_str(word).count("10") <= 1

def tomita_7_llm(word):
    prompt = BASE_PROMPT + "\n\n" + \
        f"Does the following word contain at most one occurrence of '10': {_word_to_str(word)}?\n"

    return prompt

def tomita_7_ce(dfa):
    count = len(dfa.states())
    if count == 5: # minimal DFA
        return None
    else:
        # I need to return a counterexample
        return "1010"*(count//5)



def query_llm(word, tomita_query, client, params):
    prompt = tomita_query(word)

    full_response = ""
    while len(full_response) == 0:
        full_response = client.execute_query(prompt, **params)
        time.sleep(2)

    print("Response from LLM Teacher:\n" + full_response)

    # 取出回答（沿用 automaton_learning.LLMAutomatonSUL 一致的解析方式）
    response_cleaned = full_response.replace('\n', '').replace('**', '').replace('<', '').replace('>', '')
    pattern = r"FINAL_ANSWER\s*:\s*(.*?)[\s.]*$"
    match = re.search(pattern, response_cleaned)
    if match:
        answer = match.group(1).lower()
    else:
        raise ValueError(f"No match: {full_response}")

    if answer not in {"yes", "no"}:
        raise ValueError(f"Unexpected LLM response: {answer}")

    return answer == "yes"


def test_tomita_1(client, params):
    dfa = learn_dfa(
        inputs={0, 1},
        label=lambda word: query_llm(word, tomita_1_llm, client, params),
        find_counter_example=iterative_deeping_ce(tomita_1, depth=7),
        outputs=None
    )

    return dfa

def test_tomita_2(client, params):
    dfa = learn_dfa(
        inputs={0, 1},
        label=lambda word: query_llm(word, tomita_2_llm, client, params),
        find_counter_example=iterative_deeping_ce(tomita_2, depth=7),
        outputs=None
    )

    return dfa


if __name__ == "__main__":
    model_name = "o1-mini"  # 使用的 GPT 模型名稱
    client = Client.ChatGPTClient(model_name = model_name)
    params = {
        "max_completion_tokens": 800,
        "temperature": 1,
    }

    print(test_tomita_1(client, params))
    print(test_tomita_2(client, params))