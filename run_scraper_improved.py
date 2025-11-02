# run_scraper_improved.py
import requests
import re
import json
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple
import time
import os

# --- Configuration ---
ITEM_MAP_JSON = 'item_map.json'
# --- End Configuration ---

class BannerlordTroopScraper:
    def __init__(self):
        self.base_url = "https://mountandblade.fandom.com"
        self.api_url = f"{self.base_url}/api.php"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BannerlordTroopScraper/1.0'
        })
        
        # Major factions in Bannerlord
        self.factions = {
            "Aserai": "Aserai",
            "Battania": "Battanian", 
            "Empire": "Imperial",
            "Khuzait": "Khuzait",
            "Sturgia": "Sturgian",
            "Vlandia": "Vlandian"
        }
        
        self.cultures = {}
        self.culture_id_counter = 1
        
        # Known troop upgrade paths from research
        self.troop_trees = {
            "Aserai": {
                "common": [
                    ["Aserai Recruit", "Aserai Tribesman", "Aserai Footman", "Aserai Infantry", "Aserai Veteran Infantry"],
                    ["Aserai Recruit", "Aserai Tribesman", "Aserai Skirmisher", "Aserai Veteran Skirmisher", "Aserai Master Skirmisher"],
                    ["Aserai Recruit", "Aserai Mameluke Soldier", "Aserai Mameluke Axeman", "Aserai Mameluke Cavalry", "Aserai Mameluke Heavy Cavalry"],
                    ["Aserai Recruit", "Aserai Mameluke Soldier", "Aserai Mameluke Regular", "Aserai Mameluke Cavalry", "Aserai Mameluke Heavy Cavalry"],
                    ["Aserai Recruit", "Aserai Tribesman", "Aserai Light Archer", "Aserai Archer", "Aserai Master Archer"]
                ],
                "noble": [
                    ["Aserai Youth", "Aserai Tribal Horseman", "Aserai Faris", "Aserai Veteran Faris", "Aserai Vanguard Faris"]
                ]
            },
            "Battania": {
                "common": [
                    ["Battanian Recruit", "Battanian Clanwarrior", "Battanian Trained Warrior", "Battanian Picked Warrior", "Battanian Veteran Warrior"],
                    ["Battanian Recruit", "Battanian Wood Runner", "Battanian Raider", "Battanian Scout", "Battanian Veteran Scout"],
                    ["Battanian Recruit", "Battanian Clanwarrior", "Battanian Woodrunner", "Battanian Skirmisher", "Battanian Veteran Skirmisher"],
                    ["Battanian Recruit", "Battanian Trained Warrior", "Battanian Oathsworn", "Battanian Hero"],
                ],
                "noble": [
                    ["Battanian Highborn Youth", "Battanian Highborn Warrior", "Battanian Hero", "Battanian Fian", "Battanian Fian Champion"]
                ]
            },
            "Empire": {
                "common": [
                    ["Imperial Recruit", "Imperial Infantryman", "Imperial Trained Infantryman", "Imperial Legionary", "Imperial Veteran Legionary", "Imperial Palatine Guard"],
                    ["Imperial Recruit", "Imperial Infantryman", "Imperial Trained Infantryman", "Imperial Menavliaton", "Imperial Elite Menavliaton"],
                    ["Imperial Recruit", "Imperial Infantryman", "Imperial Archer", "Imperial Veteran Archer", "Imperial Master Archer"],
                    ["Imperial Recruit", "Imperial Infantryman", "Imperial Crossbowman", "Imperial Sergeant Crossbowman"],
                ],
                "noble": [
                    ["Imperial Vigla Recruit", "Imperial Equite", "Imperial Heavy Horseman", "Imperial Cataphract", "Imperial Elite Cataphract"],
                    ["Imperial Vigla Recruit", "Imperial Bucellarii", "Imperial Bucellarii Heavy Cavalry"]
                ]
            },
            "Khuzait": {
                "common": [
                    ["Khuzait Nomad", "Khuzait Tribal Warrior", "Khuzait Spearman", "Khuzait Lancer"],
                    ["Khuzait Nomad", "Khuzait Tribal Warrior", "Khuzait Hunter", "Khuzait Marksman", "Khuzait Master Archer"],
                    ["Khuzait Nomad", "Khuzait Raider", "Khuzait Horse Archer", "Khuzait Horse Archer", "Khuzait Heavy Horse Archer"],
                ],
                "noble": [
                    ["Khuzait Noble's Son", "Khuzait Qanqli", "Khuzait Torguud", "Khuzait Kheshig", "Khuzait Khan's Guard"],
                    ["Khuzait Noble's Son", "Khuzait Darkhan", "Khuzait Heavy Lancer"]
                ]
            },
            "Sturgia": {
                "common": [
                    ["Sturgian Recruit", "Sturgian Warrior", "Sturgian Soldier", "Sturgian Spearman", "Sturgian Ulfhednar", "Sturgian Shock Warrior"],
                    ["Sturgian Recruit", "Sturgian Woodsman", "Sturgian Hunter", "Sturgian Veteran Bowman"],
                    ["Sturgian Recruit", "Sturgian Warrior", "Sturgian Hardened Brigand", "Sturgian Brigand"],
                    ["Sturgian Recruit", "Sturgian Warrior", "Sturgian Soldier", "Sturgian Axeman", "Sturgian Heavy Axeman"],
                ],
                "noble": [
                    ["Sturgian Warrior Son", "Varyag", "Varyag Veteran", "Sturgian Druzhinnik", "Sturgian Druzhinnik Champion"]
                ]
            },
            "Vlandia": {
                "common": [
                    ["Vlandian Recruit", "Vlandian Footman", "Vlandian Infantry", "Vlandian Voulgier"],
                    ["Vlandian Recruit", "Vlandian Levy Crossbowman", "Vlandian Crossbowman", "Vlandian Hardened Crossbowman", "Vlandian Sharpshooter"],
                ],
                "noble": [
                    ["Vlandian Squire", "Vlandian Gallant", "Vlandian Knight", "Vlandian Champion", "Vlandian Banner Knight"]
                ]
            }
        }
        
        self.item_map = self.load_item_map()
        self.equipment_data = [] # To store (troop_id, item_id, slot)
        self.missing_items = set() # Track items not found in map

    def load_item_map(self):
        """Loads the JSON map of item names to their IDs and slots."""
        if not os.path.exists(ITEM_MAP_JSON):
            print(f"Error: {ITEM_MAP_JSON} not found.")
            print("Please run 'create_item_map_csv.py' first.")
            return {}
        
        try:
            with open(ITEM_MAP_JSON, 'r', encoding='utf-8') as f:
                item_map = json.load(f)
                print(f"Loaded item map with {len(item_map)} items")
                return item_map
        except Exception as e:
            print(f"Error reading {ITEM_MAP_JSON}: {e}")
            return {}
    
    def get_category_members(self, category: str) -> List[str]:
        """Get all pages in a category using MediaWiki API"""
        params = {
            'action': 'query',
            'list': 'categorymembers',
            'cmtitle': f'Category:{category}',
            'cmlimit': 'max',
            'format': 'json'
        }
        
        try:
            response = self.session.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'query' in data and 'categorymembers' in data['query']:
                return [member['title'] for member in data['query']['categorymembers']]
            return []
        except Exception as e:
            print(f"Error fetching category {category}: {str(e)}")
            return []
    
    def get_page_info(self, page_title: str) -> Dict:
        """Fetch detailed page content using MediaWiki API"""
        params = {
            'action': 'parse',
            'page': page_title,
            'format': 'json',
            'prop': 'text|wikitext'
        }
        
        try:
            response = self.session.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'parse' in data:
                return {
                    'html': data['parse']['text']['*'],
                    'wikitext': data['parse'].get('wikitext', {}).get('*', '')
                }
            return {'html': '', 'wikitext': ''}
        except Exception as e:
            print(f"Error fetching {page_title}: {str(e)}")
            return {'html': '', 'wikitext': ''}
        
    def extract_equipment(self, soup: BeautifulSoup, troop_id: int):
        equipment_header = soup.find('span', {'id': 'Equipment'})
        if not equipment_header:
            return
        
        equipment_section = equipment_header.find_parent(['h2', 'h3'])
        if not equipment_section:
            return
        
        equipment_table = equipment_section.find_next('table')
        if not equipment_table:
            return
        
        slot_mapping = {
            'weapons': 'weapon',
            'weapon': 'weapon',
            'shield': 'shield',
            'head armor': 'head_armor',
            'shoulder armor': 'shoulder_armor',
            'body armor': 'body_armor',
            'hand armor': 'hand_armor',
            'leg armor': 'leg_armor',
            'foot armor': 'foot_armor',
            'mount': 'horse',
            'mount harness': 'horse_harness',
        }
        
        for row in equipment_table.find_all('tr'):
            cells = row.find_all(['th', 'td'])
            
            if len(cells) < 2:
                continue
            
            slot_name = cells[0].get_text(strip=True).lower()
            cell_text = cells[1].get_text().strip()
            
            if 'n/a' in cell_text.lower() or cell_text == '?':
                continue
            
            db_slot = slot_mapping.get(slot_name)
            if not db_slot:
                continue
            
            items_text = str(cells[1])
            items_text = items_text.replace('<br/>', '|').replace('<br />', '|').replace('<br>', '|')
            soup_cell = BeautifulSoup(items_text, 'html.parser')
            item_names = soup_cell.get_text().split('|')
            
            for item_name in item_names:
                item_name = item_name.strip()
                
                if not item_name or item_name == '?' or '(Possible)' in item_name:
                    continue
                
                item_name = item_name.replace('(Possible)', '').strip()
                if ' (' in item_name:
                    item_name = item_name.split(' (')[0]
                
                if item_name in self.item_map:
                    item_data = self.item_map[item_name]
                    self.equipment_data.append((troop_id, item_data['id'], item_data['slot']))
                else:
                    self.missing_items.add(item_name)
    
    def parse_troop_page(self, html: str, troop_name: str, faction: str, troop_id: int) -> Dict:
        """Parse individual troop page for stats AND equipment"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract tier
        tier = 1
        tier_match = re.search(r'tier-(\w+)', html, re.IGNORECASE)
        if tier_match:
            tier_text = tier_match.group(1).lower()
            tier_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6}
            tier = tier_map.get(tier_text, self.estimate_tier(troop_name))
        else:
            tier = self.estimate_tier(troop_name)
        
        # Extract wage
        wage = 0
        wage_match = re.search(r'(\d+)\s*denars?/day', html, re.IGNORECASE)
        if wage_match:
            wage = int(wage_match.group(1))
        else:
            wage = self.estimate_wage(tier)
        
        # Determine if mounted
        is_mounted = self.is_troop_mounted(troop_name, html)
        
        # Extract Equipment
        self.extract_equipment(soup, troop_id)
        
        return {
            'name': troop_name,
            'tier': tier,
            'wage': wage,
            'is_mounted': is_mounted,
            'faction': faction
        }
    
    def estimate_tier(self, troop_name: str) -> int:
        """Estimate tier based on troop name keywords"""
        name_lower = troop_name.lower()
        
        # Tier indicators in order of specificity
        if any(x in name_lower for x in ['champion', 'elite', 'master', 'khan\'s guard', 'banner knight']):
            return 6
        if any(x in name_lower for x in ['veteran', 'heavy', 'sergeant', 'cataphract', 'druzhinnik']):
            return 5
        if any(x in name_lower for x in ['trained', 'regular', 'picked', 'hardened', 'legionary']):
            return 4
        if any(x in name_lower for x in ['warrior', 'soldier', 'archer', 'cavalry', 'footman', 'infantry']):
            return 3
        if any(x in name_lower for x in ['tribesman', 'woodsman', 'skirmisher', 'hunter', 'raider']):
            return 2
        if any(x in name_lower for x in ['recruit', 'levy', 'nomad', 'youth', 'son']):
            return 1
        
        return 1  # Default to tier 1
    
    def estimate_wage(self, tier: int) -> int:
        """Estimate wage based on tier"""
        wage_map = {1: 2, 2: 4, 3: 8, 4: 12, 5: 18, 6: 25}
        return wage_map.get(tier, 2)
    
    def is_troop_mounted(self, troop_name: str, html: str) -> bool:
        """Determine if troop is mounted by checking Equipment table"""
        # Parse the HTML to find the Mount row in the Equipment table
        soup = BeautifulSoup(html, 'html.parser')
        
        mount_found = False
        has_mount = False
        
        # Look for the Equipment section
        equipment_header = soup.find('span', {'id': 'Equipment'})
        if equipment_header:
            equipment_section = equipment_header.find_parent(['h2', 'h3'])
            if equipment_section:
                equipment_table = equipment_section.find_next('table')
                if equipment_table:
                    # Find the Mount row
                    for row in equipment_table.find_all('tr'):
                        cells = row.find_all(['th', 'td'])
                        if len(cells) >= 2:
                            header = cells[0].get_text(strip=True).lower()
                            value = cells[1].get_text(strip=True)
                            
                            if header == 'mount':
                                # Check if mount value is N/A or ? or empty
                                if value.upper() == 'N/A':
                                    return False
                                elif value == '?' or not value:
                                    has_mount = False
                                else:
                                    return True
                                break
        
        # Fallback: check for mounted keywords in name (used when no Equipment table or Mount row)
        name_lower = troop_name.lower()
        mounted_keywords = ['cavalry', 'horseman', 'horse archer', 'lancer', 'knight', 
                          'cataphract', 'faris', 'mameluke', 'equite', 'bucellarii',
                          'druzhinnik', 'kheshig', 'darkhan', 'mounted']
        
        if any(keyword in name_lower for keyword in mounted_keywords):
            return True
        
        # Default to not mounted if we can't determine
        return False
    
    def get_or_create_culture_id(self, culture_name: str) -> int:
        """Get existing culture ID or create new one"""
        if culture_name not in self.cultures:
            self.cultures[culture_name] = self.culture_id_counter
            self.culture_id_counter += 1
        return self.cultures[culture_name]
    
    def scrape_all_factions(self) -> Dict:
        """Main scraping method"""
        all_troops = []
        troop_id = 1
        

        # Limit option for testing; set to a low number to limit troops scraped
        max_troops = 999999 

        for faction_key, culture_prefix in self.factions.items():
            print(f"\n{'='*60}")
            print(f"Processing {faction_key} ({culture_prefix})")
            print(f"{'='*60}")
            
            culture_id = self.get_or_create_culture_id(culture_prefix)
            
            # Get all troop types for this faction
            troop_types = []
            if faction_key in self.troop_trees:
                for tree_type in ['common', 'noble']:
                    if tree_type in self.troop_trees[faction_key]:
                        for path in self.troop_trees[faction_key][tree_type]:
                            troop_types.extend(path)
            
            # Remove duplicates while preserving order
            seen = set()
            troop_types = [x for x in troop_types if not (x in seen or seen.add(x))]
            
            print(f"Found {len(troop_types)} troops to scrape")
            
            for troop_name in troop_types:
                if troop_id > max_troops:  # STOP AFTER 5 TROOPS
                    break

                print(f"\n  Scraping: {troop_name}")
                
                # Fetch page data
                page_data = self.get_page_info(troop_name)
                
                if page_data['html']:
                    # Parse the page
                    troop_data = self.parse_troop_page(
                        page_data['html'], 
                        troop_name, 
                        faction_key,
                        troop_id
                    )
                    troop_data['troop_id'] = troop_id
                    troop_data['culture_id'] = culture_id
                    
                    all_troops.append(troop_data)
                    print(f"    ✓ Tier {troop_data['tier']}, Wage: {troop_data['wage']}, "
                          f"Mounted: {troop_data['is_mounted']}")
                    
                    troop_id += 1
                    
                    # Be nice to the API
                    time.sleep(0.5)
                else:
                    print(f"    ✗ Failed to fetch page")
        
        return {
            'troops': all_troops,
            'cultures': self.cultures,
            'upgrade_paths': self.build_upgrade_paths(all_troops)
        }
    
    def build_upgrade_paths(self, troops: List[Dict]) -> List[Dict]:
        """Build upgrade paths based on predefined trees"""
        upgrade_paths = []
        upgrade_paths_set = set()
        
        # Create name -> id mapping
        troop_name_to_id = {troop['name']: troop['troop_id'] for troop in troops}
        
        # Process each faction's troop trees
        for faction, trees in self.troop_trees.items():
            for tree_type in ['common', 'noble']:
                if tree_type not in trees:
                    continue
                
                for path in trees[tree_type]:
                    # For each consecutive pair in the path
                    for i in range(len(path) - 1):
                        base_troop = path[i]
                        upgraded_troop = path[i + 1]
                        
                        if base_troop in troop_name_to_id and upgraded_troop in troop_name_to_id:
                            base_id = troop_name_to_id[base_troop]
                            upgraded_id = troop_name_to_id[upgraded_troop]
                            path_key = (base_id, upgraded_id)
                            
                            # Only add if not already present
                            if path_key not in upgrade_paths_set:
                                upgrade_paths_set.add(path_key)
                                upgrade_paths.append({
                                    'base_troop_id': base_id,
                                    'upgraded_troop_id': upgraded_id,
                                    'xp_cost': (i + 1) * 100  # Estimated XP
                                })
        
        return upgrade_paths
    
    def generate_sql(self, data: Dict) -> str:
        """Generate SQL INSERT statements"""
        sql = []
        
        sql.append("-- ===========================================")
        sql.append("-- Mount & Blade II: Bannerlord Troops Database")
        sql.append("-- ===========================================\n")
        
        # Troops Table
        sql.append("-- Troops Table")
        sql.append("INSERT INTO Troops (troop_id, name, tier, wage, is_mounted, culture_id) VALUES")
        troop_inserts = []
        for troop in data['troops']:
            name_escaped = troop['name'].replace("'", "''")
            troop_inserts.append(
                f"  ({troop['troop_id']}, '{name_escaped}', {troop['tier']}, "
                f"{troop['wage']}, {1 if troop['is_mounted'] else 0}, {troop['culture_id']})"
            )
        sql.append(",\n".join(troop_inserts) + ";\n")
        
        # Attributes Table
        sql.append("-- Attributes Table")
        sql.append("INSERT INTO Attributes (attribute_id, name, description) VALUES")
        attributes = ['Vigor', 'Control', 'Endurance', 'Cunning', 'Social', 'Intelligence']
        attr_inserts = []
        for idx, attr in enumerate(attributes, 1):
            attr_inserts.append(f"  ({idx}, '{attr}', 'Base character attribute')")
        sql.append(",\n".join(attr_inserts) + ";\n")
        
        # Skills Table
        sql.append("-- Skills Table")
        sql.append("INSERT INTO Skills (skill_id, name, description, is_combat_skill, attribute_id) VALUES")
        skills = [
            ('One Handed', True, 1), ('Two Handed', True, 1), ('Polearm', True, 1),
            ('Bow', True, 2), ('Crossbow', True, 2), ('Throwing', True, 2),
            ('Riding', True, 3), ('Athletics', True, 3),
            ('Tactics', False, 4), ('Scouting', False, 4), ('Roguery', False, 4),
            ('Charm', False, 5), ('Leadership', False, 5), ('Trade', False, 5),
            ('Steward', False, 6), ('Medicine', False, 6), ('Engineering', False, 6)
        ]
        skill_inserts = []
        for idx, (skill_name, is_combat, attr_id) in enumerate(skills, 1):
            skill_inserts.append(
                f"  ({idx}, '{skill_name}', '{skill_name} skill', {1 if is_combat else 0}, {attr_id})"
            )
        sql.append(",\n".join(skill_inserts) + ";\n")
        
        # Upgrade Paths Table
        sql.append("-- Troop_Upgrade_Paths Table")
        sql.append("INSERT INTO Troop_Upgrade_Paths (base_troop_id, upgraded_troop_id, xp_cost) VALUES")
        upgrade_inserts = []
        for upgrade in data['upgrade_paths']:
            upgrade_inserts.append(
                f"  ({upgrade['base_troop_id']}, {upgrade['upgraded_troop_id']}, {upgrade['xp_cost']})"
            )
        sql.append(",\n".join(upgrade_inserts) + ";\n")
        
        # Equipment Junction Table
        sql.append("-- Troop_Equipment_Junction Table")
        sql.append("INSERT INTO Troop_Equipment_Junction (troop_id, item_id, slot) VALUES")
        equipment_inserts = []
        # Use set to avoid duplicates
        unique_equipment = sorted(list(set(self.equipment_data)))
        for (troop_id, item_id, slot) in unique_equipment:
            slot_escaped = slot.replace("'", "''")
            equipment_inserts.append(
                f"  ({troop_id}, {item_id}, '{slot_escaped}')"
            )
        
        if equipment_inserts:
            sql.append(",\n".join(equipment_inserts) + ";\n")
        else:
            sql.append("-- (No equipment data found)\n")
        
        return "\n".join(sql)

def main():
    print("="*60)
    print("Mount & Blade II: Bannerlord Troop Data Scraper")
    print("="*60)
    
    if not os.path.exists(ITEM_MAP_JSON):
        print(f"\nError: '{ITEM_MAP_JSON}' not found.")
        print("This file is required to map scraped item names to their IDs.")
        print("\nPlease run 'create_item_map_csv.py' first to generate this file.")
        return

    scraper = BannerlordTroopScraper()
    
    print("\nStarting scraping process...")
    print("This will fetch data from the Mount & Blade Fandom Wiki")
    print("-"*60)
    
    data = scraper.scrape_all_factions()
    
    print("\n" + "="*60)
    print("Scraping Complete!")
    print("="*60)
    print(f"Total troops: {len(data['troops'])}")
    print(f"Total cultures: {len(data['cultures'])}")
    print(f"Total upgrade paths: {len(data['upgrade_paths'])}")
    print(f"Total equipment links: {len(scraper.equipment_data)}")
    print(f"Unique equipment entries: {len(set(scraper.equipment_data))}")
    
    if scraper.missing_items:
        print(f"\nWarning: {len(scraper.missing_items)} items not found in item map:")
        for item in sorted(list(scraper.missing_items))[:20]:  # Show first 20
            print(f"  - {item}")
        if len(scraper.missing_items) > 20:
            print(f"  ... and {len(scraper.missing_items) - 20} more")
    
    # Show sample troops per faction
    print("\nTroops per faction:")
    for culture_name, culture_id in sorted(data['cultures'].items(), key=lambda x: x[1]):
        count = len([t for t in data['troops'] if t['culture_id'] == culture_id])
        print(f"  {culture_name}: {count} troops")
    
    print("\n" + "="*60)
    print("Generating SQL...")
    print("="*60)
    sql = scraper.generate_sql(data)
    
    # Save to file
    with open('bannerlord_troops.sql', 'w', encoding='utf-8') as f:
        f.write(sql)
    
    print("\n✓ SQL file saved as 'bannerlord_troops.sql'")
    
    # Save JSON (for reference)
    json_data = {
        'troops': data['troops'],
        'cultures': data['cultures'],
        'upgrade_paths': data['upgrade_paths']
    }
    
    with open('bannerlord_troops.json', 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)
    
    print("✓ JSON data saved as 'bannerlord_troops.json'")
    
    # Print sample
    print("\n" + "="*60)
    print("Sample Output (first 30 lines):")
    print("="*60)
    lines = sql.split('\n')
    for line in lines[:30]:
        print(line)
    if len(lines) > 30:
        print("...")
        print(f"\n(Total {len(lines)} lines in SQL file)")

if __name__ == "__main__":
    main()
