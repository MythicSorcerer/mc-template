#!/usr/bin/env python3
"""
mcplayer.py — advanced Minecraft playerdata editor using nbtlib
Features:
 - Select players by username (usercache.json)
 - Hierarchical menus (Basics, Inventory, Ender Chest, Attributes, Pos/Rotation, Armor/Offhand)
 - Auto-find next free slot
 - Item ID autocomplete (readline-based)
 - Armor/offhand editing
 - Teleport editing with checks
 - Save undo history (.undoN)
 - Pretty-print NBT
 - Copy inventory from another player
 - Safe backups (.bak)
Requires: nbtlib
"""

import os
import sys
import json
import shutil
import time
import readline
import glob
import copy
import nbtlib
from nbtlib import Compound, List, String, Int, Byte, Double, Float

# ========== CONFIG ==========
SERVER_ROOT = "/opt/minecraft/server/world"   # updated per your request
PLAYERDATA = os.path.join(SERVER_ROOT, "playerdata")
# USERCACHE = os.path.join(SERVER_ROOT, "usercache.json")
USERCACHE = "/opt/minecraft/server/usercache.json" # Hard coded for now
UNDO_LIMIT = 10   # keep up to .undo1..undo10

# Quick list of common item ids for autocomplete (extend as you like)
COMMON_ITEM_IDS = [
    "minecraft:stone", "minecraft:cobblestone", "minecraft:oak_log", "minecraft:oak_planks",
    "minecraft:stick", "minecraft:stone_axe", "minecraft:iron_pickaxe", "minecraft:iron_axe",
    "minecraft:diamond", "minecraft:diamond_block", "minecraft:diamond_sword", "minecraft:elytra",
    "minecraft:iron_ingot", "minecraft:gold_ingot", "minecraft:apple", "minecraft:bread",
    "minecraft:torch", "minecraft:water_bucket", "minecraft:lava_bucket"
]

# ========== Utilities ==========
def load_usercache():
    """Return mapping uuid -> name from usercache.json (if it exists)."""
    if not os.path.exists(USERCACHE):
        return {}
    try:
        with open(USERCACHE, "r") as f:
            data = json.load(f)
            return {entry.get("uuid"): entry.get("name") for entry in data if "uuid" in entry}
    except Exception:
        return {}

def safe_root(nbt):
    """
    Accept an nbtlib File or Compound and return the player compound (the correct top-level).
    Handles both old 'Data' wrapper and 1.20+ bare player compound.
    """
    # nbt may be a File object or a Compound
    root = getattr(nbt, "root", nbt)
    if isinstance(root, dict) and "Data" in root:
        return root["Data"]
    return root

def list_player_files():
    if not os.path.isdir(PLAYERDATA):
        print(f"Playerdata folder not found at {PLAYERDATA}")
        sys.exit(1)
    return sorted([p for p in os.listdir(PLAYERDATA) if p.endswith(".dat")])

def backup_file(path):
    bak = path + ".bak"
    shutil.copy2(path, bak)
    # keep only one .bak; additional undos are separate
    return bak

def push_undo(path):
    """
    Create a rotating undo file: path.undo1, path.undo2, ...
    Keeps up to UNDO_LIMIT files. Newest at .undo1
    """
    for i in range(UNDO_LIMIT, 1, -1):
        prev = f"{path}.undo{i-1}"
        cur = f"{path}.undo{i}"
        if os.path.exists(prev):
            shutil.move(prev, cur)
    # copy current snapshot to .undo1
    if os.path.exists(path):
        shutil.copy2(path, f"{path}.undo1")

def pretty_print_nbt(tag, indent=0):
    """
    Simple pretty printer for NBT compounds/lists to make tree debugging easier.
    Not guaranteed to cover all tag types in special formatting but useful.
    """
    pad = "  " * indent
    if isinstance(tag, dict) or isinstance(tag, nbtlib.tag.Compound):
        for k, v in tag.items():
            print(f"{pad}{k}: ({type(v).__name__})", end="")
            # Show short values inline
            if isinstance(v, (str, int, float, bool)) or (hasattr(v, "unpack") and not isinstance(v, (list, nbtlib.tag.Compound))):
                try:
                    print(f" = {v}")
                except Exception:
                    print()
            else:
                print()
                pretty_print_nbt(v, indent + 1)
    elif isinstance(tag, (list, nbtlib.tag.List)):
        for i, item in enumerate(tag):
            print(f"{pad}[{i}] ({type(item).__name__})")
            pretty_print_nbt(item, indent + 1)
    else:
        print(f"{pad}{repr(tag)}")

def read_nbt(path):
    return nbtlib.load(path)

def save_nbt(nbt_file, path):
    # rotate undo and make a .bak for immediate safety
    push_undo(path)
    backup_file(path)
    nbt_file.save(path)

def find_next_free_slot(inv):
    """
    Inventory slots:
      0-8 hotbar
      9-35 main inventory
      36-39 armor (boots->helmet)
      40 offhand
    We'll find first free in 0..35 (hotbar+main) by default.
    """
    occupied = set()
    for item in inv:
        try:
            s = int(item.get("Slot", -1))
            occupied.add(s)
        except Exception:
            continue
    for s in range(0, 36):
        if s not in occupied:
            return s
    return None

# ========== Readline completer for item IDs ==========
def item_id_completer(text, state):
    options = [i for i in COMMON_ITEM_IDS if i.startswith(text)]
    if state < len(options):
        return options[state]
    return None

def setup_readline_itemid():
    readline.set_completer_delims(' \t\n;')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(item_id_completer)

# ========== High-level actions ==========
def pick_player_by_name(players):
    """
    players: list of tuples (name, uuid, path)
    """
    print("\nPlayers:")
    for i, (name, uuid, _) in enumerate(players):
        print(f"{i+1}. {name} ({uuid})")
    while True:
        try:
            sel = input("Select player by number or name (q to quit): ").strip()
            if sel.lower() == "q":
                return None
            if sel.isdigit():
                idx = int(sel) - 1
                if 0 <= idx < len(players):
                    return players[idx]
                else:
                    print("Index out of range.")
            else:
                # match by name case-insensitive
                matches = [p for p in players if p[0].lower() == sel.lower()]
                if len(matches) == 1:
                    return matches[0]
                elif len(matches) > 1:
                    print("Multiple matches, pick by number:")
                    for i, (name, uuid, _) in enumerate(matches):
                        print(f"  {i+1}. {name} ({uuid})")
                else:
                    print("No exact name match. Try number or exact username.")
        except KeyboardInterrupt:
            print()
            return None

def list_players():
    usercache = load_usercache()
    files = list_player_files()
    out = []
    for f in files:
        uuid = f[:-4]
        name = usercache.get(uuid, uuid)
        out.append((name, uuid, os.path.join(PLAYERDATA, f)))
    return out

# ========== Menus ==========
def main_menu():
    players = list_players()
    if not players:
        print("No players found.")
        return
    sel = pick_player_by_name(players)
    if sel is None:
        return
    name, uuid, path = sel
    print(f"\nSelected: {name} ({uuid})\nLoading...")
    nbt_file = read_nbt(path)
    root = safe_root(nbt_file)

    run_player_menu(name, uuid, path, nbt_file, root)

def run_player_menu(name, uuid, path, nbt_file, root):
    setup_readline_itemid()
    while True:
        print(f"\n=== Player: {name} ({uuid}) ===")
        print("1. Basics")
        print("2. Inventory")
        print("3. Ender Chest")
        print("4. Armor / Offhand")
        print("5. Attributes")
        print("6. Position / Rotation")
        print("7. Pretty-print raw NBT")
        print("8. Copy inventory from another player")
        print("9. Save & Exit")
        print("0. Exit without saving")
        choice = input("> ").strip()
        if choice == "1":
            basics_menu(root)
        elif choice == "2":
            inventory_menu(root)
        elif choice == "3":
            ender_menu(root)
        elif choice == "4":
            armor_offhand_menu(root)
        elif choice == "5":
            attributes_menu(root)
        elif choice == "6":
            pos_rotation_menu(root)
        elif choice == "7":
            print("\n--- Pretty NBT ---")
            pretty_print_nbt(root)
        elif choice == "8":
            copy_inventory_from_another(root)
        elif choice == "9":
            save_nbt(nbt_file, path)
            print("Saved and created backups (.bak and .undo1).")
            break
        elif choice == "0":
            print("Exiting without saving.")
            break
        else:
            print("Invalid choice.")

# ----- Basics -----
def basics_menu(root):
    while True:
        print("\n-- Basics --")
        print("1. Show basic fields")
        print("2. Set field (Health, foodLevel, XpLevel, playerGameType, etc)")
        print("0. Back")
        c = input("> ").strip()
        if c == "1":
            for k in ["Name", "LastKnownName", "Health", "foodLevel", "XpLevel", "XpTotal", "playerGameType", "Dimension"]:
                if k in root:
                    print(f"{k}: {root[k]}")
        elif c == "2":
            key = input("Field name: ").strip()
            val = input("New value: ").strip()
            # attempt reasonable typing
            if val.isdigit():
                root[key] = Int(int(val))
            else:
                try:
                    fv = float(val)
                    root[key] = Float(fv)
                except Exception:
                    root[key] = String(val)
            print("Updated.")
        elif c == "0":
            return
        else:
            print("Invalid.")

# ----- Inventory -----
def inventory_menu(root):
    inv = root.setdefault("Inventory", List[Compound]())
    while True:
        print("\n-- Inventory --")
        print("1. Show inventory")
        print("2. Add item (auto-slot or specific slot)")
        print("3. Remove item by slot")
        print("4. Auto-find next free slot")
        print("0. Back")
        c = input("> ").strip()
        if c == "1":
            show_inventory(inv)
        elif c == "2":
            add_item_to_list(inv)
        elif c == "3":
            remove_item_from_list(inv)
        elif c == "4":
            s = find_next_free_slot(inv)
            if s is None:
                print("No free slots available in 0-35.")
            else:
                print(f"Next free slot is {s}")
        elif c == "0":
            return
        else:
            print("Invalid.")

def show_inventory(inv):
    if not inv:
        print("(empty)")
        return
    for it in inv:
        slot = int(it.get("Slot", -1))
        iid = it.get("id", "unknown")
        cnt = int(it.get("count", 1))
        print(f"Slot {slot:2d}: {iid} x{cnt}")

def add_item_to_list(inv):
    # autocompletion active
    slot_input = input("Slot (leave blank for auto): ").strip()
    if slot_input == "":
        slot = find_next_free_slot(inv)
        if slot is None:
            print("No free slot found (0-35). Aborting.")
            return
        print(f"Using slot {slot}")
    else:
        slot = int(slot_input)
    item_id = input("Item ID (TAB completes common ids): ").strip()
    if item_id == "":
        print("No item id provided.")
        return
    count = input("Count (default 1): ").strip()
    count = int(count) if count.isdigit() else 1

    # remove existing at slot
    for e in list(inv):
        if int(e.get("Slot", -1)) == slot:
            inv.remove(e)

    inv.append(Compound({
        "Slot": Byte(slot),
        "id": String(item_id),
        "count": Int(count)
    }))
    print("Added.")

def remove_item_from_list(inv):
    s = input("Slot to remove: ").strip()
    if not s.isdigit():
        print("Invalid.")
        return
    slot = int(s)
    before = len(inv)
    inv[:] = [it for it in inv if int(it.get("Slot", -1)) != slot]
    if len(inv) < before:
        print("Removed.")
    else:
        print("No item in that slot.")

# ----- Ender Chest -----
def ender_menu(root):
    ender = root.setdefault("EnderItems", List[Compound]())
    while True:
        print("\n-- Ender Chest --")
        print("1. Show ender chest")
        print("2. Add item")
        print("3. Remove item by slot")
        print("0. Back")
        c = input("> ").strip()
        if c == "1":
            show_inventory(ender)
        elif c == "2":
            add_item_to_list(ender)
        elif c == "3":
            remove_item_from_list(ender)
        elif c == "0":
            return
        else:
            print("Invalid.")

# ----- Armor / Offhand -----
def armor_offhand_menu(root):
    inv = root.setdefault("Inventory", List[Compound]())
    while True:
        print("\n-- Armor / Offhand --")
        print("1. Show armor/offhand (by special slots)")
        print("2. Set armor item (boots/legs/chest/helmet)")
        print("3. Set offhand item")
        print("4. Remove armor/offhand item")
        print("0. Back")
        c = input("> ").strip()
        if c == "1":
            # armor expected in slots 36-39 (boots->helmet), offhand 40
            armor_items = [it for it in inv if 36 <= int(it.get("Slot", -1)) <= 39]
            offhand = [it for it in inv if int(it.get("Slot", -1)) == 40]
            print("Armor:")
            if not armor_items:
                print(" (none)")
            for it in armor_items:
                print(f" Slot {int(it['Slot'])}: {it.get('id')} x{int(it.get('count',1))}")
            print("Offhand:")
            if offhand:
                it = offhand[0]
                print(f" Slot {int(it['Slot'])}: {it.get('id')} x{int(it.get('count',1))}")
            else:
                print(" (none)")
        elif c == "2":
            which = input("Which armor (boots/legs/chest/helmet): ").strip().lower()
            mapping = {"boots":36, "legs":37, "chest":38, "helmet":39}
            if which not in mapping:
                print("Invalid choice.")
                continue
            slot = mapping[which]
            item_id = input("Item ID for armor: ").strip()
            count = input("Count (default 1): ").strip()
            count = int(count) if count.isdigit() else 1
            # remove any existing in slot
            inv[:] = [it for it in inv if int(it.get("Slot",-1)) != slot]
            inv.append(Compound({"Slot": Byte(slot), "id": String(item_id), "count": Int(count)}))
            print("Set.")
        elif c == "3":
            slot = 40
            item_id = input("Offhand item ID: ").strip()
            count = input("Count (default 1): ").strip()
            count = int(count) if count.isdigit() else 1
            inv[:] = [it for it in inv if int(it.get("Slot",-1)) != slot]
            inv.append(Compound({"Slot": Byte(slot), "id": String(item_id), "count": Int(count)}))
            print("Offhand set.")
        elif c == "4":
            what = input("Remove (armor/offhand/all): ").strip().lower()
            if what == "armor":
                inv[:] = [it for it in inv if not (36 <= int(it.get("Slot",-1)) <= 39)]
                print("Armor cleared.")
            elif what == "offhand":
                inv[:] = [it for it in inv if int(it.get("Slot",-1)) != 40]
                print("Offhand cleared.")
            elif what == "all":
                inv[:] = [it for it in inv if not (36 <= int(it.get("Slot",-1)) <= 40)]
                print("Armor & offhand cleared.")
            else:
                print("Unknown.")
        elif c == "0":
            return
        else:
            print("Invalid.")

# ----- Attributes -----
def attributes_menu(root):
    attr = root.setdefault("attributes", List[Compound]())
    while True:
        print("\n-- Attributes --")
        print("1. List attributes")
        print("2. Add / Set attribute")
        print("3. Remove attribute")
        print("0. Back")
        c = input("> ").strip()
        if c == "1":
            if not attr:
                print("(no attributes)")
            for a in attr:
                print(f"{a.get('id')} = base:{a.get('base')}")
        elif c == "2":
            aid = input("Attribute id (e.g. minecraft:generic.max_health): ").strip()
            base = input("Base value (float): ").strip()
            try:
                basef = float(base)
            except Exception:
                basef = 0.0
            # remove existing same id
            attr[:] = [a for a in attr if a.get("id") != aid]
            attr.append(Compound({"id": String(aid), "base": Double(basef)}))
            print("Set.")
        elif c == "3":
            aid = input("Attribute id to remove: ").strip()
            before = len(attr)
            attr[:] = [a for a in attr if a.get("id") != aid]
            if len(attr) < before:
                print("Removed.")
            else:
                print("Not found.")
        elif c == "0":
            return
        else:
            print("Invalid.")

# ----- Position / Rotation -----
def pos_rotation_menu(root):
    while True:
        print("\n-- Position / Rotation --")
        print("1. Show Pos & Rotation")
        print("2. Teleport (set Pos)")
        print("3. Set Rotation")
        print("0. Back")
        c = input("> ").strip()
        if c == "1":
            pos = root.get("Pos")
            rot = root.get("Rotation")
            print(f"Pos: {pos}")
            print(f"Rotation: {rot}")
        elif c == "2":
            x = input("X (number): ").strip()
            y = input("Y (number): ").strip()
            z = input("Z (number): ").strip()
            try:
                xd = float(x); yd = float(y); zd = float(z)
            except Exception:
                print("Invalid numbers.")
                continue
            # simple safety checks
            if yd < -64 or yd > 320:
                print("Warning: Y coordinate out of common range (-64..320). Continue? (y/N)")
                if input("> ").lower() != "y":
                    print("Cancelled.")
                    continue
            root["Pos"] = List[Double]([Double(xd), Double(yd), Double(zd)])
            print("Teleported (NBT updated).")
        elif c == "3":
            yaw = input("Yaw (e.g. 0.0): ").strip()
            pitch = input("Pitch (e.g. 0.0): ").strip()
            try:
                yawf = float(yaw); pitchf = float(pitch)
            except Exception:
                print("Invalid.")
                continue
            root["Rotation"] = List[Float]([Float(yawf), Float(pitchf)])
            print("Rotation set.")
        elif c == "0":
            return
        else:
            print("Invalid.")

# ----- Copy inventory -----
def copy_inventory_from_another(root):
    players = list_players()
    if len(players) < 2:
        print("No other players to copy from.")
        return
    print("Pick source player:")
    for i, (n, u, _) in enumerate(players):
        print(f"{i+1}. {n} ({u})")
    s = input("Source number: ").strip()
    if not s.isdigit():
        print("Invalid.")
        return
    idx = int(s) - 1
    if not (0 <= idx < len(players)):
        print("Invalid.")
        return
    _, _, path = players[idx]
    src_nbt = read_nbt(path)
    src_root = safe_root(src_nbt)
    src_inv = copy.deepcopy(src_root.get("Inventory", List[Compound]()))
    if not src_inv:
        print("Source inventory empty.")
        return
    # optional confirmation
    print(f"Copying {len(src_inv)} items into current player's inventory. This will replace their Inventory. Proceed? (y/N)")
    if input("> ").lower() != "y":
        print("Cancelled.")
        return
    root["Inventory"] = src_inv
    print("Inventory copied.")

# ========== STARTUP ==========
def ensure_readiness():
    if not os.path.isdir(PLAYERDATA):
        print(f"Playerdata folder not found: {PLAYERDATA}")
        sys.exit(1)

def main():
    ensure_readiness()
    # set up readline completer for item IDs
    readline.set_completer(item_id_completer)
    readline.parse_and_bind("tab: complete")

    print("mcplayer.py — advanced player editor")
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nInterrupted, exiting.")

if __name__ == "__main__":
    main()

