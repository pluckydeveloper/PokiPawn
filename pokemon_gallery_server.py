#!/usr/bin/env python3
"""
Pokemon Master Gallery Server
=============================
Complete gallery of ALL captured Pokemon - 386 animated + 1025 static sprites + data
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path
import threading
import time

def serve_pokemon_gallery(port=8004):
    """Serve the complete Pokemon master gallery"""
    
    # Make sure we're in the right directory
    os.chdir(Path(__file__).parent)
    
    # Check if our gallery file exists
    if not Path("pokemon_master_gallery.html").exists():
        print("❌ Error: pokemon_master_gallery.html not found!")
        return False
    
    # Check if Pokemon directories exist
    animated_dir = Path("phygitals_dynamic_pokemon")
    static_dir = Path("pokemondb_comprehensive")
    
    if not animated_dir.exists():
        print("⚠️  Warning: Animated Pokemon directory not found")
    else:
        print(f"✅ Found animated Pokemon directory: {animated_dir}")
    
    if not static_dir.exists():
        print("⚠️  Warning: Static Pokemon directory not found")
    else:
        print(f"✅ Found static Pokemon directory: {static_dir}")
    
    # Create a custom handler to serve our Pokemon content
    class PokemonGalleryHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            # Add CORS headers
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
        
        def do_GET(self):
            # Redirect root to our gallery
            if self.path == '/':
                self.path = '/pokemon_master_gallery.html'
            return super().do_GET()
    
    try:
        with socketserver.TCPServer(("", port), PokemonGalleryHandler) as httpd:
            server_url = f"http://localhost:{port}"
            
            print(f"\n🎮 Pokemon Master Collection Gallery")
            print(f"=" * 60)
            print(f"📂 Serving from: {Path.cwd()}")
            print(f"🌐 Server running at: {server_url}")
            print(f"📱 Press Ctrl+C to stop the server")
            print(f"\n✨ Opening browser to show ALL captured Pokemon...")
            
            # Display what will be shown
            print(f"\n🎯 POKEMON COLLECTION OVERVIEW:")
            print(f"   • 386 Animated Pokemon Sprites (GIF)")
            print(f"   • 1,025 Static Pokemon Sprites (PNG)")
            print(f"   • Complete Pokemon data with stats")
            print(f"   • Generations 1, 2, and 3 coverage")
            print(f"   • 22MB+ of Pokemon visual content")
            
            # Open browser after a short delay
            def open_browser():
                time.sleep(1)
                webbrowser.open(server_url)
            
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            print(f"\n🚀 Gallery ready! Displaying your complete Pokemon collection...")
            print(f"   View all animated sprites, static sprites, and Pokemon data!")
            print(f"\n" + "=" * 60)
            
            # Serve forever
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n\n👋 Server stopped. Thanks for viewing your Pokemon collection!")
        return True
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

if __name__ == "__main__":
    print("🎮 Starting Pokemon Master Collection Gallery...")
    serve_pokemon_gallery() 