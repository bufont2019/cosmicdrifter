import pygame
import math
import os # For path checking in load_sprite
import random # For procedural details like flares

from config import (CANVAS_WIDTH, CANVAS_HEIGHT, CONNECTION_LINE_COLOR,
                    BEACON_COLOR, BEACON_HOVER_COLOR, ENDPOINT_BEACON_COLOR, ENDPOINT_PULSE_COLOR,
                    SHIP_SPRITE_WIDTH, SHIP_SPRITE_HEIGHT, SHIP_COLOR)
from game_objects import Beacon # For type hinting

# --- Color Parsing (existing) ---
def parse_color(color_str):
    if isinstance(color_str, tuple): return color_str
    if color_str.startswith('#'):
        hex_color = color_str.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    elif color_str.startswith('rgba'):
        parts = color_str.replace('rgba(', '').replace(')', '').split(',')
        r, g, b = [int(p.strip()) for p in parts[:3]]
        a = float(parts[3].strip())
        return (r, g, b, int(a * 255))
    elif color_str.startswith('rgb'):
        parts = color_str.replace('rgb(', '').replace(')', '').split(',')
        return tuple(int(p.strip()) for p in parts)
    try: return pygame.Color(color_str)
    except ValueError: print(f"Warning: Could not parse color: {color_str}. Defaulting to black."); return (0,0,0)

PYGAME_SHIP_COLOR = parse_color(SHIP_COLOR) # Used by procedural ship

# --- Sprite Loading Framework ---
_loaded_sprites = {}

def load_sprite(path, size=None):
    # Paths are relative to where main.py is run (cosmic_drifter_py/)
    # Dummy sprites were created in cosmic_drifter_py/assets/images/
    # So, path like 'assets/images/beacon_normal.png' is correct.
    if path in _loaded_sprites:
        return _loaded_sprites[path]

    if not os.path.exists(path):
        print(f"Warning: Sprite file not found: {path}")
        return None
    try:
        image = pygame.image.load(path).convert_alpha()
        if size:
            image = pygame.transform.scale(image, size)
        _loaded_sprites[path] = image
        print(f"Loaded sprite: {path}")
        return image
    except pygame.error as e:
        print(f"Error loading sprite {path}: {e}")
        return None

_beacon_sprite_paths = {
    'normal': 'assets/images/beacon_normal.png', 'hover': 'assets/images/beacon_hover.png',
    'endpoint': 'assets/images/beacon_endpoint.png', 'visited': 'assets/images/beacon_visited.png',
    'current': 'assets/images/beacon_normal.png'
}
_beacon_sprites = {}

def preload_beacon_sprites():
    print("Preloading beacon sprites...")
    for key, path in _beacon_sprite_paths.items():
        size = (16,16)
        if key == 'hover': size = (18,18)
        elif key == 'endpoint': size = (20,20)
        _beacon_sprites[key] = load_sprite(path, size)
        if not _beacon_sprites[key]: print(f"Beacon sprite for {key} failed, will use procedural.")

_planet_sprite_paths = {
    "Terran": "assets/images/planet_terran.png", "Gas Giant": "assets/images/planet_gas_giant.png",
    "Volcanic": "assets/images/planet_volcanic.png",
    # TODO: Add paths for Ice Giant, Barren Rock, Oceanic, Desert, Frozen if dummy sprites exist
}
_planet_sprites = {}

def preload_planet_sprites():
    print("Preloading planet sprites...")
    for type_name, path in _planet_sprite_paths.items():
        _planet_sprites[type_name] = load_sprite(path) # Load base, scale later if needed
        if not _planet_sprites[type_name]: print(f"Planet sprite for {type_name} failed.")


# --- Map Element Drawing (Beacons, Ship, Decorations) ---
def draw_starfield(screen): # (Existing)
    screen.fill((0, 0, 10))

def draw_map_decorations(screen, decorations): # (Existing, ensure parse_color is robust)
    for deco in decorations:
        if deco.type == 'nebula':
            nebula_surface = pygame.Surface((deco.radius_x * 2, deco.radius_y * 2), pygame.SRCALPHA)
            nebula_surface.fill((0,0,0,0))
            ellipse_color = parse_color(deco.color) # deco.color is string from game_logic
            if len(ellipse_color) == 3: ellipse_color = (*ellipse_color, 100) # Default alpha if RGB
            pygame.draw.ellipse(nebula_surface, ellipse_color, nebula_surface.get_rect())
            screen.blit(nebula_surface, (deco.x - deco.radius_x, deco.y - deco.radius_y))

# New draw_beacons using sprites
def draw_beacons(screen, game_state): # Replaces old draw_beacons
    drawn_connections = set()
    for beacon in game_state.beacons:
        for connected_beacon_id in beacon.connections:
            connection_key = tuple(sorted((beacon.id, connected_beacon_id)))
            if connection_key not in drawn_connections:
                cb = game_state.get_beacon_by_id(connected_beacon_id)
                if cb:
                    line_color_tuple = parse_color(CONNECTION_LINE_COLOR)
                    pygame.draw.line(screen, line_color_tuple[:3], (beacon.x, beacon.y), (cb.x, cb.y), 1)
                drawn_connections.add(connection_key)

    for beacon in game_state.beacons:
        sprite_key = 'normal'
        if beacon.is_endpoint: sprite_key = 'endpoint'
        elif game_state.ship.current_beacon_id == beacon.id: sprite_key = 'current'
        elif beacon.visited: sprite_key = 'visited'
        if game_state.hovered_beacon_id == beacon.id: sprite_key = 'hover'

        sprite_to_draw = _beacon_sprites.get(sprite_key)

        if sprite_to_draw:
            if beacon.is_endpoint and (pygame.time.get_ticks() // 200 % 2 == 0):
                 glow_radius = sprite_to_draw.get_width()
                 glow_color = (*parse_color(ENDPOINT_PULSE_COLOR)[:3], 100)
                 temp_glow_surf = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
                 pygame.draw.circle(temp_glow_surf, glow_color, (glow_radius, glow_radius), glow_radius)
                 screen.blit(temp_glow_surf, (beacon.x - glow_radius, beacon.y - glow_radius))
            screen.blit(sprite_to_draw, (beacon.x - sprite_to_draw.get_width()//2, beacon.y - sprite_to_draw.get_height()//2))
        else: # Fallback procedural
            color_str = BEACON_COLOR
            if beacon.is_endpoint: color_str = ENDPOINT_BEACON_COLOR
            elif game_state.hovered_beacon_id == beacon.id: color_str = BEACON_HOVER_COLOR
            elif beacon.visited: color_str = '#a16207' # Original JS color for visited
            if game_state.ship.current_beacon_id == beacon.id and not beacon.is_endpoint: color_str = '#f59e0b' # JS current
            pygame.draw.circle(screen, parse_color(color_str), (int(beacon.x),int(beacon.y)), beacon.radius)
            pygame.draw.circle(screen, parse_color('#1e293b'), (int(beacon.x),int(beacon.y)), beacon.radius, 1)


def load_ship_sprite(ship_state): # (Existing - ensure path is correct)
    if not ship_state.map_sprite_path: print("Ship sprite path not set."); ship_state.map_sprite_loaded = False; return
    try:
        sprite = pygame.image.load(ship_state.map_sprite_path).convert_alpha()
        ship_state.map_sprite = pygame.transform.scale(sprite, (SHIP_SPRITE_WIDTH, SHIP_SPRITE_HEIGHT))
        ship_state.map_sprite_loaded = True; print(f"Ship sprite '{ship_state.map_sprite_path}' loaded.")
    except pygame.error as e:
        print(f"Error loading ship sprite '{ship_state.map_sprite_path}': {e}")
        ship_state.map_sprite_loaded = False; ship_state.map_sprite = None

def draw_ship(screen, ship): # (Existing - procedural part uses PYGAME_SHIP_COLOR)
    if ship.map_sprite_loaded and ship.map_sprite:
        rotated_sprite = pygame.transform.rotate(ship.map_sprite, -ship.angle)
        new_rect = rotated_sprite.get_rect(center = (int(ship.x), int(ship.y)))
        screen.blit(rotated_sprite, new_rect.topleft)
    else:
        angle_rad = math.radians(ship.angle); w = SHIP_SPRITE_WIDTH/2.5; h = SHIP_SPRITE_HEIGHT/2.5
        points = [(0,-h),(w*0.6,-h*0.3),(w*0.6,h*0.5),(0,h*0.8),(-w*0.6,h*0.5),(-w*0.6,-h*0.3)]
        r_pts = [(int(ship.x + px*math.cos(angle_rad)-py*math.sin(angle_rad)),
                  int(ship.y + px*math.sin(angle_rad)+py*math.cos(angle_rad))) for px,py in points]
        pygame.draw.polygon(screen, PYGAME_SHIP_COLOR, r_pts)
        if ship.is_moving: # Flame
            fh=h*0.5;fw=w*0.4;fp=[(0,h*0.8+2),(fw,h*0.8+fh),(-fw,h*0.8+fh)]
            rf_pts = [(int(ship.x+px*math.cos(angle_rad)-py*math.sin(angle_rad)),
                       int(ship.y+px*math.sin(angle_rad)+py*math.cos(angle_rad))) for px,py in fp]
            fl_col = (255,200,0) if pygame.time.get_ticks()%200 < 100 else (255,165,0)
            pygame.draw.polygon(screen, fl_col, rf_pts)

# --- Particle Drawing ---
def draw_particles(screen, particles):
    for p in particles:
        if p.is_alive():
            alpha = max(0, 255 * (1 - (p.age / p.lifespan)))
            current_color_tuple = p.color # Assuming p.color is already a tuple (r,g,b)
            final_color = (*current_color_tuple[:3], int(alpha))

            if final_color[3] > 0 and p.radius > 0: # Visible
                # Simple circle drawing for particles. Alpha blending needs SRCALPHA on screen or temp surface.
                # If screen itself is not SRCALPHA, this won't blend perfectly.
                # For better alpha, draw each particle on its own small SRCALPHA surface.
                particle_surf = pygame.Surface((int(p.radius*2), int(p.radius*2)), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, final_color, (int(p.radius), int(p.radius)), int(p.radius))
                screen.blit(particle_surf, (int(p.x - p.radius), int(p.y - p.radius)))


# --- System View Drawing (Stars, Planets, Ship) ---
def draw_system_starfield(screen, width, height, starfield_data): # (Existing)
    for star_point in starfield_data:
        px, py = star_point['x']*width, star_point['y']*height
        alpha = star_point.get('alpha',0.8)*255; color = (255,255,255,int(alpha))
        star_surf = pygame.Surface((star_point['radius']*2,star_point['radius']*2), pygame.SRCALPHA)
        pygame.draw.circle(star_surf,color,(star_point['radius'],star_point['radius']),star_point['radius'])
        screen.blit(star_surf,(px-star_point['radius'],py-star_point['radius']))

def draw_system_nebula(screen, width, height, nebula_details): # (Existing)
    if not nebula_details: return
    num_layers = 3+random.randint(0,2)
    for i in range(num_layers):
        ox,oy = (random.random()-0.5)*nebula_details['radius']*0.5, (random.random()-0.5)*nebula_details['radius']*0.5
        lr = nebula_details['radius']*(0.7+random.random()*0.6); cx,cy = nebula_details['x']*width+ox, nebula_details['y']*height+oy
        col_str = nebula_details['color1'] if i%2==0 else nebula_details['color2']; pcol = parse_color(col_str)
        if not pcol or len(pcol)<4: pcol=(pcol[0],pcol[1],pcol[2],50) if pcol else (100,0,100,50)
        neb_surf = pygame.Surface((lr*2,lr*2),pygame.SRCALPHA); pygame.draw.circle(neb_surf,pcol,(lr,lr),lr)
        screen.blit(neb_surf,(cx-lr,cy-lr))

def draw_solar_flares(screen,star_x,star_y,star_radius,flare_color_str,flare_intensity): # (Existing)
    num_flares=random.randint(2,int(2+3*flare_intensity)); flare_color=parse_color(flare_color_str)
    if not flare_color or len(flare_color)<3: flare_color=(255,200,0)
    for _ in range(num_flares):
        angle=random.uniform(0,2*math.pi); length=star_radius*(0.5+random.random()*1.5*flare_intensity)
        thickness=int(1+random.random()*2*flare_intensity)
        sx,sy = star_x+math.cos(angle)*star_radius*0.8, star_y+math.sin(angle)*star_radius*0.8
        ex,ey = star_x+math.cos(angle)*(star_radius+length), star_y+math.sin(angle)*(star_radius+length)
        fcol = (*flare_color[:3],int(random.uniform(100,200))) if len(flare_color)==4 else (*flare_color,int(random.uniform(100,200)))
        pygame.draw.line(screen,fcol[:3],(sx,sy),(ex,ey),thickness)

def draw_star_in_system(screen, star_data, center_x, center_y): # (Existing)
    star_color=parse_color(star_data['color']); corona_color=parse_color(star_data['coronaColor'])
    if corona_color and len(corona_color)==4:
        cr = star_data['radius']*1.7*(0.8+random.random()*0.4)
        cs = pygame.Surface((cr*2,cr*2),pygame.SRCALPHA); pygame.draw.circle(cs,corona_color,(cr,cr),cr)
        screen.blit(cs,(center_x-cr,center_y-cr))
    pygame.draw.circle(screen,star_color,(center_x,center_y),star_data['radius'])
    if random.random()<0.1: draw_solar_flares(screen,center_x,center_y,star_data['radius'],star_data['flareColor'],star_data['flareIntensity'])
    if star_data.get('isPulsar',False) and (pygame.time.get_ticks()//500%2==0):
        pr=star_data['radius']*(1.5+random.random()*0.5); pc=(255,255,255,30)
        ps=pygame.Surface((pr*2,pr*2),pygame.SRCALPHA); pygame.draw.circle(ps,pc,(pr,pr),pr)
        screen.blit(ps,(center_x-pr,center_y-pr))

# New draw_planet_in_system using sprites
def draw_planet_in_system(screen, planet_data, orbit_center_x, orbit_center_y, orbit_radius, planet_angle): # Replaces old
    planet_x = orbit_center_x + orbit_radius * math.cos(planet_angle)
    planet_y = orbit_center_y + orbit_radius * math.sin(planet_angle)
    pygame.draw.circle(screen, (100,100,100), (int(orbit_center_x), int(orbit_center_y)), int(orbit_radius), 1)

    sprite_to_use = _planet_sprites.get(planet_data['type'])
    planet_render_radius = planet_data['radius']

    if sprite_to_use:
        scaled_size = (int(planet_render_radius * 2), int(planet_render_radius * 2))
        try:
            # Consider caching scaled sprites if performance becomes an issue
            scaled_sprite = pygame.transform.smoothscale(sprite_to_use, scaled_size) # smoothscale looks better
            screen.blit(scaled_sprite, (planet_x - planet_render_radius, planet_y - planet_render_radius))
        except Exception as e: # Fallback if scaling fails
            print(f"Error scaling planet sprite {planet_data['type']}: {e}")
            pygame.draw.circle(screen, parse_color(planet_data['color']), (int(planet_x), int(planet_y)), int(planet_render_radius))
    else:
        pygame.draw.circle(screen, parse_color(planet_data['color']), (int(planet_x), int(planet_y)), int(planet_render_radius))

    if planet_data.get('hasRings', False): # Simplified rings
        ring_color = (180, 180, 160, 60) # Fainter and slightly different color
        ring_rect_outer = pygame.Rect(0,0, planet_render_radius * 4, planet_render_radius * 2)
        ring_rect_outer.center = (int(planet_x), int(planet_y))

        ring_surf = pygame.Surface(ring_rect_outer.size, pygame.SRCALPHA)
        pygame.draw.ellipse(ring_surf, ring_color, ring_surf.get_rect(), 0) # Outer ellipse
        # Create inner transparent ellipse to punch out the center
        ring_rect_inner = pygame.Rect(0,0, planet_render_radius*2.5, planet_render_radius*1.25)
        ring_rect_inner.center = (ring_rect_outer.width//2, ring_rect_outer.height//2)
        pygame.draw.ellipse(ring_surf, (0,0,0,0), ring_rect_inner, 0) # Punch out center with full transparency

        # Tilt effect (approximate by rotating the surface)
        # angle_degrees = planet_data.get('ringTilt',0) * (180/math.pi) # Convert radians to degrees
        # tilted_ring_surf = pygame.transform.rotate(ring_surf, angle_degrees)
        # screen.blit(tilted_ring_surf, tilted_ring_surf.get_rect(center=(int(planet_x), int(planet_y))))
        screen.blit(ring_surf, ring_rect_outer.topleft) # Non-tilted for now


# --- Parallax Starfield ---
NUM_STARFIELD_LAYERS = 3
STARFIELD_LAYER_SPEEDS = [20.0, 40.0, 70.0] # Relative speeds for layers (pixels per second), increased for visibility
STARFIELD_STARS_PER_LAYER = [50, 40, 30] # Number of stars per layer
STARFIELD_LAYER_COLORS = [ # Progressively brighter/larger for closer layers
    ((100,100,120), 1), # Faint, small stars (color, radius)
    ((150,150,180), 1.5),
    ((200,200,220), 2)
]
_starfield_layers_data = [] # List of lists, each sublist contains [x, y, color_idx]

def initialize_parallax_starfield(width, height):
    global _starfield_layers_data
    _starfield_layers_data = []
    for i in range(NUM_STARFIELD_LAYERS):
        layer = []
        for _ in range(STARFIELD_STARS_PER_LAYER[i]):
            layer.append([
                random.uniform(0, width), # x
                random.uniform(0, height), # y
                i # color/radius index from STARFIELD_LAYER_COLORS
            ])
        _starfield_layers_data.append(layer)

def draw_parallax_starfield(screen, dt_seconds): # dt_seconds for smooth movement
    if not _starfield_layers_data or len(_starfield_layers_data) != NUM_STARFIELD_LAYERS : # Initialize if empty or layer count changed
        initialize_parallax_starfield(screen.get_width(), screen.get_height())

    for i, layer in enumerate(_starfield_layers_data):
        speed = STARFIELD_LAYER_SPEEDS[i]
        color, radius = STARFIELD_LAYER_COLORS[i]

        for star_data in layer:
            star_data[0] -= speed * dt_seconds

            if star_data[0] < 0:
                star_data[0] = screen.get_width() + random.uniform(0, 10)
                star_data[1] = random.uniform(0, screen.get_height())

            alpha = 128 + math.sin(pygame.time.get_ticks() * 0.001 + star_data[0]) * 127
            star_color_with_alpha = (*color, int(alpha))

            star_surf = pygame.Surface((int(radius*2), int(radius*2)), pygame.SRCALPHA) # Ensure int for Surface size
            pygame.draw.circle(star_surf, star_color_with_alpha, (int(radius), int(radius)), int(radius)) # Ensure int for draw params
            screen.blit(star_surf, (int(star_data[0] - radius), int(star_data[1] - radius)))


# --- Fade Transitions ---
def draw_fade_transition(screen, game_state):
    if game_state.is_fading:
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, game_state.fade_alpha))
        screen.blit(overlay, (0,0))


def draw_ship_on_system_view(screen, ship_state): # (Existing)
    if ship_state.map_sprite_loaded and ship_state.map_sprite:
        rot_sprite = pygame.transform.rotate(ship_state.map_sprite, -ship_state.system_view_ship_angle)
        n_rect = rot_sprite.get_rect(center=(int(ship_state.system_view_ship_x),int(ship_state.system_view_ship_y)))
        screen.blit(rot_sprite,n_rect.topleft)
    else:
        angle_rad=math.radians(ship_state.system_view_ship_angle);w=SHIP_SPRITE_WIDTH/2.5;h=SHIP_SPRITE_HEIGHT/2.5
        pts=[(0,-h),(w*0.6,-h*0.3),(w*0.6,h*0.5),(0,h*0.8),(-w*0.6,h*0.5),(-w*0.6,-h*0.3)]
        r_pts=[(int(ship_state.system_view_ship_x+px*math.cos(angle_rad)-py*math.sin(angle_rad)),
                int(ship_state.system_view_ship_y+px*math.sin(angle_rad)+py*math.cos(angle_rad))) for px,py in pts]
        pygame.draw.polygon(screen,parse_color(ship_state.color),r_pts)

def draw_solar_system_view(screen, game_state): # (Existing - calls new draw_planet_in_system)
    current_beacon = game_state.current_beacon
    if not current_beacon or not current_beacon.solar_system:
        ef = pygame.font.Font(None,20);ets=ef.render("Error: No solar system data.",True,(255,0,0));screen.blit(ets,(50,50))
        return
    system = current_beacon.solar_system; width,height = screen.get_size()
    if system.starfield_data: draw_system_starfield(screen,width,height,system.starfield_data)
    if system.has_nebula and system.nebula_details: draw_system_nebula(screen,width,height,system.nebula_details)

    num_stars = len(system.stars); star_positions = []
    if num_stars==1: star_positions.append((width//2,height//2,1.0))
    elif num_stars==2: offset=system.stars[0]['radius']*1.0; star_positions.extend([(width//2-offset,height//2,0.8),(width//2+offset,height//2,0.8)])
    elif num_stars>=3: offset=system.stars[0]['radius']*1.2; star_positions.extend([(width//2,height//2-int(offset*0.6),0.7),(width//2-int(offset*0.5),height//2+int(offset*0.3),0.7),(width//2+int(offset*0.5),height//2+int(offset*0.3),0.7)])

    primary_star_radius_for_orbit = 0
    for i,star_data in enumerate(system.stars):
        if i<len(star_positions): sx,sy,rad_mult = star_positions[i]; draw_star_in_system(screen,star_data,sx,sy)
        if i==0: primary_star_radius_for_orbit = star_data['radius']

    orbit_center_x,orbit_center_y = width//2,height//2
    if system.planets:
        max_orbit_zone = min(width,height)/2-60; min_orbit_rad = primary_star_radius_for_orbit+40
        if max_orbit_zone <= min_orbit_rad: max_orbit_zone = min_orbit_rad+(len(system.planets)*20)
        avail_space = max_orbit_zone-min_orbit_rad
        orbit_spacing = 10 if avail_space<len(system.planets)*10 and len(system.planets)>0 else (avail_space/(len(system.planets)+1) if len(system.planets)>0 else 0)
        for i,planet_data in enumerate(system.planets):
            orbit_rad = min_orbit_rad+(i+1)*orbit_spacing
            planet_angle = (pygame.time.get_ticks()/(20000.0+i*5000.0)+i*(math.pi/(len(system.planets)or 1)))%(2*math.pi)
            draw_planet_in_system(screen,planet_data,orbit_center_x,orbit_center_y,orbit_rad,planet_angle) # Calls new version

    if game_state.view_mode=='system_view' or game_state.ship.is_flying_into_system_view: draw_ship_on_system_view(screen,game_state.ship)
