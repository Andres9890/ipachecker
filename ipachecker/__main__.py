#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ipachecker - Analyze iOS IPA files for metadata and encryption status

"""ipachecker - Analyze iOS IPA files for metadata and encryption status.

Usage:
  ipachecker <input>... [--output <output>] [--json] [--quiet] [--debug]
  ipachecker -h | --help
  ipachecker --version

Arguments:
  <input>                      Path to .ipa file or URL to download .ipa file.

Options:
  -h --help                   Show this screen.
  -o --output <output>        Save results to specified JSON file.
  -j --json                   Output results as JSON to stdout.
  -q --quiet                  Only print errors and results.
  -d --debug                  Print all logs to stdout.
"""

import sys
import docopt
import logging
import traceback
import json

from ipachecker.IPAChecker import IPAChecker
from ipachecker import __version__


def main():
    # Parse arguments from file docstring
    args = docopt.docopt(__doc__, version=__version__)

    inputs = args['<input>']
    output_file = args['--output']
    json_output = args['--json']
    quiet_mode = args['--quiet']
    debug_mode = args['--debug']

    if debug_mode:
        # Display log messages.
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '\033[92m[DEBUG]\033[0m %(asctime)s - %(name)s - %(levelname)s - '
            '%(message)s')
        ch.setFormatter(formatter)
        root.addHandler(ch)

    checker = IPAChecker(verbose=not quiet_mode)

    try:
        results = []
        for input_item in inputs:
            if not quiet_mode:
                print(f'\n:: Processing {input_item}')
            
            result = checker.check_ipa(input_item)
            
            if "error" in result:
                print(f'\033[91mError analyzing {input_item}:\033[0m {result["error"]}')
                continue
                
            results.append(result)
            
            if json_output:
                print(json.dumps(result, indent=2))
            elif not quiet_mode:
                checker.print_result_table(result)
        
        # Save to file if requested
        if output_file and results:
            with open(output_file, 'w') as f:
                if len(results) == 1:
                    json.dump(results[0], f, indent=2)
                else:
                    json.dump(results, f, indent=2)
            if not quiet_mode:
                print(f'\n:: Results saved to {output_file}')
                
    except KeyboardInterrupt:
        print('\n:: Analysis interrupted by user')
        sys.exit(1)
    except Exception:
        print('\n\033[91m'  # Start red color text
              'An exception occurred. If this seems like a bug, '
              'please report this issue to the project repository.')
        traceback.print_exc()
        print('\033[0m')  # End the red color text
        sys.exit(1)


if __name__ == '__main__':
    main()