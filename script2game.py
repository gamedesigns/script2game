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
                    self.scenes[scene_name] = self.parse_scene(scene_content)

    def parse_scene(self, content):
        parsed = {}
        pattern = r'### (.+?)\n(.*?)(?=\n### |$)'
        sections = re.findall(pattern, content, re.DOTALL)
        for header, body in sections:
            header = header.strip()
            body = body.strip()
            if header == 'Dialogues':
                parsed[header] = self.parse_dialogues(body)
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

    def display_text(self, text, pace=0.01):
        for char in text:
            print(char, end='', flush=True)
            time.sleep(pace)
        print()

    def start_game(self):
        self.current_scene = list(self.scenes.keys())[0]
        self.play_scene(self.current_scene)

    def play_scene(self, scene_name):
        scene = self.scenes[scene_name]
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"__{scene_name}__\n")

        if 'Description' in scene:
            for line in scene['Description']:
                self.display_text(line)

        if 'Items' in scene:
            for item in scene['Items']:
                print(f"You see: {item}")

        if 'Characters' in scene:
            for character, description in scene['Characters'].items():
                print(f"{character} is in the room. {description}")

        if 'Exits' in scene:
            print("\nExits:")
            for exit in scene['Exits']:
                print(f"- {exit}")

        while True:
            command = input("\nWhat do you want to do? ").strip().lower()
            if command.startswith('go to '):
                exit_name = command[6:].strip().lower()
                matching_exits = [exit for exit in scene.get('Exits', []) if exit.lower() == exit_name]
                if matching_exits:
                    self.current_scene = matching_exits[0]
                    self.play_scene(self.current_scene)
                    return
                else:
                    print("Invalid exit. Try again.")
            elif any(command == exit.lower() for exit in scene.get('Exits', [])):
                self.current_scene = next(exit for exit in scene['Exits'] if exit.lower() == command)
                self.play_scene(self.current_scene)
                return
            elif command.startswith('talk to '):
                character = command[8:].strip()
                if 'Dialogues' in scene and any(speaker.lower() == character for speaker in scene['Dialogues']):
                    for speaker, text in scene['Dialogues'].items():
                        if speaker.lower() == character:
                            print(f"{speaker}: {text}")
                            break
                else:
                    print("No one by that name here.")
            elif command.startswith('take '):
                item = command[5:].strip().lower()
                scene_items = [i.lower() for i in scene.get('Items', [])]
                if item in scene_items:
                    actual_item = scene['Items'][scene_items.index(item)]
                    self.inventory.append(actual_item)
                    scene['Items'].remove(actual_item)
                    print(f"You have picked up: {actual_item}")
                else:
                    print("No such item here.")
            elif command.startswith('look at '):
                target = command[8:].strip().lower()
                # Check items
                scene_items = [i.lower() for i in scene.get('Items', [])]
                if target in scene_items:
                    actual_item = next(i for i in scene['Items'] if i.lower() == target)
                    print(f"You see: {actual_item}")
                # Check characters
                elif 'Characters' in scene:
                    characters = {name.lower(): desc for name, desc in scene['Characters'].items()}
                    if target in characters:
                        print(f"{target.capitalize()}: {characters[target]}")
                    else:
                        print("No such item or character here.")
                else:
                    print("No such item or character here.")
            elif command == 'look':
                if 'Description' in scene:
                    for line in scene['Description']:
                        self.display_text(line)
                if 'Items' in scene:
                    for item in scene['Items']:
                        print(f"You see: {item}")
                if 'Characters' in scene:
                    for character, description in scene['Characters'].items():
                        print(f"{character} is in the room. {description}")
                if 'Exits' in scene:
                    print("\nExits:")
                    for exit in scene['Exits']:
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
            else:
                print("Invalid command. Try again.")

if __name__ == "__main__":
    engine = Script2Game(['demo.md'])
    engine.start_game()