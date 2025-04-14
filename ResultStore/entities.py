"""Classes representing all data types in the result store."""
from dataclasses import dataclass

@dataclass
class ModelParameter:
    """Key/value pair representing a LLM parameter for a test run."""
    sentence_id: int = -1  # Test run ID
    parameter: str = None  # Key/parameter
    value: str = None      # Value/parameter value


@dataclass
class OracleDescription:
    """Metadata of a particular oracle."""
    id: int = -1             # Unique oracle ID
    name: str = None         # Oracle name
    description: str = None  # Oracle description


@dataclass
class OracleResult:
    """Oracle verdict regarding a particular query."""
    id: int = -1                  # Unique ID
    oracle_id: int = -1           # Oracle ID
    query_id: int = -1            # Query ID
    result: str | None = None     # Oracle verdict

    def __str__(self) -> str:
        return f'QID: {self.query_id} Result: {self.result}'

@dataclass
class TestQuery:
    """A question/answer pair based on a mutated test sentence."""
    sentence_id: int = -1          # ID of the original sentence
    modified_question: str = ""    # Mutated question including prompt prefix/suffix
    new_response: str = ""         # Returned response


@dataclass
class TestSentence:
    """A sentence to be used as a basis for testing LLMs."""
    id: int = -1                     # Unique ID
    sentence: str = ""               # The test sentence
    correct_answer_label: str = ""   # The correct answer
    ipm_vector_notation: str = ""    # XXX Unused
    source_data_name: str = ""       # Name of source data set
    model_name: str = ""             # Name of the LLM under test
    ca_file: str = ""                # Contents of the underlying CA
    ipm_file: str = ""               # Contents of the input parameter model
    ipm_description_file: str = ""   # Description of input parameter model variant
    strength: int = 2                # Tested combinatorial strength
    note: str = ""                   # Additional note for this test run
