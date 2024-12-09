import re
import json
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
        for block in blocks:
            if block.startswith('### '):
                section = block[4:].strip()
                parsed[section] = []
            elif block:
                parsed[section].append(block.strip())
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
        os.system('cls' if os.system == 'nt' else 'clear')
        print(f"## Scene: {scene_name}\n")

        if 'Description' in scene:
            self.display_text(scene['Description'][0])

        if 'Dialogues' in scene:
            for dialogue in scene['Dialogues']:
                speaker, text = dialogue.split(':', 1)
                print(f"{speaker.strip()}: {text.strip()}")

        if 'Items' in scene:
            for item in scene['Items']:
                self.inventory.append(item)

        if 'Exits' in scene:
            print("\nExits:")
            for exit in scene['Exits']:
                print(f"- {exit}")

        choice = input("\nWhat do you want to do? ").strip().lower()
        if choice in scene.get('Choices', []):
            next_scene = scene['Choices'][choice]
            self.play_scene(next_scene)
        else:
            print("Invalid choice. Try again.")
            self.play_scene(scene_name)

if __name__ == "__main__":
    engine = Script2Game(['demo.md'])
    engine.start_game()