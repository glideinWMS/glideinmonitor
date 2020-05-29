from glideinmonitor.lib.config import Config
from glideinmonitor.lib.logger import log


class Filter:
    filter_list = []

    def __init__(self):
        try:
            self.filter_list = Config.filters()
        except Exception as e:
            log("ERROR", "Filter configuration error: " + str(e))

        log("INFO", str(len(self.filter_list)) + " valid filters have been found and will run")

    def filter_builder(self, save_dir, save_file_name, files):
        # Returns full path to the archive in the save_dir directory

        # Return the path to the finalized filtered archive
        return ""
