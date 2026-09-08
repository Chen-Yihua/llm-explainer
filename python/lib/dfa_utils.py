def aalpy_dfa_to_dict(aalpy_dfa) -> dict:
    from dfa.utils import dict2dfa

    dfa_dict = {}
    for s in aalpy_dfa.states:
        sid = s.state_id  # 取得狀態ID (如 's0', 's1')
        accepting = s.is_accepting # 取得接受標記

        # 轉移表 {input: 下個狀態ID}
        transition_map = {}
        for inp, nxt in s.transitions.items():
            transition_map[inp] = nxt.state_id

        dfa_dict[sid] = (accepting, transition_map)

    dfa_dict = dict2dfa(dfa_dict, start = aalpy_dfa.initial_state.state_id)
    return dfa_dict

def learn_dfa_from_examples(positive_examples, negative_examples):
    """
    根據正例 (positive_examples) 和反例 (negative_examples) 學習 DFA
    """
    from aalpy.automata import DfaState
    from aalpy.base import Automaton

    # 創建初始狀態
    start_state = DfaState("s0")
    states = {"s0": start_state}

    # 根據範例構造 DFA
    for ex in positive_examples:
        current_state = start_state
        for symbol in ex:
            if symbol not in current_state.transitions:
                new_state_name = f"s{len(states)}"
                new_state = DfaState(new_state_name)
                states[new_state_name] = new_state
                current_state.transitions[symbol] = new_state
            current_state = current_state.transitions[symbol]
        current_state.is_accepting = True  # 正例最終狀態應該是接受狀態

    # 反例應該停在非接受狀態
    for ex in negative_examples:
        current_state = start_state
        for symbol in ex:
            if symbol not in current_state.transitions:
                new_state_name = f"s{len(states)}"
                new_state = DfaState(new_state_name)
                states[new_state_name] = new_state
                current_state.transitions[symbol] = new_state
            current_state = current_state.transitions[symbol]
        current_state.is_accepting = False  # 反例最終狀態應該是拒絕狀態

    return Automaton(initial_state=start_state.state_id, states=list(states.values()))

def extend_dfa_with_examples(dfa, positive_examples, negative_examples):
    """
    基於新的 examples 擴展 DFA，避免重新學習

    :param dfa: 目前學到的 DFA
    :param positive_examples: 新的正例
    :param negative_examples: 新的反例
    :return: 擴展後的 DFA
    """
    from aalpy.learning_algs import run_Lstar

    # 取得 DFA 目前的 SUL
    sul = dfa.sul

    # 取得新的測試例
    sul.positive_examples.update(positive_examples)
    sul.negative_examples.update(negative_examples)

    # 重新學習，但保留 DFA 的現有結構
    extended_dfa = run_Lstar(
        alphabet=dfa.get_alphabet(),
        sul=sul,
        eq_oracle=dfa.eq_oracle,
        automaton_type='dfa',
        cex_processing=None
    )

    return extended_dfa

def get_target_dfa():
    from aalpy.automata import Dfa

    target_dfa = {
        'q0': (False, {'a': 'q0', 'b': 'q1'}),  # q0 是初始狀態，非接受
        'q1': (True, {'a': 'q2', 'b': 'q2'}),   # q1 是接受狀態
        'q2': (True, {'a': 'q2', 'b': 'q2'})    # q2 是接受狀態
    }

    return Dfa.from_state_setup(target_dfa)
