#!/usr/bin/env python3
"""
Launch Pokemon TCG Integration
==============================
Quick launcher to integrate Pokemon TCG cards from PokeMon Scrape project
"""

import os
import sys
from pathlib import Path

def main():
    print("🎴 Pokemon TCG Integration Launcher")
    print("=" * 40)
    
    # Check if PokeMon Scrape project exists
    pokemon_scrape_path = Path("../PokeMon Scrape")
    if not pokemon_scrape_path.exists():
        print("❌ PokeMon Scrape project not found!")
        print(f"Looking for: {pokemon_scrape_path.absolute()}")
        return
    
    tcg_data_path = pokemon_scrape_path / "pokemon_tcg_data"
    if not tcg_data_path.exists():
        print("❌ Pokemon TCG data not found!")
        print(f"Looking for: {tcg_data_path.absolute()}")
        return
    
    # Count available cards
    card_files = list(tcg_data_path.glob("card_*.json"))
    print(f"✅ Found {len(card_files)} Pokemon TCG cards")
    
    # Ask user for integration scope
    print("\n🎯 Integration Options:")
    print("1. Test Integration (100 cards) - Quick test")
    print("2. Small Integration (1,000 cards) - Moderate test") 
    print("3. Full Integration (19,155+ cards) - Complete collection")
    print("4. Scan Only (no downloads) - Check what's available")
    
    try:
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            run_integration(max_cards=100)
        elif choice == "2":
            run_integration(max_cards=1000)
        elif choice == "3":
            run_integration(max_cards=None)
        elif choice == "4":
            scan_only()
        else:
            print("❌ Invalid choice")
            return
            
    except KeyboardInterrupt:
        print("\n👋 Integration cancelled")

def run_integration(max_cards=None):
    """Run the TCG integration"""
    print(f"\n🚀 Starting integration...")
    if max_cards:
        print(f"📊 Limiting to {max_cards} cards for testing")
    
    try:
        from pokemon_tcg_integrator import PokemonTCGIntegrator
        
        integrator = PokemonTCGIntegrator()
        
        if max_cards:
            # Create limited integrator for testing
            integrator.test_mode = True
            integrator.max_cards = max_cards
        
        # Run integration
        master_index = integrator.run_full_integration()
        
        print("\n🎉 Integration Complete!")
        print(f"📁 View cards at: http://localhost:8005/api_tcg_card_gallery.html")
        
    except ImportError:
        print("❌ Integration module not found. Please check pokemon_tcg_integrator.py")
    except Exception as e:
        print(f"❌ Integration failed: {e}")

def scan_only():
    """Scan available cards without downloading"""
    print("\n🔍 Scanning available Pokemon TCG cards...")
    
    try:
        from pokemon_tcg_integrator import PokemonTCGIntegrator
        
        integrator = PokemonTCGIntegrator()
        gen_stats, set_stats = integrator.scan_available_cards()
        
        print(f"\n📋 Set Distribution (Top 20):")
        sorted_sets = sorted(set_stats.items(), key=lambda x: x[1], reverse=True)
        for set_code, count in sorted_sets[:20]:
            generation = integrator.get_generation_for_set(set_code)
            gen_label = generation.upper() if generation else "Unknown"
            print(f"  {set_code}: {count} cards ({gen_label})")
        
    except Exception as e:
        print(f"❌ Scan failed: {e}")

if __name__ == "__main__":
    main() 