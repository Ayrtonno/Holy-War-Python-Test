from __future__ import annotations

import unicodedata
from collections.abc import Callable
from typing import Any


EffectFn = Callable[[Any, int, str, str | None], Any]
EnterFn = Callable[[Any, int, str], Any]
ActivateFn = Callable[[Any, int, str, str | None], Any]

NOT_HANDLED = object()

_play_handlers: dict[str, EffectFn] = {}
_enter_handlers: dict[str, EnterFn] = {}
_activate_handlers: dict[str, ActivateFn] = {}


def normalize_card_name(name: str) -> str:
    value = unicodedata.normalize("NFKD", name)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


def register_play(card_name: str):
    def decorator(func: EffectFn) -> EffectFn:
        _play_handlers[normalize_card_name(card_name)] = func
        return func

    return decorator


def register_enter(card_name: str):
    def decorator(func: EnterFn) -> EnterFn:
        _enter_handlers[normalize_card_name(card_name)] = func
        return func

    return decorator


def register_activate(card_name: str):
    def decorator(func: ActivateFn) -> ActivateFn:
        _activate_handlers[normalize_card_name(card_name)] = func
        return func

    return decorator


def get_play(card_name: str) -> EffectFn | None:
    return _play_handlers.get(normalize_card_name(card_name))


def get_enter(card_name: str) -> EnterFn | None:
    return _enter_handlers.get(normalize_card_name(card_name))


def get_activate(card_name: str) -> ActivateFn | None:
    return _activate_handlers.get(normalize_card_name(card_name))
