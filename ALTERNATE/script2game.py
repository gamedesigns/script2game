from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any
import yaml
import json
from pathlib import Path
import re
import cmd
import textwrap

@dataclass
class GameObject:
    id: str
    name: str
    description: str
    type: str = "object"
    aliases: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GameState:
    current_scene: str
    inventory: List[str]
    variables: Dict[str, Any]
    flags: List[str]
    character_states: Dict[str, Dict]

class GameParser:
    def __init__(self, markdown_path: str):
        self.game_data = self._parse_markdown(markdown_path)
        self.objects = self._build_object_registry()
        self.alias_map = self._build_alias_map()
        self.state = self._initialize_state()

    def _parse_markdown(self, path: str) -> Dict[str, Any]:
        content = Path(path).read_text(encoding='utf-8')
        sections = {}
        current_section = None
        metadata_content = []
        section_content = []
        
        for line in content.split('\n'):
            if line.startswith('# '):
                if current_section == 'metadata':
                    sections['metadata'] = self._parse_metadata(''.join(metadata_content))
                elif current_section:
                    sections[current_section] = self._parse_section(section_content)
                current_section = line[2:].lower().strip()
                section_content = []
            elif line.startswith('---') and not current_section:
                current_section = 'metadata'
            elif current_section == 'metadata':
                metadata_content.append(line)
                if line.startswith('---'):
                    current_section = None
            else:
                section_content.append(line)
        
        # Process last section
        if section_content:
            sections[current_section] = self._parse_section(section_content)
            
        return sections

    def _parse_metadata(self, content: str) -> Dict[str, Any]:
        # Extract content between --- markers
        match = re.search(r'---(.*?)---', content, re.DOTALL)
        if match:
            return yaml.safe_load(match.group(1))
        return {}

    def _parse_section(self, content: List[str]) -> Dict[str, Any]:
        parsed = {}
        current_obj = None
        current_data = {}
        
        for line in content:
            if line.strip():
                if line.startswith('## '):
                    if current_obj:
                        parsed[current_obj] = current_data
                    current_obj = line[3:].strip()
                    current_data = {}
                elif line.startswith('- '):
                    key_value = line[2:].split(':', 1)
                    if len(key_value) == 2:
                        key = key_value[0].strip()
                        value = key_value[1].strip()
                        try:
                            # Try parsing as JSON for lists/dicts
                            value = json.loads(value)
                        except json.JSONDecodeError:
                            pass
                        current_data[key] = value
                elif line.startswith('    * '):
                    # Handle nested lists/objects
                    item = line[6:].strip()
                    if isinstance(current_data.get(key, None), list):
                        current_data[key].append(item)
                    else:
                        current_data[key] = [item]
        
        if current_obj:
            parsed[current_obj] = current_data
            
        return parsed

    def _build_object_registry(self) -> Dict[str, GameObject]:
        registry = {}
        
        # Process items
        for item_id, item_data in self.game_data.get('items', {}).items():
            registry[item_id] = GameObject(
                id=item_id,
                name=item_data.get('name', item_id),
                description=item_data.get('description', ''),
                type=item_data.get('type', 'item'),
                aliases=item_data.get('aliases', []),
                properties={k: v for k, v in item_data.items() 
                          if k not in ['name', 'description', 'type', 'aliases']}
            )
        
        # Process scene objects
        for scene_id, scene_data in self.game_data.get('scenes', {}).items():
            for obj_id, obj_data in scene_data.get('objects', {}).items():
                registry[obj_id] = GameObject(
                    id=obj_id,
                    name=obj_data.get('name', obj_id),
                    description=obj_data.get('description', ''),
                    type=obj_data.get('type', 'scenery'),
                    aliases=obj_data.get('aliases', []),
                    properties={k: v for k, v in obj_data.items()
                              if k not in ['name', 'description', 'type', 'aliases']}
                )
        
        return registry

    def _build_alias_map(self) -> Dict[str, str]:
        alias_map = {}
        for obj in self.objects.values():
            alias_map[obj.name.lower()] = obj.id
            for alias in obj.aliases:
                alias_map[alias.lower()] = obj.id
        return alias_map

    def _initialize_state(self) -> GameState:
        metadata = self.game_data['metadata']
        variables = self.game_data.get('variables', {}).get('player', {})
        
        return GameState(
            current_scene=metadata.get('starting_scene', ''),
            inventory=metadata.get('starting_inventory', []),
            variables=variables,
            flags=[],
            character_states={}
        )

    def get_object_by_name(self, name: str) -> Optional[GameObject]:
        obj_id = self.alias_map.get(name.lower())
        return self.objects.get(obj_id)

    def get_current_scene(self) -> Dict[str, Any]:
        return self.game_data['scenes'].get(self.state.current_scene, {})

    def get_visible_objects(self) -> List[GameObject]:
        scene = self.get_current_scene()
        objects = []
        
        # Add scene objects
        for obj_id in scene.get('objects', {}).keys():
            if obj := self.objects.get(obj_id):
                objects.append(obj)
        
        # Add items in scene
        for item_id in scene.get('items', []):
            if item := self.objects.get(item_id):
                objects.append(item)
                
        return objects

class GameEngine(cmd.Cmd):
    prompt = '> '
    
    def __init__(self, game_file: str):
        super().__init__()
        self.parser = GameParser(game_file)
        self.wrapper = textwrap.TextWrapper(width=70)
        self.print_welcome()
        self.look()

    def print_welcome(self):
        metadata = self.parser.game_data['metadata']
        print(f"\n{metadata['title']}")
        print("=" * len(metadata['title']))
        print(f"\n{metadata['description']}\n")
        print("Type 'help' for a list of commands.\n")

    def _wrap_text(self, text: str) -> str:
        return '\n'.join(self.wrapper.wrap(text))

    def default(self, line: str):
        print("I don't understand that command. Type 'help' for a list of commands.")

    def do_quit(self, arg):
        """Quit the game"""
        return True

    def do_look(self, arg):
        """Look around or examine something specific"""
        if not arg:
            scene = self.parser.get_current_scene()
            print(f"\n{scene.get('name', 'Unnamed Location')}")
            print("-" * len(scene.get('name', 'Unnamed Location')))
            print(self._wrap_text(scene['description']))
            
            # List visible objects
            visible = self.parser.get_visible_objects()
            if visible:
                print("\nYou can see:")
                for obj in visible:
                    print(f"  - {obj.name}")
                    
            # List exits
            exits = scene.get('exits', {})
            if exits:
                print("\nExits:", ', '.join(exits.keys()))
        else:
            if obj := self.parser.get_object_by_name(arg):
                print(self._wrap_text(obj.description))
            else:
                print(f"You don't see any {arg} here.")

    def do_inventory(self, arg):
        """Show your inventory"""
        if not self.parser.state.inventory:
            print("You're not carrying anything.")
            return
            
        print("\nYou are carrying:")
        for item_id in self.parser.state.inventory:
            if item := self.parser.objects.get(item_id):
                print(f"  - {item.name}")

    def do_take(self, arg):
        """Take an object"""
        if not arg:
            print("Take what?")
            return
            
        scene = self.parser.get_current_scene()
        obj = self.parser.get_object_by_name(arg)
        
        if not obj:
            print(f"You don't see any {arg} here.")
            return
            
        if obj.id not in scene.get('items', []):
            print(f"You can't take the {obj.name}.")
            return
            
        scene['items'].remove(obj.id)
        self.parser.state.inventory.append(obj.id)
        print(f"Taken: {obj.name}")

    def do_drop(self, arg):
        """Drop an object from your inventory"""
        if not arg:
            print("Drop what?")
            return
            
        obj = self.parser.get_object_by_name(arg)
        if not obj or obj.id not in self.parser.state.inventory:
            print(f"You're not carrying any {arg}.")
            return
            
        self.parser.state.inventory.remove(obj.id)
        self.parser.get_current_scene().setdefault('items', []).append(obj.id)
        print(f"Dropped: {obj.name}")

    def do_go(self, arg):
        """Move in a direction"""
        if not arg:
            print("Go where?")
            return
            
        scene = self.parser.get_current_scene()
        exits = scene.get('exits', {})
        
        if arg not in exits:
            print(f"You can't go {arg}.")
            return
            
        exit_data = exits[arg]
        if isinstance(exit_data, dict):
            if 'requires' in exit_data:
                required = exit_data['requires']
                if required not in self.parser.state.inventory:
                    print(exit_data.get('message', f"You need {required} to go that way."))
                    return
                    
            if 'blocked' in exit_data and exit_data['blocked']:
                print(exit_data.get('message', "You can't go that way."))
                return
                
            self.parser.state.current_scene = exit_data['destination']
        else:
            self.parser.state.current_scene = exit_data
            
        self.do_look('')

    def do_use(self, arg):
        """Use an item, possibly with another item"""
        if not arg:
            print("Use what?")
            return
            
        args = arg.split(' on ')
        if len(args) == 1:
            args = arg.split(' with ')
            
        obj1 = self.parser.get_object_by_name(args[0])
        if not obj1:
            print(f"You don't have any {args[0]}.")
            return
            
        if len(args) == 1:
            if 'use_message' in obj1.properties:
                print(self._wrap_text(obj1.properties['use_message']))
            else:
                print(f"You can't use the {obj1.name} by itself.")
            return
            
        obj2 = self.parser.get_object_by_name(args[1])
        if not obj2:
            print(f"You don't see any {args[1]} here.")
            return
            
        # Handle using keys on locked objects
        if obj1.type == 'key' and obj2.properties.get('locked'):
            if obj1.properties.get('unlocks') == obj2.id:
                obj2.properties['locked'] = False
                print(obj2.properties.get('on_unlock', f"You unlock the {obj2.name}."))
            else:
                print(f"The {obj1.name} doesn't fit the lock.")
        else:
            print(f"You can't use the {obj1.name} with the {obj2.name}.")

    def do_talk(self, arg):
        """Talk to a character"""
        if not arg:
            print("Talk to whom?")
            return
            
        scene = self.parser.get_current_scene()
        if arg not in scene.get('characters', []):
            print(f"{arg} isn't here.")
            return
            
        char_data = self.parser.game_data['characters'][arg]
        dialogue = char_data.get('dialogue', {})
        
        char_state = self.parser.state.character_states.setdefault(arg, {})
        current_dialogue = char_state.get('current_dialogue', 'initial')
        
        if current_dialogue in dialogue:
            self._handle_dialogue(arg, dialogue[current_dialogue])
        else:
            print(f"{char_data['name']} has nothing to say.")

    def _handle_dialogue(self, char_id: str, dialogue: Dict):
        # Print character's line
        print(f"\n{dialogue.get('text', '')}")
        
        # Show response options
        options = dialogue.get('options', [])
        if not options:
            return
            
        print("\nResponses:")
        for i, option in enumerate(options, 1):
            print(f"{i}. {option['text']}")
            
        while True:
            try:
                choice = int(input("\nChoose a response (or 0 to end conversation): "))
                if choice == 0:
                    return
                if 1 <= choice <= len(options):
                    selected = options[choice - 1]
                    self._process_dialogue_option(char_id, selected)
                    break
                print("Invalid choice.")
            except ValueError:
                print("Please enter a number.")

    def _process_dialogue_option(self, char_id: str, option: Dict):
        # Handle requirements
        if 'requires' in option:
            required = option['requires']
            if required not in self.parser.state.flags:
                print("That response isn't available.")
                return
                
        # Handle item giving
        if 'gives' in option:
            item_id = option['gives']
            self.parser.state.inventory.append(item_id)
            item = self.parser.objects[item_id]
            print(f"\nReceived: {item.name}")
            
        # Handle item taking
        if 'takes' in option:
            item_id = option['takes']
            if item_id in self.parser.state.inventory:
                self.parser.state.inventory.remove(item_id)
                print(f"\nGave: {self.parser.objects[item_id].name}")
            else:
                print("You don't have that item.")
                return
                
        # Handle dialogue state changes
        if 'goto' in option:
            self.parser.state.character_states[char_id]['current_dialogue'] = option['goto']
            self._handle_dialogue(char_id, self.parser.game_data['characters'][char_id]['dialogue'][option['goto']])
        elif 'ends' in option and option['ends'] == 'dialogue':
            return

    def do_examine(self, arg):
        """Examine an object in detail"""
        if not arg:
            print("Examine what?")
            return
            
        obj = self.parser.get_object_by_name(arg)
        if not obj:
            print(f"You don't see any {arg} here.")
            return
            
        print(self._wrap_text(obj.properties.get('examine', obj.description)))
        
        # Check if object is a container
        if obj.type == 'container' and not obj.properties.get('locked', False):
            contents = obj.properties.get('contains', [])
            if contents:
                print("\nIt contains:")
                for item_id in contents:
                    if item := self.parser.objects.get(item_id):
                        print(f"  - {item.name}")

    def do_lockpick(self, arg):
        """Try to pick a lock using lockpicking tools"""
        if not arg:
            print("Pick what?")
            return
            
        # Check if player has lockpicks
        has_lockpick = False
        for item_id in self.parser.state.inventory:
            if item := self.parser.objects.get(item_id):
                if item.type == 'tool' and 'lockpicking' in item.properties.get('skill_bonus', {}):
                    has_lockpick = True
                    break
                    
        if not has_lockpick:
            print("You need lockpicking tools for that.")
            return
            
        obj = self.parser.get_object_by_name(arg)
        if not obj or not obj.properties.get('lockable'):
            print(f"You can't pick the lock of {arg}.")
            return
            
        if not obj.properties.get('locked'):
            print(f"The {obj.name} isn't locked.")
            return
            
        # Calculate lockpicking attempt
        player_skill = self.parser.state.variables.get('lockpicking_skill', 0)
        tool_bonus = item.properties['skill_bonus']['lockpicking']
        difficulty = obj.properties['lock_difficulty']
        
        if player_skill + tool_bonus >= difficulty:
            obj.properties['locked'] = False
            print(obj.properties.get('on_unlock', f"You successfully pick the lock of the {obj.name}."))
        else:
            print(obj.properties.get('on_fail_lockpick', f"You fail to pick the lock of the {obj.name}."))

def main():
    game = GameEngine("detective_office.md")
    game.cmdloop()

if __name__ == "__main__":
    main()