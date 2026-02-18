import re
import random
from flask import current_app

def merge_toml(section: str) -> dict:
    """
    merge "API" toml config with "section" toml
    """
    api_defaults = current_app.config.get("API", {}) or {}
    section_cfg = current_app.config.get(section.upper(), {}) or {}
    return {**api_defaults, **section_cfg}

def unescape_unicode(text: str) -> str:
    """
    converting sequences like '\\u00e8' into 'è'
    """
    if not isinstance(text, str):
        raise TypeError("text must be a str")

    # turning "\\u00e8" -> "\u00e8" (mapping double escaping to single escaping)
    if "\\\\u" in text:
        text = text.replace("\\\\u", "\\u")

    try:
        return text.encode("utf-8").decode("unicode_escape")
    except UnicodeDecodeError:
        return text

def fix_mojibake(s: str) -> str:
    if not isinstance(s, str):
        raise TypeError("s must be a str")

    try:
        return s.encode("latin1").decode("utf-8")
    except UnicodeError:
        try:
            return s.encode("cp1252").decode("utf-8")
        except UnicodeError:
            return s

def remove_markdown_syntax(text: str) -> str:
    # Remove triple backtick code blocks (```python ... ```)
    text = re.sub(r"```[\s\S]*?```", lambda m: re.sub(r"^```.*\n|```$", '', m.group()), text)

    # Remove inline code (`code`)
    text = re.sub(r"`([^`]*)`", r"\1", text)

    # Remove bold (**text** or __text__)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)

    # Remove italic (*text* or _text_)
    text = re.sub(r"\*(.*?)\*", r"\1", text)

    # Remove blockquotes
    text = re.sub(r"^>\s?", '', text, flags=re.MULTILINE)

    text = text.replace("python", "")
    return text.strip()

def scramble_answers(q: dict) -> dict:
    p = random.sample(range(len(q["answers"])), len(q["answers"]))
    return {**q,
            "answers": [q["answers"][i] for i in p],
            "correct_answer": p.index(q["correct_answer"])}