#!/usr/bin/env python3
"""
Pokemon Data Exporter
====================
Export your scraped Pokemon data in various formats for use in other projects.

Supports multiple export formats:
- JSON metadata with file references
- ZIP archives with organized data
- Directory copies with clean structure
- Database exports
- API-ready JSON format
"""

import os
import json
import shutil
import zipfile
import sqlite3
from pathlib import Path
from datetime import datetime
import argparse
from typing import Dict, List, Optional
import hashlib

class PokemonDataExporter:
    def __init__(self, workspace_path: str = "."):
        self.workspace_path = Path(workspace_path)
        self.export_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Source directories
        self.sources = {
            'phygitals_dynamic': self.workspace_path / 'phygitals_dynamic_pokemon',
            'phygitals_complete': self.workspace_path / 'phygitals_pokemon_complete', 
            'pokeapi_sprites': self.workspace_path / 'pokemon_sprites',
            'scraped_site': self.workspace_path / 'scraped_pokemon_site'
        }
        
        print("🎮 Pokemon Data Exporter Initialized")
        print(f"📂 Workspace: {self.workspace_path.absolute()}")
        
    def scan_data_sources(self) -> Dict:
        """Scan all data sources and generate inventory"""
        inventory = {
            'scan_timestamp': datetime.now().isoformat(),
            'workspace_path': str(self.workspace_path.absolute()),
            'sources': {}
        }
        
        for source_name, source_path in self.sources.items():
            print(f"🔍 Scanning {source_name}...")
            if source_path.exists():
                source_info = self._scan_directory(source_path)
                inventory['sources'][source_name] = source_info
                print(f"   ✅ Found {source_info['total_files']} files, {source_info['total_size_mb']:.1f}MB")
            else:
                print(f"   ⚠️  Not found: {source_path}")
                inventory['sources'][source_name] = {'exists': False}
        
        return inventory
    
    def _scan_directory(self, directory: Path) -> Dict:
        """Recursively scan directory and collect metadata"""
        total_files = 0
        total_size = 0
        file_types = {}
        
        for item in directory.rglob('*'):
            if item.is_file():
                total_files += 1
                size = item.stat().st_size
                total_size += size
                
                ext = item.suffix.lower()
                if ext not in file_types:
                    file_types[ext] = {'count': 0, 'size': 0}
                file_types[ext]['count'] += 1
                file_types[ext]['size'] += size
        
        return {
            'exists': True,
            'path': str(directory),
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'file_types': file_types
        }
    
    def export_json_metadata(self, output_path: Optional[str] = None) -> str:
        """Export complete metadata as JSON with file references"""
        if not output_path:
            output_path = f"pokemon_data_export_{self.export_timestamp}.json"
        
        print("📋 Generating JSON metadata export...")
        
        # Generate comprehensive inventory
        inventory = self.scan_data_sources()
        
        # Add detailed file listings for each source
        for source_name, source_path in self.sources.items():
            if source_path.exists():
                inventory['sources'][source_name]['files'] = self._get_file_listing(source_path)
        
        # Add Pokemon-specific metadata
        inventory['pokemon_data'] = self._extract_pokemon_metadata()
        
        # Save JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(inventory, f, indent=2, ensure_ascii=False)
        
        print(f"✅ JSON metadata exported to: {output_path}")
        return output_path
    
    def _get_file_listing(self, directory: Path) -> List[Dict]:
        """Get detailed file listing with metadata"""
        files = []
        
        for item in directory.rglob('*'):
            if item.is_file():
                relative_path = item.relative_to(directory)
                file_info = {
                    'path': str(relative_path),
                    'full_path': str(item),
                    'size_bytes': item.stat().st_size,
                    'extension': item.suffix.lower(),
                    'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                }
                
                # Add hash for integrity checking
                if item.stat().st_size < 10 * 1024 * 1024:  # Only hash files < 10MB
                    try:
                        with open(item, 'rb') as f:
                            file_info['md5_hash'] = hashlib.md5(f.read()).hexdigest()
                    except:
                        pass
                
                files.append(file_info)
        
        return files
    
    def _extract_pokemon_metadata(self) -> Dict:
        """Extract Pokemon-specific metadata"""
        pokemon_meta = {
            'generations': {},
            'sprite_types': [],
            'data_formats': []
        }
        
        # Scan for generation data
        for source_name, source_path in self.sources.items():
            if source_path.exists():
                for gen_dir in source_path.glob('generation_*'):
                    if gen_dir.is_dir():
                        gen_num = gen_dir.name.split('_')[1]
                        if gen_num not in pokemon_meta['generations']:
                            pokemon_meta['generations'][gen_num] = {}
                        
                        pokemon_meta['generations'][gen_num][source_name] = {
                            'path': str(gen_dir),
                            'pokemon_count': len(list(gen_dir.glob('**/pokemon_sprites/*.gif'))) if (gen_dir / 'pokemon_sprites').exists() else 0,
                            'has_data': (gen_dir / 'data').exists(),
                            'has_sprites': (gen_dir / 'pokemon_sprites').exists(),
                            'has_cards': (gen_dir / 'pokemon_cards').exists()
                        }
        
        return pokemon_meta
    
    def export_zip_archive(self, output_path: Optional[str] = None, include_sources: Optional[List[str]] = None) -> str:
        """Export data as organized ZIP archive"""
        if not output_path:
            output_path = f"pokemon_data_archive_{self.export_timestamp}.zip"
        
        if include_sources is None:
            include_sources = list(self.sources.keys())
        
        print(f"📦 Creating ZIP archive: {output_path}")
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add metadata
            metadata = self.scan_data_sources()
            zipf.writestr('_metadata.json', json.dumps(metadata, indent=2))
            
            # Add README
            readme_content = self._generate_export_readme(include_sources)
            zipf.writestr('README.md', readme_content)
            
            # Add each requested source
            for source_name in include_sources:
                source_path = self.sources.get(source_name)
                if source_path and source_path.exists():
                    print(f"   📁 Adding {source_name}...")
                    self._add_directory_to_zip(zipf, source_path, source_name)
        
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"✅ ZIP archive created: {output_path} ({file_size:.1f}MB)")
        return output_path
    
    def _add_directory_to_zip(self, zipf: zipfile.ZipFile, directory: Path, prefix: str):
        """Add directory contents to ZIP with prefix"""
        for item in directory.rglob('*'):
            if item.is_file():
                relative_path = item.relative_to(directory)
                zip_path = f"{prefix}/{relative_path}"
                zipf.write(item, zip_path)
    
    def export_clean_copy(self, output_dir: Optional[str] = None, include_sources: Optional[List[str]] = None) -> str:
        """Export as clean directory structure"""
        if not output_dir:
            output_dir = f"pokemon_data_clean_{self.export_timestamp}"
        
        if include_sources is None:
            include_sources = list(self.sources.keys())
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"📁 Creating clean copy: {output_path}")
        
        # Copy metadata
        metadata = self.scan_data_sources()
        with open(output_path / '_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Copy README
        readme_content = self._generate_export_readme(include_sources)
        with open(output_path / 'README.md', 'w') as f:
            f.write(readme_content)
        
        # Copy each source
        for source_name in include_sources:
            source_path = self.sources.get(source_name)
            if source_path and source_path.exists():
                dest_path = output_path / source_name
                print(f"   📁 Copying {source_name}...")
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
        
        print(f"✅ Clean copy created: {output_path}")
        return str(output_path)
    
    def export_database(self, output_path: Optional[str] = None) -> str:
        """Export data as SQLite database"""
        if not output_path:
            output_path = f"pokemon_data_{self.export_timestamp}.db"
        
        print(f"🗄️  Creating SQLite database: {output_path}")
        
        conn = sqlite3.connect(output_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                relative_path TEXT,
                full_path TEXT,
                size_bytes INTEGER,
                extension TEXT,
                md5_hash TEXT,
                modified_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE pokemon (
                id INTEGER PRIMARY KEY,
                name TEXT,
                generation INTEGER,
                sprite_path TEXT,
                data_path TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert metadata
        metadata = self.scan_data_sources()
        cursor.execute('INSERT INTO metadata (key, value) VALUES (?, ?)', 
                      ('export_metadata', json.dumps(metadata)))
        
        # Insert file data
        for source_name, source_path in self.sources.items():
            if source_path.exists():
                files = self._get_file_listing(source_path)
                for file_info in files:
                    cursor.execute('''
                        INSERT INTO files (source, relative_path, full_path, size_bytes, extension, md5_hash, modified_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        source_name, 
                        file_info['path'], 
                        file_info['full_path'],
                        file_info['size_bytes'],
                        file_info['extension'],
                        file_info.get('md5_hash'),
                        file_info['modified']
                    ))
        
        conn.commit()
        conn.close()
        
        db_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"✅ Database created: {output_path} ({db_size:.1f}MB)")
        return output_path
    
    def _generate_export_readme(self, included_sources: List[str]) -> str:
        """Generate README for exported data"""
        return f"""# Pokemon Data Export

**Export Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Source Workspace:** {self.workspace_path.absolute()}

## Included Data Sources

{chr(10).join(f"- **{source}**: {self.sources[source]}" for source in included_sources)}

## Data Structure

### Phygitals Dynamic Pokemon
- **Location**: `phygitals_dynamic/`
- **Content**: Animated Pokemon sprites from Phygitals.com
- **Generations**: 1-9 available
- **Formats**: Animated GIFs, Pokemon cards, backgrounds, trainer packs

### PokeAPI Sprites  
- **Location**: `pokeapi_sprites/`
- **Content**: Official Pokemon artwork and sprites
- **Formats**: PNG sprites (front, back, shiny, female variants)
- **Data**: JSON metadata files

### Original Website
- **Location**: `scraped_site/`
- **Content**: Static website files from original scraping
- **Formats**: HTML, CSS, JS, images

## Usage Examples

### JavaScript/Node.js
```javascript
const pokemonData = require('./_metadata.json');
console.log(pokemonData.sources);
```

### Python
```python
import json
with open('_metadata.json') as f:
    data = json.load(f)
print(data['pokemon_data']['generations'])
```

### Direct File Access
All Pokemon sprites are organized by generation:
- `phygitals_dynamic/generation_1/pokemon_sprites/001.gif` (Bulbasaur)
- `phygitals_dynamic/generation_1/pokemon_sprites/025.gif` (Pikachu)
- etc.

## File Integrity
MD5 hashes are provided in `_metadata.json` for files under 10MB to verify integrity.

## License
Data scraped from public sources. Please respect original source terms of use.
"""

def main():
    parser = argparse.ArgumentParser(description='Export Pokemon data for use in other projects')
    parser.add_argument('--format', choices=['json', 'zip', 'copy', 'database', 'all'], 
                       default='all', help='Export format')
    parser.add_argument('--output', help='Output path/filename')
    parser.add_argument('--sources', nargs='*', 
                       choices=['phygitals_dynamic', 'phygitals_complete', 'pokeapi_sprites', 'scraped_site'],
                       help='Specific sources to include (default: all)')
    parser.add_argument('--workspace', default='.', help='Workspace directory path')
    
    args = parser.parse_args()
    
    # Initialize exporter
    exporter = PokemonDataExporter(args.workspace)
    
    # Scan and display inventory
    print("\n" + "="*60)
    print("🎮 POKEMON DATA EXPORT TOOL")
    print("="*60)
    
    inventory = exporter.scan_data_sources()
    print(f"\n📊 Data Summary:")
    total_files = sum(src.get('total_files', 0) for src in inventory['sources'].values() if src.get('exists'))
    total_size = sum(src.get('total_size_mb', 0) for src in inventory['sources'].values() if src.get('exists'))
    print(f"   Total Files: {total_files:,}")
    print(f"   Total Size: {total_size:.1f}MB")
    
    # Export in requested format(s)
    exported_files = []
    
    if args.format in ['json', 'all']:
        output = args.output if args.format == 'json' else None
        exported_files.append(exporter.export_json_metadata(output))
    
    if args.format in ['zip', 'all']:
        output = args.output if args.format == 'zip' else None
        exported_files.append(exporter.export_zip_archive(output, args.sources))
    
    if args.format in ['copy', 'all']:
        output = args.output if args.format == 'copy' else None
        exported_files.append(exporter.export_clean_copy(output, args.sources))
    
    if args.format in ['database', 'all']:
        output = args.output if args.format == 'database' else None
        exported_files.append(exporter.export_database(output))
    
    # Summary
    print(f"\n🎉 Export Complete!")
    print(f"📦 Generated {len(exported_files)} export file(s):")
    for file in exported_files:
        if os.path.isfile(file):
            size = os.path.getsize(file) / (1024 * 1024)
            print(f"   📄 {file} ({size:.1f}MB)")
        else:
            print(f"   📁 {file} (directory)")
    
    print(f"\n🚀 Ready to use in other projects!")

if __name__ == "__main__":
    main() 