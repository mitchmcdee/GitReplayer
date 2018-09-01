import subprocess
import argparse
import sys
import re
from datetime import datetime
from parser import GitReplayerParser


def main():
    replayer_args = sys.argv[1:]
    # This will throw a usage error if it cannot be parsed.
    GitReplayerParser().parse_args(replayer_args)
    # Add as a string so that it doesn't interfere with nvim args.
    subprocess.run(['nvim', '-c', ':GitReplayerInit ' + ' '.join(replayer_args)])


if __name__ == "__main__":
    main()
