#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ipachecker - Analyze iOS IPA files for metadata and encryption status

"""ipachecker - Analyze iOS IPA files for metadata and encryption status.

Usage:
  ipachecker <input>... [--output <output>] [--json] [--quiet] [--debug] [--dont-delete] [--rename]
  ipachecker --batch-analysis <path> [--output <output>] [--json] [--quiet] [--debug] [--dont-delete] [--rename]
  ipachecker -h | --help
  ipachecker --version

Arguments:
  <input>                      Path to .ipa file or URL to download .ipa file
  <path>                       Path to folder containing .ipa files, or path to .txt file
                              containing paths/URLs (one per line)

Options:
  -h --help                   Show this screen
  -o --output <output>        Save results to specified JSON file
  -j --json                   Output results as JSON to stdout
  -q --quiet                  Only print errors and results
  -d --debug                  Print all logs to stdout
  --dont-delete               Don't delete downloaded files after analysis
  --rename                    Rename IPA files to obscura filename format after analysis
  --batch-analysis            Enable batch analysis mode for multiple files or URLs
"""

import json
import logging
import os
import sys
import traceback

import docopt

from ipachecker import __version__
from ipachecker.IPAChecker import IPAChecker
from ipachecker.utils import get_latest_pypi_version


def prompt_save_results(results):
    """
    Prompt user if they want to save batch results to JSON file.

    :param results: List of analysis results
    :return:       Path to saved file or None if user declined
    """
    try:
        print(f"\n:: Analysis complete! Found {len(results)} result(s).")

        # Count successful analyses
        successful = [r for r in results if "error" not in r]
        errors = len(results) - len(successful)

        if successful:
            print(f"   Successfully analyzed: {len(successful)} files")
        if errors:
            print(f"   Errors encountered: {errors} files")

        # Prompt for saving
        while True:
            response = input("\n:: Save all results to JSON file? (Y/N): ").strip().upper()

            if response in ["Y", "YES"]:
                # Generate default filename
                timestamp = __import__("datetime").datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"iparesults_{timestamp}.json"

                try:
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(results, f, indent=2, ensure_ascii=False)

                    print(f":: Results saved to: {filename}")
                    return filename

                except Exception as e:
                    print(f":: Error saving file: {e}")
                    continue

            elif response in ["N", "NO"]:
                print(":: Results not saved.")
                return None

            else:
                print(":: Please enter Y or N.")
                continue

    except KeyboardInterrupt:
        print("\n:: Operation cancelled.")
        return None


def detect_input_type(path):
    """
    Detect if the input path is a folder or a text file.

    :param path: Input path to analyze
    :return:    Tuple of (type, error_message) where type is 'folder', 'file', or None
    """
    if not os.path.exists(path):
        return None, f"Path does not exist: {path}"

    if os.path.isdir(path):
        return "folder", None
    elif os.path.isfile(path):
        if path.lower().endswith(".txt"):
            return "file", None
        else:
            return None, f"Batch analysis requires a folder or .txt file, got: {path}"
    else:
        return None, f"Invalid path type: {path}"


def main():
    # Parse arguments from file docstring
    args = docopt.docopt(__doc__, version=__version__)

    inputs = args.get("<input>", [])
    batch_path = args.get("<path>")
    output_file = args["--output"]
    json_output = args["--json"]
    quiet_mode = args["--quiet"]
    debug_mode = args["--debug"]
    dont_delete = args["--dont-delete"]
    batch_analysis = args["--batch-analysis"]
    rename_files = args["--rename"]

    if debug_mode:
        # Display log messages.
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("\033[92m[DEBUG]\033[0m %(asctime)s - %(name)s - %(levelname)s - " "%(message)s")
        ch.setFormatter(formatter)
        root.addHandler(ch)

    # Initialize checker with appropriate settings
    checker = IPAChecker(verbose=not quiet_mode, delete_downloaded=not dont_delete)

    try:
        results = []

        if batch_analysis:
            # Batch analysis mode
            if not batch_path:
                print("\033[91mError: Batch analysis requires a path argument.\033[0m")
                sys.exit(1)

            if not quiet_mode:
                print(f"\n:: Starting batch analysis of: {batch_path}")

            # Detect input type
            input_type, error = detect_input_type(batch_path)
            if error:
                print(f"\033[91mError: {error}\033[0m")
                sys.exit(1)

            # Perform batch analysis
            if input_type == "folder":
                if not quiet_mode:
                    print(":: Analyzing folder for .ipa files...")
                results = checker.batch_analyze_folder(batch_path)
            elif input_type == "file":
                if not quiet_mode:
                    print(":: Reading paths/URLs from text file...")
                results = checker.batch_analyze_from_file(batch_path)

            # Handle renaming for batch results
            if rename_files and not quiet_mode:
                print("\n:: Renaming files to obscura format...")
                renamed_count = 0
                for result in results:
                    if "error" not in result and not result.get("_metadata", {}).get("was_downloaded", False):
                        rename_result = checker.rename_to_obscura(result)
                        if rename_result["success"]:
                            renamed_count += 1
                            print(f"   Renamed: {os.path.basename(rename_result['new_path'])}")
                        elif not quiet_mode:
                            print(
                                f"   Failed to rename {os.path.basename(result['filePath'])}: {rename_result['error']}"
                            )

                if renamed_count > 0:
                    print(f"\n:: Successfully renamed {renamed_count} file(s)")

            # Display results
            if json_output:
                print(json.dumps(results, indent=2))
            elif not quiet_mode:
                # Print individual results
                for i, result in enumerate(results, 1):
                    if "error" in result:
                        source = result.get("_metadata", {}).get("source", "Unknown")
                        print(f'\n\033[91mError analyzing item {i} ({source}):\033[0m {result["error"]}')
                    else:
                        print(f"\n:: Result {i}/{len(results)}:")
                        # Remove metadata before displaying
                        display_result = {k: v for k, v in result.items() if k != "_metadata"}
                        checker.print_result_table(display_result)

                # Print batch summary
                checker.print_batch_summary(results)

            # Handle output file or prompt for saving
            if output_file:
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                if not quiet_mode:
                    print(f"\n:: Results saved to {output_file}")
            elif not json_output and not quiet_mode:
                # Interactive prompt for saving
                prompt_save_results(results)

        else:
            # Regular analysis mode
            if not inputs:
                print("\033[91mError: No input files or URLs specified.\033[0m")
                sys.exit(1)

            for input_item in inputs:
                if not quiet_mode:
                    print(f"\n:: Processing {input_item}")

                result = checker.check_ipa(input_item)

                if "error" in result:
                    print(f'\033[91mError analyzing {input_item}:\033[0m {result["error"]}')
                    continue

                results.append(result)

                # Handle renaming for single file
                if rename_files:
                    was_downloaded = result.get("_metadata", {}).get("was_downloaded", False)
                    if not was_downloaded:
                        rename_result = checker.rename_to_obscura(result)
                        if rename_result["success"]:
                            if not quiet_mode:
                                print(f"\n:: File renamed to: {os.path.basename(rename_result['new_path'])}")
                            # Update result with new path
                            result["filePath"] = rename_result["new_path"]
                        else:
                            print(f'\033[91mError renaming file:\033[0m {rename_result["error"]}')
                    elif not quiet_mode:
                        print("\n:: Skipping rename for downloaded file (use --dont-delete to keep and rename)")

                if json_output:
                    # Remove metadata for JSON output
                    display_result = {k: v for k, v in result.items() if k != "_metadata"}
                    print(json.dumps(display_result, indent=2))
                elif not quiet_mode:
                    # Remove metadata before displaying
                    display_result = {k: v for k, v in result.items() if k != "_metadata"}
                    checker.print_result_table(display_result)

            # Save to file if requested
            if output_file and results:
                # Remove metadata from results before saving
                clean_results = []
                for result in results:
                    clean_result = {k: v for k, v in result.items() if k != "_metadata"}
                    clean_results.append(clean_result)

                with open(output_file, "w", encoding="utf-8") as f:
                    if len(clean_results) == 1:
                        json.dump(clean_results[0], f, indent=2, ensure_ascii=False)
                    else:
                        json.dump(clean_results, f, indent=2, ensure_ascii=False)
                if not quiet_mode:
                    print(f"\n:: Results saved to {output_file}")

    except KeyboardInterrupt:
        print("\n:: Analysis interrupted by user")
        sys.exit(1)
    except Exception:
        print(
            "\n\033[91m"  # Start red color text
            "An exception occurred. If this seems like a bug, "
            "please report this issue to the project repository."
        )
        traceback.print_exc()
        print("\033[0m")  # End the red color text
        sys.exit(1)
    finally:
        # Clean up downloaded files if enabled
        if not dont_delete:
            checker.cleanup_downloaded_files()

        # Version check after operations complete (success or fail)
        latest_version = get_latest_pypi_version()
        if latest_version and latest_version != __version__:
            print(f"\033[93mA newer version of ipachecker is available: \033[92m{latest_version}\033[0m")
            print("Update with: pip install --upgrade ipachecker\n")


if __name__ == "__main__":
    main()
