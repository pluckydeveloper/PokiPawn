#!/usr/bin/env python3
"""
Pokemon TCG Integrator
======================
Integrates 19,155+ Pokemon TCG cards from the PokeMon Scrape project into ScrapeMore.
Downloads card images and organizes them by generation and era.

Generation Mapping:
- Gen 1 (1999-2000): Base Set, Jungle, Fossil (base1, base2, base3)
- Gen 2 (2000-2001): Neo Genesis, Neo Discovery (neo1-4)
- Gen 3 (2003-2007): EX Ruby & Sapphire, EX series (ex1-16, tk1a)
- Gen 4 (2007-2010): Diamond & Pearl, Platinum (dp1-7, pl1-4)
- Gen 5 (2011-2013): Black & White, Plasma (bw1-11)
- Gen 6 (2013-2016): XY, Generations (xy1-12, xy0, g1)
- Gen 7 (2017-2019): Sun & Moon series (sm1-12)
- Gen 8 (2020-2022): Sword & Shield, Pokémon GO (swsh1-12, pgo)
- Gen 9 (2022-2024): Scarlet & Violet series (sv1-10)
"""

import os
import json
import requests
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

class PokemonTCGIntegrator:
    def __init__(self, source_project="../PokeMon Scrape", target_project="."):
        self.source_path = Path(source_project)
        self.target_path = Path(target_project)
        self.tcg_data_path = self.source_path / "pokemon_tcg_data"
        self.output_path = self.target_path / "pokemon_tcg_cards"
        
        # Generation mapping based on TCG set codes
        self.generation_mapping = {
            # Generation 1 (1999-2000): Base Set era
            'gen1': {
                'era': '1999-2000',
                'sets': ['base1', 'base2', 'base3', 'base4', 'base5', 'base6', 'basep'],
                'description': 'Base Set, Jungle, Fossil, Team Rocket'
            },
            # Generation 2 (2000-2001): Neo era  
            'gen2': {
                'era': '2000-2001', 
                'sets': ['neo1', 'neo2', 'neo3', 'neo4'],
                'description': 'Neo Genesis, Neo Discovery, Neo Revelation, Neo Destiny'
            },
            # Generation 3 (2003-2007): EX era
            'gen3': {
                'era': '2003-2007',
                'sets': ['ex1', 'ex2', 'ex3', 'ex4', 'ex5', 'ex6', 'ex7', 'ex8', 'ex9', 'ex10', 'ex11', 'ex12', 'ex13', 'ex14', 'ex15', 'ex16', 'tk1a', 'tk2a'],
                'description': 'EX Ruby & Sapphire, EX FireRed & LeafGreen, EX Emerald'
            },
            # Generation 4 (2007-2010): Diamond & Pearl era
            'gen4': {
                'era': '2007-2010',
                'sets': ['dp1', 'dp2', 'dp3', 'dp4', 'dp5', 'dp6', 'dp7', 'pl1', 'pl2', 'pl3', 'pl4'],
                'description': 'Diamond & Pearl, Platinum, HeartGold & SoulSilver'
            },
            # Generation 5 (2011-2013): Black & White era
            'gen5': {
                'era': '2011-2013', 
                'sets': ['bw1', 'bw2', 'bw3', 'bw4', 'bw5', 'bw6', 'bw7', 'bw8', 'bw9', 'bw10', 'bw11'],
                'description': 'Black & White, Emerging Powers, Noble Victories, Plasma'
            },
            # Generation 6 (2013-2016): XY era
            'gen6': {
                'era': '2013-2016',
                'sets': ['xy0', 'xy1', 'xy2', 'xy3', 'xy4', 'xy5', 'xy6', 'xy7', 'xy8', 'xy9', 'xy10', 'xy11', 'xy12', 'xyp', 'g1'],
                'description': 'XY, Flashfire, Furious Fists, Phantom Forces, Generations'
            },
            # Generation 7 (2017-2019): Sun & Moon era
            'gen7': {
                'era': '2017-2019',
                'sets': ['sm1', 'sm2', 'sm3', 'sm4', 'sm5', 'sm6', 'sm7', 'sm8', 'sm9', 'sm10', 'sm11', 'sm12', 'smp'],
                'description': 'Sun & Moon, Guardians Rising, Burning Shadows, Ultra'
            },
            # Generation 8 (2020-2022): Sword & Shield era
            'gen8': {
                'era': '2020-2022',
                'sets': ['swsh1', 'swsh2', 'swsh3', 'swsh4', 'swsh5', 'swsh6', 'swsh7', 'swsh8', 'swsh9', 'swsh10', 'swsh11', 'swsh12', 'pgo'],
                'description': 'Sword & Shield, Rebel Clash, Darkness Ablaze, Pokémon GO'
            },
            # Generation 9 (2022-2024): Scarlet & Violet era
            'gen9': {
                'era': '2022-2024',
                'sets': ['sv1', 'sv2', 'sv3', 'sv4', 'sv5', 'sv6', 'sv7', 'sv8', 'sv9', 'sv10'],
                'description': 'Scarlet & Violet, Paldea Evolved, Obsidian Flames'
            }
        }
        
        self.downloaded_count = 0
        self.failed_downloads = []
        self.session = requests.Session()
        
        # Test mode attributes
        self.test_mode = False
        self.max_cards = None
        
    def create_directory_structure(self):
        """Create organized directory structure for TCG cards"""
        print("🏗️  Creating directory structure...")
        
        for gen, info in self.generation_mapping.items():
            gen_dir = self.output_path / gen
            gen_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            (gen_dir / "cards").mkdir(exist_ok=True)
            (gen_dir / "metadata").mkdir(exist_ok=True)
            (gen_dir / "sets").mkdir(exist_ok=True)
            
            # Create generation info file
            info_file = gen_dir / "generation_info.json"
            with open(info_file, 'w') as f:
                json.dump(info, f, indent=2)
                
        print(f"✅ Directory structure created at: {self.output_path}")
        
    def scan_available_cards(self):
        """Scan and categorize available TCG cards"""
        print("🔍 Scanning available Pokemon TCG cards...")
        
        card_files = list(self.tcg_data_path.glob("card_*.json"))
        print(f"Found {len(card_files)} card files")
        
        generation_stats = {}
        set_distribution = {}
        
        for card_file in card_files:
            try:
                # Extract set code from filename: card_base1-1_Alakazam.json -> base1
                filename = card_file.stem
                set_code = filename.split('_')[1].split('-')[0]
                
                # Determine generation
                generation = self.get_generation_for_set(set_code)
                
                if generation:
                    if generation not in generation_stats:
                        generation_stats[generation] = 0
                    generation_stats[generation] += 1
                    
                if set_code not in set_distribution:
                    set_distribution[set_code] = 0
                set_distribution[set_code] += 1
                    
            except Exception as e:
                print(f"Error processing {card_file}: {e}")
                continue
                
        print("\n📊 Generation Distribution:")
        for gen, count in sorted(generation_stats.items()):
            era = self.generation_mapping.get(gen, {}).get('era', 'Unknown')
            print(f"  {gen.upper()}: {count} cards ({era})")
            
        print(f"\n📦 Found {len(set_distribution)} unique sets")
        
        return generation_stats, set_distribution
        
    def get_generation_for_set(self, set_code):
        """Determine which generation a set belongs to"""
        for gen, info in self.generation_mapping.items():
            if set_code in info['sets']:
                return gen
        return None
        
    def download_card_image(self, card_data, target_path):
        """Download a single card image"""
        try:
            image_url = card_data.get('images', {}).get('large') or card_data.get('images', {}).get('small')
            if not image_url:
                return False
                
            response = self.session.get(image_url, timeout=30)
            response.raise_for_status()
            
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, 'wb') as f:
                f.write(response.content)
                
            return True
            
        except Exception as e:
            self.failed_downloads.append(f"{target_path}: {e}")
            return False
            
    def process_card_batch(self, card_files):
        """Process a batch of cards"""
        results = {'success': 0, 'failed': 0, 'skipped': 0}
        
        for card_file in card_files:
            try:
                # Load card data
                with open(card_file, 'r') as f:
                    card_data = json.load(f)
                    
                # Extract info
                set_code = card_data.get('set_info', {}).get('id', '')
                card_id = card_data.get('id', '')
                card_name = card_data.get('name', '').replace(' ', '_')
                
                # Determine generation
                generation = self.get_generation_for_set(set_code)
                if not generation:
                    results['skipped'] += 1
                    continue
                    
                # Create file paths
                card_filename = f"{card_id}_{card_name}.png"
                image_path = self.output_path / generation / "cards" / card_filename
                metadata_path = self.output_path / generation / "metadata" / f"{card_id}_{card_name}.json"
                
                # Skip if already exists
                if image_path.exists() and metadata_path.exists():
                    results['skipped'] += 1
                    continue
                    
                # Download image
                if self.download_card_image(card_data, image_path):
                    # Save metadata
                    with open(metadata_path, 'w') as f:
                        json.dump(card_data, f, indent=2)
                    results['success'] += 1
                    self.downloaded_count += 1
                else:
                    results['failed'] += 1
                    
            except Exception as e:
                print(f"Error processing {card_file}: {e}")
                results['failed'] += 1
                
        return results
        
    def download_all_cards(self, max_workers=5, batch_size=100):
        """Download all card images with progress tracking"""
        print("🎴 Starting Pokemon TCG card download...")
        
        card_files = list(self.tcg_data_path.glob("card_*.json"))
        
        # Apply test mode limit if enabled
        if self.test_mode and self.max_cards:
            card_files = card_files[:self.max_cards]
            print(f"🧪 Test mode: Processing {len(card_files)} of {len(list(self.tcg_data_path.glob('card_*.json')))} cards")
        
        total_cards = len(card_files)
        print(f"📦 Found {total_cards} cards to process")
        
        # Create batches
        batches = [card_files[i:i + batch_size] for i in range(0, len(card_files), batch_size)]
        
        total_results = {'success': 0, 'failed': 0, 'skipped': 0}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_batch = {executor.submit(self.process_card_batch, batch): i for i, batch in enumerate(batches)}
            
            for future in as_completed(future_to_batch):
                batch_num = future_to_batch[future]
                try:
                    results = future.result()
                    for key in total_results:
                        total_results[key] += results[key]
                        
                    progress = ((batch_num + 1) / len(batches)) * 100
                    print(f"📈 Progress: {progress:.1f}% | Downloaded: {total_results['success']} | Failed: {total_results['failed']} | Skipped: {total_results['skipped']}")
                    
                except Exception as e:
                    print(f"Batch {batch_num} failed: {e}")
                    
        print(f"\n✅ Download Complete!")
        print(f"📊 Final Stats:")
        print(f"  • Successfully downloaded: {total_results['success']} cards")
        print(f"  • Failed downloads: {total_results['failed']} cards") 
        print(f"  • Skipped (already exist): {total_results['skipped']} cards")
        
        return total_results
        
    def create_master_index(self):
        """Create master index of all cards organized by generation"""
        print("📋 Creating master card index...")
        
        master_index = {
            'total_cards': 0,
            'total_generations': len(self.generation_mapping),
            'generation_summary': {},
            'scan_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'generations': {}
        }
        
        for gen, info in self.generation_mapping.items():
            gen_dir = self.output_path / gen
            cards_dir = gen_dir / "cards"
            
            if not cards_dir.exists():
                continue
                
            # Count cards in this generation
            card_images = list(cards_dir.glob("*.png"))
            card_count = len(card_images)
            
            master_index['generations'][gen] = {
                'era': info['era'],
                'description': info['description'],
                'sets': info['sets'],
                'card_count': card_count,
                'cards': []
            }
            
            # Add individual card details
            for card_image in card_images[:50]:  # Limit to first 50 for performance
                card_id = card_image.stem
                metadata_file = gen_dir / "metadata" / f"{card_id}.json"
                
                card_entry = {
                    'id': card_id,
                    'image_path': str(card_image.relative_to(self.output_path)),
                    'metadata_path': str(metadata_file.relative_to(self.output_path)) if metadata_file.exists() else None
                }
                
                master_index['generations'][gen]['cards'].append(card_entry)
                
            master_index['total_cards'] += card_count
            master_index['generation_summary'][gen] = card_count
            
        # Save master index
        index_file = self.output_path / "master_card_index.json"
        with open(index_file, 'w') as f:
            json.dump(master_index, f, indent=2)
            
        print(f"✅ Master index created: {index_file}")
        print(f"📊 Total cards indexed: {master_index['total_cards']}")
        
        return master_index
        
    def run_full_integration(self):
        """Run the complete TCG integration process"""
        print("🚀 Starting Pokemon TCG Integration")
        print("=" * 50)
        
        # Step 1: Create directory structure
        self.create_directory_structure()
        
        # Step 2: Scan available cards
        gen_stats, set_stats = self.scan_available_cards()
        
        # Step 3: Download card images
        download_results = self.download_all_cards()
        
        # Step 4: Create master index
        master_index = self.create_master_index()
        
        print("\n🎉 Integration Complete!")
        print("=" * 50)
        print(f"📁 Cards organized in: {self.output_path}")
        print(f"🎴 Total cards available: {len(list(self.tcg_data_path.glob('card_*.json')))}")
        print(f"✅ Successfully downloaded: {download_results['success']}")
        print(f"🌟 Generations covered: {len(gen_stats)}")
        
        return master_index

if __name__ == "__main__":
    integrator = PokemonTCGIntegrator()
    master_index = integrator.run_full_integration() 