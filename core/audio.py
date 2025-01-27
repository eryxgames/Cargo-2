# core/audio.py
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
from ui.text_ui import TextUI
import pygame
import threading
import os
import json

class AudioManager:
    def __init__(self, game, frequency=44100, size=-16, channels=8, buffer=4096, num_reserved=2, settings=None):
        self.game = game # Now game object is passed here
        pygame.mixer.init(frequency=frequency, size=size, channels=channels, buffer=buffer)
        self.num_reserved = num_reserved
        pygame.mixer.set_reserved(self.num_reserved)
        self.sounds = {}
        self.music = {}
        self.current_music = None
        self.music_volume = 1.0
        self.sound_effects_volume = 1.0
        self.music_muted = False
        self.sound_effects_muted = False
        self.music_lock = threading.Lock()
        self.settings = settings if settings else self.load_settings()
        self.music_data = self.load_music_data()  # Load music data from file
        self.sound_data = self.load_sound_data()  # Load sound data from file
        self.initialize_music({track["track_id"]: track["path"] for track in self.music_data.get("tracks", [])})
        self.initialize_sounds({effect["effect_id"]: effect["path"] for effect in self.sound_data.get("effects", [])})

    def load_settings(self):
        """Load settings from data/settings.json"""
        try:
            with open("data/settings.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Error: settings.json not found. Using default settings.")
            return {}
        except json.JSONDecodeError:
            print("Error: Could not parse settings.json. Using default settings.")
            return {}

    def load_music_data(self):
        """Load music data from data/music.json"""
        try:
            with open("data/music.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Error: music.json not found. Music will be disabled.")
            return {"tracks": []}
        except json.JSONDecodeError:
            print("Error: could not parse music.json. Music will be disabled.")
            return {"tracks": []}

    def load_sound_data(self):
        """Load sound data from data/sound.json"""
        try:
            with open("data/sound.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Error: sound.json not found. Sounds will be disabled.")
            return {"effects": []}
        except json.JSONDecodeError:
            print("Error: could not parse sound.json. Sounds will be disabled.")
            return {"effects": []}

    def initialize_sounds(self, sound_files):
      for name, file_path in sound_files.items():
          try:
            self.sounds[name] = pygame.mixer.Sound(file_path)
          except pygame.error as e:
            print(f"Error loading sound {name}: {e}")
          except FileNotFoundError:
            print(f"Error: sound file not found at: {file_path}")

    def initialize_music(self, music_files):
        for name, file_path in music_files.items():
            self.music[name] = file_path

    def play_sound(self, name, priority=False):
        if not self.settings.get("sound_enabled", True):
            return
        if not self.sound_effects_muted:
            if name in self.sounds:
                if priority:
                    for i in range(self.num_reserved):
                        channel = pygame.mixer.Channel(i)
                        if not channel.get_busy():
                            channel.set_volume(self.sound_effects_volume)
                            channel.play(self.sounds[name])
                            return
                else:
                    sound = self.sounds[name]
                    sound.set_volume(self.sound_effects_volume)
                    sound.play()
            else:
                # Fallback: print sound description if sound is not present
                for effect in self.sound_data.get("effects", []):
                    if effect.get("effect_id") == name:
                       self.display_description(effect.get('description', 'Unknown sound'))
                       return

    def play_music(self, track, fade_time=0):
        with self.music_lock:
            if not self.settings.get("music_enabled", True):
                return
            if not self.music_muted and track in self.music:
                if self.current_music != track:
                    if fade_time > 0:
                        pygame.mixer.music.fadeout(fade_time)
                        while pygame.mixer.music.get_busy():
                            pygame.time.delay(100)
                    try:
                        pygame.mixer.music.load(self.music[track])
                        pygame.mixer.music.set_volume(self.music_volume)
                        pygame.mixer.music.play(-1)
                        self.current_music = track
                    except pygame.error as e:
                        print(f"Error loading music {track}: {e}")
                        # Fallback: print music description if music is not present
                        for track_data in self.music_data.get("tracks", []):
                            if track_data.get("track_id") == track:
                                self.display_description(track_data.get('title', 'Unknown track'))
                                return
            else:
                # Fallback: print music description if music is not present
                for track_data in self.music_data.get("tracks", []):
                    if track_data.get("track_id") == track:
                        self.display_description(track_data.get('title', 'Unknown track'))
                        return
    def display_description(self, text):
         self.game.ui.fast_message(text, 0.5, clear_screen=False)

    def mute_music(self):
        if not self.music_muted:
            self.music_muted = True
            pygame.mixer.music.set_volume(0.0)

    def unmute_music(self):
        if self.music_muted:
            self.music_muted = False
            pygame.mixer.music.set_volume(self.music_volume)

    def mute_sound_effects(self):
        if not self.sound_effects_muted:
            self.sound_effects_muted = True
            for sound in self.sounds.values():
                sound.set_volume(0.0)

    def unmute_sound_effects(self):
        if self.sound_effects_muted:
            self.sound_effects_muted = False
            for sound in self.sounds.values():
                sound.set_volume(self.sound_effects_volume)

    def set_music_volume(self, volume):
        self.music_volume = volume
        if not self.music_muted:
            pygame.mixer.music.set_volume(volume)

    def set_sound_effects_volume(self, volume):
        self.sound_effects_volume = volume
        if not self.sound_effects_muted:
            for sound in self.sounds.values():
                sound.set_volume(volume)

    def stop_all(self):
        for i in range(pygame.mixer.get_num_channels()):
            channel = pygame.mixer.Channel(i)
            channel.stop()
        pygame.mixer.music.stop()
        self.current_music = None