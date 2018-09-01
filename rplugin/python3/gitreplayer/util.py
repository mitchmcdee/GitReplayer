import re
from difflib import unified_diff
from git.objects.blob import Blob
from git.diff import Diff
import io


# Git's magic empty tree sha1 hash.
MAGIC_EMPTY_TREE_HASH = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


class TqdmOutput(io.StringIO):
    """
    Output stream for TQDM which will output to logger module instead of
    the stdout.
    """
    buf = ''
    def __init__(self, nvim):
        super().__init__()
        self.nvim = nvim

    def write(self, buf):
        self.buf = buf.strip('\r\n\t ')

    def flush(self):
        self.nvim.out_write(self.buf)


def get_blob_as_splitlines(blob: Blob):
    """
    Attempts to decode and split the blob file lines. If successful, returns
    the splitlines, else returns an empty list.
    """
    try:
        return blob.data_stream.read().decode().splitlines(keepends=True)
    except:
        return []


def is_diff_file_in_regex(diff: Diff, file_regex: str):
    """
    Returns True if the given diff contains a file path that matches the given
    file regex, else returns False.
    """
    return any(re.search(file_regex, p) for p in (diff.a_path, diff.b_path))


def get_file_diff(diff: Diff):
    """
    Returns the file diff for the changed file, skipping over the initial two
    diff control lines as they contain redundant information.
    """
    a_lines = get_blob_as_splitlines(diff.a_blob)
    b_lines = get_blob_as_splitlines(diff.b_blob)
    return list(unified_diff(a_lines, b_lines, n=0))[2:]


def get_current_line(header_line):
    """
    Parses the chunk header line and returns what the current line will be.
    """
    # Strip unnecessary characters, convert to integer.
    _, after = header_line[3:-3].split()
    current_line_num, *num_lines_after = list(map(int, after[1:].split(",")))
    num_lines_after = int(num_lines_after[0]) if num_lines_after else 1
    # TODO(mitch): explain why removing one is necessary
    if num_lines_after != 0:
        current_line_num -= 1
    return current_line_num
