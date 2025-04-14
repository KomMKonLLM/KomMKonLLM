# Combinatorial Methods for Consistency Testing of Large Language Models

This project enables the use of combinatorial testing methods for evaluating the consistency of LLMs. It allows developers and users to investigate:

* How consistent is a particular LLM when parts of prompts are replaced with synonyms?
* Which LLM is best for a particular set of questions?
* What are the capabilities of an LLM regarding instructions that restrict its output format?

## Who is KomMKonLLM for?

Our work on the consistency of large language models is not only aimed at 
science and research, but also in particular at companies that (want to) 
integrate or use LLMs in their product development or services and want to 
ensure that a certain degree of consistency - and in a wider sense accuracy - of 
the results is given.

## What does consistency testing mean?

Consistency testing of LLMs addresses the problem of ensuring that LLMs respond 
reliably to different inputs. Since LLMs often have complex and opaque 
structures, they can give inconsistent or unexpected answers to similar inputs. 
These inconsistencies make it difficult to use LLMs in applications where 
reliability is crucial. The challenge is to develop suitable test methods that 
systematically evaluate the consistency of the models.

## Challenges

Especially when testing the semantic complexity of LLMs, it is extremely 
challenging to cover the many possible variations in the formulation of input 
queries. We will therefore use automated methods of combinatorial testing, which 
have the advantage of covering the modelled input space (in this case a written 
sentence and the ways of formulating it) to a certain predetermined degree - in 
a certain combinatorial sense.

## How does it work?

We want to create a server solution that automatically creates consistency tests 
for LLMs using combinatorial methods, executes them on LLM instances via open 
interfaces and can also display the results in a prepared form. Together with an 
integrated repository of test cases, this offers a solution for combinatorial 
testing of the consistency of LLMs.

## Who is behind the project?

KomMKonLLM is a project funded by [netidee](https://www.netidee.at/kommkonllm) and implemented by the [MATRIS Research Group](https://matris.sba-research.org/) of SBA Research.

## Executive Summary / Testing Process

Based on a user-defined list of questions and answers, our implementation derives synonyms for most types of words. 
It then utilizes a discrete mathematical structure called a covering array to create a diversified set of questions.
Each of the entries in this set is then submitted to an LLM and its response is normalized.
An oracle can subsequently be applied to the responses to evaluate the _precision_, _recall_, _F1 score_ and overall consistency of the LLM.

The diagram below shows the KomMKonLLM System Architecture, consisting of:

* A central runner that controls the process,
* a model interface that offers a unified way to communicate with LLMs,
* an external covering array generator,
* a set of questions to evaluate against,
* a database of synonyms provided by included libraries,
* a database to store evaluation results in.

![KomMKonLLM System Architecture, consisting of a central runner that steers the process, a model interface that offers a unified way to communicate with LLMs, an external covering array generator, and a set of questions to evaluate against. Additionally, a database of synonyms is provided by included libraries. Results are stored in a database.](architecture.png "KomMKonLLM system architecture")

## Setup

To run the KomMKonLLM suite, you only need Docker and Docker Compose.
More recent versions of Docker include Compose by default; for older versions, you will need to install the `docker-compose` plugin.

Performance requirements are generally dominated by the LLM you wish to use; in general, a minimum of 10GB free disk space should be sufficient for small models.

### Building

To build the environment (either initially or after you have made changes to the source code),
clone this repository or download its contents.
Navigate into the folder that contains this file and execute:

``` sh
# Newer versions of Docker
docker compose build

# Older versions 
docker-compose build
```

Depending on your hardware and internet performance, it will roughly take a minute to an hour to perform the initial build.
Subsequent builds will reuse existing unchanged components and thus complete much faster.

### Configuration

Configuration options are defined using environment parameters in the file `docker-compose.yaml`.
Almost all are defined in the `environment` block of the `meta_runner` container.

The most important ones are:

* `CONTINUE_RUN`: If set to `true`, the framework will try to identify the last tested sentence in the previous test run and continue from there.
* `EXECUTION_NOTE`: A user-defined note to be attached to all sentences tested for this run.
* `MODEL_UNDER_TEST`: Which model interface to use. In most cases, you should use `OLLAMA` here. `T5` and `LLAMA` are also available, but deprecated.
* `USE_POSTFIX` and `USE_PREFIX`: If set to `true`, the given prompt postfix/prefix will be added to each prompt.
* `PROMPT_POSTFIX` and `PROMPT_PREFIX`: A string to append/prepend to queries, e.g. to add further instructions to the LLM.
* `CA_GENERATOR`: Which CA generator to use (see below). Allowed values are `CAGEN`, `ACTS` and `PICT`.
* `CA_GENERATOR_PATH`: Location of the CA generator executable in the `meta-runner` directory.
* `STRENGTH`: The combinatorial strength to generate CAs with. If you are unsure, use `2` here.

Additionally, the sentences to be tested must be mounted as `/app/train.jsonl` in the `meta_runner` container. You can either edit this file directly (and ensure that it is not overwritten in the `volumes` section of the `meta_runner` container) or create your own file and mount it as a volume, e.g.:

``` yaml
volumes:
    - ./my-own-questions.jsonl:/app/train.jsonl
```

See the **Questions/Answers** section below regarding the format of this file.

Depending on the model under test, you may need to add or configure additional containers.

For the `executor` container, the `MODEL_IP` environment parameter must point to the hostname and port of the individual LLM you want to communicate with (commonly, this will be the name of one of your other containers plus the port its model listens on).

If your `MODEL_UNDER_TEST` is set to `OLLAMA`, the `executor` container additionally requires a `OLLAMA_MODEL` environment variable to be set to the name of a model, e.g. `llama3.2`. You can find a list of available models on the Ollama [GitHub repository](https://github.com/ollama/ollama?tab=readme-ov-file#model-library) or on the dedicated [Ollama library page](https://ollama.com/library).

#### CA generators

Our framework supports three covering array generators:

* CAgen: This is the fastest general-purpose CA generator. A web version is available [here](https://srd.sba-research.org/tools/cagen/), although it is only single-threaded. However, the command line version is only available upon individual request.
* ACTS: Developed by NIST, ACTS is the most popular CA generator. It is available in a basic version at the [NIST combinatorial testing tools](https://csrc.nist.gov/projects/automated-combinatorial-testing-for-software/downloadable-tools) site and in an enhanced version upon request.
* PICT: Microsoft's Pairwise Independent Combinatorial Tool is [available on GitHub](https://github.com/microsoft/pict). It is mostly suitable for testing at strength 2, although it supports higher strengths at reduced performance. Note that you must build the executable yourself according to the instructions in the repository.

Place the executable (which will likely be called `cagen`, `fipo-cli`, `acts.jar` or `pict`) in a subfolder of the `meta-runner` folder and adjust the `CA_GENERATOR` and `CA_GENERATOR_PATH` environment variables in `docker-compose.yaml` as required.

### Questions/Answers

Our framework requires a list of questions and associated answers to be provided as a text file.
This file must contain one JSON object per line, each of which must have the following properties:

* `question`: A string defining a question.
* `answer`: The correct answer. **Note that only boolean questions are supported at the moment.** This property should thus be a boolean, not a string.
* `passage`: Auxiliary information to explain the answer. You may use an empty string here.

## Running

Once you have provided a list of question-answer pairs, built the Docker Compose environment and performed any additional configuration, you can start the framework using:

``` sh
# Newer versions of Docker
docker compose up --abort-on-container-exit

# Older versions 
docker-compose up --abort-on-container-exit
```

You can monitor the console output to see the testing process in action and identify any issues that may arise.

Once this process has finished, you might want to change the `MODEL_UNDER_TEST` and `EXECUTION_NOTE` variables in your `docker-compose.yaml` and re-run your tests for a different model.

### Analysis

*Note: If you are running your Docker environment on a server, you need to forward port 8888 from the server's localhost to your own using SSH.*
*If you usually log in to your server using `ssh user@my.server.com`, try `ssh -L 8888:localhost:8888 user@my.server.com` instead.*

After you have finished running the testing process for all models, it is time to analyze the results.
This requires the `db` and `store` Docker containers, which you can start separately without invoking the rest of the infrastructure:

``` sh
# First, we need to start the database
docker start db
# Next, we start the store.
# Note the parameter -a, which attaches the console.
# This is required because you need the link printed by the container.
docker start -a store
```

The `store` container will print URLs containing a token that allows you to access the JupyterLab notebook used for analysis; look for a message that contains "copy and paste one of these URLs". You need the URL under `http://127.0.0.1`.

Open the URL in a browser and access the `Visualization.ipynb` entry. The existing contents of this notebook should be fairly self-explanatory and can be modified and extended at your convenience.

## Extending

If you want to extend KomMKonLLM or are interested in gaining a better overview of the code structure, please see [HACKING.md](HACKING.md).

If you have developed a new interface and think it would be useful for others, please do not hesitate to create a pull request!

## Further comments?

Please feel free to reach out to us, either via mail (kommkonllm at sba-research.org), social media (https://bsky.app/profile/kommkonllm.bsky.social) or by creating an issue in this repository!
