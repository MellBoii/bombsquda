# Released under the MIT License. See LICENSE for details.
#
"""Implements football games (both co-op and teams varieties)."""

# pylint: disable=too-many-lines

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import math
import random
import logging
from typing import TYPE_CHECKING, override

import bascenev1 as bs

from bascenev1lib.actor.bomb import TNTSpawner, Bomb
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.respawnicon import RespawnIcon
from bascenev1lib.actor.powerupbox import PowerupBoxFactory, PowerupBox
from bascenev1lib.actor.flag import (
    FlagFactory,
    Flag,
    FlagPickedUpMessage,
    FlagDroppedMessage,
    FlagDiedMessage,
)
from bascenev1lib.actor.spazbot import (
    SpazBotDiedMessage,
    SpazBotPunchedMessage,
    SpazBotSet,
    BrawlerBotLite,
    BrawlerBot,
    BomberBotLite,
    BomberBot,
    TriggerBot,
    ChargerBot,
    TriggerBotPro,
    BrawlerBotPro,
    StickyBot,
    ExplodeyBot,
)

if TYPE_CHECKING:
    from typing import Any, Sequence

    from bascenev1lib.actor.spaz import Spaz
    from bascenev1lib.actor.spazbot import SpazBot


class FootballFlag(Flag):
    """Custom flag class for football games."""

    def __init__(self, position: Sequence[float]):
        super().__init__(
            position=position, dropped_timeout=20, color=(1.0, 1.0, 0.3)
        )
        assert self.node
        self.last_holding_player: bs.Player | None = None
        self.node.is_area_of_interest = True
        self.respawn_timer: bs.Timer | None = None
        self.scored = False
        self.held_count = 0
        self.light = bs.newnode(
            'light',
            owner=self.node,
            attrs={
                'intensity': 0.25,
                'height_attenuated': False,
                'radius': 0.2,
                'color': (0.9, 0.7, 0.0),
            },
        )
        self.node.connectattr('position', self.light, 'position')


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.respawn_timer: bs.Timer | None = None
        self.respawn_icon: RespawnIcon | None = None


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0


# ba_meta export bascenev1.GameActivity
class FootballTeamGame2(bs.TeamGameActivity[Player, Team]):
    """Football game for teams mode."""

    name = 'football2name'
    description = 'football2desc'
    available_settings = [
        bs.IntSetting(
            'Score to Win',
            min_value=7,
            default=21,
            increment=7,
        ),
        bs.IntChoiceSetting(
            'Time Limit',
            choices=[
                ('None', 0),
                ('1 Minute', 60),
                ('2 Minutes', 120),
                ('5 Minutes', 300),
                ('10 Minutes', 600),
                ('20 Minutes', 1200),
            ],
            default=0,
        ),
        bs.FloatChoiceSetting(
            'Respawn Times',
            choices=[
                ('Shorter', 0.25),
                ('Short', 0.5),
                ('Normal', 1.0),
                ('Long', 2.0),
                ('Longer', 4.0),
            ],
            default=1.0,
        ),
        bs.BoolSetting('Epic Mode', default=False),
    ]

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        # We only support two-team play.
        return issubclass(sessiontype, bs.DualTeamSession)

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        assert bs.app.classic is not None
        return bs.app.classic.getmaps('football')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._scoreboard: Scoreboard | None = Scoreboard()

        # Load some media we need.
        self._cheer_sound = bs.getsound('cheer')
        self._chant_sound = bs.getsound('crowdChant')
        self._score_sound = bs.getsound('score')
        self._swipsound = bs.getsound('swip')
        self._whistle_sound = bs.getsound('deek2')
        self._score_region_material = bs.Material()
        self._score_region_material.add_actions(
            conditions=('they_have_material', FlagFactory.get().flagmaterial),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect', self._handle_score),
            ),
        )
        self._flag_spawn_pos: Sequence[float] | None = None
        self._score_regions: list[bs.NodeActor] = []
        self._flag: FootballFlag | None = None
        self._flag_respawn_timer: bs.Timer | None = None
        self._flag_respawn_light: bs.NodeActor | None = None
        self._score_to_win = int(settings['Score to Win'])
        self._time_limit = float(settings['Time Limit'])
        self._epic_mode = bool(settings['Epic Mode'])
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.SPORTS
        )

    @override
    def get_instance_description(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        touchdowns = self._score_to_win / 7

        # NOTE: if use just touchdowns = self._score_to_win // 7
        # and we will need to score, for example, 27 points,
        # we will be required to score 3 (not 4) goals ..
        touchdowns = math.ceil(touchdowns)
        if touchdowns > 1:
            return 'Score ${ARG1} touchdowns.', touchdowns
        return 'Score a touchdown.'

    @override
    def get_instance_description_short(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        touchdowns = self._score_to_win / 7
        touchdowns = math.ceil(touchdowns)
        if touchdowns > 1:
            return 'score ${ARG1} touchdowns', touchdowns
        return 'score a touchdown'

    @override
    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops()
        self._flag_spawn_pos = self.map.get_flag_position(None)
        self._spawn_flag()
        defs = self.map.defs
        self._score_regions.append(
            bs.NodeActor(
                bs.newnode(
                    'region',
                    attrs={
                        'position': defs.boxes['goal1'][0:3],
                        'scale': defs.boxes['goal1'][6:9],
                        'type': 'box',
                        'materials': (self._score_region_material,),
                    },
                )
            )
        )
        self._score_regions.append(
            bs.NodeActor(
                bs.newnode(
                    'region',
                    attrs={
                        'position': defs.boxes['goal2'][0:3],
                        'scale': defs.boxes['goal2'][6:9],
                        'type': 'box',
                        'materials': (self._score_region_material,),
                    },
                )
            )
        )
        self._update_scoreboard()
        self._chant_sound.play()

    @override
    def on_team_join(self, team: Team) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        self._update_scoreboard()

    def _kill_flag(self) -> None:
        self._flag = None

    def _handle_score(self) -> None:
        """A point has been scored."""
        assert self._flag is not None
        if self._flag.scored:
            return
        region = bs.getcollision().sourcenode
        i = None
        for i, score_region in enumerate(self._score_regions):
            if region == score_region.node:
                break
        for team in self.teams:
            if team.id == i:
                team.score += 7
                self._flag.scored = True
                # if we have a flag, EXPLODE IT!!!!
                if self._flag and self._flag.node:
                    Bomb(position=self._flag.node.position, bomb_type='normal').explode()
                for player in team.players:
                    if player.actor:
                        player.actor.handlemessage(bs.CelebrateMessage(2.0))
                if self._flag.last_holding_player and team == self._flag.last_holding_player.team:
                    self.stats.player_scored(
                        self._flag.last_holding_player, 50, big_message=True
                    )
                if team.score >= self._score_to_win:
                    # if theres players on the other team, EXPLODE THEM TOOOO!!!!!
                    for other_team in self.teams:
                        if other_team is not team:
                            for other_player in other_team.players:
                                if other_player.actor and other_player.actor.is_alive():
                                    Bomb(
                                        position=other_player.actor.node.position, 
                                        bomb_type='tnt'
                                    ).explode()
                    self.end_game()
        self._score_sound.play()
        self._cheer_sound.play()
        bs.timer(1.5, self._kill_flag)
        light = bs.newnode(
            'light',
            attrs={
                'position': bs.getcollision().position,
                'height_attenuated': False,
                'color': (1, 0, 0),
            },
        )
        bs.animate(light, 'intensity', {0.0: 0, 0.5: 1, 1.0: 0}, loop=True)
        bs.timer(1.5, light.delete)
        bs.cameraflash(duration=10.0)
        self._update_scoreboard()
    def end_game(self) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results, announce_delay=0.8)

    def _update_scoreboard(self) -> None:
        assert self._scoreboard is not None
        for team in self.teams:
            self._scoreboard.set_team_value(
                team, team.score, self._score_to_win
            )

    @override
    def handlemessage(self, msg: Any) -> Any:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        if isinstance(msg, FlagPickedUpMessage):
            assert isinstance(msg.flag, FootballFlag)
            try:
                msg.flag.last_holding_player = msg.node.getdelegate(
                    PlayerSpaz, True
                ).getplayer(Player, True)
            except bs.NotFoundError:
                pass
            msg.flag.held_count += 1

        elif isinstance(msg, FlagDroppedMessage):
            assert isinstance(msg.flag, FootballFlag)
            msg.flag.held_count -= 1

        # Respawn dead players if they're still in the game.
        elif isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            self.respawn_player(msg.getplayer(Player))

        # Respawn dead flags.
        elif isinstance(msg, FlagDiedMessage):
            if not self.has_ended():
                if msg.self_kill:
                    self._spawn_flag()
                else:
                    self._flag_respawn_timer = bs.Timer(3.0, self._spawn_flag)
                self._flag_respawn_light = bs.NodeActor(
                    bs.newnode(
                        'light',
                        attrs={
                            'position': self._flag_spawn_pos,
                            'height_attenuated': False,
                            'radius': 0.15,
                            'color': (1.0, 1.0, 0.3),
                        },
                    )
                )
                assert self._flag_respawn_light.node
                bs.animate(
                    self._flag_respawn_light.node,
                    'intensity',
                    {0.0: 0, 0.25: 0.15, 0.5: 0},
                    loop=True,
                )
                bs.timer(3.0, self._flag_respawn_light.node.delete)

        else:
            # Augment standard behavior.
            super().handlemessage(msg)

    def _flash_flag_spawn(self) -> None:
        light = bs.newnode(
            'light',
            attrs={
                'position': self._flag_spawn_pos,
                'height_attenuated': False,
                'color': (1, 1, 0),
            },
        )
        bs.animate(light, 'intensity', {0: 0, 0.25: 0.25, 0.5: 0}, loop=True)
        bs.timer(1.0, light.delete)

    def _spawn_flag(self) -> None:
        self._swipsound.play()
        self._whistle_sound.play()
        self._flash_flag_spawn()
        assert self._flag_spawn_pos is not None
        self._flag = FootballFlag(position=self._flag_spawn_pos)