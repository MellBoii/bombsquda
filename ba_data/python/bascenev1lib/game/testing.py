# Released under the MIT License. See LICENSE for details.
#
"""Hot potato-ish gamemode that uses the Spongebob powerup mechanic."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING, override
from bascenev1lib.dialog import DialogueManager
from bascenev1lib.gameutils import SharedObjects
import bascenev1 as bs
import random
import time

if TYPE_CHECKING:
    from typing import Any, Sequence


class Player(bs.Player['Team']):
    """Our player type for this game."""


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.survival_seconds: int | None = None
        
class TouchedMsg:
    pass
        
class SignpostActor(bs.Actor):
    """
    Our signpost from Sonic CD. All it does is give 
    a message to whoever touches it.
    """
    node: bs.Node
    
    def __init__(
        self,
        position: Sequence[float] = (0.0, 3.0, 0.0),
        type: str = 'future'
    ):
        super().__init__()
        self.mesh = bs.getmesh('warpPost')
        texname = 'warp' + type
        self.tex = bs.gettexture(texname)
        self.type = type
        self.signpost_mat = bs.Material()
        self.stop_giving = False
        self.signpost_mat.add_actions(
            conditions=('they_have_material', SharedObjects.get().player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True),
                ('message', 'our_node', 'at_connect', TouchedMsg()),
            ),
        )
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'box',
                'position': position,
                'mesh': self.mesh,
                'light_mesh': self.mesh,
                'shadow_size': 0.5,
                'color_texture': self.tex,
                'reflection': 'powerup',
                'reflection_scale': [1.0],
                'materials': (self.signpost_mat, SharedObjects.get().object_material),
            },
        )

    @override
    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired
        if isinstance(msg, TouchedMsg):
            # stop giving the states if
            # we shouldn't anymore
            if self.stop_giving == True:
                return
            node = bs.getcollision().opposingnode
            self.activity.state = self.type
            bs.getsound('cd_' + self.type).play(position=self.node.position)
            self.stop_giving = True
        elif isinstance(msg, bs.DieMessage):
            if self.node:
                if msg.immediate:
                    self.node.delete()
                else:
                    bs.animate(self.node, 'mesh_scale', {0: 1, 0.6: 0})
                    bs.timer(0.6, self.node.delete)

# ba_meta export bascenev1.GameActivity
class TestActivity(bs.TeamGameActivity[Player, Team]):
    """A last-standing gametype based on Hot Potato."""

    name = 'Testing Grounds'
    description = 'Placing the holder!'
    announce_player_deaths = True
    
    def __init__(self, settings: dict):
        super().__init__(settings)
        # attribuuutes -------------------------------------
        self.state = None # which part can we time travel to
        # ee is short for eighty eight (88)
        # but python doesn't allow attrs starting
        # with numbers (gives a SyntaxError) so...
        self.eemiles = False
        self.which_future = 'bad' # how's the future?
        self._tt_pending = False # is there a time travel check pending?
        self._tt_halfway = False # halfway through the time travel?
        # --------------------------------------------------
        
    # do the thing!
    def speedcheck(self, p: bs.Player):
        speed = p.actor.getspeed()
        spaz = p.actor

        if self.state is None:
            return

        if speed > 4.0:
            bs.emitfx(
                position=spaz.node.position,
                velocity=spaz.node.velocity,
                count=20,
                scale=1.2,
                spread=1.0,
                chunk_type='spark',
            )

            self.eemiles = True

            if not self._tt_pending:
                self._tt_pending = True
                self._tt_halfway = True

                # Halfway check (3 seconds)
                bs.timer(3.0, lambda: self._halfway_check(p))

                # Final check (6 seconds)
                bs.timer(6.0, lambda: self.checkfortt(plr=p))

        else:
            self.eemiles = False
    
    def _halfway_check(self, p: bs.Player):
        if not self._tt_halfway:
            return

        if not self.eemiles:
            print('Lost speed halfway — aborting time travel')
            self.state = None
            self._tt_pending = False
            self._tt_halfway = False

    def checkfortt(self, plr: bs.Player):
        self._tt_pending = False
        self._tt_halfway = False

        print('checking...')

        if self.state is None:
            print('state is none, returning')
            return

        if not self.eemiles:
            print('not eighty eight miles!!!')
            self.state = None
            return

        print('is eighty eight miles, should time travel')

        node = plr.actor.node
        node.is_area_of_interest = False

        bs.emitfx(
            position=node.position,
            velocity=node.velocity,
            count=120,
            scale=4.0,
            spread=1.5,
            chunk_type='spark',
        )
        bs.getsound('cd_ringed').play(position=node.position)
        self.spdchktmr = None
        bs.timer(0.1, node.delete)
        self.state = None

        
            
    @override
    def on_begin(self) -> None:
        super().on_begin()
        self.signpost = SignpostActor()
        DialogueManager(
            self,
            [
                {
                    "character": "meliso",
                    "expression": "shocked",
                    "name": "Meliso",
                    "text": "holy smokes is that spaz!?",
                    "sound": "diagvoice/meliso",
                },
                {
                    "text": "...",
                    "sound": "tap",
                },
                {
                    "character": "spaz",
                    "expression": "angry",
                    "name": "Newbie",
                    "text": "Shut up.",
                    "sound": "diagvoice/spaz",
                },
                {
                    "character": "meliso",
                    "expression": "neutral",
                    "name": "Meliso",
                    "text": "well jeez, you're really \nboring you know!",
                    "sound": "diagvoice/meliso",
                },
                {
                    "character": "spaz",
                    "expression": "angry",
                    "name": "Newbie",
                    "text": "For not letting you FUCKING chainsaw me \ninto 2 halves like you tried last time? \nIf that's boring, then being boring is now normal.",
                    "sound": "diagvoice/spaz",
                },
            ],
        )
            
    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        actor = self.spawn_player_spaz(player)
        self.spdchktmr = bs.Timer(0.1, lambda: self.speedcheck(player), repeat=True)
        return actor
        
    @override
    def handlemessage(self, msg: Any) -> Any:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)

            player = msg.getplayer(Player)
            self.spdchktmr = None
            self.respawn_player(player)
