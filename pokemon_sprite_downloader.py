#!/usr/bin/env python3
"""
Pokemon Sprite & Image Downloader
Downloads Pokemon sprites and artwork from the open-source PokeAPI
"""

import os
import requests
import json
from pathlib import Path
import time
from urllib.parse import urlparse
import argparse

class PokemonSpriteDownloader:
    def __init__(self, output_dir="pokemon_sprites"):
        self.base_url = "https://pokeapi.co/api/v2"
        self.output_dir = Path(output_dir)
        self.session = requests.Session()
        self.downloaded_count = 0
        self.failed_downloads = []
        
        # Create directory structure
        self.create_directories()
        
    def create_directories(self):
        """Create organized directory structure for Pokemon data"""
        directories = [
            "sprites/front_default",
            "sprites/front_shiny", 
            "sprites/back_default",
            "sprites/back_shiny",
            "sprites/front_female",
            "sprites/front_shiny_female",
            "sprites/back_female", 
            "sprites/back_shiny_female",
            "artwork/official",
            "artwork/dream_world",
            "artwork/home",
            "data/pokemon",
            "data/species"
        ]
        
        for directory in directories:
            (self.output_dir / directory).mkdir(parents=True, exist_ok=True)
    
    def download_image(self, url, filepath):
        """Download an image from URL to filepath"""
        if not url:
            return False
            
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            self.downloaded_count += 1
            return True
            
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            self.failed_downloads.append(url)
            return False
    
    def get_pokemon_data(self, pokemon_id):
        """Get Pokemon data from PokeAPI"""
        try:
            url = f"{self.base_url}/pokemon/{pokemon_id}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to get data for Pokemon {pokemon_id}: {e}")
            return None
    
    def get_pokemon_species_data(self, pokemon_id):
        """Get Pokemon species data from PokeAPI"""
        try:
            url = f"{self.base_url}/pokemon-species/{pokemon_id}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to get species data for Pokemon {pokemon_id}: {e}")
            return None
    
    def download_pokemon_sprites(self, pokemon_data):
        """Download all available sprites for a Pokemon"""
        pokemon_name = pokemon_data['name']
        pokemon_id = pokemon_data['id']
        sprites = pokemon_data.get('sprites', {})
        
        print(f"Downloading sprites for #{pokemon_id:03d} {pokemon_name.capitalize()}")
        
        # Basic sprites
        sprite_mapping = {
            'front_default': f"sprites/front_default/{pokemon_id:03d}_{pokemon_name}.png",
            'front_shiny': f"sprites/front_shiny/{pokemon_id:03d}_{pokemon_name}.png",
            'back_default': f"sprites/back_default/{pokemon_id:03d}_{pokemon_name}.png", 
            'back_shiny': f"sprites/back_shiny/{pokemon_id:03d}_{pokemon_name}.png",
            'front_female': f"sprites/front_female/{pokemon_id:03d}_{pokemon_name}.png",
            'front_shiny_female': f"sprites/front_shiny_female/{pokemon_id:03d}_{pokemon_name}.png",
            'back_female': f"sprites/back_female/{pokemon_id:03d}_{pokemon_name}.png",
            'back_shiny_female': f"sprites/back_shiny_female/{pokemon_id:03d}_{pokemon_name}.png"
        }
        
        # Download basic sprites
        for sprite_key, file_path in sprite_mapping.items():
            sprite_url = sprites.get(sprite_key)
            if sprite_url:
                self.download_image(sprite_url, self.output_dir / file_path)
        
        # Download official artwork
        other_sprites = sprites.get('other', {})
        
        # Official artwork
        official_artwork = other_sprites.get('official-artwork', {})
        if official_artwork.get('front_default'):
            filepath = self.output_dir / f"artwork/official/{pokemon_id:03d}_{pokemon_name}.png"
            self.download_image(official_artwork['front_default'], filepath)
        
        if official_artwork.get('front_shiny'):
            filepath = self.output_dir / f"artwork/official/{pokemon_id:03d}_{pokemon_name}_shiny.png"
            self.download_image(official_artwork['front_shiny'], filepath)
        
        # Dream World artwork
        dream_world = other_sprites.get('dream_world', {})
        if dream_world.get('front_default'):
            filepath = self.output_dir / f"artwork/dream_world/{pokemon_id:03d}_{pokemon_name}.svg"
            self.download_image(dream_world['front_default'], filepath)
        
        if dream_world.get('front_female'):
            filepath = self.output_dir / f"artwork/dream_world/{pokemon_id:03d}_{pokemon_name}_female.svg"
            self.download_image(dream_world['front_female'], filepath)
        
        # Home artwork
        home = other_sprites.get('home', {})
        if home.get('front_default'):
            filepath = self.output_dir / f"artwork/home/{pokemon_id:03d}_{pokemon_name}.png"
            self.download_image(home['front_default'], filepath)
        
        if home.get('front_shiny'):
            filepath = self.output_dir / f"artwork/home/{pokemon_id:03d}_{pokemon_name}_shiny.png"
            self.download_image(home['front_shiny'], filepath)
    
    def save_pokemon_data(self, pokemon_data, species_data=None):
        """Save Pokemon data as JSON files"""
        pokemon_name = pokemon_data['name']
        pokemon_id = pokemon_data['id']
        
        # Save main Pokemon data
        pokemon_file = self.output_dir / f"data/pokemon/{pokemon_id:03d}_{pokemon_name}.json"
        with open(pokemon_file, 'w', encoding='utf-8') as f:
            json.dump(pokemon_data, f, indent=2, ensure_ascii=False)
        
        # Save species data if available
        if species_data:
            species_file = self.output_dir / f"data/species/{pokemon_id:03d}_{pokemon_name}_species.json"
            with open(species_file, 'w', encoding='utf-8') as f:
                json.dump(species_data, f, indent=2, ensure_ascii=False)
    
    def download_pokemon_range(self, start_id=1, end_id=151, include_data=True):
        """Download Pokemon sprites for a range of IDs"""
        total_pokemon = end_id - start_id + 1
        
        print(f"🎮 Starting Pokemon sprite download")
        print(f"📊 Range: #{start_id:03d} to #{end_id:03d} ({total_pokemon} Pokemon)")
        print(f"📁 Output directory: {self.output_dir}")
        print("=" * 60)
        
        for pokemon_id in range(start_id, end_id + 1):
            try:
                # Get Pokemon data
                pokemon_data = self.get_pokemon_data(pokemon_id)
                if not pokemon_data:
                    continue
                
                # Download sprites
                self.download_pokemon_sprites(pokemon_data)
                
                # Get and save additional data if requested
                if include_data:
                    species_data = self.get_pokemon_species_data(pokemon_id)
                    self.save_pokemon_data(pokemon_data, species_data)
                
                # Progress update
                progress = ((pokemon_id - start_id + 1) / total_pokemon) * 100
                print(f"Progress: {progress:.1f}% ({pokemon_id - start_id + 1}/{total_pokemon})")
                
                # Rate limiting - be nice to the API
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print(f"\n⏹️  Download stopped by user at Pokemon #{pokemon_id}")
                break
            except Exception as e:
                print(f"❌ Error processing Pokemon #{pokemon_id}: {e}")
                continue
        
        self.print_summary()
    
    def download_specific_pokemon(self, pokemon_names_or_ids):
        """Download specific Pokemon by name or ID"""
        print(f"🎮 Downloading specific Pokemon: {pokemon_names_or_ids}")
        print(f"📁 Output directory: {self.output_dir}")
        print("=" * 60)
        
        for pokemon in pokemon_names_or_ids:
            try:
                pokemon_data = self.get_pokemon_data(pokemon)
                if not pokemon_data:
                    print(f"❌ Could not find Pokemon: {pokemon}")
                    continue
                
                self.download_pokemon_sprites(pokemon_data)
                species_data = self.get_pokemon_species_data(pokemon)
                self.save_pokemon_data(pokemon_data, species_data)
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Error processing Pokemon {pokemon}: {e}")
        
        self.print_summary()
    
    def print_summary(self):
        """Print download summary"""
        print("\n" + "=" * 60)
        print("📊 DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"✅ Total images downloaded: {self.downloaded_count}")
        print(f"❌ Failed downloads: {len(self.failed_downloads)}")
        print(f"📁 Files saved to: {self.output_dir}")
        
        if self.failed_downloads:
            print(f"\n⚠️  Failed URLs (first 10):")
            for url in self.failed_downloads[:10]:
                print(f"   {url}")
        
        print(f"\n🎉 Download complete!")

def main():
    parser = argparse.ArgumentParser(description="Download Pokemon sprites from PokeAPI")
    parser.add_argument("--output", "-o", default="pokemon_sprites",
                       help="Output directory (default: pokemon_sprites)")
    parser.add_argument("--start", "-s", type=int, default=1,
                       help="Start Pokemon ID (default: 1)")
    parser.add_argument("--end", "-e", type=int, default=151,
                       help="End Pokemon ID (default: 151 - Gen 1)")
    parser.add_argument("--pokemon", "-p", nargs="+",
                       help="Specific Pokemon names or IDs to download")
    parser.add_argument("--no-data", action="store_true",
                       help="Skip downloading JSON data files")
    
    # Generation shortcuts
    gen_group = parser.add_mutually_exclusive_group()
    gen_group.add_argument("--gen1", action="store_true",
                          help="Download Generation 1 (1-151)")
    gen_group.add_argument("--gen2", action="store_true", 
                          help="Download Generation 2 (152-251)")
    gen_group.add_argument("--gen3", action="store_true",
                          help="Download Generation 3 (252-386)")
    gen_group.add_argument("--gen4", action="store_true",
                          help="Download Generation 4 (387-493)")
    gen_group.add_argument("--gen5", action="store_true",
                          help="Download Generation 5 (494-649)")
    
    args = parser.parse_args()
    
    # Set generation ranges
    if args.gen1:
        args.start, args.end = 1, 151
    elif args.gen2:
        args.start, args.end = 152, 251
    elif args.gen3:
        args.start, args.end = 252, 386
    elif args.gen4:
        args.start, args.end = 387, 493
    elif args.gen5:
        args.start, args.end = 494, 649
    
    # Create downloader
    downloader = PokemonSpriteDownloader(args.output)
    
    # Download specific Pokemon or range
    if args.pokemon:
        downloader.download_specific_pokemon(args.pokemon)
    else:
        downloader.download_pokemon_range(
            start_id=args.start,
            end_id=args.end, 
            include_data=not args.no_data
        )

if __name__ == "__main__":
    main() 