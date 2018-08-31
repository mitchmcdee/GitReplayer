import re
from git.objects.blob import Blob


def get_blob_as_splitlines(blob: Blob):
    """
    Attempts to decode and split the blob file lines. If successful, returns
    the splitlines, else returns an empty list.
    """
    try:
        return blob.data_stream.read().decode().splitlines(keepends=True)
    except:
        return []


def is_blob_file_in_regex(blob: Blob, file_regex: str):
    """
    Returns True if the given file contains a path that matches the given file
    regex, else returns False.
    """
    return any(re.search(file_regex, p) for p in (file.a_path, file.b_path))
