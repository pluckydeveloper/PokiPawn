#!/usr/bin/env python3
"""
Quick Demo: Using Exported Pokemon Data
======================================
This demonstrates how easy it is to use your exported Pokemon data in a new project.
"""

import json
import os
from pathlib import Path
import random

def load_pokemon_data(metadata_file):
    """Load Pokemon data from exported metadata"""
    with open(metadata_file) as f:
        return json.load(f)

def get_pokemon_sprites(data):
    """Extract Pokemon sprite information"""
    sprites = []
    
    if 'phygitals_dynamic' in data['sources']:
        files = data['sources']['phygitals_dynamic']['files']
        for file in files:
            if 'pokemon_sprites' in file['path'] and file['extension'] == '.gif':
                # Extract Pokemon ID from filename
                pokemon_id = file['path'].split('/')[-1].replace('.gif', '')
                generation = file['path'].split('/')[0].replace('generation_', '')
                
                sprites.append({
                    'id': int(pokemon_id),
                    'name': f"Pokemon #{pokemon_id}",
                    'generation': int(generation),
                    'sprite_path': file['path'],
                    'file_size': file['size_bytes'],
                    'hash': file.get('md5_hash')
                })
    
    return sorted(sprites, key=lambda x: x['id'])

def demo_basic_usage():
    """Demonstrate basic usage of exported data"""
    print("🎮 Pokemon Data Export Demo")
    print("=" * 50)
    
    # Find the metadata file
    metadata_files = [f for f in os.listdir('.') if f.startswith('pokemon_data_export_') and f.endswith('.json')]
    
    if not metadata_files:
        print("❌ No exported metadata file found!")
        print("   Run: python pokemon_data_exporter.py --format json")
        return
    
    metadata_file = metadata_files[0]
    print(f"📋 Loading data from: {metadata_file}")
    
    # Load the data
    data = load_pokemon_data(metadata_file)
    
    # Display summary
    print(f"\n📊 Data Summary:")
    print(f"   Export Date: {data['scan_timestamp']}")
    print(f"   Total Sources: {len(data['sources'])}")
    
    for source_name, source_info in data['sources'].items():
        if source_info.get('exists'):
            print(f"   {source_name}: {source_info['total_files']} files ({source_info['total_size_mb']:.1f}MB)")
    
    # Get Pokemon sprites
    sprites = get_pokemon_sprites(data)
    print(f"\n🎯 Found {len(sprites)} Pokemon sprites!")
    
    # Show generation breakdown
    gen_counts = {}
    for sprite in sprites:
        gen = sprite['generation']
        gen_counts[gen] = gen_counts.get(gen, 0) + 1
    
    print(f"\n📈 Generation Breakdown:")
    for gen in sorted(gen_counts.keys()):
        print(f"   Generation {gen}: {gen_counts[gen]} Pokemon")
    
    # Show some random Pokemon
    print(f"\n🎲 Random Pokemon Sample:")
    sample_size = min(5, len(sprites))
    random_pokemon = random.sample(sprites, sample_size)
    
    for pokemon in random_pokemon:
        size_kb = pokemon['file_size'] / 1024
        print(f"   #{pokemon['id']:03d} (Gen {pokemon['generation']}) - {size_kb:.1f}KB")
        print(f"       Path: {pokemon['sprite_path']}")
    
    # Show file size statistics
    sizes = [s['file_size'] for s in sprites]
    avg_size = sum(sizes) / len(sizes) / 1024
    min_size = min(sizes) / 1024
    max_size = max(sizes) / 1024
    
    print(f"\n📏 File Size Stats:")
    print(f"   Average: {avg_size:.1f}KB")
    print(f"   Range: {min_size:.1f}KB - {max_size:.1f}KB")
    
    # Integration example
    print(f"\n💻 Integration Example:")
    print(f"   # Load Pokemon #25 (Pikachu)")
    pikachu = next((p for p in sprites if p['id'] == 25), None)
    if pikachu:
        print(f"   pokemon_025 = {{")
        print(f"       'id': {pikachu['id']},")
        print(f"       'generation': {pikachu['generation']},")
        print(f"       'sprite': './phygitals_dynamic/{pikachu['sprite_path']}',")
        print(f"       'size_kb': {pikachu['file_size'] / 1024:.1f}")
        print(f"   }}")
    
    print(f"\n🚀 Your data is ready for integration!")
    print(f"   ZIP Archive: Look for pokemon_data_archive_*.zip")
    print(f"   Metadata: {metadata_file}")
    print(f"   Integration Guide: POKEMON_DATA_INTEGRATION_GUIDE.md")

def demo_api_simulation():
    """Simulate how this data would work in an API"""
    metadata_files = [f for f in os.listdir('.') if f.startswith('pokemon_data_export_') and f.endswith('.json')]
    
    if not metadata_files:
        return
    
    data = load_pokemon_data(metadata_files[0])
    sprites = get_pokemon_sprites(data)
    
    print(f"\n🌐 API Simulation:")
    print("=" * 50)
    
    # Simulate API endpoints
    print("GET /api/pokemon")
    api_response = {
        "total": len(sprites),
        "generations": list(set(s['generation'] for s in sprites)),
        "pokemon": [
            {
                "id": s['id'],
                "generation": s['generation'],
                "sprite_url": f"/sprites/{s['sprite_path']}",
                "size_bytes": s['file_size']
            }
            for s in sprites[:3]  # Show first 3
        ]
    }
    print(json.dumps(api_response, indent=2))
    
    print(f"\nGET /api/pokemon/25")
    pikachu = next((s for s in sprites if s['id'] == 25), None)
    if pikachu:
        pikachu_response = {
            "id": pikachu['id'],
            "name": "Pikachu",
            "generation": pikachu['generation'],
            "sprite_url": f"/sprites/{pikachu['sprite_path']}",
            "file_size": pikachu['file_size'],
            "hash": pikachu['hash']
        }
        print(json.dumps(pikachu_response, indent=2))

if __name__ == "__main__":
    demo_basic_usage()
    demo_api_simulation()
    
    print(f"\n" + "=" * 50)
    print("🎉 Demo Complete!")
    print("Your Pokemon data is production-ready for any project!") 