BUILT_IN_RULES = {
    'pip': {
        'source_pattern': r'{line}(=={ver})?(;.+)?\n',
        'template': r'RUN pip install {line}[=={ver}]'
    },
    'json': {
        'regex': False,
        # Default is root. Example: data.key.listkey
        # 'source_pattern': ''
    }
}