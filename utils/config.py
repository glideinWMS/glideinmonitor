from pathlib import Path
import json


config_contents = Path("config.json").read_text()
config = json.loads(config_contents)
