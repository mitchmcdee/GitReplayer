import subprocess
import argparse
import sys
import re
from datetime import datetime
from parser import GitReplayerParser


def main():
    nvim_args = sys.argv[1:]
    # This will throw a usage error if it cannot be parsed.
    GitReplayerParser().parse_args(nvim_args)
    subprocess.run(['nvim', '-c', *nvim_args])


if __name__ == "__main__":
    main()
