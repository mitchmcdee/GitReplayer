import neovim
import subprocess
import sys
import time
from git import Repo
from git.objects.commit import Commit
from datetime import datetime
from tqdm import tqdm
from pygments.lexers import guess_lexer_for_filename
from pygments.util import ClassNotFound
from util import (
    TqdmOutput,
    MAGIC_EMPTY_TREE_HASH,
    get_blob_as_splitlines,
    is_diff_file_in_regex,
    is_author_in_regex,
    get_current_line,
    get_file_diff,
)

def get_timeline(repo, start_datetime, end_datetime, file_regex, author_regex):
    """
    Get a list of timeline entries representing the current state of the repo at
    each commit, where each entry is a delta on the previous and the first entry
    is the starting state. Also stores which user made the timestep changes.
    """
    timeline = []
    # Reorder chronologically
    commits = list(reversed(list(repo.iter_commits())))
    previous_commit = repo.tree(MAGIC_EMPTY_TREE_HASH)
    for commit_num, commit in tqdm(list(enumerate(commits))):
        commit_datetime = datetime.fromtimestamp(commit.committed_date)
        if commit_datetime >= end_datetime:
            break
        if start_datetime >= commit_datetime:
            continue
        if not is_author_in_regex(commit.author.name, author_regex):
            continue
        timestep = []
        for diff in previous_commit.diff(commit):
            if not is_diff_file_in_regex(diff, file_regex):
                continue
            timestep.append(diff)
        if len(timestep) == 0:
            continue
        # If we're the first commit, add the initial state (i.e. the previous commit).
        if len(timeline) == 0:
            empty_tree = repo.tree(MAGIC_EMPTY_TREE_HASH)
            print(empty_tree, previous_commit, commit, len(timestep))
            print(list(empty_tree.diff(previous_commit)))
            timeline.append((None, list(empty_tree.diff(previous_commit))))
        timeline.append((commit, timestep))
        previous_commit = commit
    return timeline

repo = Repo('~/Repos/uqcsbot/')
something = repo.tree(MAGIC_EMPTY_TREE_HASH)
something_else = something
something_else = None
print(something, something_else)
