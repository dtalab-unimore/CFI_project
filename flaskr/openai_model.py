import io
import os
from functools import lru_cache
import time
from pydantic import BaseModel, Field
from typing import Any, Optional
from openai import OpenAI
import timeout_decorator
from flask import current_app, jsonify
from werkzeug.datastructures import FileStorage

from .compress_audio import compress_audio, split_audio_ogg_bytes, TARGET_BYTES
from .prompts.generate_qa_prompt import prompt_wo_topic, prompt_topic
from .prompts.generate_weak_topics import prompt_weak_topics, prompt_wo_weak_topics
from .prompts.generate_feedback import prompt_generate_feedback, prompt_wo_weak_topics_generate_feedback, \
    prompt_wo_topic_generate_feedback, prompt_wo_all_generate_feedback
from .utils import remove_markdown_syntax, scramble_answers


class OpenAIModel(BaseModel):
    model_name: str = Field(
        ...,
        strict=True,
        description="Name of the openai model as per their official website"
    )
    transcription_model_name: str = Field(
        ...,
        strict=True,
        description="Name of the openai transcription model as per their official website"
    )
    temperature: float = Field(
        ...,
        strict=True,
        description="The temperature of the model in between 0 and 1"
    )
    transcription_temperature: float = Field(
        ...,
        strict=True,
        description="The temperature of the transcription model in between 0 and 1"
    )
    max_retries: int = Field(
        50,
        strict=True,
        description="Number of retries in case of failed OpenAI API call"
    )
    client: Any = OpenAI()

    # @timeout_decorator.timeout(60, timeout_exception=StopIteration)
    def call_gpt(self, messages: list) -> (str, dict):
        completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature if "5" not in self.model_name else 1.0,
        )

        metadata = {
            "input_tokens": completion.usage.prompt_tokens,
            "output_tokens": completion.usage.completion_tokens,
        }

        return completion.choices[0].message.content #, metadata

    def extract_result(self, text: str, pattern: str) -> str:
        lower_text = text.lower()
        lower_pattern = pattern.lower()

        idx = lower_text.find(lower_pattern)
        if idx == -1:
            return ""  # pattern not found

        start = idx + len(pattern)
        response = text[start:].strip()
        return response

    def query(self, messages: list) -> str:
        for _ in range(self.max_retries):
            try:
                return self.call_gpt(messages)
            except StopIteration:
                print("Failed to get a response. Retrying...")

        raise RuntimeError(f"Failed to query OpenAI after {self.max_retries} retries.")

    def call_gpt_stream(self, messages: list):
        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature if "5" not in self.model_name else 1.0,
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta  # ChoiceDelta
            text_piece = getattr(delta, "content", None)
            if text_piece:
                yield text_piece

    def transcribe(self, file_obj: io.BytesIO, language: str ="it") -> (str, tuple):
        @lru_cache
        def local_transcribe(file_obj: io.BytesIO, language: str ="it") -> (str, tuple):
            file_obj = compress_audio(file_obj, filename=file_obj.name)
            size_bytes = file_obj.getbuffer().nbytes
            if size_bytes > TARGET_BYTES: # more than the audio size allowed for whisper
                print("The file is bigger than what is allowed by whisper. I will split the video.")
                file_objs = split_audio_ogg_bytes(file_obj, filename=file_obj.name)
            else:
                print("The file is not bigger than what is allowed by whisper.")
                file_objs = [file_obj]

            text_total, segments_total = "", []
            for file_obj in file_objs:
                obj = file_obj
                if isinstance(obj, tuple):
                    obj = obj[0]

                for _ in range(50): # retries
                    try:
                        text = self.client.audio.transcriptions.create(
                            model=self.transcription_model_name,
                            file=obj,
                            response_format="verbose_json",
                            timestamp_granularities=["segment"],
                            language=language,
                            temperature=self.transcription_temperature,
                        )
                        good = True
                        break
                    except Exception as e:
                        print(e)
                        time.sleep(5)
                        good = False
                if not good:
                    return -1, -1

                if isinstance(file_obj, tuple):
                    text_total += text.text+"\n"
                    segments = [s.model_dump() for s in text.segments]
                    for i in range(len(segments)):
                        segments[i]["start"] += file_obj[1]
                        segments[i]["end"] += file_obj[1]
                        segments[i]["id"] += len(segments_total)
                    segments_total += segments
                else:
                    text_total = text.text
                    segments = [s.model_dump() for s in text.segments]
                    segments_total = segments

            return text_total, segments_total

        return local_transcribe(file_obj, language)

    def generate_qa(
            self,
            materials: str,
            question_description: str,
            topic_text: Optional[str],
            num_questions: int,
            num_multiple_answers: int,
            language: str = "it",
            uploaded_file_document: list[FileStorage] = [],
            uploaded_file_syllabus: list[FileStorage] = [],
    ):
        attr = {
            "materials": materials,
            "question_description": question_description,
            "num_questions": num_questions,
            "num_multiple_answers": num_multiple_answers,
            "language": language,
        }
        if topic_text is None:
            prompt = prompt_wo_topic
        else:
            attr["topic_text"] = topic_text
            prompt = prompt_topic

        prompt = prompt.format(**attr)
        content: list[dict] = [
            {
                "type": "text",
                "text": prompt
            }
        ]

        for pdf in uploaded_file_document:
            if pdf.mimetype != "application/pdf":
                return jsonify({
                    "error": f"{pdf.filename} is not a PDF"
                }), 400

            pdf.stream.seek(0)

            uploaded = self.client.files.create(
                file=(
                    pdf.filename,
                    pdf.stream,
                    "application/pdf",
                ),
                purpose="user_data",
            )

            content.append({
                "type": "file",
                "file": {
                    "file_id": uploaded.id,
                },
            })

        messages = [{
            "content": content,
            "role": "user"
        }]
        #try:
        response = eval(self.extract_result(remove_markdown_syntax(self.query(messages)), "Final answer:"))
        #except:
        #    return -1

        if not isinstance(response, list) or not isinstance(response[0], dict):
            return -1

        return [scramble_answers(r) for r in response]

    def get_weak_topics(self, questions_txt: str, topic_text: Optional[str] = None, language: str = "it"):
        attr = {
            "questions": questions_txt,
            "language": language,
        }

        if topic_text is None:
            prompt = prompt_wo_weak_topics.format(**attr)
        else:
            attr["topic"] = topic_text
            prompt = prompt_weak_topics.format(**attr)

        messages = [{
            "content": prompt,
            "role": "user"
        }]
        try:
            response = eval(self.extract_result(remove_markdown_syntax(self.query(messages)), "Final answer:"))
        except:
            return -1

        return response

    def generate_feedback(
            self,
            materials: str,
            questions_txt: str,
            topic_text: Optional[str] = None,
            weak_topics: Optional[str] = None,
            amount_of_errors: int = 0,
            language: str = "it",
            uploaded_file_document: list[FileStorage] = [],
            uploaded_file_syllabus: list[FileStorage] = [],
    ):
        attr = {
            "materials": materials,
            "questions": questions_txt,
            "language": language,
        }

        if topic_text is not None:
            attr["topic"] = topic_text
        if weak_topics is not None:
            attr["weak_topics"] = weak_topics
            attr["amount_of_errors"] = amount_of_errors

        if "topic" in attr and "weak_topics" in attr:
            prompt = prompt_generate_feedback
        elif "topic" in attr:
            prompt = prompt_wo_weak_topics_generate_feedback
        elif "weak_topics" in attr:
            prompt = prompt_wo_topic_generate_feedback
        else:
            prompt = prompt_wo_all_generate_feedback

        prompt = prompt.format(**attr)

        content: list[dict] = [
            {
                "type": "text",
                "text": prompt
            }
        ]

        for pdf in uploaded_file_document:
            if pdf.mimetype != "application/pdf":
                return jsonify({
                    "error": f"{pdf.filename} is not a PDF"
                }), 400

            pdf.stream.seek(0)

            uploaded = self.client.files.create(
                file=(
                    pdf.filename,
                    pdf.stream,
                    "application/pdf",
                ),
                purpose="user_data",
            )

            content.append({
                "type": "text",
                "text": (
                    f"SOURCE_FILENAME: {os.path.basename(pdf.filename)}\n"
                    "The immediately following PDF is this source."
                ),
            })

            content.append({
                "type": "file",
                "file": {
                    "file_id": uploaded.id,
                },
            })

        messages = [{
            "content": content,
            "role": "user"
        }]

        """messages = [{
            "content": prompt,
            "role": "user"
        }]"""

        try:
            response = remove_markdown_syntax(self.query(messages))
        except:
            return -1

        return response
