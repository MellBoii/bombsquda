"""Actor for a chaos emerald."""
import random
import bascenev1 as bs
from typing import Any, Sequence, override
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.emerald import TouchedMsg
    
class UKHook(bs.Actor):
    """Hook"""
    node: bs.Node
    
    def __init__(
        self,
        position: Sequence[float],
        owner: bs.Actor,
    ):
        super().__init__()
        self.mesh = bs.getmesh('shrapnel1')
        self.tex = bs.gettexture('eggTex2')
        self.scale = 0.6
        self.bscale = 0.3
        self.material = bs.Material()
        self.material.add_actions(
            conditions=('they_have_material', SharedObjects.get().player_material),
            actions=(
                ('message', 'our_node', 'at_connect', TouchedMsg()),
                ('modify_part_collision', 'collide', False),
                ('modify_part_collision', 'physical', True),
            ),
        )
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'box',
                'body_scale': self.bscale,
                'position': position,
                'mesh': self.mesh,
                'mesh_scale': 0,
                'light_mesh': self.mesh,
                'shadow_size': 0.3,
                'color_texture': self.tex,
                'reflection': 'powerup',
                'reflection_scale': [1.0],
                'materials': (self.material, SharedObjects.get().object_material),
            },
        )
        bs.animate(self.node, 'mesh_scale', {0: 0, 0.2: self.scale})
        
    def _handle_hit(self, msg: Any) -> None:
        # likely hit by a punch; apply impulse
        self.node.handlemessage(
            'impulse',
            msg.pos[0],
            msg.pos[1],
            msg.pos[2],
            msg.velocity[0],
            msg.velocity[1],
            msg.velocity[2],
            msg.magnitude,
            msg.velocity_magnitude,
            msg.radius,
            0,
            msg.velocity[0],
            msg.velocity[1],
            msg.velocity[2],
        )
        
    @override
    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired
        if isinstance(msg, bs.DieMessage):
            if not self.node:
                return
            if msg.immediate:
                self.node.delete()
            else:
                bs.animate(self.node, 'mesh_scale', {0: self.mscale, 0.1: 0})
                bs.timer(0.1, self.node.delete)

        elif isinstance(msg, TouchedMsg):
            if not self.node:
                return
            toucher = bs.getcollision().opposingnode
            isspaz = toucher.getnodetype() == 'spaz'
            actor = toucher.getdelegate(bs.Actor)
            # very long list of conditions
            if (
                not toucher
                or not actor
                or not actor.is_alive()
                or not isspaz
            ):
                return
            toucher.handlemessage(HookedMessage())

        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage(immediate=True))

        elif isinstance(msg, bs.HitMessage):
            self._handle_hit(msg)
        else:
            return super().handlemessage(msg)
        return None