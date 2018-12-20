import json
from functools import partial, reduce
import glob
import logging
import re
from argparse import ArgumentParser

from rules import BUILT_IN_RULES
from utils import syntax_err, readlines, fnferror, read, clear_empty_values, \
    str_rm

logger = logging.getLogger(__name__)


DIRECTIVE = 'unpack'
END_DIRECTIVE = 'end {}'.format(DIRECTIVE)
PYTHON_PREFIX = 'pip'
DIRECTIVE_RULES = re.compile(
    r"#\s*(.{2,9})?unpack\s+'([^']+)'\s*([^\s].*[^\s])?\s*:\s*(.+)?\n?"
)

TEMPLATE_SYNTAX = re.compile(
    r"(?<!\\)(\[[^\[\]]+\])+"
)

# greedy whole token
DEFAULT_SOURCE_PATTERN = '(?P<token>.+)'


def introspect(path):
    start, end = None, None
    try:
        with open(path) as f:
            for i, line in enumerate(f):
                # skip non-comment expressions

                if line[0] != '#':
                    continue

                if END_DIRECTIVE in line:
                    end = i
                elif DIRECTIVE in line:
                    start = i

                # TODO:
                # skip other directives
                if start and end:
                    break
    except FileNotFoundError as e:
        raise e

    if end and end < start:
        raise Exception('Start directive should have enclosing directive.')

    # user can omit closing directive first time, behave like we have one
    return start, end


def parse_directive(line):

    result = DIRECTIVE_RULES.match(line)
    if result:

        # predefined rules for some templates like pip
        built_in_rule = BUILT_IN_RULES.get(result.group(1), {})

        data = {
            "built_in": built_in_rule,
            "source_path": result.group(2),
            # TODO default for re {token}
            "source_pattern": result.group(3),
            "template": result.group(4)
        }
        data.update(built_in_rule)
        return data

    return None


def regex_parser(pattern, f):
    _, content = f
    # turn braces to regex consumable form  as groups "my {a} + {b}"
    regex_template = re.sub(
        r"{([a-zA-Z]+)}", "(?P<\g<1>>.+?)", pattern
    )
    # print(regex_template)
    source_re = re.compile(regex_template)

    for match in  source_re.finditer(content):
        yield match.groupdict()


def json_parser(path, fcontent):
    fname, content = fcontent
    # cursor, try to walk
    try:
        js = json.loads(content)
    except Exception:
        logger.warning('{}: Source file cannot be parsed as json.'.format(fname))
        return {}
    print(path)
    if path:

        path_list = path.split('.')
        for key in path_list:

            if not js.get(key):
                logger.warning(
                    "{}: Source key not found '{}'".format(fname, key)
                )
                return {}

            js = js.get(key)
    print(js)
    if isinstance(js, list):
        yield from js
    else:
        logger.warning(
            "{}: Source key is not iterable ".format(fname)
        )
        yield {}


def process(files):

    for file in files:

        path = file

        # introspect scope
        try:
            # TODO other directives
            start, end = introspect(path)
        except FileNotFoundError:
            logger.warning("'{}' not found, skip..".format(path))
            continue

        # directive not found, skip
        if not start:
            continue

        lines = readlines(path)

        # fetch instructions
        directive = parse_directive(lines[start])

        if not directive:
            syntax_err(start, lines[start])

        # check if built in rule is regex based
        is_re = (directive.get('built_in') or {}).get('regex', True)

        if is_re and not (
            directive.get('source_pattern') and directive.get('template')
        ):
            syntax_err(
                start,
                lines[start],
                msg='Please provide source and template'
            )
        source_pattern = directive.get('source_pattern')

        def read_source(path):
            src = read(path, err_fn=partial(fnferror, path, start, lines[start]))
            return path, src

        f = read_source(directive.get('source_path'))

        def render(s, d):
            print(d)
            indices_to_rm = []
            clean_dict = clear_empty_values(d.items())
            print(s)
            # remove [] chunk if any empty {} and apply conditional [] operator
            for match in TEMPLATE_SYNTAX.finditer(s):
                a, b = match.span()
                try:
                    # expect exception in case of empty variables
                    match.group().format(**clean_dict)
                except KeyError:

                    # if any of {} variables not inside of [] remove whole chunk
                    indices_to_rm.extend(range(a, b))
                else:
                    # condition satisfied for bracket. release brackets
                    indices_to_rm.extend([a, b - 1])
            # print(s)
            # print(len(s))
            # print(indices_to_rm)
            # print(list(map(lambda i: s[i], indices_to_rm)))
            s = str_rm(s, *indices_to_rm)
            t = tuple(clean_dict.items())
            print(t)
            return reduce(lambda s, pair: s.replace('{' + pair[0] + '}', pair[1]), t, s)

        tmpl = directive.get('template') or ''
        print(tmpl)
        produced = [
            render(tmpl, obj) + '\n'
            for obj in partial(
                regex_parser if is_re else json_parser,
                source_pattern,
                f
            )()
        ]
        rendered = lines[start] + '\n' + "\n".join(produced) + ('\n' if end else '\n# end unpack\n')
        lines[start: end if end else start + 1] = rendered

        with open(path, 'w') as f:
            f.writelines(lines)


parser = ArgumentParser()

parser.add_argument('files', nargs='*', default=glob.glob('Dockerfile*'))
args = parser.parse_args()


process(args.files)
