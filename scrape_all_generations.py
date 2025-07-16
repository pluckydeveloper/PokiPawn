#!/usr/bin/env python3
"""
Simple Interface for Phygitals Pokemon Generation Scraper
Quick commands to scrape all Pokemon generations with focus on images and animations
"""

import subprocess
import sys
from pathlib import Path

def run_generation_scraper(command_args):
    """Run the generation scraper with given arguments"""
    try:
        cmd = [sys.executable, "phygitals_generation_scraper.py"] + command_args
        print(f"🚀 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running scraper: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Scraper file not found. Make sure phygitals_generation_scraper.py exists.")
        return False

def main():
    print("🎮 Phygitals Pokemon Generation Scraper")
    print("=" * 50)
    print("Select what to scrape:")
    print("")
    print("1. 🔥 Classic Generations (1-3) - Original, Johto, Hoenn")
    print("2. 🌟 Popular Generations (1, 4, 7) - Kanto, Sinnoh, Alola") 
    print("3. 🆕 Modern Generations (6-9) - Kalos, Alola, Galar, Paldea")
    print("4. 🎯 Specific Generation (choose number)")
    print("5. 🌍 ALL Generations (1-9) - Complete collection")
    print("6. 💨 Quick Demo (Gen 1 only)")
    print("")
    
    try:
        choice = input("Enter your choice (1-6): ").strip()
        
        if choice == "1":
            print("📥 Downloading Classic Generations (1-3)...")
            run_generation_scraper(["--classic"])
            
        elif choice == "2":
            print("📥 Downloading Popular Generations (1, 4, 7)...")
            run_generation_scraper(["-g", "1", "4", "7"])
            
        elif choice == "3":
            print("📥 Downloading Modern Generations (6-9)...")
            run_generation_scraper(["--modern"])
            
        elif choice == "4":
            gen_num = input("Which generation (1-9)? ").strip()
            if gen_num.isdigit() and 1 <= int(gen_num) <= 9:
                print(f"📥 Downloading Generation {gen_num}...")
                run_generation_scraper(["-g", gen_num])
            else:
                print("❌ Invalid generation number. Please enter 1-9.")
                
        elif choice == "5":
            confirm = input("⚠️  This will download ALL generations (large download). Continue? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                print("📥 Downloading ALL Generations (1-9)...")
                run_generation_scraper(["--all"])
            else:
                print("❌ Download cancelled.")
                
        elif choice == "6":
            print("📥 Quick Demo - Downloading Generation 1 only...")
            run_generation_scraper(["-g", "1"])
            
        else:
            print("❌ Invalid choice. Please enter 1-6.")
            
    except KeyboardInterrupt:
        print("\n⏹️  Cancelled by user.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 