import sys


def _read(path, handler, err_fn=None):
    data = None
    try:
        with open(path) as f:
            if callable(handler):
                data = handler(f)
    except FileNotFoundError:
        if callable(err_fn):
            err_fn()
        sys.exit("Cannot open file '{}'".format(path))

    return data


def readlines(path, err_fn=None):
    return _read(path, lambda f: f.readlines(), err_fn)


def read(path, err_fn=None):
    return _read(path, lambda f: f.read(), err_fn)


def syntax_err(lineno, line, msg=''):

    sys.exit('Bad directive syntax.\nline {}: {} \n{}'.format(lineno, line, msg))


def fnferror(path, lineno, line):
    sys.exit("'{}' not found.\nline {}: {}".format(path, lineno, line))


def clear_empty_values(d):

    return {k: v for k, v in d if v}


def str_rm_range(s, start, end):
    return s[:start] + s[end + 1:]


def str_rm(s, *indices):
    elems = sorted(indices, key=lambda x: -x)
    for index in elems:
        s = s[:index] + s[index + 1:]
    return s
