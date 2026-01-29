# Released under the MIT License. See LICENSE for details.
#
"""Snippets of code for use by the c++ layer."""
# (most of these are self-explanatory)
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import babase as ba

import _bascenev1
import bascenev1 as bs
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any

    import bascenev1

_end_votes: set[str] = set()
_vote_activity_id: int | None = None


def launch_main_menu_session() -> None:
    assert babase.app.classic is not None

    _bascenev1.new_host_session(babase.app.classic.get_main_menu_session())


def get_player_icon(sessionplayer: bascenev1.SessionPlayer) -> dict[str, Any]:
    info = sessionplayer.get_icon_info()
    return {
        'texture': _bascenev1.gettexture(info['texture']),
        'tint_texture': _bascenev1.gettexture(info['tint_texture']),
        'tint_color': info['tint_color'],
        'tint2_color': info['tint2_color'],
    }

def handle_command(msg: str, roster_entry: dict, client_id: int) -> None:
    display = roster_entry.get('display_string', 'Unknown Player')
    account_id = roster_entry.get('account_id')
    is_sp = roster_entry.get('singleplayer', False)
    parts = msg.split()
    cmd = parts[0].lower()

    if cmd == '/kill':
        if not is_sp:
            bs.chatmessage('Only available in Singleplayer!')
            return
        if len(parts) < 2:
            bs.chatmessage(f'{display}: usage: /kill <player_number>')
            return None
        try:
            index = int(parts[1])
        except ValueError:
            bs.chatmessage(f'{display}: player number must be an integer.')
            return None

        players = activity.players

        if index < 0 or index >= len(players):
            bs.chatmessage(
                f'{display}: player {index} does not exist '
                f'(0–{len(players) - 1}).'
            )
            return None

        player = players[index]
        actor = getattr(player, 'actor', None)

        if actor is None:
            bs.chatmessage(f'{display}: player {index} has no actor.')
            return None

        actor.die()
        bs.broadcastmessage(f'{display} killed player {index}.')
        return None
    
    elif cmd == '/super':
        if not is_sp:
            bs.chatmessage('Only available in Singleplayer!')
            return
        if len(parts) < 2:
            bs.chatmessage(f'{display}: usage: /kill <player_number>')
            return None
        try:
            index = int(parts[1])
        except ValueError:
            bs.chatmessage(f'{display}: player number must be an integer.')
            return None

        players = activity.players

        if index < 0 or index >= len(players):
            bs.chatmessage(
                f'{display}: player {index} does not exist '
                f'(0–{len(players) - 1}).'
            )
            return None

        player = players[index]
        actor = getattr(player, 'actor', None)

        if actor is None:
            bs.chatmessage(f'{display}: player {index} has no actor.')
            return None

        actor.gosuper()
        bs.broadcastmessage(f'{display} killed player {index}.')
        return None
    
    elif cmd == '/end':
        # In singleplayer, end immediately
        if is_sp:
            bs.broadcastmessage('Ending activity (/end was sent)')
            activity = _bascenev1.get_foreground_host_activity()
            if activity:
                with activity.context:
                    activity.end_game()
            return None

        # In Multiplayer, do voting
        if account_id in _end_votes:
            bs.chatmessage(f'{display}: you already voted.')
            return None

        _end_votes.add(account_id)
        bs.getsound('vote_added').play()

        voters = _end_votes
        needed = (len(voters) // 2) + 1
        current = len(_end_votes)

        bs.broadcastmessage(
            f'{display} voted to end '
            f'({current}/{needed})'
        )

        # ── Majority reached ─────────────────────────
        if current >= needed:
            bs.broadcastmessage('Vote passed! Ending activity.')
            _end_votes.clear()
            bs.getsound('vote_passed')
            activity = _bascenev1.get_foreground_host_activity()
            if activity:
                with activity.context:
                    activity.end_game()
    else:
        bs.broadcastmessage('Not a valid command!')
        return None
    return None


def filter_chat_message(msg: str, client_id: int) -> str | None:
    roster = _bascenev1.get_game_roster()

    # ── Singleplayer fallback ────────────────────
    if not roster:
        plus = bui.app.plus
        fake_entry = {
            'client_id': -1,
            'display_string': plus.get_v1_account_display_string(),
            'account_id': None,
            'is_admin': True,
            'singleplayer': True
        }

        if msg.startswith('/'):
            return handle_command(
                msg=msg,
                roster_entry=fake_entry,
                client_id=-1
            )

        return msg

    # ── Multiplayer ──────────────────────────────
    roster_entry = next(
        (p for p in roster if p.get('client_id') == client_id),
        None
    )

    if roster_entry is None:
        return None

    display = roster_entry.get('display_string', 'Unknown Player')
    account_id = roster_entry.get('account_id')

    # Require account ID in multiplayer
    if not account_id:
        print(f'Player {display} has no account id; message ignored.')
        return None

    if msg.startswith('/'):
        return handle_command(
            msg=msg,
            roster_entry=roster_entry,
            client_id=client_id
        )

    return msg



def local_chat_message(msg: str) -> None:
    classic = babase.app.classic
    assert classic is not None
    party_window = (
        None if classic.party_window is None else classic.party_window()
    )

    if party_window is not None:
        party_window.on_chat_message(msg)
