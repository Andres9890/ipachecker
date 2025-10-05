[License Button]: https://img.shields.io/badge/License-MIT-white
[License Link]: https://github.com/Andres9890/ipachecker/blob/main/LICENSE 'MIT License.'

[PyPI Button]: https://img.shields.io/pypi/v/ipachecker?color=blue&label=PyPI
[PyPI Link]: https://pypi.org/project/ipachecker/ 'PyPI Package.'

[Downloads Badge]: https://static.pepy.tech/badge/ipachecker/month
[Downloads Link]: https://pepy.tech/project/ipachecker 'Downloads Per Month.'

# IPAchecker
[![Lint](https://github.com/Andres9890/ipachecker/actions/workflows/lint.yml/badge.svg)](https://github.com/Andres9890/ipachecker/actions/workflows/lint.yml)
[![Unit Tests](https://github.com/Andres9890/ipachecker/actions/workflows/unit-test.yml/badge.svg)](https://github.com/Andres9890/ipachecker/actions/workflows/unit-test.yml)
[![License Button]][License Link]
[![PyPI Button]][PyPI Link]
[![Downloads Badge]][Downloads Link]

IPAchecker is a tool for analyzing iOS IPA files, It extracts metadata, checks encryption status, determines architecture, and provides detailed information about iOS applications, The tool supports both local path analysis and direct downloads from URLs (using curl), with batch processing for analyzing multiple ipas

> Python script provided by norep on discord, credits to him

## Features

- **Encryption Detection**: Determines if an IPA file is encrypted or decrypted by analyzing mach-o load commands
- **Metadata Extraction**: Reads app information from Info.plist including bundle ID, version, minimum iOS version, and display name
- **Architecture Analysis**: Identifies app architecture (32-bit, 64-bit, or Universal binary)
- **Batch Processing**: Analyze multiple IPA files from folders or URL/path lists
- **Remote Downloads**: Download and analyze IPA files directly from URLs using curl
- **File Renaming**: Automatically rename IPA files to standardized obscura filename format
- **Console Output**: progress bars, tables, and colored output using the `rich` library
- **JSON Export**: Export analysis results to JSON format
- **Obscura Filename**: Creates standardized filenames in iOSObscura format
- **MD5 Hash**: Generates file hash
- **Automatic Cleanup**: Optionally removes downloaded files after analysis

## Installation

Requires Python 3.8 or newer

```bash
pip install ipachecker
```

The package creates a console script named `ipachecker` once installed, You can also install from source using `pip install .`

## Usage

```bash
ipachecker <input>... [--output <output>] [--json] [--quiet] [--debug] [--dont-delete] [--rename]
ipachecker --batch-analysis <path> [--output <output>] [--json] [--quiet] [--debug] [--dont-delete] [--rename]
```

### Arguments

- `<input>` – Path to .ipa file or URL to download .ipa file
- `<path>` – For batch analysis: folder containing .ipa files, or .txt file with paths/URLs

### Options

- `-h, --help` – Show help message
- `-o, --output <output>` – Save results to specified JSON file
- `-j, --json` – Output results as JSON to stdout
- `-q, --quiet` – Only print errors and results
- `-d, --debug` – Print all logs to stdout for troubleshooting
- `--dont-delete` – Don't delete downloaded files after analysis
- `--rename` – Rename IPA files to obscura filename format after analysis
- `--batch-analysis` – Enable batch analysis mode for multiple files

### Examples

```bash
# Analyze a local IPA file
ipachecker /path/to/app.ipa

# Download and analyze from URL
ipachecker https://example.com/releases/MyApp-v1.2.ipa

# Analyze and rename to obscura format
ipachecker app.ipa --rename

# Analyze multiple files
ipachecker app1.ipa app2.ipa https://example.com/app3.ipa

# Batch analyze all IPAs in a folder and rename them
ipachecker --batch-analysis /path/folder --rename

# Batch analyze from URL/path list file
ipachecker --batch-analysis thereisalist.txt

# Export results to JSON
ipachecker app.ipa --json --output results.json

# Debug mode for troubleshooting
ipachecker app.ipa --debug

# Keep downloaded files and rename them
ipachecker https://example.com/app.ipa --dont-delete --rename
```

### Example Output:

```
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property              ┃ Value                                                          ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Name                  │ Example                                                        │
│ Display Name          │ Example                                                        │
│ Bundle Identifier     │ com.example.app                                                │
│ Version               │ 1.0                                                            │
│ Minimum iOS           │ 2.0                                                            │
│ Architecture          │ 32-bit                                                         │
│ Encrypted             │ YES                                                            │
│ Original Filename     │ example_app.ipa                                                │
│ MD5 Hash              │ d41d8cd98f00b204e9800998ecf8427e                               │
│ File Size             │ 67 bytes                                                       │
└───────────────────────┴────────────────────────────────────────────────────────────────┘

Obscura-format filename:
Example-(com.example.app)-1.0-(iOS_2.0)-d41d8cd98f00b204e9800998ecf8427e.ipa
```

## File Renaming

The `--rename` flag automatically renames analyzed IPA files to the standardized Obscura filename format:

```
{DisplayName}-({BundleID})-{AppVersion}-(iOS_{MinVersion})-{MD5Hash}.ipa
```

**Key behaviors:**
- Only renames local files (not downloaded files, unless used with `--dont-delete`)
- Skips files that already have the correct obscura format name
- Will not overwrite existing files
- Works with both single file and batch analysis modes
- Displays clear status messages for each rename operation

**Examples:**

```bash
# Rename a single file after analysis
ipachecker MyApp.ipa --rename
# Result: MyApp-(com.company.myapp)-1.2.3-(iOS_13.0)-abc123...ipa

# Batch rename all IPAs in a folder
ipachecker --batch-analysis /path/to/ipas --rename

# Download, analyze, keep em, and rename
ipachecker https://example.com/app.ipa --dont-delete --rename
```

## Batch Analysis

ipachecker supports batch processing in two modes:

### Folder Analysis
Point to a folder containing .ipa files:
```bash
ipachecker --batch-analysis /User/downloads/ipas/
```

### List File Analysis
Create a text file with paths/URLs (one per line):
```
# ipas.txt
/Users/downloads/app1.ipa
/Users/downloads/app2.ipa

or

https://example.com/app.ipa
https://releases.example.zip/app67.ipa
```

Then analyze:
```bash
ipachecker --batch-analysis ipas.txt
```

### Batch Rename
Add the `--rename` flag to automatically rename all successfully analyzed files:
```bash
ipachecker --batch-analysis /path/ --rename
```

## How it works

1. **Input Processing**: ipachecker determines if the input is a local file path or URL, For URLs, it uses curl to download the file with SSL compatibility and retry logic

2. **IPA Extraction**: The tool treats IPA files as ZIP archives and extracts them to a temporary directory, locating the `Payload/*.app` structure

3. **Metadata Reading**: Parses the `Info.plist` file to extract app metadata including bundle identifier, version information, display name, and minimum iOS version

4. **Binary Analysis**: Uses the macholib library to analyze the main executable's Mach-O binary format, checking load commands for encryption information and architecture details

5. **Encryption Detection**: Examines `encryption_info_command` and `encryption_info_command_64` load commands, If the `cryptid` field is 0, the binary is decrypted; if 1 or missing commands, it's encrypted

6. **Architecture Detection**: Identifies CPU types from Mach-O headers:
   - ARM64 (cputype 16777228) = 64-bit
   - ARMv7/ARMv7s (cputype 12) = 32-bit  
   - Multiple architectures = Universal

7. **Result Generation**: Compiles all information into a structured result with standardized Obscura filename format: `{DisplayName}-{BundleID}-{AppVersion}-{iOS_MinVersion}-{MD5Hash}.ipa`

8. **File Renaming** (Optional): When `--rename` flag is used, renames the analyzed IPA file to the obscura format, handling file conflicts and permission errors gracefully

9. **Output**: Presents results in rich console tables or JSON format, with batch summaries for multiple file analysis

10. **Cleanup**: Automatically removes downloaded temporary files unless `--dont-delete` is specified

## Error Handling

ipachecker provides clear error messages for common issues:

- **File not found**: Missing local files or invalid paths
- **Download failures**: Network issues, invalid URLs, or SSL problems
- **Invalid IPA files**: Corrupted archives or non-IPA files
- **Missing metadata**: Apps without proper Info.plist files
- **Analysis errors**: Corrupted binaries or unsupported formats
- **Rename failures**: Permission issues, file conflicts, or filesystem errors

Use `--debug` flag for detailed troubleshooting info

## Integration

### JSON Output
Use `--json` arg for programmatic integration:

```json
{
  "appName": "Instagram",
  "displayName": "Instagram", 
  "bundleId": "com.burbn.instagram",
  "appVersion": "245.0",
  "minIOS": "13.0",
  "architecture": "64-bit",
  "encrypted": true,
  "obscuraFilename": "Instagram-(com.burbn.instagram)-245.0-(iOS_13.0)-d41d8cd98f00b204e9800998ecf8427e.ipa",
  "originalFilename": "instagram.ipa",
  "md5": "d41d8cd98f00b204e9800998ecf8427e",
  "fileSize": 125829120,
  "filePath": "/path/to/instagram.ipa"
}
```

### Exit Codes
- `0`: Success
- `1`: Analysis errors or failures

>[!WARNING]
> This tool is not affiliated with, endorsed by, or sponsored by Apple Inc.