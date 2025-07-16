#!/usr/bin/env python3
"""
Phygitals Pokemon Collection Viewer
Browse your scraped animated Pokemon sprites and data
"""

import http.server
import socketserver
import json
import webbrowser
from pathlib import Path
import argparse
import os

class PhygitalsPokemonHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, pokemon_dir=None, **kwargs):
        self.pokemon_dir = Path(pokemon_dir) if pokemon_dir else Path("phygitals_dynamic_pokemon")
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/':
            self.serve_main_page()
        elif self.path == '/pokemon-data':
            self.serve_pokemon_data()
        elif self.path.startswith('/generation/'):
            gen_num = self.path.split('/')[-1]
            self.serve_generation_page(gen_num)
        else:
            # Serve static files
            self.serve_static_file()
    
    def serve_main_page(self):
        """Serve the main Pokemon collection page"""
        html = self.generate_main_html()
        self.send_html_response(html)
    
    def serve_pokemon_data(self):
        """Serve JSON data for all generations"""
        all_pokemon = self.get_all_pokemon_data()
        self.send_json_response(all_pokemon)
    
    def serve_generation_page(self, gen_num):
        """Serve a specific generation page"""
        html = self.generate_generation_html(gen_num)
        self.send_html_response(html)
    
    def serve_static_file(self):
        """Serve Pokemon sprites and other static files"""
        file_path = self.pokemon_dir / self.path.lstrip('/')
        
        if file_path.exists() and file_path.is_file():
            self.send_file(file_path)
        else:
            self.send_error(404, "File not found")
    
    def send_html_response(self, html):
        """Send HTML response"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        json_data = json.dumps(data, ensure_ascii=False)
        self.wfile.write(json_data.encode('utf-8'))
    
    def send_file(self, file_path):
        """Send file response"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Determine content type
            if str(file_path).endswith('.gif'):
                content_type = 'image/gif'
            elif str(file_path).endswith('.png'):
                content_type = 'image/png'
            elif str(file_path).endswith('.json'):
                content_type = 'application/json'
            else:
                content_type = 'application/octet-stream'
            
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.send_header('Content-length', str(len(content)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error serving file: {e}")
    
    def get_all_pokemon_data(self):
        """Get Pokemon data from all generations"""
        all_pokemon = []
        
        for gen_dir in sorted(self.pokemon_dir.glob("generation_*")):
            if gen_dir.is_dir():
                gen_num = gen_dir.name.split('_')[1]
                
                # Get Pokemon sprites
                sprite_dir = gen_dir / "pokemon_sprites"
                if sprite_dir.exists():
                    for sprite_file in sorted(sprite_dir.glob("*.gif")):
                        try:
                            pokemon_num = int(sprite_file.stem)
                            pokemon_info = {
                                'id': pokemon_num,
                                'name': f"Pokemon #{pokemon_num:03d}",
                                'generation': int(gen_num),
                                'sprite_url': f"generation_{gen_num}/pokemon_sprites/{sprite_file.name}",
                                'type': 'animated_sprite'
                            }
                            all_pokemon.append(pokemon_info)
                        except ValueError:
                            continue
        
        return all_pokemon
    
    def get_generation_stats(self):
        """Get statistics for each generation"""
        stats = {}
        
        for gen_dir in sorted(self.pokemon_dir.glob("generation_*")):
            if gen_dir.is_dir():
                gen_num = gen_dir.name.split('_')[1]
                sprite_dir = gen_dir / "pokemon_sprites"
                
                pokemon_count = 0
                if sprite_dir.exists():
                    pokemon_count = len(list(sprite_dir.glob("*.gif")))
                
                stats[gen_num] = {
                    'pokemon_count': pokemon_count,
                    'has_data': (gen_dir / "data" / "pokemon_data.json").exists()
                }
        
        return stats
    
    def generate_main_html(self):
        """Generate the main collection page"""
        stats = self.get_generation_stats()
        
        return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phygitals Pokemon Collection</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            text-align: center;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            color: #333;
            font-size: 3em;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            color: #666;
            font-size: 1.2em;
            margin-bottom: 20px;
        }}
        
        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
        }}
        
        .stat-card {{
            background: #f8f9fa;
            padding: 15px 25px;
            border-radius: 10px;
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #ff6b6b;
        }}
        
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        
        .generation-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            padding: 40px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .generation-card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .generation-card:hover {{
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        }}
        
        .gen-number {{
            font-size: 3em;
            font-weight: bold;
            color: #ff6b6b;
            margin-bottom: 10px;
        }}
        
        .gen-title {{
            font-size: 1.5em;
            color: #333;
            margin-bottom: 15px;
        }}
        
        .pokemon-count {{
            font-size: 1.2em;
            color: #666;
            margin-bottom: 20px;
        }}
        
        .view-btn {{
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 1.1em;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .view-btn:hover {{
            background: linear-gradient(45deg, #764ba2, #667eea);
            transform: scale(1.05);
        }}
        
        .footer {{
            text-align: center;
            padding: 40px;
            color: rgba(255,255,255,0.8);
        }}
        
        .preview-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .pokemon-preview {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        
        .pokemon-preview:hover {{
            transform: scale(1.05);
        }}
        
        .pokemon-sprite {{
            width: 120px;
            height: 120px;
            margin: 0 auto 15px;
            background: #f8f9fa;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }}
        
        .pokemon-sprite img {{
            max-width: 100%;
            max-height: 100%;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎮 Phygitals Pokemon Collection</h1>
        <div class="subtitle">Your Complete Animated Pokemon Sprite Collection</div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{sum(s["pokemon_count"] for s in stats.values())}</div>
                <div class="stat-label">Total Pokemon</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(stats)}</div>
                <div class="stat-label">Generations</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">GIF</div>
                <div class="stat-label">Animated Sprites</div>
            </div>
        </div>
    </div>
    
    <div class="generation-grid">
        {self.generate_generation_cards(stats)}
    </div>
    
    <div class="footer">
        <p>🎉 All Pokemon sprites are animated GIFs from the official PokeAPI repository</p>
        <p>✨ Click on any generation to explore individual Pokemon</p>
    </div>
    
    <script>
        function viewGeneration(genNum) {{
            window.location.href = `/generation/${{genNum}}`;
        }}
        
        function viewAllPokemon() {{
            // Load and display all Pokemon in a grid
            fetch('/pokemon-data')
                .then(response => response.json())
                .then(pokemon => {{
                    displayAllPokemon(pokemon);
                }});
        }}
        
        function displayAllPokemon(pokemon) {{
            const container = document.querySelector('.generation-grid');
            container.innerHTML = '<h2 style="text-align: center; grid-column: 1/-1; color: white;">All Pokemon Collection</h2>';
            
            const previewGrid = document.createElement('div');
            previewGrid.className = 'preview-grid';
            
            pokemon.forEach(p => {{
                const card = document.createElement('div');
                card.className = 'pokemon-preview';
                card.innerHTML = `
                    <div class="pokemon-sprite">
                        <img src="${{p.sprite_url}}" alt="${{p.name}}" loading="lazy">
                    </div>
                    <div style="font-weight: bold;">${{p.name}}</div>
                    <div style="color: #666;">Generation ${{p.generation}}</div>
                `;
                previewGrid.appendChild(card);
            }});
            
            container.appendChild(previewGrid);
        }}
    </script>
</body>
</html>
        '''
    
    def generate_generation_cards(self, stats):
        """Generate HTML for generation cards"""
        generation_names = {
            '1': 'Kanto',
            '2': 'Johto', 
            '3': 'Hoenn',
            '4': 'Sinnoh',
            '5': 'Unova',
            '6': 'Kalos',
            '7': 'Alola',
            '8': 'Galar',
            '9': 'Paldea'
        }
        
        cards = []
        for gen_num, stat in stats.items():
            if stat['pokemon_count'] > 0:
                gen_name = generation_names.get(gen_num, f'Generation {gen_num}')
                cards.append(f'''
                <div class="generation-card" onclick="viewGeneration('{gen_num}')">
                    <div class="gen-number">Gen {gen_num}</div>
                    <div class="gen-title">{gen_name}</div>
                    <div class="pokemon-count">{stat['pokemon_count']} Pokemon</div>
                    <button class="view-btn">View Collection</button>
                </div>
                ''')
        
        return ''.join(cards)
    
    def generate_generation_html(self, gen_num):
        """Generate HTML for a specific generation"""
        return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generation {gen_num} Pokemon</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .back-btn {{
            position: absolute;
            left: 20px;
            top: 20px;
            background: #ff6b6b;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 20px;
            cursor: pointer;
            text-decoration: none;
        }}
        
        .pokemon-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 20px;
            padding: 30px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .pokemon-card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        
        .pokemon-card:hover {{
            transform: translateY(-5px);
        }}
        
        .pokemon-sprite {{
            width: 150px;
            height: 150px;
            margin: 0 auto 15px;
            background: #f8f9fa;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }}
        
        .pokemon-sprite img {{
            max-width: 100%;
            max-height: 100%;
        }}
        
        .pokemon-id {{
            color: #666;
            font-size: 14px;
            margin-bottom: 5px;
        }}
        
        .pokemon-name {{
            font-size: 18px;
            font-weight: bold;
            color: #333;
        }}
    </style>
</head>
<body>
    <div class="header">
        <a href="/" class="back-btn">← Back to Collection</a>
        <h1>Generation {gen_num} Pokemon</h1>
    </div>
    
    <div class="pokemon-grid" id="pokemonGrid">
        <div style="text-align: center; grid-column: 1/-1; color: white; padding: 50px;">
            Loading Pokemon...
        </div>
    </div>
    
    <script>
        const genNum = '{gen_num}';
        
        // Load Pokemon sprites for this generation
        fetch(`/generation_${{genNum}}/pokemon_sprites/`)
            .catch(() => {{
                // Fallback: load all data and filter
                return fetch('/pokemon-data')
                    .then(response => response.json())
                    .then(allPokemon => {{
                        return allPokemon.filter(p => p.generation == genNum);
                    }});
            }})
            .then(pokemon => {{
                if (Array.isArray(pokemon)) {{
                    renderPokemon(pokemon);
                }} else {{
                    // Load from directory listing
                    loadPokemonFromDirectory();
                }}
            }});
        
        function loadPokemonFromDirectory() {{
            // Create Pokemon cards based on available sprites
            const pokemonData = [];
            
            fetch('/pokemon-data')
                .then(response => response.json())
                .then(allPokemon => {{
                    const genPokemon = allPokemon.filter(p => p.generation == genNum);
                    renderPokemon(genPokemon);
                }});
        }}
        
        function renderPokemon(pokemon) {{
            const grid = document.getElementById('pokemonGrid');
            
            if (pokemon.length === 0) {{
                grid.innerHTML = '<div style="text-align: center; grid-column: 1/-1; color: white;">No Pokemon found for this generation.</div>';
                return;
            }}
            
            grid.innerHTML = pokemon.map(p => `
                <div class="pokemon-card">
                    <div class="pokemon-sprite">
                        <img src="/${{p.sprite_url}}" alt="${{p.name}}" loading="lazy">
                    </div>
                    <div class="pokemon-id">#${{p.id.toString().padStart(3, '0')}}</div>
                    <div class="pokemon-name">${{p.name}}</div>
                </div>
            `).join('');
        }}
    </script>
</body>
</html>
        '''

def serve_pokemon_collection(directory="phygitals_dynamic_pokemon", port=8002, open_browser=True):
    """Start the Phygitals Pokemon collection viewer"""
    
    if not Path(directory).exists():
        print(f"❌ Error: Directory '{directory}' does not exist!")
        print("Please run the Pokemon scraper first:")
        print("  python phygitals_browser_scraper.py --classic")
        return False
    
    # Create custom handler
    handler = lambda *args, **kwargs: PhygitalsPokemonHandler(*args, pokemon_dir=directory, **kwargs)
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            server_url = f"http://localhost:{port}"
            print(f"\n🎮 Phygitals Pokemon Collection Viewer starting...")
            print(f"📂 Serving from: {Path(directory).absolute()}")
            print(f"🌐 Server running at: {server_url}")
            print(f"📱 Press Ctrl+C to stop the server")
            
            if open_browser:
                print(f"🔗 Opening browser...")
                webbrowser.open(server_url)
            
            print(f"\n✅ Pokemon Collection Viewer is ready!")
            print(f"   Visit: {server_url}")
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped by user")
        return True
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Error: Port {port} is already in use!")
            print(f"   Try a different port: python phygitals_pokemon_viewer.py --port 8003")
        else:
            print(f"❌ Error starting server: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Phygitals Pokemon Collection Viewer")
    parser.add_argument("--directory", "-d", default="phygitals_dynamic_pokemon",
                       help="Directory containing Pokemon collection (default: phygitals_dynamic_pokemon)")
    parser.add_argument("--port", "-p", type=int, default=8002,
                       help="Port to serve on (default: 8002)")
    parser.add_argument("--no-browser", action="store_true",
                       help="Don't automatically open browser")
    
    args = parser.parse_args()
    
    serve_pokemon_collection(
        directory=args.directory,
        port=args.port,
        open_browser=not args.no_browser
    )

if __name__ == "__main__":
    main() 