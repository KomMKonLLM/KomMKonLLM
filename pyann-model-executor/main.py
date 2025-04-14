"""Flask app to query LLMs and update their settings.

Developers who have implemented a new LLM interface should add it to the
`models` variable below."""

import logging
import json
from os import getenv
from flask import Flask, Response, request
from models import T5Executor, LlamaExecutor, OllamaExecutor

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(getenv('LOG_LEVEL', default='DEBUG'))
logger.propagate = True
models = {'LLAMA': LlamaExecutor(), 'T5': T5Executor(), 'OLLAMA': OllamaExecutor()}
app = Flask(__name__)

@app.route('/models', methods=['GET'])
def show_models():
    """List available models."""
    model_names = '\n'.join([f'<li>{k}</li>' for k in models])
    return f'<h1>Available models:</h1>\n<ul>{model_names}</ul>'

@app.route('/query/<model>', methods=['GET'])
def query(model: str):
    """Query a LLM with the input provided as the `prompt` GET parameter."""
    if not model in models:
        logging.error('Trying to query nonexistent model %s', model)
        return Response('Model does not exist.', status=400, mimetype='text/plain')

    prompt = request.args.get('prompt')
    if not prompt:
        logging.error('Received prompt-less query to model %s', model)
        return Response('Please specify a prompt.', status=400, mimetype='text/plain')

    logging.debug('Prompt for %s: %s', model, prompt)
    res = models[model].query(prompt)
    logging.debug('Sending response %s', res)
    return res

@app.route('/<model>/settings', methods=['POST'])
def settings(model: str):
    """Update and return a LLM's settings."""
    if not model in models:
        logging.error('Trying to query nonexistent model %s', model)
        return Response('Model does not exist.', status=400, mimetype='text/plain')

    ret = models[model].set_settings(request.get_json(force=True))
    return json.dumps(ret)

if __name__ == '__main__':
    port = int(getenv('SERVICE_PORT', default='4200'))
    app.run('0.0.0.0', port=port)
    logger.info('LLM Model Executor listening on port %s', port)
