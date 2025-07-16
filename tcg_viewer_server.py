#!/usr/bin/env python3
"""
Pokemon TCG Captured Content Viewer Server
==========================================
Simple HTTP server to display what was captured from tcg.pokemon.com
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path
import threading
import time

def serve_tcg_viewer(port=8003):
    """Serve the TCG captured content viewer"""
    
    # Make sure we're in the right directory
    os.chdir(Path(__file__).parent)
    
    # Check if our viewer file exists
    if not Path("tcg_captured_viewer.html").exists():
        print("❌ Error: tcg_captured_viewer.html not found!")
        return False
    
    # Check if the screenshot exists
    screenshot_path = Path("tcg_animations_comprehensive/screenshots/tcg_galleries_initial.png")
    if not screenshot_path.exists():
        print("⚠️  Warning: Screenshot file not found at expected location")
        print(f"     Looking for: {screenshot_path}")
    
    # Create a custom handler to serve our content
    class TCGViewerHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            # Add CORS headers
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
        
        def do_GET(self):
            # Redirect root to our viewer
            if self.path == '/':
                self.path = '/tcg_captured_viewer.html'
            return super().do_GET()
    
    try:
        with socketserver.TCPServer(("", port), TCGViewerHandler) as httpd:
            server_url = f"http://localhost:{port}"
            
            print(f"\n🃏 Pokemon TCG Captured Content Viewer")
            print(f"=" * 50)
            print(f"📂 Serving from: {Path.cwd()}")
            print(f"🌐 Server running at: {server_url}")
            print(f"📱 Press Ctrl+C to stop the server")
            print(f"\n✨ Opening browser to show captured TCG content...")
            
            # Open browser after a short delay
            def open_browser():
                time.sleep(1)
                webbrowser.open(server_url)
            
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            print(f"\n🚀 Server ready! Displaying what was captured from:")
            print(f"   https://tcg.pokemon.com/en-us/all-galleries/")
            print(f"\n" + "=" * 50)
            
            # Serve forever
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n\n👋 Server stopped. Thanks for viewing the TCG captured content!")
        return True
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

if __name__ == "__main__":
    print("🎮 Starting Pokemon TCG Captured Content Viewer...")
    serve_tcg_viewer() 