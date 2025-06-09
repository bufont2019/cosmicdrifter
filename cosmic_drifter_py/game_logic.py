import math
import random
import copy

from config import (FUEL_PER_JUMP, BASE_SHIP_SPEED, CANVAS_WIDTH, CANVAS_HEIGHT,
                    BEACON_RADIUS, MIN_BEACON_DISTANCE, PADDING, NUM_BEACONS,
                    MAX_CONNECTIONS_PER_BEACON, USER_SHIP_IMAGE_URL, NUM_MAP_NEBULAE,
                    CONNECTION_LINE_COLOR, BEACON_COLOR, BEACON_HOVER_COLOR,
                    ENDPOINT_BEACON_COLOR, ENDPOINT_PULSE_COLOR, SHIP_COLOR,
                    PLANET_TYPES, PLANET_SIZES_MAP, NAME_PREFIXES, NAME_SUFFIXES,
                    STAR_NAMES_ADJ, STAR_NAMES_NOUN, STAR_TYPES,
                    NUM_SYSTEM_VIEW_STARS, NEBULA_CHANCE, SYSTEM_VIEW_SHIP_FLY_IN_SPEED,
                    MAX_PLANETS_PER_SYSTEM, MIN_PLANETS_PER_SYSTEM, SHIP_SPRITE_WIDTH, SHIP_SPRITE_HEIGHT) # Added SHIP_SPRITE_HEIGHT

from game_objects import GameState, Beacon, SolarSystem, MapDecoration, Particle # Added Particle
from ui import MAX_LOG_MESSAGES
from events import EVENTS
import audio


def log_event(game_state, message, type="normal"): # Existing
    print(f"EVENT [{type.upper()}]: {message}")
    if game_state:
        game_state.event_log_messages.append((type, message))
        if len(game_state.event_log_messages) > MAX_LOG_MESSAGES + 10:
            game_state.event_log_messages = game_state.event_log_messages[-MAX_LOG_MESSAGES:]

# --- Particle System Logic ---
def spawn_engine_particles(game_state):
    ship = game_state.ship
    if not ship.is_moving or len(game_state.particles) > 100: # Limit max particles
        return

    angle_rad = math.radians(ship.angle)
    # Emit from just behind the center of the ship for a typical sprite
    offset_dist = SHIP_SPRITE_HEIGHT / 2
    emit_x = ship.x - math.cos(angle_rad) * offset_dist
    emit_y = ship.y - math.sin(angle_rad) * offset_dist

    # Base velocity is opposite to ship's angle
    # Velocity magnitude (pixels per second)
    base_particle_speed = random.uniform(30, 60)
    base_vel_x = -math.cos(angle_rad) * base_particle_speed
    base_vel_y = -math.sin(angle_rad) * base_particle_speed

    for _ in range(2): # Spawn a couple of particles
        # Add random angular spread to velocity (e.g., +/- 30 degrees)
        spread_angle_rad = math.radians(random.uniform(-30, 30))

        final_vel_x = base_vel_x * math.cos(spread_angle_rad) - base_vel_y * math.sin(spread_angle_rad)
        final_vel_y = base_vel_x * math.sin(spread_angle_rad) + base_vel_y * math.cos(spread_angle_rad)

        radius = random.uniform(1, 3.5)
        color = random.choice([(255,223,0), (255,165,0), (255,100,0), (200,150,50)])
        lifespan = random.uniform(200, 700) # milliseconds

        p = Particle(emit_x, emit_y, final_vel_x, final_vel_y, radius, color, lifespan)
        game_state.particles.append(p)

def update_particles_logic(game_state, dt_seconds):
    alive_particles = []
    for p in game_state.particles:
        p.update(dt_seconds)
        if p.is_alive():
            alive_particles.append(p)
    game_state.particles = alive_particles

# --- Event System (Existing) ---
def trigger_random_event(game_state): # Existing
    current_solar_system = game_state.current_beacon.solar_system if game_state.current_beacon else None
    possible_events = [e for e in EVENTS if 'condition' not in e or e['condition'](game_state, current_solar_system)]
    chosen_event_def = random.choice(possible_events) if possible_events else next((e for e in EVENTS if e['id'] == 'nothing_event'), None)
    if not chosen_event_def: log_event(game_state, "Error: No events available.", "error"); game_state.is_modal_active=False; game_state.view_mode='map'; return

    modal_title = chosen_event_def['title']
    modal_description = chosen_event_def['description']
    if callable(modal_description): modal_description = modal_description(game_state)
    modal_choices = [{'text':cd['text'],'action_key':f'modal_choice_{i}'} for i,cd in enumerate(chosen_event_def['choices'])]

    game_state.current_modal_data = {'id':chosen_event_def['id'],'title':modal_title,'text':modal_description,'choices':modal_choices}
    game_state.is_modal_active = True; audio.play_sound('event_alert')
    log_event(game_state, f"Event: {modal_title}", "event-title"); game_state._current_full_event_def = chosen_event_def

def handle_modal_choice(game_state, choice_action_key): # Existing
    if not game_state.current_modal_data or not hasattr(game_state, '_current_full_event_def'): game_state.is_modal_active=False; return
    full_event_def = game_state._current_full_event_def; outcome_message="No action."
    if choice_action_key == 'modal_close' or not full_event_def['choices']:
        if not full_event_def['choices'] and 'outcome' in full_event_def: outcome_message=full_event_def['outcome'](game_state)
        else: outcome_message="Modal closed."
        log_event(game_state, outcome_message, "info") ; audio.play_sound('positive_feedback') # Or neutral sound
    else:
        try:
            choice_index = int(choice_action_key.split('_')[-1])
            if 0 <= choice_index < len(full_event_def['choices']):
                selected_choice_def = full_event_def['choices'][choice_index]
                if hasattr(game_state, '_previous_scrap_for_event'): delattr(game_state, '_previous_scrap_for_event') # Cleanup
                outcome_message = selected_choice_def['outcome'](game_state)
                audio.play_sound('positive_feedback') # Assuming most choices are neutral or positive for now
                log_event(game_state, outcome_message, "event-choice")
            else: audio.play_sound('negative_feedback'); log_event(game_state, f"Invalid choice index: {choice_action_key}", "error")
        except (ValueError, Exception) as e: audio.play_sound('negative_feedback'); log_event(game_state, f"Error in choice: {e}", "error")

    game_state.is_modal_active=False; game_state.current_modal_data=None
    if hasattr(game_state, '_current_full_event_def'): delattr(game_state, '_current_full_event_def')
    update_ship_power_and_speed(game_state)
    if game_state.player_resources.hull <= 0 and not game_state.game_over:
        game_state.game_over=True; log_event(game_state,"Hull critical! Game Over.","critical")
        game_state.current_modal_data={'id':'game_over','title':'Game Over','text':'Ship destroyed.','choices':[{'text':'Restart (Not Implemented)','action_key':'modal_close'}]}
        game_state.is_modal_active=True; audio.play_sound('negative_feedback')

# --- Solar System Generation and View Logic (Existing, condensed for brevity) ---
def generate_planet_name(): return f"{random.choice(NAME_PREFIXES)} {random.choice(NAME_SUFFIXES)}" if random.random()<0.5 else f"{random.choice(NAME_PREFIXES)}-{random.randint(1,1000)}"
def generate_star_name(): return f"{random.choice(STAR_NAMES_ADJ)} {random.choice(STAR_NAMES_NOUN)}"
def generate_solar_system_details():
    planets_list = [] # ... (Full generation logic as before) ...
    for _ in range(random.randint(MIN_PLANETS_PER_SYSTEM,MAX_PLANETS_PER_SYSTEM)):
        pt=random.choice(PLANET_TYPES);sk=random.choice(list(PLANET_SIZES_MAP.keys())[:-1])
        if pt['name'] in ["Gas Giant","Ice Giant"]: sk=random.choice(list(PLANET_SIZES_MAP.keys()))
        elif sk=="Gigantic": sk="Large"
        planets_list.append({'name':generate_planet_name(),'type':pt['name'],'size':sk,'radius':PLANET_SIZES_MAP[sk],'color':pt['color'],'keywords':pt['keywords'],'surfaceFeatures':[],'hasRings':(pt['name']in["Gas Giant","Ice Giant"])and random.random()<0.4,'ringTilt':(random.random()-0.5)*0.6})
    sf_list = [{'x':random.random(),'y':random.random(),'radius':int(random.uniform(1,2.2)),'alpha':random.uniform(0.3,1)} for _ in range(NUM_SYSTEM_VIEW_STARS)]
    num_s=1; sr=random.random(); num_s=3 if sr<0.01 else (2 if sr<0.06 else 1)
    s_list=[copy.deepcopy(random.choice(STAR_TYPES)) for _ in range(num_s)]
    hn=random.random()<NEBULA_CHANCE; nd=None
    if hn:c1,c2=(random.randint(80,120),random.randint(0,40),random.randint(120,160)),(random.randint(0,40),random.randint(80,120),random.randint(120,160));nd={'x':random.uniform(0.2,0.8),'y':random.uniform(0.2,0.8),'radius':random.uniform(100,300),'color1':f"rgba({c1[0]},{c1[1]},{c1[2]},0.08)",'color2':f"rgba({c2[0]},{c2[1]},{c2[2]},0.04)"}
    return SolarSystem(name=generate_star_name(),stars=s_list,planets=planets_list,starfield_data=sf_list,has_nebula=hn,nebula_details=nd)

def update_system_view_ship_animation(game_state): # Existing
    ship=game_state.ship;
    if not ship.is_flying_into_system_view:return
    dx,dy=ship.system_view_ship_target_x-ship.system_view_ship_x,ship.system_view_ship_target_y-ship.system_view_ship_y
    dist=math.sqrt(dx*dx+dy*dy)
    if dist<SYSTEM_VIEW_SHIP_FLY_IN_SPEED: ship.system_view_ship_x,ship.system_view_ship_y,ship.is_flying_into_system_view=ship.system_view_ship_target_x,ship.system_view_ship_target_y,False; log_event(game_state,"Fly-in complete. Engage scanners.","info")
    else: angle_r=math.atan2(dy,dx);ship.system_view_ship_x+=SYSTEM_VIEW_SHIP_FLY_IN_SPEED*math.cos(angle_r);ship.system_view_ship_y+=SYSTEM_VIEW_SHIP_FLY_IN_SPEED*math.sin(angle_r);ship.system_view_ship_angle=math.degrees(angle_r)+90

def handle_system_view_click(game_state, mouse_pos): # Existing
    pr=game_state.ui_button_rects.get('system_view_proceed')
    if pr and pr.collidepoint(mouse_pos) and not game_state.ship.is_flying_into_system_view and not game_state.is_modal_active:
        if not game_state.system_event_triggered_this_visit: log_event(game_state,"Engaging scanners...","event-title");trigger_random_event(game_state);game_state.system_event_triggered_this_visit=True
        else: log_event(game_state,"Leaving system...","info");game_state.view_mode='map';
        if game_state.current_beacon:game_state.ship.x,game_state.ship.y=game_state.current_beacon.x,game_state.current_beacon.y

# --- Ship and Map Logic (Existing, condensed) ---
def change_system_power(game_state,sk,d): ship=game_state.ship;sys=ship.systems.get(sk); assert sys; np=sys.power+d; assert 0<=np<=sys.max_power; assert not(d>0 and (ship.power_used+d)>ship.reactor_output); sys.power=np;update_ship_power_and_speed(game_state);log_event(game_state,f"{sys.name} pwr {sys.power}. React: {ship.power_used}/{ship.reactor_output}","system-info")
def update_ship_power_and_speed(game_state): ship=game_state.ship;pr=game_state.player_resources;npu=sum(s.power for s in ship.systems.values());ship.power_used=npu;eng=ship.systems.get('engines');shs=ship.systems.get('shields');ship.current_speed=BASE_SHIP_SPEED+(eng.base_effect+eng.power*eng.effect_per_power) if eng else BASE_SHIP_SPEED;ship.current_speed=max(0.1,ship.current_speed);pr.max_shield_layers=int(shs.base_effect+shs.power*shs.effect_per_power) if shs else 0;pr.shield_points=min(pr.shield_points,pr.max_shield_layers)

def update_ship_position(game_state, change_view_callback=None): # Added change_view_callback
    ship = game_state.ship
    if ship.is_moving: # Spawn particles if ship is set to move, regardless of target validity here
        spawn_engine_particles(game_state)

    if not ship.is_moving or ship.target_beacon_id is None: ship.is_moving = False; return # Stop if no target/not moving
    target_beacon = game_state.get_beacon_by_id(ship.target_beacon_id)
    if not target_beacon: ship.is_moving = False; log_event(game_state, "Error: Target beacon lost.", "error"); return

    dx,dy = target_beacon.x-ship.x, target_beacon.y-ship.y
    angle_r = math.atan2(dy,dx); ship.angle = math.degrees(angle_r)
    dist = math.sqrt(dx*dx+dy*dy); update_ship_power_and_speed(game_state)
    eff_speed = ship.current_speed

    if dist < eff_speed: # Arrived
        ship.x,ship.y,ship.is_moving = target_beacon.x,target_beacon.y,False
        log_event(game_state,f"Fuel: -{FUEL_PER_JUMP}. Rem:{game_state.player_resources.fuel-FUEL_PER_JUMP}","resource")
        game_state.player_resources.fuel = max(0, game_state.player_resources.fuel-FUEL_PER_JUMP)
        if game_state.player_resources.fuel==0: log_event(game_state,"Fuel depleted!","critical")

        ship.current_beacon_id = target_beacon.id; target_beacon.visited=True
        game_state.system_event_triggered_this_visit = False # Reset for new system
        ship.target_beacon_id=None
        log_event(game_state,f"Arrived: {target_beacon.solar_system.name}. Fuel:{game_state.player_resources.fuel}","system-info-title")
        if target_beacon.is_endpoint: game_state.game_won=True; log_event(game_state,f"VICTORY! Endpoint: {target_beacon.solar_system.name}","event-title")
        else:
            log_event(game_state,f"Preparing to enter {target_beacon.solar_system.name}.","info")
            if change_view_callback:
                change_view_callback('system_view') # This will handle fade out, then view switch + fade in
            else: # Fallback if no callback provided (direct switch)
                game_state.view_mode='system_view'; ship.is_flying_into_system_view=True
                ship.system_view_ship_x = -SHIP_SPRITE_WIDTH; ship.system_view_ship_y=CANVAS_HEIGHT/2
                ship.system_view_ship_target_x=CANVAS_WIDTH/3; ship.system_view_ship_target_y=CANVAS_HEIGHT/2
                tdx,tdy = ship.system_view_ship_target_x-ship.system_view_ship_x, ship.system_view_ship_target_y-ship.system_view_ship_y
                ship.system_view_ship_angle = math.degrees(math.atan2(tdy,tdx))+90 if not (tdx==0 and tdy==0) else ship.angle
    else: # Still moving
        ship.x += eff_speed*math.cos(angle_r); ship.y += eff_speed*math.sin(angle_r)

def generate_map_decorations(game_state): # Existing (condensed)
    game_state.map_decorations=[]; nc=["rgba(128,0,128,0.05)","rgba(0,0,255,0.04)","rgba(0,128,128,0.06)","rgba(255,0,0,0.03)","rgba(0,255,0,0.04)"]
    for _ in range(NUM_MAP_NEBULAE): nx,ny,nrx,nry,rot,cs = random.uniform(0,CANVAS_WIDTH),random.uniform(0,CANVAS_HEIGHT),random.uniform(CANVAS_WIDTH*0.1,CANVAS_WIDTH*0.3),random.uniform(CANVAS_HEIGHT*0.1,CANVAS_HEIGHT*0.3),random.uniform(0,360),random.choice(nc); game_state.map_decorations.append(MapDecoration('nebula',nx,ny,nrx,nry,rot,cs))
    log_event(game_state,f"Gen {NUM_MAP_NEBULAE} map decorations.","info")

# --- Fade Transition Logic ---
def start_fade_transition(game_state, to_alpha, speed, on_complete_action=None, next_view=None):
    game_state.is_fading = True
    # If fading to black (to_alpha=255), start from transparent (fade_alpha=0)
    # If fading to clear (to_alpha=0), start from opaque (fade_alpha=255)
    game_state.fade_alpha = 0 if to_alpha == 255 else 255
    game_state.fade_target_alpha = to_alpha
    game_state.fade_speed = abs(speed) # Ensure speed is positive
    game_state.on_fade_complete_action = on_complete_action
    game_state.next_view_after_fade = next_view
    # print(f"Starting fade: current_alpha={game_state.fade_alpha}, target_alpha={to_alpha}, speed={speed}")


def update_fade_transition(game_state):
    if not game_state.is_fading:
        return

    if game_state.fade_alpha < game_state.fade_target_alpha: # Fading to darker / more opaque (e.g. fade_alpha from 0 to 255)
        game_state.fade_alpha += game_state.fade_speed
        if game_state.fade_alpha >= game_state.fade_target_alpha:
            game_state.fade_alpha = game_state.fade_target_alpha
            game_state.is_fading = False
            # print(f"Fade to target {game_state.fade_target_alpha} complete.")
            if game_state.on_fade_complete_action:
                # print("Executing on_fade_complete_action (e.g. for fade-out)")
                game_state.on_fade_complete_action()
                game_state.on_fade_complete_action = None

    elif game_state.fade_alpha > game_state.fade_target_alpha: # Fading to lighter / more transparent (e.g. fade_alpha from 255 to 0)
        game_state.fade_alpha -= game_state.fade_speed
        if game_state.fade_alpha <= game_state.fade_target_alpha:
            game_state.fade_alpha = game_state.fade_target_alpha
            game_state.is_fading = False
            # print(f"Fade to target {game_state.fade_target_alpha} complete.")
            if game_state.on_fade_complete_action: # Usually for fade-out, not fade-in completion
                 # print("Executing on_fade_complete_action (e.g. for fade-in, if any)")
                 game_state.on_fade_complete_action()
                 game_state.on_fade_complete_action = None


def initialize_game(game_state): # Existing (condensed)
    game_state.ship.map_sprite_path=USER_SHIP_IMAGE_URL;game_state.beacons=[];pes=[]
    for i in range(NUM_BEACONS):
        att,vp,bx,by=0,False,0,0
        while not vp and att<100:bx,by=random.uniform(PADDING,CANVAS_WIDTH-PADDING),random.uniform(PADDING,CANVAS_HEIGHT-PADDING);vp=True;[(vp:=False) for eb in game_state.beacons if math.sqrt((bx-eb.x)**2+(by-eb.y)**2)<MIN_BEACON_DISTANCE];att+=1
        if vp:nb=Beacon(i,bx,by,BEACON_RADIUS,BEACON_COLOR,None);nb.solar_system=generate_solar_system_details();nb.solar_system.name=f"Sys {nb.id} ({nb.solar_system.name})";game_state.beacons.append(nb);pes.append(nb)
    for bA in game_state.beacons:
        sbs=sorted([b for b in game_state.beacons if b.id!=bA.id],key=lambda bB:math.sqrt((bA.x-bB.x)**2+(bA.y-bB.y)**2))
        for idx in range(min(len(sbs),random.randint(1,MAX_CONNECTIONS_PER_BEACON))): bB=sbs[idx]; conn_dist=math.sqrt((bA.x-bB.x)**2+(bA.y-bB.y)**2);not(len(bA.connections)>=MAX_CONNECTIONS_PER_BEACON or len(bB.connections)>=MAX_CONNECTIONS_PER_BEACON or bB.id in bA.connections or conn_dist>=MIN_BEACON_DISTANCE*7)and(bA.connections.append(bB.id),bB.connections.append(bA.id))
    if not game_state.beacons:log_event(game_state,"No beacons gen.","error");game_state.game_over=True;return
    sb=random.choice(game_state.beacons);game_state.ship.current_beacon_id=sb.id;game_state.ship.x,game_state.ship.y=sb.x,sb.y;sb.visited=True;log_event(game_state,f"Ship at {sb.solar_system.name}.","info")
    veps=[b for b in pes if b.id!=sb.id and math.sqrt((b.x-sb.x)**2+(b.y-sb.y)**2)>min(CANVAS_WIDTH,CANVAS_HEIGHT)*0.3];veps=veps if veps else[b for b in pes if b.id!=sb.id]
    if veps:ep=random.choice(veps);ep.is_endpoint=True;game_state.endpoint_beacon_id=ep.id;log_event(game_state,f"Endpoint: {ep.solar_system.name}.","info")
    elif len(game_state.beacons)>1:fep=next((b for b in game_state.beacons if b.id!=sb.id),None);fep.is_endpoint=True;game_state.endpoint_beacon_id=fep.id;log_event(game_state,f"Fallback Endpoint: {fep.solar_system.name}.","warning")
    else:log_event(game_state,"No endpoint beacons.","error")
    update_ship_power_and_speed(game_state);generate_map_decorations(game_state);game_state.view_mode='map';game_state.game_won,game_state.game_over,game_state.system_event_triggered_this_visit=False,False,False;log_event(game_state,"Game initialized.","event-title")

def handle_map_click(game_state, mouse_pos): # Existing (condensed)
    mx,my=mouse_pos;ship=game_state.ship
    if ship.is_moving or game_state.game_over or game_state.game_won:return
    cbk=None;[(cbk:=b) for b in game_state.beacons if math.sqrt((mx-b.x)**2+(my-b.y)**2)<b.radius+5]
    if cbk:
        curb=game_state.current_beacon
        if curb and cbk.id in curb.connections:
            if game_state.player_resources.fuel>=FUEL_PER_JUMP:ship.target_beacon_id=cbk.id;ship.is_moving=True;audio.play_sound('jump');log_event(game_state,f"Target: {cbk.solar_system.name}. Engage.","info")
            else:audio.play_sound('negative_feedback');log_event(game_state,f"No jump: low fuel {game_state.player_resources.fuel}/{FUEL_PER_JUMP}.","warning")
        elif curb and cbk.id==curb.id:
            log_event(game_state,f"At {curb.solar_system.name}. Triggering System View.","info")
            # This part is tricky: handle_map_click is called from main, which has change_view_callback
            # but game_logic itself doesn't store it. This needs to be passed or handled in main.
            # For now, assume direct change, main.py's change_view_with_fade handles the actual call.
            # The `change_view_with_fade` should be called from main.py for this action.
            # Direct change here for simplicity if callback is not available:
            if 'change_view_callback' in locals() and callable(locals()['change_view_callback']):
                 locals()['change_view_callback']('system_view') # This is conceptually what we want
            else: # Fallback if no easy way to call main's helper here
                game_state.view_mode='system_view' # This will be caught by main loop for ambience, but no fade
                ship.is_flying_into_system_view=True; ship.system_view_ship_x=CANVAS_WIDTH/2; ship.system_view_ship_y=CANVAS_HEIGHT+SHIP_SPRITE_HEIGHT
                ship.system_view_ship_target_x=CANVAS_WIDTH/2; ship.system_view_ship_target_y=CANVAS_HEIGHT*0.66
                dx,dy=ship.system_view_ship_target_x-ship.system_view_ship_x,ship.system_view_ship_target_y-ship.system_view_ship_y
                ship.system_view_ship_angle=math.degrees(math.atan2(dy,dx))+90 if not(dx==0 and dy==0) else ship.angle

        elif not curb:log_event(game_state,"Error: Current beacon unknown.","error")
        else:log_event(game_state,f"No direct conn to {cbk.solar_system.name}.","warning")
    else:log_event(game_state,"Empty map click.","debug")

```
