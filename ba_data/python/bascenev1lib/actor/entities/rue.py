"""mime but a body and the eyes of ire"""
from __future__ import annotations
from bascenev1lib.gameutils import SharedObjects, TouchedMessage
from bascenev1lib.actor.spazfactory import SpazFactory
import bascenev1 as bs
import random
import math

class Rue(bs.Actor):
    """it'll approach spaz and if it does it kills him.
    hitting it makes it disappear for a while"""
    def __init__(self, actor: bs.Actor):
        super().__init__()
        self.actor = actor
        self.exists2 = False
        self.scale = 0.8
        self.volume = 1.0
        shared = SharedObjects.get()
        self.material = shared.touch_material
        self.node: bs.Node | None = None
    
    def _check(self):
        chance = 0.25
        if (
            random.random() >= chance 
            or self.exists2
            or not self.actor().rued
            or not self.actor()
            or not self.actor().node
            or not self.actor().is_alive()
        ):
            if not self.actor() or not self.actor().is_alive():
                self.stop()
                return
            if not self.actor().rued:
                self.stop()
            return
        # assuming from this point forward everything is ok
        pos = self.actor().node.position
        dist = 6
        offset_x = random.uniform(-dist, dist)
        offset_z = random.uniform(-dist, dist)
        offset_y = 1.5
        position = (pos[0] + offset_x, pos[1] + offset_y, pos[2] + offset_z)
        self.create_node(position=position)
        self._move_timer = bs.Timer(0.1, self.move_tick, repeat=True)
    
    def create_node(self, position):
        shared = SharedObjects.get()
        factory = SpazFactory.get()
        color = (1, 1, 1)
        highlight = (1, 1, 1)
        character = 'RueEntityDataLmfao'
        media = factory.get_media(character)
        roller_materials = [factory.roller_material, shared.player_material]
        self.exists2 = True
        self.node: bs.Node = bs.newnode(
            type='spaz',
            delegate=self,
            attrs={
                'color': color,
                'highlight': highlight,
                'jump_sounds': media['jump_sounds'],
                'attack_sounds': media['attack_sounds'],
                'impact_sounds': media['impact_sounds'],
                'death_sounds': media['death_sounds'],
                'pickup_sounds': media['pickup_sounds'],
                'fall_sounds': media['fall_sounds'],
                'color_texture': media['color_texture'],
                'color_mask_texture': media['color_mask_texture'],
                'head_mesh': media['head_mesh'],
                'torso_mesh': media['torso_mesh'],
                'pelvis_mesh': media['pelvis_mesh'],
                'upper_arm_mesh': media['upper_arm_mesh'],
                'forearm_mesh': media['forearm_mesh'],
                'hand_mesh': media['hand_mesh'],
                'upper_leg_mesh': media['upper_leg_mesh'],
                'lower_leg_mesh': media['lower_leg_mesh'],
                'toes_mesh': media['toes_mesh'],
                'style': 'bones',
                'materials': (self.material, shared.object_material),
            },
        )
        # good luck surviving this one
        self.node.hockey = True
        self.node.is_area_of_interest = False
        # make it stand up all the time
        self.node.handlemessage('footing', 1)
        # yeah make it stand in the position
        self.node.handlemessage(
            'stand',
            position[0],
            position[1],
            position[2],
            0,
        )
    
    def move_tick(self):
        if not self.node or not self.actor().node:
            return
        # check distance between us and spaz.
        our_pos = self.node.position
        spaz_pos = self.actor().node.position
        dx = spaz_pos[0] - our_pos[0]
        dy = spaz_pos[1] - our_pos[1] * 2
        dz = spaz_pos[2] - our_pos[2]
        
        target_pos_raw = bs.Vec3(spaz_pos)
        our_pos = bs.Vec3(our_pos)
        diff = target_pos_raw - our_pos
        dist = diff.length()
        to_target = diff.normalized()
        
        # make the rue's spaz node point towards spaz!
        nerfed = 0.7
        self.node.move_left_right = to_target.x * (dist * nerfed)
        self.node.move_up_down = -to_target.z * (dist * nerfed)
    
    def _delete(self):
        if self.node:
            self.node.delete()
            self.node = None
        self.exists2 = False
    
    def start(self):
        self.check_timer = bs.Timer(0.8, self._check, repeat=True)
    
    def stop(self):
        self.check_timer = None
        self._delete()
    
    def handlemessage(self, msg):
        # ouch. we just got hit.
        if isinstance(msg, bs.HitMessage):
            # we only accept hits from our actor's player
            if (
                msg.get_source_player(bs.Player) 
                is self.actor().source_player
            ):
                bs.getsound('mhurt').play(
                    volume=self.volume, 
                    position=self.node.position
                )
                self._delete()
        # aha! came into contact with something
        elif isinstance(msg, TouchedMessage):
            from bascenev1lib.actor.spaz import Spaz
            toucher = bs.getcollision().opposingnode
            actor = None
            if toucher:
                actor = toucher.getdelegate(Spaz)
            # we don't check if it's our actor here, 
            # so irregardless of whoever we touch we kill
            if actor:
                actor.impulse(x=-50, y=190)
                actor.shatter()
                actor.killed_by_entity('rue')
        # ow. we fell out of bounds
        elif isinstance(msg, bs.OutOfBoundsMessage):
            bs.getsound('mhurt').play(
                volume=self.volume, 
                position=self.node.position
            )
            self._delete()
        else:
            return super().handlemessage(msg) # Augment the very standard behavior.
        return None