prompt_generate_feedback = """Given the materials, the questions and answers, the amount of errors, the broad topic of the questions, and the subtopics where the user is lacking knowledge, you must generate a feedback to provide to the user.
You must indicate:
1. the general result of the test, including the amount of errors;
2. The subtopics where the user is currently lacking;
3. If there's at least a subtopic where the user is lacking, you must provide suggestions of where to improve, which material to revise and where
    a) for example, for transcripts, you must indicate the timeframes where the user needs to revise;
    b) for documents, you must indicate where in the document the user needs to revise (page, section, or general position).

You MUST NOT:
1. hallucinate or invent things that are not provided, both in the materials and in the question results.

You MUST:
1. give the response in the following language: {language}

# MATERIALS

{materials}

# QUESTIONS AND ANSWERS

{questions}

# TOPIC AND WEAK SUBTOPICS

Topic: {topic}
Weak subtopics: {weak_topics}
Amount of errors: {amount_of_errors}

# ANSWER

"""

prompt_wo_weak_topics_generate_feedback = """Given the materials, the questions and answers, the amount of errors, and the broad topic of the questions, you must generate a feedback to provide to the user.
You must indicate:
1. the general result of the test, including the amount of errors;
2. tell the user that he did no mistakes and to keep on practicing, and encouraging him/her.

You MUST NOT:
1. hallucinate or invent things that are not provided, both in the materials and in the question results.

You MUST:
1. give the response in the following language: {language}

# MATERIALS

{materials}

# QUESTIONS AND ANSWERS

{questions}

# TOPIC

Topic: {topic}
Amount of errors: 0

# ANSWER

"""

prompt_wo_topic_generate_feedback = """Given the materials, the questions and answers, the amount of errors, and the subtopics where the user is lacking knowledge, you must generate a feedback to provide to the user.
You must indicate:
1. the general result of the test, including the amount of errors;
2. The subtopics where the user is currently lacking;
3. If there's at least a subtopic where the user is lacking, you must provide suggestions of where to improve, which material to revise and where
    a) for example, for transcripts, you must indicate the timeframes where the user needs to revise;
    b) for documents, you must indicate where in the document the user needs to revise (page, section, or general position).

You MUST NOT:
1. hallucinate or invent things that are not provided, both in the materials and in the question results.

You MUST:
1. give the response in the following language: {language}

# MATERIALS

{materials}

# QUESTIONS AND ANSWERS

{questions}

# WEAK SUBTOPICS

Weak subtopics: {weak_topics}
Amount of errors: {amount_of_errors}

# ANSWER

"""

prompt_wo_all_generate_feedback = """Given the materials, the questions and answers, and the amount of errors, you must generate a feedback to provide to the user.
You must indicate:
1. the general result of the test, including the amount of errors;
2. tell the user that he did no mistakes and to keep on practicing, and encouraging him/her.

You MUST NOT:
1. hallucinate or invent things that are not provided, both in the materials and in the question results.

You MUST:
1. give the response in the following language: {language}

# MATERIALS

{materials}

# AMOUNT OF ERRORS

Amount of errors: {amount_of_errors}

# QUESTIONS AND ANSWERS

{questions}

# ANSWER

"""