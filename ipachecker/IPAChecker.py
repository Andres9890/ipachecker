# This python script provided by norep on discord, credits to him
import os
import sys
import glob
import shutil
import zipfile
import hashlib
import plistlib
import subprocess
import tempfile
import json
import logging
import macholib.mach_o
import macholib.MachO
from urllib.parse import urlparse
from rich.console import Console
from rich.table import Table
try:
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, PercentageColumn
except ImportError:
    # Fallback for older versions of rich
    try:
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
        from rich.progress import TaskProgressColumn as PercentageColumn
    except ImportError:
        # Even older version fallback
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
        PercentageColumn = None

from ipachecker import __version__
from ipachecker.utils import is_valid_url, sanitize_filename


class IPAChecker:
    
    def __init__(self, verbose=False, work_dir='~/.ipachecker', delete_downloaded=True):
        """
        IPAChecker - Analyze iOS IPA files for metadata and encryption status.

        :param verbose:           A boolean, True means all loggings will be
                                 printed out to stdout.
        :param work_dir:         A path to directory that will be used for
                                temporary files. Default to '~/.ipachecker'.
        :param delete_downloaded: A boolean, True means downloaded files will be
                                deleted after analysis.
        """
        self.verbose = verbose
        self.work_dir = os.path.expanduser(work_dir)
        self.console = Console()
        self.logger = logging.getLogger(__name__)
        self.delete_downloaded = delete_downloaded
        self.downloaded_files = set()  # Track downloaded files for cleanup
        
        if not self.verbose:
            self.logger.setLevel(logging.ERROR)
            
        # Create work directory
        os.makedirs(self.work_dir, exist_ok=True)
        
    def check_ipa(self, input_source):
        """
        Check an IPA file from local path or URL.
        
        :param input_source: Path to .ipa file or URL to download .ipa file.
        :return:            Dictionary containing analysis results and metadata.
        """
        try:
            was_downloaded = False
            
            # Determine if input is URL or local path
            if is_valid_url(input_source):
                ipa_file = self._download_ipa(input_source)
                if not ipa_file:
                    return {"error": f"Failed to download IPA from {input_source}"}
                was_downloaded = True
                self.downloaded_files.add(ipa_file)
            else:
                ipa_file = input_source
                
            # Validate file exists and is .ipa
            if not os.path.exists(ipa_file):
                return {"error": f"File not found: {ipa_file}"}
                
            if not ipa_file.lower().endswith('.ipa'):
                return {"error": f"File must be a .ipa file: {ipa_file}"}
                
            # Analyze the IPA
            result = self._analyze_ipa(ipa_file)
            
            # Add metadata about the analysis
            if "error" not in result:
                result["_metadata"] = {
                    "was_downloaded": was_downloaded,
                    "source": input_source,
                    "analyzed_at": __import__('datetime').datetime.now().isoformat()
                }
            
            return result
            
        except Exception as e:
            self.logger.exception("Error during IPA check")
            return {"error": str(e)}
    
    def cleanup_downloaded_files(self):
        """
        Clean up downloaded files if delete_downloaded is enabled.
        """
        if not self.delete_downloaded:
            return
            
        cleaned_count = 0
        for file_path in self.downloaded_files.copy():
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    cleaned_count += 1
                    if self.verbose:
                        self.console.print(f"[dim]Deleted downloaded file: {file_path}[/dim]")
                self.downloaded_files.discard(file_path)
            except Exception as e:
                self.logger.error(f"Failed to delete {file_path}: {e}")
        
        if self.verbose and cleaned_count > 0:
            self.console.print(f"[green]Cleaned up {cleaned_count} downloaded file(s)[/green]")
    
    def batch_analyze_folder(self, folder_path):
        """
        Analyze all .ipa files in a folder.
        
        :param folder_path: Path to folder containing .ipa files
        :return:           List of analysis results
        """
        if not os.path.exists(folder_path):
            return [{"error": f"Folder not found: {folder_path}"}]
        
        if not os.path.isdir(folder_path):
            return [{"error": f"Path is not a directory: {folder_path}"}]
        
        # Find all .ipa files in the folder
        ipa_files = glob.glob(os.path.join(folder_path, "*.ipa"))
        
        if not ipa_files:
            return [{"error": f"No .ipa files found in folder: {folder_path}"}]
        
        results = []
        if self.verbose:
            self.console.print(f"[blue]Found {len(ipa_files)} .ipa file(s) in folder[/blue]")
        
        for ipa_file in ipa_files:
            if self.verbose:
                self.console.print(f"\n[yellow]Processing:[/yellow] {os.path.basename(ipa_file)}")
            
            result = self.check_ipa(ipa_file)
            results.append(result)
        
        return results
    
    def batch_analyze_from_file(self, file_path):
        """
        Analyze .ipa files or URLs listed in a text file.
        
        :param file_path: Path to text file containing paths/URLs (one per line)
        :return:         List of analysis results
        """
        if not os.path.exists(file_path):
            return [{"error": f"File not found: {file_path}"}]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            return [{"error": f"Failed to read file {file_path}: {e}"}]
        
        if not lines:
            return [{"error": f"No valid entries found in file: {file_path}"}]
        
        results = []
        if self.verbose:
            self.console.print(f"[blue]Found {len(lines)} entries in file[/blue]")
        
        for i, line in enumerate(lines, 1):
            if self.verbose:
                self.console.print(f"\n[yellow]Processing {i}/{len(lines)}:[/yellow] {line}")
            
            result = self.check_ipa(line)
            results.append(result)
        
        return results
    
    def _download_ipa(self, url):
        """
        Download IPA file from URL using curl.
        
        :param url: URL to download from
        :return:    Path to downloaded file or None if failed
        """
        try:
            filename = sanitize_filename(os.path.basename(urlparse(url).path))
            if not filename.lower().endswith('.ipa'):
                filename += '.ipa'
                
            download_path = os.path.join(self.work_dir, filename)
            
            if self.verbose:
                self.console.print(f"[blue]Downloading from:[/blue] {url}")
                self.console.print(f"[blue]Saving to:[/blue] {download_path}")
            
            # Use curl to download with progress and SSL options to handle certificate revocation issues
            cmd = [
                'curl', 
                '-L',  # Follow redirects
                '-o', download_path,  # Output file
                '--progress-bar',  # Show progress bar
                '--ssl-no-revoke',  # Disable certificate revocation checking (fixes Windows schannel issue)
                '--retry', '3',  # Retry on transient failures
                '--retry-delay', '2',  # Wait between retries
                '--connect-timeout', '30',  # Connection timeout
                '--max-time', '300',  # Maximum time for the entire operation
                url
            ]
            
            if self.verbose:
                # Show curl progress
                process = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True)
                
                for line in iter(process.stderr.readline, ''):
                    if line.strip():
                        sys.stderr.write(f'\r{line.strip()}')
                        sys.stderr.flush()
                        
                process.wait()
                if self.verbose:
                    sys.stderr.write('\n')
            else:
                # Silent download
                process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, 
                                         stderr=subprocess.DEVNULL)
                process.wait()
            
            if process.returncode != 0:
                if self.verbose:
                    self.console.print(f"[red]Curl failed with return code: {process.returncode}[/red]")
                return None
                
            if not os.path.exists(download_path) or os.path.getsize(download_path) == 0:
                if self.verbose:
                    self.console.print(f"[red]Downloaded file is missing or empty[/red]")
                return None
                
            return download_path
            
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            return None
    
    def _analyze_ipa(self, ipa_file):
        """
        Analyze IPA file and extract metadata.
        
        :param ipa_file: Path to IPA file
        :return:        Dictionary containing analysis results
        """
        extract_dir = None
        
        try:
            # Create temporary extraction directory
            extract_dir = tempfile.mkdtemp(prefix='ipachecker_', dir=self.work_dir)
            
            # Create progress columns based on available rich version
            progress_columns = [
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
            ]
            
            # Add percentage column if available
            if PercentageColumn is not None:
                progress_columns.append(PercentageColumn())
            
            with Progress(
                *progress_columns,
                console=self.console,
                disable=not self.verbose
            ) as progress:
                
                task = progress.add_task("Analyzing IPA...", total=100)
                
                # Step 1: Extract IPA (20%)
                progress.update(task, description="Extracting IPA file...", completed=10)
                self._extract_ipa(ipa_file, extract_dir)
                progress.update(task, completed=20)
                
                # Step 2: Read metadata (40%)
                progress.update(task, description="Reading app metadata...", completed=30)
                properties = self._get_properties(extract_dir)
                if not properties:
                    return {"error": "Failed to read app metadata"}
                progress.update(task, completed=40)
                
                # Step 3: Find executable (60%)
                progress.update(task, description="Locating app executable...", completed=50)
                exec_name = properties.get("CFBundleExecutable")
                macho_file = glob.glob(os.path.join(extract_dir, "Payload", "*.app", exec_name))
                if not macho_file:
                    return {"error": "App executable not found"}
                macho_file = macho_file[0]
                progress.update(task, completed=60)
                
                # Step 4: Check encryption (80%)
                progress.update(task, description="Checking encryption status...", completed=70)
                is_encrypted = self._get_cryptid(macho_file)
                progress.update(task, completed=80)
                
                # Step 5: Get architecture (90%)
                progress.update(task, description="Analyzing architecture...", completed=85)
                architecture = self._get_architecture(macho_file)
                progress.update(task, completed=90)
                
                # Step 6: Calculate hash (100%)
                progress.update(task, description="Calculating file hash...", completed=95)
                md5_hash = self._calculate_md5(ipa_file)
                progress.update(task, completed=100, description="Analysis complete!")
            
            # Generate results
            display_name = properties.get('CFBundleDisplayName', properties.get('CFBundleName', 'Unknown'))
            bundle_id = properties.get('CFBundleIdentifier', 'unknown')
            version = properties.get('CFBundleVersion', '1.0')
            min_ios = properties.get('MinimumOSVersion', '2.0')
            
            obscura_filename = f"{display_name}-({bundle_id})-{version}-(iOS_{min_ios})-{md5_hash}.ipa"
            
            return {
                "appName": properties.get("CFBundleName", "Unknown"),
                "displayName": display_name,
                "bundleId": bundle_id,
                "appVersion": version,
                "minIOS": min_ios,
                "architecture": architecture,
                "encrypted": is_encrypted,
                "obscuraFilename": obscura_filename,
                "md5": md5_hash,
                "fileSize": os.path.getsize(ipa_file),
                "filePath": os.path.abspath(ipa_file)
            }
            
        finally:
            # Clean up extraction directory
            if extract_dir and os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
    
    def _extract_ipa(self, ipa_file, extract_dir):
        """Extract IPA file to directory."""
        with zipfile.ZipFile(ipa_file, 'r') as ipa_zip:
            ipa_zip.extractall(extract_dir)
    
    def _get_properties(self, extract_dir):
        """Read app metadata from Info.plist."""
        info_plist = glob.glob(os.path.join(extract_dir, "Payload", "*.app", 'Info.plist'))
        
        if not info_plist:
            return None
        
        info_plist = info_plist[0]
        
        with open(info_plist, "rb") as plist:
            plist_data = plistlib.load(plist)
            # Handle missing MinimumOSVersion for older apps
            if plist_data.get("MinimumOSVersion") is None:
                plist_data["MinimumOSVersion"] = "2.0"
            return plist_data
    
    def _get_cryptid(self, filename):
        """Check if the Mach-O binary is encrypted."""
        try:
            macho = macholib.MachO.MachO(filename)
            for header in macho.headers:
                load_commands = header.commands
                for load_command in load_commands:
                    if isinstance(load_command[1], macholib.mach_o.encryption_info_command):
                        if load_command[1].cryptid == 0:
                            return False
                    if isinstance(load_command[1], macholib.mach_o.encryption_info_command_64):
                        if load_command[1].cryptid == 0:
                            return False
            return True
        except Exception:
            return True  # Assume encrypted if we can't determine
    
    def _get_architecture(self, filename):
        """Get the architecture of the Mach-O binary."""
        try:
            macho = macholib.MachO.MachO(filename)
            supports_32 = False
            supports_64 = False

            for header in macho.headers:
                if header.header.cputype == 16777228:  # ARM64
                    supports_64 = True
                if header.header.cputype == 12:  # ARMv7 and ARMv7s
                    supports_32 = True
                    
            if supports_32 and supports_64:
                return "Universal"
            elif supports_64:
                return "64-bit"
            else:
                return "32-bit"
        except Exception:
            return "Unknown"
    
    def _calculate_md5(self, filepath):
        """Calculate MD5 hash of file."""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def print_result_table(self, results):
        """Print results in a formatted table."""
        table = Table(title=results["displayName"])
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Name", results["appName"])
        table.add_row("Display Name", results["displayName"])
        table.add_row("Bundle Identifier", results["bundleId"])
        table.add_row("Version", results["appVersion"])
        table.add_row("Minimum iOS", results["minIOS"])
        table.add_row("Architecture", results["architecture"])
        
        encryption_color = "[bold red]" if results["encrypted"] else "[bold green]"
        encryption_text = f"{encryption_color}{'YES' if results['encrypted'] else 'NO'}"
        table.add_row("Encrypted", encryption_text)
        
        table.add_row("MD5 Hash", results["md5"])
        table.add_row("File Size", f"{results['fileSize']:,} bytes")
        
        self.console.print(table)
        self.console.print(f"\n[bold]Obscura-format filename:[/bold]")
        self.console.print(f"{results['obscuraFilename']}")
    
    def print_batch_summary(self, results):
        """Print a summary table for batch analysis results."""
        if not results:
            return
        
        # Filter out errors for summary
        valid_results = [r for r in results if "error" not in r]
        error_count = len(results) - len(valid_results)
        
        summary_table = Table(title="Batch Analysis Summary")
        summary_table.add_column("Property", style="cyan")
        summary_table.add_column("Value", style="white")
        
        summary_table.add_row("Total Files", str(len(results)))
        summary_table.add_row("Successfully Analyzed", str(len(valid_results)))
        summary_table.add_row("Errors", str(error_count))
        
        if valid_results:
            encrypted_count = sum(1 for r in valid_results if r.get("encrypted", True))
            summary_table.add_row("Encrypted Apps", str(encrypted_count))
            summary_table.add_row("Decrypted Apps", str(len(valid_results) - encrypted_count))
        
        self.console.print("\n")
        self.console.print(summary_table)
# This python script provided by norep on discord, credits to him