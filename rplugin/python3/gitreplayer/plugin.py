import neovim
import subprocess
import sys
import argparse
import git
import re
import logging
import curses
import time
from dataclasses import dataclass
from datetime import datetime
from difflib import unified_diff
from tqdm import tqdm


# Git's magic empty tree sha1 hash.
MAGIC_EMPTY_TREE_HASH = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


@neovim.plugin
class GitReplayer:
    '''
    TODO(mitch): write this.
    '''

    def __init__(self, nvim):
        self.nvim = nvim

    @neovim.function('TestFunction', sync=True)
    def testfunction(self, args):
        return 3

    @neovim.command('TestCommand', nargs='*', range='')
    def testcommand(self, args, range):
        self.nvim.current.line = ('Command with args: {}, range: {}'
                                  .format(args, range))

    @neovim.autocmd('VimEnter', pattern='*.git', sync=True)
    def on_git_repo_enter(self, filename):
        self.nvim.out_write('testplugin is in ' + filename + '\n')


# def get_blob_as_splitlines(blob):
#     """
#     Attempts to decode and split the blob file lines. If successful, returns
#     the splitlines, else returns an empty list.
#     """
#     try:
#         return blob.data_stream.read().decode().splitlines(keepends=True)
#     except:
#         return []


# def get_commits_in_window(repo, window):
#     """
#     Get commits from oldest to newest and filter out those outside window.
#     """
#     commits = []
#     chronological_commits = list(reversed(list(repo.iter_commits())))
#     for commit_num, commit in enumerate(chronological_commits):
#         commit_datetime = datetime.fromtimestamp(commit.committed_date)
#         if window.start >= commit_datetime:
#             continue
#         if commit_datetime >= window.end:
#             break
#         # If we're adding the first commit, make sure we add either the previous commit
#         # or an empty tree to correctly diff the timeline.
#         if len(commits) == 0:
#             if commit_num != 0:
#                 commits.append(chronological_commits[commit_num - 1])
#             else:
#                 commits.append(repo.tree(MAGIC_EMPTY_TREE_HASH))
#         commits.append(commit)
#     return commits


# def is_file_in_regex(file, file_regex):
#     """
#     Returns True if the given file contains a path that matches the given file regex,
#     else returns False.
#     """
#     return any(re.search(file_regex, p) for p in (file.a_path, file.b_path))


# def get_timeline(repo, window, file_regex):
#     """
#     Get a list of timeline entries representing the current state of the repo at
#     each commit, where each entry is a delta on the previous and the first entry
#     is the starting state.
#     """
#     timeline = []
#     commits = get_commits_in_window(repo, window)
#     previous_commit = repo.tree(MAGIC_EMPTY_TREE_HASH)
#     with tqdm(total=len(commits)) as progress_bar:
#         for commit_num, commit in enumerate(commits):
#             timestep = []
#             for changed_file in previous_commit.diff(commit):
#                 # First entry in timeline is the current state, so ignore invalid regex.
#                 if commit_num == 0 or is_file_in_regex(changed_file, file_regex):
#                     timestep.append(changed_file)
#             # First entry in timeline is the current state, so ignore if empty.
#             if commit_num == 0 or len(timestep) != 0:
#                 timeline.append(timestep)
#             previous_commit = commit
#             progress_bar.update(1)
#     return timeline


# @dataclass
# class Window:
#     """
#     A time window specifying an inclusive start and end datetime range.
#     """

#     start: datetime
#     end: datetime


# class GitReplayer:
#     """
#     A player that visualises git repos being created by replaying its files
#     being written in order of the commit timeline.
#     """

#     def __init__(self, timeline, initial_playback_speed):
#         # Initial repo file state
#         self.initial_files = {
#             file.b_path: get_blob_as_splitlines(file.b_blob) for file in timeline[0]
#         }
#         # Commits to visualise.
#         self.timeline = timeline[1:]
#         # Current playback speed (initially initial_playback_speed).
#         self.playback_speed = initial_playback_speed

#     def get_file_diff(self, changed_file):
#         """
#         Returns the file diff for the changed file, skipping over the initial two
#         diff control lines.
#         """
#         a_lines = get_blob_as_splitlines(changed_file.a_blob)
#         b_lines = get_blob_as_splitlines(changed_file.b_blob)
#         return list(unified_diff(a_lines, b_lines, n=0))[2:]

#     def get_hunk_values(self, header_line):
#         """
#         Parses and returns the chunk header (i.e. hunk) line values.
#         """
#         before, after = header_line[3:-3].split()
#         b_line_num, *b_num_lines = list(map(int, before[1:].split(",")))
#         b_num_lines = int(b_num_lines[0]) if b_num_lines else 1
#         a_line_num, *a_num_lines = list(map(int, after[1:].split(",")))
#         a_num_lines = int(a_num_lines[0]) if a_num_lines else 1
#         return b_line_num, b_num_lines, a_line_num, a_num_lines

#     def draw_file_around_row(self, file, row):
#         """
#         TODO(mitch): this
#         """
#         # TODO(mitch): fix this and make more robust
#         self.screen.clear()
#         self.screen.move(0, 0)
#         for line in file[row - (self.height // 2) : row + (self.height // 2)]:
#             self.screen.addstr(line)

#     def draw_file_changes(self, file):
#         """
#         Draws the file changes to the screen.
#         """
#         # TODO(mitch): abstract out writing to screen + refreshing + waiting?
#         file_path = file.b_path or file.a_path
#         for line in self.get_file_diff(file):
#             change_type = line[0]
#             if change_type == "@":
#                 _, _, current_line_num, a_num_lines = self.get_hunk_values(line)
#                 # TODO(mitch): explain why removing one is necessary
#                 if a_num_lines != 0:
#                     current_line_num -= 1
#                 # TODO(mitch): match current_line_num to place on screen
#                 self.draw_file_around_row(self.files[file_path], current_line_num)
#             elif change_type == "+":
#                 added_line = line[1:]
#                 self.files[file_path].insert(current_line_num, added_line)
#                 current_line_num += 1
#                 # TODO(mitch): abstract this out, prevent writing too much width
#                 self.screen.insertln()
#                 for char in added_line:
#                     self.screen.addch(char)
#                     self.screen.refresh()
#                     time.sleep(1 / self.playback_speed)
#             elif change_type == "-":
#                 self.files[file_path].pop(current_line_num)
#                 self.screen.deleteln()
#             self.screen.refresh()
#             time.sleep(1 / self.playback_speed)

#     def play(self, screen):
#         """
#         Start git repo playback.
#         """
#         self.screen = screen
#         self.height, self.width = self.screen.getmaxyx()
#         # Auto-scroll when at edge of window
#         self.screen.scrollok(True)
#         # TODO(mitch): replace curses with vim for syntax highlighting and nicer text handling?
#         # TODO(mitch): setup ncurses keypresses
#         # TODO(mitch): support play, pause, restart, quit, speed up/down, forward/back timestep
#         while True:
#             self.files = self.initial_files
#             # For each timestep, play back the changed lines in affected files.
#             for timestep in self.timeline:
#                 for file in timestep:
#                     # Move renamed files
#                     if file.renamed_file:
#                         self.files[file.b_path] = self.files[file.a_path]
#                         del self.files[file.a_path]
#                     # Add new files
#                     if file.new_file:
#                         self.files[file.b_path] = []
#                     # Draw file changes
#                     self.draw_file_changes(file)
#                     # Remove deleted files
#                     if file.deleted_file:
#                         del self.files[file.a_path]
#             else:
#                 break


# def main():
    # parsed_args = arg_parser.parse_args(sys.argv[1:])
    # repo = git.Repo(parsed_args.repo_path)
    # window = Window(parsed_args.start_datetime, parsed_args.end_datetime)
    # print("Processing git timeline...")
    # timeline = get_timeline(repo, window, parsed_args.file_regex)
    # print("Starting GitReplayer...")
    # curses.wrapper(GitReplayer(timeline, parsed_args.playback_speed).play)
    # print("Finished!")
