#!/usr/bin/env python3
"""
Setup and Run Script for Pokemon Website Scraper
Installs dependencies, scrapes the website, and starts local server
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is sufficient"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"❌ Python 3.7+ required. Current version: {version.major}.{version.minor}")
        return False
    print(f"✅ Python version {version.major}.{version.minor} is compatible")
    return True

def install_dependencies():
    """Install required Python packages"""
    print(f"\n📦 Installing dependencies...")
    return run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing packages")

def scrape_website():
    """Run the website scraper"""
    print(f"\n🕷️  Starting website scraper...")
    return run_command(f"{sys.executable} scraper.py", "Scraping Pokemon website")

def start_server():
    """Start the local server"""
    print(f"\n🚀 Starting local server...")
    print(f"   The server will open in your browser automatically")
    print(f"   Press Ctrl+C to stop the server when done")
    
    try:
        subprocess.run([sys.executable, "local_server.py"], check=True)
        return True
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped by user")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        return False

def main():
    print("🎮 Pokemon Website Scraper Setup & Run")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print(f"\n❌ Failed to install dependencies. Please check the error above.")
        sys.exit(1)
    
    # Scrape the website
    if not scrape_website():
        print(f"\n❌ Failed to scrape website. Please check the error above.")
        print(f"   You can try running manually: python scraper.py")
        sys.exit(1)
    
    # Check if scraping was successful
    if not Path("scraped_pokemon_site/index.html").exists():
        print(f"\n❌ Scraping seems to have failed - no index.html found")
        print(f"   Try running manually: python scraper.py")
        sys.exit(1)
    
    print(f"\n🎉 Scraping completed successfully!")
    print(f"   Website saved to: scraped_pokemon_site/")
    
    # Ask user if they want to start the server
    try:
        response = input(f"\n🤔 Would you like to start the local server now? (y/n): ").lower().strip()
        if response in ['y', 'yes', '']:
            start_server()
        else:
            print(f"\n📝 To start the server later, run: python local_server.py")
            print(f"   Your scraped website is in: scraped_pokemon_site/")
    except KeyboardInterrupt:
        print(f"\n\n📝 To start the server later, run: python local_server.py")
        print(f"   Your scraped website is in: scraped_pokemon_site/")

if __name__ == "__main__":
    main() 