#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Setup embedded Python distribution for ChooseYourDestiny project."""

import sys
import os
import argparse
import shutil
import zipfile
import tarfile
import subprocess
import urllib.request
import tempfile
from pathlib import Path

# Set output encoding to UTF-8 for proper character display
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.stdout:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


PYTHON_VERSIONS = {
    "3.14.6": "3146",
    "3.14.5": "3145",
    "3.14.4": "3144",
    "3.14.3": "3143",
    "3.14.2": "3142",
    "3.14.1": "3141",
    "3.14.0": "3140",
    "3.13.1": "3131",
    "3.13.0": "3130",
    "3.12.8": "3128",
    "3.12.7": "3127",
    "3.11.9": "3119",
    "3.11.8": "3118",
}

ARCH_MAP = {
    "32bit": "win32",
    "64bit": "win-amd64",
}


def get_download_urls(version, arch_key):
    """Get Python download URLs for both embedded and full distributions."""
    # Map architecture keys to their naming convention in URLs
    if arch_key == "32bit":
        arch_code = "win32"
    else:  # 64bit
        arch_code = "amd64"
    
    # Embedded distribution (lightweight, no tkinter)
    embedded_url = f"https://www.python.org/ftp/python/{version}/python-{version}-embed-{arch_code}.zip"
    
    # Full distribution (includes tkinter and other libraries)
    full_url = f"https://www.python.org/ftp/python/{version}/python-{version}-{arch_code}.zip"
    
    return embedded_url, full_url


def install_packages_from_wheels(python_exe, dist_path, requirements_file):
    """Install packages by downloading and extracting wheels/source distributions (no pip required)."""
    # Use site-packages for installed packages
    site_packages = dist_path / "Lib" / "site-packages"
    site_packages.mkdir(parents=True, exist_ok=True)
    
    installed_packages = []
    failed_packages = []
    
    try:
        # Try to read with UTF-16 BOM, fall back to UTF-8
        try:
            with open(requirements_file, 'r', encoding='utf-16') as f:
                lines = f.readlines()
        except:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Parse package name and version
            if ';' in line:
                line = line.split(';')[0].strip()  # Remove python version constraints
            
            if '==' in line:
                pkg_name, version = line.split('==')
                pkg_name = pkg_name.strip()
                version = version.strip()
            else:
                pkg_name = line.strip()
                version = None
            
            if not version:
                print(f"  ⚠ Skipping {pkg_name} (no version specified)")
                continue
            
            # Get distribution URLs from PyPI JSON API
            try:
                print(f"  Downloading {pkg_name}=={version}...")
                pypi_api_url = f"https://pypi.org/pypi/{pkg_name}/{version}/json"
                response = urllib.request.urlopen(pypi_api_url)
                pypi_data = __import__('json').loads(response.read().decode())
                
                # Find suitable distribution: prefer wheel over tar.gz
                dist_url = None
                dist_file = None
                
                for file_info in pypi_data.get('urls', []):
                    filename = file_info.get('filename', '')
                    
                    # Look for py3 wheel first
                    if '.whl' in filename and 'py3-none-any' in filename:
                        dist_url = file_info['url']
                        dist_file = filename
                        break
                    # Fall back to py2.py3 wheel
                    elif '.whl' in filename and 'py2.py3-none-any' in filename and not dist_url:
                        dist_url = file_info['url']
                        dist_file = filename
                    # Fall back to tar.gz source
                    elif filename.endswith('.tar.gz') and not dist_url:
                        dist_url = file_info['url']
                        dist_file = filename
                
                if not dist_url:
                    print(f"  ✗ Could not find suitable distribution for {pkg_name}=={version}")
                    failed_packages.append(f"{pkg_name} (no distribution found)")
                    continue
                
                # Download distribution
                temp_file = Path(tempfile.gettempdir()) / dist_file
                urllib.request.urlretrieve(dist_url, str(temp_file))
                
                # Extract distribution
                print(f"  Extracting {pkg_name}...")
                
                if temp_file.suffix == '.whl':
                    # Extract wheel to site-packages
                    with zipfile.ZipFile(str(temp_file), 'r') as zf:
                        zf.extractall(str(site_packages))
                elif temp_file.suffix == '.gz':
                    # Extract tar.gz - find the package directory
                    with tarfile.open(str(temp_file), 'r:gz') as tf:
                        # Extract to temp directory first
                        extract_temp = Path(tempfile.gettempdir()) / f"{pkg_name}_{version}_extract"
                        if extract_temp.exists():
                            shutil.rmtree(extract_temp)
                        tf.extractall(str(extract_temp))
                        
                        # Find the package directory within the extracted source
                        source_dir = None
                        
                        # Step 1: Find the root subdirectory (usually {package-version})
                        subdirs = list(extract_temp.glob('*'))
                        if subdirs and subdirs[0].is_dir():
                            root_extracted = subdirs[0]
                            
                            # Step 2: Look for package directory in the root
                            pkg_name_normalized = pkg_name.replace('-', '_')
                            for item in root_extracted.iterdir():
                                if item.is_dir() and (item.name == pkg_name or item.name == pkg_name_normalized):
                                    if (item / '__init__.py').exists():
                                        source_dir = item
                                        break
                        
                        # Copy the package to site-packages if found
                        if source_dir and source_dir.exists():
                            dest_dir = site_packages / source_dir.name
                            if dest_dir.exists():
                                shutil.rmtree(dest_dir)
                            shutil.copytree(source_dir, dest_dir)
                        
                        # Cleanup extract temp
                        if extract_temp.exists():
                            shutil.rmtree(extract_temp)
                
                installed_packages.append(f"{pkg_name}=={version}")
                print(f"  ✓ Installed {pkg_name}=={version}")
                
                # Cleanup
                if temp_file.exists():
                    temp_file.unlink()
                        
            except Exception as e:
                print(f"  ✗ Failed to install {pkg_name}: {str(e)[:50]}")
                failed_packages.append(f"{pkg_name} ({str(e)[:40]})")
    
    except Exception as e:
        print(f"  ✗ Error reading requirements file: {e}")
    
    if installed_packages:
        print(f"  ✓ Installed {len(installed_packages)} package(s)")
        for pkg in installed_packages:
            print(f"    - {pkg}")
    
    if failed_packages:
        print(f"  ⚠ Failed to install {len(failed_packages)} package(s)")
        for pkg in failed_packages:
            print(f"    - {pkg}")
    
    return installed_packages, failed_packages





def download_file(url, dest_path):
    """Download file from URL."""
    if os.path.exists(dest_path):
        print(f"  Using cached: {os.path.basename(dest_path)}")
        return True
    
    print(f"  Downloading: {url}")
    try:
        urllib.request.urlretrieve(url, dest_path)
        size_mb = os.path.getsize(dest_path) / 1024 / 1024
        print(f"  Downloaded: {os.path.basename(dest_path)} ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        print(f"  ERROR downloading: {e}")
        return False


def setup_embedded_python(version="3.14.3", arch="64bit", no_download=False):
    """Setup embedded Python."""
    
    arch_key = f"{arch}bit" if not arch.endswith("bit") else arch
    if arch_key not in ARCH_MAP:
        raise ValueError(f"Invalid architecture: {arch_key}")
    
    if version not in PYTHON_VERSIONS:
        raise ValueError(f"Unsupported Python version: {version}")
    
    print(f"\n{'='*60}")
    print(f"Setting up Embedded Python {version} ({arch_key})")
    print(f"{'='*60}\n")
    
    project_root = Path(__file__).parent
    dist_path = project_root / "dist" / "python"
    cache_path = project_root / ".python_cache"
    cache_path.mkdir(exist_ok=True)
    
    # Generate correct arch code for URLs and cache filenames
    if arch_key == "32bit":
        arch_code = "win32"
    else:  # 64bit
        arch_code = "amd64"
    
    embedded_url, full_url = get_download_urls(version, arch_key)
    embedded_file = cache_path / f"python-{version}-embed-{arch_code}.zip"
    full_file = cache_path / f"python-{version}-{arch_code}.zip"
    
    if not no_download:
        print("Step 1: Downloading embedded Python and full distribution...")
        if not download_file(embedded_url, str(embedded_file)):
            if not embedded_file.exists():
                raise RuntimeError(f"Could not download or find Python {version} embedded")
        if not download_file(full_url, str(full_file)):
            print(f"  Warning: Could not download full distribution (tkinter may not be available)")
    else:
        print("Step 1: Skipping downloads (--no-download)")
        if not embedded_file.exists():
            raise FileNotFoundError(f"Embedded Python cache not found: {embedded_file}")
    
    print("\nStep 2: Extracting embedded Python...")
    if dist_path.exists():
        shutil.rmtree(dist_path)
    dist_path.mkdir(parents=True, exist_ok=True)
    
    try:
        with zipfile.ZipFile(str(embedded_file), 'r') as zf:
            zf.extractall(str(dist_path))
        print(f"  Extracted to: {dist_path}")
    except Exception as e:
        print(f"  ERROR extracting: {e}")
        raise
    
    python_exe = dist_path / "python.exe"
    
    print("\nStep 3: Installing tkinter from full distribution...")
    if full_file.exists():
        try:
            temp_extract = cache_path / f"python-{version}-full"
            if temp_extract.exists():
                shutil.rmtree(temp_extract)
            temp_extract.mkdir(exist_ok=True)
            
            print(f"  Extracting tkinter components from full distribution...")
            
            with zipfile.ZipFile(str(full_file), 'r') as zf:
                # List of files/patterns to extract
                items_to_extract = []
                for item in zf.namelist():
                    item_lower = item.lower()
                    # Extract:
                    # - tcl directory (full folder with all runtime files)
                    # - All DLLs including _tkinter, tcl86t, tk86t and dependencies
                    # - tkinter Python module (Lib/tkinter)
                    if (item_lower.startswith('tcl/') or
                        item_lower.startswith('dlls/') or
                        item_lower.startswith('lib/tkinter/')):
                        items_to_extract.append(item)
                
                # Extract all items
                for item in items_to_extract:
                    try:
                        zf.extract(item, str(temp_extract))
                    except Exception as e:
                        pass  # Skip items that fail to extract
                
                # Copy tcl directory to embedded Python root
                src_tcl = temp_extract / 'tcl'
                if src_tcl.exists():
                    dst_tcl = dist_path / 'tcl'
                    if dst_tcl.exists():
                        shutil.rmtree(dst_tcl)
                    shutil.copytree(src_tcl, dst_tcl)
                    print(f"  ✓ Installed tcl library")
                
                # Copy ALL DLLs from DLLs folder
                src_dlls = temp_extract / 'DLLs'
                if src_dlls.exists():
                    for dll_file in src_dlls.glob('*.dll'):
                        dst = dist_path / dll_file.name
                        shutil.copy2(dll_file, dst)
                        if 'tcl' in dll_file.name.lower() or 'tk' in dll_file.name.lower() or '_tkinter' in dll_file.name:
                            print(f"  ✓ Installed {dll_file.name}")
                    
                    # Copy all .pyd files (including _tkinter.pyd)
                    for pyd_file in src_dlls.glob('*.pyd'):
                        dst = dist_path / pyd_file.name
                        shutil.copy2(pyd_file, dst)
                        if 'tkinter' in pyd_file.name.lower():
                            print(f"  ✓ Installed {pyd_file.name}")
                
                # Copy tkinter module (Lib/tkinter)
                src_tkinter = temp_extract / 'Lib' / 'tkinter'
                if src_tkinter.exists():
                    dst_tkinter = dist_path / 'tkinter'
                    if dst_tkinter.exists():
                        shutil.rmtree(dst_tkinter)
                    shutil.copytree(src_tkinter, dst_tkinter)
                    print(f"  ✓ Installed tkinter module")
                
        except zipfile.BadZipFile:
            print(f"  Warning: Full distribution file cannot be extracted (not a ZIP)")
            print(f"  tkinter will not be available")
        except Exception as e:
            print(f"  Warning: tkinter installation failed: {e}")
    else:
        print(f"  Warning: Full distribution not available, skipping tkinter installation")
    
    print("\nStep 4: Installing required packages...")
    req_file = project_root / "src" / "cydc" / "requirements.txt"
    
    if req_file.exists():
        print(f"  Installing packages from wheels (no pip required)...")
        installed, failed = install_packages_from_wheels(python_exe, dist_path, req_file)
        
        if installed:
            print(f"  ✓ Installed {len(installed)} package(s)")
            for pkg in installed:
                print(f"    - {pkg}")
        if failed:
            print(f"  ⚠ Failed to install {len(failed)} package(s)")
            for pkg in failed:
                print(f"    - {pkg}")
    else:
        print(f"  Note: {req_file} not found - skipping package installation")
    
    print("\nStep 5: Configuring sitecustomize.py (backup path configuration)...")
    try:
        # For embedded Python, we create sitecustomize.py which is automatically imported
        # This is more reliable than ._pth files for site-packages configuration
        sitecustomize_path = dist_path / "Lib" / "sitecustomize.py"
        site_packages_path = dist_path / "Lib" / "site-packages"
        src_cydc_path = project_root / "src" / "cydc"
        
        with open(sitecustomize_path, 'w') as f:
            f.write("# Automatically add site-packages and project paths\n")
            f.write("import sys\n")
            f.write(f"sys.path.insert(0, r'{site_packages_path}')\n")
            f.write(f"sys.path.insert(0, r'{src_cydc_path}')\n")
        
        print(f"  sitecustomize.py configured")
        print(f"    - Added site-packages path: {site_packages_path}")
        print(f"    - Added src/cydc path: {src_cydc_path}")
    except Exception as e:
        print(f"  Warning: sitecustomize configuration failed: {e}")
    
    print("\nStep 6: Verifying tkinter installation...")
    tkinter_ok = False
    
    # Check 1: Try importing tkinter directly
    try:
        result = subprocess.run([
            str(python_exe),
            "-c", "import tkinter"
        ], capture_output=True, timeout=10, text=True)
        
        if result.returncode == 0:
            tkinter_ok = True
            print(f"  ✓ tkinter module is operational")
        else:
            print(f"  ✗ tkinter import failed: {result.stderr[:60] if result.stderr else 'unknown error'}")
    except Exception as e:
        print(f"  Warning: tkinter verification failed: {e}")
    
    # Check 2: Verify _tkinter.pyd exists as backup
    if not tkinter_ok:
        if (dist_path / "_tkinter.pyd").exists() and (dist_path / "tcl86t.dll").exists():
            print(f"  ⚠ _tkinter.pyd and DLLs exist (tkinter may be operational)")
    
    # Clean up cached files from different versions/architectures
    print("\nStep 7: Cleaning up cache...")
    try:
        cleaned_count = 0
        # Keep: current version's embedded/full zips and get-pip.py for future use
        keep_files = {str(embedded_file), str(full_file), str(cache_path / "get-pip.py")}
        for cache_file in cache_path.glob("*"):
            if cache_file.is_file() and str(cache_file) not in keep_files:
                cache_file.unlink()
                cleaned_count += 1
                print(f"  Removed: {cache_file.name}")
            elif cache_file.is_dir() and cache_file.name.startswith("python-"):
                shutil.rmtree(cache_file)
                print(f"  Removed: {cache_file.name}/")
        if cleaned_count == 0:
            print(f"  Cache is clean")
    except Exception as e:
        print(f"  Warning: cache cleanup failed: {e}")
    
    # Step 8: Update ._pth file to include site-packages
    print("\nStep 8: Updating ._pth file...")
    try:
        # Get the major.minor version (e.g., 3.14 from 3.14.3)
        version_parts = version.split('.')
        python_ver_short = f"{version_parts[0]}{version_parts[1]}"  # e.g., 314
        pth_file = dist_path / f"python{python_ver_short}._pth"
        
        # Read existing content
        existing_content = []
        if pth_file.exists():
            with open(pth_file, 'r', encoding='utf-8') as f:
                existing_content = [line.strip() for line in f.readlines() if line.strip() and not line.strip().startswith('#')]
        
        # Ensure Lib/site-packages is in the path
        site_packages_rel = "Lib\\site-packages"
        if site_packages_rel not in existing_content:
            existing_content.insert(1, site_packages_rel)  # Insert after python314.zip and .
        
        # Write updated content
        with open(pth_file, 'w', encoding='utf-8') as f:
            for line in existing_content:
                f.write(line + '\n')
            f.write('\n# Uncomment to run site.main() automatically\n')
            f.write('#import site\n')
        
        print(f"  ._pth file updated: {pth_file.name}")
        print(f"    - Added Lib\\site-packages to path")
    except Exception as e:
        print(f"  Warning: ._pth update failed: {e}")
    
    print(f"\n{'='*60}")
    print(f"Setup complete!")
    print(f"Python: {python_exe}")
    print(f"{'='*60}\n")
    
    return dist_path


def main():
    parser = argparse.ArgumentParser(description="Setup embedded Python")
    
    parser.add_argument("--32bit", action="store_const", const="32bit", dest="arch", default="64bit",
        help="Setup 32-bit Python (default: 64-bit)")
    parser.add_argument("--python-version", default="3.14.3", help="Python version (default: 3.14.3)")
    parser.add_argument("--no-download", action="store_true", help="Use existing cache")
    parser.add_argument("--list-versions", action="store_true", help="List supported versions")
    parser.add_argument("--verify", action="store_true", help="Only verify installation")
    
    args = parser.parse_args()
    
    if args.list_versions:
        print("\nSupported Python versions:")
        for version in sorted(PYTHON_VERSIONS.keys(), reverse=True):
            print(f"  - {version}")
        print()
        return 0
    
    try:
        setup_embedded_python(version=args.python_version, arch=args.arch, no_download=args.no_download)
        return 0
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
