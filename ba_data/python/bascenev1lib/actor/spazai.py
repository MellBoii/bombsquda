from __future__ import annotations

import random
import weakref
import logging
from typing import TYPE_CHECKING, overload, override

import bascenev1 as bs
from bascenev1._coopsession import CoopSession
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.spaz import Spaz
from bascenev1lib.actor.spazbot import SpazBot
from bascenev1lib.actor.bomb import Bomb
from bascenev1._gameactivity import EmeraldActor

if TYPE_CHECKING:
    from typing import Any, Sequence, Callable, Literal
    from bascenev1lib.actor.flag import Flag

class AIPlayer(bs.Player):
    @override
    def __init__(self):
        sessionplayer = bs.SessionPlayer(None)
        super().__init__()
        self._sessionplayer = sessionplayer

    @override
    def postinit(self, sessionplayer: Any) -> None:
        super().postinit(sessionplayer=self._sessionplayer)


class SpazAI(Spaz):
    """
    A dumber AI version of Spaz.
    The point is not to create a bot version
    separate from spaz, rather a regular spaz
    that is controlled by conditions (like SpazBot).
    """

    character = 'Spaz'
    punchiness = 0.5
    throwiness = 0.7
    static = False
    bouncy = False
    run = False
    charge_dist_min = 0.0  # When we can start a new charge.
    charge_dist_max = 2.0  # When we can start a new charge.
    run_dist_min = 0.0  # How close we can be to continue running.
    charge_speed_min = 0.4
    charge_speed_max = 1.0
    throw_dist_min = 5.0
    throw_dist_max = 9.0
    throw_rate = 1.0
    default_bomb_type = 'normal'
    default_bomb_count = 1
    namelist = [
        'Spazzy',
        'SpazBot',
        'gamer',
        'spazito',
        'Device',
        'Boomer',
        'Android589316',
        'ultra caballero',
        'spaz killer',
        'i have\nline breaks!!',
    ]

    def __init__(self) -> None:
        """Instantiate a spaz-bot."""
        self.name = random.choice(self.namelist)
        self.color = (random.random(), random.random(), random.random())
        self.highlight = (random.random(), random.random(), random.random())
        super().__init__(
            color=self.color,
            highlight=self.highlight,
            character=self.character,
            name=self.name,
            source_player=None,
            start_invincible=False,
            can_accept_powerups=True,
        )
        self._player_pts = []
        self.node.name_color = self.color
        self.update_callback: Callable[[SpazBot], Any] | None = None
        activity = self.activity
        assert isinstance(activity, bs.GameActivity)
        self.coopmode: bool = isinstance(activity.session, CoopSession)
        self._map = weakref.ref(activity.map)
        self.last_player_attacked_by: bs.Player | None = None
        self.last_attacked_time = 0.0
        self.last_attacked_type: tuple[str, str] | None = None
        self.target_point_default: bs.Vec3 | None = None
        self.held_count = 0
        self.last_player_held_by: bs.Player | None = None
        self.target_flag: Flag | None = None
        self._charge_speed = 0.5 * (
            self.charge_speed_min + self.charge_speed_max
        )
        self.emerald_chase_time = 0
        self._lead_amount = 0.5
        self._mode = 'wait'
        self._charge_closing_in = False
        self._last_charge_dist = 0.0
        self._running = False
        self._last_jump_time = 0.0

        self._throw_release_time: float | None = None
        self._have_dropped_throw_bomb: bool | None = None
        self._player_pts: list[tuple[bs.Vec3, bs.Vec3]] | None = None

        # These cooldowns didn't exist when these bots were calibrated,
        # so take them out of the equation.
        self._jump_cooldown = 0
        self._pickup_cooldown = 0
        self._fly_cooldown = 0
        self._bomb_cooldown = 0
        self.source_player = AIPlayer()
        self.source_player.actor = self
        self.activity.players.append(self.source_player)
        self.updateTimer = bs.Timer(0.05, self.update, repeat=True)
    
    @property
    def map(self) -> bs.Map:
        """The map this bot was created on."""
        mval = self._map()
        assert mval is not None
        return mval

    def _get_nearest_emerald(self):
        nearest = None
        nearest_dist = 9999.0
        nearest_type = None
        our_pos = bs.Vec3(self.node.position[0], 0, self.node.position[2])

        for node in bs.getnodes():
            actor = node.getdelegate(EmeraldActor)

            if not actor:
                continue  # Not an emerald actor

            if not node.exists():
                continue

            pos = bs.Vec3(node.position[0], 0, node.position[2])
            dist = (pos - our_pos).length()

            if dist < nearest_dist:
                nearest_dist = dist
                nearest = actor

        return nearest, nearest_dist

    def set_player_points(self, pts: list[tuple[bs.Vec3, bs.Vec3]]) -> None:
        """Provide the spaz-bot with the locations of its enemies."""
        self._player_pts = pts
    
    def update(self):
        if not self.node:
            return
        # Update our list of player points for the bots to use.
        player_pts = []
        nearest = None
        nearest_dist = 9999.0
        botsorplayers = 'bots' if self.coopmode else 'players'

        for snode in bs.getnodes():
            spaz = snode.getdelegate(Spaz)
            if not spaz or spaz is self or spaz._dead:
                continue
            # Exclude players from the list if we're in coop
            if (
                botsorplayers == 'bots' and 
                spaz.source_player != None
                or isinstance(spaz, SpazAI)
            ):
                continue

            player_pts.append(
                (
                    bs.Vec3(spaz.node.position),
                    bs.Vec3(spaz.node.velocity),
                )
            )

        self._player_pts = player_pts
        self.update_ai()
    
    def _get_target_player_pt(self) -> tuple[bs.Vec3 | None, bs.Vec3 | None]:
        """Returns the position and velocity of our target.

        Both values will be None in the case of no target.
        """
        assert self.node
        botpt = bs.Vec3(self.node.position)
        closest_dist: float | None = None
        closest_vel: bs.Vec3 | None = None
        closest: bs.Vec3 | None = None
        assert self._player_pts is not None
        for plpt, plvel in self._player_pts:
            dist = (plpt - botpt).length()

            # Ignore player-points that are significantly below the bot
            # (keeps bots from following players off cliffs).
            if (closest_dist is None or dist < closest_dist) and (
                plpt[1] > botpt[1] - 5.0
            ):
                closest_dist = dist
                closest_vel = plvel
                closest = plpt
        if closest_dist is not None:
            assert closest_vel is not None
            assert closest is not None
            return (
                bs.Vec3(closest[0], closest[1], closest[2]),
                bs.Vec3(closest_vel[0], closest_vel[1], closest_vel[2]),
            )
        return None, None

    def update_ai(self) -> None:
        """Should be called periodically to update the spaz' AI."""
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        if not self.node:
            return

        pos = self.node.position
        our_pos = bs.Vec3(pos[0], 0, pos[2])
        can_attack = True
        force_target = False
        target_is_emerald = False
        we_chase_emeralds = True

        target_pt_raw: bs.Vec3 | None
        target_vel: bs.Vec3 | None
        # don't gaf if we're super already. >B)
        if self.issuper:
            we_chase_emeralds = False
        # handle if we've taken too much to
        # grab a emerald
        if self.emerald_chase_time > 4.0:
            self.emerald_chase_time = 0
        elif self.emerald_chase_time > 1.0:
            we_chase_emeralds = False
            self.emerald_chase_time += 0.1
        if we_chase_emeralds:
            # save coords
            emerald, edist = self._get_nearest_emerald()
            if emerald != None:
                if emerald.texname in self.emeralds:
                    emerald = None
            # no one? let's chase that emerald!
            if emerald and edist < 4.3:
                target_pt_raw = bs.Vec3(*emerald.node.position)
                target_vel = bs.Vec3(0, 0, 0)
                can_attack = False
                force_target = True
                target_is_emerald = True
                self.node.run = 1.0
                self.emerald_chase_time += 0.1
                if self.node.hold_node:
                    self.node.pickup_pressed = True
                    self.node.pickup_pressed = False
            else:
                self.emerald_chase_time = 0
            
        # If we're a flag-bearer, we're pretty simple-minded - just walk
        # towards the flag and try to pick it up.
        if self.target_flag:
            if self.node.hold_node:
                holding_flag = self.node.hold_node.getnodetype() == 'flag'
            else:
                holding_flag = False

            # If we're holding the flag, just walk left.
            if holding_flag:
                # Just walk left.
                self.node.move_left_right = -1.0
                self.node.move_up_down = 0.0

            # Otherwise try to go pick it up.
            elif self.target_flag.node:
                target_pt_raw = bs.Vec3(*self.target_flag.node.position)
                diff = target_pt_raw - our_pos
                diff = bs.Vec3(diff[0], 0, diff[2])  # Don't care about y.
                dist = diff.length()
                to_target = diff.normalized()

                # If we're holding some non-flag item, drop it.
                if self.node.hold_node:
                    self.node.pickup_pressed = True
                    self.node.pickup_pressed = False
                    return

                # If we're a runner, run only when not super-near the flag.
                if self.run and dist > 3.0:
                    self._running = True
                    self.node.run = 1.0
                else:
                    self._running = False
                    self.node.run = 0.0

                self.node.move_left_right = to_target.x
                self.node.move_up_down = -to_target.z
                if dist < 1.25:
                    self.node.pickup_pressed = True
                    self.node.pickup_pressed = False
            return

        # Not a flag-bearer. If we're holding anything but a bomb, drop it.
        if self.node.hold_node:
            holding_bomb = self.node.hold_node.getnodetype() in ['bomb', 'prop']
            if not holding_bomb:
                self.node.pickup_pressed = True
                self.node.pickup_pressed = False
                return

        if not force_target:
            target_pt_raw, target_vel = self._get_target_player_pt()

        if target_pt_raw is None:
            # Use default target if we've got one.
            if self.target_point_default is not None:
                target_pt_raw = self.target_point_default
                target_vel = bs.Vec3(0, 0, 0)
                can_attack = False

            # With no target, we stop moving and drop whatever we're holding.
            else:
                self.node.move_left_right = 0
                self.node.move_up_down = 0
                if self.node.hold_node:
                    self.node.pickup_pressed = True
                    self.node.pickup_pressed = False
                return

        # We don't want height to come into play.
        target_pt_raw[1] = 0.0
        assert target_vel is not None
        target_vel[1] = 0.0

        dist_raw = (target_pt_raw - our_pos).length()

        # Use a point out in front of them as real target.
        # (more out in front the farther from us they are)
        target_pt = (
            target_pt_raw + target_vel * dist_raw * 0.3 * self._lead_amount
        )

        diff = target_pt - our_pos
        dist = diff.length()
        to_target = diff.normalized()
        # oh, we have all the emeralds.
        # even tho its rare to achieve them, we will go super >:3
        if len(self.emeralds) >= 7:
            self.on_jump_press()
            bs.timer(0.1, self.on_jump_release)
            bs.timer(0.3, self.on_pickup_press)
            bs.timer(0.4, self.on_pickup_release)
        if self._mode == 'throw':
            # We can only throw if alive and well.
            if not self._dead and not self.node.knockout:
                assert self._throw_release_time is not None
                time_till_throw = self._throw_release_time - bs.time()

                if not self.node.hold_node:
                    # If we haven't thrown yet, whip out the bomb.
                    if not self._have_dropped_throw_bomb:
                        self.drop_bomb()
                        self._have_dropped_throw_bomb = True

                    # Otherwise our lack of held node means we successfully
                    # released our bomb; lets retreat now.
                    else:
                        self._mode = 'flee'

                # Oh crap, we're holding a bomb; better throw it.
                elif time_till_throw <= 0.0:
                    # Jump and throw.
                    def _safe_pickup(node: bs.Node) -> None:
                        if node and self.node:
                            self.node.pickup_pressed = True
                            self.node.pickup_pressed = False

                    if dist > 5.0:
                        self.node.jump_pressed = True
                        self.node.jump_pressed = False

                        # Throws:
                        bs.timer(0.1, bs.Call(_safe_pickup, self.node))
                    else:
                        # Throws:
                        bs.timer(0.1, bs.Call(_safe_pickup, self.node))

                if self.static:
                    if time_till_throw < 0.3:
                        speed = 1.0
                    elif time_till_throw < 0.7 and dist > 3.0:
                        speed = -1.0  # Whiplash for long throws.
                    else:
                        speed = 0.02
                else:
                    if time_till_throw < 0.7:
                        # Right before throw charge full speed towards target.
                        speed = 1.0
                    else:
                        # Earlier we can hold or move backward for a whiplash.
                        speed = 0.0125
                self.node.move_left_right = to_target.x * speed
                self.node.move_up_down = to_target.z * -1.0 * speed

        elif self._mode == 'charge':
            if random.random() < 0.3:
                self._charge_speed = random.uniform(
                    self.charge_speed_min, self.charge_speed_max
                )

                # If we're a runner we run during charges *except when near
                # an edge (otherwise we tend to fly off easily).
                if self.run and dist_raw > self.run_dist_min:
                    self._lead_amount = 0.3
                    self._running = True
                    self.node.run = 1.0
                else:
                    self._lead_amount = 0.01
                    self._running = False
                    self.node.run = 0.0

            self.node.move_left_right = to_target.x * self._charge_speed
            self.node.move_up_down = to_target.z * -1.0 * self._charge_speed

        elif self._mode == 'wait':
            # Every now and then, aim towards our target.
            # Other than that, just stand there.
            if int(bs.time() * 1000.0) % 1234 < 100:
                self.node.move_left_right = to_target.x * (400.0 / 33000)
                self.node.move_up_down = to_target.z * (-400.0 / 33000)
            else:
                self.node.move_left_right = 0
                self.node.move_up_down = 0

        elif self._mode == 'flee':
            # Even if we're a runner, only run till we get away from our
            # target (if we keep running we tend to run off edges).
            if self.run and dist < 3.0:
                self._running = True
                self.node.run = 1.0
            else:
                self._running = False
                self.node.run = 0.0
            self.node.move_left_right = to_target.x * -1.0
            self.node.move_up_down = to_target.z

        # We might wanna switch states unless we're doing a throw
        # (in which case that's our sole concern).
        if self._mode != 'throw':
            # If we're currently charging, keep track of how far we are
            # from our target. When this value increases it means our charge
            # is over (ran by them or something).
            if self._mode == 'charge':
                if (
                    self._charge_closing_in
                    and self._last_charge_dist < dist < 3.0
                ):
                    self._charge_closing_in = False
                self._last_charge_dist = dist

            # make some  room im boutta shoot this idiot >:3
            if (
                self.throw_dist_min <= dist < self.throw_dist_max
                and random.random() < self.throwiness
                and can_attack
            ):
                self._mode = 'throw'
                self._lead_amount = (
                    (0.4 + random.random() * 0.6)
                    if dist_raw > 4.0
                    else (0.1 + random.random() * 0.4)
                )
                self._have_dropped_throw_bomb = False
                self._throw_release_time = bs.time() + (
                    1.0 / self.throw_rate
                ) * (0.8 + 1.3 * random.random())

            # always wait when static
            elif self.static:
                self._mode = 'wait'

            # too close and not charging? run away :(
            elif (
                dist < self.charge_dist_min
                and not self._charge_closing_in
                and not target_is_emerald
            ):
                # unless, well... we're near a edge. we can't really run away.
                if self.map.is_point_near_edge(our_pos, self._running):
                    if self._mode != 'charge':
                        self._mode = 'charge'
                        self._lead_amount = 0.2
                        self._charge_closing_in = True
                        self._last_charge_dist = dist
                else:
                    self._mode = 'flee'

            # we're close enough to charge and
            # backed up against a cliff or too far to
            # throw... charge!!!! >:o
            elif (
                dist < self.charge_dist_max
                or dist > self.throw_dist_max
                or self.map.is_point_near_edge(our_pos, self._running)
            ):
                if self._mode != 'charge':
                    self._mode = 'charge'
                    self._lead_amount = 0.01
                    self._charge_closing_in = True
                    self._last_charge_dist = dist

            # well dang! we're too close to throw but too far
            # to charge, so we just run away or standby
            elif dist < self.throw_dist_min and not target_is_emerald:
                # Charge if either we're within charge range or
                # cant retreat to throw.
                self._mode = 'flee'

            # do some real cool jumps if we runnin :D
            # FIXME: pylint: disable=too-many-boolean-expressions
            # love some fixmes hahahaha
            if (
                self._running
                and 1.2 < dist < 2.2
                and bs.time() - self._last_jump_time > 1.0
            ) or (
                self.bouncy
                and bs.time() - self._last_jump_time > 0.4
                and random.random() < 0.5
            ):
                self._last_jump_time = bs.time()
                self.node.jump_pressed = True
                self.node.jump_pressed = False

            # start punching if close!!!
            if dist < (1.6 if self._running else 1.2) and can_attack:
                if random.random() < self.punchiness:
                    self.on_punch_press()
                    self.on_punch_release()
                # parry dem bitches if we can >:/
                if self.canparry:
                    if random.random() < 0.5:
                        self.on_pickup_press()
                        self.on_pickup_release()