prompt_generate_feedback = """Given the materials, the questions and answers, the amount of errors, the broad topic of the questions, and the subtopics where the user is lacking knowledge, you must generate a feedback to provide to the user.
You must indicate:
1. the general result of the test, including the amount of errors;
2. The subtopics where the user is currently lacking;
3. If there's at least a subtopic where the user is lacking, you must provide suggestions of where to improve, which material to revise and where. Provide suggestions of which materials to revise based exclusively on what questions the user got wrong
    a) for example, for transcripts, you must indicate the timeframes where the user needs to revise. In the feedback, refer to the video, not the term "transcript". Use the format minutes:seconds, not only seconds. If no transcripts are provided, you can avoid this point;
    b) for documents, you must indicate which document(s) and where in the document(s) the user needs to revise. If no documents are provided, you can avoid this point.

Avoid writing other things outside of the points above. Do not be too verbose.
If all the answers are correct, you can avoid telling the user which subtopics and materials to revise, but still encourage the user to keep on practicing and learning.

You MUST NOT:
1. hallucinate or invent things that are not provided, both in the materials and in the question results.

You MUST:
1. give the response in the following language: {language}
2. avoid gender-identifying pronouns, and avoid using gender-neutral pronouns as well. Structure your feedback so that it does not require any pronouns to be used.

# MATERIALS

{materials}

# QUESTIONS AND ANSWERS

{questions}

# TOPIC AND WEAK SUBTOPICS

Topic: {topic}
Weak subtopics: {weak_topics}
Amount of questions: {num_questions}
Amount of errors: {amount_of_errors}

# ANSWER

"""

prompt_wo_weak_topics_generate_feedback = """Given the materials, the questions and answers, the amount of errors, and the broad topic of the questions, you must generate a feedback to provide to the user.
You must indicate:
1. the general result of the test, including the amount of errors;
2. tell the user that he/she did no mistakes and to keep on practicing, and encouraging him/her.

Avoid writing other things outside of the points above. Do not be too verbose.

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
Amount of questions: {num_questions}
Amount of errors: {amount_of_errors}

# ANSWER

"""

prompt_wo_topic_generate_feedback = """Given the materials, the questions and answers, the amount of errors, and the subtopics where the user is lacking knowledge, you must generate a feedback to provide to the user.
You must indicate:
1. the general result of the test, including the amount of errors;
2. The subtopics where the user is currently lacking;
3. If there's at least a subtopic where the user is lacking, you must provide suggestions of where to improve, which material to revise and where. Provide suggestions of which materials to revise based exclusively on what questions the user got wrong
    a) for example, for transcripts, you must indicate the timeframes where the user needs to revise. In the feedback, refer to the video, not the term "transcript". Use the format minutes:seconds, not only seconds. If no transcripts are provided, you can avoid this point;
    b) for document(s), you must indicate where in the document(s) the user needs to revise. If no documents are provided, you can avoid this point.

Avoid writing other things outside of the points above. Do not be too verbose.
If all the answers are correct, you can avoid telling the user which subtopics and materials to revise, but still encourage the user to keep on practicing and learning.

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
Amount of questions: {num_questions}
Amount of errors: {amount_of_errors}

# ANSWER

"""

prompt_wo_all_generate_feedback = """Given the materials, the questions and answers, and the amount of errors, you must generate a feedback to provide to the user.
You must indicate:
1. the general result of the test, including the amount of errors;
2. tell the user that he/she did no mistakes and to keep on practicing, and encouraging him/her.

Avoid writing other things outside of the points above. Do not be too verbose.
You MUST NOT:
1. hallucinate or invent things that are not provided, both in the materials and in the question results.

You MUST:
1. give the response in the following language: {language}

# MATERIALS

{materials}

# AMOUNT OF ERRORS

Amount of errors: {amount_of_errors}

# QUESTIONS AND ANSWERS

Amount of questions: {num_questions}

{questions}

# ANSWER

"""