create table if not exists test_sentence
(
    id                        SERIAL primary key,
    sentence                  text,
    date                      date default CURRENT_DATE,
    correct_answer_label      text,
    ipm_vector_notation       text,
    source_data_name          text,
    model_name                text,
    ca_file                   text,
    ipm_file                  text,
    ipm_description_file      text,
    strength                  integer,
    note                      text
);

create table if not exists test_query
(
    sentence_id       int REFERENCES test_sentence (id),
    id                SERIAL unique,
    modified_question text,
    new_response      text,
    primary key (sentence_id, id)
);

create table if not exists oracle_description
(
    id          SERIAL primary key,
    name        text,
    description text
);

insert into oracle_description (id, name, description) values (
       1,
       'Default Oracle',
       'Simple heuristic conversion to boolean'
) on conflict do nothing;

create table if not exists oracle_result
(
    id          SERIAL unique,
    query_id    int REFERENCES test_query (id),
    oracle_id   int REFERENCES oracle_description (id),
    result      text,
    primary key (query_id, id, oracle_id)
);

create table if not exists model_parameter
(
    id          SERIAL unique,
    sentence_id int REFERENCES test_sentence (id),
    parameter   text,
    value       text,
    primary key (id, sentence_id)
);
