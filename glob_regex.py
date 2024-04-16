import re

def glob_re(pattern, strings):
    return list(filter(re.compile(pattern).match, strings))


