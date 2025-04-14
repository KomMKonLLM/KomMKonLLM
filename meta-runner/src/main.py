"""Meta runner for KomMKonLLM.

This is the primary entrypoint that conducts the process of LLM consistency
testing. It loads sentences (questions) to be tested, generates mutated
versions of these questions and submits them to a LLM, then stores
the responses."""
import json
import logging
from os import getenv
import time
import sys
from payload_generator.payload_generator import (
    generate_synonyms,
    consume_payload_from_ca,
    generate_ca,
)
from requests.models import PreparedRequest
import requests
from bs4 import BeautifulSoup

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def prepare_prompt(query):
    """Prepare the prompt by surrounding the query with postfix/prefix."""
    prompt_prefix = ""
    prompt_postfix = ""
    if getenv("USE_PREFIX", "").lower() == "true":
        prompt_prefix = getenv("PROMPT_PREFIX")
    if getenv("USE_POSTFIX", "").lower() == "true":
        prompt_postfix = getenv("PROMPT_POSTFIX")
    return prompt_prefix + query + prompt_postfix

def store_result(prompt, result):
    """Store a LLM response."""
    return requests.post(
        f"http://{getenv('STORAGE_HOST')}:{getenv('STORAGE_PORT')}/"
        "store/test_query",
        json={
            "modified_question": prompt,
            "new_response": result
        },
        headers={"Content-Type": "application/json"},
        timeout=64
    )

def perform_query(query):
    """Query a LLM and store its response."""
    prompt = prepare_prompt(query)
    executor_req = PreparedRequest()
    executor_req.prepare_url(
        f"http://{getenv('EXECUTOR_HOST')}:{getenv('EXECUTOR_PORT')}/query/"
        f"{getenv('MODEL_UNDER_TEST')}", {"prompt": prompt})
    logging.debug("perform_query() Calling executor via: %s", executor_req.url)
    request_successful = False
    retry_counter = 0
    execute_res = None

    while (not request_successful) and retry_counter < 10:
        try:
            execute_res = requests.get(executor_req.url, timeout=64)
            request_successful = True
        except Exception:
            logging.info('Request %s failed, retrying in 10s', executor_req.url)
            time.sleep(10)
            retry_counter += 1
            continue
    if execute_res and execute_res.status_code == 200:
        logging.debug('Storing result: %s => %s', prompt, execute_res.text)
        store_result(prompt, execute_res.text)
    else:
        logging.error(
            "Executor responded with status code %s and response %s (%s)",
            execute_res.status_code, execute_res.text, executor_req.url
        )

def find_last_sentence():
    """Identify the last tested sentence (in its non-mutated form)."""
    try:
        stored_sentences = requests.get(
            f"http://{getenv('STORAGE_HOST')}:{getenv('STORAGE_PORT')}/"
            "load/test_sentences", timeout=64)
        stored_sentences_soup = BeautifulSoup(
            stored_sentences.text, features='html.parser')
        last_tr = stored_sentences_soup.find_all("tr")[-1]
        last_td = last_tr.find_all("td")[1]
        return last_td.text
    except Exception as e:
        logging.error(
            "Could not find a sentence to continue from "
            "(maybe this is the first run?): %s", e)
    return None

def create_test_sentence_data(question, answer, passage, strength):
    """Prepare test sentence data for DB storage."""
    return {
        "sentence": question,
        "original_response": passage,
        "correct_answer_label": answer,
        "ipm_vector_notation": "",
        "source_data_name": "",
        "model_name": getenv("MODEL_UNDER_TEST"),
        "ca_file": "",
        "ipm_file": "",
        "ipm_description_file": "",
        "strength": strength,
        "note": getenv("EXECUTION_NOTE", ""),
    }

if __name__ == "__main__":
    # Main functionality
    # If we want to continue a previous run, first find the last tested sentence
    last_sentence = None
    reached_last_stop = False
    if getenv("CONTINUE_RUN", "").lower() == "true":
        last_sentence = find_last_sentence()
    strength = int(getenv("STRENGTH", "2"))

    # Open the list of questions, with one JSON object per line
    # Each object should have the following properties:
    # - `question`, the question text
    # - `answer`, a boolean string ("true" or "false")
    # - `passage`, additional explanatory notes
    with open("train.jsonl", mode="r", encoding="utf-8") as f:
        for index, line in enumerate(f):
            obj = json.loads(line)

            # If we want to continue from a previous sentence, skip until then
            if last_sentence and not reached_last_stop:
                if obj["question"] != last_sentence:
                    continue
                reached_last_stop = True

            # Create test sentence data and available synonyms
            logging.debug("Starting test sentence '%s'", str(obj["question"]))
            test_sentence_data = create_test_sentence_data(obj["question"],
                                                           obj["answer"],
                                                           obj["passage"],
                                                           strength)
            synonyms = generate_synonyms(obj["question"])
            test_sentence_data["ipm_file"] = json.dumps(synonyms)

            # Generate a covering array (CA) as the LLM test set
            ca_filename, ca_size = generate_ca(synonyms, strength)
            with open(ca_filename, 'r', encoding='utf-8') as fp:
                test_sentence_data["ca_file"] = fp.read()

            # Store the test sentence in the database
            res = requests.post(
                f"http://{getenv('STORAGE_HOST')}:{getenv('STORAGE_PORT')}/"
                "store/test_sentence",
                json=test_sentence_data,
                headers={"Content-Type": "application/json"},
                timeout=64
            )

            # Translate each row in the CA to a natural language query
            # and submit it to the LLM
            for ca_line in consume_payload_from_ca(synonyms, strength):
                logging.debug("Starting test query '%s'", ca_line)
                perform_query(ca_line)
