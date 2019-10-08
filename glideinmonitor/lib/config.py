from pathlib import Path
import json


class Config:
    config_data = {}

    @classmethod
    def init(cls, config_path=None):
        if config_path is None:
            config_contents = Path("config.json").read_text()
        else:
            config_contents = Path(config_path).read_text()

        cls.config_data = json.loads(config_contents)

    @classmethod
    def db(cls, key):
        return cls.config_data["db"][key]

    @classmethod
    def get(cls, key):
        return cls.config_data[key]

    @classmethod
    def set(cls, key, value):
        cls.config_data[key] = value
