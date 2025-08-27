import json
import os
import plistlib
import shutil
import tempfile
import unittest
import zipfile
from unittest.mock import MagicMock, mock_open, patch

import requests_mock

from ipachecker import __version__
from ipachecker.IPAChecker import IPAChecker

from .constants import sample_decrypted_ipa_result, sample_encrypted_ipa_result, sample_info_plist

current_path = os.path.dirname(os.path.realpath(__file__))


def get_testfile_path(name):
    return os.path.join(current_path, "test_ipachecker_files", name)


class MockMachO:
    """Mock class for macholib.MachO.MachO"""

    def __init__(self, filename):
        self.headers = []

        # Create mock header based on filename to simulate different scenarios
        mock_header = MagicMock()

        if "encrypted" in filename:
            # Mock encrypted binary
            mock_command = MagicMock()
            mock_command.cryptid = 1
            mock_header.commands = [(None, mock_command)]
        else:
            # Mock decrypted binary
            mock_command = MagicMock()
            mock_command.cryptid = 0
            mock_header.commands = [(None, mock_command)]

        # Set architecture based on filename
        if "arm64" in filename:
            mock_header.header.cputype = 16777228  # ARM64
        elif "universal" in filename:
            mock_header.header.cputype = 16777228  # ARM64
            # Add second header for universal binary
            mock_header2 = MagicMock()
            mock_header2.header.cputype = 12  # ARMv7
            mock_header2.commands = mock_header.commands
            self.headers = [mock_header, mock_header2]
            return
        else:
            mock_header.header.cputype = 12  # ARMv7

        self.headers = [mock_header]


class MockEncryptionInfoCommand:
    """Mock encryption info command"""

    def __init__(self, cryptid=1):
        self.cryptid = cryptid


def create_mock_ipa_file(path, app_name="TestApp", encrypted=True, universal=False):
    """Create a mock IPA file for testing"""
    with zipfile.ZipFile(path, "w") as zip_file:
        # Create mock app structure
        app_dir = f"Payload/{app_name}.app/"

        # Create Info.plist
        info_plist = {
            "CFBundleName": app_name,
            "CFBundleDisplayName": f"{app_name} Display",
            "CFBundleIdentifier": f"com.test.{app_name.lower()}",
            "CFBundleVersion": "1.0.0",
            "CFBundleExecutable": app_name,
            "MinimumOSVersion": "12.0",
        }

        plist_data = plistlib.dumps(info_plist)
        zip_file.writestr(f"{app_dir}Info.plist", plist_data)

        # Create mock executable
        exec_name = app_name
        if encrypted:
            exec_name += "_encrypted"
        if universal:
            exec_name += "_universal"

        zip_file.writestr(f"{app_dir}{app_name}", b"mock_executable_data")


@patch("ipachecker.IPAChecker.macholib.MachO.MachO", MockMachO)
class IPACheckerTests(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.checker = IPAChecker(verbose=False, work_dir=self.test_dir)
        self.maxDiff = None

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init_with_default_parameters(self):
        checker = IPAChecker()
        self.assertFalse(checker.verbose)
        self.assertEqual(checker.work_dir, os.path.expanduser("~/.ipachecker"))
        self.assertTrue(checker.delete_downloaded)

    def test_init_with_custom_parameters(self):
        custom_dir = "/tmp/test_ipa"
        checker = IPAChecker(verbose=True, work_dir=custom_dir, delete_downloaded=False)
        self.assertTrue(checker.verbose)
        self.assertEqual(checker.work_dir, custom_dir)
        self.assertFalse(checker.delete_downloaded)

    def test_check_ipa_with_local_file_success(self):
        # Create test IPA file
        test_ipa = os.path.join(self.test_dir, "test.ipa")
        create_mock_ipa_file(test_ipa, "TestApp", encrypted=False)

        result = self.checker.check_ipa(test_ipa)

        self.assertNotIn("error", result)
        self.assertEqual(result["appName"], "TestApp")
        self.assertEqual(result["displayName"], "TestApp Display")
        self.assertEqual(result["bundleId"], "com.test.testapp")
        self.assertEqual(result["appVersion"], "1.0.0")
        self.assertEqual(result["minIOS"], "12.0")
        self.assertFalse(result["encrypted"])

    def test_check_ipa_with_encrypted_file(self):
        # Create test IPA file with encrypted binary
        test_ipa = os.path.join(self.test_dir, "encrypted_test.ipa")
        create_mock_ipa_file(test_ipa, "EncryptedApp", encrypted=True)

        result = self.checker.check_ipa(test_ipa)

        self.assertNotIn("error", result)
        self.assertTrue(result["encrypted"])

    def test_check_ipa_with_universal_binary(self):
        # Create test IPA file with universal binary
        test_ipa = os.path.join(self.test_dir, "universal_test.ipa")
        create_mock_ipa_file(test_ipa, "UniversalApp", encrypted=False, universal=True)

        result = self.checker.check_ipa(test_ipa)

        self.assertNotIn("error", result)
        self.assertEqual(result["architecture"], "Universal")

    def test_check_ipa_file_not_found(self):
        result = self.checker.check_ipa("/nonexistent/file.ipa")

        self.assertIn("error", result)
        self.assertIn("File not found", result["error"])

    def test_check_ipa_invalid_extension(self):
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("not an ipa")

        result = self.checker.check_ipa(test_file)

        self.assertIn("error", result)
        self.assertIn("must be a .ipa file", result["error"])

    @patch("subprocess.Popen")
    def test_download_ipa_success(self, mock_popen):
        # Mock successful curl download
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.wait.return_value = None
        mock_process.stderr.readline.return_value = ""
        mock_popen.return_value = mock_process

        # Create a fake downloaded file
        test_url = "https://example.com/test.ipa"
        expected_path = os.path.join(self.test_dir, "test.ipa")

        # Mock the file creation
        with patch("os.path.exists") as mock_exists, patch("os.path.getsize") as mock_getsize:
            mock_exists.return_value = True
            mock_getsize.return_value = 1000

            result = self.checker._download_ipa(test_url)

        self.assertEqual(result, expected_path)
        mock_popen.assert_called_once()

    @patch("subprocess.Popen")
    def test_download_ipa_failure(self, mock_popen):
        # Mock failed curl download
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.wait.return_value = None
        mock_popen.return_value = mock_process

        test_url = "https://example.com/test.ipa"
        result = self.checker._download_ipa(test_url)

        self.assertIsNone(result)

    def test_check_ipa_with_url(self):
        test_url = "https://example.com/test.ipa"

        with patch.object(self.checker, "_download_ipa") as mock_download:
            test_ipa = os.path.join(self.test_dir, "downloaded.ipa")
            create_mock_ipa_file(test_ipa, "DownloadedApp")
            mock_download.return_value = test_ipa

            result = self.checker.check_ipa(test_url)

            self.assertNotIn("error", result)
            self.assertEqual(result["appName"], "DownloadedApp")
            mock_download.assert_called_once_with(test_url)

    def test_check_ipa_with_invalid_url(self):
        test_url = "https://example.com/test.ipa"

        with patch.object(self.checker, "_download_ipa") as mock_download:
            mock_download.return_value = None

            result = self.checker.check_ipa(test_url)

            self.assertIn("error", result)
            self.assertIn("Failed to download", result["error"])

    def test_batch_analyze_folder(self):
        # Create test folder with multiple IPA files
        test_folder = os.path.join(self.test_dir, "test_ipas")
        os.makedirs(test_folder)

        # Create test IPA files
        ipa1 = os.path.join(test_folder, "app1.ipa")
        ipa2 = os.path.join(test_folder, "app2.ipa")
        create_mock_ipa_file(ipa1, "App1", encrypted=False)
        create_mock_ipa_file(ipa2, "App2", encrypted=True)

        results = self.checker.batch_analyze_folder(test_folder)

        self.assertEqual(len(results), 2)
        # Results should contain both apps
        app_names = [r["appName"] for r in results if "error" not in r]
        self.assertIn("App1", app_names)
        self.assertIn("App2", app_names)

    def test_batch_analyze_folder_not_found(self):
        results = self.checker.batch_analyze_folder("/nonexistent/folder")

        self.assertEqual(len(results), 1)
        self.assertIn("error", results[0])
        self.assertIn("Folder not found", results[0]["error"])

    def test_batch_analyze_folder_no_ipas(self):
        # Create empty folder
        empty_folder = os.path.join(self.test_dir, "empty")
        os.makedirs(empty_folder)

        results = self.checker.batch_analyze_folder(empty_folder)

        self.assertEqual(len(results), 1)
        self.assertIn("error", results[0])
        self.assertIn("No .ipa files found", results[0]["error"])

    def test_batch_analyze_from_file(self):
        # Create test IPA files
        ipa1 = os.path.join(self.test_dir, "app1.ipa")
        ipa2 = os.path.join(self.test_dir, "app2.ipa")
        create_mock_ipa_file(ipa1, "App1")
        create_mock_ipa_file(ipa2, "App2")

        # Create file list
        list_file = os.path.join(self.test_dir, "ipa_list.txt")
        with open(list_file, "w") as f:
            f.write(f"{ipa1}\n")
            f.write(f"{ipa2}\n")
            f.write("https://example.com/app3.ipa\n")

        with patch.object(self.checker, "_download_ipa") as mock_download:
            ipa3 = os.path.join(self.test_dir, "app3.ipa")
            create_mock_ipa_file(ipa3, "App3")
            mock_download.return_value = ipa3

            results = self.checker.batch_analyze_from_file(list_file)

        self.assertEqual(len(results), 3)
        app_names = [r["appName"] for r in results if "error" not in r]
        self.assertEqual(len(app_names), 3)

    def test_batch_analyze_from_file_not_found(self):
        results = self.checker.batch_analyze_from_file("/nonexistent/file.txt")

        self.assertEqual(len(results), 1)
        self.assertIn("error", results[0])

    def test_cleanup_downloaded_files(self):
        # Create test files and add to downloaded set
        test_file1 = os.path.join(self.test_dir, "download1.ipa")
        test_file2 = os.path.join(self.test_dir, "download2.ipa")

        with open(test_file1, "w") as f:
            f.write("test")
        with open(test_file2, "w") as f:
            f.write("test")

        self.checker.downloaded_files.add(test_file1)
        self.checker.downloaded_files.add(test_file2)

        self.checker.cleanup_downloaded_files()

        # Files should be deleted
        self.assertFalse(os.path.exists(test_file1))
        self.assertFalse(os.path.exists(test_file2))
        self.assertEqual(len(self.checker.downloaded_files), 0)

    def test_cleanup_downloaded_files_disabled(self):
        # Test with delete_downloaded=False
        checker = IPAChecker(delete_downloaded=False, work_dir=self.test_dir)

        test_file = os.path.join(self.test_dir, "download.ipa")
        with open(test_file, "w") as f:
            f.write("test")

        checker.downloaded_files.add(test_file)
        checker.cleanup_downloaded_files()

        # File should still exist
        self.assertTrue(os.path.exists(test_file))

    def test_get_properties_success(self):
        # Create test extraction directory
        extract_dir = os.path.join(self.test_dir, "extracted")
        payload_dir = os.path.join(extract_dir, "Payload", "TestApp.app")
        os.makedirs(payload_dir)

        # Create Info.plist
        info_plist = sample_info_plist.copy()
        plist_path = os.path.join(payload_dir, "Info.plist")

        with open(plist_path, "wb") as f:
            plistlib.dump(info_plist, f)

        result = self.checker._get_properties(extract_dir)

        self.assertIsNotNone(result)
        self.assertEqual(result["CFBundleName"], "TestApp")

    def test_get_properties_no_plist(self):
        # Create test extraction directory without Info.plist
        extract_dir = os.path.join(self.test_dir, "extracted")
        os.makedirs(extract_dir)

        result = self.checker._get_properties(extract_dir)

        self.assertIsNone(result)

    def test_get_properties_adds_default_minimum_os(self):
        # Create test extraction directory
        extract_dir = os.path.join(self.test_dir, "extracted")
        payload_dir = os.path.join(extract_dir, "Payload", "TestApp.app")
        os.makedirs(payload_dir)

        # Create Info.plist without MinimumOSVersion
        info_plist = {"CFBundleName": "TestApp", "CFBundleIdentifier": "com.test.app"}
        plist_path = os.path.join(payload_dir, "Info.plist")

        with open(plist_path, "wb") as f:
            plistlib.dump(info_plist, f)

        result = self.checker._get_properties(extract_dir)

        self.assertIsNotNone(result)
        self.assertEqual(result["MinimumOSVersion"], "2.0")

    def test_get_cryptid_encrypted(self):
        # Test with encrypted binary (mocked)
        test_binary = os.path.join(self.test_dir, "encrypted_app")
        with open(test_binary, "w") as f:
            f.write("encrypted")

        result = self.checker._get_cryptid(test_binary)

        self.assertTrue(result)

    def test_get_cryptid_decrypted(self):
        # Test with decrypted binary (mocked)
        test_binary = os.path.join(self.test_dir, "decrypted_app")
        with open(test_binary, "w") as f:
            f.write("decrypted")

        result = self.checker._get_cryptid(test_binary)

        self.assertFalse(result)

    def test_get_architecture_arm64(self):
        test_binary = os.path.join(self.test_dir, "arm64_app")
        with open(test_binary, "w") as f:
            f.write("arm64")

        result = self.checker._get_architecture(test_binary)

        self.assertEqual(result, "64-bit")

    def test_get_architecture_universal(self):
        test_binary = os.path.join(self.test_dir, "universal_app")
        with open(test_binary, "w") as f:
            f.write("universal")

        result = self.checker._get_architecture(test_binary)

        self.assertEqual(result, "Universal")

    def test_calculate_md5(self):
        test_file = os.path.join(self.test_dir, "test.ipa")
        test_data = b"test data for md5"

        with open(test_file, "wb") as f:
            f.write(test_data)

        result = self.checker._calculate_md5(test_file)

        # Should be a 32-character hex string
        self.assertEqual(len(result), 32)
        self.assertTrue(all(c in "0123456789abcdef" for c in result))

    def test_print_result_table(self):
        # Test that print methods don't crash (output testing is complex)
        test_result = sample_decrypted_ipa_result.copy()

        # Should not raise exception
        self.checker.print_result_table(test_result)

    def test_print_batch_summary(self):
        # Test batch summary printing
        results = [sample_decrypted_ipa_result.copy(), sample_encrypted_ipa_result.copy(), {"error": "Test error"}]

        # Should not raise exception
        self.checker.print_batch_summary(results)

    def test_analyze_ipa_corrupted_zip(self):
        # Create corrupted zip file
        corrupted_ipa = os.path.join(self.test_dir, "corrupted.ipa")
        with open(corrupted_ipa, "w") as f:
            f.write("not a zip file")

        result = self.checker.check_ipa(corrupted_ipa)

        self.assertIn("error", result)

    def test_extract_ipa_success(self):
        test_ipa = os.path.join(self.test_dir, "test.ipa")
        extract_dir = os.path.join(self.test_dir, "extracted")

        create_mock_ipa_file(test_ipa, "TestApp")

        # Should not raise exception
        self.checker._extract_ipa(test_ipa, extract_dir)

        # Check extraction worked
        self.assertTrue(os.path.exists(os.path.join(extract_dir, "Payload")))
