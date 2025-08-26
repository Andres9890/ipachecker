import re
import os
from urllib.parse import urlparse


def is_valid_url(url):
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


def sanitize_filename(filename):
    """
    Sanitize a filename by removing/replacing invalid characters.
    
    :param filename:    Original filename
    :return:           Sanitized filename safe for filesystem
    """
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    
    # Ensure filename is not empty
    if not filename:
        filename = 'download'
        
    # Limit filename length
    name, ext = os.path.splitext(filename)
    if len(name) > 200:  # Leave room for extension
        name = name[:200]
        
    return name + ext


def format_file_size(size_bytes):
    """
    Format file size in human readable format.
    
    :param size_bytes: Size in bytes
    :return:          Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
        
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
        
    return f"{size_bytes:.1f} {size_names[i]}"


def validate_ipa_file(filepath):
    """
    Validate that a file is likely an IPA file.
    
    :param filepath: Path to file to validate
    :return:        Tuple of (is_valid, error_message)
    """
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"
        
    if not filepath.lower().endswith('.ipa'):
        return False, f"File must have .ipa extension: {filepath}"
        
    if os.path.getsize(filepath) == 0:
        return False, f"File is empty: {filepath}"
        
    # Try to open as zip file (IPA files are zip archives)
    try:
        import zipfile
        with zipfile.ZipFile(filepath, 'r') as zf:
            # Check for typical IPA structure
            files = zf.namelist()
            has_payload = any(f.startswith('Payload/') for f in files)
            if not has_payload:
                return False, "File does not appear to be a valid IPA (missing Payload directory)"
    except zipfile.BadZipFile:
        return False, "File is not a valid ZIP archive"
    except Exception as e:
        return False, f"Error validating file: {e}"
        
    return True, None


def get_latest_pypi_version(package_name="ipachecker"):
    """
    Request PyPI for the latest version
    Returns the version string, or None if it cannot be determined
    """
    import json
    import urllib.request
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.load(response)
            return data["info"]["version"]
    except Exception:
        return None