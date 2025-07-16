#!/usr/bin/env python3
"""
Phygitals Pokemon Collection Launcher
Quick setup and launch script for viewing the complete captured Pokemon collection
"""

import os
import sys
import subprocess
import time

def print_banner():
    print("\n" + "="*70)
    print("🔥 PHYGITALS POKEMON COLLECTION VIEWER")
    print("="*70)
    print("🎮 Welcome to your complete offline Pokemon collection!")
    print("✨ View 960+ animated Pokemon sprites from all 9 generations")
    print("🌟 Captured from Phygitals.com - fully offline ready!")
    print("="*70)

def check_requirements():
    """Check if all required files and directories exist"""
    print("\n🔍 Checking collection integrity...")
    
    requirements = [
        {
            'path': 'phygitals_local_gallery.html',
            'type': 'file',
            'description': 'Main gallery interface'
        },
        {
            'path': 'phygitals_local_server.py',
            'type': 'file', 
            'description': 'Local web server'
        },
        {
            'path': 'phygitals_FINAL_COMPLETE',
            'type': 'directory',
            'description': 'Pokemon data directory'
        },
        {
            'path': 'phygitals_FINAL_COMPLETE/pokemon_animations',
            'type': 'directory',
            'description': 'Pokemon animations directory'
        },
        {
            'path': 'phygitals_FINAL_COMPLETE/generation_data',
            'type': 'directory',
            'description': 'Generation data directory'
        }
    ]
    
    all_good = True
    
    for req in requirements:
        if req['type'] == 'file':
            exists = os.path.isfile(req['path'])
        else:
            exists = os.path.isdir(req['path'])
        
        status = "✅" if exists else "❌"
        print(f"  {status} {req['description']}: {req['path']}")
        
        if not exists:
            all_good = False
    
    return all_good

def count_pokemon():
    """Count available Pokemon animations"""
    animation_dir = 'phygitals_FINAL_COMPLETE/pokemon_animations'
    if not os.path.exists(animation_dir):
        return 0
    
    return len([f for f in os.listdir(animation_dir) if f.endswith('.gif')])

def show_collection_stats():
    """Display collection statistics"""
    print("\n📊 COLLECTION STATISTICS")
    print("-" * 40)
    
    pokemon_count = count_pokemon()
    print(f"🎯 Pokemon Animations: {pokemon_count}")
    
    # Check generation data
    gen_data_dir = 'phygitals_FINAL_COMPLETE/generation_data'
    generations = 0
    if os.path.exists(gen_data_dir):
        generations = len([f for f in os.listdir(gen_data_dir) if f.endswith('.json')])
    
    print(f"🌟 Generations Available: {generations}")
    
    # Calculate total size
    total_size = 0
    if os.path.exists('phygitals_FINAL_COMPLETE/pokemon_animations'):
        for filename in os.listdir('phygitals_FINAL_COMPLETE/pokemon_animations'):
            if filename.endswith('.gif'):
                filepath = os.path.join('phygitals_FINAL_COMPLETE/pokemon_animations', filename)
                if os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)
    
    size_mb = round(total_size / (1024 * 1024), 2)
    print(f"💾 Total Size: {size_mb} MB")
    print(f"🔌 Source: Phygitals.com")
    print(f"📱 Status: Fully Offline Ready")

def launch_server():
    """Launch the Phygitals local server"""
    print("\n🚀 LAUNCHING LOCAL SERVER")
    print("-" * 40)
    
    try:
        # Start the server
        print("🌐 Starting Phygitals local server...")
        subprocess.run([sys.executable, 'phygitals_local_server.py'], check=True)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
    except FileNotFoundError:
        print("❌ Python not found. Please ensure Python is installed.")

def show_quick_start():
    """Show quick start instructions"""
    print("\n🚀 QUICK START OPTIONS")
    print("-" * 40)
    print("1. 🌐 Launch Local Web Viewer (Recommended)")
    print("   → Full interactive gallery with search and filters")
    print("   → Animated Pokemon sprites with generation navigation")
    print("   → Runs on http://localhost:8005")
    print("")
    print("2. 📁 Browse Raw Files")
    print("   → Direct access to Pokemon animations")
    print("   → Located in: phygitals_FINAL_COMPLETE/pokemon_animations/")
    print("")
    print("3. 📋 View Generation Data")
    print("   → JSON files with Pokemon metadata")
    print("   → Located in: phygitals_FINAL_COMPLETE/generation_data/")

def main():
    print_banner()
    
    # Check requirements
    if not check_requirements():
        print("\n❌ SETUP INCOMPLETE")
        print("Some required files are missing. Please ensure you have:")
        print("1. Run the Phygitals scraper successfully")
        print("2. All files are in the correct location")
        print("3. The Pokemon animations have been downloaded")
        return
    
    # Show stats
    show_collection_stats()
    show_quick_start()
    
    # Ask user what they want to do
    print("\n" + "="*70)
    print("💡 What would you like to do?")
    print("="*70)
    print("🌐 [1] Launch Interactive Web Viewer (Default)")
    print("📁 [2] Open Pokemon Animations Folder")
    print("📋 [3] Show Collection Details")
    print("❌ [4] Exit")
    
    try:
        choice = input("\n🎯 Enter your choice (1-4, default=1): ").strip()
        
        if choice == "" or choice == "1":
            print("\n🚀 Launching interactive web viewer...")
            launch_server()
            
        elif choice == "2":
            animation_dir = 'phygitals_FINAL_COMPLETE/pokemon_animations'
            if os.path.exists(animation_dir):
                print(f"\n📁 Opening: {os.path.abspath(animation_dir)}")
                if sys.platform == "darwin":  # macOS
                    subprocess.run(["open", animation_dir])
                elif sys.platform == "win32":  # Windows
                    subprocess.run(["explorer", animation_dir])
                else:  # Linux
                    subprocess.run(["xdg-open", animation_dir])
            else:
                print("❌ Pokemon animations directory not found!")
                
        elif choice == "3":
            print("\n📋 DETAILED COLLECTION INFO")
            print("="*50)
            
            # List all directories
            directories = ['phygitals_FINAL_COMPLETE', 'phygitals_dynamic_pokemon', 
                          'phygitals_with_images', 'phygitals_targeted_complete']
            
            for directory in directories:
                if os.path.exists(directory):
                    file_count = sum([len(files) for r, d, files in os.walk(directory)])
                    print(f"📂 {directory}: {file_count} files")
            
            print(f"\n🎮 Main viewer: phygitals_local_gallery.html")
            print(f"🌐 Server script: phygitals_local_server.py")
            print(f"🔥 Original data: phygitals_FINAL_COMPLETE/index.html")
            
        elif choice == "4":
            print("\n👋 Thanks for exploring the Phygitals Pokemon collection!")
            return
            
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main() 