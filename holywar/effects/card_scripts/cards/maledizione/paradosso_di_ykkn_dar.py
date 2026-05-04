from __future__ import annotations

CARD_NAME = 'Paradosso di Ykknødar'

SCRIPT = {'on_play_mode': 'scripted',
 'on_enter_mode': 'auto',
 'on_activate_mode': 'auto',
 'triggered_effects': [],
 'on_play_actions': [{'effect': {'action': 'excommunicate_top_cards_from_relicario',
                                 'amount': 5,
                                 'target_player': 'me'}},
                     {'effect': {'action': 'excommunicate_top_cards_from_relicario',
                                 'amount': 5,
                                 'target_player': 'opponent'}},
                     {'effect': {'action': 'draw_by_zone_count_comparison',
                                 'amount': 3,
                                 'compare_zone': 'excommunicated',
                                 'target_player': 'me',
                                 'compare_target_player': 'opponent',
                                 'tie_policy': 'both',
                                 'tie_amount': 3}}]}
