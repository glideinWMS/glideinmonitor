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
    def filters(cls):
        # Returns a list of filters
        if "filters" not in cls.config_data:
            return []

        filter_list = []

        for cur_filter in cls.config_data["filters"]:
            # Check if the necessary fields are present for the filter
            if not all(k in cur_filter for k in ("name", "exe", "type")):
                raise Exception("A filter is missing a name, exe, and/or type field")

            # Add other optional fields with defaults if they are not present
            cur_filter.setdefault("timeout", 0)
            cur_filter.setdefault("description", "")

            # Check if the exe is a valid executable
            if not os.path.exists(cur_filter["exe"]):
                raise Exception("A filter '" + str(cur_filter["name"]) + "' has an exe that cannot be found")

            if not os.access(cur_filter["exe"], os.X_OK):
                raise Exception("A filter '" + str(cur_filter["name"]) + "' has an exe that is not executable")

            # Check if the name is a duplicate
            for other_added_filter in filter_list:
                if other_added_filter["name"] == cur_filter["name"]:
                    raise Exception(
                        "A filter '" + str(cur_filter["name"]) + "' of the same name has already been added")

            # Add the filter to the master list
            filter_list.append(cur_filter)

        return filter_list

    @classmethod
    def db(cls, key):
        return cls.config_data["db"][key]

    @classmethod
    def get(cls, key):
        return cls.config_data[key]

    @classmethod
    def set(cls, key, value):
        cls.config_data[key] = value
