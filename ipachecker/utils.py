import os
import re
from typing import Optional, Tuple
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """
    Check if a string is a valid URL.

    :param url: String to check
    :return:    Boolean indicating if string is a valid URL
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing/replacing invalid characters.

    :param filename:    Original filename
    :return:           Sanitized filename safe for filesystem
    """
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

    # Remove leading/trailing whitespace and dots
    filename = filename.strip(" .")

    # Ensure filename is not empty
    if not filename:
        filename = "download"

    # Limit filename length
    name, ext = os.path.splitext(filename)
    if len(name) > 200:  # Leave room for extension
        name = name[:200]

    return name + ext


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.

    :param size_bytes: Size in bytes
    :return:          Formatted size string
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size_float = float(size_bytes)

    while size_float >= 1024.0 and i < len(size_names) - 1:
        size_float /= 1024.0
        i += 1

    return f"{size_float:.1f} {size_names[i]}"


def validate_ipa_file(filepath: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a file is likely an IPA file.

    :param filepath: Path to file to validate
    :return:        Tuple of (is_valid, error_message)
    """
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"

    if not filepath.lower().endswith(".ipa"):
        return False, f"File must have .ipa extension: {filepath}"

    if os.path.getsize(filepath) == 0:
        return False, f"File is empty: {filepath}"

    # Try to open as zip file (IPA files are zip archives)
    try:
        import zipfile

        with zipfile.ZipFile(filepath, "r") as zf:
            # Check for typical IPA structure
            files = zf.namelist()
            has_payload = any(f.startswith("Payload/") for f in files)
            if not has_payload:
                return (
                    False,
                    "File does not appear to be a valid IPA (missing Payload directory)",
                )
    except zipfile.BadZipFile:
        return False, "File is not a valid ZIP archive"
    except Exception as e:
        return False, f"Error validating file: {e}"

    return True, None


def dict_to_xml(data, root_name="root", indent=0):
    """
    Convert a Python dictionary or list to XML format.

    :param data:       Dictionary or list to convert
    :param root_name:  Name for the root XML element
    :param indent:     Current indentation level
    :return:          XML string representation
    """
    xml_output = []
    indent_str = "  " * indent

    if isinstance(data, dict):
        xml_output.append(f"{indent_str}<{root_name}>")
        for key, value in data.items():
            # Sanitize key names to be valid XML element names
            safe_key = re.sub(r"[^a-zA-Z0-9_-]", "_", str(key))
            if isinstance(value, (dict, list)):
                xml_output.append(dict_to_xml(value, safe_key, indent + 1))
            else:
                # Escape special XML characters
                escaped_value = (
                    str(value)
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                    .replace("'", "&apos;")
                )
                xml_output.append(
                    f"{indent_str}  <{safe_key}>{escaped_value}</{safe_key}>"
                )
        xml_output.append(f"{indent_str}</{root_name}>")
    elif isinstance(data, list):
        xml_output.append(f"{indent_str}<{root_name}>")
        for item in data:
            xml_output.append(dict_to_xml(item, "item", indent + 1))
        xml_output.append(f"{indent_str}</{root_name}>")
    else:
        # Handle scalar values
        escaped_value = (
            str(data)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )
        xml_output.append(f"{indent_str}<{root_name}>{escaped_value}</{root_name}>")

    return "\n".join(xml_output)


def results_to_xml(results):
    """
    Convert IPA analysis results to XML format.

    :param results: Single result dict or list of result dicts
    :return:       XML string with proper header
    """
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>'

    if isinstance(results, list):
        xml_body = dict_to_xml(results, "results", 0)
    else:
        xml_body = dict_to_xml(results, "result", 0)

    return f"{xml_header}\n{xml_body}"


def get_latest_pypi_version(package_name: str = "ipachecker") -> Optional[str]:
    """
    Request PyPI for the latest version
    Returns the version string, or None if it cannot be determined
    """
    import json
    import urllib.request

    try:
        # Validate the package name to prevent URL manipulation
        if not re.match(r"^[a-zA-Z0-9_-]+$", package_name):
            return None

        # Construct secure HTTPS only PyPI URL
        url = f"https://pypi.org/pypi/{package_name}/json"

        # To validate the URL is what we expect
        if not url.startswith("https://pypi.org/pypi/"):
            return None

        with urllib.request.urlopen(url, timeout=5) as response:  # nosec B310
            data = json.load(response)
            return data["info"]["version"]
    except Exception:
        return None
