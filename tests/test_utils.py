import json
import os
import tempfile
import unittest
import zipfile
from unittest.mock import mock_open, patch
from urllib.error import URLError

from ipachecker.utils import (
    format_file_size,
    get_latest_pypi_version,
    is_valid_url,
    sanitize_filename,
    validate_ipa_file,
)


class UtilsTest(unittest.TestCase):

    def test_is_valid_url_with_valid_urls(self):
        valid_urls = [
            "https://example.com/app.ipa",
            "http://test.domain.com/files/myapp.ipa",
            "https://downloads.example.org/apps/test-app.ipa",
            "ftp://files.example.net/app.ipa",
        ]

        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(is_valid_url(url))

    def test_is_valid_url_with_invalid_urls(self):
        invalid_urls = [
            "not-a-url",
            "just-text",
            "file.ipa",
            "//incomplete-url",
            "https://",
            "http://",
            "ftp:",
            "",
            None,
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                if url is None:
                    with self.assertRaises(AttributeError):
                        is_valid_url(url)
                else:
                    self.assertFalse(is_valid_url(url))

    def test_sanitize_filename_with_valid_names(self):
        valid_names = ["normal_filename.ipa", "app-name-v2.ipa", "MyApp_1.0.0.ipa", "test123.ipa"]

        for name in valid_names:
            with self.subTest(name=name):
                result = sanitize_filename(name)
                self.assertEqual(result, name)

    def test_sanitize_filename_with_invalid_characters(self):
        test_cases = [
            ("app<name>.ipa", "app_name_.ipa"),
            ("app:name.ipa", "app_name.ipa"),
            ('app"name".ipa', "app_name_.ipa"),
            ("app/name\\test.ipa", "app_name_test.ipa"),
            ("app|name?.ipa", "app_name_.ipa"),
            ("app*name.ipa", "app_name.ipa"),
        ]

        for input_name, expected in test_cases:
            with self.subTest(input=input_name):
                result = sanitize_filename(input_name)
                self.assertEqual(result, expected)

    def test_sanitize_filename_with_leading_trailing_chars(self):
        test_cases = [
            ("  app.ipa  ", "app.ipa"),
            ("...app.ipa...", "app.ipa"),
            ("  .app.ipa.  ", "app.ipa"),
            (" . app . ipa . ", "app . ipa"),
        ]

        for input_name, expected in test_cases:
            with self.subTest(input=input_name):
                result = sanitize_filename(input_name)
                self.assertEqual(result, expected)

    def test_sanitize_filename_empty_name(self):
        empty_inputs = ["", "   ", "...", " . "]

        for empty_input in empty_inputs:
            with self.subTest(input=empty_input):
                result = sanitize_filename(empty_input)
                self.assertEqual(result, "download")

    def test_sanitize_filename_long_name(self):
        # Create a very long filename
        long_name = "a" * 250 + ".ipa"
        result = sanitize_filename(long_name)

        # Should be truncated but keep extension
        self.assertTrue(result.endswith(".ipa"))
        self.assertLessEqual(len(result), 204)  # 200 + '.ipa'

    def test_format_file_size_bytes(self):
        test_cases = [(0, "0 B"), (1, "1.0 B"), (512, "512.0 B"), (1023, "1023.0 B")]

        for size_bytes, expected in test_cases:
            with self.subTest(size=size_bytes):
                result = format_file_size(size_bytes)
                self.assertEqual(result, expected)

    def test_format_file_size_kilobytes(self):
        test_cases = [(1024, "1.0 KB"), (1536, "1.5 KB"), (2048, "2.0 KB"), (1024 * 100, "100.0 KB")]

        for size_bytes, expected in test_cases:
            with self.subTest(size=size_bytes):
                result = format_file_size(size_bytes)
                self.assertEqual(result, expected)

    def test_format_file_size_megabytes(self):
        test_cases = [(1024 * 1024, "1.0 MB"), (1024 * 1024 * 2.5, "2.5 MB"), (1024 * 1024 * 100, "100.0 MB")]

        for size_bytes, expected in test_cases:
            with self.subTest(size=size_bytes):
                result = format_file_size(int(size_bytes))
                self.assertEqual(result, expected)

    def test_format_file_size_gigabytes(self):
        test_cases = [(1024 * 1024 * 1024, "1.0 GB"), (1024 * 1024 * 1024 * 2.5, "2.5 GB")]

        for size_bytes, expected in test_cases:
            with self.subTest(size=size_bytes):
                result = format_file_size(int(size_bytes))
                self.assertEqual(result, expected)

    def test_format_file_size_terabytes(self):
        tb_size = 1024 * 1024 * 1024 * 1024
        result = format_file_size(tb_size)
        self.assertEqual(result, "1.0 TB")

    def test_validate_ipa_file_not_exists(self):
        is_valid, error = validate_ipa_file("/nonexistent/file.ipa")

        self.assertFalse(is_valid)
        self.assertIn("File not found", error)

    def test_validate_ipa_file_wrong_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file_path = temp_file.name

        try:
            is_valid, error = validate_ipa_file(temp_file_path)

            self.assertFalse(is_valid)
            self.assertIn("must have .ipa extension", error)
        finally:
            os.unlink(temp_file_path)

    def test_validate_ipa_file_empty_file(self):
        with tempfile.NamedTemporaryFile(suffix=".ipa", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            is_valid, error = validate_ipa_file(temp_file_path)

            self.assertFalse(is_valid)
            self.assertIn("File is empty", error)
        finally:
            os.unlink(temp_file_path)

    def test_validate_ipa_file_not_zip(self):
        with tempfile.NamedTemporaryFile(suffix=".ipa", delete=False) as temp_file:
            temp_file.write(b"not a zip file")
            temp_file_path = temp_file.name

        try:
            is_valid, error = validate_ipa_file(temp_file_path)

            self.assertFalse(is_valid)
            self.assertIn("not a valid ZIP archive", error)
        finally:
            os.unlink(temp_file_path)

    def test_validate_ipa_file_no_payload(self):
        # Create a zip file without Payload directory
        with tempfile.NamedTemporaryFile(suffix=".ipa", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            with zipfile.ZipFile(temp_file_path, "w") as zip_file:
                zip_file.writestr("META-INF/MANIFEST.MF", "test content")

            is_valid, error = validate_ipa_file(temp_file_path)

            self.assertFalse(is_valid)
            self.assertIn("missing Payload directory", error)
        finally:
            os.unlink(temp_file_path)

    def test_validate_ipa_file_valid(self):
        # Create a valid IPA-like zip file
        with tempfile.NamedTemporaryFile(suffix=".ipa", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            with zipfile.ZipFile(temp_file_path, "w") as zip_file:
                zip_file.writestr("Payload/TestApp.app/Info.plist", "plist content")
                zip_file.writestr("Payload/TestApp.app/TestApp", "executable")

            is_valid, error = validate_ipa_file(temp_file_path)

            self.assertTrue(is_valid)
            self.assertIsNone(error)
        finally:
            os.unlink(temp_file_path)

    def test_validate_ipa_file_exception_handling(self):
        # Test general exception handling
        with patch("zipfile.ZipFile") as mock_zip:
            mock_zip.side_effect = Exception("Unexpected error")

            with tempfile.NamedTemporaryFile(suffix=".ipa", delete=False) as temp_file:
                temp_file.write(b"some content")
                temp_file_path = temp_file.name

            try:
                is_valid, error = validate_ipa_file(temp_file_path)

                self.assertFalse(is_valid)
                self.assertIn("Error validating file", error)
                self.assertIn("Unexpected error", error)
            finally:
                os.unlink(temp_file_path)

    @patch("urllib.request.urlopen")
    def test_get_latest_pypi_version_success(self, mock_urlopen):
        # Mock successful API response
        mock_response_data = {"info": {"version": "2.0.0"}}
        mock_response = mock_open(read_data=json.dumps(mock_response_data).encode())
        mock_urlopen.return_value.__enter__.return_value = mock_response.return_value

        result = get_latest_pypi_version("ipachecker")

        self.assertEqual(result, "2.0.0")

    @patch("urllib.request.urlopen")
    def test_get_latest_pypi_version_network_error(self, mock_urlopen):
        # Mock network error
        mock_urlopen.side_effect = URLError("Network error")

        result = get_latest_pypi_version("ipachecker")

        self.assertIsNone(result)

    @patch("urllib.request.urlopen")
    def test_get_latest_pypi_version_timeout(self, mock_urlopen):
        # Mock timeout
        mock_urlopen.side_effect = TimeoutError("Connection timeout")

        result = get_latest_pypi_version("ipachecker")

        self.assertIsNone(result)

    @patch("urllib.request.urlopen")
    def test_get_latest_pypi_version_invalid_json(self, mock_urlopen):
        # Mock invalid JSON response
        mock_response = mock_open(read_data=b"invalid json")
        mock_urlopen.return_value.__enter__.return_value = mock_response.return_value

        result = get_latest_pypi_version("ipachecker")

        self.assertIsNone(result)

    @patch("urllib.request.urlopen")
    def test_get_latest_pypi_version_missing_version(self, mock_urlopen):
        # Mock response without version info
        mock_response_data = {"info": {}}
        mock_response = mock_open(read_data=json.dumps(mock_response_data).encode())
        mock_urlopen.return_value.__enter__.return_value = mock_response.return_value

        result = get_latest_pypi_version("ipachecker")

        self.assertIsNone(result)

    def test_get_latest_pypi_version_custom_package(self):
        # Test with custom package name
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response_data = {"info": {"version": "1.5.0"}}
            mock_response = mock_open(read_data=json.dumps(mock_response_data).encode())
            mock_urlopen.return_value.__enter__.return_value = mock_response.return_value

            result = get_latest_pypi_version("custom-package")

            self.assertEqual(result, "1.5.0")
            # Verify correct URL was called
            called_url = mock_urlopen.call_args[0][0]
            self.assertIn("custom-package", called_url.url)
