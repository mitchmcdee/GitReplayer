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
    # TODO(mitch): remove hardcoding of command name?
    neovim_command = '":InitGitReplayer ' + ' '.join(replayer_args) + '"'
    subprocess.run(['nvim', '-c', neovim_command])


if __name__ == "__main__":
    main()
