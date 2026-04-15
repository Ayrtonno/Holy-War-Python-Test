from __future__ import annotations

CARD_NAME = 'Resurrezione del Sacerdote'

SCRIPT = {'on_play_mode': 'scripted',
 'on_enter_mode': 'auto',
 'on_activate_mode': 'auto',
 'triggered_effects': [],
 'on_play_actions': [{'effect': {'action': 'draw_cards', 'amount': 5, 'target_player': 'me'}}]}
