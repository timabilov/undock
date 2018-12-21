"""
Depend on the type of source we use different parsers. By default parser is RE.
Each rule has own parser. Each parser takes source pattern and (name,content)
param.
"""

import json
import logging
import re

logger = logging.getLogger(__name__)


def regex_parser(pattern, f):
    _, content = f
    # turn braces to regex consumable form  as groups "my {a} + {b}"
    regex_template = re.sub(
        r"{([a-zA-Z]+)}", "(?P<\g<1>>.+?)", pattern
    )
    # print(regex_template)
    source_re = re.compile(regex_template)

    for match in source_re.finditer(content):
        yield match.groupdict()


def json_parser(path, fcontent):
    fname, content = fcontent
    # cursor, try to walk
    try:
        js = json.loads(content)
    except Exception:
        logger.warning('{}: Source file cannot be parsed as json.'.format(fname))
        return {}

    if path:

        path_list = path.split('.')
        for key in path_list:

            if not js.get(key):
                logger.warning(
                    "{}: Source key not found '{}'".format(fname, key)
                )
                return {}

            js = js.get(key)

    if isinstance(js, list):
        yield from js
    else:
        logger.warning(
            "{}: Source key is not iterable ".format(fname)
        )
        yield {}
