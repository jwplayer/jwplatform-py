import os


def get_file_size(file):
    start_position = file.tell()
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(start_position, os.SEEK_SET)
    return size
