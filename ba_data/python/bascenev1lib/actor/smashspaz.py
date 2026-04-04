"""Subclass for PlayerSpaz."""
from __future__ import annotations
from typing import override

import bascenev1 as bs
import babase as ba
import random
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.spazfactory import SpazFactory
PERCENT_COLORS = [
    (0,   (1, 1, 1)),      # white
    (50,  (1, 1, 0)),      # yellow
    (100, (1, 0, 0)),      # red
    (200, (1, 0, 1)),      # magenta
    (300, (0.5, 0, 1)),    # purple
]

def _lerp_color(c1, c2, t: float):
    return (
        c1[0] + (c2[0] - c1[0]) * t,
        c1[1] + (c2[1] - c1[1]) * t,
        c1[2] + (c2[2] - c1[2]) * t,
    )
    
def _get_percent_color(percent: float):
    points = PERCENT_COLORS

    # Below first threshold
    if percent <= points[0][0]:
        return points[0][1]

    # Between thresholds
    for i in range(len(points) - 1):
        p1, c1 = points[i]
        p2, c2 = points[i + 1]

        if p1 <= percent <= p2:
            t = (percent - p1) / (p2 - p1)  # 0 → 1
            return _lerp_color(c1, c2, t)

    # Above last threshold
    return points[-1][1]

class SmashSpaz(PlayerSpaz):
    """A separate PlayerSpaz type made 
    to act differently on smash bros."""
    def __init__(
        self,
        player: bs.Player,
        *,
        color: Sequence[float] = (1.0, 1.0, 1.0),
        highlight: Sequence[float] = (0.5, 0.5, 0.5),
        character: str = 'Spaz',
        powerups_expire: bool = True,
    ):
        super().__init__(
            color=color,
            highlight=highlight,
            character=character,
            powerups_expire=powerups_expire,
            player=player,
        )
        self.percent_text = None
        self.percentage = 0
        self.percentage_clamper = 17
        self.impulse_clamper = 24
        bs.timer(0.3, self.update_percent_text)
    
    def update_percent_text(self):
        if not self.node or not self.is_alive():
            if self.percent_text:
                self.percent_text.delete()
                self.percent_text = None
            return
        color = _get_percent_color(self.percentage)
        if not self.percent_text:
            mathnode = bs.newnode(
                'math',
                owner=self.node,
                attrs={'input1': (0, 1.5, 0), 'operation': 'add'},
            )
            self.node.connectattr('torso_position', mathnode, 'input2')
            self.percent_text = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'text': f'{str(self.percentage)}%',
                    'in_world': True,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'scale': 0.015,
                    'color': color,
                    'h_align': 'center',
                },
            )
            mathnode.connectattr('output', self.percent_text, 'position')
        else:
            self.percent_text.text = f'{str(self.percentage)}%'
            self.percent_text.color = color
    
    def on_jump_press(self):
        super().on_jump_press()
        # Apply a bit more impulse so we can jump high.
        # This is to encourage more jumping than BOMB 
        # jumping, since we can't grab.
        if self.standing:
            self.impulse(y=160)

    @override
    def handlemessage(self, msg):
        # Oh boy time to overide everything
        if isinstance(msg, bs.HitMessage):
            if not self.node:
                return None
            if self.node.invincible:
                SpazFactory.get().block_sound.play(
                    1.0,
                    position=self.node.position,
                )
                return True
            if (
                msg.hit_subtype == 'non_self_hurt' 
                and msg.bombowner == self.node
            ):
                return True
            if self.parrying == True:
                # Check for source node. Most likely being punched.
                if msg.srcnode:
                    # Get the other spaz's node.
                    otherspaz = msg.srcnode.getdelegate(bs.Actor)
                    # If the otherspaz is parrying, do something
                    # to prevent a infinite recursion.
                    if otherspaz.parrying == True:
                        xforce = -200
                        yforce = 200
                        v = (-self.node.velocity[0], -self.node.velocity[1], -self.node.velocity[2])
                        v2 = self.node.velocity   
                        hurtiness = 3.8
                        flash_color = (1.0, 0.8, 0.4)
                        bs.getsound('bellHigh').play(position=self.node.position)
                        bs.getsound('OUUHH').play(position=self.node.position)
                        self.impulse(xforce, yforce)
                        bs.timer(0.01, lambda: self.impulse(xforce))
                        # FIXME: for some reason impulse doesn't 
                        # work on other node?
                        msg.srcnode.handlemessage('impulse', 
                            msg.srcnode.position[0], 
                            msg.srcnode.position[1], 
                            msg.srcnode.position[2],
                            0, 25, 0,
                            yforce, 0.05, 0, 0,
                            0, 20*400, 0
                        )
                        msg.srcnode.handlemessage('impulse', 
                            msg.srcnode.position[0], 
                            msg.srcnode.position[1], 
                            msg.srcnode.position[2],
                            0, 25, 0,
                            xforce, 0.05, 0, 0,
                            v2[0]*15*2, 0, v2[2]*15*2
                        )
                        bs.timer(0.01, lambda: msg.srcnode.handlemessage('impulse', 
                                msg.srcnode.position[0], 
                                msg.srcnode.position[1], 
                                msg.srcnode.position[2],
                                0, 25, 0,
                                xforce, 0.05, 0, 0,
                                v2[0]*15*2, 0, v2[2]*15*2
                            )
                        )
                        # Flash light to confirm we parried.
                        light = bs.newnode(
                            'light',
                            attrs={
                                'position': self.node.position,
                                'radius': 0.12 + hurtiness * 0.31,
                                'intensity': 1.4 * (1.0 + 1.0 * hurtiness),
                                'height_attenuated': False,
                                'color': flash_color,
                            },
                        )
                        bs.timer(0.06, light.delete)
                        flash = bs.newnode(
                            'flash',
                            attrs={
                                'position': self.node.position,
                                'size': 0.37 + 0.37 * hurtiness,
                                'color': flash_color,
                            },
                        )
                        bs.timer(0.06, flash.delete)
                        return
                    # Values for the force.
                    xforce = 30
                    yforce = 4
                    v = (-self.node.velocity[0], -self.node.velocity[1], -self.node.velocity[2])
                    v2 = self.node.velocity   
                    # Hurt the other spaz.
                    otherspaz.handlemessage(
                        bs.HitMessage(
                            pos=msg.pos,
                            velocity=msg.velocity,
                            magnitude=msg.magnitude * 3.0,
                            velocity_magnitude=msg.velocity_magnitude * 3.5,
                            radius=0,
                            srcnode=self.node,
                            source_player=self.source_player,
                            force_direction=msg.force_direction,
                        )
                    )
                    msg.srcnode.handlemessage(
                        'impulse', 
                        self.node.position[0], 
                        self.node.position[1], 
                        self.node.position[2],
                        0, 25, 0, yforce, 0.05, 
                        0, 0, 0, 20*400, 0
                    )
                    msg.srcnode.handlemessage(
                        'impulse', 
                        self.node.position[0], 
                        self.node.position[1], 
                        self.node.position[2],
                        0, 25, 0, xforce, 0.05, 
                        0, 0, v2[0]*15*2, 0, 
                        v2[2]*15*2
                    )        
                # No source node? Check for bomb owner.
                # This lets us affects people who threw a bomb to us.
                elif msg.bombowner:
                    yforce = 45
                    # ---------- DONT ALLOW PLAYER TEAM BOMB PARRYING!! -----------
                    if (
                        msg.bombowner.source_player != None and
                        self.source_player != None and
                        msg.bombowner.source_player.team is 
                        self.source_player.team
                    ):
                        hurtiness = 3.8
                        flash_color = (1.0, 0.8, 0.4)
                        light = bs.newnode(
                            'light',
                            attrs={
                                'position': self.node.position,
                                'radius': 0.12 + hurtiness * 0.12,
                                'intensity': 0.3 * (1.0 + 1.0 * hurtiness),
                                'height_attenuated': False,
                                'color': flash_color,
                            },
                        )
                        flash = bs.newnode(
                            'flash',
                            attrs={
                                'position': self.node.position,
                                'size': 0.17 + 0.17 * hurtiness,
                                'color': flash_color,
                            },
                        )
                        bs.timer(0.06, light.delete)
                        bs.timer(0.06, flash.delete)
                        bs.getsound('parried').play(position=self.node.position)
                        bs.getsound('player_unready').play(position=self.node.position)
                        return
                    # ---------- DONT ALLOW PLAYER TEAM BOMB PARRYING!! ----------- 
                    msg.bombowner.handlemessage('impulse', 
                            self.node.position[0], 
                            self.node.position[1], 
                            self.node.position[2],
                            0, 25, 0, yforce, 0.05, 
                            0, 0, 0, 20*400, 0
                    )
                    # hitmessage
                    msg.bombowner.handlemessage(
                        bs.HitMessage(
                            pos=msg.pos,
                            velocity=msg.velocity,
                            magnitude=msg.magnitude - 1800 + random.randint(100, 250),
                            velocity_magnitude=msg.velocity_magnitude / 2.0,
                            radius=0,
                            srcnode=self.node,
                            source_player=self.source_player,
                            force_direction=self.node.velocity,                           
                        )
                    )
                self.mpa()
                return True
            # If we were recently hit, don't count this as another.
            # (so punch flurries and bomb pileups essentially count as 1 hit).
            local_time = int(bs.time() * 1000.0)
            assert isinstance(local_time, int)
            if (
                self._last_hit_time is None
                or local_time - self._last_hit_time > 1000
            ):
                self._num_times_hit += 1
                self._last_hit_time = local_time

            mag = msg.magnitude * self.impact_scale
            velocity_mag = msg.velocity_magnitude * self.impact_scale
            damage_scale = 0.22
            # Reset our times parried, due to getting hurt.
            self.timesparried = 0
            source_player = msg.get_source_player(bs.Player)
            if source_player:
                self.last_player_attacked_by = source_player
            # Change last hit type to the message's hit type.
            self.lasthittype = msg.hit_type
            # If they've got a shield, deliver it to that instead.
            if self.shield:
                if msg.flat_damage:
                    damage = msg.flat_damage * self.impact_scale
                else:
                    # Hit our spaz with an impulse but tell it to only return
                    # theoretical damage; not apply the impulse.
                    assert msg.force_direction is not None
                    self.node.handlemessage(
                        'impulse',
                        msg.pos[0],
                        msg.pos[1],
                        msg.pos[2],
                        msg.velocity[0],
                        msg.velocity[1],
                        msg.velocity[2],
                        mag,
                        velocity_mag,
                        msg.radius,
                        1,
                        msg.force_direction[0],
                        msg.force_direction[1],
                        msg.force_direction[2],
                    )
                    damage = damage_scale * self.node.damage
                assert self.shield_hitpoints is not None
                # For the shield it's FINE if we take damage.
                # That's how we should work...
                self.shield_hitpoints -= int(damage)
                self.shield.hurt = (
                    1.0
                    - float(self.shield_hitpoints) / self.shield_hitpoints_max
                )

                # Its a cleaner event if a hit just kills the shield
                # without damaging the player.
                # However, massive damage events should still be able to
                # damage the player. This hopefully gives us a happy medium.
                max_spillover = SpazFactory.get().max_shield_spillover_damage
                if self.shield_hitpoints <= 0:
                    # FIXME: Transition out perhaps?
                    self.shield.delete()
                    self.shield = None
                    SpazFactory.get().shield_down_sound.play(
                        1.0,
                        position=self.node.position,
                    )

                    # Emit some cool looking sparks when the shield dies.
                    npos = self.node.position
                    bs.emitfx(
                        position=(npos[0], npos[1] + 0.9, npos[2]),
                        velocity=self.node.velocity,
                        count=random.randrange(20, 30),
                        scale=1.0,
                        spread=0.6,
                        chunk_type='spark',
                    )

                else:
                    SpazFactory.get().shield_hit_sound.play(
                        0.5,
                        position=self.node.position,
                    )

                # Emit some cool looking sparks on shield hit.
                assert msg.force_direction is not None
                bs.emitfx(
                    position=msg.pos,
                    velocity=(
                        msg.force_direction[0] * 1.0,
                        msg.force_direction[1] * 1.0,
                        msg.force_direction[2] * 1.0,
                    ),
                    count=min(30, 5 + int(damage * 0.005)),
                    scale=0.5,
                    spread=0.3,
                    chunk_type='spark',
                )

                # If they passed our spillover threshold,
                # pass damage along to spaz.
                if self.shield_hitpoints <= -max_spillover:
                    leftover_damage = -max_spillover - self.shield_hitpoints
                    shield_leftover_ratio = leftover_damage / damage

                    # Scale down the magnitudes applied to spaz accordingly.
                    mag *= shield_leftover_ratio
                    velocity_mag *= shield_leftover_ratio
                else:
                    return True  # Good job shield!
            else:
                shield_leftover_ratio = 1.0

            if msg.flat_damage:
                damage = int(
                    msg.flat_damage * self.impact_scale * shield_leftover_ratio
                )
            else:
                # Hit it with an impulse and get the resulting damage.
                assert msg.force_direction is not None
                self.node.handlemessage(
                    'impulse',
                    msg.pos[0],
                    msg.pos[1],
                    msg.pos[2],
                    msg.velocity[0],
                    msg.velocity[1],
                    msg.velocity[2],
                    mag,
                    velocity_mag,
                    msg.radius,
                    0,
                    msg.force_direction[0],
                    msg.force_direction[1],
                    msg.force_direction[2],
                )
                damage = int(damage_scale * self.node.damage)
                # Apply another impulse but with extra force based on
                # Impulse scale.
                # (hopefully shouldn't apply extra damage)
                if self.impulse_scale > 0:
                    self.node.handlemessage(
                        'impulse',
                        msg.pos[0],
                        msg.pos[1],
                        msg.pos[2],
                        msg.velocity[0],
                        msg.velocity[1],
                        msg.velocity[2],
                        mag * self.impulse_scale,
                        velocity_mag * self.impulse_scale,
                        msg.radius,
                        0,
                        msg.force_direction[0],
                        msg.force_direction[1],
                        msg.force_direction[2],
                    )
            self.node.handlemessage('hurt_sound')

            # Play punch impact sound based on damage if it was a punch.
            if msg.hit_type == 'punch':
                self.on_punched(damage)   

                chance = 0.2  # 20% chance for all, set to 90% if you wanna test
                
                # If damage was significant, lets show it.
                if damage >= 150:
                    assert msg.force_direction is not None
                    bs.show_damage_count(
                        '-' + str(int(damage / 10)) + '%',
                        msg.pos,
                        msg.force_direction,
                    )

                # Let's always add in a super-punch sound with boxing
                # gloves just to differentiate them.
                if msg.hit_subtype == 'super_punch':
                    SpazFactory.get().punch_sound_stronger.play(
                        1.0,
                        position=self.node.position,
                    )
                volume = 1
                if damage >= 1200:
                    sound = SpazFactory.get().punch_sound_strongest
                elif damage >= 450:
                    sounds = SpazFactory.get().punch_sound_strong
                    sound = sounds[random.randrange(len(sounds))]
                elif damage >= 270:
                    sounds = SpazFactory.get().punch_sound_medium
                    sound = sounds[random.randrange(len(sounds))]
                    volume = 3
                elif damage >= 200:
                    sound = SpazFactory.get().punch_sound
                else:
                    sounds = SpazFactory.get().punch_sound_weak
                    sound = sounds[random.randrange(len(sounds))]
                    volume = 3
                sound.play(volume, position=self.node.position)

                # Throw up some chunks.
                assert msg.force_direction is not None
                bs.emitfx(
                    position=msg.pos,
                    velocity=(
                        msg.force_direction[0] * 0.5,
                        msg.force_direction[1] * 0.5,
                        msg.force_direction[2] * 0.5,
                    ),
                    count=min(10, 1 + int(damage * 0.0025)),
                    scale=0.3,
                    spread=0.03,
                )

                bs.emitfx(
                    position=msg.pos,
                    chunk_type='sweat',
                    velocity=(
                        msg.force_direction[0] * 1.3,
                        msg.force_direction[1] * 1.3 + 5.0,
                        msg.force_direction[2] * 1.3,
                    ),
                    count=min(30, 1 + int(damage * 0.04)),
                    scale=0.9,
                    spread=0.28,
                )

                # Momentary flash.
                hurtiness = damage * 0.003
                punchpos = (
                    msg.pos[0] + msg.force_direction[0] * 0.02,
                    msg.pos[1] + msg.force_direction[1] * 0.02,
                    msg.pos[2] + msg.force_direction[2] * 0.02,
                )
                flash_color = (1.0, 0.8, 0.4)
                light = bs.newnode(
                    'light',
                    attrs={
                        'position': punchpos,
                        'radius': 0.12 + hurtiness * 0.12,
                        'intensity': 0.3 * (1.0 + 1.0 * hurtiness),
                        'height_attenuated': False,
                        'color': flash_color,
                    },
                )
                bs.timer(0.06, light.delete)

                flash = bs.newnode(
                    'flash',
                    attrs={
                        'position': punchpos,
                        'size': 0.17 + 0.17 * hurtiness,
                        'color': flash_color,
                    },
                )
                bs.timer(0.06, flash.delete)

            if msg.hit_type == 'impact':
                assert msg.force_direction is not None
                bs.emitfx(
                    position=msg.pos,
                    velocity=(
                        msg.force_direction[0] * 2.0,
                        msg.force_direction[1] * 2.0,
                        msg.force_direction[2] * 2.0,
                    ),
                    count=min(10, 1 + int(damage * 0.01)),
                    scale=0.4,
                    spread=0.1,
                )
            if self.hitpoints > 0:
                self.node.handlemessage('flash')
                # any damage makes us drop stuff..
                if damage > 1.0 and self.node.hold_node:
                    self.node.hold_node = None
                self.node.hurt = (
                    1.0 - float(self.hitpoints) / self.hitpoints_max
                )

                # If we're cursed, any damage above 25 explodes us.
                if self._cursed and damage > 25:
                    bs.timer(
                        0.05,
                        bs.WeakCall(
                            self.curse_explode, msg.get_source_player(bs.Player)
                        ),
                    )
                
                
                # If we're frozen, shatter.. otherwise die if we hit zero
                if self.frozen and (damage > 1 or self.hitpoints <= 0):
                    self.shatter()
                    
            # -- PERCENTAGE BEHAVIOR HERE --
            # get some "clamped" values
            # and round em up so its not ass
            self.percentage += round(damage / self.percentage_clamper)
            self.impulse_scale = round(self.percentage / self.impulse_clamper)
            self.update_percent_text()
            if not self.source_player:
                return
            if self.source_player.icons:
                for icon in self.source_player.icons:
                    icon.update_for_percentage()
                    icon.shake_for_damage(damage / self.percentage_clamper)
                    
        elif isinstance(msg, bs.DieMessage):
            # Oh well we died so make explode
            # and DONT autodie so our game doesnt die
            if not self._dead:
                self.percentage = 0
                self.smashkill(sound='smashDied', autodie=False)
                self.percentage = 0
                self.impulse_scale = round(self.percentage / self.impulse_clamper)
                if self.source_player.icons:
                    for icon in self.source_player.icons:
                        icon.shake_for_damage()
                def update():
                    self.percentage = 0
                    if self.source_player.icons:
                        for icon in self.source_player.icons:
                            icon.update_for_percentage()
                bs.timer(0, update)
                self.update_percent_text()
            super().handlemessage(msg)
        elif isinstance(msg, bs.PowerupMessage):
            if msg.poweruptype == 'health':
                super().handlemessage(msg)
                self.percentage /= 2
                self.percentage = round(self.percentage)
                self.impulse_scale = round(self.percentage / self.impulse_clamper)
                self.update_percent_text()
            else:
                return super().handlemessage(msg)
        else:
            return super().handlemessage(msg)
        return None