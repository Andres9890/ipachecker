---
name: Bug report
about: Create a bug report to help us improve ipachecker
title: 'Bug report: '
labels: bug
assignees: ''

---

**Checklist**

# If you just delete all this text and post an issue it will be closed on sight.

Carefully read and work through this check list in order to prevent the most common mistakes and misuse of ipachecker, Put x into all relevant boxes (like this [x])

- [ ] I understand that ipachecker is a tool for analyzing iOS IPA files and checking their encryption status, not for jailbreaking or decrypting apps
- [ ] I've updated `ipachecker` and its dependencies (`macholib`, `rich`, `docopt-ng`) to their latest stable versions
- [ ] I've included the full and unredacted command and console output (with the exception of file paths that may contain sensitive information like usernames), I understand that hiding relevant information will get the issue closed on sight
- [ ] I've verified that the IPA file I'm trying to analyze is not corrupted and can be opened as a ZIP archive
- [ ] I've searched the existing issues (both open and closed) for similar bug reports
- [ ] I'm not reporting issues with files that are not valid IPA files (e.g., APK files, regular ZIP files, corrupted downloads)
- [ ] If reporting download issues, I've verified that the URL is accessible and returns a valid IPA file when accessed directly in a browser
- [ ] I have properly indented [with triple backticks - the key directly below Escape on a QWERTY keyboard - before and after the console output](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#quoting-code) the full terminal output from the line where the command was run to where I was returned to the command prompt

**System Information**

Please provide the following information:

Operating System: (e.g., macOS 26, Ubuntu 22.04, Windows 11)

Python version:
```
python --version
```

ipachecker version:
```
ipachecker --version
```

**Description of the bug**
A clear and concise description of what the bug is and what you were trying to accomplish.

**Command used**
The exact command you ran that produced the bug:
```
# Example:
ipachecker /path/to/app.ipa
```

**Wanted behavior**
A clear and concise description of what you wanted to happen

**Actual behavior**
A clear and concise description of what actually happened

**Full console output**
```
# Paste the complete terminal output here, including the command you ran
# and all output until you were returned to the command prompt
```

**Additional context**

**File Information** (if applicable):
- IPA file size: 
- Source of IPA file: (e.g., App Store backup, third-party download, etc)
- App name and version (if known):

**Error Details** (if applicable):
- Does this happen with multiple IPA files or just one specific file?
- Does the issue occur consistently or intermittently?
- Are there any specific patterns you've noticed?

**Screenshots** (if applicable):
Add screenshots to help explain your problem, especially if there are GUI-related issues.

**Workarounds** (if any):
If you've found any temporary workarounds, please describe them here

**Additional context**
Add any other context about the problem here that might be helpful for debugging