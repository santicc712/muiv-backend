import re
import os
import glob

def glob_re(pattern, strings):
    return list(filter(re.compile(pattern).match, strings))


def get_filepaths_with_oswalk(root_path: str, file_regex: str):
    files_paths = []
    pattern = re.compile(file_regex)
    for root, directories, files in os.walk(root_path):
        for file in files:
            if pattern.match(file):
                files_paths.append(os.path.join(root, file))
    return files_paths

def get_filepaths_with_glob(root_path: str, file_regex: str):
    return glob.glob(os.path.join(root_path, file_regex))


