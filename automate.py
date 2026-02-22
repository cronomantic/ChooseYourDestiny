#!/usr/bin/env python3

"""
Master automation script for ChooseYourDestiny
Automates common development and release tasks.

This script provides a unified interface to:
- Update locale files (.po)
- Compile locales (.po → .mo)
- Run regression tests
- Generate PDF documentation
- Create distribution packages
- Update GitHub Wiki

MIT License - Copyright (c) 2024-2026 Sergio Chico
"""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None, shell=None):
    """
    Run a command and return success status.
    
    Args:
        cmd: Command to run (string or list)
        cwd: Working directory
        shell: Override shell usage (auto-detect if None)
    
    Returns:
        True if command succeeded, False otherwise
    """
    if shell is None:
        # Use shell for string commands, not for lists
        shell = isinstance(cmd, str)
    
    try:
        # For Windows, we need different handling
        if platform.system() == "Windows" and isinstance(cmd, str):
            # Use cmd.exe for batch files and built-in commands
            if cmd.endswith(".cmd") or cmd.endswith(".bat"):
                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=cwd,
                    check=True
                )
            else:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=cwd,
                    check=True
                )
        else:
            result = subprocess.run(
                cmd,
                shell=shell,
                cwd=cwd,
                check=True
            )
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Command failed with exit code {e.returncode}")
        return False
    except FileNotFoundError as e:
        print(f"\n✗ Command not found: {e}")
        return False


def update_locales(base_path):
    """Update .po locale files from source code."""
    print("\n" + "=" * 60)
    print("STEP 1: Updating Locale Files")
    print("=" * 60)
    
    script = base_path / "update_locales.py"
    if not script.exists():
        print(f"✗ Error: {script} not found")
        return False
    
    return run_command([sys.executable, str(script)], cwd=base_path)


def compile_locales(base_path):
    """Compile .po files to .mo files."""
    print("\n" + "=" * 60)
    print("STEP 1b: Compiling Locale Files (.po → .mo)")
    print("=" * 60)
    
    # The compilation is done automatically by make_dist.py
    # But we can trigger it separately
    script = base_path / "make_dist.py"
    if not script.exists():
        print(f"✗ Error: {script} not found")
        return False
    
    print("Compiling translations...")
    # Run make_dist with skip-compile to only do translations
    # Actually, we'll import it as a module
    try:
        sys.path.insert(0, str(base_path))
        import make_dist
        make_dist.compile_translations(base_path, "src/cydc")
        print("✓ Locale files compiled successfully")
        return True
    except Exception as e:
        print(f"✗ Error compiling locales: {e}")
        return False


def run_tests(base_path):
    """Run regression test suite."""
    print("\n" + "=" * 60)
    print("STEP 2: Running Regression Tests")
    print("=" * 60)
    
    script = base_path / "tests" / "run_tests.py"
    if not script.exists():
        print(f"✗ Error: {script} not found")
        return False
    
    return run_command([sys.executable, str(script)], cwd=base_path)


def generate_pdfs(base_path):
    """Generate PDF documentation."""
    print("\n" + "=" * 60)
    print("STEP 3: Generating PDF Documentation")
    print("=" * 60)
    
    system = platform.system()
    
    if system == "Windows":
        script = base_path / "make_pdf.bat"
        if not script.exists():
            print(f"✗ Error: {script} not found")
            return False
        return run_command(str(script), cwd=base_path)
    else:
        script = base_path / "make_pdf.sh"
        if not script.exists():
            print(f"✗ Error: {script} not found")
            return False
        # Make executable
        os.chmod(script, 0o755)
        return run_command(["bash", str(script)], cwd=base_path)


def create_distributions(base_path, platforms=None):
    """Create distribution packages."""
    print("\n" + "=" * 60)
    print("STEP 4: Creating Distribution Packages")
    print("=" * 60)
    
    script = base_path / "make_dist.py"
    if not script.exists():
        print(f"✗ Error: {script} not found")
        return False
    
    cmd = [sys.executable, str(script)]
    
    if platforms:
        if platforms == "all":
            cmd.append("--all")
        else:
            cmd.extend(["--platform", platforms])
    
    return run_command(cmd, cwd=base_path)


def update_wiki(base_path):
    """Update GitHub Wiki."""
    print("\n" + "=" * 60)
    print("STEP 5: Updating GitHub Wiki")
    print("=" * 60)
    
    script = base_path / "update_wiki.py"
    if not script.exists():
        print(f"✗ Error: {script} not found")
        return False
    
    return run_command([sys.executable, str(script)], cwd=base_path)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ChooseYourDestiny automation toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python automate.py --all                    Run all tasks
  python automate.py --locales --tests        Update locales and run tests
  python automate.py --dist --platform all    Create all distributions
  python automate.py --pdf --wiki             Generate PDFs and update wiki
  python automate.py --release                Full release workflow
        """
    )
    
    # Task selection
    parser.add_argument(
        "--locales",
        action="store_true",
        help="Update locale .po files from source code"
    )
    
    parser.add_argument(
        "--tests",
        action="store_true",
        help="Run regression test suite"
    )
    
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Generate PDF documentation"
    )
    
    parser.add_argument(
        "--dist",
        action="store_true",
        help="Create distribution packages"
    )
    
    parser.add_argument(
        "--wiki",
        action="store_true",
        help="Update GitHub Wiki"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tasks (except wiki update)"
    )
    
    parser.add_argument(
        "--release",
        action="store_true",
        help="Full release workflow (all tasks including wiki)"
    )
    
    # Distribution options
    parser.add_argument(
        "--platform",
        choices=["windows", "linux", "macos", "all"],
        help="Target platform for distribution"
    )
    
    args = parser.parse_args()
    
    # If no tasks specified, show help
    if not any([args.locales, args.tests, args.pdf, args.dist, args.wiki, args.all, args.release]):
        parser.print_help()
        return 0
    
    base_path = Path(__file__).parent.absolute()
    
    print("=" * 60)
    print("ChooseYourDestiny Automation Toolkit")
    print("=" * 60)
    print(f"Working directory: {base_path}")
    
    # Determine which tasks to run
    tasks = []
    
    if args.release:
        tasks = ["locales", "tests", "pdf", "dist", "wiki"]
    elif args.all:
        tasks = ["locales", "tests", "pdf", "dist"]
    else:
        if args.locales:
            tasks.append("locales")
        if args.tests:
            tasks.append("tests")
        if args.pdf:
            tasks.append("pdf")
        if args.dist:
            tasks.append("dist")
        if args.wiki:
            tasks.append("wiki")
    
    print(f"\nTasks to execute: {', '.join(tasks)}")
    
    # Execute tasks
    success = True
    
    if "locales" in tasks:
        if not update_locales(base_path):
            print("\n✗ Locale update failed")
            success = False
        else:
            # Compile locales after updating
            if not compile_locales(base_path):
                print("\n✗ Locale compilation failed")
                success = False
    
    if success and "tests" in tasks:
        if not run_tests(base_path):
            print("\n✗ Tests failed")
            success = False
    
    if success and "pdf" in tasks:
        if not generate_pdfs(base_path):
            print("\n✗ PDF generation failed")
            success = False
    
    if success and "dist" in tasks:
        platform_arg = args.platform if args.platform else None
        if not create_distributions(base_path, platform_arg):
            print("\n✗ Distribution creation failed")
            success = False
    
    if success and "wiki" in tasks:
        if not update_wiki(base_path):
            print("\n✗ Wiki update failed (you may need to commit changes)")
            # Don't set success = False, as this is non-critical
    
    # Final summary
    print("\n" + "=" * 60)
    if success:
        print("✓ All tasks completed successfully!")
    else:
        print("✗ Some tasks failed - see messages above")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
