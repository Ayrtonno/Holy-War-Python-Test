from holywar.core.state import GameState, PlayerState, CardInstance
from holywar.data.models import CardDefinition
from holywar.core.engine import GameEngine
from holywar.effects.runtime import runtime_cards

p0 = PlayerState.empty("P1")
p1 = PlayerState.empty("P2")
instances = {}

def make_def(name):
    return CardDefinition.from_dict({"name": name, "card_type": "santo", "crosses": "", "faith": 0, "strength": 0, "effect_text": "", "expansion": ""})

hun_def = make_def("Hun-Came")
hun_uid = "c00001"
instances[hun_uid] = CardInstance(uid=hun_uid, definition=hun_def, owner=0, current_faith=hun_def.faith)

p0.attack[0] = hun_uid
for i in range(2, 9):
    uid = f"c{i:05d}"
    defn = make_def(f"Filler{i}")
    instances[uid] = CardInstance(uid=uid, definition=defn, owner=0, current_faith=defn.faith)

p0.deck = [f"c{i:05d}" for i in range(2, 7)]
p0.graveyard = [f"c{i:05d}" for i in range(7, 9)]

state = GameState(players=[p0, p1], instances=instances, active_player=0, turn_number=0, flags={"oltretomba_promise_active": {"0": True, "1": False}})
engine = GameEngine(state, seed=1)
runtime_cards.ensure_all_cards_migrated(engine)

print('counted_bonuses:', runtime_cards.get_counted_bonuses('Hun-Came', context='strength'))

req = runtime_cards.get_counted_bonuses('Hun-Came', context='strength')[0].get('requirement')
print('requirement:', req)

candidates = runtime_cards._collect_cards_for_requirement(engine, 0, req)
print('candidates raw:', candidates)
print('len candidates:', len(candidates))

# Show _get_zone_cards behavior
print('graveyard cards via _get_zone_cards:', runtime_cards._get_zone_cards(engine, 0, 'graveyard'))
print('deck cards via _get_zone_cards:', runtime_cards._get_zone_cards(engine, 0, 'deck'))
print('merged when graveyard query:', runtime_cards._get_zone_cards(engine, 0, 'graveyard'))

print('effective strength:', engine.get_effective_strength(hun_uid))
print('current faith:', engine.state.instances[hun_uid].current_faith)
