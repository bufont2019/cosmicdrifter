# cosmic_drifter_py/audio.py
import pygame
import os

SOUND_EFFECTS_PATHS = {
    'jump': 'assets/sounds/jump.wav',
    'event_alert': 'assets/sounds/event_alert.wav',
    'positive_feedback': 'assets/sounds/positive_feedback.wav',
    'negative_feedback': 'assets/sounds/negative_feedback.wav',
}

MUSIC_PATHS = {
    'main_ambience': 'assets/sounds/main_ambience.ogg',
    'system_ambience': 'assets/sounds/system_ambience.ogg',
}

_sound_effects = {}
_current_music_key = None
_mixer_initialized = False

def init_mixer():
    global _mixer_initialized
    if _mixer_initialized:
        return True
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        print("Pygame mixer initialized.")
        _mixer_initialized = True
        return True
    except pygame.error as e:
        print(f"Error initializing pygame.mixer: {e}. Sound will be disabled.")
        # pygame.mixer.quit() # Don't quit if it failed init, get_init() will be false
        _mixer_initialized = False
        return False

def load_sounds():
    if not _mixer_initialized: # Use our flag
        print("Mixer not initialized. Cannot load sounds.")
        return

    # Adjust paths to be relative to this file's location if needed,
    # or assume execution from project root.
    # For now, 'assets/sounds/...' assumes main.py is in project root.
    # If main.py is in 'cosmic_drifter_py/', paths should be '../assets/sounds/...'
    # Let's assume the paths are correct for the execution context of main.py
    # The script create_dummy_sounds.py used 'cosmic_drifter_py/assets/sounds'.
    # So these paths need to reflect that if main.py is in cosmic_drifter_py.
    # Paths are relative to the execution directory of main.py (expected to be cosmic_drifter_py/)
    # and dummy sounds were created in cosmic_drifter_py/assets/sounds/

    for key, path in SOUND_EFFECTS_PATHS.items(): # Use original paths
        if not os.path.exists(path): # os.path.exists resolves from CWD
            print(f"Warning: Sound file not found: {path}")
            _sound_effects[key] = None
            continue
        try:
            _sound_effects[key] = pygame.mixer.Sound(path)
        except pygame.error as e:
            print(f"Error loading sound {key} at {path}: {e}")
            _sound_effects[key] = None
    print("Sound effects loading process completed.")

    for key, path in MUSIC_PATHS.items(): # Use original paths
        if not os.path.exists(path):
            print(f"Warning: Music file not found: {path}")
    print("Music paths check completed.")


def play_sound(key, loops=0, volume=1.0):
    if not _mixer_initialized: return
    if key in _sound_effects and _sound_effects[key]:
        sound = _sound_effects[key]
        sound.set_volume(volume)
        sound.play(loops=loops)
    else:
        if key not in _sound_effects:
             print(f"Sound effect '{key}' is not defined in SOUND_EFFECTS_PATHS.")


def play_music(key, loops=-1, volume=0.7):
    global _current_music_key
    if not _mixer_initialized: return

    path_to_load = MUSIC_PATHS.get(key) # Use original MUSIC_PATHS

    if not path_to_load or not os.path.exists(path_to_load):
        print(f"Music track '{key}' not found at {path_to_load or MUSIC_PATHS.get(key, 'undefined path')}.")
        return

    try:
        if _current_music_key == key and pygame.mixer.music.get_busy():
            return

        pygame.mixer.music.load(path_to_load)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loops=loops)
        _current_music_key = key
        print(f"Playing music: {key}")
    except pygame.error as e:
        print(f"Error playing music {key}: {e}")
        _current_music_key = None

def stop_music():
    global _current_music_key
    if not _mixer_initialized: return
    if pygame.mixer.music.get_busy(): # Check if music is actually playing
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
    _current_music_key = None
    # print("Music stopped.") # Can be noisy if called frequently

def switch_ambience(new_ambience_key):
    if not _mixer_initialized: return

    # Check if already playing the target ambience and music is busy
    if _current_music_key == new_ambience_key and pygame.mixer.music.get_busy():
        return

    # If different music is playing, or no music, or target music stopped
    # print(f"Switching ambience to {new_ambience_key}. Current: {_current_music_key}")
    stop_music() # Stop current music (if any)
    play_music(new_ambience_key, loops=-1, volume=0.5)
