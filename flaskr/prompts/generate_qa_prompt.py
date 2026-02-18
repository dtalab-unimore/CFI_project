prompt_topic = """Given some data of a course, like video transcriptions, documents or syllabus, generate a list of {num_questions} multiple-choice questions (with {num_multiple_answers} answers) about the {topic_text} topic.
The questions MUST BE in the following language: {language}.
The questions must be grounded on the given material, and must not ask things that are not indicated in the materials.
You must not have verbosity bias: the correct answer must not always be the longest answer out of all the options.
The questions must be of the following typology:
    - {question_description}
    
Generate directly the list of questions in the following manner. Write exactly "Final answer:" followed by a Python list, containing Python dictionaries in the following format:

{{
    "question": ..., # string containing the question text
    "answers": ..., # list containing {num_multiple_answers} answers. The answers do not contain the text indicating the options (e.g. "a)", "i)" etc.)
    "correct_answer": ..., # position in the list of the correct answer. The positioning must use Python indexing (starting from 0 to n-1)
    "question_type": ..., # string indicating the question type name, based on the different question typologies listed earlier
}}

Strictly follow the requirements, making questions about the {topic_text} topic, with the correct question typology and with the correct {language} language.
To generate the questions, follow exactly the response format. Do not write anything else after "Final answer:"

# Materials

{materials}

"""

prompt_wo_topic = """Given some data of a course, like video transcriptions, documents or syllabus, generate a list of {num_questions} multiple-choice questions (with {num_multiple_answers} answers).
The questions MUST BE in the following language: {language}.
The questions must be grounded on the given material, and must not ask things that are not indicated in the materials.
You must not have verbosity bias: the correct answer must not always be the longest answer out of all the options.
The questions must be of the following typology:
    - {question_description}

Generate directly the list of questions in the following manner. Write exactly "Final answer:" followed by a Python list, containing Python dictionaries in the following format:

{{
    "question": ..., # string containing the question text
    "answers": ..., # list containing {num_multiple_answers} answers. The answers do not contain the text indicating the options (e.g. "a)", "i)" etc.)
    "correct_answer": ..., # position in the list of the correct answer. The positioning must use Python indexing (starting from 0 to n-1)
    "question_type": ..., # string indicating the question type name, based on the different question typologies listed earlier
}}

Strictly follow the requirements, making questions with the correct question typology and with the correct {language} language.
To generate the questions, follow exactly the response format. Do not write anything else after "Final answer:"

# Materials

{materials}

"""