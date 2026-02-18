import os
from flask import Flask
import tomllib
import os
from .routes import api

def load_toml_config(app: Flask, filename: str = "config.toml") -> None:
    """
    loading toml file and merging it to app.config
    """
    path = os.path.join(app.instance_path, filename)
    if not os.path.exists(path):
        return

    with open(path, "rb") as f:
        data = tomllib.load(f)

    flask_section = data.get("flask", {})

    if "secret_key" in flask_section:
        app.config["SECRET_KEY"] = flask_section["secret_key"]
    if "debug" in flask_section:
        app.config["DEBUG"] = bool(flask_section["debug"])
    if "openai_api_key" in flask_section:
        app.config["OPENAI_API_KEY"] = os.environ["OPENAI_API_KEY"] = flask_section["openai_api_key"]

    for section, values in data.items():
        if section == "flask":
            continue
        if isinstance(values, dict):
            app.config[section.upper()] = values


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.json.ensure_ascii = False

    load_toml_config(app, "config.toml")

    from .openai_model import OpenAIModel
    app.extensions["openai_model"] = OpenAIModel(
        model_name=app.config["API"]["model_name"],
        transcription_model_name=app.config["TRANSCRIBE"]["model_name"],
        temperature=float(app.config["API"]["temperature"]),
        transcription_temperature=float(app.config["TRANSCRIBE"]["temperature"]),
    )

    if test_config is not None:
        app.config.from_mapping(test_config)

    url_prefix = app.config["API"]["url_prefix"]
    app.register_blueprint(api.bp, url_prefix=url_prefix)

    return app
