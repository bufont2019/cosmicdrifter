# cosmic_drifter_py/ui.py
import pygame
from config import SYSTEMS_CONFIG # For names, etc.
# from game_objects import PlayerResources, ShipState # For type hinting

pygame.font.init() # Initialize font module

# Define some colors (more can be added from config or defined directly)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_LIGHT_GREY = (200, 200, 200)
COLOR_DARK_GREY = (50, 50, 50)
COLOR_HUD_TEXT = (125, 211, 252) # sky-300 from Tailwind
COLOR_PANEL_BG = (24, 32, 48) # slate-800/900
COLOR_BORDER = (48, 56, 72) # slate-700
COLOR_EVENT_TITLE = (100, 181, 246) # blue-400
COLOR_SYSTEM_INFO_TITLE = (100, 181, 246)
COLOR_SYSTEM_NAME = (200, 208, 224) # slate-300
COLOR_POWER_BAR_ACTIVE = (59, 130, 246) # blue-500
COLOR_POWER_BAR_INACTIVE = (55, 65, 81) # gray-600
COLOR_BUTTON = (79, 70, 229) # indigo-600
COLOR_BUTTON_HOVER = (67, 56, 202) # indigo-700
COLOR_BUTTON_DISABLED = (107, 114, 128) # gray-500
COLOR_ORBITRON_LIKE = (100, 181, 246) # Default for Orbitron-style titles

# UI Layout constants (can be moved to config.py)
HUD_HEIGHT = 40
BOTTOM_PANEL_HEIGHT = 180
MAX_LOG_MESSAGES = 15 # Store more, but display last N (used in game_logic for trimming)

try:
    # Assuming assets folder is at the root of the project, and this script is in cosmic_drifter_py
    FONT_ORBITRON_PATH = "assets/fonts/Orbitron-Regular.ttf"
    FONT_ROBOTO_PATH = "assets/fonts/Roboto-Regular.ttf"
    # If running from cosmic_drifter_py, path might need to be "../assets/fonts/..."
    # For now, assume the execution context allows this path.
    # A more robust solution would use absolute paths or paths relative to main.py's location.
    # Let's try a relative path from where ui.py is.
    # FONT_ORBITRON_PATH = "../assets/fonts/Orbitron-Regular.ttf" # This might be needed if main.py is in cosmic_drifter_py
    # FONT_ROBOTO_PATH = "../assets/fonts/Roboto-Regular.ttf"
    # For now, using the provided path structure, assuming it resolves correctly during execution by main.py
    FONT_HUD = pygame.font.Font(FONT_ORBITRON_PATH, 18)
    FONT_PANEL_TITLE = pygame.font.Font(FONT_ORBITRON_PATH, 16)
    FONT_LOG_TEXT = pygame.font.Font(FONT_ROBOTO_PATH, 13)
    FONT_SYSTEM_TEXT = pygame.font.Font(FONT_ROBOTO_PATH, 14)
    FONT_BUTTON = pygame.font.Font(FONT_ROBOTO_PATH, 12)
except pygame.error as e:
    print(f"Warning: Custom fonts not found in assets/fonts/ ({e}). Using default font.")
    FONT_HUD = pygame.font.Font(None, 24)
    FONT_PANEL_TITLE = pygame.font.Font(None, 22)
    FONT_LOG_TEXT = pygame.font.Font(None, 18)
    FONT_SYSTEM_TEXT = pygame.font.Font(None, 20)
    FONT_BUTTON = pygame.font.Font(None, 18)


def render_text(screen, text, position, font, color=COLOR_WHITE, antialias=True, bg_color=None):
    text_surface = font.render(text, antialias, color, bg_color)
    screen.blit(text_surface, position)
    return text_surface.get_rect(topleft=position)

def draw_hud(screen, game_state):
    player_resources = game_state.player_resources
    ship = game_state.ship

    hud_rect = pygame.Rect(0, 0, screen.get_width(), HUD_HEIGHT)
    pygame.draw.rect(screen, COLOR_PANEL_BG, hud_rect)
    pygame.draw.line(screen, COLOR_BORDER, (0, HUD_HEIGHT -1), (screen.get_width(), HUD_HEIGHT-1), 1)

    margin = 10
    current_x = margin

    hud_items = [
        f"Fuel: {player_resources.fuel}",
        f"Scrap: {player_resources.scrap}",
        f"Hull: {player_resources.hull}%",
        f"Shields: {player_resources.shield_points}",
        f"Power: {ship.power_used}/{ship.reactor_output}"
    ]

    for item_text in hud_items:
        text_surface = FONT_HUD.render(item_text, True, COLOR_HUD_TEXT)
        screen.blit(text_surface, (current_x, (HUD_HEIGHT - text_surface.get_height()) / 2))
        current_x += text_surface.get_width() + 30

def draw_event_log(screen, game_state, panel_rect):
    pygame.draw.rect(screen, COLOR_PANEL_BG, panel_rect)
    pygame.draw.rect(screen, COLOR_BORDER, panel_rect, 1)

    title_rect = render_text(screen, "Event Log", (panel_rect.x + 5, panel_rect.y + 5), FONT_PANEL_TITLE, COLOR_EVENT_TITLE)

    log_area_y_start = title_rect.bottom + 5
    log_area_height = panel_rect.height - (log_area_y_start - panel_rect.y) - 5

    line_height = FONT_LOG_TEXT.get_linesize()
    if line_height == 0: line_height = 15 # Fallback if font not loaded
    max_visible_lines = log_area_height // line_height

    start_index = max(0, len(game_state.event_log_messages) - max_visible_lines)
    visible_messages = game_state.event_log_messages[start_index:]

    current_y = log_area_y_start
    for msg_type, message in visible_messages: # Oldest first (top down)
        text_color = COLOR_LIGHT_GREY
        if msg_type == "event-title": text_color = COLOR_EVENT_TITLE
        elif msg_type == "system-info-title": text_color = COLOR_SYSTEM_INFO_TITLE
        elif msg_type == "error": text_color = (239, 68, 68)
        elif msg_type == "warning": text_color = (245, 158, 11) # amber-500
        elif msg_type == "resource": text_color = (34, 197, 94) # green-500
        elif msg_type == "info": text_color = (14, 165, 233) # sky-500
        # Add more type-specific colors as needed

        render_text(screen, message, (panel_rect.x + 5, current_y), FONT_LOG_TEXT, text_color)
        current_y += line_height
        if current_y + line_height > panel_rect.bottom -5:
            break

def draw_ship_systems_panel(screen, game_state, panel_rect):
    ship = game_state.ship
    pygame.draw.rect(screen, COLOR_PANEL_BG, panel_rect)
    pygame.draw.rect(screen, COLOR_BORDER, panel_rect, 1)

    title_rect = render_text(screen, "Ship Systems", (panel_rect.x + 5, panel_rect.y + 5), FONT_PANEL_TITLE, COLOR_ORBITRON_LIKE)

    current_y = title_rect.bottom + 10
    button_rects = {} # Store generated rects for click detection

    for system_key, system_obj in ship.systems.items():
        name_text = f"{system_obj.name} (Lvl: {system_obj.level})"
        render_text(screen, name_text, (panel_rect.x + 10, current_y), FONT_SYSTEM_TEXT, COLOR_SYSTEM_NAME)

        power_bar_y = current_y + FONT_SYSTEM_TEXT.get_height() + 2
        power_bar_x_start = panel_rect.x + 10 # Keep track of where power bars start
        power_bar_x = power_bar_x_start # current x for drawing segments

        segment_width = 10
        segment_height = 16
        segment_margin = 1

        for i in range(1, system_obj.max_power + 1):
            bar_color = COLOR_POWER_BAR_ACTIVE if i <= system_obj.power else COLOR_POWER_BAR_INACTIVE
            pygame.draw.rect(screen, bar_color, (power_bar_x, power_bar_y, segment_width, segment_height))
            power_bar_x += segment_width + segment_margin

        button_size = 18
        button_y = power_bar_y # Align with power bar

        # Minus Button
        minus_button_x = power_bar_x + 10 # Place buttons after all power bar segments
        minus_rect = pygame.Rect(minus_button_x, button_y, button_size, button_size)
        minus_disabled = system_obj.power == 0

        btn_color_minus = COLOR_BUTTON_DISABLED if minus_disabled else COLOR_BUTTON
        # Example hover (mouse interaction needs to be handled in main loop and passed or checked here)
        # if not minus_disabled and minus_rect.collidepoint(pygame.mouse.get_pos()):
        #    btn_color_minus = COLOR_BUTTON_HOVER
        pygame.draw.rect(screen, btn_color_minus, minus_rect)
        render_text(screen, "-", (minus_button_x + 6, button_y + 1), FONT_BUTTON, COLOR_WHITE) # Centering '-'
        button_rects[f'{system_key}_power_minus'] = minus_rect

        # Plus Button
        plus_button_x = minus_button_x + button_size + 5
        plus_rect = pygame.Rect(plus_button_x, button_y, button_size, button_size)
        # Disable plus if at max power for the system OR if reactor output is already met/exceeded
        # (unless reducing power in another system would free it up - this logic is simpler)
        plus_disabled = system_obj.power == system_obj.max_power or \
                        (ship.power_used >= ship.reactor_output and system_obj.power < system_obj.max_power)

        btn_color_plus = COLOR_BUTTON_DISABLED if plus_disabled else COLOR_BUTTON
        # if not plus_disabled and plus_rect.collidepoint(pygame.mouse.get_pos()):
        #    btn_color_plus = COLOR_BUTTON_HOVER
        pygame.draw.rect(screen, btn_color_plus, plus_rect)
        render_text(screen, "+", (plus_button_x + 5, button_y + 1), FONT_BUTTON, COLOR_WHITE) # Centering '+'
        button_rects[f'{system_key}_power_plus'] = plus_rect

        current_y += FONT_SYSTEM_TEXT.get_height() + segment_height + 10 # Spacing for next system

    # Reactor Info (Placed at the bottom of the panel)
    reactor_text = f"Reactor: {ship.power_used} / {ship.reactor_output}"
    render_text(screen, reactor_text, (panel_rect.x + 10, panel_rect.bottom - 25), FONT_SYSTEM_TEXT, COLOR_LIGHT_GREY)

    return button_rects


# (Existing UI functions and constants remain)
FONT_SYSTEM_VIEW_TITLE = FONT_ORBITRON_PATH # pygame.font.Font(FONT_ORBITRON_PATH, 28) if specific needed
FONT_PLANET_DETAILS_TITLE = FONT_ORBITRON_PATH # pygame.font.Font(FONT_ORBITRON_PATH, 16)
FONT_PLANET_DETAILS_TEXT = FONT_ROBOTO_PATH # pygame.font.Font(FONT_ROBOTO_PATH, 13)
FONT_SYSTEM_VIEW_BUTTON = FONT_ORBITRON_PATH # pygame.font.Font(FONT_ORBITRON_PATH, 16)

# Lazy load fonts to avoid pygame.error if called before display init in some contexts
_font_cache = {}
def get_font(path, size):
    key = (path, size)
    if key not in _font_cache:
        try:
            if path: # Custom font
                _font_cache[key] = pygame.font.Font(path, size)
            else: # Default font
                _font_cache[key] = pygame.font.Font(None, size)
        except pygame.error:
            print(f"Warning: Font error for {path} size {size}. Using default.")
            _font_cache[key] = pygame.font.Font(None, size) # Fallback to default font
    return _font_cache[key]


# System View specific UI elements
SYSTEM_VIEW_TITLE_RECT = None # Will be set dynamically
PLANET_DETAILS_RECT = None # Will be set dynamically
PROCEED_BUTTON_RECT = None # Will be set dynamically

def draw_system_view_ui_overlays(screen, game_state, current_solar_system):
    global SYSTEM_VIEW_TITLE_RECT, PLANET_DETAILS_RECT, PROCEED_BUTTON_RECT

    # System Name Title
    title_font = get_font(FONT_SYSTEM_VIEW_TITLE, 28)
    title_text = f"Entering {current_solar_system.name}"
    if current_solar_system.stars:
        star_names = [s['name'] for s in current_solar_system.stars]
        title_text += f" ({', '.join(star_names)})"

    title_surf = title_font.render(title_text, True, COLOR_WHITE)
    SYSTEM_VIEW_TITLE_RECT = title_surf.get_rect(centerx=screen.get_width() // 2, top=20)

    # Simple background for title
    title_bg_rect = SYSTEM_VIEW_TITLE_RECT.inflate(20, 10)
    title_bg_surf = pygame.Surface(title_bg_rect.size, pygame.SRCALPHA)
    title_bg_surf.fill((10, 15, 24, 180)) # Semi-transparent dark bg
    screen.blit(title_bg_surf, title_bg_rect)
    screen.blit(title_surf, SYSTEM_VIEW_TITLE_RECT)

    # Planet Details Overlay (bottom-leftish)
    PLANET_DETAILS_RECT = pygame.Rect(20, screen.get_height() - 170, 300, 150) # x, y, w, h
    details_bg_surf = pygame.Surface(PLANET_DETAILS_RECT.size, pygame.SRCALPHA)
    details_bg_surf.fill((16, 24, 40, 220)) # More opaque dark bg
    pygame.draw.rect(details_bg_surf, COLOR_BORDER, details_bg_surf.get_rect(), 1)
    screen.blit(details_bg_surf, PLANET_DETAILS_RECT.topleft)

    details_title_font = get_font(FONT_PLANET_DETAILS_TITLE, 16)
    details_text_font = get_font(FONT_PLANET_DETAILS_TEXT, 13)

    render_text(screen, "Planetary Scan", (PLANET_DETAILS_RECT.x + 10, PLANET_DETAILS_RECT.y + 10), details_title_font, COLOR_ORBITRON_LIKE)
    current_y = PLANET_DETAILS_RECT.y + 10 + details_title_font.get_height() + 5

    if current_solar_system.planets:
        for planet in current_solar_system.planets:
            planet_info = f"- {planet['name']} ({planet['type']}, {planet['size']})"
            if current_y + details_text_font.get_height() < PLANET_DETAILS_RECT.bottom - 10:
                render_text(screen, planet_info, (PLANET_DETAILS_RECT.x + 10, current_y), details_text_font, COLOR_LIGHT_GREY)
                current_y += details_text_font.get_height() + 3
            else:
                render_text(screen, "...", (PLANET_DETAILS_RECT.x + 10, current_y), details_text_font, COLOR_LIGHT_GREY)
                break
    else:
        render_text(screen, "No significant planetary bodies detected.", (PLANET_DETAILS_RECT.x + 10, current_y), details_text_font, COLOR_LIGHT_GREY)

    # "Engage Local Scanners" / "Proceed" Button (bottom-center)
    button_font = get_font(FONT_SYSTEM_VIEW_BUTTON, 16)
    proceed_text = "Engage Local Scanners"
    if game_state.ship.is_flying_into_system_view:
        proceed_text = "Approaching..." # Or disable button

    button_surf = button_font.render(proceed_text, True, COLOR_WHITE)
    button_padding = (20, 10)
    PROCEED_BUTTON_RECT = button_surf.get_rect(centerx=screen.get_width() // 2, bottom=screen.get_height() - 20)
    PROCEED_BUTTON_RECT.inflate_ip(button_padding[0]*2, button_padding[1]*2) # Inflate rect for bg

    button_color = COLOR_BUTTON_DISABLED if game_state.ship.is_flying_into_system_view else COLOR_BUTTON
    # Check for hover for proceed button (needs mouse pos)
    # mouse_pos = pygame.mouse.get_pos()
    # if PROCEED_BUTTON_RECT and PROCEED_BUTTON_RECT.collidepoint(mouse_pos) and not game_state.ship.is_flying_into_system_view:
    #    button_color = COLOR_BUTTON_HOVER

    pygame.draw.rect(screen, button_color, PROCEED_BUTTON_RECT, border_radius=6)
    screen.blit(button_surf, button_surf.get_rect(center=PROCEED_BUTTON_RECT.center))

    # Store button rect for click detection in main loop
    game_state.ui_button_rects['system_view_proceed'] = PROCEED_BUTTON_RECT


# (Existing UI content)
FONT_MODAL_TITLE = FONT_ORBITRON_PATH # get_font(FONT_ORBITRON_PATH, 24)
FONT_MODAL_TEXT = FONT_ROBOTO_PATH # get_font(FONT_ROBOTO_PATH, 16)
FONT_MODAL_CHOICE = FONT_ROBOTO_PATH # get_font(FONT_ROBOTO_PATH, 14)

# Modal specific UI elements to be stored in game_state.ui_button_rects
# Example: 'modal_choice_0', 'modal_choice_1', 'modal_close'

def draw_modal(screen, game_state):
    if not game_state.is_modal_active or not game_state.current_modal_data:
        return {} # Return empty dict if no buttons

    modal_data = game_state.current_modal_data

    # Backdrop (semi-transparent overlay)
    backdrop_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    backdrop_surface.fill((0, 0, 0, 180)) # Darken the background
    screen.blit(backdrop_surface, (0,0))

    # Modal content box
    modal_width = screen.get_width() * 0.7
    modal_height = screen.get_height() * 0.6
    modal_x = (screen.get_width() - modal_width) / 2
    modal_y = (screen.get_height() - modal_height) / 2
    modal_rect = pygame.Rect(modal_x, modal_y, modal_width, modal_height)

    # Draw modal box
    pygame.draw.rect(screen, COLOR_PANEL_BG, modal_rect, border_radius=8)
    pygame.draw.rect(screen, COLOR_BORDER, modal_rect, 2, border_radius=8)

    padding = 20
    content_x = modal_x + padding
    content_y = modal_y + padding
    content_width = modal_width - 2 * padding

    # Title
    title_font = get_font(FONT_MODAL_TITLE, 24)
    title_rect = render_text(screen, modal_data['title'], (content_x, content_y), title_font, COLOR_ORBITRON_LIKE)
    content_y += title_rect.height + 15

    # Body Text (handle multi-line)
    text_font = get_font(FONT_MODAL_TEXT, 16)

    # Basic word wrapping for modal text
    available_text_width = content_width
    lines = []

    paragraphs = modal_data['text'].split('\n')
    for paragraph in paragraphs:
        words = paragraph.split(' ')
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if text_font.size(test_line)[0] <= available_text_width:
                current_line = test_line
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        lines.append(current_line.strip()) # Add the last line of the paragraph
        lines.append("") # Add a blank line for paragraph spacing if desired (or handle differently)
    if lines and not lines[-1]: lines.pop() # Remove trailing blank line if any

    for line in lines:
        if content_y + text_font.get_height() < modal_rect.bottom - padding - 40: # Reserve space for buttons
            render_text(screen, line, (content_x, content_y), text_font, COLOR_LIGHT_GREY)
            content_y += text_font.get_height() # +5 for more spacing if needed
        else:
            render_text(screen, "...", (content_x, content_y), text_font, COLOR_LIGHT_GREY) # Truncate if too long
            break

    content_y += 15 # Spacing before choices

    # Choices as buttons
    choice_font = get_font(FONT_MODAL_CHOICE, 14)
    button_height = 30
    button_spacing = 10
    modal_buttons = {}

    # Position buttons from the bottom of the modal, working upwards if too many choices.
    # This ensures buttons are always visible if possible.
    # max_buttons_area_height = modal_rect.bottom - content_y - padding
    # total_buttons_height = len(modal_data['choices']) * (button_height + button_spacing) - button_spacing
    # if total_buttons_height > max_buttons_area_height: # Logic for scrollable choices or just overflow
        # For now, assume they fit or truncate as originally designed (top-down placement)

    if modal_data['choices']:
        for i, choice in enumerate(modal_data['choices']):
            button_y = content_y + i * (button_height + button_spacing)
            if button_y + button_height > modal_rect.bottom - padding:
                # Add "..." if choices overflow
                if i > 0: # Draw ... only if at least one button was drawn
                    prev_button_y = content_y + (i-1) * (button_height + button_spacing)
                    render_text(screen, "...", (content_x + 5, prev_button_y + button_height // 2 ), choice_font, COLOR_LIGHT_GREY)
                break

            choice_rect = pygame.Rect(content_x, button_y, content_width, button_height)

            button_color = COLOR_BUTTON
            # Basic hover effect (can be enhanced if mouse_pos is passed to draw_modal)
            # if 'mouse_pos' in locals() and choice_rect.collidepoint(mouse_pos):
            #    button_color = COLOR_BUTTON_HOVER

            pygame.draw.rect(screen, button_color, choice_rect, border_radius=5)

            choice_text_surf = choice_font.render(choice['text'], True, COLOR_WHITE)
            text_rect = choice_text_surf.get_rect(center=choice_rect.center)
            screen.blit(choice_text_surf, text_rect)

            # Use the action_key from modal_data for mapping, not just index
            modal_buttons[choice.get('action_key', f'modal_choice_{i}')] = choice_rect
    else: # Default "Continue" or "Close" button if no choices
        close_button_rect = pygame.Rect(modal_rect.centerx - 75, modal_rect.bottom - padding - button_height, 150, button_height)
        pygame.draw.rect(screen, COLOR_BUTTON, close_button_rect, border_radius=5)
        close_text_surf = choice_font.render("Continue", True, COLOR_WHITE)
        text_rect = close_text_surf.get_rect(center=close_button_rect.center)
        screen.blit(close_text_surf, text_rect)
        modal_buttons['modal_close'] = close_button_rect # Consistent action key

    return modal_buttons
