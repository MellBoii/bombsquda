"""Functionality for rolling balls that are controlled by players."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload, override

import math

import bascenev1 as bs
import bascenev1lib as bslib
from bascenev1lib.actor.spaz import FootingMessage
from bascenev1lib.actor.playerspaz import PlayerSpazHurtMessage
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.bomb import ExplodeHitMessage
from bascenev1lib.actor.popuptext import PopupText

COLOR_TEXTURES = {
    'confetti_colors/purple': (0.6, 0.2, 0.8),
    'confetti_colors/orange': (1.0, 0.5, 0.1),
    'confetti_colors/green':  (0.2, 0.8, 0.2),
    'confetti_colors/blue':   (0.2, 0.4, 1.0),
    'confetti_colors/red':    (1.0, 0.2, 0.2),
    'confetti_colors/yellow': (1.0, 0.9, 0.2),
    'white2':                 (1.0, 1.0, 1.0),
    'black':                  (0.0, 0.0, 0.0),
}



if TYPE_CHECKING:
    from typing import Any, Sequence, Literal

class CollideMessage:
    """A message telling us we collided with another player/ball."""
    def __init__(self, collided):
        self.collided = collided

class PlayerBall(bs.Actor):
    """A rolling ball controlled by a bascenev1.Player."""
    node: bs.Node

    def texture_for_color(self, color):
        """
        color: (r, g, b) in 0–1 range
        returns: texture name
        """
        def color_distance(a, b):
            return (
                (a[0] - b[0]) ** 2 +
                (a[1] - b[1]) ** 2 +
                (a[2] - b[2]) ** 2
            )
        best_tex = None
        best_dist = float('inf')

        for tex, tex_color in COLOR_TEXTURES.items():
            d = color_distance(color, tex_color)
            if d < best_dist:
                best_dist = d
                best_tex = tex

        return best_tex

    def __init__(
        self,
        player: bs.Player,
        position: tuple[float, float, float],
        color: tuple[float, float, float] = (1, 1, 1),
    ):
        super().__init__()
        # Make the ball node.
        shared = SharedObjects.get()
        footing_material = shared.footing_material
        player_material = shared.player_material
        self.roller_material = bs.Material()
        self.roller_material.add_actions(
            conditions=(
                ('they_are_different_node_than_us',),
                'and',
                ('they_have_material', player_material),
            ),
            actions=(
                ('message', 'our_node', 'at_connect', CollideMessage(1)),
                ('message', 'our_node', 'at_disconnect', CollideMessage(-1)),
            ),
        )
        self.roller_material.add_actions(
            conditions=('they_have_material', footing_material),
            actions=(
                ('message', 'our_node', 'at_connect', FootingMessage(1)),
                ('message', 'our_node', 'at_disconnect', FootingMessage(-1)),
            ),
        )
        texture = self.texture_for_color(color)
        mesh = 'bomb'
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'position': position,
                'mesh': bs.getmesh(mesh),
                'light_mesh': bs.getmesh(mesh),
                'body': 'sphere',
                'body_scale': 1.0,
                'shadow_size': 0.5,
                'color_texture': bs.gettexture(texture),
                'reflection': 'soft',
                'reflection_scale': [0.23],
                'materials': [self.roller_material, player_material],
            },
        )
        self.source_player = player
        self._connected_to_player: bs.Player | None = None
        self._num_times_hit = 0
        self.points_mult = 0
        self.can_thok = False
        self.parrying = False
        self.lasthittype = None
        self.initial_speed = 600.0
        self.multipliernt = 4
        self.speed = self.initial_speed / self.multipliernt
        self.move_x = 0.0
        self.move_z = 0.0
        self.move_timer = None
        self.node.is_area_of_interest = True
        self.name_text = None
        self.hp_text = None
        self.standing = False
        self._dead = False
        self.last_player_attacked_by = None
        self.max_hitpoints = 1000
        self.hitpoints = self.max_hitpoints
        self.set_hp(
            (
                f'{str(int(self.hitpoints / 10))}'
                f'/{str(int(self.max_hitpoints / 10))}'
            )
        )

    # Overloads to tell the type system our return type based on doraise val.
    @overload
    def getplayer[PlayerT: bs.Player](
        self, playertype: type[PlayerT], doraise: Literal[False] = False
    ) -> PlayerT | None: ...

    @overload
    def getplayer[PlayerT: bs.Player](
        self, playertype: type[PlayerT], doraise: Literal[True]
    ) -> PlayerT: ...

    def getplayer[PlayerT: bs.Player](
        self, playertype: type[PlayerT], doraise: bool = False
    ) -> PlayerT | None:
        """Get the bascenev1.Player associated with this Spaz.

        By default this will return None if the Player no longer exists.
        If you are logically certain that the Player still exists, pass
        doraise=False to get a non-optional return type.
        """
        player: Any = self.source_player
        assert isinstance(player, playertype)
        if not player.exists() and doraise:
            raise bs.PlayerNotFoundError()
        return player if player.exists() else None
    
    def set_name(self, name: str, color: tuple[float, float, float]):
        """
        Makes a node above the actor with
        some text. Updates it if already exists.
        Args:
            name (str): String of the name
            color (tuple[float, float, float]): Color
        """        
        color_fin = bs.safecolor(color)[:3]
        self.name = name
        final_scale = 0.01
        if not self.node:
            return
        if not self.name_text:
            start_scale = 0.0
            mnode = bs.newnode(
                'math',
                owner=self.node,
                attrs={'input1': (0, 0.5, 0), 'operation': 'add'},
            )
            self.node.connectattr('position', mnode, 'input2')
            self.name_text = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'text': name,
                    'in_world': True,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'color': color_fin,
                    'opacity': 0.9,
                    'scale': final_scale,
                    'h_align': 'center',
                },
            )
            mnode.connectattr('output', self.name_text, 'position')
        else:
            self.name_text.color = color_fin
            assert isinstance(self.name_text.scale, float)
            start_scale = self.name_text.scale
            self.name_text.text = name
        bs.animate(self.name_text, 'scale', {0.0: start_scale, 0.2: final_scale})
    
    def set_hp(self, text: str, color: tuple[float, float, float] = (1, 1, 1)):
        """
        Makes a node above the actor with
        some text. Updates it if already exists.
        Args:
            name (str): String of the name
            color (tuple[float, float, float]): Color
        """        
        color_fin = bs.safecolor(color)[:3]
        final_scale = 0.006
        if not self.node:
            return
        if not self.hp_text:
            start_scale = 0.0
            mnode = bs.newnode(
                'math',
                owner=self.node,
                attrs={'input1': (0, 0.3, 0), 'operation': 'add'},
            )
            self.node.connectattr('position', mnode, 'input2')
            self.hp_text = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'text': text,
                    'in_world': True,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'color': color_fin,
                    'opacity': 0.9,
                    'scale': final_scale,
                    'h_align': 'center',
                },
            )
            mnode.connectattr('output', self.hp_text, 'position')
        else:
            self.hp_text.color = color_fin
            assert isinstance(self.name_text.scale, float)
            start_scale = self.hp_text.scale
            self.hp_text.text = text
        bs.animate(self.hp_text, 'scale', {0.0: start_scale, 0.2: final_scale})
        
    def refresh_earth_meter(self):
        """Does nothing."""
        pass
    def set_cansay(self):
        """Does nothing."""
        pass
    def say(self, wave = False):
        """Does nothing."""
        del wave
        pass
    def gosuper(self, shouldntsetmusic = False):
        """Does nothing."""
        del shouldntsetmusic
        pass

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

    def connect_controls_to_player(self) -> None:
        """
        Wire this ball's movement to the input types
        of the given bascenev1.Player. In short, 
        connect controls to a player.
        """
        player = self.getplayer(bs.Player)
        assert player

        # Reset any currently connected player and/or the player we're
        # wiring up.
        if self._connected_to_player:
            if player != self._connected_to_player:
                player.resetinput()
            self.disconnect_controls_from_player()
        else:
            player.resetinput()
        player.assigninput(bs.InputType.UP_DOWN, self.on_up_down)
        player.assigninput(bs.InputType.LEFT_RIGHT, self.on_left_right)
        player.assigninput(bs.InputType.JUMP_PRESS, self.on_jump)
        player.assigninput(bs.InputType.RUN, self.on_run)
        # We don't need these (our actor is not complex). 
        # Comment just so we can revert if needed.

        # player.assigninput(
        #     bs.InputType.HOLD_POSITION_PRESS, self.on_hold_position_press
        # )
        # player.assigninput(
        #     bs.InputType.HOLD_POSITION_RELEASE,
        #     self.on_hold_position_release,
        # )

        self._connected_to_player = player
       
    def disconnect_controls_from_player(self) -> None:
        """
        Completely sever any previously connected
        bascenev1.Player from control of this spaz.
        """
        if self._connected_to_player:
            self._connected_to_player.resetinput()
            self._connected_to_player = None

            # Send releases for anything in case its held.
            self.on_up_down(0)
            self.on_left_right(0)
            self.on_run(0)
        else:
            print(
                'WARNING: disconnect_controls_from_player() called for'
                ' non-connected player'
            )
    def impulse(
        self, 
        x: float | int = 0, 
        y: float | int = 0, 
        z: float | int = 0, 
        force: float | int = 3.0
    ) -> None: 
        if not self.node:
            return
        self.node.handlemessage(
            'impulse',
            self.node.position[0],
            self.node.position[1],
            self.node.position[2],
            0,
            0,
            0,
            force,
            force,
            0,
            0,
            x,
            y,
            z,
        )
    def dash(self, x: float | int = 0, y: float | int = 0):
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
    
    def _update_move_timer(self):
        if self.move_x == 0 and self.move_z == 0:
            self.move_timer = None
            return

        if self.move_timer is None:
            self.move_timer = bs.Timer(
                0.001,
                self._apply_movement,
                repeat=True
            )

    def on_up_down(self, value: float):
        # UP = -1, DOWN = +1
        self.move_z = -value
        self._update_move_timer()

    def on_left_right(self, value: float):
        # LEFT = -1, RIGHT = +1
        self.move_x = value
        self._update_move_timer()
    
    def on_run(self, value: float):
        if value <= 0:
            self.speed = self.initial_speed / self.multipliernt
        elif value >= 0:
            self.speed = self.initial_speed
    
    def _apply_movement(self):
        if not self.node:
            return

        x = self.move_x
        z = self.move_z

        # Normalize diagonals so they aren't faster
        mag = (x * x + z * z) ** 0.5
        if mag > 1.0:
            x /= mag
            z /= mag

        self.impulse(
            x=x * self.speed,
            z=z * self.speed
        )
    
    def on_jump(self):
        if not self.standing:
            if self.can_thok:
                self.dash(x=250)
                bs.getsound('srb2_thok').play()
                self.can_thok = False
            return
        self.dash(y=150)
        bs.getsound('zoeJump01').play()

    def is_alive(self):
        """Tells us if the ball's still fine."""
        return not self._dead

    def die(self, how: bs.DeathType = bs.DeathType.GENERIC):
        self.handlemessage(bs.DieMessage(how=how))

    def get_death_points(self, how: bs.DeathType) -> tuple[int, int]:
        """Get the points awarded for killing this spaz."""
        del how  # Unused.
        num_hits = float(max(1, self._num_times_hit))

        # Base points is simply 10 for 1-hit-kills and 5 otherwise.
        importance = 2 if num_hits < 2 else 1
        return (10 if num_hits < 2 else 5) * self.points_mult, importance
    
    @override
    def handlemessage(self, msg: Any) -> Any:
        # FIXME: Tidy this up.
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-nested-blocks
        assert not self.expired
        if isinstance(msg, bs.DieMessage): 
            if not self.node or self._dead:
                return None
            # Was this player attacked before death?
            was_attacked_recently = (
                self.last_player_attacked_by
                and bs.time() - self.last_attacked_time < 4.0
            )
            # Leaving the game doesn't count as a kill *unless*
            # someone does it intentionally while being attacked.
            left_game_cleanly = (
                msg.how is bs.DeathType.LEFT_GAME 
                and not was_attacked_recently
            )

            killed = not (msg.immediate or left_game_cleanly)

            activity = self._activity()

            player = self.getplayer(bs.Player, False)
            if not killed:
                killerplayer = None
            else:
                # Otherwise, if they were attacked by someone in the
                # last few seconds, that person is the killer.
                # Otherwise it was a suicide.
                # FIXME: Currently disabling suicides in Co-Op since
                #  all bot kills would register as suicides; need to
                #  change this from last_player_attacked_by to
                #  something like last_actor_attacked_by to fix that.
                if was_attacked_recently:
                    killerplayer = self.last_player_attacked_by
                else:
                    # ok, call it a suicide unless we're in co-op
                    if activity is not None and not isinstance(
                        activity.session, bs.CoopSession
                    ):
                        killerplayer = player
                    else:
                        killerplayer = None

            # We should never wind up with a dead-reference here;
            # we want to use None in that case.
            assert killerplayer is None or killerplayer

            # Only report if both the player and the activity still exist.
            if killed and activity is not None and player:
                activity.handlemessage(
                    bs.PlayerDiedMessage(
                        player, killed, killerplayer, msg.how
                    )
                )
            bs.getsound('playerDeath3').play()
            player = self.getplayer(bs.Player, False)
            self._dead = True
            if msg.immediate:
                    self.node.delete()
                    return True
            else:      
                bs.animate(
                    self.node, 
                    'mesh_scale', 
                    {   
                        # seconds: scale
                        0: 1.0, 
                        0.1: 0
                    }
                )
                bs.timer(0.1, self.node.delete)
                return True

        if isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())

        elif isinstance(msg, bs.HitMessage):
            # Get who last hit us for point rewarding.
            source_player = msg.get_source_player(type(self.source_player))
            if source_player:
                self.last_player_attacked_by = source_player
                self.last_attacked_time = bs.time()
                self.last_attacked_type = (msg.hit_type, msg.hit_subtype)
            activity = self._activity()
            if activity is not None and self.source_player.exists():
                activity.handlemessage(PlayerSpazHurtMessage(self))
            # Impulse.
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
                1,
                msg.force_direction[0],
                msg.force_direction[1],
                msg.force_direction[2],
            )
            # Set damage and HP text.
            damage = (
                msg.flat_damage 
                if msg.flat_damage 
                else msg.magnitude * 3
            )
            self.hitpoints -= damage
            if self.hitpoints <= 0:
                self.die()
            self._num_times_hit += 1
            self.set_hp(
                (
                    f'{str(int(self.hitpoints / 10))}'
                    f'/{str(int(self.max_hitpoints / 10))}'
                )
            )
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
                chunk_type='spark',
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

        elif isinstance(msg, FootingMessage):
            self.standing = msg.footing == 1
            self.can_thok = True

        elif isinstance(msg, CollideMessage):
            node = bs.getcollision().opposingnode
            actor = node.getdelegate(bs.Actor)
            speed = self.getspeed()
            if speed <= 4.5:
                # dont hit when slow
                return
            actor.handlemessage(
                bs.HitMessage(
                    pos=self.node.position,
                    velocity=self.node.velocity,
                    magnitude=speed,
                    velocity_magnitude=speed,
                    radius=0,
                    srcnode=self.node,
                    source_player=self.source_player,
                    force_direction=self.node.velocity,                           
                )
            )
            # sfx
            if speed >= 13:
                bs.getsound('punchSFX/punchDeath1').play()
            if speed >= 9:
                bs.getsound('punchSFX/punchStrong12').play()
            elif speed >= 5:
                bs.getsound('punchSFX/superPunch').play()
            mag = -270.0 * speed
            self.node.handlemessage(
                'kick_back',
                self.node.position[0],
                self.node.position[1],
                self.node.position[2],
                self.node.velocity[0],
                self.node.velocity[1],
                self.node.velocity[2],
                mag,
            )
        else:
            return super().handlemessage(msg)
        return None
    