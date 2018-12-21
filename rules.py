from parsers import json_parser

BUILT_IN_RULES = {
    'pip': {
        'source_pattern': r'{line}(=={ver})?(;.+)?\n',
        'template': r'RUN pip install {line}[=={ver}]',
    },
    'json': {
        'regex': False,
        # Default is json file root.
        # Example of syntax: data.key.listkey
        'parser': json_parser

    }
}
