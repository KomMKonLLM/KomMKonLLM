"""LLM model interfaces.

This module contains the ModelExecutor class and its subclasses.
They offer a common interface to query a LLM and update or retrieve
its settings.

To implement your own LLM interface, create your own subclass of
ModelExecutor and implement at least the query() method."""

from os import getenv
import json
import logging
import requests
import socketio

# Logger configuration
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = True
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

class ModelExecutor:
    """Model executor abstract class.

    Allows callers to query a LLM and update/retrieve its settings.
    Do not use this class directly, except when implementing subclasses."""
    def query(self, prompt: str) -> str | bool:
        """Query the model with the given string."""
        raise NotImplementedError(
            "ModelExecutor::query() must not be accessed directly"
        )

    def set_settings(self, settings: dict) -> dict:
        """Update the model settings."""
        return {}

    def get_settings(self) -> dict:
        """Retrieve the current model settings."""
        return {}

class OllamaExecutor(ModelExecutor):
    """Executor for Ollama models.

    Ollama offers a common interface to multiple LLMs.
    You can choose which LLM to use by setting the OLLAMA_MODEL environment
    variable."""
    def __init__(self):
        """Set model parameters and default values."""
        self.settings = {
            'seed': 1337,
            'temperature': 0.1
        }
        self.model = getenv('OLLAMA_MODEL', default='llama3.2')
        self.endpoint = getenv('MODEL_IP', default='ollama:11434')
        self.enabled_models = []
        self.model_prefix = 'test-'

    def query(self, prompt: str) -> str:
        """Query the model with the given string."""
        if self.model not in self.enabled_models:
            self.setup()
        model = self.model_prefix + self.model
        params = {
            'model': model,
            'prompt': prompt,
            'format': 'json',
            'stream': False,
            'options': self.settings.copy()
        }
        response = requests.post(f'http://{self.endpoint}/api/generate',
                                 json=params, timeout=64).text
        try:
            # Try to decode as JSON; return as-is otherwise
            decoded = json.loads(response)
        except:
            return response
        try:
            # Try to extract response property from JSON;else return full object
            resp = decoded['response']
        except:
            return decoded
        try:
            # Try to decode inner JSON; return full property otherwise
            decoded_inner = json.loads(resp)
        except:
            return resp
        for _, val in decoded_inner.items():
            # Find the first boolean property and return it.
            if isinstance(val, bool):
                return str(val)
        # There was no boolean property, return entire object
        return decoded_inner

    def setup(self):
        """Enable the requested model"""
        if self.model in self.enabled_models:
            logging.debug('Model %s already enabled, skipping.', self.model)
            return # Already done
        output_model = self.model_prefix + self.model
        params = {"model": output_model, "from": self.model}
        logging.info('Creating local model %s from %s...', output_model, self.model)
        response = requests.post(f'http://{self.endpoint}/api/create',
                                 json=params, timeout=32).text
        logging.debug('Ollama create response: %s', response)
        self.enabled_models.append(self.model)
        logging.debug('Enabled model %s.', output_model)

    def set_settings(self, settings: dict) -> dict:
        """Update the model settings."""
        self.settings = settings
        return self.settings

    def get_settings(self) -> dict:
        """Retrieve the current model settings."""
        return self.settings

class T5Executor(ModelExecutor):
    """Executor for T5 (deprecated).

    This is intended to be used in combination with t5-flask-app.
    Future developments should use Ollama instead."""
    def __init__(self):
        """Set model parameters and default values."""
        self.settings = {
            'early_stopping': True,
            'max_length': 50,
            'num_beam': 2
        }
        self.endpoint = getenv('MODEL_IP', default='t5:5069')

    def query(self, prompt: str) -> str:
        """Query the model with the given string."""
        params = self.settings.copy()
        params['prompt'] = prompt
        return requests.get(f'http://{self.endpoint}/query',
                            params=params, timeout=16).text

    def set_settings(self, settings: dict) -> dict:
        """Update the model settings."""
        self.settings = settings
        return self.settings

    def get_settings(self) -> dict:
        """Retrieve the current model settings."""
        return self.settings

class LlamaExecutor(ModelExecutor):
    """Executor for a self-hosted Llama instance (deprecated).

    Future developments should use Ollama instead."""
    def __init__(self):
        """Set model parameters and default values."""
        self.settings = {
            'seed': 42069,
            'threads': 4,
            'n_predict': 3,
            'model': '7B',
            'top_k': 40,
            'top_p': 1,
            'temp': 0.001,
            'repeat_last_n': 64,
            'repeat_penalty': 1.3,
            'models': ['13B', '30B', '65B', '7B'],
        }
        self.socket = socketio.SimpleClient()
        self.model_ip = getenv('SELF.MODEL_IP')

    def query(self, prompt: str) -> str:
        """Query the model with the given string."""

        # XXX Dirty, socketio.SimpleClient does not expose its `connected` property publicly
        if not self.socket.connected:
            self.socket.connect(f'http://{self.model_ip}', transports=['websocket'])
            logging.debug('Connected to Llama at %s', self.model_ip)

        params = self.settings.copy()
        params['prompt'] = prompt
        self.socket.emit('request', params)
        logging.debug('Sent request to Llama')
        event = self.socket.receive()
        logging.debug('Received response from Llama: "%s" with arguments %s}',
                      event[0], event[1:])
        return event[1:]

    def set_settings(self, settings: dict) -> dict:
        """Update the model settings."""
        self.settings = settings
        return self.settings

    def get_settings(self) -> dict:
        """Retrieve the current model settings."""
        return self.settings
