#!/usr/bin/env python3
"""
Pokemon Data Demo - How to use your scraped Pokemon data in other projects
"""

import json
import pandas as pd
from pathlib import Path

def load_pokemon_data():
    """Load the main Pokemon dataset"""
    try:
        # Load the comprehensive Pokemon data
        data_file = Path("pokemondb_comprehensive/data/complete_pokemon_list.json")
        if data_file.exists():
            with open(data_file, 'r') as f:
                return json.load(f)
        else:
            print("⚠️  Main data file not found. Make sure pokemondb_comprehensive/ exists.")
            return None
    except Exception as e:
        print(f"❌ Error loading Pokemon data: {e}")
        return None

def demo_basic_usage():
    """Demonstrate basic Pokemon data usage"""
    print("🎮 Pokemon Data Demo - Basic Usage")
    print("=" * 50)
    
    data = load_pokemon_data()
    if not data:
        return
    
    pokemon_list = data['pokemon']
    
    print(f"📊 Total Pokemon available: {len(pokemon_list)}")
    print(f"📅 Data scraped on: {data['scraped_at']}")
    print(f"🌐 Source: {data['source']}")
    print()
    
    # Show first 5 Pokemon
    print("🎯 First 5 Pokemon:")
    for pokemon in pokemon_list[:5]:
        print(f"  #{pokemon['number']:03d} {pokemon['name']}")
        print(f"       Types: {', '.join(pokemon['types'])}")
        print(f"       Stats: HP={pokemon['hp']} ATK={pokemon['attack']} DEF={pokemon['defense']}")
        print(f"       Sprite: {pokemon['sprite_url']}")
        print()

def demo_pokemon_search():
    """Demonstrate searching for specific Pokemon"""
    print("🔍 Pokemon Search Demo")
    print("=" * 50)
    
    data = load_pokemon_data()
    if not data:
        return
    
    pokemon_list = data['pokemon']
    
    # Search examples
    search_names = ['Pikachu', 'Charizard', 'Bulbasaur', 'Mew']
    
    for name in search_names:
        pokemon = next((p for p in pokemon_list if p['name'].lower() == name.lower()), None)
        if pokemon:
            print(f"✅ Found {pokemon['name']}:")
            print(f"   Number: #{pokemon['number']:03d}")
            print(f"   Types: {', '.join(pokemon['types'])}")
            print(f"   Total Stats: {pokemon['total']}")
            print(f"   Sprite URL: {pokemon['sprite_url']}")
        else:
            print(f"❌ {name} not found")
        print()

def demo_data_analysis():
    """Demonstrate data analysis capabilities"""
    print("📊 Pokemon Data Analysis Demo")
    print("=" * 50)
    
    data = load_pokemon_data()
    if not data:
        return
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(data['pokemon'])
    
    print(f"📈 Statistics:")
    print(f"   Average HP: {df['hp'].mean():.1f}")
    print(f"   Average Attack: {df['attack'].mean():.1f}")
    print(f"   Highest Total Stats: {df['total'].max()}")
    print()
    
    # Top 10 strongest Pokemon
    strongest = df.nlargest(10, 'total')[['name', 'total', 'types']]
    print("🏆 Top 10 Strongest Pokemon:")
    for idx, row in strongest.iterrows():
        types_str = ', '.join(row['types']) if isinstance(row['types'], list) else row['types']
        print(f"   {row['name']}: {row['total']} ({types_str})")
    print()
    
    # Type distribution
    all_types = []
    for pokemon in data['pokemon']:
        if isinstance(pokemon['types'], list):
            all_types.extend(pokemon['types'])
    
    type_counts = pd.Series(all_types).value_counts()
    print("🏷️  Most Common Types:")
    for type_name, count in type_counts.head(5).items():
        print(f"   {type_name}: {count} Pokemon")

def demo_api_simulation():
    """Simulate how you'd use this data in an API"""
    print("🌐 API Simulation Demo")
    print("=" * 50)
    
    data = load_pokemon_data()
    if not data:
        return
    
    pokemon_list = data['pokemon']
    
    def get_pokemon_by_id(pokemon_id):
        """Simulate API endpoint: GET /api/pokemon/:id"""
        return next((p for p in pokemon_list if p['number'] == pokemon_id), None)
    
    def get_pokemon_by_type(type_name):
        """Simulate API endpoint: GET /api/pokemon/type/:type"""
        return [p for p in pokemon_list if type_name.upper() in p['types']]
    
    # Demo API calls
    print("🔥 API Call: GET /api/pokemon/25 (Pikachu)")
    pikachu = get_pokemon_by_id(25)
    if pikachu:
        print(f"   Response: {pikachu['name']} - {', '.join(pikachu['types'])}")
    
    print("\n⚡ API Call: GET /api/pokemon/type/electric")
    electric_pokemon = get_pokemon_by_type('electric')
    print(f"   Found {len(electric_pokemon)} Electric-type Pokemon:")
    for p in electric_pokemon[:5]:  # Show first 5
        print(f"     - {p['name']}")

def demo_web_app_data():
    """Show how to structure data for web applications"""
    print("🌐 Web App Data Structure Demo")
    print("=" * 50)
    
    data = load_pokemon_data()
    if not data:
        return
    
    # Create simplified data structure for frontend
    web_app_data = {
        'pokemon': [],
        'types': set(),
        'generations': {}
    }
    
    for pokemon in data['pokemon'][:10]:  # Sample first 10
        # Simplified Pokemon object for frontend
        simple_pokemon = {
            'id': pokemon['number'],
            'name': pokemon['name'],
            'types': pokemon['types'],
            'sprite': pokemon['sprite_url'],
            'stats': {
                'hp': pokemon['hp'],
                'attack': pokemon['attack'],
                'defense': pokemon['defense'],
                'total': pokemon['total']
            }
        }
        web_app_data['pokemon'].append(simple_pokemon)
        
        # Collect unique types
        web_app_data['types'].update(pokemon['types'])
    
    web_app_data['types'] = sorted(list(web_app_data['types']))
    
    print("🎯 Sample Web App Data Structure:")
    print(f"   Pokemon count: {len(web_app_data['pokemon'])}")
    print(f"   Available types: {', '.join(web_app_data['types'])}")
    print("\n📱 Sample Pokemon for frontend:")
    print(json.dumps(web_app_data['pokemon'][0], indent=2))

def main():
    """Run all demos"""
    print("🎮 POKEMON DATA USAGE DEMONSTRATION")
    print("🎯 Showing how to use your scraped Pokemon data in other projects")
    print("=" * 70)
    print()
    
    demo_basic_usage()
    print()
    
    demo_pokemon_search()
    print()
    
    try:
        demo_data_analysis()
    except ImportError:
        print("📊 Data Analysis Demo skipped (pandas not installed)")
        print("   Install with: pip install pandas")
    print()
    
    demo_api_simulation()
    print()
    
    demo_web_app_data()
    print()
    
    print("✅ Demo completed! Your Pokemon data is ready to use in any project.")
    print("\n🚀 Next steps:")
    print("   1. Copy the data directories to your new project")
    print("   2. Install any required dependencies (pandas, requests, etc.)")
    print("   3. Use the examples above as starting points")
    print("   4. Check QUICK_PROJECT_SETUP.md for more integration examples")

if __name__ == "__main__":
    main() 