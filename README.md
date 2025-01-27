# Cargo-2
The Cargo saga continues! Navigate treacherous space lanes and pilot customizable cargo haulers in this event-packed text strategic RPG sequel. Manage your cargo efficiently and face off against new enemies and environmental hazards in thrilling new chapters that follow the original story.
- [ ] Improved game system
- [ ] Evolving story lines
- [ ] New ships and items
- [ ] Evolving story lines
- [ ] Original music and sounds

```console
>>> 
        ╔═══════ C Δ R G Ω ][ ══════╗
        ║     Space Trading Saga    ║
        ╚═══════════════════════════╝
               Version 0.1.0-a

```

You are professional game developer and you are refactoring Cargo text rpg strategy game to Cargo 2, with goal to refactor its structure to data driven approach. I will present a structure of the project so far, several refactored files and the original code. You will analyze the data and find necessary adjustments. 

cargo-2/
├── core/
│   ├── __init__.py
│   ├── game.py
│   ├── gameplay.py    
│   ├── game_events.py    
│   ├── location.py
│   ├── location_data.py
│   ├── location_manager.py
│   ├── captain.py
│   ├── character.py
│   ├── character_encounters.py
│   ├── dynamic_character_system.py
│   ├── quest.py
│   ├── contract.py
│   ├── ship.py
│   ├── shop.py
│   ├── cantina.py
│   ├── research.py
│   ├── reputation.py
│   ├── audio.py
│   ├── action.py
│   ├── port.py
│   ├── event.py
│   ├── uprising.py
│   ├── utils.py
│   ├── template.py
│   ├── ui.py
│   ├── uprising.py
│   ├── story_requirements.py
│   └── story.py
├── data/
│   ├── items.csv
│   ├── locations.csv
│   ├── buildings.csv
│   ├── enemies.yml
│   ├── events.yml
│   ├── characters.yml
│   ├── quests.yml
│   ├── contracts.yml
│   ├── story.yml
│   ├── infestations.json
│   ├── ranks.json
│   ├── reputation.json
│   ├── settings.json
│   ├── themes.json
│   ├── music.json
│   └── sound.json
├── assets/
│   ├── music/
│   │   ├── theme1.mp3
│   │   ├── theme2.mp3
│   │   └── ...
│   ├── sound/
│   │   ├── click.wav
│   │   ├── explosion.wav
│   │   └── ...
│   └── themes/
│       ├── default.json
│       ├── dark.json
│       └── ...
├── backend/
│   ├── __init__.py
│   ├── api.py
│   └── auth.py
├── ui/
│   ├── __init__.py
│   ├── text_ui.py
│   └── theme_manager.py
├── cargo.py
├── savegames/
│   ├── save1.json
│   └── ...
└── requirements.txt
