"""Simple wrapper around a database connection."""
import persistence.DBConnection as DBConnection
from entities import TestSentence

db = DBConnection.DBConnection()

def save_test_query(test_query):
    db.add_test_query(test_query)

def save_test_sentence(test_sentence: TestSentence):
    db.add_test_sentence(test_sentence)

def save_model_parameters(model_parameter):
    db.add_model_parameter(model_parameter)

def save_oracle_result(oracle_result):
    db.add_oracle_result(oracle_result)

def save_oracle_description(oracle_description):
    db.add_oracle_description(oracle_description)

def get_current_run_id():
    return db.get_last_run_id()

def get_test_sentences():
    return db.get_test_sentences_as_df()

def get_oracle_results():
    return db.get_oracle_results_as_df()

def get_oracle_descriptions():
    return db.get_oracle_descriptions_as_df()

def get_test_queries_by_sentence_id(sentence_id):
    return db.get_test_queries_by_sentence_id_as_df(sentence_id)

def get_test_queries():
    return db.get_test_queries_as_df()

def get_unevaluated_test_queries_by_sentence_id(sentence_id, oracle_id):
    return db.get_unevaluated_test_queries_by_sentence_id(sentence_id, oracle_id)

def get_model_parameters(sentence_id):
    return db.get_model_parameters_by_sentence_id_as_df(sentence_id)

def get_filtered_sentence_ids(filter_args):
    if filter_args:
        return db.get_filtered_sentence_ids(filter_args)
    else:
        return db.get_test_sentences_as_df()

def get_complete_data_by_oracle_id(oracle_id):
    return db.get_complete_data_by_oracle_id(oracle_id)

def get_test_data():
    return db.get_test_data()

def get_test_data_by_oracle_id(oracle_id):
    return db.get_test_data_by_oracle_id(oracle_id)

def get_test_data_by_sentence_id(sentence_id):
    return db.get_test_data_by_sentence_id(sentence_id)
