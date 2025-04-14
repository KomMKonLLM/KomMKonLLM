-- Insert data into test_sentence table
INSERT INTO test_sentence (sentence, correct_answer_label, ipm_vector_notation, source_data_name, model_name, ca_file_name, ipm_file_name, ipm_description_file, strength, note)
VALUES ('This is a test sentence 1.', 'true', 'IPM vector notation 1', 'Source data name 1', 'Model name 1', 'CA file name 1', 'IPM file name 1', 'IPM description file name 1', 10, 'Note 1'),
       ('This is a test sentence 2.', 'false', 'IPM vector notation 2', 'Source data name 2', 'Model name 2', 'CA file name 2', 'IPM file name 2', 'IPM description file name 2', 8, 'Note 2'),
       ('This is a test sentence 3.', 'true', 'IPM vector notation 3', 'Source data name 3', 'Model name 3', 'CA file name 3', 'IPM file name 3', 'IPM description file name 3', 6, 'Note 3');

-- Insert data into test_query table
INSERT INTO test_query (sentence_id, modified_question, new_response)
VALUES (1, 'Modified question 1', 'yes'),
       (1, 'Modified question 7', 'yes'),
       (1, 'Modified question 2', 'no'),
       (2, 'Modified question 3', 'yes'),
       (2, 'Modified question 4', 'yes'),
       (3, 'Modified question 5', 'yes'),
       (3, 'Modified question 6', 'yes');

-- Insert data into oracle_description table
INSERT INTO oracle_description (name, description)
VALUES ('Oracle description 1', 'Description for Oracle 1.'),
       ('Oracle description 2', 'Description for Oracle 2.');

-- Insert data into oracle_result table
INSERT INTO oracle_result (query_id, oracle_id, result)
VALUES (1, 1, 'true'),
       (1, 2, 'true'),
       (2, 1, 'true'),
       (2, 2, 'false'),
       (3, 1, 'false'),
       (3, 2, 'false');

-- Insert data into model_parameter table
INSERT INTO model_parameter (sentence_id, parameter, value)
VALUES (1, 'Parameter 1', 'Value 1'),
       (1, 'Parameter 2', 'Value 2'),
       (2, 'Parameter 3', 'Value 3');
