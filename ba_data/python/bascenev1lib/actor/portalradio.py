"""Portal radio (lol)"""
import random
import bascenev1 as bs
from typing import Any, Sequence, override
from bascenev1lib.gameutils import SharedObjects

class PortalRadio(bs.Actor):
    """Yes"""
    
    # Our node.
    node: bs.Node
    
    def __init__(
        self, 
        position: Sequence[float],
        volume: int = 3 
    ):
        super().__init__()
        shared = SharedObjects.get()
        self.mesh = bs.getmesh('portalRadio')
        self.tex = bs.gettexture('portalRadio')
        scale = self.scale = 1
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'box',
                'position': position,
                'mesh': self.mesh,
                'shadow_size': 0.3,
                'body_scale': scale,
                'mesh_scale': scale,
                'light_mesh': self.mesh,
                'color_texture': self.tex,
                'materials': [shared.object_material],
            },
        )
        muslist = ['radio_DF', 'radio_TVWORLD']
        music = random.choice(muslist)
        self.sound = bs.newnode(
            'sound',
            owner=self.node,
            attrs={
                'sound': bs.getsound(music),
                'volume': volume,
                'music': True,
                'position': self.node.position,
            }
        )
        self.node.connectattr('position', self.sound, 'position')
        
    def _handle_hit(self, msg: Any) -> None:
        if msg.hit_type == 'explosion': # exploded? just die
            self.handlemessage(bs.DieMessage())
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
                bs.animate(self.node, 'mesh_scale', {0: self.scale, 0.1: 0})
                bs.timer(0.1, self.node.delete)
                bs.emitfx(
                    position=self.node.position,
                    velocity=self.node.velocity,
                    count=120,
                    scale=4.0,
                    spread=1.5,
                    chunk_type='spark',
                )
                bs.getsound('gibbed2').play(position=self.node.position)
                self.sound.volume = 0
                self.sound.delete()
        elif isinstance(msg, bs.HitMessage):
            self._handle_hit(msg)
        else:
            return super().handlemessage(msg)
        return None
            