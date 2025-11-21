#!/usr/bin/env python3
"""
Interactive Minecraft NBT Player Data Tool
"""

import sys
import json
from pathlib import Path

# Import the library
sys.path.insert(0, str(Path(__file__).parent))
import nbt_lib as nbt


def clear_screen():
    """Clear the terminal screen"""
    print("\033[2J\033[H", end='')


def print_header(title):
    """Print a formatted header"""
    width = 60
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width + "\n")


def select_player():
    """Interactive player selection"""
    players = nbt.list_players()
    
    if not players:
        print("No player data found!")
        return None
    
    print_header("SELECT PLAYER")
    
    for i, (name, uuid, _) in enumerate(players, 1):
        print(f"  {i}. {name:20s} ({uuid})")
    
    print(f"\n  0. Exit")
    
    while True:
        try:
            choice = input("\nSelection: ").strip()
            if not choice:
                continue
            
            choice = int(choice)
            if choice == 0:
                return None
            if 1 <= choice <= len(players):
                return players[choice - 1][1]  # Return UUID
            
            print("Invalid selection!")
        except ValueError:
            print("Please enter a number!")
        except KeyboardInterrupt:
            return None


def display_main_stats(data, player_name):
    """Display main player statistics"""
    clear_screen()
    print_header(f"PLAYER: {player_name}")
    
    print("MAIN STATS:")
    print("-" * 60)
    
    if 'Health' in data:
        print(f"  Health:          {data['Health']:.1f} / 20.0")
    if 'foodLevel' in data:
        print(f"  foodLevel:       {data['foodLevel']} / 20")
    if 'XpLevel' in data:
        print(f"  XpLevel:         {data['XpLevel']}")
    if 'Pos' in data:
        pos = data['Pos']
        print(f"  Pos:             X={pos[0]:.1f}, Y={pos[1]:.1f}, Z={pos[2]:.1f}")
    if 'Dimension' in data:
        print(f"  Dimension:       {data['Dimension']}")
    if 'playerGameType' in data:
        modes = {0: 'Survival', 1: 'Creative', 2: 'Adventure', 3: 'Spectator'}
        mode = modes.get(data['playerGameType'], 'Unknown')
        print(f"  playerGameType:  {mode}")
    
    print("\n" + "=" * 60)
    print("\nActions: [r]ead field  [w]rite field  [b]ack")
    
    return input("\n> ").strip().lower()


def display_secondary_stats(data, player_name):
    """Display secondary/extra statistics"""
    clear_screen()
    print_header(f"PLAYER: {player_name}")
    
    print("SECONDARY STATS:")
    print("-" * 60)
    
    if 'AbsorptionAmount' in data:
        print(f"  AbsorptionAmount:      {data['AbsorptionAmount']:.1f}")
    if 'foodSaturationLevel' in data:
        print(f"  foodSaturationLevel:   {data['foodSaturationLevel']:.1f}")
    if 'Rotation' in data:
        rot = data['Rotation']
        print(f"  Rotation:              Yaw={rot[0]:.1f}°, Pitch={rot[1]:.1f}°")
    if 'Score' in data:
        print(f"  Score:                 {data['Score']}")
    if 'SelectedItemSlot' in data:
        print(f"  SelectedItemSlot:      {data['SelectedItemSlot']}")
    
    print("\n" + "=" * 60)
    print("\nActions: [r]ead field  [w]rite field  [b]ack")
    
    return input("\n> ").strip().lower()


def display_inventory(data, player_name):
    """Display player inventory"""
    clear_screen()
    print_header(f"PLAYER: {player_name}")
    
    inventory = data.get('Inventory', [])
    
    print("INVENTORY:")
    print("-" * 60)
    
    if not inventory:
        print("  (empty)")
    else:
        print(f"  Total items: {len(inventory)}\n")
        
        for i, item in enumerate(inventory[:15]):  # Show first 15
            slot = item.get('Slot', -1)
            item_id = item.get('id', 'unknown').replace('minecraft:', '')
            count = item.get('count', 1)
            
            print(f"  [{slot:2d}] {count:2d}x {item_id}")
            
            if 'components' in item:
                comps = item['components']
                if 'minecraft:custom_name' in comps:
                    print(f"       └─ Custom name")
                if 'minecraft:enchantments' in comps:
                    print(f"       └─ Enchanted")
                if 'minecraft:food' in comps:
                    print(f"       └─ Food component")
        
        if len(inventory) > 15:
            print(f"\n  ... and {len(inventory) - 15} more items")
    
    print("\n" + "=" * 60)
    print("\nActions: [r]ead item  [g]ive item  [c]lear all  [b]ack")
    
    return input("\n> ").strip().lower()


def display_enderchest(data, player_name):
    """Display player ender chest"""
    clear_screen()
    print_header(f"PLAYER: {player_name}")
    
    enderchest = data.get('EnderItems', [])
    
    print("ENDER CHEST:")
    print("-" * 60)
    
    if not enderchest:
        print("  (empty)")
    else:
        print(f"  Total items: {len(enderchest)}\n")
        
        for i, item in enumerate(enderchest[:15]):
            slot = item.get('Slot', -1)
            item_id = item.get('id', 'unknown').replace('minecraft:', '')
            count = item.get('count', 1)
            
            print(f"  [{slot:2d}] {count:2d}x {item_id}")
            
            if 'components' in item:
                comps = item['components']
                if 'minecraft:custom_name' in comps:
                    print(f"       └─ Custom name")
                if 'minecraft:enchantments' in comps:
                    print(f"       └─ Enchanted")
        
        if len(enderchest) > 15:
            print(f"\n  ... and {len(enderchest) - 15} more items")
    
    print("\n" + "=" * 60)
    print("\nActions: [r]ead item  [g]ive item  [c]lear all  [b]ack")
    
    return input("\n> ").strip().lower()


def display_attributes(data, player_name):
    """Display player attributes"""
    clear_screen()
    print_header(f"PLAYER: {player_name}")
    
    attributes = data.get('attributes', [])
    
    print("ATTRIBUTES:")
    print("-" * 60)
    
    if not attributes:
        print("  No custom attributes found")
    else:
        for attr in attributes[:10]:  # Show first 10
            # Handle both old and new attribute formats
            if isinstance(attr, dict):
                name = attr.get('Name', attr.get('id', 'unknown'))
                base = attr.get('Base', attr.get('base', 0))
            else:
                name = 'unknown'
                base = 0
            
            # Clean up the name
            name = str(name).replace('minecraft:', '')
            
            print(f"  {name}: {base}")
            
            # Show modifiers if present
            if isinstance(attr, dict) and 'Modifiers' in attr:
                mods = attr['Modifiers']
                if mods and len(mods) > 0:
                    for mod in mods[:2]:  # First 2 modifiers
                        mod_name = mod.get('Name', mod.get('name', 'modifier'))
                        amount = mod.get('Amount', mod.get('amount', 0))
                        print(f"    └─ {mod_name}: {amount}")
        
        if len(attributes) > 10:
            print(f"\n  ... and {len(attributes) - 10} more attributes")
    
    print("\n" + "=" * 60)
    print("\nActions: [r]ead full data  [b]ack")
    
    return input("\n> ").strip().lower()


def display_recipes(data, player_name):
    """Display player recipes"""
    clear_screen()
    print_header(f"PLAYER: {player_name}")
    
    recipes = data.get('recipeBook', {}).get('recipes', [])
    to_be_displayed = data.get('recipeBook', {}).get('toBeDisplayed', [])
    
    print("RECIPES:")
    print("-" * 60)
    
    if not recipes:
        print("  No recipes unlocked")
    else:
        print(f"  Unlocked recipes:  {len(recipes)}")
        print(f"  To be displayed:   {len(to_be_displayed)}\n")
        
        for i, recipe in enumerate(recipes[:15]):
            recipe_name = str(recipe).replace('minecraft:', '')
            print(f"  {recipe_name}")
        
        if len(recipes) > 15:
            print(f"\n  ... and {len(recipes) - 15} more recipes")
    
    print("\n" + "=" * 60)
    print("\nActions: [r]ead full data  [b]ack")
    
    return input("\n> ").strip().lower()


def display_abilities(data, player_name):
    """Display player abilities"""
    clear_screen()
    print_header(f"PLAYER: {player_name}")
    
    abilities = data.get('abilities', {})
    
    print("ABILITIES:")
    print("-" * 60)
    
    if not abilities:
        print("  No abilities data")
    else:
        for key, value in abilities.items():
            if isinstance(value, bool):
                value_display = "✓" if value else "✗"
            else:
                value_display = str(value)
            print(f"  {key:30s} {value_display}")
    
    print("\n" + "=" * 60)
    print("\nActions: [r]ead field  [w]rite field  [b]ack")
    
    return input("\n> ").strip().lower()


def display_other(data, player_name):
    """Display all other data"""
    clear_screen()
    print_header(f"PLAYER: {player_name}")
    
    # Skip the major categories
    skip_keys = {'Health', 'foodLevel', 'XpLevel', 'Pos', 'Dimension', 'playerGameType',
                 'AbsorptionAmount', 'foodSaturationLevel', 'Rotation', 'Score', 'SelectedItemSlot',
                 'Inventory', 'EnderItems', 'attributes', 'recipeBook', 'abilities'}
    
    other_keys = [k for k in data.keys() if k not in skip_keys]
    
    print("OTHER DATA:")
    print("-" * 60)
    
    if not other_keys:
        print("  No other data")
    else:
        for key in other_keys[:20]:  # Show first 20 fields
            print(f"  {key}")
        
        if len(other_keys) > 20:
            print(f"\n  ... and {len(other_keys) - 20} more fields")
    
    print("\n" + "=" * 60)
    print("\nActions: [r]ead field  [w]rite field  [b]ack")
    
    return input("\n> ").strip().lower()


def handle_read(data):
    """Handle reading a specific field"""
    field = input("\nField name: ").strip()
    
    if field in data:
        print(f"\n{field}:")
        print("─" * 60)
        for line in nbt.format_value(field, data[field]):
            print(line)
    else:
        print(f"\n✗ Field '{field}' not found!")
        print("\nAvailable fields:")
        for key in sorted(data.keys())[:20]:
            print(f"  • {key}")
    
    input("\nPress Enter to continue...")


def handle_write(data, dat_file):
    """Handle writing a field"""
    field = input("\nEnter field name: ").strip()
    
    if field not in data:
        print(f"\nField '{field}' not found!")
        input("\nPress Enter to continue...")
        return
    
    old_value = data[field]
    print(f"\nCurrent value: {old_value}")
    print(f"Type: {type(old_value).__name__}")
    
    new_value_str = input("\nEnter new value: ").strip()
    
    try:
        if isinstance(old_value, int):
            new_value = int(new_value_str)
        elif isinstance(old_value, float):
            new_value = float(new_value_str)
        elif isinstance(old_value, str):
            new_value = new_value_str
        else:
            print(f"\nCannot edit field of type {type(old_value).__name__}")
            input("\nPress Enter to continue...")
            return
        
        data[field] = new_value
        backup = nbt.save_player_data(data, dat_file)
        
        print(f"\n✓ Updated {field}: {old_value} → {new_value}")
        print(f"✓ Backup: {backup}")
    except ValueError as e:
        print(f"\nError: {e}")
    
    input("\nPress Enter to continue...")


def handle_give_item(data, dat_file, is_enderchest=False):
    """Handle giving an item using /give command format"""
    print("\n" + "=" * 60)
    print("  GIVE ITEM")
    print("=" * 60)
    print("\nEnter /give command or item spec:")
    print("Example: diamond_sword[custom_name='\"Magic Sword\"']")
    
    give_cmd = input("\n> ").strip()
    
    if not give_cmd:
        return
    
    try:
        item_id, count, components = nbt.parse_give_command(give_cmd)
        
        print(f"\n✓ Parsed:")
        print(f"  ID: {item_id}")
        print(f"  Count: {count}")
        if components:
            comp_list = list(components.keys())
            print(f"  Components: {', '.join(c.replace('minecraft:', '') for c in comp_list[:5])}")
            if len(comp_list) > 5:
                print(f"              ... and {len(comp_list) - 5} more")
        
        confirm = input("\nAdd this item? (y/n): ").strip().lower()
        if confirm != 'y':
            return
        
        # Create item
        item = {
            'id': item_id,
            'count': count
        }
        
        if components:
            item['components'] = components
        
        # Find empty slot
        inv_key = 'EnderItems' if is_enderchest else 'Inventory'
        inventory = data.get(inv_key, [])
        used_slots = {item.get('Slot', -1) for item in inventory}
        
        max_slot = 27 if is_enderchest else 36
        empty_slot = None
        for slot in range(max_slot):
            if slot not in used_slots:
                empty_slot = slot
                break
        
        if empty_slot is None:
            print(f"\n✗ Error: {'Ender chest' if is_enderchest else 'Inventory'} is full!")
            input("\nPress Enter to continue...")
            return
        
        item['Slot'] = empty_slot
        inventory.append(item)
        data[inv_key] = inventory
        
        backup = nbt.save_player_data(data, dat_file)
        
        print(f"\n✓ Gave {count}x {item_id} (slot {empty_slot})")
        print(f"✓ Backup: {backup.name}")
        
    except Exception as e:
        print(f"\n✗ Error parsing command: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to continue...")


def handle_clear_inventory(data, dat_file):
    """Clear player inventory"""
    confirm = input("\nAre you sure you want to clear inventory? (yes/no): ").strip().lower()
    if confirm == 'yes':
        data['Inventory'] = []
        backup = nbt.save_player_data(data, dat_file)
        print(f"\n✓ Inventory cleared")
        print(f"✓ Backup: {backup}")
        input("\nPress Enter to continue...")


def handle_clear_enderchest(data, dat_file):
    """Clear player ender chest"""
    confirm = input("\nAre you sure you want to clear ender chest? (yes/no): ").strip().lower()
    if confirm == 'yes':
        data['EnderItems'] = []
        backup = nbt.save_player_data(data, dat_file)
        print(f"\n✓ Ender chest cleared")
        print(f"✓ Backup: {backup}")
        input("\nPress Enter to continue...")


def player_menu(uuid):
    """Main menu for a selected player"""
    while True:
        # Reload data each time to show updates
        data, dat_file, player_name = nbt.load_player_data(uuid)
        
        if data is None:
            print("✗ Error loading player data!")
            return
        
        clear_screen()
        print_header(f"SELECTED: {player_name}")
        
        print("SECTIONS:")
        print("-" * 60)
        print("  1. Main Stats")
        print("  2. Secondary Stats")
        print("  3. Inventory")
        print("  4. Ender Chest")
        print("  5. Attributes")
        print("  6. Recipes")
        print("  7. Abilities")
        print("  8. Other Data")
        print("\n  0. Back to player selection")
        print("-" * 60)
        
        try:
            choice = input("\n> ").strip()
            
            if choice == '0':
                return
            elif choice == '1':
                action = display_main_stats(data, player_name)
                if action == 'r':
                    handle_read(data)
                elif action == 'w':
                    handle_write(data, dat_file)
            elif choice == '2':
                action = display_secondary_stats(data, player_name)
                if action == 'r':
                    handle_read(data)
                elif action == 'w':
                    handle_write(data, dat_file)
            elif choice == '3':
                action = display_inventory(data, player_name)
                if action == 'r':
                    handle_read(data)
                elif action == 'g':
                    handle_give_item(data, dat_file, is_enderchest=False)
                elif action == 'c':
                    handle_clear_inventory(data, dat_file)
            elif choice == '4':
                action = display_enderchest(data, player_name)
                if action == 'r':
                    handle_read(data)
                elif action == 'g':
                    handle_give_item(data, dat_file, is_enderchest=True)
                elif action == 'c':
                    handle_clear_enderchest(data, dat_file)
            elif choice == '5':
                action = display_attributes(data, player_name)
                if action == 'r':
                    handle_read(data)
            elif choice == '6':
                action = display_recipes(data, player_name)
                if action == 'r':
                    handle_read(data)
            elif choice == '7':
                action = display_abilities(data, player_name)
                if action == 'r':
                    handle_read(data)
                elif action == 'w':
                    handle_write(data, dat_file)
            elif choice == '8':
                action = display_other(data, player_name)
                if action == 'r':
                    handle_read(data)
                elif action == 'w':
                    handle_write(data, dat_file)
        
        except KeyboardInterrupt:
            return


def main():
    """Main application loop"""
    try:
        while True:
            uuid = select_player()
            if uuid is None:
                print("\nGoodbye!")
                break
            
            player_menu(uuid)
    
    except KeyboardInterrupt:
        print("\n\nGoodbye!")


if __name__ == '__main__':
    main()
