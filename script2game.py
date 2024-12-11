import os
import time
import sys
import re
from collections import defaultdict

class DialogueNode:
    def __init__(self, text):
        self.text = text
        self.choices = []

    def add_choice(self, choice_text, next_node):
        self.choices.append((choice_text, next_node))

class Script2Game:
    def __init__(self, markdown_files):
        self.scenes = {}
        self.inventory = []
        self.variables = {}
        self.current_scene = None
        self.current_dialogue_node = None
        self.item_combinations = defaultdict(list)
        self.load_markdown_files(markdown_files)

    def load_markdown_files(self, markdown_files):
        for file in markdown_files:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                scene_pattern = r'## Scene: (.+?)\n(.*?)(?=\n## Scene: |## Global Item Combinations|$)'
                scenes = re.findall(scene_pattern, content, re.DOTALL)
                for scene_name, scene_content in scenes:
                    scene_name = scene_name.strip()
                    scene_content = scene_content.strip()
                    self.scenes[scene_name.lower()] = {
                        'name': scene_name,
                        'content': self.parse_scene(scene_content)
                    }
                
                global_combinations_pattern = r'## Global Item Combinations\n(.*?$)'
                global_combinations_content = re.search(global_combinations_pattern, content, re.DOTALL)
                if global_combinations_content:
                    global_combinations_content = global_combinations_content.group(1).strip()
                    self.parse_item_combinations(global_combinations_content)

    def parse_scene(self, content):
        parsed = {}
        pattern = r'### (.+?)\n(.*?)(?=\n### |$)'
        sections = re.findall(pattern, content, re.DOTALL)
        for header, body in sections:
            header = header.strip()
            body = body.strip()
            if header == 'Dialogues':
                parsed[header] = self.parse_dialogues(body)
            elif header == 'Characters':
                parsed[header] = self.parse_characters(body)
            elif header == 'Items':
                parsed[header] = self.parse_items(body)
            elif header == 'Item Combinations':
                self.parse_item_combinations(body)
            else:
                parsed[header] = self.parse_section_content(body)
        return parsed

    def parse_dialogues(self, content):
        lines = content.strip().split('\n')
        dialogues = {}
        current_speaker = None
        stack = []
        for line in lines:
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            if ':' in stripped:
                parts = stripped.split(':', 1)
                speaker = parts[0].strip()
                text = parts[1].strip()
                lower_speaker = speaker.lower()
                if lower_speaker not in dialogues:
                    dialogues[lower_speaker] = DialogueNode(f"{speaker}: {text}")
                    stack = [dialogues[lower_speaker]]
                    current_speaker = lower_speaker
                else:
                    print("Error: Multiple dialogues for the same speaker.")
            elif stripped.startswith('1.') or stripped.startswith('2.') or stripped.startswith('3.') or stripped.startswith('4.') or stripped.startswith('5.'):
                option_text = stripped[3:].strip()
                new_node = DialogueNode(option_text)
                if stack:
                    parent_node = stack[-1]
                    parent_node.add_choice(option_text, new_node)
                    stack.append(new_node)
                else:
                    print("Error: Option without a parent node.")
            else:
                if current_speaker and stack:
                    current_node = stack[-1]
                    current_node.text += '\n' + stripped
                else:
                    print("Warning: Orphaned line in dialogues.")
        return dialogues

    def parse_characters(self, content):
        characters = {}
        lines = content.strip().split('\n')
        current_character = None
        for line in lines:
            if ':' in line:
                parts = line.split(':', 1)
                name = parts[0].strip()
                description = parts[1].strip()
                characters[name] = {'description': description}
                current_character = name
            elif line.startswith('####'):
                item = line.lstrip('####').strip()
                if current_character:
                    if 'Items' not in characters[current_character]:
                        characters[current_character]['Items'] = []
                    characters[current_character]['Items'].append(item)
            else:
                current_character = line.strip()
        return characters

    def parse_items(self, content):
        items = []
        lines = content.strip().split('\n')
        current_item = None
        for line in lines:
            if line.startswith('####'):
                nested_item = line.lstrip('####').strip()
                if current_item:
                    current_item['contains'] = nested_item
                    items[-1] = current_item
                    current_item = None
            else:
                item_name = line.lstrip('- ').strip()
                movable = '(X)' not in item_name
                item_name = item_name.replace('(X)', '').strip()
                description = None
                if '##### Description:' in line:
                    description = line.split('##### Description:')[1].strip()
                current_item = {'name': item_name, 'contains': None, 'movable': movable, 'description': description, 'revealed': False}
                items.append(current_item)
        return items

    def parse_item_combinations(self, content):
        lines = content.strip().split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('- '):
                line = line.strip('- ')
                if ' = ' in line:
                    result_side, ingredients_side = line.split(' = ')
                    result_item_name = result_side.strip().split(': ')[0].strip().lower()
                    description = None
                    if ': ' in result_side:
                        description = result_side.split(': ')[1].strip()
                    items = re.split(r'\s*\+\s*', ingredients_side.strip())
                    if len(items) == 2:
                        item1, item2 = items[0].strip().lower(), items[1].strip().lower()
                        self.item_combinations[tuple(sorted([item1, item2]))].append((result_item_name, description))
                        print(f"Parsed combination: {tuple(sorted([item1, item2]))} = {result_item_name}")
            i += 1

    def parse_section_content(self, content):
        lines = content.strip().split('\n')
        if lines[0].startswith('- '):
            return [line.lstrip('- ').strip() for line in lines]
        elif ':' in lines[0]:
            return {line.split(':', 1)[0].strip(): line.split(':', 1)[1].strip() for line in lines}
        else:
            return lines

    def display_text(self, text, pace=0.01):
        for char in text:
            print(char, end='', flush=True)
            time.sleep(pace)
        print()

    def start_game(self):
        self.current_scene = list(self.scenes.keys())[0]
        self.play_scene(self.current_scene)

    def play_scene(self, scene_name):
        scene = self.scenes[scene_name.lower()]
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"__{scene['name']}__\n")

        self.display_scene_description(scene)
        self.display_scene_items(scene)
        self.display_scene_characters(scene)
        self.display_scene_exits(scene)

        while True:
            try:
                command = input("\nWhat do you want to do? ").strip().lower()
                self.handle_command(command, scene)
            except KeyboardInterrupt:
                print("\nThank you for playing! Goodbye.")
                sys.exit(0)

    def display_scene_description(self, scene):
        if 'Description' in scene['content']:
            for line in scene['content']['Description']:
                self.display_text(line)

    def display_scene_items(self, scene):
        if 'Items' in scene['content']:
            print("You see:")
            for item in scene['content']['Items']:
                print(f"  {item['name']}")
                if item['revealed'] and item['contains']:
                    print(f"    Inside, you see: {item['contains']}")

    def display_scene_characters(self, scene):
        if 'Characters' in scene['content']:
            for character, details in scene['content']['Characters'].items():
                print(f"{character} is in the room. {details['description']}")
                if 'Items' in details:
                    for item in details['Items']:
                        print(f"  {character} has: {item}")

    def display_scene_exits(self, scene):
        if 'Exits' in scene['content']:
            print("\nExits:")
            for exit in scene['content']['Exits']:
                print(f"- {exit}")

    def handle_command(self, command, scene):
        if command.startswith('talk to '):
            self.handle_talk_to_command(command, scene)
        elif command.startswith('go to '):
            self.handle_go_to_command(command, scene)
        elif any(command == exit.lower() for exit in scene['content'].get('Exits', [])):
            self.handle_exit_command(command, scene)
        elif command.startswith('take '):
            self.handle_take_command(command, scene)
        elif command.startswith('look at '):
            self.handle_look_at_command(command, scene)
        elif command == 'look':
            self.handle_look_command(scene)
        elif command == 'inventory' or command == 'inv':
            self.handle_inventory_command()
        elif command.startswith('use '):
            self.handle_use_command(command)
        elif command.startswith('give '):
            self.handle_give_command(command, scene)
        elif command.startswith('combine '):
            self.handle_combine_command(command)
        elif command.startswith('drop '):
            self.handle_drop_command(command, scene)
        else:
            print("Invalid command. Try again.")

    def handle_talk_to_command(self, command, scene):
        character = command[8:].strip()
        if 'Characters' in scene['content'] and character in [char.lower() for char in scene['content']['Characters']]:
            if 'Dialogues' in scene['content'] and character in scene['content']['Dialogues']:
                dialogue_root = scene['content']['Dialogues'][character]
                self.current_dialogue_node = dialogue_root
                self.handle_dialogue(dialogue_root)
            else:
                print("No dialogue available for this character.")
        else:
            print("No one by that name here.")

    def handle_go_to_command(self, command, scene):
        exit_name = command[6:].strip().lower()
        matching_exits = [exit for exit in scene['content'].get('Exits', []) if exit.lower() == exit_name]
        if matching_exits:
            self.current_scene = matching_exits[0].lower()
            self.play_scene(self.current_scene)
        else:
            print("Invalid exit. Try again.")

    def handle_exit_command(self, command, scene):
        self.current_scene = next(exit.lower() for exit in scene['content']['Exits'] if exit.lower() == command)
        self.play_scene(self.current_scene)

    def handle_take_command(self, command, scene):
        item = command[5:].strip().lower()
        scene_items = [i['name'].lower() for i in scene['content'].get('Items', [])]
        if item in scene_items:
            actual_item = next(i for i in scene['content']['Items'] if i['name'].lower() == item)
            if actual_item['movable']:
                self.inventory.append(actual_item)
                scene['content']['Items'].remove(actual_item)
                print(f"You have picked up: {actual_item['name']}")
            else:
                print("Not too handy to take along.")
        else:
            print("No such item here.")

    def handle_look_at_command(self, command, scene):
        target = command[8:].strip().lower()
        scene_items = [i['name'].lower() for i in scene['content'].get('Items', [])]
        inventory_items = [i['name'].lower() for i in self.inventory]

        if target in scene_items:
            actual_item = next(i for i in scene['content']['Items'] if i['name'].lower() == target)
            print(f"You see: {actual_item['name']}")
            if actual_item['contains']:
                print(f"Inside, you see: {actual_item['contains']}")
                # Reveal the nested item
                nested_item = {'name': actual_item['contains'], 'contains': None, 'movable': True, 'description': actual_item.get('description', None), 'revealed': True}
                scene['content']['Items'].append(nested_item)
                actual_item['revealed'] = True
            if actual_item['description']:
                print(f"Description: {actual_item['description']}")
        elif target in inventory_items:
            actual_item = next(i for i in self.inventory if i['name'].lower() == target)
            print(f"You see: {actual_item['name']}")
            if actual_item['contains']:
                print(f"Inside, you see: {actual_item['contains']}")
            if actual_item['description']:
                print(f"Description: {actual_item['description']}")
        elif 'Characters' in scene['content']:
            characters = {name.lower(): details for name, details in scene['content']['Characters'].items()}
            if target in characters:
                print(f"{target.capitalize()}: {characters[target]['description']}")
                if 'Items' in characters[target]:
                    for item in characters[target]['Items']:
                        print(f"  {target.capitalize()} has: {item}")
            else:
                print("No such item or character here.")
        else:
            print("No such item or character here.")

    def handle_look_command(self, scene):
        if 'Description' in scene['content']:
            for line in scene['content']['Description']:
                self.display_text(line)
        if 'Items' in scene['content']:
            print("You see:")
            for item in scene['content']['Items']:
                print(f"  {item['name']}")
                if item['revealed'] and item['contains']:
                    print(f"    Inside, you see: {item['contains']}")
        if 'Characters' in scene['content']:
            for character, details in scene['content']['Characters'].items():
                print(f"{character} is in the room. {details['description']}")
                if 'Items' in details:
                    for item in details['Items']:
                        print(f"  {character} has: {item}")
        if 'Exits' in scene['content']:
            print("\nExits:")
            for exit in scene['content']['Exits']:
                print(f"- {exit}")

    def handle_inventory_command(self):
        if self.inventory:
            print("Inventory:")
            for item in self.inventory:
                print(f"- {item['name']}")
                if item['description']:
                    print(f"  ({item['description']})")
        else:
            print("Your inventory is empty.")

    def handle_use_command(self, command):
        item = command[4:].strip().lower()
        inventory_items = {i['name'].lower(): i for i in self.inventory}
        if item in inventory_items:
            actual_item = inventory_items[item]
            print(f"You use {actual_item['name']}.")
            # Add specific effects based on the item used
            if actual_item['name'] == 'key':
                print("You unlock the door with the key.")
                # Add logic to handle the unlocked door
        else:
            print("You don't have that item.")

    def handle_give_command(self, command, scene):
        item = command[5:].strip().lower()
        inventory_items = {i['name'].lower(): i for i in self.inventory}
        if item in inventory_items:
            actual_item = inventory_items[item]
            print(f"You give {actual_item['name']}.")
            # Add specific effects based on the item given
            if actual_item['name'] == 'book':
                print("Sherlock Holmes: And that is exactly what I was looking for!")
                self.inventory.remove(actual_item)
        else:
            print("You don't have that item.")

    def handle_combine_command(self, command):
        # Split the command by '+' to separate the items
        parts = command.split('+')
        if len(parts) != 2:
            print("Invalid command format. Use: combine item1 + item2")
            return

        item1 = parts[0].strip().lower()
        item2 = parts[1].strip().lower()

        # Remove the 'combine ' prefix from the first item
        if item1.startswith('combine '):
            item1 = item1[len('combine '):].strip().lower()

        inventory_items = {i['name'].lower(): i for i in self.inventory}

        print(f"Debug: Trying to combine '{item1}' and '{item2}'")  # Debug print
        print(f"Debug: Inventory items: {list(inventory_items.keys())}")  # Debug print

        if item1 in inventory_items and item2 in inventory_items:
            combination_key = tuple(sorted([item1, item2]))
            if combination_key in self.item_combinations:
                possible_results = self.item_combinations[combination_key]
                if len(possible_results) == 1:
                    result_name, description = possible_results[0]
                    result_item = {'name': result_name, 'contains': None, 'movable': True, 'description': description, 'revealed': False}
                    self.inventory.remove(inventory_items[item1])
                    self.inventory.remove(inventory_items[item2])
                    self.inventory.append(result_item)
                    print(f"You create a new item: {result_name}.")
                    if description:
                        print(f"Description: {description}")
                else:
                    print("Multiple possible results. Specify which result you want.")
                    for result_name, description in possible_results:
                        print(f"- {result_name} (Description: {description if description else 'None'})")
                    result_name = input("Enter the result you want: ").strip().lower()
                    for possible_result_name, possible_description in possible_results:
                        if possible_result_name.lower() == result_name:
                            result_item = {'name': possible_result_name, 'contains': None, 'movable': True, 'description': possible_description, 'revealed': False}
                            self.inventory.remove(inventory_items[item1])
                            self.inventory.remove(inventory_items[item2])
                            self.inventory.append(result_item)
                            print(f"You create a new item: {possible_result_name}.")
                            if possible_description:
                                print(f"Description: {possible_description}")
                            return
                    print("Invalid result specified.")
            else:
                print("These items cannot be combined.")
        else:
            print("You don't have both items.")



    def handle_drop_command(self, command, scene):
        item = command[5:].strip().lower()
        inventory_items = {i['name'].lower(): i for i in self.inventory}
        if item in inventory_items:
            actual_item = inventory_items[item]
            self.inventory.remove(actual_item)
            scene['content']['Items'].append(actual_item)
            print(f"You drop {actual_item['name']}.")
        else:
            print("You don't have that item.")

    def handle_dialogue(self, current_node):
        while current_node:
            print(current_node.text)
            if current_node.choices:
                for i, (choice_text, next_node) in enumerate(current_node.choices, 1):
                    print(f"{i}. {choice_text}")
                print("E. Exit dialogue")
                choice = input("Enter the number of your choice or 'E' to exit: ").strip().lower()
                if choice == 'e':
                    self.current_dialogue_node = None
                    return
                elif choice.isdigit() and 1 <= int(choice) <= len(current_node.choices):
                    selected_choice = current_node.choices[int(choice) - 1]
                    current_node = selected_choice[1]
                    if '(Leaves to the ' in selected_choice[0]:
                        new_scene = selected_choice[0].split('(Leaves to the ')[1].split(')')[0].strip().lower()
                        self.current_scene = new_scene
                        self.play_scene(self.current_scene)
                        return
                else:
                    print("Invalid choice. Please enter a number corresponding to one of the options or 'E' to exit.")
            else:
                current_node = None

    def get_item_or_character_by_last_word(self, name, items, characters):
        last_word = name.split()[-1].lower()
        matching_items = [item for item in items if item['name'].lower().endswith(last_word)]
        matching_characters = [char for char in characters if char.lower().endswith(last_word)]

        if len(matching_items) == 1 and len(matching_characters) == 0:
            return matching_items[0]
        elif len(matching_characters) == 1 and len(matching_items) == 0:
            return matching_characters[0]
        elif len(matching_items) + len(matching_characters) > 1:
            print("Multiple matches found. Please choose the correct one:")
            for i, item in enumerate(matching_items, 1):
                print(f"{i}. {item['name']}")
            for i, char in enumerate(matching_characters, len(matching_items) + 1):
                print(f"{i}. {char}")
            choice = input("Enter the number of your choice: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(matching_items) + len(matching_characters):
                choice_index = int(choice) - 1
                if choice_index < len(matching_items):
                    return matching_items[choice_index]
                else:
                    return matching_characters[choice_index - len(matching_items)]
            else:
                print("Invalid choice. Try again.")
                return None
        else:
            return None

if __name__ == "__main__":
    engine = Script2Game(['demo.md'])
    engine.start_game()