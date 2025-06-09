# cosmic_drifter_py/game_objects.py
import copy
from config import SYSTEMS_CONFIG, INITIAL_REACTOR_OUTPUT, SHIP_RADIUS, SHIP_COLOR, CANVAS_WIDTH, CANVAS_HEIGHT, BASE_SHIP_SPEED, USER_SHIP_IMAGE_URL

class PlayerResources:
    def __init__(self, fuel=100, scrap=50, hull=100, shield_points=0, max_shield_layers=0):
        self.fuel = fuel
        self.scrap = scrap
        self.hull = hull
        self.shield_points = shield_points
        self.max_shield_layers = max_shield_layers

class ShipSystem:
    def __init__(self, name, max_power, power, level, max_level, upgrade_cost_base, upgrade_cost_multiplier, base_effect, effect_per_power):
        self.name = name
        self.max_power = max_power
        self.power = power
        self.level = level
        self.max_level = max_level
        self.upgrade_cost_base = upgrade_cost_base
        self.upgrade_cost_multiplier = upgrade_cost_multiplier
        self.base_effect = base_effect
        self.effect_per_power = effect_per_power

class ShipState:
    def __init__(self):
        self.x = CANVAS_WIDTH / 2
        self.y = CANVAS_HEIGHT / 2
        self.radius = SHIP_RADIUS # For procedural drawing
        self.color = SHIP_COLOR # For procedural drawing
        self.target_beacon_id = None # Store ID, actual object resolved in game_logic
        self.current_beacon_id = None # Store ID
        self.is_moving = False
        self.angle = 0.0 # General orientation angle for the ship on the map

        # Sprite related - Pygame will handle image loading
        self.map_sprite_path = USER_SHIP_IMAGE_URL # Path to be used by Pygame loader
        self.map_sprite_loaded = False # Will be set by Pygame loading success
        self.map_sprite = None # Will hold the Pygame Surface object

        # Systems - deepcopy to avoid modifying the config dict
        self.systems = {key: ShipSystem(**copy.deepcopy(value)) for key, value in SYSTEMS_CONFIG.items()}
        self.reactor_output = INITIAL_REACTOR_OUTPUT
        self.power_used = 0 # Will be calculated

        # System View specific state
        self.system_view_ship_x = 0
        self.system_view_ship_y = 0
        self.system_view_ship_target_x = 0
        self.system_view_ship_target_y = 0
        self.is_flying_into_system_view = False
        self.system_view_ship_angle = 0.0

        self.current_speed = BASE_SHIP_SPEED # Initial speed

class SolarSystem:
    def __init__(self, name, stars, planets, starfield_data, has_nebula, nebula_details):
        self.name = name
        self.stars = stars # List of star type dicts
        self.planets = planets # List of planet dicts
        self.starfield_data = starfield_data # List of dicts for stars in system view
        self.has_nebula = has_nebula
        self.nebula_details = nebula_details # Dict or None

class Beacon:
    def __init__(self, id, x, y, radius, color, solar_system, is_endpoint=False):
        self.id = id
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color # Will be Pygame color
        self.connections = [] # List of connected beacon IDs
        self.solar_system = solar_system # SolarSystem object
        self.visited = False
        self.is_endpoint = is_endpoint

class MapDecoration:
    def __init__(self, type, x, y, radius_x, radius_y, rotation, color):
        self.type = type
        self.x = x
        self.y = y
        self.radius_x = radius_x
        self.radius_y = radius_y
        self.rotation = rotation
        self.color = color # Pygame color/tuple

class GameState:
    def __init__(self):
        self.beacons = [] # List of Beacon objects
        self.ship = ShipState()
        self.player_resources = PlayerResources()
        self.hovered_beacon_id = None # Store ID
        self.map_decorations = [] # List of MapDecoration objects
        self.endpoint_beacon_id = None
        self.game_won = False
        self.game_over = False # Added for clarity
        self.event_log_messages = [] # List of (type, message) tuples
        self.ui_button_rects = {} # Store active UI button rects and their actions/keys
        self.view_mode = 'map' # Default view mode
        self.is_modal_active = False
        self.current_modal_data = None # Will store {'id':..., 'title': ..., 'text': ..., 'choices': [{'text':..., 'action_key':...}]}
        self.system_event_triggered_this_visit = False # Ensures event triggers once per system visit
        self.particles = []
        # For fade transitions:
        self.is_fading = False # True if a fade is active
        self.fade_alpha = 0 # Current alpha of the fade overlay (0-255)
        self.fade_target_alpha = 255 # Target alpha (255 for fade out, 0 for fade in)
        self.fade_speed = 15 # Alpha change per frame (approx)
        self.on_fade_complete_action = None # Function to call when fade out (to black) is done
        self.next_view_after_fade = None # View to switch to after fade cycle

    def get_beacon_by_id(self, beacon_id):
        if beacon_id is None:
            return None
        for beacon in self.beacons:
            if beacon.id == beacon_id:
                return beacon
        return None

    @property
    def current_beacon(self):
        return self.get_beacon_by_id(self.ship.current_beacon_id)

    @current_beacon.setter
    def current_beacon(self, beacon_object):
        if beacon_object:
            self.ship.current_beacon_id = beacon_object.id
        else:
            self.ship.current_beacon_id = None

    @property
    def target_beacon(self):
        return self.get_beacon_by_id(self.ship.target_beacon_id)

    @target_beacon.setter
    def target_beacon(self, beacon_object):
        if beacon_object:
            self.ship.target_beacon_id = beacon_object.id
        else:
            self.ship.target_beacon_id = None

    @property
    def hovered_beacon(self):
        return self.get_beacon_by_id(self.hovered_beacon_id)

    @hovered_beacon.setter
    def hovered_beacon(self, beacon_object):
        if beacon_object:
            self.hovered_beacon_id = beacon_object.id
        else:
            self.hovered_beacon_id = None

# Example of how gameState would be initialized in main.py or game_logic.py
# current_game_state = GameState()
# current_game_state.ship.x = CONFIG.CANVAS_WIDTH / 2 # Initial ship position (example)
# ... other initializations ...

import random
# import pygame # For Vector2 if used, or simple tuple math. Not strictly needed for this Particle impl.

class Particle:
    def __init__(self, x, y, vx, vy, radius, color, lifespan):
        self.x = x
        self.y = y
        # self.pos = pygame.math.Vector2(x,y) # Alternative using Vector2
        self.vx = vx
        self.vy = vy
        # self.vel = pygame.math.Vector2(vx,vy)
        self.radius = radius
        self.color = color
        self.lifespan = lifespan # in milliseconds or frames
        self.age = 0

    def update(self, dt_seconds): # dt_seconds is delta time in seconds
        self.x += self.vx * dt_seconds
        self.y += self.vy * dt_seconds
        # self.pos += self.vel * dt_seconds
        self.age += dt_seconds * 1000 # Convert dt_seconds to ms for age comparison
        self.radius -= 2.0 * dt_seconds # Shrink a bit, increased rate for visibility
        if self.radius < 0: self.radius = 0

    def is_alive(self):
        return self.age < self.lifespan and self.radius > 0
