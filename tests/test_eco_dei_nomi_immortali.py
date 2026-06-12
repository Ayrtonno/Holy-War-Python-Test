from holywar.core.engine import GameEngine
from holywar.core.state import CardInstance, GameState, PlayerState
from holywar.data.models import CardDefinition
from holywar.effects.runtime import runtime_cards


def _card(name: str, card_type: str, faith: int | None = 1, strength: int | None = 1) -> CardDefinition:
    return CardDefinition(
        name=name,
        card_type=card_type,
        crosses="",
        faith=faith,
        strength=strength,
        effect_text="",
        expansion="Taoismo",
    )


def test_eco_dei_nomi_immortali_summons_different_ba_xian_from_hand() -> None:
    eco_uid = "c00012"
    field_baxian_uid = "c10001"
    hand_baxian_uid = "c10002"

    instances = {
        eco_uid: CardInstance(eco_uid, _card("Eco dei Nomi Immortali", "Benedizione"), 0, 1),
        field_baxian_uid: CardInstance(field_baxian_uid, _card("Lu Dongbin", "Santo", 3, 3), 0, 3),
        hand_baxian_uid: CardInstance(hand_baxian_uid, _card("Han Xiangzi", "Santo", 3, 3), 0, 3),
    }

    p1 = PlayerState.empty("P1")
    p2 = PlayerState.empty("P2")
    p1.hand = [eco_uid, hand_baxian_uid]
    p1.attack[0] = field_baxian_uid

    engine = GameEngine(
        GameState(
            players=[p1, p2],
            instances=instances,
            active_player=0,
            turn_number=1,
            phase="main",
        )
    )

    runtime_cards.resolve_play(
        engine,
        0,
        eco_uid,
        f"seq:0={field_baxian_uid};;2={hand_baxian_uid}",
    )

    assert hand_baxian_uid not in engine.state.players[0].hand
    assert hand_baxian_uid in engine.state.players[0].attack + engine.state.players[0].defense
