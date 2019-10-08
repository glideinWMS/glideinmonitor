from pathlib import Path
import json
import os
import glideinmonitor


class Config:
    config_data = {}

    @classmethod
    def init(cls, config_path=None):
        if config_path is None:
            default_config_path = os.path.join(os.path.dirname(glideinmonitor.__file__), "default_config.json")
            config_contents = Path(default_config_path).read_text()
        else:
            config_contents = Path(config_path).read_text()

        curr = json.loads(config_contents)

        if "parent_config" in curr and curr["parent_config"] != "":
            parent = cls.dive(curr["parent_config"])

            curr.update(parent)

            cls.config_data = curr
        else:
            cls.config_data = curr

    @classmethod
    def dive(cls, config_path):
        config_contents = Path(config_path).read_text()

        curr = json.loads(config_contents)

        if "parent_config" in curr and curr["parent_config"] != "":
            parent = cls.dive(curr["parent_config"])

            curr.update(parent)

            return curr
        else:
            return curr

    @classmethod
    def db(cls, key):
        return cls.config_data["db"][key]

    @classmethod
    def get(cls, key):
        return cls.config_data[key]

    @classmethod
    def set(cls, key, value):
        cls.config_data[key] = value
