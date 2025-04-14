import re
from services import DatabaseService
from entities import OracleResult

def save_oracle_results(test_data, oracle_id=1):
    """Save the result of comparing a LLM response with the correct answer."""
    assert "result" in test_data, "Oracle was not applied before saving!"
    for res in [OracleResult(-1, oracle_id, qid, label == predict)
              for qid, label, predict
              in zip(test_data["query_id"],
                     test_data["correct_answer_label"],
                     test_data["result"])]:
        DatabaseService.save_oracle_result(res)

def apply_oracle(test_data, oracle_function):
    """Attach oracle verdicts to a dataframe."""
    test_data["result"] = test_data.apply(oracle_function, axis=1)
    return test_data

def encode_for_classification(query: str) -> list[str]:
    """Normalize string to produce an oracle verdict.

    This replaces superfluous elements and non-alphanumeric
    characters before splitting the input string by whitespace."""
    query = query.replace("<pad>", "")
    query = re.sub(r"[^a-zA-Z0-9 ]", "", query)
    return query.lower().split()

def reduce_response(row):
    """Remove superfluous parts from a LLM's response."""
    return (row["new_response"]
            .replace("Result is: ", "")
            .replace(row["modified_question"], ""))

def initial_oracle_function(response):
    """Simple oracle that transforms the LLM response into boolean string."""
    response = encode_for_classification(reduce_response(response))
    if len(response) > 0:
        response = response[0]
    else:
        return "undefined"
    oracle_result = ""
    if "no" == response or "false" == response or "0" == response:
        oracle_result += "false"
    if "yes" == response or "true" == response or "1" == response:
        oracle_result += "true"
    if not oracle_result or oracle_result == "falsetrue":
        oracle_result = "undefined"
    return oracle_result

def preliminary_check():
    """Apply oracle function and return counts per label."""
    test_queries = DatabaseService.get_test_queries()
    label_stats = {}
    for _, row in test_queries.iterrows():
        result_label = initial_oracle_function(row)
        label_stats[result_label] = label_stats.get(result_label, 0) + 1
    return label_stats

def get_precision(df):
    """Calculate the precision of LLM responses.

    The precision is defined as tp/(tp+fp), where
    tp is the number of true positives and
    fp is the number of false positives."""
    tp = get_true_positives(df)
    fp = get_false_positives(df)
    if tp + fp == 0:
        return 0
    return tp / (tp + fp)

def get_recall(df):
    """Calculate the recall of LLM responses.

    The recall is defined as tp/(tp+fn), where
    tp is the number of true positives and
    fn is the number of false negatives."""
    tp = get_true_positives(df)
    fn = get_false_negatives(df)
    if tp + fn == 0:
        return 0
    return tp / (tp + fn)

def get_f1_score(df):
    """Calculate the F1 score."""
    precision = get_precision(df)
    recall = get_recall(df)
    if precision + recall == 0:
        return 0
    return 2 * (precision * recall) / (precision + recall)

def get_true_positives(df):
    """Return the number of true positives in the dataframe."""
    return len(df.query('(correct_answer_label == "true") and (result == "true")'))

def get_false_positives(df):
    """Return the number of false positives in the dataframe."""
    return len(df.query('(correct_answer_label == "false") and (result == "true")'))

def get_true_negatives(df):
    """Return the number of true negatives in the dataframe."""
    return len(df.query('(correct_answer_label == "false") and (result == "false")'))

def get_false_negatives(df):
    """Return the number of false negatives in the dataframe."""
    return len(df.query('(correct_answer_label == "true") and (result == "false")'))

def get_consistency(test_data):
    """Calculate the mean consistency of a LLM over all sentences."""
    grouped_test_data = test_data.groupby("sentence_id")
    accumulated_consistency = 0
    for _, group in grouped_test_data:
        consistency = calculate_consistency(group)
        accumulated_consistency += consistency
    return accumulated_consistency / len(grouped_test_data)

def calculate_consistency(sentence_data):
    """Calculate how many LLM responses are identical to the initial one.

    The initial response corresponds to the unmodified question,
    i.e. without any synonyms applied."""
    min_id = sentence_data["query_id"].min()
    initial_result = sentence_data.loc[sentence_data["query_id"] == min_id]
    initial_result = initial_result["result"].values[0]
    counts = sentence_data["result"].value_counts(normalize=True)
    return counts[initial_result]
