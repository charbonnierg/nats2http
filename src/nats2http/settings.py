import os


def parse_bool(v: str) -> bool:
    return v.lower() in ["true", "1", "t", "y", "yes", "on"]


ROOT_PATH = ""
DEV = parse_bool(os.environ.get("DEV", "false"))
WEB_CONCURRENCY = int(os.environ.get("WEB_CONCURRENCY", 1))
AIO_LOOP = os.environ.get("AIO_LOOP", "uvloop")
HTTP_IMPL = os.environ.get("HTTP_IMPL", "httptools")

AUTH_TMP_DIR = "/.tmp"
