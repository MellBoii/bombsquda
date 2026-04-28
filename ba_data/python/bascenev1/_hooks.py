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
reset_timer = None


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
    activity = bs.get_foreground_host_activity()
    if not activity:
        return msg

    if cmd == '/kill':
        if not is_sp:
            bs.chatmessage('Only available in Singleplayer!')
            return
        if len(parts) < 2:
            bs.chatmessage(f'{display}: usage: /kill <player_index>')
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
        with activity.context:
            actor.die()
        bs.broadcastmessage(f'{display} killed player {index}.')
        return None
    
    elif cmd == '/end':
        # In singleplayer, end immediately
        if is_sp:
            bs.broadcastmessage('Ending activity (/end was sent)')
            if activity:
                with activity.context:
                    if hasattr(activity, 'end_game'):
                        activity.end_game()
            return None
        players = activity.players
        try:
            player = players[client_id]
        except IndexError:
            player = None
        # In Multiplayer, do voting
        if not player:
            bs.chatmessage(f'{display}, you have to be in-game to vote!')
            return None
        if client_id in _end_votes:
            bs.chatmessage(f'{player.getname()}, you already voted!')
            return None
        if not _end_votes:
            global reset_timer
            with activity.context:
                bs.getsound('vote_started').play()
            reset_timer = ba.AppTimer(8, reset_end_votes)
        else:
            with activity.context:
                bs.getsound('vote_added').play()
            reset_timer = ba.AppTimer(8, reset_end_votes)
        _end_votes.add(client_id)
            
        voters = _end_votes
        needed = len(bs.get_game_roster())
        current = len(_end_votes)
        
        with activity.context:
            bs.broadcastmessage(
                f'{player.getname()} voted to end the game '
                f'({current}/{needed})'
            )

        # ── Majority reached ─────────────────────────
        if current >= needed:
            _end_votes.clear()
            if activity:
                with activity.context:
                    bs.broadcastmessage('Vote passed! Ending activity.')
                    reset_timer = None
                    bs.getsound('vote_passed').play()
                    activity.end_game()
    else:
        bs.broadcastmessage('Not a valid command!')
        return None
    return None

def reset_end_votes():
    activity = bs.get_foreground_host_activity()
    bs.broadcastmessage("The vote was canceled (not enough votes).")
    _end_votes.clear()
    with activity.context:
        bs.getsound('vote_failed').play()

def filter_chat_message(msg: str, client_id: int) -> str | None:
    roster = bs.get_game_roster()
    activity = bs.get_foreground_host_activity()
    if not activity:
        return msg
    # ── Singleplayer fallback ────────────────────
    if not roster:
        plus = bui.app.plus
        fake_entry = {
            'client_id': 0,
            'display_string': plus.get_v1_account_display_string(),
            'account_id': None,
            'is_admin': True,
            'singleplayer': True
        }

        if msg.startswith('/'):
            return handle_command(
                msg=msg,
                roster_entry=fake_entry,
                client_id=0
            )
        if activity:
            with activity.context:
                try:
                    # We're in singleplayer, so presumably
                    # whoever's sending the message is P1.
                    player = activity.players[0]
                    player.actor.say(msg)
                except Exception as e:
                    pass
        return msg

    # ── Multiplayer ──────────────────────────────
    roster_entry = next(
        (p for p in roster if p.get('client_id') == client_id),
        None
    )

    if roster_entry is None:
        return msg

    display = roster_entry.get('display_string', 'Unknown Player')
    client_id = roster_entry.get('client_id')
    players = roster_entry.get('players')
    player_id = None
    if players:
        name = players[0].get('name')
        player = next(
            (plr for plr in activity.players if plr.getname() == name),
            None
        )
        try:
            player_id = activity.players.index(player)
        except:
            player_id = None

    if msg.startswith('/'):
        return handle_command(
            msg=msg,
            roster_entry=roster_entry,
            client_id=player_id
        )
    if activity:
        with activity.context:
            try:
                player = activity.players[player_id]
                player.actor.say(msg, melblow=False)
            except Exception as e:
                pass
    return msg



def local_chat_message(msg: str) -> None:
    classic = babase.app.classic
    assert classic is not None
    party_window = (
        None if classic.party_window is None else classic.party_window()
    )

    if party_window is not None:
        party_window.on_chat_message(msg)
