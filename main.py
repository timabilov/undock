import os
import sys
from functools import partial, reduce
import glob
import logging
import re
from argparse import ArgumentParser

from parsers import regex_parser
from rules import BUILT_IN_RULES
from utils import syntax_err, readlines, fnferror, read, clear_empty_values, \
    str_rm

logger = logging.getLogger(__name__)


DIRECTIVE = 'unpack'
END_DIRECTIVE = 'end {}'.format(DIRECTIVE)

# WITHOUT INTERPRET PREFIX
DIRECTIVE_RULES = r"\s*(.{2,9})?unpack\s" \
                  r"+'([^']+)'\s*([^\s].*[^\s])?\s*:\s*(.+)?\n?"

TEMPLATE_SYNTAX = re.compile(
    r"(?<!\\)(\[[^\[\]]+\])+"
)

# greedy whole RE token
DEFAULT_SOURCE_PATTERN = '(?P<token>.+)'


def introspect(path, interpret_prefix):
    start, end = None, None
    try:
        with open(path) as f:
            for i, line in enumerate(f):
                # skip non-comment expressions

                if not line.startswith(interpret_prefix):
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
        raise Exception(
            '{}:{} Start directive should have following enclosing directive.'.format(
                path, start + 1
            )
        )

    # user can omit closing directive first time, behave like we have one
    return start, end


def parse_directive(line, directive_re):

    result = directive_re.match(line)
    if result:

        # predefined rules for some templates like pip
        built_in_rule = BUILT_IN_RULES.get(result.group(1), {})

        data = {
            "built_in": built_in_rule,
            "source_path": result.group(2),

            "template": result.group(4),
            'parser': regex_parser
        }
        data.update(built_in_rule)

        if built_in_rule.get('regex', True):
            data.setdefault(
                "source_pattern", result.group(3) or DEFAULT_SOURCE_PATTERN
            )
        return data

    return None


def process(conf):

    files = conf.get('files')
    interpret_prefix = conf.get('interpret')
    directive_re = re.compile(interpret_prefix + DIRECTIVE_RULES)
    for file in files:

        if not os.path.isfile(file):
            continue
        path = file

        try:
            start, end = introspect(path, interpret_prefix)
        except FileNotFoundError:
            logger.warning("'{}' not found, skip..".format(path))
            continue
        except Exception as e:
            sys.exit(e)

        # directive not found, skip
        if not start:
            continue

        lines = readlines(path)

        # fetch instructions, parser func
        directive = parse_directive(lines[start], directive_re)

        if not directive:
            syntax_err(start, lines[start])

        # check if built-in rule is regex based
        is_re = (directive.get('built_in') or {}).get('regex', True)

        if is_re and not (
            directive.get('source_pattern') and directive.get('template')
        ):
            syntax_err(
                start,
                lines[start],
                msg='Please provide source and template.'
            )

        if not is_re and not directive.get('template'):
            syntax_err(
                start,
                lines[start],
                msg='Please provide template.'
            )

        source_pattern = directive.get('source_pattern')

        def read_source(path):
            src = read(path, err_fn=partial(fnferror, path, start, lines[start]))
            return path, src

        f = read_source(directive.get('source_path'))

        def render(s, d):
            indices_to_rm = []
            clean_dict = clear_empty_values(d.items())

            # remove [] chunk if any empty {} and apply conditional [] operator
            for match in TEMPLATE_SYNTAX.finditer(s):
                a, b = match.span()
                try:
                    # expect exception in case of empty variables
                    match.group().format(**clean_dict)
                except KeyError:
                    # if any of variables inside [] is None, remove whole chunk
                    indices_to_rm.extend(range(a, b))
                else:
                    # condition satisfied for bracket. release brackets
                    indices_to_rm.extend([a, b - 1])

            s = str_rm(s, *indices_to_rm)
            t = tuple(clean_dict.items())

            return reduce(
                lambda l, pair: l.replace('{' + pair[0] + '}', pair[1]), t, s
            )

        tmpl = directive.get('template') or ''

        produced = [
            render(tmpl, obj) + '\n'
            for obj in partial(
                # by default parser is RE
                directive.get('parser'),
                source_pattern,
                f
            )()
        ]
        rendered = lines[start] + '\n' + "\n".join(produced) + (
            '\n' if end else '\n{} {}\n'.format(interpret_prefix, END_DIRECTIVE)
        )
        lines[start: end if end else start + 1] = rendered

        with open(path, 'w') as f:
            f.writelines(lines)


parser = ArgumentParser()
AFFECTED_LINES_PREFIX = '#'
parser.add_argument('-i', "--interpret", default=AFFECTED_LINES_PREFIX)
parser.add_argument('-f', "--files", nargs='*', default=glob.glob('*'))

# parser.add_argument('', nargs='*', default=glob.glob('Dockerfile*'))
args = parser.parse_args()

process(args.__dict__)
