import re
import os
import time

class Script2Game:
    def __init__(self, markdown_files):
        self.scenes = {}
        self.inventory = []
        self.variables = {}
        self.current_scene = None
        self.load_markdown_files(markdown_files)

    def load_markdown_files(self, markdown_files):
        for file in markdown_files:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                pattern = r'## Scene: (.+?)\n(.*?)(?=\n## Scene: |$)'
                scenes = re.findall(pattern, content, re.DOTALL)
                for scene_name, scene_content in scenes:
                    scene_name = scene_name.strip()
                    scene_content = scene_content.strip()
                    self.scenes[scene_name.lower()] = {
                        'name': scene_name,
                        'content': self.parse_scene(scene_content)
                    }

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
            else:
                parsed[header] = self.parse_section_content(body)
        return parsed

    def parse_section_content(self, content):
        lines = content.strip().split('\n')
        if lines[0].startswith('- '):
            return [line.lstrip('- ').strip() for line in lines]
        elif ':' in lines[0]:
            return {line.split(':', 1)[0].strip(): line.split(':', 1)[1].strip() for line in lines}
        else:
            return lines

    def parse_dialogues(self, content):
        dialogues = {}
        lines = content.strip().split('\n')
        current_speaker = None
        for line in lines:
            if ':' in line:
                parts = line.split(':', 1)
                speaker = parts[0].strip()
                text = parts[1].strip()
                current_speaker = speaker
                if speaker in dialogues:
                    dialogues[speaker] += ' ' + text
                else:
                    dialogues[speaker] = text
            else:
                if current_speaker is not None:
                    dialogues[current_speaker] += ' ' + line.strip()
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
        for line in lines:
            if line.startswith('####'):
                nested_item = line.lstrip('####').strip()
                if items:
                    items[-1] = f"{items[-1]} (contains {nested_item})"
            else:
                items.append(line.strip())
        return items

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

        if 'Description' in scene['content']:
            for line in scene['content']['Description']:
                self.display_text(line)

        if 'Items' in scene['content']:
            for item in scene['content']['Items']:
                print(f"You see: {item}")

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

        while True:
            command = input("\nWhat do you want to do? ").strip().lower()
            if command.startswith('go to '):
                exit_name = command[6:].strip().lower()
                matching_exits = [exit for exit in scene['content'].get('Exits', []) if exit.lower() == exit_name]
                if matching_exits:
                    self.current_scene = matching_exits[0]
                    self.play_scene(self.current_scene)
                    return
                else:
                    print("Invalid exit. Try again.")
            elif any(command == exit.lower() for exit in scene['content'].get('Exits', [])):
                self.current_scene = next(exit for exit in scene['content']['Exits'] if exit.lower() == command)
                self.play_scene(self.current_scene)
                return
            elif command.startswith('talk to '):
                character = command[8:].strip()
                if 'Dialogues' in scene['content'] and any(speaker.lower() == character for speaker in scene['content']['Dialogues']):
                    for speaker, text in scene['content']['Dialogues'].items():
                        if speaker.lower() == character:
                            print(f"{speaker}: {text}")
                            # Handle branching dialogue
                            if 'branch' in text.lower():
                                self.handle_branching_dialogue(scene, speaker)
                            break
                else:
                    print("No one by that name here.")
            elif command.startswith('take '):
                item = command[5:].strip().lower()
                scene_items = [i.lower() for i in scene['content'].get('Items', [])]
                if item in scene_items:
                    actual_item = next(i for i in scene['content']['Items'] if i.lower() == item)
                    self.inventory.append(actual_item)
                    scene['content']['Items'].remove(actual_item)
                    print(f"You have picked up: {actual_item}")
                else:
                    print("No such item here.")
            elif command.startswith('look at '):
                target = command[8:].strip().lower()
                # Check items
                scene_items = [i.lower() for i in scene['content'].get('Items', [])]
                if target in scene_items:
                    actual_item = next(i for i in scene['content']['Items'] if i.lower() == target)
                    print(f"You see: {actual_item}")
                    if 'contains' in actual_item:
                        nested_item = actual_item.split('(contains ')[1].split(')')[0]
                        print(f"Inside, you see: {nested_item}")
                # Check characters
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
            elif command == 'look':
                if 'Description' in scene['content']:
                    for line in scene['content']['Description']:
                        self.display_text(line)
                if 'Items' in scene['content']:
                    for item in scene['content']['Items']:
                        print(f"You see: {item}")
                        if 'contains' in item:
                            nested_item = item.split('(contains ')[1].split(')')[0]
                            print(f"Inside, you see: {nested_item}")
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
            elif command == 'inventory' or command == 'inv':
                if self.inventory:
                    print("Inventory:")
                    for item in self.inventory:
                        print(f"- {item}")
                else:
                    print("Your inventory is empty.")
            elif command.startswith('use '):
                item = command[4:].strip().lower()
                inventory_items = [i.lower() for i in self.inventory]
                if item in inventory_items:
                    actual_item = next(i for i in self.inventory if i.lower() == item)
                    print(f"You use {actual_item}.")
                    # Add specific effects based on the item used
                else:
                    print("You don't have that item.")
            elif command.startswith('give '):
                item = command[5:].strip().lower()
                inventory_items = [i.lower() for i in self.inventory]
                if item in inventory_items:
                    actual_item = next(i for i in self.inventory if i.lower() == item)
                    print(f"You give {actual_item}.")
                    # Add specific effects based on the item given
                else:
                    print("You don't have that item.")
            elif command.startswith('combine '):
                items = command[8:].strip().lower().split()
                if len(items) == 2:
                    item1, item2 = items
                    inventory_items = [i.lower() for i in self.inventory]
                    if item1 in inventory_items and item2 in inventory_items:
                        actual_item1 = next(i for i in self.inventory if i.lower() == item1)
                        actual_item2 = next(i for i in self.inventory if i.lower() == item2)
                        print(f"You combine {actual_item1} and {actual_item2}.")
                        # Add specific effects based on the items combined
                    else:
                        print("You don't have both items.")
                else:
                    print("Invalid command. Try again.")
            else:
                print("Invalid command. Try again.")

    def handle_branching_dialogue(self, scene, speaker):
        if speaker == 'Sherlock Holmes' and 'ask him about an experiment' in scene['content']['Dialogues'][speaker].lower():
            print("Sherlock Holmes: I must go to the laboratory to continue my experiment. Follow me if you wish.")
            self.current_scene = 'Laboratory'
            self.play_scene(self.current_scene)

if __name__ == "__main__":
    engine = Script2Game(['demo.md'])
    engine.start_game()
