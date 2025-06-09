# cosmic_drifter_py/events.py
# Defines the structure for events and provides some example events.
# In a larger game, this could be loaded from JSON or a database.

# Event functions can modify game_state and should return a log message.
# game_state will be passed to condition and outcome functions.

import random # Make sure random is available for outcomes

# Example Event Definitions (more to be ported from JS EVENTS array)
# Each event is a dictionary.
# 'id': unique string identifier
# 'title': string for the modal title
# 'description': string or function(game_state) -> string for modal body
# 'condition': (optional) function(game_state, current_solar_system) -> bool. If event can trigger.
# 'choices': list of choice dictionaries
#   - 'text': string for the button
#   - 'outcome': function(game_state) -> string (log message)

EVENTS = [
    {
        'id': "derelict_ship",
        'title': "Derelict Vessel",
        'description': "You detect a drifting ship nearby, showing no signs of life. It might contain valuable salvage... or dangers.",
        'condition': lambda gs, sys: gs.player_resources.scrap < 100, # Example: more likely if low on scrap
        'choices': [
            {
                'text': "Board the ship (Risky)",
                'outcome': lambda gs: (
                    setattr(gs.player_resources, 'scrap', gs.player_resources.scrap + random.randint(20, 50)),
                    setattr(gs.player_resources, 'hull', max(0, gs.player_resources.hull - random.randint(0, 15))),
                    "Boarding party returns with some scrap, but the ship suffered minor damage."
                )[-1] # Return only the message
            },
            {
                'text': "Scan from afar",
                'outcome': lambda gs: (
                    setattr(gs.player_resources, 'scrap', gs.player_resources.scrap + random.randint(5, 15)),
                    "Scans reveal a small amount of easily recoverable materials."
                )[-1]
            },
            {
                'text': "Leave it",
                'outcome': lambda gs: "You decide to leave the derelict vessel undisturbed."
            }
        ]
    },
    {
        'id': "asteroid_field",
        'title': "Rich Asteroid Field",
        'description': "Sensors pick up a dense asteroid field rich in valuable ores.",
        'condition': lambda gs, sys: True, # Always possible
        'choices': [
            {
                'text': "Mine the asteroids (+Scrap, risk Hull dmg)",
                'outcome': lambda gs: (
                    setattr(gs.player_resources, 'scrap', gs.player_resources.scrap + random.randint(15,40)),
                    setattr(gs.player_resources, 'hull', max(0, gs.player_resources.hull - random.randint(0,10))),
                    "Mining operations were successful, though the hull took a few hits."
                )[-1]
            },
            {
                'text': "Carefully navigate through",
                'outcome': lambda gs: "You expertly pilot through the dense field."
            }
        ]
    },
    {
        'id': "nothing_event", # Fallback event
        'title': "All Quiet",
        'description': "The system appears stable and uneventful. You have a moment to check your ship's status.",
        'condition': lambda gs, sys: True,
        'choices': [
            {
                'text': "Perform routine checks",
                'outcome': lambda gs: "All systems nominal. Ready to proceed."
            }
        ]
    },
    {
        'id': "distress_signal",
        'title': "Distress Signal",
        'description': lambda gs: f"A faint distress signal. It seems to be coming from a small freighter in {gs.current_beacon.solar_system.name if gs.current_beacon and gs.current_beacon.solar_system else 'this system'}.",
        'choices': [
            {
                'text': "Offer assistance (+Scrap if lucky, -Fuel)",
                'outcome': lambda gs: (
                    setattr(gs, '_previous_scrap_for_event', gs.player_resources.scrap), # Store before change
                    setattr(gs.player_resources, 'fuel', max(0, gs.player_resources.fuel - 3)),
                    (lambda: (setattr(gs.player_resources, 'scrap', gs.player_resources.scrap + random.randint(10,30)),"They reward you handsomely!"))() if random.random() > 0.4 else (lambda: "They were grateful but had nothing to offer.")(),
                    "Assistance rendered." # Base message part
                )[-1] + " " + ( "They reward you handsomely with some spare parts!" if gs.player_resources.scrap > getattr(gs, '_previous_scrap_for_event', gs.player_resources.scrap) else "They were grateful but had nothing to offer beyond thanks.")
            },
            {
                'text': "Ignore it (Conserve resources)",
                'outcome': lambda gs: "You decide the risk isn't worth it and continue on your way."
            }
        ]
    }
]
