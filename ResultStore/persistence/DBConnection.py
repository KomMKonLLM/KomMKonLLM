import numpy
import pandas.io.sql as sqlio
import psycopg2
import psycopg2.extras
from psycopg2.extensions import register_adapter, AsIs
from entities import TestSentence, TestQuery, ModelParameter, OracleResult, OracleDescription
from services.ConfigParser import *
from tenacity import retry, stop_after_attempt, wait_exponential

class DBConnection:
    """Persistence layer, can store/retrieve objects to/from a Postgres DB."""

    def __init__(self):
        """Connect to database and execute DB setup script."""
        register_adapter(numpy.float64, AsIs)
        register_adapter(numpy.int64, AsIs)
        self.connect()

    @retry(reraise=True, stop=stop_after_attempt(4),
           wait=wait_exponential(multiplier=1, min=2, max=16))
    def connect(self):
        """Establish database connection."""
        self.__connection = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                                             host=DB_HOST, port=DB_PORT,
                                             password=DB_PW)

    def add_test_sentence(self, test_sentence: TestSentence):
        """Add a TestSentence to the DB and return its ID."""
        cursor = self.__connection.cursor()
        cursor.execute("INSERT INTO test_sentence (id, sentence, "
                       "correct_answer_label, ipm_vector_notation, "
                       "source_data_name, model_name, ca_file, ipm_file, "
                       "ipm_description_file, strength, note)"
                       " VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                       "%s) RETURNING id", (test_sentence.sentence,
                                            test_sentence.correct_answer_label,
                                            test_sentence.ipm_vector_notation,
                                            test_sentence.source_data_name,
                                            test_sentence.model_name,
                                            test_sentence.ca_file,
                                            test_sentence.ipm_file,
                                            test_sentence.ipm_description_file,
                                            test_sentence.strength,
                                            test_sentence.note))
        self.__connection.commit()
        self.__currentRunId = cursor.fetchone()[0]
        cursor.close()

    def add_test_query(self, test_query: TestQuery):
        """Store a TestQuery."""
        cursor = self.__connection.cursor()
        cursor.execute("INSERT into test_query VALUES (%s, DEFAULT, %s, %s)",
                       (test_query.sentence_id,
                        test_query.modified_question,
                        test_query.new_response))
        self.__connection.commit()
        cursor.close()

    def add_model_parameter(self, model_parameter: ModelParameter):
        """Store a ModelParameter."""
        cursor = self.__connection.cursor()
        cursor.execute("INSERT into model_parameter VALUES (DEFAULT, %s, %s, %s)",
                       (model_parameter.sentence_id,
                        model_parameter.parameter,
                        model_parameter.value))
        self.__connection.commit()
        cursor.close()

    def add_oracle_result(self, oracle_result: OracleResult):
        """Store an OracleResult."""
        cursor = self.__connection.cursor()
        cursor.execute("INSERT into oracle_result VALUES (DEFAULT, %s, %s, %s)"
                       " ON CONFLICT DO NOTHING",
                       (oracle_result.query_id,
                        oracle_result.oracle_id,
                        oracle_result.result))
        self.__connection.commit()
        cursor.close()

    def add_oracle_description(self, oracle_description: OracleDescription):
        """Store an OracleDescription."""
        cursor = self.__connection.cursor()
        cursor.execute("INSERT into oracle_description VALUES (DEFAULT, %s, %s)",
                       (oracle_description.name, oracle_description.description))
        self.__connection.commit()
        cursor.close()

    def get_last_run_id(self) -> int:
        """Return the highest test run ID."""
        cursor = self.__connection.cursor()
        cursor.execute("Select max(id) from test_sentence")
        self.__connection.commit()
        self.__currentRunId = cursor.fetchone()[0]
        return self.__currentRunId

    def get_test_sentences(self):
        """Retrieve all test sentences."""
        cursor = self.__connection.cursor()
        cursor.execute("Select * from test_sentence")
        self.__connection.commit()
        return cursor.fetchall()

    def get_test_sentences_as_df(self):
        """Retrieve all test sentences as a Pandas dataframe."""
        return sqlio.read_sql_query("Select * from test_sentence", self.__connection)

    def get_oracle_results_as_df(self):
        """Retrieve all oracle results as a Pandas dataframe."""
        return sqlio.read_sql_query("Select * from oracle_result", self.__connection)

    def get_test_queries_as_df(self):
        """Retrieve all test queries as a Pandas dataframe."""
        return sqlio.read_sql_query(
            "Select ts.id as sentence_id, sentence, correct_answer_label,"
            "tq.id as query_id, modified_question, new_response "
            "from test_sentence ts join test_query tq on ts.id = tq.sentence_id",
            self.__connection)

    def get_oracle_descriptions_as_df(self):
        """Retrieve all oracle descriptions as a Pandas dataframe."""
        return sqlio.read_sql_query("Select * from oracle_description", self.__connection)

    def get_test_queries_by_sentence_id_as_df(self, sentence_id):
        """Retrieve test queries for a given sentence ID as dataframe."""
        return sqlio.read_sql_query(
            "Select ts.id as sentence_id, sentence, correct_answer_label,"
            "tq.id as query_id, modified_question, new_response "
            "from test_sentence ts join test_query tq on ts.id = tq.sentence_id"
            f" where sentence_id = {sentence_id}", self.__connection)

    def get_unevaluated_test_queries_by_sentence_id(self, sentence_id, oracle_id):
        """Retrieve test queries without an oracle decision."""
        return sqlio.read_sql_query(
            f"Select * from test_query tq where sentence_id = {sentence_id} "
            f"and not EXISTS(select * from oracle_result ores where "
            f"tq.id = ores.query_id and ores.id = {oracle_id})",
            self.__connection)

    def get_model_parameters_by_sentence_id_as_df(self, sentence_id):
        """Retrieve model parameters for a given sentence ID as dataframe."""
        return sqlio.read_sql_query(
            f"Select * from model_parameter where sentence_id = {sentence_id}",
            self.__connection)

    def get_query_count_by_sentence_id(self, sentence_id):
        """Fetch the number of test queries for a sentence ID."""
        cursor = self.__connection.cursor()
        cursor.execute(
            "Select count(*) from test_query where sentence_id = %s",
            (sentence_id,))
        self.__connection.commit()  # XXX Probably not needed?
        return cursor.fetchone()[0]

    def get_filtered_sentence_ids(self, filter_args: dict):
        """Get sentence IDs based on model parameters.

        If filter_args is not empty, each key is used in a LIKE
        clause as the parameter name and its associated value is
        used in a LIKE clause selecting the parameter value.

        This method is vulnerable to SQL injections."""
        query = "select ts.id from test_sentence ts where"
        for k in filter_args:
            query += f" exists(select * from model_parameter mp where "
            query += f"mp.sentence_id = ts.id and parameter like '{k}'"
            query += f" and value like '{filter_args[k]}') and"
        query = query[:-4]
        return sqlio.read_sql_query(query, self.__connection)

    def get_connection(self):
        """Get current database connection."""
        return self.__connection

    def get_complete_data_by_oracle_id(self, oracle_id):
        """Retrieve all verdicts by a specific oracle ID."""
        return sqlio.read_sql_query(
            "Select ts.id as sentence_id, sentence, correct_answer_label, "
            "tq.id as query_id, modified_question, new_response, result "
            "from test_sentence ts join test_query tq on ts.id = tq.sentence_id"
            " join oracle_result ores on tq.id = ores.query_id "
            f"where ores.oracle_id = {oracle_id}", self.__connection)

    def get_test_data(self):
        """Retrieve the question/response of a test and the correct answer."""
        return sqlio.read_sql_query(
            "Select ts.id as sentence_id, sentence, correct_answer_label, "
            "tq.id as query_id, modified_question, new_response, ca_file "
            "from test_sentence ts join test_query tq on ts.id = tq.sentence_id",
            self.__connection)

    def get_test_data_until_sentence(self, sentence_id):
        """Retrieve question/response and correct answer up to a sentence ID."""
        return sqlio.read_sql_query(
            "Select ts.id as sentence_id, sentence, correct_answer_label, "
            "tq.id as query_id, modified_question, new_response, ca_file "
            "from test_sentence ts join test_query tq on ts.id = tq.sentence_id "
            f"where ts.id <= {sentence_id}", self.__connection)

    def get_test_data_by_oracle_id(self, oracle_id):
        """Retrieve all question/responses and correct answers for an oracle."""
        return sqlio.read_sql_query(
            "Select ts.id as sentence_id, sentence, correct_answer_label, "
            "tq.id as query_id, modified_question, new_response "
            "from test_sentence ts join test_query tq on "
            "ts.id = tq.sentence_id join oracle_result ores on "
            f"tq.id = ores.query_id where ores.oracle_id = {oracle_id}",
            self.__connection)

    def get_test_data_by_sentence_id(self, sentence_id):
        """Retrieve question/response/correct answers based on a sentence."""
        return sqlio.read_sql_query(
            "Select ts.id as sentence_id, sentence, correct_answer_label, tq.id"
            " as query_id, modified_question, new_response from test_sentence "
            "ts join test_query tq on ts.id = tq.sentence_id join "
            "oracle_result ores on tq.id = ores.query_id "
            f"where ts.id = {sentence_id}", self.__connection)
