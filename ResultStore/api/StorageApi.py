"""A Flask application exposing the storage API."""
from flask import Flask, request, Response
from services import DatabaseService
from entities import ModelParameter, TestQuery, TestSentence
from services.ConfigParser import *
import threading

app = Flask(__name__)

@app.route("/store/test_sentence", methods=['POST'])
def store_test_sentence():
    """Store a tested sentence including its synonym IPM and resulting CA."""
    req = request.json
    DatabaseService.save_test_sentence(
        TestSentence(-1, req["sentence"], req["correct_answer_label"],
                     req["ipm_vector_notation"], req["source_data_name"],
                     req["model_name"], req["ca_file"], req["ipm_file"],
                     req["ipm_description_file"], req["strength"], req["note"])
    )
    return "Success"


@app.route("/store/test_query", methods=['POST'])
def store_test_query():
    """Store a mutated question and the resulting LLM response."""
    request_data = request.json
    DatabaseService.save_test_query(
        TestQuery(DatabaseService.get_current_run_id(),
                           request_data["modified_question"],
                           request_data["new_response"])
    )
    return "Success"


@app.route("/store/model_parameters", methods=['POST'])
def store_model_parameters():
    """Store model parameters as key-value pairs."""
    request_data = request.json
    run_id = DatabaseService.get_current_run_id()
    for parameter, value in request_data:
        DatabaseService.save_model_parameters(
            ModelParameter(run_id, parameter, value)
        )
    return "Success"


@app.route("/load/test_sentences", methods=['GET'])
def load_test_sentences():
    """Retrieve all (original) test sentences from the database."""
    sentences = DatabaseService.get_test_sentences()
    return_type = request.args.get("return_type", "html")
    if return_type == "json":
        return Response(sentences.to_json(orient="records"), mimetype='application/json')
    else:
        return sentences.to_html()


@app.route("/load/oracle_results", methods=['GET'])
def load_oracle_results():
    """Retrieve oracle results from the database."""
    oracle_results = DatabaseService.get_oracle_results()
    return_type = request.args.get("return_type", "html")
    if return_type == "json":
        return Response(oracle_results.to_json(orient="records"), mimetype='application/json')
    else:
        return oracle_results.to_html()


@app.route("/load/oracle_descriptions", methods=['GET'])
def load_oracle_descriptions():
    """Retrieve oracles and their description."""
    oracle_descriptions = DatabaseService.get_oracle_descriptions()
    return_type = request.args.get("return_type", "html")
    if return_type == "json":
        return Response(oracle_descriptions.to_json(orient="records"), mimetype='application/json')
    else:
        return oracle_descriptions.to_html()


@app.route("/load/test_queries", methods=['GET'])
def load_test_queries():
    """Retrieve all mutated sentences by the `sentence_id` GET parameter."""
    sentence_id = int(request.args["sentence_id"])
    queries = DatabaseService.get_test_queries_by_sentence_id(sentence_id)
    return_type = request.args.get("return_type", "html")
    if return_type == "json":
        return Response(queries.to_json(orient="records"), mimetype='application/json')
    else:
        return queries.to_html()


@app.route("/load/model_parameters", methods=['GET'])
def load_model_parameters():
    """Load the parameters of a LLM by a `sentence_id` GET parameter."""
    sentence_id = int(request.args["sentence_id"])
    model_parameters = DatabaseService.get_model_parameters(sentence_id)
    return_type = request.args.get("return_type", "html")
    if return_type == "json":
        return Response(model_parameters.to_json(orient="records"), mimetype='application/json')
    else:
        return model_parameters.to_html()

def start_server():
    """Run Flask app on the port given by the SERVICE_PORT env variable."""
    global port
    app.run(host="0.0.0.0", port=SERVICE_PORT)

# Start the server in a thread
threading.Thread(target=start_server).start()
