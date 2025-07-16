#!/usr/bin/env python3
"""
Pokemon Sprite Viewer
Web-based interface to browse downloaded Pokemon sprites and data
"""

import http.server
import socketserver
import os
import json
import webbrowser
from pathlib import Path
import argparse
from urllib.parse import parse_qs, urlparse

class PokemonSpriteHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, sprite_dir=None, **kwargs):
        self.sprite_dir = Path(sprite_dir) if sprite_dir else Path("pokemon_sprites")
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_index()
        elif parsed_path.path == '/pokemon-data':
            self.serve_pokemon_list()
        elif parsed_path.path.startswith('/pokemon/'):
            pokemon_id = parsed_path.path.split('/')[-1]
            self.serve_pokemon_detail(pokemon_id)
        else:
            # Serve static files (sprites, etc.)
            self.serve_static_file(parsed_path.path)
    
    def serve_index(self):
        """Serve the main Pokemon sprite browser page"""
        html = self.generate_index_html()
        self.send_html_response(html)
    
    def serve_pokemon_list(self):
        """Serve JSON list of all available Pokemon"""
        pokemon_list = self.get_pokemon_list()
        self.send_json_response(pokemon_list)
    
    def serve_pokemon_detail(self, pokemon_id):
        """Serve detailed view of a specific Pokemon"""
        html = self.generate_pokemon_detail_html(pokemon_id)
        self.send_html_response(html)
    
    def serve_static_file(self, path):
        """Serve sprite images and other static files"""
        # Remove leading slash
        path = path.lstrip('/')
        file_path = self.sprite_dir / path
        
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
        """Send a file response"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Determine content type
            if str(file_path).endswith('.png'):
                content_type = 'image/png'
            elif str(file_path).endswith('.svg'):
                content_type = 'image/svg+xml'
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
    
    def get_pokemon_list(self):
        """Get list of all available Pokemon from data files"""
        pokemon_list = []
        data_dir = self.sprite_dir / "data" / "pokemon"
        
        if data_dir.exists():
            for json_file in sorted(data_dir.glob("*.json")):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        pokemon_data = json.load(f)
                    
                    pokemon_info = {
                        'id': pokemon_data['id'],
                        'name': pokemon_data['name'],
                        'height': pokemon_data['height'],
                        'weight': pokemon_data['weight'],
                        'types': [t['type']['name'] for t in pokemon_data['types']],
                        'sprites_available': self.check_available_sprites(pokemon_data['id'], pokemon_data['name'])
                    }
                    pokemon_list.append(pokemon_info)
                except Exception as e:
                    print(f"Error loading {json_file}: {e}")
        
        return pokemon_list
    
    def check_available_sprites(self, pokemon_id, pokemon_name):
        """Check which sprites are available for a Pokemon"""
        sprites = {}
        sprite_types = {
            'front_default': f'sprites/front_default/{pokemon_id:03d}_{pokemon_name}.png',
            'front_shiny': f'sprites/front_shiny/{pokemon_id:03d}_{pokemon_name}.png',
            'back_default': f'sprites/back_default/{pokemon_id:03d}_{pokemon_name}.png',
            'back_shiny': f'sprites/back_shiny/{pokemon_id:03d}_{pokemon_name}.png',
            'official_artwork': f'artwork/official/{pokemon_id:03d}_{pokemon_name}.png',
            'official_artwork_shiny': f'artwork/official/{pokemon_id:03d}_{pokemon_name}_shiny.png',
            'home': f'artwork/home/{pokemon_id:03d}_{pokemon_name}.png',
            'home_shiny': f'artwork/home/{pokemon_id:03d}_{pokemon_name}_shiny.png'
        }
        
        for sprite_name, sprite_path in sprite_types.items():
            full_path = self.sprite_dir / sprite_path
            sprites[sprite_name] = full_path.exists()
        
        return sprites
    
    def generate_index_html(self):
        """Generate the main Pokemon browser HTML"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pokemon Sprite Viewer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        
        .header h1 {
            text-align: center;
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .search-container {
            max-width: 600px;
            margin: 0 auto;
            position: relative;
        }
        
        .search-input {
            width: 100%;
            padding: 15px 20px;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            outline: none;
        }
        
        .filters {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        
        .filter-btn {
            padding: 8px 16px;
            border: none;
            border-radius: 20px;
            background: #ff6b6b;
            color: white;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .filter-btn:hover, .filter-btn.active {
            background: #ff5252;
            transform: translateY(-2px);
        }
        
        .pokemon-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            padding: 30px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .pokemon-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            cursor: pointer;
            backdrop-filter: blur(10px);
        }
        
        .pokemon-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
        }
        
        .pokemon-sprite {
            width: 120px;
            height: 120px;
            margin: 0 auto 15px;
            background: #f8f9fa;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        
        .pokemon-sprite img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }
        
        .pokemon-id {
            color: #666;
            font-size: 14px;
            margin-bottom: 5px;
        }
        
        .pokemon-name {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 10px;
            text-transform: capitalize;
            color: #333;
        }
        
        .pokemon-types {
            display: flex;
            justify-content: center;
            gap: 5px;
            margin-bottom: 10px;
        }
        
        .type-badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            color: white;
        }
        
        .type-normal { background: #A8A878; }
        .type-fire { background: #F08030; }
        .type-water { background: #6890F0; }
        .type-electric { background: #F8D030; }
        .type-grass { background: #78C850; }
        .type-ice { background: #98D8D8; }
        .type-fighting { background: #C03028; }
        .type-poison { background: #A040A0; }
        .type-ground { background: #E0C068; }
        .type-flying { background: #A890F0; }
        .type-psychic { background: #F85888; }
        .type-bug { background: #A8B820; }
        .type-rock { background: #B8A038; }
        .type-ghost { background: #705898; }
        .type-dragon { background: #7038F8; }
        .type-dark { background: #705848; }
        .type-steel { background: #B8B8D0; }
        .type-fairy { background: #EE99AC; }
        
        .loading {
            text-align: center;
            padding: 50px;
            color: white;
            font-size: 18px;
        }
        
        .no-results {
            text-align: center;
            padding: 50px;
            color: rgba(255,255,255,0.8);
            font-size: 18px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎮 Pokemon Sprite Viewer</h1>
        <div class="search-container">
            <input type="text" class="search-input" placeholder="Search Pokemon by name or number..." id="searchInput">
            <div class="filters">
                <button class="filter-btn active" data-type="all">All</button>
                <button class="filter-btn" data-type="fire">Fire</button>
                <button class="filter-btn" data-type="water">Water</button>
                <button class="filter-btn" data-type="grass">Grass</button>
                <button class="filter-btn" data-type="electric">Electric</button>
                <button class="filter-btn" data-type="psychic">Psychic</button>
            </div>
        </div>
    </div>
    
    <div class="pokemon-grid" id="pokemonGrid">
        <div class="loading">Loading Pokemon sprites...</div>
    </div>
    
    <script>
        let allPokemon = [];
        let filteredPokemon = [];
        
        // Load Pokemon data
        fetch('/pokemon-data')
            .then(response => response.json())
            .then(data => {
                allPokemon = data;
                filteredPokemon = data;
                renderPokemon();
            })
            .catch(error => {
                document.getElementById('pokemonGrid').innerHTML = 
                    '<div class="no-results">Error loading Pokemon data. Make sure you have downloaded Pokemon sprites first!</div>';
            });
        
        // Search functionality
        document.getElementById('searchInput').addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            filteredPokemon = allPokemon.filter(pokemon => 
                pokemon.name.toLowerCase().includes(query) || 
                pokemon.id.toString().includes(query)
            );
            renderPokemon();
        });
        
        // Type filter functionality
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                // Update active button
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                const type = btn.dataset.type;
                if (type === 'all') {
                    filteredPokemon = allPokemon;
                } else {
                    filteredPokemon = allPokemon.filter(pokemon => 
                        pokemon.types.includes(type)
                    );
                }
                renderPokemon();
            });
        });
        
        function renderPokemon() {
            const grid = document.getElementById('pokemonGrid');
            
            if (filteredPokemon.length === 0) {
                grid.innerHTML = '<div class="no-results">No Pokemon found matching your criteria.</div>';
                return;
            }
            
            grid.innerHTML = filteredPokemon.map(pokemon => {
                const spriteUrl = pokemon.sprites_available.official_artwork ? 
                    `artwork/official/${pokemon.id.toString().padStart(3, '0')}_${pokemon.name}.png` :
                    `sprites/front_default/${pokemon.id.toString().padStart(3, '0')}_${pokemon.name}.png`;
                
                return `
                    <div class="pokemon-card" onclick="openPokemonDetail(${pokemon.id})">
                        <div class="pokemon-sprite">
                            <img src="${spriteUrl}" alt="${pokemon.name}" onerror="this.src='sprites/front_default/${pokemon.id.toString().padStart(3, '0')}_${pokemon.name}.png'">
                        </div>
                        <div class="pokemon-id">#${pokemon.id.toString().padStart(3, '0')}</div>
                        <div class="pokemon-name">${pokemon.name}</div>
                        <div class="pokemon-types">
                            ${pokemon.types.map(type => `<span class="type-badge type-${type}">${type}</span>`).join('')}
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function openPokemonDetail(pokemonId) {
            window.open(`/pokemon/${pokemonId}`, '_blank');
        }
    </script>
</body>
</html>
        '''
    
    def generate_pokemon_detail_html(self, pokemon_id):
        """Generate detailed Pokemon view HTML"""
        return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pokemon #{pokemon_id} Details</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        }}
        
        .back-btn {{
            background: #ff6b6b;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 20px;
            cursor: pointer;
            margin-bottom: 20px;
            text-decoration: none;
            display: inline-block;
        }}
        
        .sprite-gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .sprite-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }}
        
        .sprite-card img {{
            max-width: 150px;
            max-height: 150px;
            margin-bottom: 10px;
        }}
        
        .sprite-title {{
            font-weight: bold;
            margin-bottom: 5px;
            text-transform: capitalize;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-btn">← Back to Pokemon List</a>
        
        <div id="pokemonDetail">
            <div style="text-align: center; padding: 50px;">
                Loading Pokemon details...
            </div>
        </div>
    </div>
    
    <script>
        const pokemonId = {pokemon_id};
        
        // Load Pokemon data from JSON file
        fetch(`/data/pokemon/${{pokemonId.toString().padStart(3, '0')}}_*.json`)
            .then(response => {{
                if (!response.ok) {{
                    throw new Error('Pokemon data not found');
                }}
                return response.json();
            }})
            .then(pokemon => {{
                renderPokemonDetail(pokemon);
            }})
            .catch(error => {{
                document.getElementById('pokemonDetail').innerHTML = 
                    '<div style="text-align: center; color: #ff6b6b;">Pokemon data not available. Make sure sprites are downloaded!</div>';
            }});
        
        function renderPokemonDetail(pokemon) {{
            const container = document.getElementById('pokemonDetail');
            
            // Create sprite gallery
            const sprites = [
                {{ name: 'Front Default', path: `sprites/front_default/${{pokemon.id.toString().padStart(3, '0')}}_${{pokemon.name}}.png` }},
                {{ name: 'Front Shiny', path: `sprites/front_shiny/${{pokemon.id.toString().padStart(3, '0')}}_${{pokemon.name}}.png` }},
                {{ name: 'Back Default', path: `sprites/back_default/${{pokemon.id.toString().padStart(3, '0')}}_${{pokemon.name}}.png` }},
                {{ name: 'Back Shiny', path: `sprites/back_shiny/${{pokemon.id.toString().padStart(3, '0')}}_${{pokemon.name}}.png` }},
                {{ name: 'Official Artwork', path: `artwork/official/${{pokemon.id.toString().padStart(3, '0')}}_${{pokemon.name}}.png` }},
                {{ name: 'Official Artwork Shiny', path: `artwork/official/${{pokemon.id.toString().padStart(3, '0')}}_${{pokemon.name}}_shiny.png` }},
                {{ name: 'Home', path: `artwork/home/${{pokemon.id.toString().padStart(3, '0')}}_${{pokemon.name}}.png` }},
                {{ name: 'Home Shiny', path: `artwork/home/${{pokemon.id.toString().padStart(3, '0')}}_${{pokemon.name}}_shiny.png` }}
            ];
            
            container.innerHTML = `
                <h1 style="text-align: center; margin-bottom: 20px;">
                    #${{pokemon.id.toString().padStart(3, '0')}} ${{pokemon.name.charAt(0).toUpperCase() + pokemon.name.slice(1)}}
                </h1>
                
                <div class="sprite-gallery">
                    ${{sprites.map(sprite => `
                        <div class="sprite-card">
                            <div class="sprite-title">${{sprite.name}}</div>
                            <img src="${{sprite.path}}" alt="${{sprite.name}}" 
                                 onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                            <div style="display: none; color: #999;">Not available</div>
                        </div>
                    `).join('')}}
                </div>
                
                <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 10px;">
                    <h3>Pokemon Information</h3>
                    <p><strong>Height:</strong> ${{pokemon.height / 10}} m</p>
                    <p><strong>Weight:</strong> ${{pokemon.weight / 10}} kg</p>
                    <p><strong>Types:</strong> ${{pokemon.types.map(t => t.type.name).join(', ')}}</p>
                    <p><strong>Abilities:</strong> ${{pokemon.abilities.map(a => a.ability.name).join(', ')}}</p>
                </div>
            `;
        }}
    </script>
</body>
</html>
        '''

def serve_pokemon_sprites(directory="pokemon_sprites", port=8001, open_browser=True):
    """Start the Pokemon sprite viewer server"""
    
    if not Path(directory).exists():
        print(f"❌ Error: Directory '{directory}' does not exist!")
        print("Please run the Pokemon sprite downloader first:")
        print("  python pokemon_sprite_downloader.py --gen1")
        return False
    
    # Create custom handler with sprite directory
    handler = lambda *args, **kwargs: PokemonSpriteHandler(*args, sprite_dir=directory, **kwargs)
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            server_url = f"http://localhost:{port}"
            print(f"\n🎮 Pokemon Sprite Viewer starting...")
            print(f"📂 Serving sprites from: {Path(directory).absolute()}")
            print(f"🌐 Server running at: {server_url}")
            print(f"📱 Press Ctrl+C to stop the server")
            
            if open_browser:
                print(f"🔗 Opening browser...")
                webbrowser.open(server_url)
            
            print(f"\n✅ Pokemon Sprite Viewer is ready!")
            print(f"   Visit: {server_url}")
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped by user")
        return True
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Error: Port {port} is already in use!")
            print(f"   Try a different port: python pokemon_sprite_viewer.py --port 8002")
        else:
            print(f"❌ Error starting server: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Pokemon Sprite Viewer")
    parser.add_argument("--directory", "-d", default="pokemon_sprites",
                       help="Directory containing Pokemon sprites (default: pokemon_sprites)")
    parser.add_argument("--port", "-p", type=int, default=8001,
                       help="Port to serve on (default: 8001)")
    parser.add_argument("--no-browser", action="store_true",
                       help="Don't automatically open browser")
    
    args = parser.parse_args()
    
    serve_pokemon_sprites(
        directory=args.directory,
        port=args.port,
        open_browser=not args.no_browser
    )

if __name__ == "__main__":
    main() 