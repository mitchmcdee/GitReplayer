'''
Parser class
'''
import re
import argparse
from datetime import datetime


# Default constants
DEFAULT_PLAYBACK_SPEED = 1000


def valid_datetime(datetime_string):
    """
    Attempts to conver the given datetime string to a datetime object. If successful,
    returns the datetime object, else raises ArgumentTypeError.
    """
    try:
        return datetime.strptime(datetime_string, "%d/%m/%Y %H:%M:%S %Z")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Not a valid datetime: {datetime_string}")


def valid_regex(regex_string):
    """
    Attempts to compile the given regex string. If successful, returns the string
    in its raw form, else raises ArgumentTypeError.
    """
    try:
        re.compile(regex_string)
    except re.error:
        raise argparse.ArgumentTypeError(f"Not valid regex: {regex_string}")
    return fr"{regex_string}"


class GitReplayerParser(argparse.ArgumentParser):
    '''
    A custom parser for configuring a git replayer.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_argument(
            "-r",
            "--repo-path",
            dest="repo_path",
            required=True,
            help="Path to repo to visualise e.g. /path/to/repo",
        )
        self.add_argument(
            "-s",
            "--start-datetime",
            dest="start_datetime",
            type=valid_datetime,
            nargs="?",
            default=datetime.min,
            help='Start with the first entry after the supplied datetime e.g. "DD/MM/YYYY hh:mm:ss tz"',
        )
        self.add_argument(
            "-e",
            "--end-datetime",
            dest="end_datetime",
            type=valid_datetime,
            nargs="?",
            default=datetime.max,
            help='End after the first entry after the supplied datetime e.g. "DD/MM/YYYY hh:mm:ss tz"',
        )
        self.add_argument(
            "-f",
            "--file-regex",
            dest="file_regex",
            type=valid_regex,
            nargs="?",
            default=r".*",
            help='Only visualise files whose relative filepath matches the given regex e.g. "test/*.txt"',
        )
        self.add_argument(
            "-p",
            "--playback-speed",
            dest="playback_speed",
            type=int,
            nargs="?",
            default=DEFAULT_PLAYBACK_SPEED,
            help="The initial playback speed in characters per second",
        )
