#!/usr/bin/env python3
"""
Python Script Runner
A simple script runner that can execute any Python script with the required libraries.
"""

import sys
import os
import subprocess

def install_dependencies():
    """Install required Python packages."""
    required_packages = ['pandas', 'openpyxl', 'lxml']
    
    print("📦 Installing required packages...")
    for package in required_packages:
        try:
            print(f"Installing {package}...")
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e.stderr}")
            return False
    
    return True

def run_python_script(script_path):
    """Run a Python script and return its output."""
    try:
        if not os.path.exists(script_path):
            print(f"❌ Error: Script '{script_path}' not found.")
            return 1
        
        # Install dependencies first
        if not install_dependencies():
            print("❌ Failed to install required dependencies")
            return 1
        
        print(f"🐍 Executing Python script: {script_path}")
        
        # Execute the Python script
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, text=True)
        
        # Print stdout and stderr
        if result.stdout:
            print("📤 Output:")
            print(result.stdout)
        
        if result.stderr:
            print("⚠️  Errors:")
            print(result.stderr)
        
        return result.returncode
        
    except Exception as e:
        print(f"❌ Error running script: {e}")
        return 1

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python script_runner.py <script_path>")
        print("Example: python script_runner.py my_script.py")
        print("")
        print("Pre-installed libraries:")
        print("  - pandas: Data manipulation and analysis")
        print("  - openpyxl: Excel file reading and writing")
        print("  - lxml: XML and HTML processing")
        return 1
    
    script_path = sys.argv[1]
    return run_python_script(script_path)

if __name__ == "__main__":
    sys.exit(main()) 