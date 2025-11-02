import pandas as pd
import json
import os
from difflib import get_close_matches

# Use project directory for CSV files
SOURCE_FOLDER = 'items'
OUTPUT_JSON = 'item_map.json'

# --- Configuration: All files to read ---
FILES_TO_PROCESS = {
    'items.csv': ('items', 'Item_ID', 'Item_Name'),
    'armors.csv': ('armors', 'Item_ID', 'Item_Name'),
    'melee_weapons.csv': ('melee_weapons', 'Item_ID', 'Item_Name'),
    'ranged_weapons.csv': ('ranged_weapons', 'Item_ID', 'Item_Name'),
    'shields.csv': ('shields', 'Shield_ID', 'Shield_name'),
    'mounts.csv': ('horses', 'Mount_ID', 'Mount_Name'),
}

ITEM_TYPES_FILE = os.path.join(SOURCE_FOLDER, 'items_types_ids.csv')

def find_fuzzy_match(item_name, item_map, cutoff=0.8):
    """Find the best fuzzy match for an item name"""
    matches = get_close_matches(item_name, item_map.keys(), n=1, cutoff=cutoff)
    return matches[0] if matches else None

def create_map():
    """
    Reads ALL item files and creates a master map of
    {"Item Name": {"id": 123, "slot": "slot_name"}}
    """
    print(f"Creating master item map from CSV files in '{SOURCE_FOLDER}'...")
    master_item_map = {}
    
    # 1. Load item types (ID -> Name)
    try:
        df_types = pd.read_csv(ITEM_TYPES_FILE)
        type_id_to_slot_name = df_types.set_index('Item_Type_ID')['Item_Type_Name'].to_dict()
        print(f"Loaded {len(type_id_to_slot_name)} item types")
    except Exception as e:
        print(f"CRITICAL ERROR reading {ITEM_TYPES_FILE}: {e}")
        print("This file is required to assign slots. Aborting.")
        return

    # 2. Process all configured item files
    for filename, (default_slot, id_col, name_col) in FILES_TO_PROCESS.items():
        filepath = os.path.join(SOURCE_FOLDER, filename)
        if not os.path.exists(filepath):
            print(f"Warning: File not found, skipping: {filepath}")
            continue

        try:
            df = pd.read_csv(filepath)
            count = 0
            
            if id_col not in df.columns or name_col not in df.columns:
                print(f"Warning: Skipping '{filename}'. Missing columns: '{id_col}' or '{name_col}'")
                continue

            for _, row in df.iterrows():
                item_name = str(row[name_col]).strip()
                item_id = int(row[id_col])
                
                # Determine the slot
                slot = default_slot
                if 'Item_Type_ID' in row and pd.notna(row['Item_Type_ID']):
                    type_id = int(row['Item_Type_ID'])
                    slot = type_id_to_slot_name.get(type_id, default_slot)
                elif 'Item_Type' in row:
                    item_type_name = str(row['Item_Type']).lower().replace(' ', '_')
                    if item_type_name in type_id_to_slot_name.values():
                        slot = item_type_name

                if item_name not in master_item_map:
                    master_item_map[item_name] = {"id": item_id, "slot": slot}
                    count += 1
                
            print(f"Loaded {count} new items from {filename}")
            
        except Exception as e:
            print(f"Error reading {filepath}: {e}")

    # 3. Add generic fallback items
    generic_mappings = {
        "Horse": "Hunter",
        "Bow": "Hunting Bow",
        "Sword": "Iron Arming Sword",
        "Spear": "Simple Spear",
        "Axe": "Hatchet",
        "Mace": "Club",
    }
    
    for generic_name, specific_name in generic_mappings.items():
        if generic_name not in master_item_map and specific_name in master_item_map:
            master_item_map[generic_name] = master_item_map[specific_name].copy()
            print(f"Added generic '{generic_name}' mapping from '{specific_name}'")

    # 4. Add known wiki-to-game mappings
    # These are manually curated mappings for items where wiki names differ from game data
    wiki_to_game_mappings = {
        # Battanian Equipment
        "Highland Spiked Club": "Highland Spiked Club",
        "Highland Villager Tunic": "Belted Tunic",  # Approximate match
        "Highland Tunic": "Light Tunic",  # Approximate match
        "Tasseled Highland Cloak": None,  # Need to find in data
        "Highland Furred Cloak": None,  # Need to find in data
        
        # Common armor variations
        "Wrapped Shoes": "Wrapped Shoes",
        "Rough Tied Boots": "Rough Tied Boots",
        "Buttoned Leather Bracers": "Buttoned Leather Bracers",
    }
    
    added_wiki_mappings = 0
    for wiki_name, game_name in wiki_to_game_mappings.items():
        if wiki_name not in master_item_map:
            if game_name and game_name in master_item_map:
                master_item_map[wiki_name] = master_item_map[game_name].copy()
                added_wiki_mappings += 1
            elif game_name is None:
                # Try fuzzy matching
                match = find_fuzzy_match(wiki_name, master_item_map, cutoff=0.7)
                if match:
                    master_item_map[wiki_name] = master_item_map[match].copy()
                    print(f"Fuzzy matched '{wiki_name}' to '{match}'")
                    added_wiki_mappings += 1
    
    if added_wiki_mappings > 0:
        print(f"Added {added_wiki_mappings} wiki-to-game item mappings")

    # 5. Create reverse lookup helpers for debugging
    id_to_name = {v['id']: k for k, v in master_item_map.items()}
    
    # 6. Save the map to JSON
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(master_item_map, f, indent=2)
        
    print(f"\nSuccessfully created {OUTPUT_JSON} with {len(master_item_map)} total items.")
    
    # 7. Save a reverse lookup file for convenience
    reverse_map = {
        "id_to_name": id_to_name,
        "slot_counts": {}
    }
    
    # Count items per slot
    for item_data in master_item_map.values():
        slot = item_data['slot']
        reverse_map['slot_counts'][slot] = reverse_map['slot_counts'].get(slot, 0) + 1
    
    with open('item_map_reverse.json', 'w', encoding='utf-8') as f:
        json.dump(reverse_map, f, indent=2)
    
    print(f"Created item_map_reverse.json with ID lookups")
    
    # 8. Print statistics
    print("\nItem Statistics:")
    for slot, count in sorted(reverse_map['slot_counts'].items()):
        print(f"  {slot:20} {count:4} items")
    
    # Print some sample mappings
    print("\nSample item mappings:")
    for i, (name, data) in enumerate(list(master_item_map.items())[:10]):
        print(f"  {name:30} → ID={data['id']:4}, Slot={data['slot']}")

def search_item_by_name(search_term):
    """Helper function to search for items"""
    if not os.path.exists(OUTPUT_JSON):
        print("item_map.json not found. Run create_map() first.")
        return
    
    with open(OUTPUT_JSON, 'r') as f:
        item_map = json.load(f)
    
    search_lower = search_term.lower()
    matches = [(name, data) for name, data in item_map.items() 
               if search_lower in name.lower()]
    
    if matches:
        print(f"\nFound {len(matches)} matches for '{search_term}':")
        for name, data in sorted(matches)[:20]:  # Show first 20
            print(f"  {name:40} ID={data['id']:4}, Slot={data['slot']}")
        if len(matches) > 20:
            print(f"  ... and {len(matches) - 20} more")
    else:
        print(f"No matches found for '{search_term}'")
        
        # Try fuzzy matching
        fuzzy = get_close_matches(search_term, item_map.keys(), n=5, cutoff=0.6)
        if fuzzy:
            print(f"\nDid you mean:")
            for match in fuzzy:
                print(f"  {match}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "search":
        if len(sys.argv) > 2:
            search_item_by_name(" ".join(sys.argv[2:]))
        else:
            print("Usage: python create_item_map_enhanced.py search <item_name>")
    else:
        create_map()
