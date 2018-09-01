import neovim
import subprocess
import sys
import git
import time
from datetime import datetime
from tqdm import tqdm
from pygments.lexers import guess_lexer_for_filename
from pygments.util import ClassNotFound
from .parser import GitReplayerParser
from .util import (MAGIC_EMPTY_TREE_HASH, get_blob_as_splitlines, is_diff_file_in_regex, get_hunk_values, get_file_diff)


@neovim.plugin
class GitReplayerPlugin:
    """
    A player plugin that visualises git repos being created by replaying files
    being written in pseudo-realtime in order of the commit timeline.
    """

    def __init__(self, nvim):
        self.nvim = nvim

    # TODO(mitch): setup neovim keypresses \/ \/ \/
    # TODO(mitch): support play, pause, restart, quit, speed up/down, forward/back timestep commands
    # TODO(mitch): setup state for ^^^

    @neovim.command('InitGitReplayer', nargs='*')
    def on_init_git_replayer(self, args):
        '''
        TODO(mitch): explain this.
        '''
        parsed_args = GitReplayerParser().parse_args(args)
        repo = git.Repo(parsed_args.repo_path)
        file_regex = parsed_args.file_regex
        start_datetime = parsed_args.start_datetime
        end_datetime = parsed_args.end_datetime
        self.playback_speed = parsed_args.playback_speed
        print('waiting')
        timeline = self.get_timeline(repo, start_datetime, end_datetime, file_regex)
        if len(timeline) == 0:
            print('No commits in git repo to process.')
            sys.exit(1)
        # Initial repo file state
        self.initial_files = {
            file.b_path: get_blob_as_splitlines(file.b_blob) for file in timeline[0]
        }
        # Commits to visualise.
        self.timeline = timeline[1:]
        print('hey')
        self.replay()

    def set_filetype(self, file_path):
        '''
        Sets the filetype in neovim based off of the filename.
        '''
        file_name = file_path.split('/')[-1]
        file_contents = ''.join(self.files[file_path])
        try:
            file_type = guess_lexer_for_filename(file_name, file_contents).name
            self.nvim.command(f'set filetype={file_type}')
        except ClassNotFound:
            pass

    def load_file(self, file_path):
        '''
        Loads the given file into the current buffer.
        '''
        # Neovim doesn't like newlines.
        self.nvim.current.buffer[:] = [l.strip('\n') for l in self.files[file_path]]

    def handle_line_addition(self, file_path, line_num, line):
        '''
        Handles encountering a '+' diff and write out the new line.
        '''
        added_line = line[1:]
        self.files[file_path].insert(line_num, added_line)
        self.nvim.current.buffer.append('', line_num)
        # Jump to appended line.
        self.nvim.command(str(line_num + 1))
        _, cursor_y = self.nvim.api.nvim_win_get_cursor(self.nvim.current.number)
        # Write out all chars in added line.
        for i in range(len(added_line)):
            self.nvim.current.buffer[line_num] = added_line[:i]
            self.nvim.api.nvim_win_set_cursor(self.nvim.current.number, (i, cursor_y))
            time.sleep(1 / self.playback_speed)

    def handle_line_removal(self, line_num):
        '''
        Handles encountering a '-' diff and removes the current line.
        '''
        self.files[file_path].pop(line_num)
        del self.nvim.current.buffer[line_num]

    def draw_file_changes(self, file):
        """
        Draws the file changes to the screen.
        """
        file_path = file.b_path or file.a_path
        self.set_filetype(file_path)
        self.load_file(file_path)
        for line in get_file_diff(file):
            change_type = line[0]
            if change_type == "@":
                _, _, current_line_num, a_num_lines = get_hunk_values(line)
                # TODO(mitch): explain why removing one is necessary
                if a_num_lines != 0:
                    current_line_num -= 1
            elif change_type == "+":
                self.handle_line_addition(file_path, current_line_num, line)
                current_line_num += 1
            elif change_type == "-":
                self.handle_line_removal(current_line_num)
            # Jump to current line.
            self.nvim.command(str(current_line_num))
            time.sleep(1 / self.playback_speed)

    def replay(self):
        """
        Start git repo playback.
        """
        while True:
            self.files = self.initial_files
            # For each timestep, play back the changed lines in affected files.
            for timestep in self.timeline:
                for file in timestep:
                    # Move renamed files
                    if file.renamed_file:
                        self.files[file.b_path] = self.files[file.a_path]
                        del self.files[file.a_path]
                    # Add new files
                    if file.new_file:
                        self.files[file.b_path] = []
                    # Draw file changes
                    self.draw_file_changes(file)
                    # Remove deleted files
                    if file.deleted_file:
                        del self.files[file.a_path]
            #TODO(mitch): fix this loop
            else:
                break

    def get_commits_in_range(self, repo, start_datetime, end_datetime):
        """
        Get commits from oldest to newest and filter out those outside the given range.
        """
        commits = []
        chronological_commits = list(reversed(list(repo.iter_commits())))
        for commit_num, commit in enumerate(chronological_commits):
            commit_datetime = datetime.fromtimestamp(commit.committed_date)
            if start_datetime >= commit_datetime:
                continue
            if commit_datetime >= end_datetime:
                break
            # If we're adding the first commit, make sure we add either the previous
            # commit or an empty tree to correctly diff the timeline.
            if len(commits) == 0:
                if commit_num != 0:
                    commits.append(chronological_commits[commit_num - 1])
                else:
                    commits.append(repo.tree(MAGIC_EMPTY_TREE_HASH))
            commits.append(commit)
        return commits

    def get_timeline(self, repo, start_datetime, end_datetime, file_regex):
        """
        Get a list of timeline entries representing the current state of the repo at
        each commit, where each entry is a delta on the previous and the first entry
        is the starting state.
        """
        timeline = []
        commits = self.get_commits_in_range(repo, start_datetime, end_datetime)
        previous_commit = repo.tree(MAGIC_EMPTY_TREE_HASH)
        # TODO(mitch): fix this for neovim
        # TODO(mitch): try to make faster?
        for commit_num, commit in tqdm(enumerate(commits), total=len(commits)):
            timestep = []
            for changed_file in previous_commit.diff(commit):
                # First entry in timeline is the current state, so ignore invalid regex.
                if commit_num == 0 or is_diff_file_in_regex(changed_file, file_regex):
                    timestep.append(changed_file)
            # First entry in timeline is the current state, so ignore if empty.
            if commit_num == 0 or len(timestep) != 0:
                timeline.append(timestep)
            previous_commit = commit
        return timeline
