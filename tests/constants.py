# Test constants and sample data for ipachecker tests

# Sample Info.plist data for testing
sample_info_plist = {
    'CFBundleName': 'TestApp',
    'CFBundleDisplayName': 'Test Application',
    'CFBundleIdentifier': 'com.example.testapp',
    'CFBundleVersion': '1.2.3',
    'CFBundleShortVersionString': '1.2',
    'CFBundleExecutable': 'TestApp',
    'MinimumOSVersion': '13.0',
    'CFBundleInfoDictionaryVersion': '6.0',
    'CFBundlePackageType': 'APPL',
    'CFBundleSignature': '????',
    'LSRequiresIPhoneOS': True,
    'UIDeviceFamily': [1, 2],
    'UISupportedInterfaceOrientations': [
        'UIInterfaceOrientationPortrait',
        'UIInterfaceOrientationLandscapeLeft',
        'UIInterfaceOrientationLandscapeRight'
    ],
    'NSAppTransportSecurity': {
        'NSAllowsArbitraryLoads': False
    }
}

# Sample Info.plist for an older app without MinimumOSVersion
sample_old_info_plist = {
    'CFBundleName': 'OldApp',
    'CFBundleDisplayName': 'Legacy Application',
    'CFBundleIdentifier': 'com.legacy.oldapp',
    'CFBundleVersion': '1.0',
    'CFBundleExecutable': 'OldApp',
    'CFBundleInfoDictionaryVersion': '6.0',
    'CFBundlePackageType': 'APPL'
}

# Sample result for an encrypted IPA
sample_encrypted_ipa_result = {
    'appName': 'TestApp',
    'displayName': 'Test Application',
    'bundleId': 'com.example.testapp',
    'appVersion': '1.2.3',
    'minIOS': '13.0',
    'architecture': '64-bit',
    'encrypted': True,
    'obscuraFilename': 'Test Application-(com.example.testapp)-1.2.3-(iOS_13.0)-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6.ipa',
    'md5': 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6',
    'fileSize': 5242880,
    'filePath': '/path/to/encrypted_app.ipa'
}

# Sample result for a decrypted IPA
sample_decrypted_ipa_result = {
    'appName': 'DecryptedApp',
    'displayName': 'Decrypted Application',
    'bundleId': 'com.example.decryptedapp',
    'appVersion': '2.0.1',
    'minIOS': '14.0',
    'architecture': 'Universal',
    'encrypted': False,
    'obscuraFilename': 'Decrypted Application-(com.example.decryptedapp)-2.0.1-(iOS_14.0)-z9y8x7w6v5u4t3s2r1q0p9o8n7m6l5k4.ipa',
    'md5': 'z9y8x7w6v5u4t3s2r1q0p9o8n7m6l5k4',
    'fileSize': 10485760,
    'filePath': '/path/to/decrypted_app.ipa'
}

# Sample result for a 32-bit app
sample_32bit_ipa_result = {
    'appName': 'LegacyApp',
    'displayName': 'Legacy 32-bit App',
    'bundleId': 'com.legacy.app32',
    'appVersion': '1.0.0',
    'minIOS': '8.0',
    'architecture': '32-bit',
    'encrypted': True,
    'obscuraFilename': 'Legacy 32-bit App-(com.legacy.app32)-1.0.0-(iOS_8.0)-f1e2d3c4b5a6978685746352190fedcb.ipa',
    'md5': 'f1e2d3c4b5a6978685746352190fedcb',
    'fileSize': 2097152,
    'filePath': '/path/to/legacy_app.ipa'
}

# Sample batch analysis results
sample_batch_results = [
    sample_encrypted_ipa_result,
    sample_decrypted_ipa_result,
    {
        'error': 'File not found: /path/to/missing.ipa'
    },
    sample_32bit_ipa_result,
    {
        'error': 'Failed to download IPA from https://invalid-url.com/app.ipa'
    }
]

# Sample download URLs for testing
sample_download_urls = [
    'https://example.com/apps/testapp-v1.2.3.ipa',
    'https://releases.example.org/ios/myapp.ipa',
    'https://cdn.example.net/mobile/apps/demo-app-encrypted.ipa'
]

# Sample file paths for batch testing
sample_file_paths = [
    '/Users/test/Downloads/app1.ipa',
    '/Users/test/Downloads/app2.ipa',
    '/Users/test/Downloads/app3.ipa'
]

# Sample mixed list (URLs and file paths) for testing
sample_mixed_inputs = [
    '/Users/test/Downloads/local-app.ipa',
    'https://example.com/remote-app.ipa',
    '/Applications/Another App.ipa',
    'https://downloads.example.com/encrypted-app.ipa'
]

# Sample curl output for testing download progress
sample_curl_progress_output = """
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
  3 5242k    3  188k    0     0   187k      0  0:00:28  0:00:01  0:00:27  187k
 12 5242k   12  678k    0     0   339k      0  0:00:15  0:00:02  0:00:13  339k
 28 5242k   28 1544k    0     0   515k      0  0:00:10  0:00:03  0:00:07  515k
 50 5242k   50 2638k    0     0   659k      0  0:00:07  0:00:04  0:00:03  659k
 75 5242k   75 3956k    0     0   791k      0  0:00:06  0:00:05  0:00:01  791k
100 5242k  100 5242k    0     0   874k      0  0:00:06  0:00:06 --:--:--  874k
"""

# Error messages for testing
error_messages = {
    'file_not_found': 'File not found: {}',
    'invalid_extension': 'File must be a .ipa file: {}',
    'download_failed': 'Failed to download IPA from {}',
    'invalid_ipa': 'File does not appear to be a valid IPA (missing Payload directory)',
    'extraction_failed': 'Failed to extract IPA file',
    'no_executable': 'App executable not found',
    'no_metadata': 'Failed to read app metadata',
    'network_error': 'Network error occurred while downloading',
    'permission_denied': 'Permission denied when accessing file'
}

# Sample metadata with various edge cases
sample_metadata_edge_cases = {
    'empty_display_name': {
        'CFBundleName': 'App',
        'CFBundleDisplayName': '',
        'CFBundleIdentifier': 'com.test.app',
        'CFBundleVersion': '1.0',
        'CFBundleExecutable': 'App'
    },
    'missing_display_name': {
        'CFBundleName': 'App',
        'CFBundleIdentifier': 'com.test.app',
        'CFBundleVersion': '1.0',
        'CFBundleExecutable': 'App'
    },
    'unicode_app_name': {
        'CFBundleName': '测试应用',
        'CFBundleDisplayName': '测试应用程序',
        'CFBundleIdentifier': 'com.test.unicode',
        'CFBundleVersion': '1.0.0',
        'CFBundleExecutable': 'TestApp'
    },
    'very_long_bundle_id': {
        'CFBundleName': 'LongBundleApp',
        'CFBundleDisplayName': 'App with Very Long Bundle ID',
        'CFBundleIdentifier': 'com.example.very.long.bundle.identifier.that.might.cause.issues.with.filename.generation',
        'CFBundleVersion': '1.0',
        'CFBundleExecutable': 'LongBundleApp'
    }
}