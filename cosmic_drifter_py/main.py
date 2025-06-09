import pygame
import os
import ui
import audio
from config import CANVAS_WIDTH, CANVAS_HEIGHT, SHIP_SPRITE_WIDTH, SHIP_SPRITE_HEIGHT, USER_SHIP_IMAGE_URL
from game_objects import GameState
import graphics
import game_logic
import math

def run_game():
    pygame.init()
    audio.init_mixer()

    screen = pygame.display.set_mode((CANVAS_WIDTH, CANVAS_HEIGHT))
    pygame.display.set_caption("Cosmic Drifter (Python)")
    clock = pygame.time.Clock()

    audio.load_sounds()
    graphics.preload_beacon_sprites()
    graphics.preload_planet_sprites()
    graphics.initialize_parallax_starfield(CANVAS_WIDTH, CANVAS_HEIGHT - ui.HUD_HEIGHT - ui.BOTTOM_PANEL_HEIGHT) # Initialize for map area
    audio.switch_ambience('main_ambience')

    current_game_state = GameState()

    HUD_HEIGHT = ui.HUD_HEIGHT
    BOTTOM_PANEL_HEIGHT = ui.BOTTOM_PANEL_HEIGHT
    LEFT_PANEL_WIDTH_PERCENT = 0.6

    map_render_rect = pygame.Rect(0, HUD_HEIGHT, CANVAS_WIDTH, CANVAS_HEIGHT - HUD_HEIGHT - BOTTOM_PANEL_HEIGHT)
    event_log_panel_rect = pygame.Rect(0, CANVAS_HEIGHT - BOTTOM_PANEL_HEIGHT, int(CANVAS_WIDTH * LEFT_PANEL_WIDTH_PERCENT), BOTTOM_PANEL_HEIGHT)
    ship_systems_panel_rect = pygame.Rect(event_log_panel_rect.width, CANVAS_HEIGHT - BOTTOM_PANEL_HEIGHT, CANVAS_WIDTH - event_log_panel_rect.width, BOTTOM_PANEL_HEIGHT)

    game_logic.initialize_game(current_game_state)

    sprite_path_to_load = current_game_state.ship.map_sprite_path
    is_url = sprite_path_to_load.startswith("http://") or sprite_path_to_load.startswith("https://")
    if is_url or not os.path.exists(sprite_path_to_load):
        log_msg_type = "warning" if is_url else "info"
        game_logic.log_event(current_game_state, f"Ship sprite: {sprite_path_to_load} {'is URL or not found.' if is_url else 'not found locally.'}", log_msg_type)
        game_logic.log_event(current_game_state, "Attempting dummy sprite.", "info")
        dummy_sprite_dir = "cosmic_drifter_py/assets/images"
        os.makedirs(dummy_sprite_dir, exist_ok=True)
        dummy_sprite_path = os.path.join(dummy_sprite_dir, "dummy_ship.png")
        try:
            dummy_surface = pygame.Surface((SHIP_SPRITE_WIDTH, SHIP_SPRITE_HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(dummy_surface, graphics.parse_color(current_game_state.ship.color),
                                [(0,SHIP_SPRITE_HEIGHT),(SHIP_SPRITE_WIDTH/2,0),(SHIP_SPRITE_WIDTH,SHIP_SPRITE_HEIGHT)])
            pygame.image.save(dummy_surface, dummy_sprite_path)
            current_game_state.ship.map_sprite_path = dummy_sprite_path
            game_logic.log_event(current_game_state, f"Using dummy sprite: {dummy_sprite_path}", "info")
        except Exception as e:
            game_logic.log_event(current_game_state, f"Could not create dummy sprite: {e}", "error")
            current_game_state.ship.map_sprite_loaded = False
    graphics.load_ship_sprite(current_game_state.ship)

    running = True
    previous_view_mode = current_game_state.view_mode

    # Define a helper for view changes with fade
    def change_view_with_fade(target_view):
        def action_after_fade_out():
            current_game_state.view_mode = target_view
            # Reset relevant states for the new view
            if target_view == 'system_view':
                # This logic is mostly in update_ship_position, but if called directly:
                current_game_state.ship.is_flying_into_system_view = True
                current_game_state.ship.system_view_ship_x = -SHIP_SPRITE_WIDTH
                current_game_state.ship.system_view_ship_y = CANVAS_HEIGHT / 2
                current_game_state.ship.system_view_ship_target_x = CANVAS_WIDTH / 3
                current_game_state.ship.system_view_ship_target_y = CANVAS_HEIGHT / 2
                # ... (calculate angle)
                current_game_state.system_event_triggered_this_visit = False # Reset for new system
            elif target_view == 'map':
                 if current_game_state.current_beacon:
                     current_game_state.ship.x = current_game_state.current_beacon.x
                     current_game_state.ship.y = current_game_state.current_beacon.y

            game_logic.start_fade_transition(current_game_state, 0, 25) # Start fade-in

        # Start fade_out
        game_logic.start_fade_transition(current_game_state, 255, 25, action_after_fade_out, target_view)


    while running:
        dt_seconds = clock.get_time() / 1000.0
        current_game_state.ui_button_rects = {}

        # --- Handle view mode change audio ---
        if current_game_state.view_mode != previous_view_mode and not current_game_state.is_fading : # Avoid during fade
            # This is simplified. Ideally, change_view_with_fade would handle this transition.
            # For now, ambience switches immediately after fade-in for the new view.
            if current_game_state.view_mode == 'map': audio.switch_ambience('main_ambience')
            elif current_game_state.view_mode == 'system_view': audio.switch_ambience('system_ambience')
            previous_view_mode = current_game_state.view_mode

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if current_game_state.is_fading : continue # Block input during fade

            if event.type == pygame.MOUSEMOTION:
                mx,my=event.pos; current_game_state.hovered_beacon_id=None
                if current_game_state.view_mode=='map' and map_render_rect.collidepoint(mx,my):
                    [(current_game_state.hovered_beacon_id:=b.id) for b in current_game_state.beacons if math.sqrt((mx-b.x)**2+(my-b.y)**2)<b.radius+3]

            if event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
                mp=event.pos; cui_act=None
                for ack,rct in current_game_state.ui_button_rects.items():
                    if rct.collidepoint(mp): cui_act=ack; break
                if cui_act:
                    game_logic.log_event(current_game_state,f"UI Click: {cui_act}","debug")
                    if cui_act.startswith("modal_choice_") or cui_act=="modal_close": game_logic.handle_modal_choice(current_game_state,cui_act)
                    elif cui_act.startswith("engines_power") or cui_act.startswith("shields_power") or cui_act.startswith("weapons_power"):
                        sys_key,delta = (cui_act.split("_power_plus")[0],1) if cui_act.endswith("_plus") else (cui_act.split("_power_minus")[0],-1)
                        game_logic.change_system_power(current_game_state,sys_key,delta)
                    elif cui_act=='system_view_proceed' and current_game_state.view_mode=='system_view' and not current_game_state.is_modal_active:
                        # This now uses the fade transition helper
                        # game_logic.handle_system_view_click(current_game_state,mp) # Old direct call
                        # New: if event not triggered, trigger it. If triggered, then fade to map.
                        if not current_game_state.system_event_triggered_this_visit:
                             game_logic.handle_system_view_click(current_game_state,mp) # This triggers event modal
                        else: # Event done, button means "Exit System"
                             change_view_with_fade('map')
                elif not current_game_state.is_modal_active:
                    if current_game_state.view_mode=='map' and map_render_rect.collidepoint(mp): game_logic.handle_map_click(current_game_state,mp)

        # --- Game Logic Updates ---
        game_logic.update_particles_logic(current_game_state, dt_seconds)
        game_logic.update_fade_transition(current_game_state)

        if not current_game_state.is_fading and not current_game_state.is_modal_active:
            if current_game_state.view_mode == 'map':
                if not current_game_state.game_won and not current_game_state.game_over: game_logic.update_ship_position(current_game_state, change_view_with_fade) # Pass helper
            elif current_game_state.view_mode == 'system_view': game_logic.update_system_view_ship_animation(current_game_state)

        # --- Rendering ---
        screen.fill((0,0,0))
        if current_game_state.view_mode == 'map':
            graphics.draw_parallax_starfield(screen, dt_seconds) # Use parallax for map
            graphics.draw_map_decorations(screen, current_game_state.map_decorations)
            graphics.draw_beacons(screen, current_game_state)
            graphics.draw_particles(screen, current_game_state.particles)
            graphics.draw_ship(screen, current_game_state.ship)
        elif current_game_state.view_mode == 'system_view':
            if current_game_state.current_beacon and current_game_state.current_beacon.solar_system:
                graphics.draw_solar_system_view(screen, current_game_state) # System view has its own starfield
            else: ui.render_text(screen, "Error: No system data.",(50,screen.get_height()//2),ui.get_font(None,20),(255,0,0))

        graphics.draw_fade_transition(screen, current_game_state) # Draw fade overlay if active

        # --- UI Overlays ---
        ui.draw_hud(screen, current_game_state)
        ui.draw_event_log(screen, current_game_state, event_log_panel_rect)

        ship_system_buttons = ui.draw_ship_systems_panel(screen, current_game_state, ship_systems_panel_rect)
        current_game_state.ui_button_rects.update(ship_system_buttons)

        if current_game_state.view_mode == 'system_view' and not current_game_state.is_modal_active :
             if current_game_state.current_beacon and current_game_state.current_beacon.solar_system:
                 ui.draw_system_view_ui_overlays(screen, current_game_state, current_game_state.current_beacon.solar_system)

        if current_game_state.is_modal_active:
            modal_buttons = ui.draw_modal(screen, current_game_state)
            current_game_state.ui_button_rects.update(modal_buttons)

        pygame.display.flip(); clock.tick(60)
    pygame.quit()

if __name__ == '__main__':
    run_game()
