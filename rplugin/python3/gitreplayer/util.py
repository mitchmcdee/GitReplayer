import re
from difflib import unified_diff
from git.objects.blob import Blob
from git.diff import Diff


# Git's magic empty tree sha1 hash.
MAGIC_EMPTY_TREE_HASH = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


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


def get_hunk_values(header):
    """
    Parses and returns the chunk header (i.e. hunk) line values.
    """
    # TODO(mitch): explain this function?
    before, after = header[3:-3].split()
    b_line_num, *b_num_lines = list(map(int, before[1:].split(",")))
    b_num_lines = int(b_num_lines[0]) if b_num_lines else 1
    a_line_num, *a_num_lines = list(map(int, after[1:].split(",")))
    a_num_lines = int(a_num_lines[0]) if a_num_lines else 1
    return b_line_num, b_num_lines, a_line_num, a_num_lines
