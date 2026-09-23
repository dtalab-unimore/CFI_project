import hmac
import io
import os
import json

from flask import Blueprint, current_app, request, abort, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path
from ..utils import merge_toml, unescape_unicode, fix_mojibake

bp = Blueprint("api", __name__)
ALLOWED_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
ALLOWED_LANGUAGES = [
  "af","ar","hy","az","be","bs","bg","ca","zh","hr","cs","da","nl","en","et","fi",
  "fr","gl","de","el","he","hi","hu","is","id","it","ja","kn","kk","ko","lv","lt",
  "mk","ms","mr","mi","ne","no","fa","pl","pt","ro","ru","sr","sk","sl","es","sw",
  "sv","tl","ta","th","tr","uk","ur","vi","cy"
]
EASY_QUESTION_DESCRIPTION = """Name of question typology: factual questioning
Description: in this typology, the questions exclusively ask things that are explicitly indicated inside the materials. No inferential or deductive questions are made. The questions must be of easy difficulty."""
MEDIUM_QUESTION_DESCRIPTION = """Name of question typology: mixed questioning
Description: in this typology, half of the questions must be factual, where the questions asks things that are explicitly indicated inside the materials, while the other half must contain inferential questions, where the questions ask things that must be inferred from the provided materials (and are not explicitly stated). The questions must be of medium difficulty. The question_type can only be "factual" or "inferential"."""
HARD_QUESTION_DESCRIPTION = """Name of question typology: inferential questioning
Description: in this typology, the questions must exclusively ask things that must be inferred from the provided materials (and are not explicitly stated). The questions must be of hard difficulty."""
competency_levels = ["low", "medium", "high"]
# error handlers

@bp.app_errorhandler(401)
def unauthorized(_):
    return jsonify(error="missing or invalid passcode"), 401

@bp.app_errorhandler(403)
def forbidden(_):
    return jsonify(error="wrong passcode"), 403

@bp.app_errorhandler(400)
def bad_request(text):
    return jsonify(error=text), 400

@bp.app_errorhandler(415)
def unsupported_media_type(text):
    return jsonify(error=text), 415

@bp.app_errorhandler(500)
def internal_server_error(text):
    return jsonify(error=text), 500

@bp.before_request
def check_passcode():
    allowed = current_app.config["API"].get("secret_passcode") or []
    if isinstance(allowed, str):
        allowed = [allowed]

    provided = request.headers.get("X-API-PASSCODE")

    if not provided or not allowed:
        return unauthorized(None)
    if not any(hmac.compare_digest(provided, code) for code in allowed):
        return forbidden(None)

@bp.post("/transcribe")
def transcribe():
    if "video" not in request.files:
        return bad_request('Missing file field "video"')
    if "language" not in request.form:
        return bad_request('Missing language field "language"')

    f = request.files["video"]
    if not f.filename:
        return bad_request("Empty filename")

    language = request.form["language"]
    if language not in ALLOWED_LANGUAGES:
        return bad_request(f"Invalid language {language}. Allowed languages are: {ALLOWED_LANGUAGES}")

    filename = secure_filename(f.filename)
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTS:
        return unsupported_media_type(f"Unsupported file type {ext}")

    data = f.read()
    file_obj = io.BytesIO(data)
    file_obj.name = f.filename

    openai_model = current_app.extensions["openai_model"]
    text_total, segments_total = openai_model.transcribe(file_obj, language=language)
    if text_total == -1:
        return internal_server_error("Internal processing error. Please try again later.")

    text_total = fix_mojibake(unescape_unicode(text_total))
    #segments_total = [s.model_dump() for s in segments_total]
    for i in range(len(segments_total)):
        segments_total[i]["text"] = fix_mojibake(unescape_unicode(segments_total[i]["text"]))
        segments_total[i] = {"start": segments_total[i]["start"], "end": segments_total[i]["end"], "text": segments_total[i]["text"]}

    return jsonify(
        # text=text_total,
        segments=segments_total
    )

@bp.post("/generate_qa")
def generate_qa():
    if "transcription" not in request.form and "document" not in request.form and "document" not in request.files and "syllabus" not in request.form and "syllabus" not in request.files:
        return bad_request('At least one among "transcription", "document", or "syllabus" needs to be passed to generate the questions')
    if "competency_level" not in request.form:
        is_competency_provided = False
        competency_level = ""
    else:
        is_competency_provided = True
        competency_level = request.form["competency_level"]

    if "language" not in request.form:
        return bad_request('Missing language field "language"')
    else:
        language = request.form["language"]

    if language not in ALLOWED_LANGUAGES:
        return bad_request(f"Invalid language {language}. Allowed languages are: {ALLOWED_LANGUAGES}")

    if "topic" not in request.form:
        topic_text = None
    else:
        topic_text = request.form["topic"]

    if "num_questions" not in request.form:
        num_questions = 10
    else:
        num_questions = int(request.form["num_questions"])

    if "num_multiple_answers" not in request.form:
        num_multiple_answers = 4
    else:
        num_multiple_answers = int(request.form["num_multiple_answers"])

    if is_competency_provided:
        if competency_level == "low":
            question_description = EASY_QUESTION_DESCRIPTION
        elif competency_level == "medium":
            question_description = MEDIUM_QUESTION_DESCRIPTION
        elif competency_level == "high":
            question_description = HARD_QUESTION_DESCRIPTION
        else:
            return bad_request(f"Invalid competency level: {competency_level}. Must be one of \"low\", \"medium\", \"high\".")
    else:
        question_description = MEDIUM_QUESTION_DESCRIPTION

    materials = ""
    if "transcription" in request.form:
        materials += f"## Transcription\n{request.form['transcription']}\n\n" # TODO: maybe it needs to be reprocessed

    uploaded_file_document = []
    if "document" in request.form or "document" in request.files:
        uploaded_text = request.form.get("document")

        uploaded_file_document = [
            document
            for document in request.files.getlist("document")
            if document.filename
        ]

        if len(uploaded_file_document) > 0 and uploaded_text is not None:
            bad_request(f"Cannot both send files and texts for the \"document\" attribute.")

        if uploaded_text is not None:
            materials += f"## Document\n{request.form['document']}\n\n"
        else:
            materials += f"## Document\nSee the attached documents below.\n\n"

    uploaded_file_syllabus = []
    if "syllabus" in request.form or "syllabus" in request.files:
        uploaded_text_syllabus = request.form.get("syllabus")

        uploaded_file_syllabus = [
            document
            for document in request.files.getlist("syllabus")
            if document.filename
        ]

        if len(uploaded_file_syllabus) > 0 and uploaded_text_syllabus is not None:
            bad_request(f"Cannot both send files and texts for the \"syllabus\" attribute.")

        if uploaded_text_syllabus is not None:
            materials += f"## Syllabus\n{request.form['syllabus']}\n\n"
        else:
            materials += f"## Syllabus\nSee the attached syllabus below.\n\n"

    openai_model = current_app.extensions["openai_model"]
    questions = openai_model.generate_qa(
        materials,
        question_description,
        topic_text,
        num_questions,
        num_multiple_answers,
        language=language,
        uploaded_file_document=uploaded_file_document,
        uploaded_file_syllabus=uploaded_file_syllabus
    )

    if questions == -1:
        return internal_server_error("Internal processing error. Please try again later.")

    return jsonify(
        questions=questions,
    )

@bp.post("/evaluate")
def evaluate():
    if "transcription" not in request.form and "document" not in request.form and "document" not in request.files and "syllabus" not in request.form and "syllabus" not in request.files:
        return bad_request('At least one among "transcription", "document", or "syllabus" needs to be passed to generate the questions')

    if "language" not in request.form:
        return bad_request('Missing language field "language"')
    else:
        language = request.form["language"]

    if language not in ALLOWED_LANGUAGES:
        return bad_request(f"Invalid language {language}. Allowed languages are: {ALLOWED_LANGUAGES}")

    if "topic" not in request.form:
        topic_text = None
    else:
        topic_text = request.form["topic"]

    if "competency_level" not in request.form:
        return bad_request('Missing system competency level')
    else:
        competency_level = request.form["competency_level"]

    if "questions" not in request.form:
        return bad_request('Missing questions')
    else:
        questions = json.loads(request.form["questions"])

    if "user_answers" not in request.form:
        return bad_request('Missing user answers')
    else:
        user_answers = json.loads(request.form["user_answers"])

    if "correct_answers" not in request.form:
        return bad_request('Missing correct answers')
    else:
        correct_answers = json.loads(request.form["correct_answers"])

    if len(user_answers) != len(correct_answers):
        return bad_request('Mismatch between length of user answers and correct answers')
    if len(user_answers) != len(questions):
        return bad_request('Mismatch between length of user answers and questions')

    wrong_answers = [ua != ca for ua, ca in zip(user_answers, correct_answers)]
    for i in range(len(user_answers)):
        questions[i]["user_answer"] = user_answers[i]
        questions[i]["correct_answer"] = correct_answers[i]

    def dict_to_string(d: dict) -> str:
        txt = d["question"]
        for i in range(len(d["answers"])):
            txt += f"\n{i}) {d['answers'][i]}"
        txt += f"\nUser answer: {d['user_answer']}"
        txt += f"\nCorrect answer: {d['correct_answer']}"
        return txt

    num_questions = len(questions)
    questions_txt = "\n\n".join([dict_to_string(question) for question in questions])

    openai_model = current_app.extensions["openai_model"]
    if any(wrong_answers):
        weak_topics = openai_model.get_weak_topics(questions_txt, topic_text=topic_text, language=language)
        if weak_topics == -1:
            return bad_request("Internal processing error. Please try again later.")
    else:
        weak_topics = None

    if sum(wrong_answers) <= 2:
        next_sys_competency_level = competency_levels[min(len(competency_levels)-1, competency_levels.index(competency_level)+1)]
    elif sum(wrong_answers) >= len(wrong_answers)-2:
        next_sys_competency_level = competency_levels[max(0, competency_levels.index(competency_level) - 1)]
    else:
        next_sys_competency_level = competency_level

    materials = ""
    if "transcription" in request.form:
        materials += f"## Transcription\n{request.form['transcription']}\n\n"  # TODO: maybe it needs to be reprocessed

    uploaded_file_document = []
    if "document" in request.form or "document" in request.files:
        uploaded_text = request.form.get("document")

        uploaded_file_document = [
            document
            for document in request.files.getlist("document")
            if document.filename
        ]

        if len(uploaded_file_document) > 0 and uploaded_text is not None:
            bad_request(f"Cannot both send files and texts for the \"document\" attribute.")

        if uploaded_text is not None:
            materials += f"## Document\n{request.form['document']}\n\n"
        else:
            filenames = ", ".join(os.path.basename(d.filename) for d in uploaded_file_document)
            materials += f"## Document\nAttached PDF files (attached in the following order): {filenames}.\n\n"

    uploaded_file_syllabus = []
    if "syllabus" in request.form or "syllabus" in request.files:
        uploaded_text_syllabus = request.form.get("syllabus")

        uploaded_file_syllabus = [
            document
            for document in request.files.getlist("syllabus")
            if document.filename
        ]

        if len(uploaded_file_syllabus) > 0 and uploaded_text_syllabus is not None:
            bad_request(f"Cannot both send files and texts for the \"syllabus\" attribute.")

        if uploaded_text_syllabus is not None:
            materials += f"## Syllabus\n{request.form['syllabus']}\n\n"
        else:
            materials += f"## Syllabus\nSee the attached syllabus below.\n\n"

    general_feedback_message = openai_model.generate_feedback(
        materials,
        questions_txt,
        num_questions,
        topic_text,
        weak_topics,
        amount_of_errors=sum(wrong_answers),
        language=language,
        uploaded_file_document=uploaded_file_document,
        uploaded_file_syllabus=uploaded_file_syllabus,
    )

    if general_feedback_message == -1:
        return bad_request("Internal processing error. Please try again later.")

    return jsonify({
        "wrong_answers": wrong_answers,
        "weak_topics": weak_topics,
        "general_feedback": general_feedback_message,
        "next_sys_competency_level": next_sys_competency_level,
    })
