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

print('faith rules:', runtime_cards.get_faith_bonus_rules('Hun-Came'))
print('counted bonuses:', runtime_cards.get_counted_bonuses('Hun-Came', context='strength'))
print('zone graveyard via registry _get_zone_cards:', runtime_cards._get_zone_cards(engine,0,'graveyard'))

runtime_cards.refresh_conditional_faith_bonuses(engine, 0)
print('after refresh faith:', engine.state.instances[hun_uid].current_faith)
print('blessed tags:', engine.state.instances[hun_uid].blessed)
