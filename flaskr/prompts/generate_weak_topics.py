prompt_weak_topics = """Given a list of questions about the {topic} topic, the possible answers, the user answer position and the correct answer position, indicate the broad weak subtopic (or weak subtopics) that the user needs to revise to improve.
As output, write exclusively "Final answer:" followed by a Python list, containing strings indicating the weak subtopics. The weak subtopics must not be sentences. Do not write anything else after "Final answer:".
The response must be in the following language: {language}.

# Questions

{questions}

"""

prompt_wo_weak_topics = """Given a list of questions, the possible answers, the user answer position and the correct answer position, indicate the broad weak subtopic (or weak subtopics) that the user needs to revise to improve.
As output, write exclusively "Final answer:" followed by a Python list, containing strings indicating the weak subtopics. The weak subtopics must not be sentences. Do not write anything else after "Final answer:".
The response must be in the following language: {language}.

# Questions

{questions}

"""