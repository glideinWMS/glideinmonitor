from config import config
import datetime


def log(error_level, message):
    if config["Warn_Level"] == "NONE":
        return

    if config["Warn_Level"] == "ERROR":
        if error_level != "ERROR":
            return

    if config["Warn_Level"] == "WARNING":
        if error_level == "INFO":
            return

    # Write to error log
    with open(config['Log_Dir'] + datetime.datetime.now().strftime("/%Y-%m-%d") + ".txt", "a") as log_file:
        log_file.write(error_level + " - " + str(datetime.datetime.now()) + " - " + message + "\n")
