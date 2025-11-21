#!/usr/bin/env python3
"""
Minecraft NBT Library
Core functions for reading and writing Minecraft player NBT data
"""

import os
import sys
import json
import struct
import gzip
from pathlib import Path

# Paths (absolute from /opt/minecraft)
MINECRAFT_DIR = Path("/opt/minecraft")
USERCACHE_PATH = MINECRAFT_DIR / "server/usercache.json"
PLAYERDATA_DIR = MINECRAFT_DIR / "server/world/playerdata"


class NBTReader:
    """Simple NBT parser for Minecraft player data"""
    
    TAG_End = 0
    TAG_Byte = 1
    TAG_Short = 2
    TAG_Int = 3
    TAG_Long = 4
    TAG_Float = 5
    TAG_Double = 6
    TAG_Byte_Array = 7
    TAG_String = 8
    TAG_List = 9
    TAG_Compound = 10
    TAG_Int_Array = 11
    TAG_Long_Array = 12
    
    def __init__(self, data):
        self.data = data
        self.pos = 0
    
    def read_byte(self):
        val = struct.unpack('>b', self.data[self.pos:self.pos+1])[0]
        self.pos += 1
        return val
    
    def read_ubyte(self):
        val = struct.unpack('>B', self.data[self.pos:self.pos+1])[0]
        self.pos += 1
        return val
    
    def read_short(self):
        val = struct.unpack('>h', self.data[self.pos:self.pos+2])[0]
        self.pos += 2
        return val
    
    def read_int(self):
        val = struct.unpack('>i', self.data[self.pos:self.pos+4])[0]
        self.pos += 4
        return val
    
    def read_long(self):
        val = struct.unpack('>q', self.data[self.pos:self.pos+8])[0]
        self.pos += 8
        return val
    
    def read_float(self):
        val = struct.unpack('>f', self.data[self.pos:self.pos+4])[0]
        self.pos += 4
        return val
    
    def read_double(self):
        val = struct.unpack('>d', self.data[self.pos:self.pos+8])[0]
        self.pos += 8
        return val
    
    def read_string(self):
        length = self.read_short()
        try:
            val = self.data[self.pos:self.pos+length].decode('utf-8')
        except UnicodeDecodeError:
            # Fallback for invalid UTF-8 - use latin-1 which accepts all bytes
            val = self.data[self.pos:self.pos+length].decode('latin-1')
        self.pos += length
        return val
    
    def read_tag(self, tag_type):
        if tag_type == self.TAG_End:
            return None
        elif tag_type == self.TAG_Byte:
            return self.read_byte()
        elif tag_type == self.TAG_Short:
            return self.read_short()
        elif tag_type == self.TAG_Int:
            return self.read_int()
        elif tag_type == self.TAG_Long:
            return self.read_long()
        elif tag_type == self.TAG_Float:
            return self.read_float()
        elif tag_type == self.TAG_Double:
            return self.read_double()
        elif tag_type == self.TAG_Byte_Array:
            length = self.read_int()
            return [self.read_byte() for _ in range(length)]
        elif tag_type == self.TAG_String:
            return self.read_string()
        elif tag_type == self.TAG_List:
            list_type = self.read_ubyte()
            length = self.read_int()
            return [self.read_tag(list_type) for _ in range(length)]
        elif tag_type == self.TAG_Compound:
            return self.read_compound()
        elif tag_type == self.TAG_Int_Array:
            length = self.read_int()
            return [self.read_int() for _ in range(length)]
        elif tag_type == self.TAG_Long_Array:
            length = self.read_int()
            return [self.read_long() for _ in range(length)]
    
    def read_compound(self):
        compound = {}
        while True:
            tag_type = self.read_ubyte()
            if tag_type == self.TAG_End:
                break
            name = self.read_string()
            compound[name] = self.read_tag(tag_type)
        return compound
    
    def read_root(self):
        tag_type = self.read_ubyte()
        if tag_type != self.TAG_Compound:
            raise ValueError("Root tag must be compound")
        name = self.read_string()
        return self.read_compound()


class NBTWriter:
    """Simple NBT writer for Minecraft player data"""
    
    def __init__(self):
        self.data = bytearray()
    
    def write_byte(self, val):
        self.data.extend(struct.pack('>b', val))
    
    def write_ubyte(self, val):
        self.data.extend(struct.pack('>B', val))
    
    def write_short(self, val):
        self.data.extend(struct.pack('>h', val))
    
    def write_int(self, val):
        self.data.extend(struct.pack('>i', val))
    
    def write_long(self, val):
        self.data.extend(struct.pack('>q', val))
    
    def write_float(self, val):
        self.data.extend(struct.pack('>f', val))
    
    def write_double(self, val):
        self.data.extend(struct.pack('>d', val))
    
    def write_string(self, val):
        encoded = val.encode('utf-8')
        self.write_short(len(encoded))
        self.data.extend(encoded)
    
    def write_tag(self, val):
        if isinstance(val, bool):
            return NBTReader.TAG_Byte, lambda: self.write_byte(1 if val else 0)
        elif isinstance(val, int):
            if -128 <= val <= 127:
                return NBTReader.TAG_Byte, lambda: self.write_byte(val)
            elif -32768 <= val <= 32767:
                return NBTReader.TAG_Short, lambda: self.write_short(val)
            elif -2147483648 <= val <= 2147483647:
                return NBTReader.TAG_Int, lambda: self.write_int(val)
            else:
                return NBTReader.TAG_Long, lambda: self.write_long(val)
        elif isinstance(val, float):
            return NBTReader.TAG_Double, lambda: self.write_double(val)
        elif isinstance(val, str):
            return NBTReader.TAG_String, lambda: self.write_string(val)
        elif isinstance(val, list):
            if len(val) == 0:
                return NBTReader.TAG_List, lambda: (self.write_ubyte(NBTReader.TAG_End), self.write_int(0))
            first_type, _ = self.write_tag(val[0])
            return NBTReader.TAG_List, lambda: self.write_list(val, first_type)
        elif isinstance(val, dict):
            return NBTReader.TAG_Compound, lambda: self.write_compound(val)
        else:
            raise ValueError(f"Unsupported type: {type(val)}")
    
    def write_list(self, lst, item_type):
        self.write_ubyte(item_type)
        self.write_int(len(lst))
        for item in lst:
            _, writer = self.write_tag(item)
            writer()
    
    def write_compound(self, compound):
        for name, val in compound.items():
            tag_type, writer = self.write_tag(val)
            self.write_ubyte(tag_type)
            self.write_string(name)
            writer()
        self.write_ubyte(NBTReader.TAG_End)
    
    def write_root(self, compound, name=""):
        self.write_ubyte(NBTReader.TAG_Compound)
        self.write_string(name)
        self.write_compound(compound)
        return bytes(self.data)


def load_usercache():
    """Load the usercache.json file"""
    try:
        with open(USERCACHE_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def get_player_name(uuid):
    """Get player name from UUID"""
    usercache = load_usercache()
    # Try with and without dashes
    uuid_str = str(uuid).replace('-', '').lower()
    for entry in usercache:
        cache_uuid = entry.get('uuid', '').replace('-', '').lower()
        if cache_uuid == uuid_str:
            return entry.get('name', 'Unknown')
    return 'Unknown'


def get_player_uuid(name):
    """Get UUID from player name (returns with dashes for filename)"""
    usercache = load_usercache()
    for entry in usercache:
        if entry.get('name', '').lower() == name.lower():
            return entry.get('uuid', '').lower()
    return None


def list_players():
    """List all players with data files"""
    if not PLAYERDATA_DIR.exists():
        return []
    
    players = []
    for dat_file in PLAYERDATA_DIR.glob('*.dat'):
        uuid = dat_file.stem
        name = get_player_name(uuid)
        players.append((name, uuid, dat_file))
    
    return sorted(players)


def load_player_data(identifier):
    """Load player data by name or UUID
    
    Returns: (nbt_data, dat_file, player_name) or (None, None, None)
    """
    dat_file = None
    if identifier.endswith('.dat'):
        dat_file = PLAYERDATA_DIR / identifier
    else:
        # Try as UUID (could be with or without dashes)
        dat_file = PLAYERDATA_DIR / f"{identifier}.dat"
        if not dat_file.exists():
            uuid_clean = identifier.replace('-', '').lower()
            dat_file = PLAYERDATA_DIR / f"{uuid_clean}.dat"
        if not dat_file.exists():
            # Try as username - get UUID from usercache
            uuid = get_player_uuid(identifier)
            if uuid:
                dat_file = PLAYERDATA_DIR / f"{uuid}.dat"
    
    if not dat_file or not dat_file.exists():
        return None, None, None
    
    # Read and parse NBT data
    with gzip.open(dat_file, 'rb') as f:
        data = f.read()
    
    reader = NBTReader(data)
    nbt_data = reader.read_root()
    player_name = get_player_name(dat_file.stem)
    
    return nbt_data, dat_file, player_name


def save_player_data(nbt_data, dat_file):
    """Save NBT data back to file with backup"""
    writer = NBTWriter()
    nbt_bytes = writer.write_root(nbt_data)
    
    # Create backup
    backup_file = dat_file.with_suffix('.dat.bak')
    with open(dat_file, 'rb') as f:
        with open(backup_file, 'wb') as b:
            b.write(f.read())
    
    # Write new data
    with gzip.open(dat_file, 'wb') as f:
        f.write(nbt_bytes)
    
    return backup_file


def parse_give_command(give_cmd):
    """Parse a Minecraft /give command and extract item data
    
    Example: give @a diamond_sword[custom_name='{"text":"Sword"}',enchantments={sharpness:5}]
    Returns: (item_id, count, components_dict)
    """
    # Remove 'give' and target selector
    give_cmd = give_cmd.strip()
    if give_cmd.startswith('give'):
        give_cmd = give_cmd[4:].strip()
    
    # Remove target selector (@a, @p, etc.)
    parts = give_cmd.split(None, 1)
    if len(parts) > 1 and parts[0].startswith('@'):
        give_cmd = parts[1]
    elif len(parts) > 1:
        give_cmd = parts[1]
    
    # Extract item ID and NBT
    if '[' in give_cmd:
        item_id, nbt_part = give_cmd.split('[', 1)
        nbt_part = '[' + nbt_part
    else:
        # Check for count
        parts = give_cmd.split()
        item_id = parts[0]
        count = int(parts[1]) if len(parts) > 1 else 1
        return item_id, count, {}
    
    item_id = item_id.strip()
    if ':' not in item_id:
        item_id = f'minecraft:{item_id}'
    
    # Parse count if present (after the closing bracket)
    count = 1
    if nbt_part.count('[') == nbt_part.count(']'):
        closing = nbt_part.rfind(']')
        remainder = nbt_part[closing+1:].strip()
        if remainder.isdigit():
            count = int(remainder)
            nbt_part = nbt_part[:closing+1]
    
    # Parse NBT components
    components = parse_nbt_components(nbt_part[1:-1])  # Remove [ ]
    
    return item_id, count, components


def parse_nbt_components(nbt_str):
    """Parse NBT component string into Python dict
    
    Handles formats like:
    custom_name='{"text":"Name"}',enchantments={sharpness:5},food={nutrition:20}
    """
    components = {}
    nbt_str = nbt_str.strip()
    
    if not nbt_str:
        return components
    
    # Split by commas, but respect nested structures
    parts = []
    current = []
    depth = 0
    in_string = False
    escape = False
    string_char = None
    
    for i, char in enumerate(nbt_str):
        if escape:
            current.append(char)
            escape = False
            continue
        
        if char == '\\':
            escape = True
            current.append(char)
            continue
        
        if char in '"\'':
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None
            current.append(char)
        elif not in_string:
            if char in '{[':
                depth += 1
                current.append(char)
            elif char in '}]':
                depth -= 1
                current.append(char)
            elif char == ',' and depth == 0:
                parts.append(''.join(current).strip())
                current = []
            else:
                current.append(char)
        else:
            current.append(char)
    
    if current:
        parts.append(''.join(current).strip())
    
    # Parse each component
    for part in parts:
        if '=' in part:
            key, value = part.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # Convert to minecraft: namespaced key
            if ':' not in key and key not in ['unbreakable', 'damage']:
                key = f'minecraft:{key}'
            
            # Parse the value
            components[key] = parse_nbt_value(value)
    
    return components


def parse_nbt_value(value):
    """Parse a single NBT value"""
    value = value.strip()
    
    # JSON string (between quotes or apostrophes)
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        json_str = value[1:-1]
        # Handle escaped quotes
        json_str = json_str.replace("\\'", "'").replace('\\"', '"')
        try:
            return json.loads(json_str)
        except:
            return json_str
    
    # Boolean
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    
    # Number
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except:
        pass
    
    # Compound (object)
    if value.startswith('{') and value.endswith('}'):
        return parse_nbt_compound(value[1:-1])
    
    # List/Array
    if value.startswith('[') and value.endswith(']'):
        return parse_nbt_list(value[1:-1])
    
    # Plain string
    return value


def parse_nbt_compound(content):
    """Parse NBT compound/object"""
    result = {}
    content = content.strip()
    
    if not content:
        return result
    
    # Split by commas respecting nesting
    parts = []
    current = []
    depth = 0
    in_string = False
    
    for char in content:
        if char in '"\'':
            in_string = not in_string
        elif not in_string:
            if char in '{[':
                depth += 1
            elif char in '}]':
                depth -= 1
            elif char == ',' and depth == 0:
                parts.append(''.join(current).strip())
                current = []
                continue
        current.append(char)
    
    if current:
        parts.append(''.join(current).strip())
    
    for part in parts:
        if ':' in part:
            key, value = part.split(':', 1)
            key = key.strip().strip('"\'')
            result[key] = parse_nbt_value(value.strip())
    
    return result


def parse_nbt_list(content):
    """Parse NBT list/array"""
    content = content.strip()
    
    if not content:
        return []
    
    # Split by commas respecting nesting
    parts = []
    current = []
    depth = 0
    in_string = False
    
    for char in content:
        if char in '"\'':
            in_string = not in_string
        elif not in_string:
            if char in '{[':
                depth += 1
            elif char in '}]':
                depth -= 1
            elif char == ',' and depth == 0:
                parts.append(''.join(current).strip())
                current = []
                continue
        current.append(char)
    
    if current:
        parts.append(''.join(current).strip())
    
    return [parse_nbt_value(part) for part in parts]


def format_value(key, value, indent=0):
    """Format a value for human-readable display"""
    prefix = "  " * indent
    
    if isinstance(value, dict):
        lines = [f"{prefix}{key}:"]
        for k, v in value.items():
            lines.extend(format_value(k, v, indent + 1))
        return lines
    elif isinstance(value, list):
        if len(value) == 0:
            return [f"{prefix}{key}: []"]
        elif isinstance(value[0], (int, float)) and len(value) <= 3:
            return [f"{prefix}{key}: [{', '.join(str(x) for x in value)}]"]
        else:
            lines = [f"{prefix}{key}: ["]
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    lines.append(f"{prefix}  [{i}]:")
                    for k, v in item.items():
                        lines.extend(format_value(k, v, indent + 2))
                else:
                    lines.append(f"{prefix}  {item}")
            lines.append(f"{prefix}]")
            return lines
    else:
        return [f"{prefix}{key}: {value}"]


if __name__ == '__main__':
    print("This is a library file. Use nbt-tool.py for the interactive tool.")
    print("Or import this module in your own scripts.")
