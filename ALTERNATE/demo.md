# The Detective's Office
---
title: The Detective's Office
subtitle: A Noir Mystery
author: Sample Author
version: 1.0
credits:
  - Writing: John Smith
  - Design: Jane Doe
  - Testing: Mike Johnson
description: |
  A noir detective story where you explore a mysterious office
  and uncover hidden secrets.
starting_scene: office_main
starting_inventory: ["id_card_player"]
---

# Variables
## player
- health: 100
- max_health: 100
- lockpicking_skill: 1

# Items

## id_card_player
- name: Detective's Badge
- description: Your trusty detective's badge
- examine: The badge shows your photo and ID number 7749
- type: key
- aliases: ["badge", "detective badge", "id", "detective's badge"]

## drawer_key_brass
- name: Brass Key
- description: A small brass key
- examine: A tarnished brass key with the number "3" engraved on it
- type: key
- aliases: ["brass key", "small key", "key"]
- unlocks: drawer_locked

## lockpick_basic
- name: Lockpick Set
- description: A basic set of lockpicking tools
- examine: A set of basic lockpicking tools. Might be useful for simple locks.
- type: tool
- aliases: ["lockpick", "picks", "lockpicks", "picking tools"]
- skill_bonus: 
    lockpicking: 1

## paper_confidential
- name: Confidential Document
- description: A document marked "CONFIDENTIAL" in red
- examine: The document contains sensitive information about a recent case
- type: document
- aliases: ["document", "confidential paper", "papers", "file"]
- readable: true
- content: |
    Case #458
    Subject: Missing Artifacts
    Location: City Museum
    Details: Three artifacts disappeared during regular hours...

## desk_drawer_contents
- name: Drawer Contents
- type: container
- description: Various items inside the drawer
- aliases: ["drawer items", "items in drawer"]
- contains: ["paper_confidential"]

# Characters

## secretary_jane
- name: Jane Wilson
- description: The department's secretary
- location: office_reception
- initial_state: working
- inventory: ["drawer_key_brass"]
- dialogue:
    * [initial]
      > Good morning, detective. Working late again?
      - response: Can I have the drawer key?
        * requires: working_late
        * gives: drawer_key_brass
        * goto: gives_key
      - response: Just passing through
        * ends: dialogue
    
    * [gives_key]
      > Here's the key to drawer 3. Please return it before you leave.
      - response: Thanks, I will
        * ends: dialogue
      - response: What's in the drawer?
        * goto: drawer_contents

    * [drawer_contents]
      > Just some old case files, I think. Nothing too exciting.
      - response: Thanks for the info
        * ends: dialogue

# Scenes

## office_main
- name: Detective's Office
- description: |
    A cramped detective's office with a worn wooden desk dominating the space.
    Yellow light filters through venetian blinds, casting striped shadows on the wall.
- items: ["lockpick_basic"]
- examine: |
    The office is cluttered but organized. A large desk sits in the center,
    with a locked drawer on its right side. A door leads to the reception area.
- objects:
    * desk_main:
        - name: Wooden Desk
        - description: A solid wooden desk with three drawers
        - aliases: ["desk", "office desk", "table"]
        - interactive: true
        - actions: ["examine", "search"]
    * drawer_locked:
        - name: Locked Drawer
        - description: A drawer with a brass lock
        - aliases: ["drawer", "locked drawer", "desk drawer"]
        - locked: true
        - lockable: true
        - lock_difficulty: 2
        - key_required: drawer_key_brass
        - contains: ["desk_drawer_contents"]
        - on_unlock: "The drawer slides open smoothly."
        - on_fail_lockpick: "You struggle with the lock but can't quite get it open."
- exits:
    * north: office_reception
    * window: 
        - destination: street
        - blocked: true
        - message: The window is painted shut.

## office_reception
- name: Reception Area
- description: |
    A tidy reception area with a polished counter and several chairs.
    The secretary's desk faces the entrance.
- examine: |
    The reception area is well-maintained. A row of filing cabinets lines
    the wall behind the secretary's desk. The main office is to the south.
- characters: ["secretary_jane"]
- objects:
    * cabinet_files:
        - name: Filing Cabinets
        - description: A row of metal filing cabinets
        - aliases: ["cabinets", "files", "file cabinet"]
        - locked: true
        - lockable: true
        - lock_difficulty: 4
        - on_fail_lockpick: "These locks are too sophisticated for your basic lockpicking tools."
- exits:
    * south: office_main
    * entrance:
        - destination: hallway
        - requires: id_card_player
        - message: You show your badge to exit.

# GameStates

## time_states
- morning:
    - time: 0
    - description: "Sunlight streams through the windows."
- evening:
    - time: 12
    - description: "Long shadows stretch across the floor."
    - triggers: ["working_late"]

## working_late
- conditions: ["time_state:evening"]
- effects:
    * message: "It's getting late. Most staff have gone home."
    * set_flag: working_late

# Events

## enter_office
- trigger: location:office_main
- once: true
- effects:
    * message: "Another day at the detective agency begins..."

## pick_drawer
- trigger: action:lockpick:drawer_locked
- conditions: ["has:lockpick_basic"]
- effects:
    * check: "player.lockpicking_skill + lockpick_basic.skill_bonus >= drawer_locked.lock_difficulty"
    * success:
        - message: "After some careful work, the lock clicks open."
        - unlock: drawer_locked
    * failure:
        - message: "The lock proves too difficult for your current skill."