from __future__ import annotations

CARD_NAME = 'Avidità di Av'

SCRIPT = {'on_play_mode': 'scripted',
 'on_enter_mode': 'auto',
 'on_activate_mode': 'auto',
 'triggered_effects': [],
 'on_play_actions': [
                        {'effect': {'action': 'draw_cards', 
                            'amount': 3, 
                            'target_player': 'me'}
                        },
                        {'effect': {'action': 'draw_cards',
                            'amount': 3,
                            'target_player': 'opponent'}
                        }
                    ]
                }
