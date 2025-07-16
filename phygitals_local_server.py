#!/usr/bin/env python3
"""
Phygitals Local Server
Serves the complete captured Phygitals Pokemon collection locally
"""

import http.server
import socketserver
import os
import json
import mimetypes
from urllib.parse import urlparse, parse_qs
import threading
import webbrowser
import time

class PhygitalsHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.getcwd(), **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()
    
    def do_GET(self):
        # Handle special routes
        path = urlparse(self.path).path
        
        if path == '/':
            # Serve our main Phygitals-style gallery page
            self.serve_file('phygitals_complete_local_site.html')
        elif path == '/api/pokemon':
            # API endpoint to get all Pokemon data
            self.serve_pokemon_api()
        elif path == '/api/generation':
            # API endpoint to get generation data
            self.serve_generation_api()
        elif path == '/api/stats':
            # API endpoint to get collection statistics
            self.serve_stats_api()
        else:
            # Default file serving
            super().do_GET()
    
    def serve_file(self, filename):
        try:
            with open(filename, 'rb') as f:
                content = f.read()
                
            # Determine content type
            content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.send_header('Content-length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            
        except FileNotFoundError:
            self.send_error(404)
    
    def serve_pokemon_api(self):
        """Serve consolidated Pokemon data from all generations"""
        try:
            all_pokemon = []
            stats = {
                'total_pokemon': 0,
                'total_generations': 0,
                'total_size_mb': 0,
                'by_generation': {}
            }
            
            # Load data from all generation files
            for gen in range(1, 10):
                gen_file = f'phygitals_FINAL_COMPLETE/generation_data/generation_{gen}.json'
                if os.path.exists(gen_file):
                    try:
                        with open(gen_file, 'r') as f:
                            gen_data = json.load(f)
                        
                        stats['total_generations'] += 1
                        gen_pokemon_count = 0
                        
                        if 'pokemon_assets' in gen_data:
                            for pokemon in gen_data['pokemon_assets']:
                                if pokemon.get('alt') and pokemon.get('alt') != f'Generation {gen} logo':
                                    pokemon_entry = {
                                        'name': pokemon['alt'],
                                        'id': self.extract_pokemon_id(pokemon.get('filename', '')),
                                        'generation': gen,
                                        'filename': pokemon.get('filename', ''),
                                        'image_path': f'phygitals_FINAL_COMPLETE/pokemon_animations/{pokemon.get("filename", "")}',
                                        'type': pokemon.get('type', 'animation')
                                    }
                                    all_pokemon.append(pokemon_entry)
                                    gen_pokemon_count += 1
                        
                        stats['by_generation'][gen] = {
                            'pokemon_count': gen_pokemon_count,
                            'assets_found': gen_data.get('assets_found', 0),
                            'assets_downloaded': gen_data.get('assets_downloaded', 0)
                        }
                        
                    except Exception as e:
                        print(f"Error loading generation {gen}: {e}")
            
            # Calculate directory sizes
            if os.path.exists('phygitals_FINAL_COMPLETE/pokemon_animations'):
                total_size = 0
                for filename in os.listdir('phygitals_FINAL_COMPLETE/pokemon_animations'):
                    if filename.endswith('.gif'):
                        filepath = os.path.join('phygitals_FINAL_COMPLETE/pokemon_animations', filename)
                        if os.path.isfile(filepath):
                            total_size += os.path.getsize(filepath)
                stats['total_size_mb'] = round(total_size / (1024 * 1024), 2)
            
            stats['total_pokemon'] = len(all_pokemon)
            
            # Sort Pokemon by ID
            all_pokemon.sort(key=lambda x: x['id'])
            
            response_data = {
                'pokemon': all_pokemon,
                'stats': stats,
                'success': True,
                'message': f'Loaded {len(all_pokemon)} Pokemon from {stats["total_generations"]} generations'
            }
            
            self.send_json_response(response_data)
            
        except Exception as e:
            self.send_json_response({
                'success': False,
                'error': str(e),
                'pokemon': [],
                'stats': {}
            })
    
    def serve_generation_api(self):
        """Serve specific generation data"""
        query = parse_qs(urlparse(self.path).query)
        gen_num = query.get('gen', ['1'])[0]
        
        try:
            gen_file = f'phygitals_FINAL_COMPLETE/generation_data/generation_{gen_num}.json'
            if os.path.exists(gen_file):
                with open(gen_file, 'r') as f:
                    gen_data = json.load(f)
                self.send_json_response(gen_data)
            else:
                self.send_json_response({
                    'error': f'Generation {gen_num} data not found',
                    'success': False
                })
        except Exception as e:
            self.send_json_response({
                'error': str(e),
                'success': False
            })
    
    def serve_stats_api(self):
        """Serve collection statistics"""
        try:
            stats = {
                'directories': [],
                'total_files': 0,
                'total_size_mb': 0,
                'generations_data': {},
                'capture_info': {}
            }
            
            # Check various directories
            directories_to_check = [
                'phygitals_FINAL_COMPLETE',
                'phygitals_dynamic_pokemon',
                'phygitals_with_images'
            ]
            
            for directory in directories_to_check:
                if os.path.exists(directory):
                    dir_stats = self.get_directory_stats(directory)
                    stats['directories'].append({
                        'name': directory,
                        'files': dir_stats['files'],
                        'size_mb': dir_stats['size_mb'],
                        'structure': dir_stats['structure']
                    })
                    stats['total_files'] += dir_stats['files']
                    stats['total_size_mb'] += dir_stats['size_mb']
            
            # Load generation data
            for gen in range(1, 10):
                gen_file = f'phygitals_FINAL_COMPLETE/generation_data/generation_{gen}.json'
                if os.path.exists(gen_file):
                    try:
                        with open(gen_file, 'r') as f:
                            gen_data = json.load(f)
                        stats['generations_data'][gen] = {
                            'assets_found': gen_data.get('assets_found', 0),
                            'assets_downloaded': gen_data.get('assets_downloaded', 0),
                            'pokemon_count': len([p for p in gen_data.get('pokemon_assets', []) 
                                                if p.get('alt') and 'logo' not in p.get('alt', '').lower()])
                        }
                    except:
                        pass
            
            # Capture metadata
            if os.path.exists('phygitals_FINAL_COMPLETE/metadata'):
                stats['capture_info'] = {
                    'capture_date': 'July 16, 2025',
                    'source': 'Phygitals.com',
                    'method': 'Comprehensive scraping with animation extraction',
                    'generations': list(range(1, 10))
                }
            
            self.send_json_response(stats)
            
        except Exception as e:
            self.send_json_response({
                'error': str(e),
                'success': False
            })
    
    def get_directory_stats(self, directory):
        """Get statistics for a directory"""
        total_files = 0
        total_size = 0
        structure = {}
        
        if not os.path.exists(directory):
            return {'files': 0, 'size_mb': 0, 'structure': {}}
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                if os.path.isfile(filepath):
                    total_files += 1
                    total_size += os.path.getsize(filepath)
                    
                    # Track file types
                    ext = os.path.splitext(file)[1].lower()
                    if ext not in structure:
                        structure[ext] = 0
                    structure[ext] += 1
        
        return {
            'files': total_files,
            'size_mb': round(total_size / (1024 * 1024), 2),
            'structure': structure
        }
    
    def extract_pokemon_id(self, filename):
        """Extract Pokemon ID from filename"""
        if not filename:
            return 0
        
        # Look for patterns like "gen_X_123.gif" or "123.gif"
        import re
        match = re.search(r'(\d+)\.gif$', filename)
        return int(match.group(1)) if match else 0
    
    def send_json_response(self, data):
        """Send JSON response"""
        json_data = json.dumps(data, indent=2).encode('utf-8')
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-length', str(len(json_data)))
        self.end_headers()
        self.wfile.write(json_data)
    
    def log_message(self, format, *args):
        """Custom logging"""
        print(f"[{time.strftime('%H:%M:%S')}] {format % args}")

def start_server(port=8005):
    """Start the Phygitals local server"""
    
    print("\n" + "="*60)
    print("🔥 PHYGITALS POKEMON LOCAL SERVER")
    print("="*60)
    
    # Check if required files exist
    if not os.path.exists('phygitals_local_gallery.html'):
        print("❌ Main gallery file not found!")
        return
    
    if not os.path.exists('phygitals_FINAL_COMPLETE'):
        print("❌ Pokemon data directory not found!")
        return
    
    # Count available Pokemon
    animation_dir = 'phygitals_FINAL_COMPLETE/pokemon_animations'
    pokemon_count = 0
    if os.path.exists(animation_dir):
        pokemon_count = len([f for f in os.listdir(animation_dir) if f.endswith('.gif')])
    
    print(f"📊 Found {pokemon_count} Pokemon animations")
    print(f"🌐 Starting server on port {port}...")
    
    try:
        with socketserver.TCPServer(("", port), PhygitalsHandler) as httpd:
            server_url = f"http://localhost:{port}"
            
            print(f"✅ Server running at: {server_url}")
            print(f"🎮 View Pokemon collection: {server_url}")
            print(f"📋 Raw data access: {server_url}/phygitals_FINAL_COMPLETE/")
            print(f"🔌 API endpoints available:")
            print(f"   • {server_url}/api/pokemon - All Pokemon data")
            print(f"   • {server_url}/api/generation?gen=1 - Generation data")
            print(f"   • {server_url}/api/stats - Collection statistics")
            print("\n💡 Press Ctrl+C to stop the server")
            print("="*60)
            
            # Auto-open browser after a short delay
            def open_browser():
                time.sleep(2)
                print(f"🌐 Opening browser to {server_url}...")
                webbrowser.open(server_url)
            
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            # Start serving
            httpd.serve_forever()
            
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use. Trying port {port + 1}...")
            start_server(port + 1)
        else:
            print(f"❌ Error starting server: {e}")
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        print("✅ Thanks for exploring the Phygitals Pokemon collection!")

if __name__ == "__main__":
    import sys
    
    # Get port from command line or use default
    port = 8005
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number, using default 8005")
    
    start_server(port) 