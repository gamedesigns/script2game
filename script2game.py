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
                scenes = re.split(r'## Scene: (.+?)\n', content)
                for i in range(0, len(scenes)-1, 2):
                    scene_name = scenes[i+1].strip()
                    scene_content = scenes[i+2].strip()
                    self.scenes[scene_name] = self.parse_scene(scene_content)

    def parse_scene(self, content):
        parsed = {}
        blocks = re.split(r'\n\n', content)
        current_section = None
        for block in blocks:
            if block.startswith('### '):
                current_section = block[4:].strip()
                parsed[current_section] = []
            elif block:
                if current_section == 'Choices':
                    choices = block.strip().split('\n')
                    choice_dict = {}
                    for choice in choices:
                        choice_text, next_scene = choice.split(':')
                        choice_dict[choice_text.strip()] = next_scene.strip()
                    parsed[current_section] = choice_dict
                elif current_section == 'Dialogues':
                    dialogues = block.strip().split('\n')
                    dialogue_dict = {}
                    for dialogue in dialogues:
                        speaker, text = dialogue.split(':', 1)
                        dialogue_dict[speaker.strip()] = text.strip()
                    parsed[current_section] = dialogue_dict
                elif current_section == 'Characters':
                    characters = block.strip().split('\n')
                    character_dict = {}
                    for character in characters:
                        name, description = character.split(':', 1)
                        character_dict[name.strip()] = description.strip()
                    parsed[current_section] = character_dict
                elif current_section == 'Exits':
                    exits = [exit.lstrip('- ').strip() for exit in block.strip().split('\n')]
                    parsed[current_section] = exits
                elif current_section == 'Items':
                    items = [item.strip() for item in block.strip().split('\n')]
                    parsed[current_section] = items
                else:
                    parsed[current_section].append(block.strip())
        return parsed

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
            self.display_text(scene['Description'][0])

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
                matching_exits = [exit for exit in scene['Exits'] if exit.lower() == exit_name]
                if matching_exits:
                    self.current_scene = matching_exits[0]
                    self.play_scene(self.current_scene)
                    return
                else:
                    print("Invalid exit. Try again.")
            elif any(command == exit.lower() for exit in scene['Exits']):
                self.current_scene = [exit for exit in scene['Exits'] if exit.lower() == command][0]
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
                item = command[5:].strip()
                if any(item.lower() == i.lower() for i in scene.get('Items', [])):
                    self.inventory.append([i for i in scene['Items'] if i.lower() == item][0])
                    scene['Items'].remove([i for i in scene['Items'] if i.lower() == item][0])
                    print(f"You have picked up: {[i for i in self.inventory if i.lower() == item][0]}")
                else:
                    print("No such item here.")
            elif command.startswith('look at '):
                target = command[8:].strip()
                if any(target == item.lower() for item in scene.get('Items', [])):
                    print(f"You see: {[item for item in scene['Items'] if item.lower() == target][0]}")
                elif any(target == character.lower() for character in scene.get('Characters', {})):
                    for character, description in scene['Characters'].items():
                        if character.lower() == target:
                            print(f"{character} is in the room. {description}")
                            break
                else:
                    print("No such item or character here.")
            elif command == 'look':
                if 'Description' in scene:
                    self.display_text(scene['Description'][0])
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
            else:
                print("Invalid command. Try again.")

if __name__ == "__main__":
    engine = Script2Game(['demo.md'])
    engine.start_game()