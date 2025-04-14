"""Runs a T5 LLM based on huggingface's triviaqa-t5-base model."""

import logging
from os import getenv
from flask import Flask, request, Response
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

logging.basicConfig(level=0)
LOG = logging.getLogger(__name__)

MODEL_INITIALIZED = False
TOKENIZER = None
MODEL = None
device = torch.device("cpu")

app = Flask(__name__)

def init_model():
    """Initialize the model and its associated tokenizer."""
    LOG.info("Starting to initialize ANNs. Get some coffee, this will take a while")

    global TOKENIZER
    global MODEL
    TOKENIZER = AutoTokenizer.from_pretrained("deep-learning-analytics/triviaqa-t5-base")
    MODEL = AutoModelForSeq2SeqLM.from_pretrained("deep-learning-analytics/triviaqa-t5-base")
    MODEL = MODEL.to(device)

    LOG.info("Done initializing models. How was your coffee?")
    global MODEL_INITIALIZED
    MODEL_INITIALIZED = True

@app.route("/verify")
def verify():
    """Return HTTP 200 if the underlying model is initialized, 500 otherwise."""
    global MODEL_INITIALIZED
    if MODEL_INITIALIZED:
        return 'OK'
    return app.make_response(('FAIL', 500))

def query_t5(input_query: str, max_length: int, num_beams: int, early_stopping: bool):
    """Query the LLM and return its textual response."""
    tokens = TOKENIZER.encode(
        input_query.strip().replace("\n", " "), return_tensors="pt"
    ).to(device)
    return "".join([
        TOKENIZER.decode(t) for t in MODEL.generate(
            tokens, max_length, num_beams, early_stopping)
        ])

@app.route('/')
def index():
    """Display a help page."""
    return """
    <h1> T5 Model</h1>
    <p>Query with the endpoint /query?prompt=PROMPT IN URLENCODING </p>
    <p>Parameters (provided with query params):</p>
    <ul>
        <li>maxLength default: 50</li>
        <li>numBeams default: 2</li>
        <li>earlyStopping default: True</li>
    </ul> <br>
    """

@app.route('/query', methods=["GET"])
def query():
    """HTTP endpoint to perform a query and return the LLM response."""
    if not request.args.get("prompt"):
        return Response("please specify a prompt", status=400, mimetype="text/plain")

    max_length = request.args.get("maxLength", default=50, type=int)
    num_beams = request.args.get("numBeams", default=2, type=int)
    early_stopping = request.args.get("earlyStopping", default=True, type=bool)

    ret = query_t5(request.args.get("prompt", default=""), max_length, num_beams, early_stopping)
    LOG.debug('T5 returning result "%s"', ret)
    return ret


if __name__ == "__main__":
    # Initialize the model and start the HTTP server
    T5_PORT = int(getenv("T5_PORT", default='5069'))
    init_model()
    app.run("0.0.0.0", port=T5_PORT)
    LOG.info("Started T5 service. Listening for host:%s/query?prompt=<PROMPT>", T5_PORT)
