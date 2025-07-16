#!/usr/bin/env python3
"""
Local HTTP Server for Scraped Pokemon Website
Serves the scraped website on localhost
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path
import argparse

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to avoid cross-origin issues
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def serve_website(directory="scraped_pokemon_site", port=8000, open_browser=True):
    """Serve the scraped website on a local HTTP server"""
    
    # Check if directory exists
    if not Path(directory).exists():
        print(f"Error: Directory '{directory}' does not exist!")
        print("Please run the scraper first: python scraper.py")
        return False
    
    # Change to the scraped website directory
    os.chdir(directory)
    
    # Create server
    handler = CustomHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            server_url = f"http://localhost:{port}"
            print(f"\n🚀 Server starting...")
            print(f"📂 Serving directory: {Path.cwd()}")
            print(f"🌐 Server running at: {server_url}")
            print(f"📱 Press Ctrl+C to stop the server")
            
            # Open browser automatically
            if open_browser:
                print(f"🔗 Opening browser...")
                webbrowser.open(server_url)
            
            print(f"\n✅ Server is ready! Your Pokemon website is now running locally.")
            print(f"   Visit: {server_url}")
            print(f"   Files: {Path.cwd()}")
            
            # Start serving
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped by user")
        return True
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Error: Port {port} is already in use!")
            print(f"   Try a different port: python local_server.py --port 8001")
        else:
            print(f"❌ Error starting server: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Serve scraped Pokemon website locally")
    parser.add_argument("--directory", "-d", default="scraped_pokemon_site",
                       help="Directory containing the scraped website (default: scraped_pokemon_site)")
    parser.add_argument("--port", "-p", type=int, default=8000,
                       help="Port to serve on (default: 8000)")
    parser.add_argument("--no-browser", action="store_true",
                       help="Don't automatically open browser")
    
    args = parser.parse_args()
    
    success = serve_website(
        directory=args.directory,
        port=args.port,
        open_browser=not args.no_browser
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 