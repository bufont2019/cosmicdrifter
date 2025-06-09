# cosmic_drifter_py/config.py

# Canvas and Map
CANVAS_WIDTH = 1000
CANVAS_HEIGHT = 500
NUM_BEACONS = 80
BEACON_RADIUS = 8
BEACON_COLOR = '#4ade80' # Consider Pygame color format (r,g,b) later
BEACON_HOVER_COLOR = '#86efac'
ENDPOINT_BEACON_COLOR = '#bf3eff'
ENDPOINT_PULSE_COLOR = 'rgba(191, 62, 255, 0.5)' # Pygame handles alpha
CONNECTION_LINE_COLOR = 'rgba(100,116,139,0.2)'
MIN_BEACON_DISTANCE = 35
PADDING = 30 # From JS: const padding=30;

# Ship
SHIP_COLOR = '#facc15'
SHIP_RADIUS = 12 # For procedural drawing if sprite fails
BASE_SHIP_SPEED = 1.0 # Ensure float for calculations
SHIP_SPRITE_WIDTH = 50
SHIP_SPRITE_HEIGHT = 50
USER_SHIP_IMAGE_URL = "https://i.ibb.co/7Nr18nN2/Gemini.png" # Will be handled by asset loading

# Resources & Systems
FUEL_PER_JUMP = 5
INITIAL_REACTOR_OUTPUT = 5
MAX_PLANETS_PER_SYSTEM = 5
MIN_PLANETS_PER_SYSTEM = 0

# Systems configuration (will be used to initialize ship's systems)
SYSTEMS_CONFIG = {
    'engines': { 'name': "Engines", 'max_power': 3, 'power': 1, 'level': 1, 'max_level': 5, 'upgrade_cost_base': 20, 'upgrade_cost_multiplier': 1.5, 'base_effect': 0.5, 'effect_per_power': 0.5 },
    'shields': { 'name': "Shields", 'max_power': 2, 'power': 0, 'level': 1, 'max_level': 5, 'upgrade_cost_base': 25, 'upgrade_cost_multiplier': 1.6, 'base_effect': 0, 'effect_per_power': 1 },
    'weapons': { 'name': "Weapons", 'max_power': 2, 'power': 0, 'level': 1, 'max_level': 5, 'upgrade_cost_base': 30, 'upgrade_cost_multiplier': 1.7, 'base_effect': 0, 'effect_per_power': 1 }
}
CURRENT_SHIP_SPEED = BASE_SHIP_SPEED # Initial value, will be updated by engine power

# System View
NUM_SYSTEM_VIEW_STARS = 150
NEBULA_CHANCE = 0.4
SYSTEM_VIEW_SHIP_FLY_IN_SPEED = 3
NUM_MAP_NEBULAE = 5 # For the main map

# Planet Generation
PLANET_TYPES = [
    {'name':"Terran", 'color':"#60a5fa", 'keywords':"continents, oceans, atmosphere"},
    {'name':"Gas Giant", 'color':"#f97316", 'keywords':"swirling bands, rings, massive"},
    {'name':"Ice Giant", 'color':"#a5f3fc", 'keywords':"icy, pale blue, distant"},
    {'name':"Volcanic", 'color':"#ef4444", 'keywords':"lava flows, magma, smoke plumes"},
    {'name':"Barren Rock", 'color':"#a8a29e", 'keywords':"craters, desolate, rocky"},
    {'name':"Oceanic", 'color':"#22d3ee", 'keywords':"global ocean, islands, deep blue"},
    {'name':"Desert", 'color':"#f59e0b", 'keywords':"sand dunes, arid, canyons"},
    {'name':"Frozen", 'color':"#e0f2fe", 'keywords':"ice sheets, glaciers, frozen tundra"}
]
PLANET_SIZES_MAP = { "Small": 8, "Medium": 12, "Large": 18, "Gigantic": 25 }
NAME_PREFIXES = ["Alpha","Beta","Gamma","New","Prime","Neo","Nova","Terra","Xylo","Zeta"]
NAME_SUFFIXES = ["Centauri","Prime","Minor","Major","Secundus","Colony","Outpost","Reach","Haven","B","C","D"]
STAR_NAMES_ADJ = ["Crimson","Azure","Golden","Emerald","Silver","Whispering","Forgotten","Shining","Distant"]
STAR_NAMES_NOUN = ["Sun","Star","Nebula","Void","Expanse","Cluster","Core","Ridge","Passage","Gate"]
STAR_TYPES = [
    { 'name': "Yellow Dwarf", 'color': "#fffde7", 'radius': 35, 'coronaColor': "rgba(255, 235, 59, 0.2)", 'flareColor': "rgba(255, 200, 0, 0.7)", 'flareIntensity': 0.5 },
    { 'name': "Red Giant", 'color': "#ffccbc", 'radius': 55, 'coronaColor': "rgba(255, 82, 82, 0.25)", 'flareColor': "rgba(255, 100, 50, 0.6)", 'flareIntensity': 0.7 },
    { 'name': "Blue Supergiant", 'color': "#bbdefb", 'radius': 65, 'coronaColor': "rgba(66, 165, 245, 0.3)", 'flareColor': "rgba(150, 200, 255, 0.8)", 'flareIntensity': 1.0 },
    { 'name': "White Dwarf", 'color': "#eceff1", 'radius': 18, 'coronaColor': "rgba(207, 216, 220, 0.2)", 'flareColor': "rgba(220, 220, 255, 0.5)", 'flareIntensity': 0.3 },
    { 'name': "Neutron Star", 'color': "#e1bee7", 'radius': 8, 'coronaColor': "rgba(171, 71, 188, 0.4)", 'flareColor': "rgba(200, 150, 220, 0.9)", 'flareIntensity': 1.2 },
    { 'name': "Pulsar", 'color': "#f8bbd0", 'radius': 12, 'coronaColor': "rgba(240, 98, 146, 0.35)", 'flareColor': "rgba(255, 150, 180, 0.7)", 'flareIntensity': 0.8, 'isPulsar': True }
]

# Max connections per beacon (from connectBeacons logic)
MAX_CONNECTIONS_PER_BEACON = 4

# Audio - Placeholder, will need specific Pygame implementation
# TONE_BPM = 80 # Example

# Colors for Pygame (RGB or RGBA tuples)
# These will be converted from hex/rgba strings as needed.
# Example: PYGAME_BEACON_COLOR = (74, 222, 128)
# This conversion will be handled in graphics.py or when colors are used.
