"""Script for Ire, the entity that forces a spaz to jump (at correct timing) or die."""
from __future__ import annotations
from typing import override
import bascenev1 as bs
import fromgoverhaul.mell_resources as mell
import random
from bascenev1lib.actor.image_looped import LoopingImageAnimation

class Ire(bs.Actor):
    """spaz must jump when it strikes, or he dies
    'it's pronounced eye-r-uh!', was what this docstring originally said
    (and yes, that's how it's pronounced and i'm standing by that)"""
    def __init__(self, actor: bs.Actor):
        super().__init__()
        self.actor = actor
        self.color = None
        self.high = None
        self.head = None
        self._x = 0
        self._y = 0
        self._scale = 0
        self.tick_timer = None
        self.exists2 = False
        self.name_text = None
        self.check_timer = None
        self._slot = 0
        self.times_avoided = 0

    def _get_free_space(self):
        # ok... get a free space based on how many of us
        # there are
        if not hasattr(self._activity(), 'entities'):
            self._activity().entities = {}
        def _get_free_slot(entities: dict) -> int:
            slot = 0
            while slot in entities:
                slot += 1
            return slot
        entities = self._activity().entities
        self._slot = _get_free_slot(entities)
        if len(self.getactivity().players) > 0:
            self.color = self.actor().node.color
            self.high = self.actor().node.highlight
        else:
            self.color = (1, 1, 1)
            self.high = (0, 0, 0)
        entities[self._slot] = self
        max_per_column = 5
        col = self._slot // max_per_column
        row = self._slot % max_per_column
        spacing = 140
        x = -500 + (col * 200)
        y = 100 + (row * spacing)
        self._x = x
        self._y = y
    
    def _delete(self):
        # delete nodes
        if getattr(self.head, 'node', None):
            self.head.node.delete()
        if self.name_text:
            self.name_text.delete()
        self.exists2 = False
        if not hasattr(self._activity(), 'entities'):
            self._activity().entities = {}
        entities = self._activity().entities
        entities.pop(self._slot, None)  
    
    # note; should rename this to 'recreate_eye'
    # ..get it? because ire's a eye? okay whatever.
    def recreate_head(
        self, 
        tex: str = 'ktransb',
        frames: int = 1, 
        delay: int = 0.05,
        repeat: bool = True,
    ):
        pos = (self._x, self._y)
        scale = (self._scale, self._scale)
        if self.head:
            self.head.node.delete()
        # transition in persay idk man
        self.head = LoopingImageAnimation(
            tex, 
            f'{tex}CM', 
            frame_count=frames, 
            frame_delay=delay, 
            scale=scale, 
            position=pos,
            loop=repeat,
            attach="bottomCenter",
        )
        self.head.node.tint_color = self.color
        self.head.node.tint2_color = self.high
    
    def _check(self, chance = 0.12):
        # Ire will do some checks of whether the actor exists, 
        # whether the actor has a node, 
        # whether the actor is alive and still kicking, 
        # whether the actor should have Ire's status, 
        # and whether the chance is exactly the one we should pop up with.
        # This is obviously to prevent us from appearing where we'll bug out,
        # or maybe when we shouldn't appear.
        if (
            random.random() >= chance 
            or self.exists2
            or not self.actor().ired
            or not self.actor()
            or not self.actor().node
            or not self.actor().is_alive()
            or (self.actor().sorrow and self.actor().sorrow.exists2)
        ):
            if not self.actor() or not self.actor().is_alive() or not self.actor().node:
                self.stop()
                return
            if not self.actor().ired:
                self.stop()
            return
        if not self.actor().node:
            self._delete()
            return
        self._get_free_space()
        scale = 200
        self._scale = scale
        self.exists2 = True
        self.recreate_head('iappr', frames=3, delay=0.08, repeat=True)
        self.name_text =  bs.newnode(
            'text',
            delegate=self,
            attrs={
                'text': f'({self.actor().node.name})',
                'scale': 1.0,
                'color': self.actor().node.color,
                'h_align': 'center',
                'position': (self._x - 3, self._y - 90),
                'v_attach': 'bottom',
                'front': True,
            },
        )
        bs.animate(self.name_text, 'opacity', {
            0.0: 0,
            0.5: 0.5,
        })
        bs.getsound('iappr').play(1.5)
        bs.timer(1.7, self._ready)
    
    def _check_ungrounded(self):
        if not self.actor().node or not self.actor().is_alive():
            self.actor().ired = False
            self._delete()
            return
        # standing determines whether 
        # spaz is on ground
        if self.actor().standing == True:
            self._death()
        else:
            self._animate_out()
        self.tick_timer = None
        return
    
    def _animate_out(self):
        self.times_avoided += 1
        # if we got avoided too many times, start doing another expression
        if self.times_avoided >= 6:
            expression = 'iangry'
        else:
            expression = 'ifrown'
        self.recreate_head(expression, frames=3, delay=0.05, repeat=True)
        bs.timer(0.5, self._delete)
    
    def _death(self):
        bs.getsound('ideath').play(1.2)
        self.recreate_head('istatic', frames=4, delay=0.03, repeat=True)
        mell.shake_node(
            self.head.node,
            duration=0.6,
            interval=0.0001,
            intensity=2,
        )
        bs.timer(0.6, lambda: mell.shake_node(
                self.head.node,
                duration=0.6,
                interval=0.0001,
                intensity=7,
            )
        )
        def die():
            # dont die if the player is parrying
            if self.actor().parrying:
                self.actor().sugarcoat_overlay(sound='bellMed', image='sugarcoatparry')
                self.actor().mpa()
                self.actor().smashkill(sound='thunder', autodie=False)
                self._delete()
                return
            self.actor().ired = False
            # we reuse hardmode's death because it's similar
            self.actor().hardmode_death()
            self.actor().die()
            self.actor().impulse(y=500)
            self.actor().killed_by_entity('ire')
            self._delete()
            bs.getsound('shatter_worse').play(1.2)
        bs.timer(1.2, die)
        bs.timer(1.1, self.actor().wheelchair_warning)
    
    def _anim_attack(self):
        self.recreate_head('iatk', frames=4, delay=0.05, repeat=False)
        bs.getsound('iatk').play(1.5)
        bs.timer(0.4, self._check_ungrounded)
    
    def _ready(self):
        # flash red, basically
        self.recreate_head('iready', frames=3, delay=0.06, repeat=True)
        dict = {
            0: self.color,
            0.1: (5, 0, 0),
            0.3: self.color,
        }
        dict2 = {
            0: self.high,
            0.1: (12, 0, 0),
            0.3: self.high,
        }
        bs.animate_array(self.head.node, 'tint_color', 3, dict)
        bs.animate_array(self.head.node, 'tint2_color', 3, dict2)
        bs.getsound('iready').play(1.5)
        bs.timer(1.1, self._anim_attack)
    
    def start(self):
        self.check_timer = bs.Timer(1.2, self._check, repeat=True)
    
    def stop(self):
        self.check_timer = None
        self._delete()
    
    @override
    def handlemessage(self, msg):
        if isinstance(msg, bs.DieMessage):
            # we'll check if the spaz still exists and has us, and if it doesn't we can stop
            if self.actor() and self.actor().node and not self.actor().ired:
                self.stop()
            elif not self.actor() or not self.actor().node:
                self.stop()
            else:
                self._delete()
        else:
            super().handlemessage(msg) # Augment standard behavior.