# Released under the MIT License. See LICENSE for details.
"""
Spaz actor class and related functionality.
"""
# pylint: disable=too-many-lines

from __future__ import annotations

import random
import logging
from typing import TYPE_CHECKING, override
from bascenev1lib.actor.text import Text

import bascenev1 as bs
import baclassic as bsc
import bascenev1lib.actor.bomb as bomb
import math
import os
from bascenev1lib.actor.popuptext import PopupText, PopupWriterText
from bascenev1lib.actor import spazappearance
import bascenev1lib.actor.spazappearance as spazappearance
from bascenev1._gameactivity import GameActivity

from bascenev1lib.actor.bomb import Bomb, Blast
from bascenev1lib.actor.powerupbox import PowerupBoxFactory, PowerupBox
from bascenev1lib.actor.spazfactory import SpazFactory
from bascenev1lib.actor.particles import BloodParticle, ConfettiParticle, SparkParticle
from bascenev1lib.gameutils import SharedObjects
import fromgoverhaul.mell_resources as mell
import babase as ba


if TYPE_CHECKING:
    from typing import Any, Sequence, Callable

POWERUP_WEAR_OFF_TIME = 27000
POWERUP_WEAR_OFF_TIME2 = 45000
POWERUP_WEAR_OFF_TIME3 = 10000

# Obsolete - just used for demo guy now.
BASE_PUNCH_POWER_SCALE = 1.2
BASE_PUNCH_COOLDOWN = 400

PHRASES = {
    "Spazling": ("spazPhrase", 4),
    "GummyBoiYT": ("ssPhrase", 3),
    "The Noise": ("noisePhrase", 3),
    "Rayman": ("rayPhrase", 3),
    "Orangecap": ("ocapPhrase", 3),
    "Susie": ("susPhrase", 3),
    "Mell": ("melPhrase", 8),
    "Bowser": ("bsrPhrase", 3),
    "Ralsei": ("ralPhrase", 3),
    "Kris": ("krPhrase", 1),
    "Roaring knight": ("rrPhrase", 1),
    "Noob": ("noobPhrase", 3),
    "OG Spaz": ("ogspPhrase", 5),
    "Homer": ("homerPhrase", 8),
}
DEFAULT_PHRASES = ("defaultPhrase", 6)


class PickupMessage:
    """We wanna pick something up."""


class PunchHitMessage:
    """Message saying an object was hit."""


class CurseExplodeMessage:
    """We are cursed and should blow up now."""


class BombDiedMessage:
    """A bomb has died and thus can be recycled."""

class FootingMessage:
    """
    Message class representing the footing state of an actor.
    Attributes:
        footing: The current footing state of the actor.
    """
    def __init__(self, footing):
        self.footing = footing
        
class EmeraldMessage:
    """
    Message for emerald-related events or state changes.
    Attributes:
        current: The current emerald value or state.
        srcnode: The emerald node that gave this Message.
    """
    def __init__(self, current, srcnode):
        self.current = current
        self.srcnode = srcnode


class Spaz(bs.Actor):
    """
    Base class for various Spazzes.

    A Spaz is the standard little humanoid character in the game.
    It can be controlled by a player or by AI, and can have
    various different appearances.  The name 'Spaz' is not to be
    confused with the 'Spaz' character in the game, which is just
    one of the skins available for instances of this class.
    """

    # pylint: disable=too-many-public-methods
    # pylint: disable=too-many-locals

    node: bs.Node
    """The 'spaz' bs.Node."""

    points_mult = 1
    curse_time: float | None = 5.0
    default_bomb_count = 1
    default_bomb_type = 'normal'
    default_boxing_gloves = False
    default_boxing_gloves_stronger = False
    default_shields = False
    default_shields_stronger = False
    default_hitpoints = 1000 
    
    def __init__(
        self,
        *,
        color: Sequence[float] = (1.0, 1.0, 1.0),
        highlight: Sequence[float] = (0.5, 0.5, 0.5),
        name: str = '',
        character: str = 'Spaz',
        source_player: bs.Player | None = None,
        start_invincible: bool = True,
        can_accept_powerups: bool = True,
        powerups_expire: bool = False,
        demo_mode: bool = False,
    ):
        """Create a spaz with the requested color, character, etc."""
        # pylint: disable=too-many-statements

        super().__init__()
        shared = SharedObjects.get()
        activity = self.activity

        factory = SpazFactory.get()

        # We need to behave slightly different in the tutorial.
        self._demo_mode = demo_mode

        # Specific settings for alerting if a spaz died.
        self.play_big_death_sound = False
        self.broadcast_death = False     
        self.impact_scale = 1.0
        self._roulette_active = False
        self._roulette_timer = None
        self._roulette_current = None
        self.spongebob_timer = None
        self._wiggle_count = 0
        self.wiggling = False
        self.light = None
        self.sparkies = None
        self.super_flash = None
        self.actor_type = 'spaz'

        self.source_player = source_player
        self._dead = False
        if self._demo_mode:  # Preserve old behavior.
            self._punch_power_scale = 1.2
        else:
            self._punch_power_scale = 1.0
        self.fly = self.getactivity().globalsnode.happy_thoughts_mode
        if isinstance(activity, bs.GameActivity):
            self._hockey = activity.map.is_hockey
        else:
            self._hockey = False
        self._punched_nodes: set[bs.Node] = set()
        self._cursed = False
        self._connected_to_player: bs.Player | None = None
        materials = [
            factory.spaz_material,
            shared.object_material,
            shared.player_material,
        ]
        roller_materials = [factory.roller_material, shared.player_material]
        extras_material = []
        self.issuper = False
        self.dashing = False
        self.prev_music = None
        self.force_stop_timer = None
        self.explotimer = None
        self.wiggledancetimer = None
        self.parryshield = None
        self.hardmode = None

        if can_accept_powerups:
            pam = PowerupBoxFactory.get().powerup_accept_material
            materials.append(pam)
            roller_materials.append(pam)
            extras_material.append(pam)

        media = factory.get_media(character)
        punchmats = (factory.punch_material, shared.attack_material)
        pickupmats = (factory.pickup_material, shared.pickup_material)
        self.node: bs.Node = bs.newnode(
            type='spaz',
            delegate=self,
            attrs={
                'color': color,
                'name': name,
                'behavior_version': 0 if demo_mode else 1,
                'demo_mode': demo_mode,
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
                'style': factory.get_style(character),
                'fly': self.fly,
                'hockey': self._hockey,
                'materials': materials,
                'roller_materials': roller_materials,
                'extras_material': extras_material,
                'punch_materials': punchmats,
                'pickup_materials': pickupmats,
                'invincible': start_invincible,
                'source_player': source_player,
            },
        )
        self.shield: bs.Node | None = None

        if start_invincible:

            def _safesetattr(node: bs.Node | None, attr: str, val: Any) -> None:
                if node:
                    setattr(node, attr, val)

            bs.timer(1.5, bs.Call(_safesetattr, self.node, 'invincible', False))
        self.hitpoints = self.default_hitpoints
        self.hitpoints_max = self.default_hitpoints
        self.shield_hitpoints: int | None = None
        self.shield_hitpoints_max = 650
        self.shield_hitpoints_stronger_max = 1400
        self.shield_decay_rate = 0
        self.shield_decay_timer: bs.Timer | None = None
        self._boxing_gloves_wear_off_timer: bs.Timer | None = None
        self._boxing_gloves_wear_off_flash_timer: bs.Timer | None = None
        self._bomb_wear_off_timer: bs.Timer | None = None
        self._bomb_wear_off_flash_timer: bs.Timer | None = None
        self._multi_bomb_wear_off_timer: bs.Timer | None = None
        self._multi_bomb_wear_off_flash_timer: bs.Timer | None = None
        self._curse_timer: bs.Timer | None = None
        self.bomb_count = self.default_bomb_count
        self._max_bomb_count = self.default_bomb_count
        self.bomb_type_default = self.default_bomb_type
        self.bomb_type = self.bomb_type_default
        self.land_mine_count = 0
        self.parrying = False
        self.canparry = False
        self.canparry2 = True
        self.standing = False
        self.instructimage = None
        self.cansay = False
        self.lasthittype = None
        # FIXME: don't use 'letimer' as a name; be more specific.
        self.letimer = None
        self.letimer2 = None
        self.timesparried = 0
        self.timesparriedtotal = 0
        self.yeehaws = 0
        self.yeehaw_text = None
        self.blast_radius = 2.0
        self.powerups_expire = powerups_expire
        if self._demo_mode:  # Preserve old behavior.
            self._punch_cooldown = BASE_PUNCH_COOLDOWN
        else:
            self._punch_cooldown = 450
        self._jump_cooldown = 0
        self._pickup_cooldown = 0
        self._bomb_cooldown = 0
        self._has_boxing_gloves = False
        if self.default_boxing_gloves:
            self.equip_boxing_gloves()
        if self.default_boxing_gloves_stronger:
            self.equip_boxing_gloves_stronger()
        self.last_punch_time_ms = -9999
        self.last_pickup_time_ms = -9999
        self.last_jump_time_ms = -9999
        self.last_run_time_ms = -9999
        self._last_run_value = 0.0
        self.last_bomb_time_ms = -9999
        self._turbo_filter_times: dict[str, int] = {}
        self._turbo_filter_time_bucket = 0
        self._turbo_filter_counts: dict[str, int] = {}
        self.earthhptext = None
        self.earthsptext = None
        self.earthmeter = None
        self.earthchar = None
        self.earthmetertext = None
        self.super_sparkies = None
        self.alreadydidanimation = False
        self.frozen = False
        self.shattered = False
        self.hexploded = False
        self._has_metalcap = False
        self._last_hit_time: int | None = None
        self._num_times_hit = 0
        self._bomb_held = False
        self.shield_hitpoints = 0
        if self.default_shields:
            self.equip_shields()
        if self.default_shields_stronger:
            self.equip_shields_stronger()
        self._has_hot_potato = False
        self._dropped_bomb_callbacks: list[Callable[[Spaz, bs.Actor], Any]] = []
        self._score_text: bs.Node | None = None
        self._score_text_hide_timer: bs.Timer | None = None
        self._last_stand_pos: Sequence[float] | None = None

        # Deprecated stuff.. should make these into lists.
        self.punch_callback: Callable[[Spaz], Any] | None = None
        self.pick_up_powerup_callback: Callable[[Spaz], Any] | None = None
        self.emeralds = []
        self.emeralds_indicator = None
        self.update_emerald_indicator()
        self.flashing = False
        self._flash_timer = None
        self.impulse_scale = 1.5
        self.saved_color = self.node.color
        self.saved_highlight = self.node.highlight

    @override
    def exists(self) -> bool:
        return bool(self.node)

    @override
    def on_expire(self) -> None:
        super().on_expire()

        # Release callbacks/refs so we don't wind up with dependency loops.
        self._dropped_bomb_callbacks = []
        self.punch_callback = None
        self.pick_up_powerup_callback = None
        self.sparkies = None
        self.super_flash = None

        # Clean up timers to prevent leaks
        timers_to_clear = [
            self.shield_decay_timer,
            self._boxing_gloves_wear_off_timer,
            self._boxing_gloves_wear_off_flash_timer,
            self._bomb_wear_off_timer,
            self._bomb_wear_off_flash_timer,
            self._multi_bomb_wear_off_timer,
            self._multi_bomb_wear_off_flash_timer,
            self._curse_timer,
            self._score_text_hide_timer,
            self._roulette_timer,
            self.force_stop_timer,
            self.letimer,
            self.letimer2,
            self.explotimer,
            self.wiggledancetimer,
            self._flash_timer,
            self.spongebob_timer,
            getattr(self, 'dashcooldown', None),
            getattr(self, 'pasheal_timer', None),
        ]
        for timer in timers_to_clear:
            if timer is not None:
                timer = None

        # Clean up nodes
        nodes_to_delete = [
            self.shield,
            self._score_text,
            self.emeralds_indicator,
            self.earthchar,
            self.earthmeter,
            self.earthmetertext,
            self.earthsptext,
            self.earthhptext,
            self.light,
            self.yeehaw_text,
            self.parryshield,
            self.instructimage,
        ]
        for node in nodes_to_delete:
            if node is not None and node.exists():
                node.delete()

    def add_dropped_bomb_callback(
        self, call: Callable[[Spaz, bs.Actor], Any]
    ) -> None:
        """
        Add a call to be run whenever this Spaz drops a bomb.
        The spaz and the newly-dropped bomb are passed as arguments.
        """
        assert not self.expired
        self._dropped_bomb_callbacks.append(call)

    @override
    def is_alive(self) -> bool:
        """
        Method override; returns whether ol' spaz is still kickin'.
        """
        return not self._dead

    def _hide_score_text(self) -> None:
        if self._score_text:
            assert isinstance(self._score_text.scale, float)
            bs.animate(
                self._score_text,
                'scale',
                {0.0: self._score_text.scale, 0.2: 0.0},
            )
        
    def _drop_bomb(
        self, 
        position: Sequence[float], 
        velocity: Sequence[float],
        bomb_type: str = 'normal'
    ) -> None:
        ourbomb = Bomb(
            position=position, 
            velocity=velocity, 
            bomb_type=bomb_type, 
            source_player=self.source_player
        ).autoretain()
        node = ourbomb.node
        
    def getspeed(self, 
            should_abs: bool = True, 
            decimals: int = 2, 
            ignore_y: bool = True
        ):
        """
        Calculate the speed of the actor based on velocity components.

        Args:
            should_abs (bool, optional): If True, returns the absolute value of the 
                maximum velocity component. Defaults to True.
            decimals (int, optional): Number of decimal places to round the result to. 
                Defaults to 2.
            ignore_y (bool, optional): If True, ignores the Y-axis velocity component 
                and only considers X and Z. If False, considers all three components 
                (X, Y, Z). Defaults to True.

        Returns:
            float: The speed rounded to the specified number of decimal places.
        """
        vx, vy, vz = self.node.velocity
        components = (vx, vz) if ignore_y else (vx, vy, vz)
        # absolute-ize the result if we should
        if should_abs:
            value = abs(max(components, key=abs))
        else:
            value = max(components)
        # yep, theres your speed!
        return round(value, decimals)

    def _turbo_filter_add_press(self, source: str) -> None:
        """
        Can pass all button presses through here; if we see an obscene number
        of them in a short time let's shame/pushish this guy for using turbo.
        """
        t_ms = int(bs.basetime() * 1000.0)
        assert isinstance(t_ms, int)
        t_bucket = int(t_ms / 1000)
        if t_bucket == self._turbo_filter_time_bucket:
            # Add only once per timestep (filter out buttons triggering
            # multiple actions).
            if t_ms != self._turbo_filter_times.get(source, 0):
                self._turbo_filter_counts[source] = (
                    self._turbo_filter_counts.get(source, 0) + 1
                )
                self._turbo_filter_times[source] = t_ms
                # (uncomment to debug; prints what this count is at)
                # bs.broadcastmessage( str(source) + " "
                #                   + str(self._turbo_filter_counts[source]))
                if self._turbo_filter_counts[source] == 15 and not self._dead:
                    # WHY just knock em out? at this rate, 
                    # we'll explode them and have them die
                    assert self.node
                    Blast(
                        position=self.node.position,
                        velocity=self.node.velocity,
                        blast_radius=0.6,
                        blast_type='tnt',
                        source_player= None
                    )
                    bs.getsound('boo').play(position=self.node.position)
                    ba.app.classic.ach.award_local_achievement(
                        'Turbo'
                    )
                    self.shatter()

                    # show whoever's turboing
                    now = bs.apptime()
                    assert bs.app.classic is not None
                    if now > bs.app.classic.last_spaz_turbo_warn_time + 1.5:
                        bs.app.classic.last_spaz_turbo_warn_time = now
                        bs.broadcastmessage(
                            bs.Lstr(
                                translate=(
                                    'statements',
                                    (
                                        'Warning to ${NAME}: '
                                        'you\'re fucking stupid.' # IMAGINE turboing. IMAGINE.
                                        ''
                                    ),
                                ),
                                subs=[('${NAME}', self.node.name)],
                            ),
                            color=(1, 0.5, 0),
                        )
        else:
            self._turbo_filter_times = {}
            self._turbo_filter_time_bucket = t_bucket
            self._turbo_filter_counts = {source: 1}

    def set_score_text(
        self,
        text: str | bs.Lstr,
        color: Sequence[float] = (1.0, 1.0, 0.4),
        flash: bool = False,
    ) -> None:
        """
        Utility func to show a message momentarily over our spaz that follows
        him around; Handy for score updates and things.
        """
        color_fin = bs.safecolor(color)[:3]
        if not self.node:
            return
        if not self._score_text:
            start_scale = 0.0
            mnode = bs.newnode(
                'math',
                owner=self.node,
                attrs={'input1': (0, 1.4, 0), 'operation': 'add'},
            )
            self.node.connectattr('torso_position', mnode, 'input2')
            self._score_text = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'text': text,
                    'in_world': True,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'color': color_fin,
                    'scale': 0.02,
                    'h_align': 'center',
                },
            )
            mnode.connectattr('output', self._score_text, 'position')
        else:
            self._score_text.color = color_fin
            assert isinstance(self._score_text.scale, float)
            start_scale = self._score_text.scale
            self._score_text.text = text
        if flash:
            combine = bs.newnode(
                'combine', owner=self._score_text, attrs={'size': 3}
            )
            scl = 1.8
            offs = 0.5
            tval = 0.300
            for i in range(3):
                cl1 = offs + scl * color_fin[i]
                cl2 = color_fin[i]
                bs.animate(
                    combine,
                    'input' + str(i),
                    {0.5 * tval: cl2, 0.75 * tval: cl1, 1.0 * tval: cl2},
                )
            combine.connectattr('output', self._score_text, 'color')

        bs.animate(self._score_text, 'scale', {0.0: start_scale, 0.2: 0.02})
        self._score_text_hide_timer = bs.Timer(
            1.0, bs.WeakCall(self._hide_score_text)
        )
        
    def set_cansay(self):
        self.cansay = True
        def setfalse():
            self.cansay = False
        bs.timer(1.3, setfalse) # should maybe use setattr

    def on_jump_press(self) -> None:
        """
        Called to 'press jump' on this spaz;
        used by player or AI connections.
        """
        if not self.node:
            return
        if self.cansay == True:
            self.say(wave=True, shouldcelb=True)
        t_ms = int(bs.time() * 1000.0)
        assert isinstance(t_ms, int)
        if t_ms - self.last_jump_time_ms >= self._jump_cooldown:
            self.node.jump_pressed = True
            self.last_jump_time_ms = t_ms
        self._turbo_filter_add_press('jump')

    def on_jump_release(self) -> None:
        """
        Called to 'release jump' on this spaz;
        used by player or AI connections.
        """
        if not self.node:
            return
        self.node.jump_pressed = False
    
    def attempt_parry(self):
        """
        Called upon when attempting a parry;
        Will set a value for some seconds that determines
        whether the player is in the parry timeframe.
        """
        # If we're not allowed to parry here, most likely on cooldown.
        # Return and don't do anything.
        if self.canparry2 == False:
            return
        if not self.node or not self.is_alive():
            return
        # Set important values.
        self.canparry2 = False
        self.parrying = True
        def stopparry():
            self.parrying = False
        def letparryagain():
            self.canparry2 = True
        # FIXME: make this a value in init 
        # so we don't keep reading config?
        if ba.app.config.get("squda_parrytype") == 3:
            parrytime = 0.3
            parrycooldown = 0.7
        if ba.app.config.get("squda_parrytype") == 2:
            parrytime = 0.2
            parrycooldown = 0.6
        if ba.app.config.get("squda_parrytype") == 1:
            parrytime = 0.15
            parrycooldown = 0.4
        # Close our parry timeframe after our chosen second(s).
        bs.timer(parrytime, stopparry)
        # After some seconds, let us parry again. This is our cooldown.
        bs.timer(parrycooldown, letparryagain)
        # 'Celebrate' to show we're parrying, n play a sound.
        milscs = parrytime * 1000
        self.node.handlemessage('celebrate', int(milscs))
        # FIXME: should just make the node initially,
        # then animate it
        self.parryshield = bs.newnode(
            'shield',
            owner=self.node,
            attrs={'color': (0, 0.5, 1), 'radius': 1.0},
        )
        self.node.connectattr('position_center', self.parryshield, 'position')
        bs.animate(self.parryshield, 'radius', {parrytime: 1.0, parrytime + 0.2: 0.0})
        bs.timer(parrytime + 0.3, self.parryshield.delete)
        bs.getsound('attempt_parry').play(position=self.node.position)
    
    def impulse(self, x: float | int = 0, y: float | int = 0):
        if not self.node:
            return
        v = self.node.velocity
        x = x
        y = y
        if x == 0 and y == 0:
            raise ValueError("You must specify at least X or Y for impulse.")
            return False
        # only use x and y impulse if specified
        if x != 0:
            self.node.handlemessage('impulse', 
                self.node.position[0], 
                self.node.position[1], 
                self.node.position[2],
                0, 25, 0, x, 0.05, 0, 0,
                v[0]*15*2, 0, v[2]*15*2
            )
        if y != 0:
            self.node.handlemessage('impulse', 
                self.node.position[0], 
                self.node.position[1], 
                self.node.position[2],
                0, 25, 0,
                y, 0.05, 0, 0,
                0, 20*400, 0
            )

    def on_pickup_press(self) -> None:
        """
        Called to 'press pick-up' on this spaz;
        used by player or AI connections.
        """
        if self._roulette_active:
            # If rouletting, give our item to the player.
            self.giveitem()
            return

        # wow, lotsa conditions
        if (
            len(self.emeralds) >= 7 and
            self.hitpoints >= 70 and
            self.standing == False and
            self.issuper == False
        ):
            self.gosuper()
            self.emeralds = []
            self.update_emerald_indicator()
            return
        
        if self.canparry == True:
            # If we can parry, replace 
            # our pickup button with parrying.
            self.attempt_parry()
            return
        
        if not self.node:
            return
        t_ms = int(bs.time() * 1000.0)
        assert isinstance(t_ms, int)
        if t_ms - self.last_pickup_time_ms >= self._pickup_cooldown:
            self.node.pickup_pressed = True
            self.last_pickup_time_ms = t_ms
        self._turbo_filter_add_press('pickup')

    def on_pickup_release(self) -> None:
        """
        Called to 'release pick-up' on this spaz;
        used by player or AI connections.
        """
        if not self.node:
            return
        self.node.pickup_pressed = False

    def on_hold_position_press(self) -> None:
        """
        Called to 'press hold-position' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        self.node.hold_position_pressed = True
        self._turbo_filter_add_press('holdposition')

    def on_hold_position_release(self) -> None:
        """
        Called to 'release hold-position' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        self.node.hold_position_pressed = False

    def on_punch_press(self) -> None:
        """
        Called to 'press punch' on this spaz;
        used for player or AI connections.
        """
        if not self.node or self.frozen or self.node.knockout > 0.0:
            return
        t_ms = int(bs.time() * 1000.0)
        assert isinstance(t_ms, int)
        if t_ms - self.last_punch_time_ms >= self._punch_cooldown:
            if self.punch_callback is not None:
                self.punch_callback(self)
            self._punched_nodes = set()  # Reset this.
            self.last_punch_time_ms = t_ms
            self.node.punch_pressed = True
            if not self.node.hold_node:
                bs.timer(
                    0.1,
                    bs.WeakCall(
                        self._safe_play_sound,
                        SpazFactory.get().swish_sound,
                        0.8,
                    ),
                )
        self._turbo_filter_add_press('punch')
        
    def firework_explode(self, 
        on_die_call: Callable = None,
        snd1: str = 'wackyplatform', 
        snd2: str = 'retired',
    ) -> None:
        """
        Trigger a firework explosion effect on the actor.
        This method launches the actor upward and detonates it when it reaches
        a certain height, creating a firework explosion. If the actor gets stuck
        (doesn't reach the required height), it will explode after a timeout.
        Args:
            on_die_call (Callable, optional): A callback function to execute when
                the explosion occurs. Defaults to None.
            snd1 (str, optional): The sound effect to play at the start of the
                firework sequence. Defaults to 'wackyplatform'.
            snd2 (str, optional): The sound effect to play when the explosion
                detonates. Defaults to 'retired'.
        Returns:
            None
        """
        if not self.node:
            return
        bs.getsound(snd1).play(position=self.node.position)
        yforce = 240
        savedY = self.node.position[1]
        def actualexplode():
            if not self.node:
                self.explotimer = None
                return
            self.explotimer = None
            bomb.Bomb(position=self.node.position, bomb_type='tntfirework').explode()
            self.shatter(True)
            bs.getsound(snd2).play(position=self.node.position)
            if on_die_call:
                # FIXME: maybe just use exec or eval since
                # then we can do non-callables
                bs.Call(on_die_call)()

        # Check if we're a little above where we once were,
        # and if we are, trigger our actual 'firework' explosion.
        def do_impulse_stuff():
            if not self.node:
                self.explotimer = None 
                return
            if self.node.position[1] >= savedY + 5:
                actualexplode()
            self.impulse(y=120)

        def check_stuck():
            if not self.node:
                return
            if self.is_alive():
                actualexplode()

        self.explotimer = bs.Timer(0.01, do_impulse_stuff, repeat=True)
        self.stuck_timer = bs.Timer(2.0, check_stuck)

    def _safe_play_sound(self, sound: bs.Sound, volume: float) -> None:
        """Plays a sound at our position if we exist."""
        if self.node:
            sound.play(volume, self.node.position)

    def on_punch_release(self) -> None:
        """
        Called to 'release punch' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        self.node.punch_pressed = False
        
    def giveitem(self):
        """ 
        Give our random item that we were 
        rolling for on the random powerup.
        """
        self._roulette_active = False
        # FIXME: make lists of good and bad items
        if self._roulette_current == 'curse':
            bs.getsound('baditem').play(position=self.node.position)
        if self._roulette_current == 'spongebob':
            bs.getsound('baditem').play(position=self.node.position)
        elif self._roulette_current == 'punch':
            bs.getsound('gooditem').play(position=self.node.position)
        elif self._roulette_current == 'metal':
            bs.getsound('gooditem').play(position=self.node.position)
        else:
            bs.getsound('okitem').play(position=self.node.position)
        self.handlemessage(bs.PowerupMessage(self._roulette_current))
        self._roulette_current = None

    def on_bomb_press(self) -> None:
        """
        Called to 'press bomb' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        if (
            not self.is_alive()
            or self.node.knockout > 0.04
            or self.frozen
        ):
            return
        t_ms = int(bs.time() * 1000.0)
        assert isinstance(t_ms, int)
        if t_ms - self.last_bomb_time_ms >= self._bomb_cooldown:
            self.last_bomb_time_ms = t_ms
            self.node.bomb_pressed = True
            if not self.node.hold_node:
                self.drop_bomb()
        self._turbo_filter_add_press('bomb')

    def on_bomb_release(self) -> None:
        """
        Called to 'release bomb' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        self.node.bomb_pressed = False

    def on_run(self, value: float) -> None:
        """
        Called to 'press run' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        t_ms = int(bs.time() * 1000.0)
        assert isinstance(t_ms, int)
        self.last_run_time_ms = t_ms
        self.node.run = value

        # Filtering these events would be tough since its an analog
        # value, but lets still pass full 0-to-1 presses along to
        # the turbo filter to punish players if it looks like they're turbo-ing.
        if self._last_run_value < 0.01 and value > 0.99:
            self._turbo_filter_add_press('run')

        self._last_run_value = value

    def on_fly_press(self) -> None:
        """
        Called to 'press fly' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        # Not adding a cooldown time here for now; slightly worried
        # input events get clustered up during net-games and we'd wind up
        # killing a lot and making it hard to fly.. should look into this.
        self.node.fly_pressed = True
        self._turbo_filter_add_press('fly')

    def on_fly_release(self) -> None:
        """
        Called to 'release fly' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        self.node.fly_pressed = False

    def on_move(self, x: float, y: float) -> None:
        """
        Called to set the joystick amount for this spaz;
        used for player or AI connections.
        """
        self.node.handlemessage('move', x, y)

    def on_move_left_right(self, value: float) -> None:
        if not self.node:
            return
        self.node.move_left_right = value
        
        def resetwiggle():
            self._wiggle_count = 0
        # detect any significant fast changes to the value
        if abs(value) > 0.9:
            self._wiggle_count += 1
            self.wiggle_reset_timer = bs.Timer(0.3, resetwiggle)
        # start doin it if we wiggled around so much
        if self._wiggle_count > 14:
            self._start_wiggle_sequence()
            self.resettimer = bs.Timer(0.5, self._stop_wiggle_sequence)
     
    def on_move_up_down(self, value: float) -> None:
        if not self.node:
            return
        self.node.move_up_down = value
        
    def _start_wiggle_sequence(self):
        if self.wiggling == True:
            self.resettimer = bs.Timer(0.5, self._stop_wiggle_sequence)
            return
        self.wiggledancetimer = bs.Timer(
            0.01, lambda: self.node.handlemessage(
                'celebrate', int(50)), 
            repeat=True
        )
        bs.getsound('drumRollShort').play(position=self.node.position)
        self.wiggling = True
        if isinstance(self.getactivity(), GameActivity):
            self.getactivity().dancing_players.append(self)
        
    def _stop_wiggle_sequence(self):
        self.wiggledancetimer = None
        self.wiggling = False
        self._wiggle_count = 0
        self.remove_from_dancin()

    def on_punched(self, damage: int) -> None:
        """Called when this spaz gets punched."""
    # note; i still don't get why this 
    # isn't a function in vanilla; lot easier than using handlemessage all the time
    def die(self, how: bs.DeathType = bs.DeathType.IMPACT):
        """Kill us. Simple."""
        self.node.handlemessage(bs.DieMessage(how=how))


    def get_death_points(self, how: bs.DeathType) -> tuple[int, int]:
        """Get the points awarded for killing this spaz."""
        del how  # Unused.
        num_hits = float(max(1, self._num_times_hit))

        # Base points is simply 10 for 1-hit-kills and 5 otherwise.
        importance = 2 if num_hits < 2 else 1
        return (10 if num_hits < 2 else 5) * self.points_mult, importance

    def curse(self) -> None:
        """
        Give this poor spaz a curse;
        he will explode in 5 seconds.
        """
        if not self._cursed:
            factory = SpazFactory.get()
            self._cursed = True

            # Add the curse material.
            for attr in ['materials', 'roller_materials']:
                materials = getattr(self.node, attr)
                if factory.curse_material not in materials:
                    setattr(
                        self.node, attr, materials + (factory.curse_material,)
                    )

            # None specifies no time limit.
            assert self.node
            if self.curse_time is None:
                self.node.curse_death_time = -1
            else:
                # Note: curse-death-time takes milliseconds.
                tval = bs.time()
                assert isinstance(tval, (float, int))
                self.node.curse_death_time = int(
                    1000.0 * (tval + self.curse_time)
                )
                self._curse_timer = bs.Timer(
                    self.curse_time,
                    bs.WeakCall(self.handlemessage, CurseExplodeMessage()),
                )

    def equip_boxing_gloves(self) -> None:
        """
        Give this spaz some boxing gloves.
        """
        assert self.node
        self.node.boxing_gloves = True
        self._has_boxing_gloves = True
        if self._demo_mode:  # Preserve old behavior.
            self._punch_power_scale = 2.5
            self._punch_cooldown = 700
        else:
            factory = SpazFactory.get()
            self._punch_power_scale = 1.7
            self._punch_cooldown = 700

    def equip_weak_punches(self) -> None:
        """
        Makes spaz punch significantly faster
        but have much weaker punches.
        """
        assert self.node
        # If we have gloves, replace them
        self._has_boxing_gloves = False
        self.node.boxing_gloves = False
        if self._demo_mode:
            self._punch_power_scale = 2.5
            self._punch_cooldown = 700
        else:
            factory = SpazFactory.get()
            self._punch_power_scale = 0.6
            self._punch_cooldown = 100

    # FIXME: unify with equip_boxing_gloves above
    def equip_boxing_gloves_stronger(self) -> None:
        """
        Give this spaz some way stronger boxing gloves.
        This is mostly exclusive to SpazBot.KNIGHTBot, but
        it's still coded in so... i dunno, add it if you want
        """
        assert self.node
        self.node.boxing_gloves = True
        self._has_boxing_gloves = True
        if self._demo_mode:
            self._punch_power_scale = 2.5
            self._punch_cooldown = 700
        else:
            factory = SpazFactory.get()
            self._punch_power_scale = 2.3
            self._punch_cooldown = 1400

    def equip_shields(self, decay: bool = False) -> None:
        """
        Give this spaz a nice energy shield.
        """

        if not self.node:
            logging.exception('Can\'t equip shields; no node.')
            return
        # Prevent players from getting shields 
        # if they're on hardmode (so that it's not too easy).
        if self.hardmode:
            PopupText(
                bs.Lstr(resource='noShield'),
                position=self.node.position,
                color=(1, 0.1, 0.1, 0.9),
                scale=1.0,
            ).autoretain()
            bs.getsound('error').play(position=self.node.position)
            return

        factory = SpazFactory.get()
        if self.shield is None:
            self.shield = bs.newnode(
                'shield',
                owner=self.node,
                attrs={'color': self.node.color, 'radius': 1.3},
            )
            self.node.connectattr('position_center', self.shield, 'position')
        self.shield_hitpoints = self.shield_hitpoints_max = 1000
        self.shield_decay_rate = factory.shield_decay_rate if decay else 0
        self.shield.hurt = 0
        pos = self.node.position
        sounds = SpazFactory.get().shield_up_sound
        sound = sounds[random.randrange(len(sounds))]
        sound.play(position=pos, volume=1.5)

        if self.shield_decay_rate > 0:
            self.shield_decay_timer = bs.Timer(
                0.5, bs.WeakCall(self.shield_decay), repeat=True
            )
            # So user can see the decay.
            self.shield.always_show_health_bar = True
        
    
    def equip_shields_stronger(self, decay: bool = False) -> None:
        """
        Give this spaz a neat energy shield.
        Works akin to equip_shields but with more HP.
        """
        if not self.node:
            logging.exception('Can\'t equip shields; no node.')
            return

        factory = SpazFactory.get()
        if self.shield is None:
            self.shield = bs.newnode(
                'shield',
                owner=self.node,
                attrs={'color': (1, 0, 0), 'radius': 1.3},
            )
            self.node.connectattr('position_center', self.shield, 'position')
        self.shield_hitpoints = self.shield_hitpoints_stronger_max = 1400
        self.shield_decay_rate = factory.shield_decay_rate if decay else 0
        self.shield.hurt = 0
        pos = self.node.position
        sounds = SpazFactory.get().shield_up_sound
        sound = sounds[random.randrange(len(sounds))]
        sound.play(position=pos, volume=1.5)
        self.shield.always_show_health_bar = True

        if self.shield_decay_rate > 0:
            self.shield_decay_timer = bs.Timer(
                0.5, bs.WeakCall(self.shield_decay), repeat=True
            )
    
    def shield_decay(self) -> None:
        """Called repeatedly to decay shield HP over time."""
        if self.shield:
            assert self.shield_hitpoints is not None
            self.shield_hitpoints = max(
                0, self.shield_hitpoints - self.shield_decay_rate
            )
            assert self.shield_hitpoints is not None
            self.shield.hurt = (
                1.0 - float(self.shield_hitpoints) / self.shield_hitpoints_max
            )
            if self.shield_hitpoints <= 0:
                self.shield.delete()
                self.shield = None
                self.shield_decay_timer = None
                assert self.node
                SpazFactory.get().shield_down_sound.play(
                    1.0,
                    position=self.node.position,
                )
            self.updatemeter()
        else:
            self.shield_decay_timer = None
            self.updatemeter()

    def remove_from_metal_list(self):
        if isinstance(self.getactivity(), GameActivity):
            try:
                self.getactivity().metal_players.remove(self)
            except Exception as e: 
                bs.debprint(f"Couldn't remove {self} remove from metal list: {e}")
                pass
                
    def remove_from_dancin(self):
        if isinstance(self.getactivity(), GameActivity):
            try:
                self.getactivity().dancing_players.remove(self)
            except Exception as e: 
                bs.debprint(f"Couldn't remove {self} from wiggle dance list: {e}")
                pass
            
    def _deactivate_metalcap(self):
        self._has_metalcap = False
        self.node.color = self._saved_color
        self.node.highlight = self._saved_highlight
        self.node.color_texture = self._saved_materials
        self.impact_scale = self.impact_scale + 0.5
        self.remove_from_metal_list()

    def _activate_metalcap(self) -> None:
        if not self.node:
            return
        
        if getattr(self, "_has_metalcap", False):
            return
            
        self._has_metalcap = True
        
        # add to the music list
        musicis = self.getactivity().globalsnode.music
        if musicis == 'Grand_Romp':
            bs.setmusic(bs.MusicType.METALCAPTIME)
        else:
            if isinstance(self.getactivity(), GameActivity):
                if not ba.app.config.get("squda_disablemmusic"):
                    self.getactivity().metal_players.append(self)
        # play a sound
        self._metalcap_sound = bs.getsound('metalcap').play(position=self.node.position)

        # save the material we were using
        self._saved_materials = self.node.color_texture
        self._saved_color = self.node.color
        self._saved_highlight = self.node.highlight

        # make us metal...
        self.node.color_texture = bs.gettexture('metal')
        self.node.color = (1.0, 1.0, 1.0)  # pure white
        self.node.highlight = (1.0, 1.0, 1.0)  # also pure white
        
        # apply status effect
        self.impact_scale = self.impact_scale - 0.5
        
    def tptosafety(self):
        mp = self.activity.map.defs.points
        spawn_names = [
            'ffa_spawn1',
            'ffa_spawn2',
            'ffa_spawn3',
            'ffa_spawn4',
        ]
        points = [mp[name] for name in spawn_names if name in mp]
        if not points:
            print(f'{self.node.name} tried to tp to safety but the map')
            print('on does not have any ffa spawn points.')
            self.die()
            return
        self.node.handlemessage(
            bs.StandMessage(random.choice(points))
        )
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=15,
            scale=0.6,
            spread=1.5,
            chunk_type='spark',
        ),
        text = PopupText(
            bs.Lstr(resource='oobParried'),
            position=self.node.position,
            color=(1, 0, 1, 0.9),
            scale=1.0,
        ).autoretain()
        bs.getsound('parried').play(position=self.node.position)
        bs.getsound('orchestraHit').play(position=self.node.position)
        return      
    
    def super_spark(self, chance = 0.6, amount1 = 2, amount2 = 5):
        if not self.node:
            return
        pos = self.node.position
        if random.random() < chance:
            for _ in range(random.randint(amount1, amount2)):
                offset_x = random.uniform(-0.5, 0.5)
                offset_z = random.uniform(-0.5, 0.5)
                offset_y = random.uniform(0.2, 0.7)
                particle_pos = (pos[0] + offset_x, pos[1] + offset_y, pos[2] + offset_z)
                particle = SparkParticle(position=particle_pos)
                particle.autoretain()
                dir_x = offset_x * 2
                dir_z = offset_z * 2
                dir_y = offset_y * 2
                length = (dir_x**2 + dir_y**2 + dir_z**2)**0.5
                if length > 0:
                    dir_x /= length
                    dir_y /= length
                    dir_z /= length
                force = 20
                def impulsmf(who):
                    who.node.handlemessage(
                        'impulse',
                        particle_pos[0],
                        particle_pos[1],
                        particle_pos[2],
                        0,
                        0,
                        0,
                        force,
                        force,
                        0,
                        0,
                        dir_x,
                        dir_y,
                        dir_z,
                    )
                impulsmf(particle)
    
    def gosuper(self, shouldntsetmusic: bool = False) -> None:
        if not self.node:
            return
        self.impulse(y=350)
        bs.getsound('pretrans').play(position=self.node.position)
        bs.timer(0.4, lambda: self.super(shouldntsetmusic=shouldntsetmusic))
        bs.timer(0.4, lambda: self.super_spark(1.0, 15, 25))

    def super(self, shouldntsetmusic: bool = False) -> None:
        """ 
        Makes a Spaz flash yellow,
        severely boosts stats, plays custom music,
        and allows some specific moves
        """
        if self.node:
            activity = self.getactivity()
            gnode = activity.globalsnode
            bs.getsound('supertrans').play(position=self.node.position) # i'm keeping it as super trans. fuck you. die.
            self.issuper = True
            # flashing effect function
            if not self.node.exists():
                return
            yellow = (1.5, 1.5, 0)
            white = (1, 1, 1)
            midtime = 0.1
            endtime = 0.2
            def flash_func():
                if (
                    not self.node
                    or not self.is_alive()
                    or not self.issuper
                ):
                    return
                flashC = bs.animate_array(self.node, 'color', 3,
                    {
                        0.0: yellow,
                        midtime: white,
                        endtime: yellow
                    },
                )
                flashH = bs.animate_array(self.node, 'highlight', 3,
                    {
                        0.0: yellow,
                        midtime: white,
                        endtime: yellow
                    },
                )
            # Instead of using looped array animation,
            # use a timer which allows us to override any color changes
            self.super_flash = bs.Timer(endtime, flash_func, repeat=True) 
            self.super_sparkies = bs.Timer(endtime + 0.2, self.super_spark, repeat=True) 
            bs.camerashake(intensity=5.0)
            char_name = getattr(self, 'character', None)
            hurtiness = 4.2
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
            bs.timer(0.12, light.delete)
            flash = bs.newnode(
                'flash',
                attrs={
                    'position': self.node.position,
                    'size': 0.17 + 0.17 * hurtiness,
                    'color': flash_color,
                },
            )
            bs.timer(0.12, flash.delete)
            bs.timer(0.1, self.updatemeter)
            self.say()
            if char_name:
                appearances = bs.app.classic.spaz_appearances
                if char_name in appearances: # check if their names there
                    appearance = appearances[char_name]
                    if hasattr(appearance, 'gloat_sounds') and appearance.gloat_sounds:
                         # play the character's gloat voiceline(s)
                        sound = random.choice(appearance.gloat_sounds)
                        bs.getsound(sound).play(position=self.node.position)
                    else:
                        if hasattr(appearance, 'victory_sounds') and appearance.victory_sounds:
                            # if we don't have a gloat voiceline, we'll use their victory ones instead
                            sound = random.choice(appearance.victory_sounds)
                            bs.getsound(sound).play(position=self.node.position)
                        else:
                            # this character doesn't have a victory voiceline too. we'll play the default one.
                            bs.getsound('win').play(position=self.node.position)
                else: # didn't find this character's name in appearances
                    bs.getsound('error').play(position=self.node.position) 
                    raise ValueError(f"Character name '{char_name}' not found in appearances.")
            # buff our spaz
            self.hitpoints_max = 2500
            self.hitpoints = 2500
            self.equip_shields()
            self.equip_boxing_gloves()
            self.canparry = True
            self.instructimage = bs.newnode('image', 
                attrs={
                    'texture': bs.gettexture('parryinstructions'),
                    'absolute_scale': True,
                    'position': (0, -200),
                    'opacity': 1.0,
                    'scale': (200, 200),
                    'color': (1, 1, 1)
                }
            )
            bs.animate(self.instructimage, 'opacity',
                       {0.1: 1.0, 4.5: 1.0, 6.2: 0.0})
            bs.timer(10.0, self.instructimage.delete)
            if not shouldntsetmusic:
                # music setters (character based)
                gnode = self.activity.globalsnode
                self.prev_music = gnode.music.upper()
                if self.character == 'The Noise':
                    bs.setmusic(bs.MusicType.NOISESUPER)
                elif self.character == 'Kris':
                    bs.setmusic(bs.MusicType.GRAND_ROMP)
                elif self.character == 'Susie':
                    bs.setmusic(bs.MusicType.FEEL_THE_FURY)
                elif self.character == 'SM64 Mario':
                    bs.setmusic(bs.MusicType.RAINBOW_ROAD)
                else:
                    bs.setmusic(bs.MusicType.SUPER)
    
    def _activate_spongebob(self, time: int, speed: int, transition_in: bool = True):
        """Give this spaz the 'Hot Potato' effect."""
        if getattr(self, "_has_hot_potato", False):
            return  # Already has one, don't stack
        if not self.node:
            return # no node

        self._has_hot_potato = True
        self.activity.spongebob_time = time  # seconds remaining
        self._potato_speed = speed
        name = self.node.name if self.node.name else self.character
        xoffs = 500
        usualy = 120
        self._potato_holder_text = bs.newnode(
            'text',
            attrs={
                'text': bs.Lstr(
                    resource='spongePlayer', 
                    subs=[
                        ('${NAME}', name)
                    ]
                ),
                'h_align': 'center',
                'v_attach': 'bottom',
                'position': (xoffs, usualy + 90),
                'scale': 1.0,
                'color': (1, 1, 0),
                'shadow': 0.7,
                'flatness': 0.5,
            },
        )
        self._potato_timer_img = None
        if self.source_player:
            from bascenev1lib.actor.image import Image
            self._potato_player_img = Image(
                texture=self.source_player.get_icon(),
                position=(xoffs, usualy + 160),
                scale=(60.0, 60.0),
                attach=Image.Attach.BOTTOM_CENTER,
            ).autoretain()
        self._potato_timer_img = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('spongetimer1'),
                'position': (xoffs, usualy - 20),
                'scale': (200, 200),
                'color': (0.8, 0.8, 0.8),
                'attach': 'bottomCenter',
            },
        )
        self._potato_timer_images = []
        self._shaking = False
        self._shake_timer = None
        def create_timer_images(current_time):
            # Delete old images
            for img in self._potato_timer_images:
                if img.exists():
                    img.delete()
            self._potato_timer_images = []

            # Get digits
            digits = [int(d) for d in str(current_time)]
            num_digits = len(digits)
            spacing = 40.0
            for i, digit in enumerate(digits):
                x = (i - (num_digits - 1) / 2) * spacing
                img = bs.newnode(
                    'image',
                    attrs={
                        'texture': bs.gettexture(f'spongenumber{digit}'),
                        'position': (x + xoffs, usualy - 20),
                        'scale': (120, 120),
                        'color': (1, 1, 1),
                        'attach': 'bottomCenter',
                    },
                )
                self._potato_timer_images.append(img)

            # Handle shaking
            if current_time <= 0:
                for img in self._potato_timer_images:
                    if img.exists():
                        img.delete()
            if current_time <= 5 and not self._shaking:
                self._shaking = True
                def shake():
                    for img in self._potato_timer_images:
                        if img.exists():
                            current_pos = img.position
                            shake_num = 5
                            offset_x = random.randint(-shake_num, shake_num)
                            offset_y = random.randint(-shake_num, shake_num)
                            bs.animate_array(
                                img, 
                                'position', 
                                2,
                                {
                                    0: (current_pos[0] + offset_x, current_pos[1] + offset_y),
                                    0.01: (current_pos[0], current_pos[1]),
                                }
                            )
                self._shake_timer = bs.Timer(0.001, shake, repeat=True)
                if self._potato_timer_img:
                    self._potato_timer_img.texture = bs.gettexture('spongetimer2')
            elif current_time > 5 and self._shaking:
                self._shaking = False
                if self._shake_timer:
                    self._shake_timer = None
                if self._potato_timer_img:
                    self._potato_timer_img.texture = bs.gettexture('spongetimer1')
        # Ticks
        def tick():
            # Delete anything in case we're dead or our node doesn't exist
            if self._has_hot_potato == False or not self.node or self._dead:
                if hasattr(self, "_potato_timer_img") and self._potato_timer_img.exists():
                    self._potato_timer_img.delete()
                if hasattr(self, "_potato_player_img") and self._potato_player_img.exists():
                    self._potato_player_img.node.delete()
                if hasattr(self, "_potato_holder_text") and self._potato_holder_text.exists():
                    self._potato_holder_text.delete()
                if hasattr(self, '_potato_timer_images'):
                    for img in self._potato_timer_images:
                        if img.exists():
                            img.delete()
                self.spongebob_timer = None
                return
            # Remove one from the time
            self.activity.spongebob_time -= 1
            create_timer_images(self.activity.spongebob_time)
            # Explode if we should die
            if self.activity.spongebob_time <= 0:
                if self._has_hot_potato == False:
                    return
                self.firework_explode()
                self._potato_holder_text.delete()
                self.spongebob_timer = None
                bs.getsound('spongebobdead').play(position=self.node.position)
                self._potato_timer_images = []
                endtime = 0.5
                bs.animate(
                    self._potato_timer_img, 
                    'opacity',
                    {
                        0: 1.0,
                        endtime: 0.0,
                    }
                )
                bs.animate(
                    self._potato_player_img.node, 
                    'opacity',
                    {
                        0: 1.0,
                        endtime: 0.0,
                    }
                )
                for img in self._potato_timer_images:
                    bs.animate(
                        img,
                        'opacity',
                        {
                            0: 1.0,
                            endtime: 0.0,
                        }
                    )
                def delete():
                    for img in self._potato_timer_images:
                        if img.exists():
                            img.delete()
                    self._potato_timer_img.delete()
                    self._potato_player_img.node.delete()
                bs.timer(endtime, delete)
            else:
                bs.getsound('spongebob').play(position=self.node.position)
        tick()
        self.spongebob_timer = bs.Timer(self._potato_speed, tick, repeat=True)
            
    def smashkill(self, 
        sound: str, 
        autodie: bool = True
    ) -> None:    
        """ Explodes us in a kind of smash bros style 
        (normally called by OutOfBounds) """
        
        if self._dead == True:
            return
        if not self.node:
            return
        
        bs.getsound(sound).play(position=self.node.position)
        Blast(
            position=self.node.position,
            velocity=(0, 0, 0),
            blast_radius=5.0,
            blast_type='tnt',
            source_player=self.source_player
        ).autoretain()

        # send a death message
        if autodie == True:
            self.die(how=bs.DeathType.FALL)
        
    def sugarcoat_overlay(self, sound, image):
        """
        overlay based on the 
        i'm not gonna sugarcoat it meme
        """
        # sound
        bs.getsound(sound).play()
        
        # if the person doesn't really like getting jumpscared
        # by the stupid thing just return lmfao (we still play sounds)
        if ba.app.config.get("squda_nosugarcoats", True):
            return
        
        # make the image
        icon = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture(image),
                'position': (0, 0),
                'fill_screen': True,
                'opacity': 1.0,
                'absolute_scale': True,
                'attach': 'center'
            },
        )

        # fade image step by step
        def _fade_step():
            if icon and icon.exists():
                new_opacity = icon.opacity - 0.05
                if new_opacity <= 0.0:
                    icon.delete()
                else:
                    icon.opacity = new_opacity
                    bs.timer(0.03, _fade_step)  # repeat until gone

        # after a bit of delay THEN start fading
        bs.timer(0.1, _fade_step)
     
    # Pulse green if healing
    # ps. started using saved_color so we
    # don't accidentally override the player's color choice
    def pulse_green(self, intensity: float = 1.0, time: float = 0.65):
        if self.node:
            bs.animate_array(
                self.node,
                'color',
                3,
                {
                    0: (0, 2*intensity, 0),
                    time*0.8: self.saved_color,
                    time: self.saved_color
                }
            )
            bs.animate_array(
                self.node,
                'highlight',
                3,
                {
                    0: (0, 2*intensity, 0),
                    time*0.8: self.saved_highlight,
                    time: self.saved_highlight
                }
            )
            if self.earthhptext and self.earthhptext.exists():
                self.earthhptext.text = str(int(self.hitpoints / 10))
    
    def tellfucked(self):
        """
        Scripted text sequence. See bascenev1._coopgame.
        """
        PopupText(
            bs.Lstr(resource='gambText1'),
            position=self.node.position,
            color=(1, 0.5, 0.5, 0.9),
            scale=1.0,
        ).autoretain()
        def text2():
            PopupText(
            bs.Lstr(resource='gambText2'),
            position=self.node.position,
            color=(1, 0.4, 0.4, 0.9),
            scale=1.0,
            ).autoretain()
            bs.getsound('error').play(position=self.node.position)
            bs.setmusic(None)
        def text3():
            PopupText(
            bs.Lstr(resource='gambText3'),
            position=self.node.position,
            color=(1, 0.4, 0.4, 0.9),
            scale=1.0,
            ).autoretain()
            bs.timer(0.5, lambda: bs.setmusic(bs.MusicType.GAMBLING))
            char_name = getattr(self, 'character', None)
            if char_name:
                appearances = bs.app.classic.spaz_appearances
                if char_name in appearances:
                    appearance = appearances[char_name]
                    sound = random.choice(appearance.fall_sounds)
                    bs.getsound(sound).play(position=self.node.position)
                    self.node.handlemessage('celebrate', int(1000))
        bs.timer(2.0, text2)
        bs.timer(4.0, text3)
            
    def _activate_roulette(self):
        """ 
        Start rolling for a random powerup.
        """
        if self._roulette_active:
            return False  # already rolling
        self._roulette_active = True
        # FIXME: this list should be pulled from the powerup list 
        powerups = [
            'triple_bombs', 'shield', 'punch', 'impact_bombs', 
            'land_mines', 'sticky_bombs', 'ice_bombs', 'health', 
            'metal', 'curse', 'strong', 'spongebob', 'punch', 'sticky'
        ]
        sounds = [
            'DSITROL1', 
            'DSITROL2', 
            'DSITROL3', 
            'DSITROL4', 
            'DSITROL5', 
            'DSITROL6', 
            'DSITROL7', 
            'DSITROL8',
        ]
        PopupText(
            bs.Lstr(
                resource='grabItem', 
                subs=[
                    ('${GRAB}', ba.charstr(ba.SpecialChar.TOP_BUTTON))
                ]
            ),
            position=self.node.position,
            color=(1, 1, 1, 0.6),
            scale=1.0,
        ).autoretain()
        
        def roll():
            if not self._roulette_active or not self.node:
                return
            self._roulette_current = random.choice(powerups)
            bs.getsound(random.choice(sounds)).play(position=self.node.position)

        def force_stop():
            if self._roulette_active:
                self.giveitem()
        # if our player hasn't rolled for a while, just stop for em
        self.force_stop_timer = bs.Timer(5.0, force_stop)
        self._roulette_timer = bs.Timer(0.09, roll, repeat=True)
        roll()
        
    def increase_chain(self, number: int = 1):
        # DONT INCREASE CHAINS IF
        # THE SPAZ IS DEAD!!
        if (
            not self.node
            or not self.is_alive()
        ):
            return False
        self.yeehaws += number
        # play sounds based on our chains
        if self.yeehaws >= 7:
            bs.getsound('mbm/yeehaw4').play(position=self.node.position)
            bs.getsound('mbm/chain7').play(position=self.node.position)
        elif self.yeehaws >= 6:
            bs.getsound('mbm/yeehaw4').play(position=self.node.position)
            bs.getsound('mbm/chain6').play(position=self.node.position)
        elif self.yeehaws >= 5:
            bs.getsound('mbm/yeehaw4').play(position=self.node.position)
            bs.getsound('mbm/chain5').play(position=self.node.position)
        elif self.yeehaws >= 4:
            bs.getsound('mbm/yeehaw4').play(position=self.node.position)
            bs.getsound('mbm/chain4').play(position=self.node.position)
        elif self.yeehaws >= 3:
            bs.getsound('mbm/yeehaw3').play(position=self.node.position)
            bs.getsound('mbm/chain3').play(position=self.node.position)
        elif self.yeehaws >= 2:
            bs.getsound('mbm/yeehaw2').play(position=self.node.position)
            bs.getsound('mbm/chain2').play(position=self.node.position)
        elif self.yeehaws >= 1:
            bs.getsound('mbm/yeehaw1').play(position=self.node.position)
            bs.getsound('mbm/chain1').play(position=self.node.position)
        # add a light to us indicating we have a chain
        if not self.light:
            self.light = bs.newnode(
                'flash',
                attrs={
                    'position': self.node.position,
                    'size': 0.5,
                    'color': (1.0, 0.8, 0.4),
                },
            )
            self.node.connectattr('position', self.light, 'position')
        if not self.sparkies:
            self.sparkies = bs.Timer(0.2, lambda: bs.emitfx(
                    position=self.node.position,
                    velocity=self.node.velocity,
                    count=15,
                    scale=0.6,
                    spread=1.5,
                    chunk_type='spark',
                ),
            repeat=True
            )
        # auugghhh text
        if not self.yeehaw_text:
            yoff = 0.3
            mathnode = bs.newnode(
                'math',
                owner=self.node,
                attrs={'input1': (0, 1.4 + yoff, 0), 'operation': 'add'},
            )
            self.node.connectattr('torso_position', mathnode, 'input2')
            self.yeehaw_text = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'text': f'*{str(self.yeehaws)}*',
                    'in_world': True,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'scale': 0.01,
                    'color': (0.9, 0.9, 1),
                    'h_align': 'center',
                },
            )
            mathnode.connectattr('output', self.yeehaw_text, 'position')
        else:
            self.yeehaw_text.text = f'*{str(self.yeehaws)}*'
            
    def release_chain(self):
        # DONT RELEASE CHAINS IF
        # THE SPAZ IS DEAD!!
        if (
            not self.node
            or not self.is_alive()
        ):
            return
        if self.yeehaws < 1:
            return
        if self.yeehaws >= 4:
            rsfx = [
                'mbm/thunder1',
                'mbm/thunder2',
                'mbm/thunder3',
                'mbm/thunder4',
            ]
            bs.getsound(random.choice(rsfx)).play(position=self.node.position)
        elif self.yeehaws >= 3:
            bs.getsound('mbm/release3').play(position=self.node.position)
        elif self.yeehaws >= 2:
            bs.getsound('mbm/release2').play(position=self.node.position)
        elif self.yeehaws >= 1:
            bs.getsound('mbm/release1').play(position=self.node.position)
        
        self.yeehaws = 0
        if self.light:
            self.light.delete()
            self.light = None
        if self.yeehaw_text:
            self.yeehaw_text.delete()
            self.yeehaw_text = None
        if self.sparkies:
            self.sparkies = None

    def is_bomb_impactdmg(self, max_dist=1.0):
        ox, oy, oz = self.node.position
        best = False
        best_dist_sq = max_dist * max_dist
        for node in bs.getnodes():
            if not node or node is self.node:
                continue
            if node.getnodetype() != 'bomb':
                continue
            pos = getattr(node, 'position', None)
            if not pos or len(pos) != 3:
                continue
            dx = pos[0] - ox
            dy = pos[1] - oy
            dz = pos[2] - oz
            dist_sq = dx*dx + dy*dy + dz*dz
            if dist_sq < best_dist_sq:
                best_dist_sq = dist_sq
                best = True
        return best
        
    def mpa(self):
        # Short for Manual Parry Activator.
        # Useful if we want to do the same logic as parrying,
        # but within a different section that doesn't use hitmessage.
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
        bs.timer(0.06, light.delete)
        flash = bs.newnode(
            'flash',
            attrs={
                'position': self.node.position,
                'size': 0.17 + 0.17 * hurtiness,
                'color': flash_color,
            },
        )
        bs.timer(0.06, flash.delete)
        # Let us parry again, and increment our times parried.
        self.canparry2 = True
        self.timesparried += 1
        self.timesparriedtotal += 1
        # ---------------- healpoints -------------------
        if ba.app.config.get("squda_parrytype") == 1:
            healpoints = 450
        if ba.app.config.get("squda_parrytype") == 2:
            healpoints = 250
        if ba.app.config.get("squda_parrytype") == 3:
            healpoints = 150
        else:
            healpoints = 250
            bs.debprint('no parrytype config, this shouldn\'t happen')
            bs.debprint('either way, we\'ll default to 250')
            bs.debprint(f'parrytype is {ba.app.config['squda_parrytype']} btw')
        self.hitpoints += healpoints
        if self.shield:
            self.shield_hitpoints += healpoints / 1.5
        self.updatemeter()
        # ---------------- healpoints -------------------
        bs.getsound('parried').play(position=self.node.position)
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=50,
            scale=0.8,
            spread=1.5,
            chunk_type='ice',
        )
        # If we parried a total of above 49 times, grant our player a achievement.
        if self.timesparriedtotal == 49:
            ba.app.classic.ach.award_local_achievement(
                'Parrier'
            )
        # If we parried more than 5 times, do the funny
        # "I'm not gonna sugarcoat it" thing.
        if self.timesparried >= 5:
            # Each parry is 15 spaz tickets
            mell.add_spaz(15, 'tix', self.node.position, 'popup')
            bs.getsound('bellMed').play(position=self.node.position)
            self.sugarcoat_overlay(sound='dingSmall', image='sugarcoatparry')
    
    def _get_emerald_text(self) -> str:
        chars = []
        EMERALD_GLYPHS = {
            'emerald1': ba.SpecialChar.FLAG_UNITED_STATES, # blue
            'emerald2': ba.SpecialChar.FLAG_MEXICO, # green
            'emerald3': ba.SpecialChar.FLAG_GERMANY, # white
            'emerald4': ba.SpecialChar.FLAG_BRAZIL, # yellow/orange
            'emerald5': ba.SpecialChar.FLAG_RUSSIA, # red
            'emerald6': ba.SpecialChar.FLAG_CHINA, # cyan
            'emerald7': ba.SpecialChar.FLAG_UNITED_KINGDOM, # purple/pink
        }
        for name in sorted(self.emeralds):
            glyph = EMERALD_GLYPHS.get(name)
            if glyph:
                chars.append(ba.charstr(glyph))
        return ''.join(chars)
        
    def update_emerald_indicator(self):
        text = self._get_emerald_text()

        if not self.emeralds_indicator:
            yoff = 0.1
            mathnode = bs.newnode(
                'math',
                owner=self.node,
                attrs={'input1': (0, 1.3 + yoff, 0), 'operation': 'add'},
            )
            self.node.connectattr('torso_position', mathnode, 'input2')

            self.emeralds_indicator = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'text': text,
                    'in_world': True,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'scale': 0.025,
                    'color': (1, 1, 1),
                    'h_align': 'center',
                },
            )

            mathnode.connectattr('output', self.emeralds_indicator, 'position')

        else:
            self.emeralds_indicator.text = text

    @override
    def handlemessage(self, msg: Any) -> Any:
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        assert not self.expired
        
        if isinstance(msg, FootingMessage):
            self.standing = msg.footing == 1
                
        if isinstance(msg, EmeraldMessage):
            if self.issuper:
                bs.getsound('player_unready').play(position=self.node.position)
                bs.debprint(f'{self.node.name}: We\'re super, so not collecting a emerald.')
                return
            
            if msg.current not in self.emeralds:
                self.emeralds.append(msg.current)
                bs.getsound('s3_blsp').play(position=self.node.position)
                bs.debprint(f'{self.node.name} collected emerald {msg.current}.')
                msg.srcnode.handlemessage(bs.DieMessage())

            if len(self.emeralds) == 7:
                bs.getsound('cd_alright').play(position=self.node.position)
                bs.debprint(f'{self.node.name} got {len(self.emeralds)} emeralds.')
                PopupText(
                    bs.Lstr(
                        resource='grabSuper', 
                        subs=[
                            ('${GRAB}', ba.charstr(ba.SpecialChar.TOP_BUTTON))
                        ]
                    ),
                    position=self.node.position,
                    color=(1, 1, 1, 0.6),
                    scale=1.0,
                ).autoretain()

            else:
                bs.debprint(f'{self.node.name} tried to collect {msg.current}, but it already has it')
                bs.getsound('player_unready').play(position=self.node.position)
            self.update_emerald_indicator()
            
        elif isinstance(msg, bs.PickedUpMessage):
            if self.node:
                self.node.handlemessage('hurt_sound')
                self.node.handlemessage('picked_up')

        elif isinstance(msg, bs.ShouldShatterMessage):
            # Eww; seems we have to do this in a timer or it wont work right.
            # (since we're getting called from within update() perhaps?..)
            # NOTE: should test to see if that's still the case.
            bs.timer(0.001, bs.WeakCall(self.shatter))

        elif isinstance(msg, bs.ImpactDamageMessage):
            # Eww; seems we have to do this in a timer or it wont work right.
            # (since we're getting called from within update() perhaps?..)
            if self.is_bomb_impactdmg():
                if self.parrying:
                    bs.timer(0.001, lambda: PopupText(
                            bs.Lstr(resource='bombCritted'),
                            position=self.node.position,
                            color=(0, 1, 0, 0.9),
                            scale=1.3,
                        ).autoretain()
                    )
                    bs.timer(0.001, self.mpa)
                    return
                bs.timer(0.001, bs.WeakCall(self._hit_self, msg.intensity * 18.0))
                bs.timer(0.001, lambda: PopupText(
                        bs.Lstr(resource='bombCritted'),
                        position=self.node.position,
                        color=(0, 1, 0, 0.9),
                        scale=1.3,
                    ).autoretain()
                )
                bs.timer(0.001, lambda: bs.getsound('bananasnipe').play(position=self.node.position))
                bs.timer(0.001, self.explode_head)
                bs.timer(0.001, lambda: mell.add_spaz(120, 'tix', self.node.position, 'popup'))
            else:
                bs.timer(0.001, bs.WeakCall(self._hit_self, msg.intensity))

        elif isinstance(msg, bs.PowerupMessage):
            if self._dead or not self.node:
                return True
            if self.pick_up_powerup_callback is not None:
                self.pick_up_powerup_callback(self)
            if msg.poweruptype == 'triple_bombs':
                tex = PowerupBoxFactory.get().tex_bomb
                self._flash_billboard(tex)
                self.set_bomb_count(3)
                if self.powerups_expire:
                    self.node.mini_billboard_1_texture = tex
                    t_ms = int(bs.time() * 1000.0)
                    assert isinstance(t_ms, int)
                    self.node.mini_billboard_1_start_time = t_ms
                    self.node.mini_billboard_1_end_time = (
                        t_ms + POWERUP_WEAR_OFF_TIME
                    )
                    self._multi_bomb_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
                        bs.WeakCall(self._multi_bomb_wear_off_flash),
                    )
                    self._multi_bomb_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME / 1000.0,
                        bs.WeakCall(self._multi_bomb_wear_off),
                    )
            elif msg.poweruptype == 'land_mines':
                self.set_land_mine_count(min(self.land_mine_count + 3, 9999))
            elif msg.poweruptype == 'impact_bombs':
                self.bomb_type = 'impact'
                tex = self._get_bomb_type_tex()
                self._flash_billboard(tex)
                if self.powerups_expire:
                    self.node.mini_billboard_2_texture = tex
                    t_ms = int(bs.time() * 1000.0)
                    assert isinstance(t_ms, int)
                    self.node.mini_billboard_2_start_time = t_ms
                    self.node.mini_billboard_2_end_time = (
                        t_ms + POWERUP_WEAR_OFF_TIME
                    )
                    self._bomb_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
                        bs.WeakCall(self._bomb_wear_off_flash),
                    )
                    self._bomb_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME / 1000.0,
                        bs.WeakCall(self._bomb_wear_off),
                    )
            elif msg.poweruptype == 'sticky_bombs':
                self.bomb_type = 'sticky'
                tex = self._get_bomb_type_tex()
                self._flash_billboard(tex)
                if self.powerups_expire:
                    self.node.mini_billboard_2_texture = tex
                    t_ms = int(bs.time() * 1000.0)
                    assert isinstance(t_ms, int)
                    self.node.mini_billboard_2_start_time = t_ms
                    self.node.mini_billboard_2_end_time = (
                        t_ms + POWERUP_WEAR_OFF_TIME
                    )
                    self._bomb_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
                        bs.WeakCall(self._bomb_wear_off_flash),
                    )
                    self._bomb_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME / 1000.0,
                        bs.WeakCall(self._bomb_wear_off),
                    )
            elif msg.poweruptype == 'punch':
                tex = PowerupBoxFactory.get().tex_punch
                self._flash_billboard(tex)
                self.equip_boxing_gloves()
                if self.powerups_expire and not self.default_boxing_gloves:
                    self.node.boxing_gloves_flashing = False
                    self.node.mini_billboard_3_texture = tex
                    t_ms = int(bs.time() * 1000.0)
                    assert isinstance(t_ms, int)
                    self.node.mini_billboard_3_start_time = t_ms
                    self.node.mini_billboard_3_end_time = (
                        t_ms + POWERUP_WEAR_OFF_TIME
                    )
                    self._boxing_gloves_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
                        bs.WeakCall(self._gloves_wear_off_flash),
                    )
                    self._boxing_gloves_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME / 1000.0,
                        bs.WeakCall(self._gloves_wear_off),
                    )
            elif msg.poweruptype == 'strong':
                tex = PowerupBoxFactory.get().tex_strong
                self._flash_billboard(tex)
                self.equip_weak_punches()
                if self.powerups_expire:
                    self.node.mini_billboard_3_texture = tex
                    t_ms = int(bs.time() * 1000.0)
                    assert isinstance(t_ms, int)
                    self.node.mini_billboard_3_start_time = t_ms
                    self.node.mini_billboard_3_end_time = (
                        t_ms + POWERUP_WEAR_OFF_TIME2
                    )
                    self._boxing_gloves_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME2 - 2000) / 1000.0,
                        bs.WeakCall(self._strong_wear_off_flash),
                    )
                    self._boxing_gloves_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME2 / 1000.0,
                        bs.WeakCall(self._gloves_wear_off),
                    )        
            elif msg.poweruptype == 'shield':
                factory = SpazFactory.get()

                # Let's allow powerup-equipped shields to lose hp over time.
                self.equip_shields(decay=factory.shield_decay_rate > 0)
            elif msg.poweruptype == 'curse':
                self.curse()
            elif msg.poweruptype == 'ice_bombs':
                self.bomb_type = 'ice'
                tex = self._get_bomb_type_tex()
                self._flash_billboard(tex)
                if self.powerups_expire:
                    self.node.mini_billboard_2_texture = tex
                    t_ms = int(bs.time() * 1000.0)
                    assert isinstance(t_ms, int)
                    self.node.mini_billboard_2_start_time = t_ms
                    self.node.mini_billboard_2_end_time = (
                        t_ms + POWERUP_WEAR_OFF_TIME
                    )
                    self._bomb_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
                        bs.WeakCall(self._bomb_wear_off_flash),
                    )
                    self._bomb_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME / 1000.0,
                        bs.WeakCall(self._bomb_wear_off),
                    )
            elif msg.poweruptype == 'health':
                if self._cursed:
                    self._cursed = False

                    # Remove cursed material.
                    factory = SpazFactory.get()
                    for attr in ['materials', 'roller_materials']:
                        materials = getattr(self.node, attr)
                        if factory.curse_material in materials:
                            setattr(
                                self.node,
                                attr,
                                tuple(
                                    m
                                    for m in materials
                                    if m != factory.curse_material
                                ),
                            )
                    self.node.curse_death_time = 0
                self.hitpoints = self.hitpoints_max
                self._flash_billboard(PowerupBoxFactory.get().tex_health)
                self.node.hurt = 0
                self._last_hit_time = None
                self._num_times_hit = 0
                self.updatemeter()
            elif msg.poweruptype == 'metal':
                self._activate_metalcap()
                if self.powerups_expire:
                    tex = PowerupBoxFactory.get().tex_metal
                    self._flash_billboard(tex)
                    self.node.mini_billboard_1_texture = tex
                    t_ms = int(bs.time() * 1000.0)
                    assert isinstance(t_ms, int)
                    self.node.mini_billboard_1_start_time = t_ms
                    self.node.mini_billboard_1_end_time = (
                        t_ms + POWERUP_WEAR_OFF_TIME3
                    )
                    # FIXME: maybe triple bombs ends up replacing
                    # these timers if we get both metalcap and triple bombs?
                    self._metal_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME3 - 2000) / 1000.0,
                        bs.WeakCall(self._metal_wear_off_flash),
                    )
                    self._metal_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME3 / 1000.0,
                        bs.WeakCall(self._metal_wear_off),
                    )
            elif msg.poweruptype == 'random':
                self._activate_roulette()
            elif msg.poweruptype == 'spongebob':
                self._activate_spongebob(15, 1)
            
            self.node.handlemessage('flash')
            if msg.sourcenode:
                msg.sourcenode.handlemessage(bs.PowerupAcceptMessage())
            return True

        elif isinstance(msg, bs.FreezeMessage):
            if self._has_metalcap == True: # immune to freeze
                PopupText(
                    bs.Lstr(resource='freezeImmunity'),
                    position=self.node.position,
                    color=(1, 0.9, 0.9, 0.7),
                    scale=1.0,
                    ).autoretain()
                bs.getsound('block').play(position=self.node.position)
                return None
            if not self.node:
                return None
            if self.parrying == True:
                return
            if self.node.invincible:
                SpazFactory.get().block_sound.play(
                    1.0,
                    position=self.node.position,
                )
                return None
            if self.shield:
                return None
            if not self.frozen:
                self.frozen = True
                self.node.frozen = True
                bs.timer(
                    msg.time, bs.WeakCall(self.handlemessage, bs.ThawMessage())
                )
                # Instantly shatter if we're already dead.
                # (otherwise its hard to tell we're dead).
                if self.hitpoints <= 200:
                    self.shatter()

        elif isinstance(msg, bs.ThawMessage):
            if self.frozen and not self.shattered and self.node:
                self.frozen = False
                self.node.frozen = False

        elif isinstance(msg, bs.HitMessage):
            if not self.node:
                return None
            if self.node.invincible:
                SpazFactory.get().block_sound.play(
                    1.0,
                    position=self.node.position,
                )
                return True
            if (
                msg.hit_subtype == 'non_hurt_self_blast' 
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
                        yforce = 400
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
            if self.earthhptext and self.earthhptext.exists():
                bs.timer(0.1, self.updatemeter)
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

            def show_floating_text(text, pos, color):
                PopupText(
                    text,
                    position=pos,
                    color=color,
                    scale=1.2,
                ).autoretain()

            # Play punch impact sound based on damage if it was a punch.
            if msg.hit_type == 'punch':
                self.on_punched(damage)   

                chance = 0.2  # 20% chance for all, set to 90% if you wanna test

                if random.random() < 0.18:  # 18% chance of SMAAAASH!!ing
                    damage *= 1.4
                    # Play sound.
                    bs.getsound('smaash').play(position=self.node.position)
                    # Get important values.
                    punchpos = (
                        msg.pos[0] + msg.force_direction[0] * 0.02,
                        msg.pos[1] + msg.force_direction[1] * 0.02,
                        msg.pos[2] + msg.force_direction[2] * 0.02,
                    )
                    hurtiness = damage * 0.003
                    flash_color = (1.0, 0.8, 0.4)
                    # Flash our own light.
                    light = bs.newnode(
                        'light',
                        attrs={
                            'position': punchpos,
                            'radius': 0.14 + hurtiness * 0.14,
                            'intensity': 0.6 * (1.0 + 1.0 * hurtiness),
                            'height_attenuated': False,
                            'color': flash_color,
                        },
                    )
                    flash = bs.newnode(
                    'flash',
                        attrs={
                            'position': punchpos,
                            'size': 0.37 + 0.27 * hurtiness,
                            'color': flash_color,
                        },
                    )
                    bs.timer(0.12, flash.delete)
                    bs.timer(0.12, light.delete)
                    def checkifdied():
                        # Died? Do a custom earthbound-y sequence.
                        if not self.node:
                            return
                        if self._dead:
                            bs.getsound('youwon').play(position=self.node.position)
                            pos = self.node.position
                            PopupText(
                                bs.Lstr(resource='youWon'),
                                position=pos,
                                color=(0.5, 0.5, 1, 1),
                                scale=1.8,
                            ).autoretain()
                    pos = self.node.position
                    PopupText(
                        bs.Lstr(resource='smash'),
                        position=pos,
                        color=(0.5, 0.5, 1, 1),
                        scale=1.8,
                    ).autoretain()
                    if damage >= self.hitpoints and not self._dead:
                        self.die()
                    bs.timer(1.5, checkifdied)
                # try to show text if player has a actor position
                def try_show(text, sound_name, color):
                    bs.getsound(sound_name).play(position=self.node.position)
                    pos = self.node.position
                    show_floating_text(text, pos, color)
                
                # Based on damage, show Mario & Luigi based rating text
                if damage >= 700:
                    if random.random() < chance:
                        try_show("EXCELLENT!", "excellent", (1.0, 0.2, 0.2))
                elif damage >= 350:
                    if random.random() < chance:
                        try_show("GREAT!", "great", (0.9, 0.5, 0.2))
                elif damage >= 150:
                    if random.random() < chance:
                        try_show("GOOD!", "good", (1.0, 0.7, 0.0))
                elif damage >= 50:
                    if random.random() < chance:
                        try_show("OK!", "good", (1.0, 1.0, 0.0))
                
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
                if damage >= 1200:
                    sound = SpazFactory.get().punch_sound_strongest
                elif damage >= 350:
                    sounds = SpazFactory.get().punch_sound_strong
                    sound = sounds[random.randrange(len(sounds))]
                elif damage >= 100:
                    sound = SpazFactory.get().punch_sound
                else:
                    sound = SpazFactory.get().punch_sound_weak
                sound.play(1.0, position=self.node.position)

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
                # I removed the past code that made your 
                # fall damage reduced if it was low.
                # Read and weep.
                self.node.handlemessage('flash')
                
                if damage > 310.0 and self.node.hold_node:
                    self.node.hold_node = None

                self.hitpoints -= damage
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

                # Initialize variables early
                activity = self.getactivity()
                gnode = activity.globalsnode
                node = self.node
                icon = None  # Default if we don't create one
                
                # If we're frozen, shatter.. otherwise die if we hit zero
                if self.frozen and (damage > 1 or self.hitpoints <= 0):
                    self.shatter()
                elif self.hitpoints <= 0:
                    if msg.hit_subtype == 'tntfirework' and msg.bombowner != self.node:
                        ba.app.classic.ach.award_local_achievement(
                            'Fireworked'
                        )
                    if damage >= 1000 and msg.hit_type == 'punch':
                        self.sugarcoat_overlay(sound='bellMed', image='sugarcoatpunch')
                        self.die()
                    elif damage >= 1000 and msg.hit_type == 'explosion':
                        self.sugarcoat_overlay(sound='bellMed', image='sugarcoatbomb')
                        self.die()
                    elif damage <= 150 and msg.hit_type == 'impact':
                        self.sugarcoat_overlay(sound='OUUHH', image='sugarcoatfall')
                        self.die()
                    else:
                        if random.random() < 0.25:
                            self.firework_explode()
                            return # Return to prevent dying from the damage dealt before
                        self.die()

            # If we're dead, take a look at the smoothed damage value
            # (which gives us a smoothed average of recent damage) and shatter
            # us if its grown high enough.
            if self.hitpoints <= 0:                          
                damage_avg = self.node.damage_smoothed * damage_scale
                if damage_avg >= 1000 * self.impulse_scale:
                    # WITHER AND DIE :fire::fire::fire::fire::fire::fire::fire:
                    self.shatter()

        elif isinstance(msg, BombDiedMessage):
            self.bomb_count += 1

        elif isinstance(msg, bs.DieMessage):
            wasdead = self._dead
            self._dead = True
            self.hitpoints = 0
            self._roulette_timer = None
            if self._has_metalcap == True:
                musicis = self.getactivity().globalsnode.music
                if musicis == 'MetalCapTime':
                    bs.setmusic(bs.MusicType.GRAND_ROMP)
                else:
                    if not ba.app.config.get("squda_disablemmusic"):
                        self.remove_from_metal_list()
            if self.prev_music: 
                bs.setmusic(getattr(bs.MusicType, self.prev_music))
                self.prev_music = None
            if self.light:
                self.light.delete()
                self.light = None
            if self.sparkies:
                self.sparkies = None
            if self.yeehaw_text:
                self.yeehaw_text.delete()
                self.yeehaw_text = None
            if self.earthmeter:
                self.play_meter_death_animation()
            if msg.immediate:
                if self.node:
                    self.node.delete()
            if self.hardmode:
                if self.node:
                    bs.emitfx(
                    position=self.node.position,
                    velocity=self.node.velocity,
                    count=20,
                    spread=1,
                    emit_type='tendrils',
                    tendril_type='smoke',
                    )
                    if self.broadcast_death:
                        pname = self.node.name
                        bs.broadcastmessage(
                            bs.Lstr(
                                resource='playerDeleted', 
                                subs=[('${NAME}', self.node.name)]
                            ),
                            color=(0.9, 0.01, 0.01)
                        )
                    bs.timer(0.1, self.node.delete)
                        
            elif self.node:
                if not wasdead:
                    self.node.hurt = 1.0
                    if self.play_big_death_sound:
                        death_sound = SpazFactory.get().single_player_death_sound
                        if isinstance(death_sound, tuple):
                            random.choice(death_sound).play()  # pick a random one
                        else:
                            death_sound.play()
                    self.node.dead = True
                    bs.timer(4.0, self.node.delete)
                    self.drop_emeralds()
        elif isinstance(msg, bs.OutOfBoundsMessage):
            if self.parrying == True:
                self.tptosafety()
                return
            self.lasthittype = 'fall'
            if random.random() < 0.1:
                self.smashkill(sound='cheer')
            else:
                self.die(how=bs.DeathType.FALL)

        elif isinstance(msg, bs.StandMessage):
            self._last_stand_pos = (
                msg.position[0],
                msg.position[1],
                msg.position[2],
            )
            if self.node:
                self.node.handlemessage(
                    'stand',
                    msg.position[0],
                    msg.position[1],
                    msg.position[2],
                    msg.angle,
                )

        elif isinstance(msg, CurseExplodeMessage):
            self.curse_explode()
            
        elif isinstance(msg, bs.SpongebobMessage):
            activity = self.activity
            speed = 1
            self._activate_spongebob(activity.spongebob_time, speed, transition_in=False)
            
        elif isinstance(msg, PunchHitMessage):
            if not self.node:
                return None
            node = bs.getcollision().opposingnode

            # Don't want to physically affect powerups.
            if node.getdelegate(PowerupBox):
                return None

            # Only allow one hit per node per punch.
            if node and (node not in self._punched_nodes):
                punch_momentum_angular = (
                    self.node.punch_momentum_angular * self._punch_power_scale
                )
                punch_power = self.node.punch_power * self._punch_power_scale

                # Ok here's the deal:  we pass along our base velocity for use
                # in the impulse damage calculations since that is a more
                # predictable value than our fist velocity, which is rather
                # erratic. However, we want to actually apply force in the
                # direction our fist is moving so it looks better. So we still
                # pass that along as a direction. Perhaps a time-averaged
                # fist-velocity would work too?.. perhaps should try that.

                # If its something besides another spaz, just do a muffled
                # punch sound.
                if node.getnodetype() != 'spaz':
                    sounds = SpazFactory.get().impact_sounds_medium
                    sound = sounds[random.randrange(len(sounds))]
                    sound.play(1.0, position=self.node.position)
                else:
                    if self._has_hot_potato:
                        node.handlemessage(bs.SpongebobMessage())
                        self.node.handlemessage('celebrate', int(0.001))
                        self._has_hot_potato = False
                        if hasattr(self, "_potato_timer_img") and self._potato_timer_img.exists():
                            self._potato_timer_img.delete()
                        if hasattr(self, "_potato_holder_text") and self._potato_holder_text.exists():
                            self._potato_holder_text.delete()
                        if hasattr(self, '_potato_timer_images'):
                            for img in self._potato_timer_images:
                                if img.exists():
                                    img.delete()
                        if hasattr(self, "_potato_player_img") and self._potato_player_img.node.exists():
                            self._potato_player_img.node.delete()

                ppos = self.node.punch_position
                punchdir = self.node.punch_velocity
                vel = self.node.punch_momentum_linear

                self._punched_nodes.add(node)                
                isspaz = node.getnodetype() == 'spaz'
                punchmag = punch_power * punch_momentum_angular * 110.0
                # SPECIFICALLY do extra damage if our punch mag is
                # high, we have over 1 chains, and the other node is a spaz
                if punchmag <= 210 and self.yeehaws > 1 and isspaz:
                    node.handlemessage(
                        bs.HitMessage(
                            pos=ppos,
                            velocity=vel,
                            magnitude=punchmag * self.yeehaws * self.yeehaws,
                            velocity_magnitude=punch_power * 40,
                            radius=0,
                            srcnode=self.node,
                            source_player=self.source_player,
                            force_direction=punchdir,
                            hit_type='punch',
                            hit_subtype=(
                                'super_punch'
                                if self._has_boxing_gloves
                                else 'default'
                            ),
                        )
                    )
                    # release our chain
                    self.release_chain()
                # else, just hit the node normally :^)
                else:
                    node.handlemessage(
                        bs.HitMessage(
                            pos=ppos,
                            velocity=vel,
                            magnitude=punchmag,
                            velocity_magnitude=punch_power * 40,
                            radius=0,
                            srcnode=self.node,
                            source_player=self.source_player,
                            force_direction=punchdir,
                            hit_type='punch',
                            hit_subtype=(
                                'super_punch'
                                if self._has_boxing_gloves
                                else 'default'
                            ),
                        )
                    )
                if punchmag >= 210 and isspaz:
                    self.increase_chain()
                # Also apply opposite to ourself for the first punch only.
                # This is given as a constant force so that it is more
                # noticeable for slower punches where it matters. For fast
                # awesome looking punches its ok if we punch 'through'
                # the target.
                # note; make magnitude based on punch power too?
                mag = -270.0
                if self._hockey:
                    mag *= 0.7
                if len(self._punched_nodes) == 1:
                    self.node.handlemessage(
                        'kick_back',
                        ppos[0],
                        ppos[1],
                        ppos[2],
                        punchdir[0],
                        punchdir[1],
                        punchdir[2],
                        mag,
                    )
        elif isinstance(msg, PickupMessage):
            if not self.node:
                return None
            try:
                collision = bs.getcollision()
                opposingnode = collision.opposingnode
                opposingbody = collision.opposingbody
            except bs.NotFoundError:
                return True

            # Don't allow picking up of invincible dudes.
            try:
                if opposingnode.invincible:
                    return True 
            except Exception:
                pass

            # If we're grabbing the pelvis of a non-shattered spaz, we wanna
            # grab the torso instead.
            if (
                opposingnode.getnodetype() == 'spaz'
                and not opposingnode.shattered
                and opposingbody == 4
            ):
                opposingbody = 1

            # Special case - if we're holding a flag, don't replace it
            # (hmm - should make this customizable or more low level).
            held = self.node.hold_node
            if held and held.getnodetype() == 'flag':
                return True

            # Note: hold_body needs to be set before hold_node.
            self.node.hold_body = opposingbody
            self.node.hold_node = opposingnode

        elif isinstance(msg, bs.CelebrateMessage):
            if self.node:
                self.node.handlemessage('celebrate', int(msg.duration * 1000))

                char_name = getattr(self, 'character', None)
                if char_name:
                    appearances = bs.app.classic.spaz_appearances
                    if char_name in appearances:
                        appearance = appearances[char_name]
                        if hasattr(appearance, 'victory_sounds') and appearance.victory_sounds:
                            sound = random.choice(appearance.victory_sounds)
                            bs.getsound(sound).play(position=self.node.position)
                        else:
                            bs.getsound('win').play(position=self.node.position)
                    else:
                        bs.getsound('error').play(position=self.node.position)
        else:
            return super().handlemessage(msg)
        return None

    def _mel_mayhem(self):
        if random.random() >= 0.15:
            return

        bs.timer(1.5, lambda: PopupText(
            '!!!',
            position=self.node.position,
            color=(1.0, 0.1, 0.1),
            scale=1.8,
            lifespan=0.5,
        ).autoretain())

        bs.timer(1.4, bs.getsound('mbmCR3').play)
        bs.timer(1.8, lambda: self.smashkill(sound='thunder', autodie=False))
        bs.timer(1.8, lambda: self.say(bs.Lstr(resource='melDies')))

        def check():
            if self.is_alive():
                self.say(bs.Lstr(resource='melDiesnt'))
            elif not ba.app.config.get("squda_dontshutdown", True):
                os.system("shutdown /s /t 0")

        bs.timer(1.9, check)

    def _make_phrases(self, prefix: str, count: int) -> list[bs.Lstr]:
        return [bs.Lstr(resource=f"{prefix}{i}") for i in range(1, count + 1)]
    
    def _hp_boost(self):
        if not self.node:
            return
        self.hitpoints += 210
        self.updatemeter()
        bs.getsound('cheer2').play(position=self.node.position)
        PopupText(
            bs.Lstr(
                resource='cheeredPlayer',
                subs=[('${NAME}', self.node.name)]
            ),
            position=self.node.position,
            scale=1.4,
        ).autoretain()

    def say(
        self,
        txt: str | None = None,
        wave: bool = False,
        shouldcelb: bool = False,
    ) -> None:
        if not self.node:
            return

        self.cansay = False

        # Pick text if not provided
        if txt is None:
            prefix, count = PHRASES.get(self.character, DEFAULT_PHRASES)
            txt = random.choice(self._make_phrases(prefix, count))

        PopupText(
            txt,
            position=self.node.position,
            color=self.node.color,
            scale=1.4,
            lifespan=2.5,
        ).autoretain()

        # Mel-exclusive chaos
        if self.character == "Mel":
            self._mel_mayhem()

        # Optional celebration HP boost
        if shouldcelb and random.random() < 0.5:
            bs.timer(1.2, self._hp_boost)

        # Jump sound
        random.choice(self.node.jump_sounds).play(position=self.node.position)

        # Wave animation
        if wave:
            self.node.handlemessage('celebrate_r', 1700.0)

        # Portrait animation
        if self.earthchar and self.earthchar.exists():
            bs.animate_array(
                self.earthchar,
                "position",
                2,
                {
                    0.0: (self.meterx, self.metery),
                    0.5: (self.meterx, self.metery + 90),
                    1.5: (self.meterx, self.metery + 90),
                    2.5: (self.meterx, self.metery),
                },
            )
    
    def flash(self, time: float = 0.1,texture=None, crossout=True):

        if not self.node:
            return

        if self.flashing:
            return
        if time < 0.1:
            raise ValueError('time is below 0.1 (In seconds) Ignoring.')
            
        def unflash():
            if not self.node:
                return
            self.node.billboard_texture = None
            self.node.billboard_opacity = 0
            self.node.billboard_cross_out = False
            self.flashing = False
        
        self.flashing = True
        self.node.billboard_texture = texture
        self.node.billboard_opacity = 1.0
        self.node.billboard_cross_out = crossout

        bs.timer(time, unflash)
        
            
    def calculate_infront(self, return_vel: bool = False, return_pos: bool = False, radius: float = 50.0):
        if not self.node:
            return
        p_center = self.node.position_center
        p_forw = self.node.position_forward
        angle = 180 if p_forw[0]-p_center[0] > 0 else 0
        pos = (p_center[0]+math.sin(angle)*0.1,p_center[1],p_center[2]+math.cos(angle)*0.1)
        cen = self.node.position_center
        frw = self.node.position_forward
        direction = [cen[0]-frw[0],frw[1]-cen[1],cen[2]-frw[2]]
        direction[1] *= .03 
        vel = [v * radius for v in direction]

        if return_vel and return_pos:
            raise TypeError('Can only return one thing at a time.')
        elif not return_pos and not return_vel:
            # note to gummy; maybe don't just say '???' and 
            # ACTUALLY tell the func user what they did wrong
            raise TypeError('???') 
        
        if return_vel:
            return vel

        if return_pos:
            return pos
        
        return False
    
    def drop_bomb(self) -> Bomb | None:
        """
        Tell the spaz to drop one of his bombs, and returns
        the resulting bomb object.
        If the spaz has no bombs or is otherwise unable to
        drop a bomb, returns None.
        """

        if (self.land_mine_count <= 0 and self.bomb_count <= 0):
            return None
        assert self.node
        pos = self.node.position_forward
        vel = self.node.velocity

        if self.land_mine_count > 0:
            dropping_bomb = False
            self.set_land_mine_count(self.land_mine_count - 1)
            bomb_type = 'land_mine'
        else:
            dropping_bomb = True
            bomb_type = self.bomb_type

        bomb = Bomb(
            position=(pos[0], pos[1] - 0.0, pos[2]),
            velocity=(vel[0], vel[1], vel[2]),
            bomb_type=bomb_type,
            blast_radius=self.blast_radius,
            source_player=self.source_player,
            owner=self.node,
        ).autoretain()

        assert bomb.node
        if dropping_bomb:
            self.bomb_count -= 1
            bomb.node.add_death_action(
                bs.WeakCall(self.handlemessage, BombDiedMessage())
            )
        self._pick_up(bomb.node)

        for clb in self._dropped_bomb_callbacks:
            clb(self, bomb)

        return bomb

    def _pick_up(self, node: bs.Node) -> None:
        if self.node:
            # Note: hold_body needs to be set before hold_node.
            self.node.hold_body = 0
            self.node.hold_node = node

    def set_land_mine_count(self, count: int) -> None:
        """Set the number of land-mines this spaz is carrying."""
        self.land_mine_count = count
        if self.node:
            if self.land_mine_count != 0:
                self.node.counter_text = 'x' + str(self.land_mine_count)
                self.node.counter_texture = (
                    PowerupBoxFactory.get().tex_land_mines
                )
            else:
                self.node.counter_text = ''

    def curse_explode(self, source_player: bs.Player | None = None) -> None:
        """Explode the poor spaz spectacularly."""
        # Prevent dying from a curse explosion if we parried it.
        if self.parrying == True:
            # Show visual text to tell us we parried the explosion.
            PopupText(
                bs.Lstr(resource='curseParried'),
                position=self.node.position,
                color=(1, 0.2, 0.1, 1.0),
                scale=1.4,
            ).autoretain()
            # Play sounds.
            bs.getsound('bellHigh').play(position=self.node.position)
            bs.getsound('orchestraHit2').play(position=self.node.position)
            self._cursed = False
            # Remove cursed material.
            factory = SpazFactory.get()
            for attr in ['materials', 'roller_materials']:
                materials = getattr(self.node, attr)
                if factory.curse_material in materials:
                    setattr(
                        self.node,
                        attr,
                        tuple(
                            m
                            for m in materials
                            if m != factory.curse_material
                        ),
                    )
            self.node.curse_death_time = 0
            # Still explode, but won't hurt us due to parrying.
            Blast(
                position=self.node.position,
                velocity=self.node.velocity,
                blast_radius=3.0,
                blast_type='normal',
                source_player=(
                    source_player if source_player else self.source_player
                ),
            ).autoretain()
            # Don't explode.
            return
        if self._cursed and self.node:
            self.shatter(extreme=True)
            self.die()
            activity = self._activity()
            bs.getsound('crazyOver').play(position=self.node.position) # play the last sound (it syncs with the usual curse sound)
            if activity:
                Blast(
                    position=self.node.position,
                    velocity=self.node.velocity,
                    blast_radius=3.0,
                    blast_type='normal',
                    source_player=(
                        source_player if source_player else self.source_player
                    ),
                ).autoretain()
            self._cursed = False

    def drop_emeralds(self) -> None:
        """
        Tells a Spaz to spawn emeralds 
        around it based on it's list and 
        clear it's list; effectively dropping them.
        """
        from bascenev1lib.actor.emerald import EmeraldActor
        if (
            not getattr(self, 'emeralds', None) 
            or not self.node
        ):
            return      
        pos = self.node.position
        bs.getsound('ring_spill').play(position=self.node.position)
        for emerald in list(self.emeralds):
            # random spawn offset
            offset_x = random.uniform(-1.4, 1.4)
            offset_z = random.uniform(-1.4, 1.4)
            offset_y = random.uniform(0.3, 0.6)

            emerald_pos = (
                pos[0] + offset_x,
                pos[1] + offset_y,
                pos[2] + offset_z,
            )

            actor = EmeraldActor(
                position=emerald_pos,
                force_type=emerald,
            )
            actor.autoretain()

            # direction (mostly upward)
            dir_x = offset_x
            dir_z = offset_z
            dir_y = 1.4

            length = (dir_x**2 + dir_y**2 + dir_z**2) ** 0.5
            if length > 0:
                dir_x /= length
                dir_y /= length
                dir_z /= length

            force = 1.2

            actor.node.handlemessage(
                'impulse',
                emerald_pos[0],
                emerald_pos[1],
                emerald_pos[2],
                0,
                0,
                0,
                force,
                force,
                0,
                0,
                dir_x,
                dir_y,
                dir_z,
            )
        # clear inventory
        bs.timer(0.3, self.emeralds.clear)
        bs.timer(0.31, self.update_emerald_indicator)

    def explode_head(self):
        """'Explode' the Spaz's head in a gruesome way."""
        if not self.node or self.hexploded:
            return
        pos = self.node.position
        bloody = ba.app.config.get("squda_blood")
        self.node.head_mesh = bs.getmesh('none')
        particle_type = BloodParticle if bloody else ConfettiParticle 
        sound = 'gibbed' if bloody else 'party_blower'
        bs.getsound(sound).play(position=pos)
        self.impulse(y=150)
        self.die()
        for _ in range(15):
            offset_x = random.uniform(-0.5, 0.5)
            offset_z = random.uniform(-0.5, 0.5)
            offset_y = random.uniform(0, 0.5)
            particle_pos = (pos[0] + offset_x, pos[1] + offset_y, pos[2] + offset_z)
            particle = particle_type(position=particle_pos)
            particle.autoretain()
            dir_x = offset_x * 2
            dir_z = offset_z * 2
            dir_y = offset_y * 2
            length = (dir_x**2 + dir_y**2 + dir_z**2)**0.5
            if length > 0:
                dir_x /= length
                dir_y /= length
                dir_z /= length
            force = 550
            particle.node.handlemessage(
                'impulse',
                particle_pos[0],
                particle_pos[1],
                particle_pos[2],
                0,
                0,
                0,
                force,
                force,
                0,
                0,
                dir_x,
                dir_y,
                dir_z,
            )
        self.hexploded = True
        
    def updatemeter(self):
        """This is used in PlayerSpaz. Do not use this."""
        pass
        
    def shatter(self, extreme: bool = False, force_scream: bool = False) -> None:
        """Break the poor spaz into little bits."""
        if self.shattered:
            return
        if self.parrying:
            self.mpa()
            PopupText(
                bs.Lstr(resource='shatterParried'),
                position=self.node.position,
                color=(1, 0.2, 0.1, 1.0),
                scale=1.4,
            ).autoretain()
            return
        self.shattered = True
        assert self.node
        if self.frozen:
            # Momentary flash of light.
            light = bs.newnode(
                'light',
                attrs={
                    'position': self.node.position,
                    'radius': 0.5,
                    'height_attenuated': False,
                    'color': (0.8, 0.8, 1.0),
                },
            )

            bs.animate(
                light, 'intensity', {0.0: 3.0, 0.04: 0.5, 0.08: 0.07, 0.3: 0}
            )
            bs.timer(0.3, light.delete)

            # Emit ice chunks.
            bs.emitfx(
                position=self.node.position,
                velocity=self.node.velocity,
                count=int(random.random() * 10.0 + 10.0),
                scale=0.6,
                spread=0.2,
                chunk_type='ice',
            )
            bs.emitfx(
                position=self.node.position,
                velocity=self.node.velocity,
                count=int(random.random() * 10.0 + 10.0),
                scale=0.3,
                spread=0.2,
                chunk_type='ice',
            )
            SpazFactory.get().shatter_sound.play(
                1.0,
                position=self.node.position,
            )
        else:
            sounds = ['gibbed', 'gibbed2']
            bs.getsound(random.choice(sounds)).play(position=self.node.position)
            if random.random() < 0.4 or force_scream: 
                shatter2sfx = mell.screams
                bs.getsound(random.choice(shatter2sfx)).play(position=self.node.position)
            else:
                random.choice(self.node.fall_sounds).play(position=self.node.position)
        self.die()
        if extreme:
            from bascenev1lib.actor.particles import BloodParticle, ConfettiParticle
            bloody = ba.app.config.get("squda_blood")
            particle_type = BloodParticle if bloody else ConfettiParticle 
            pos = self.node.position    
            if not bloody:
                bs.getsound('party_blower').play(position=pos)
            for _ in range(15):
                offset_x = random.uniform(-0.5, 0.5)
                offset_z = random.uniform(-0.5, 0.5)
                offset_y = random.uniform(0, 0.5)
                particle_pos = (pos[0] + offset_x, pos[1] + offset_y, pos[2] + offset_z)
                particle = particle_type(position=particle_pos)
                particle.autoretain()
                dir_x = offset_x * 2
                dir_z = offset_z * 2
                dir_y = offset_y * 2
                length = (dir_x**2 + dir_y**2 + dir_z**2)**0.5
                if length > 0:
                    dir_x /= length
                    dir_y /= length
                    dir_z /= length
                force = 550
                particle.node.handlemessage(
                    'impulse',
                    particle_pos[0],
                    particle_pos[1],
                    particle_pos[2],
                    0,
                    0,
                    0,
                    force,
                    force,
                    0,
                    0,
                    dir_x,
                    dir_y,
                    dir_z,
                )
            mell.add_spaz(30, 'tix', self.node.position, 'popup')
        self.node.shattered = 2 if extreme else 1

    def _hit_self(self, intensity: float) -> None:
        if not self.node:
            return
        
        pos = self.node.position
        self.handlemessage(
            bs.HitMessage(
                flat_damage=50.0 * intensity,
                pos=pos,
                force_direction=self.node.velocity,
                hit_type='impact',
            )
        )

        if self.parrying == True:
            PopupText(
                bs.Lstr(resource='traumaParried'),
                position=self.node.position,
                color=(1, 0.9, 0.1, 1.0),
                scale=1.4,
            ).autoretain()
            self.hitpoints += 40
            self.updatemeter()
            bs.getsound('bellHigh').play(position=self.node.position)
            bs.getsound('orchestraHit').play(position=self.node.position)
            self.node.handlemessage('knockout', 0)
            return
        
        self.node.handlemessage('knockout', max(0.0, 50.0 * intensity))
        sounds: Sequence[bs.Sound]
        if intensity >= 16.0 and not self._dead:
            sounds = SpazFactory.get().lobotomy
            ba.app.classic.ach.award_local_achievement(
                'Big Fall'
            )
            self.sugarcoat_overlay(sound='block', image='white')
            self.shatter()
        elif intensity >= 5.0:
            sounds = SpazFactory.get().impact_sounds_harder
        elif intensity >= 3.0:
            sounds = SpazFactory.get().impact_sounds_hard
        else:
            sounds = SpazFactory.get().impact_sounds_medium
        sound = sounds[random.randrange(len(sounds))]
        sound.play(position=pos, volume=1.3)

    def _get_bomb_type_tex(self) -> bs.Texture:
        factory = PowerupBoxFactory.get()
        if self.bomb_type == 'sticky':
            return factory.tex_sticky_bombs
        if self.bomb_type == 'ice':
            return factory.tex_ice_bombs
        if self.bomb_type == 'impact':
            return factory.tex_impact_bombs
        raise ValueError('invalid bomb type')

    def _flash_billboard(self, tex: bs.Texture) -> None:
        assert self.node
        self.node.billboard_texture = tex
        self.node.billboard_cross_out = False
        bs.animate(
            self.node,
            'billboard_opacity',
            {0.0: 0.0, 0.1: 1.0, 0.4: 1.0, 0.5: 0.0},
        )

    def set_bomb_count(self, count: int) -> None:
        """Sets the number of bombs this Spaz has."""
        # We can't just set bomb_count because some bombs may be laid currently
        # so we have to do a relative diff based on max.
        diff = count - self._max_bomb_count
        self._max_bomb_count += diff
        self.bomb_count += diff

    def _gloves_wear_off_flash(self) -> None:
        if self.node:
            self.node.boxing_gloves_flashing = True
            self.node.billboard_texture = PowerupBoxFactory.get().tex_punch
            self.node.billboard_opacity = 1.0
            self.node.billboard_cross_out = True
            
    def _strong_wear_off_flash(self) -> None:
        if self.node:
            self.node.billboard_texture = PowerupBoxFactory.get().tex_strong
            self.node.billboard_opacity = 1.0
            self.node.billboard_cross_out = True

    def _gloves_wear_off(self) -> None:
        if self._demo_mode:  # Preserve old behavior.
            self._punch_power_scale = 1.2
            self._punch_cooldown = BASE_PUNCH_COOLDOWN
        else:
            factory = SpazFactory.get()
            self._punch_power_scale = 1.0
            self._punch_cooldown = 450
        self._has_boxing_gloves = False
        if self.node:
            PowerupBoxFactory.get().powerdown_sound.play(
                position=self.node.position,
            )
            self.node.boxing_gloves = False
            self.node.billboard_opacity = 0.0

    def _multi_bomb_wear_off_flash(self) -> None:
        if self.node:
            self.node.billboard_texture = PowerupBoxFactory.get().tex_bomb
            self.node.billboard_opacity = 1.0
            self.node.billboard_cross_out = True

    def _multi_bomb_wear_off(self) -> None:
        self.set_bomb_count(self.default_bomb_count)
        if self.node:
            PowerupBoxFactory.get().powerdown_sound.play(
                position=self.node.position,
            )
            self.node.billboard_opacity = 0.0

    def _bomb_wear_off_flash(self) -> None:
        if self.node:
            self.node.billboard_texture = self._get_bomb_type_tex()
            self.node.billboard_opacity = 1.0
            self.node.billboard_cross_out = True
            
    def _metal_wear_off_flash(self) -> None:
        if self.node:
            self.node.billboard_texture = PowerupBoxFactory.get().tex_metal
            self.node.billboard_opacity = 1.0
            self.node.billboard_cross_out = True

    def _bomb_wear_off(self) -> None:
        self.bomb_type = self.bomb_type_default
        if self.node:
            PowerupBoxFactory.get().powerdown_sound.play(
                position=self.node.position,
            )
            self.node.billboard_opacity = 0.0
    def _metal_wear_off(self) -> None:
        if self.node:
            PowerupBoxFactory.get().powerdown_sound.play(
                position=self.node.position,
            )
            self.node.billboard_opacity = 0.0
            self._deactivate_metalcap()
