if __name__ == '__main__':
    import sys
    import os.path as _p
    import json
    import toolz as z
    from .tidy import *
    import argparse

    def warn(s):
        sys.stderr.write(s + '\n')
        sys.stderr.flush()

    def echo(s):
        sys.stdout.write(s + '\n')
        sys.stdout.flush()


    KNOWN_TYPES = [
        'json-array',
        'json-analysis',
        'bash-exports',
        'bash-env',
    ]
    [
        TYPE_JSON_ARRAY,
        TYPE_JSON_ANALYSIS,
        TYPE_BASH_EXPORTS,
        TYPE_BASH_ASSIGNMENTS,
    ] = KNOWN_TYPES

    parser = argparse.ArgumentParser()
    parser.add_argument('--input-file')
    parser.add_argument('--input-type', choices=KNOWN_TYPES)
    parser.add_argument('--output-type', choices=KNOWN_TYPES)
    options = parser.parse_args()

    input_handlers = {
        TYPE_JSON_ARRAY: json.loads,
        TYPE_BASH_EXPORTS: from_bash_expression,
        TYPE_BASH_ASSIGNMENTS: from_bash_expression,
    }

    output_handlers = {
        TYPE_JSON_ARRAY: lambda cleaned: json.dumps(clean_special_vars(cleaned), indent=2),
        TYPE_BASH_EXPORTS: lambda cleaned: to_bash_expression(cleaned),
        TYPE_BASH_ASSIGNMENTS: lambda cleaned: to_bash_expression(cleaned, prefix=''),
    }

    if not sys.stdin.isatty():
        input = sys.stdin.read().strip()
        # detect json array input
        if input.startswith('['):
            options.input_type = TYPE_JSON_ARRAY
            input_envvars = json.loads(input)
        elif input.startswith('{'):
            options.input_type = TYPE_JSON_ANALYSIS
            if options.output_type != TYPE_JSON_ANALYSIS:
                warn('{} input type can only output as {}'.format(
                    TYPE_JSON_ANALYSIS, TYPE_JSON_ANALYSIS))
            options.output_type = TYPE_JSON_ANALYSIS
        elif input.startswith('export'):
            options.input_type = TYPE_BASH_EXPORTS
        else:
            options.input_type = TYPE_BASH_ASSIGNMENTS
    else:
        is_error = False
        if not options.input_file:
            warn('This usage requires a file path.')
            is_error = True
        elif not _p.exists(options.input_file):
            warn('File at "{}" does not exist.')
            is_error = True

        if is_error:
            parser.print_help()
            sys.exit()

        input = open(options.input_file).read()
        options.input_type = TYPE_JSON_ANALYSIS

    if options.output_type is None:
        options.output_type = options.input_type

    if options.input_type == TYPE_JSON_ANALYSIS:
        analysis_data = json.loads(input)
        for version in analysis_data['versions']:
            version['environment_variables'] = \
                tidy_sort_groups(version['environment_variables'])
        echo(json.dumps(analysis_data, indent=2))
    else:
        input_evs = input_handlers[options.input_type](input)
        cleaned_evs = tidy_sort_groups(input_evs)
        echo(output_handlers[options.output_type](cleaned_evs))
