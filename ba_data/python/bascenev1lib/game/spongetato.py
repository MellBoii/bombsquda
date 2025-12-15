# Released under the MIT License. See LICENSE for details.
#
"""Hot potato-ish gamemode that uses the Spongebob powerup mechanic."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING, override

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


# ba_meta export bascenev1.GameActivity
class SpongetatoGame(bs.TeamGameActivity[Player, Team]):
    """A last-standing gametype based on Hot Potato."""

    name = 'Hot Spongetato'
    description = 'Be the last one sponged to win.'
    scoreconfig = bs.ScoreConfig(
        label='Survived', scoretype=bs.ScoreType.SECONDS, none_is_winner=True
    )
    allow_mid_activity_joins = False
    announce_player_deaths = True

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.FreeForAllSession)

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        assert bs.app.classic is not None
        return bs.app.classic.getmaps('melee')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._score_to_win: int | None = None
        # For now, keep it false. We ain't
        # doing slow mode for now
        self._epic_mode = False
        # Base class overrides.
        self.slow_motion = self._epic_mode
        if self._epic_mode:
            self.default_music = bs.MusicType.EPIC
        else:
            music_choices = [
                bs.MusicType.MODULATINGTIME,
                bs.MusicType.GAMBLING
            ]
            random.seed(time.time())
            self.default_music = random.choice(music_choices)
            
    def _get_living_teams(self) -> list[Team]:
        # Get any team that's alive.
        return [
            team
            for team in self.teams
            if any(
                player.is_alive()
                for player in team.players
            )
        ]
            
    def trigger_potato(self, player: Player) -> None:
        player.actor._activate_spongebob()
        
    @override
    def on_begin(self) -> None:
        super().on_begin()
        # Track the time we've started, and
        # hand out the hot potato to someone
        self._start_time = bs.time()
        self._update()
        
    def _update(self) -> None:
        # If we're down to 1 or fewer living teams, start a timer to end
        # the game (allows the dust to settle and draws to occur if deaths
        # are close enough).
        if len(self._get_living_teams()) < 2:
            self._round_end_timer = bs.Timer(1.0, self.end_game)
        # Otherwise, give someone the hot potato.
        else:
            bs.timer(1.0, lambda: self.trigger_potato(
                player=random.choice(random.choice(
                            self._get_living_teams()
                        ).players
                    )
                )
            )
            
    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        """Spawn a player (override)."""
        actor = self.spawn_player_spaz(player)
        # Veeerry low impact scale
        # so we don't die frequently.
        actor.impact_scale = 0.01
        actor.play_big_death_sound = True
        return actor
        
    @override
    def handlemessage(self, msg: Any) -> Any:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)

            player = msg.getplayer(Player)
            # If a player awkwardly dies without
            # having a hot potato, just respawn em'.
            if player.actor._has_hot_potato != True:
                self.respawn_player(player)
            # Otherwise, hand out another potato
            # to others.
            else:
                # Update.
                bs.timer(0.1, self._update)
                # Save the player's survival seconds.
                player.team.survival_seconds = int(
                    bs.time() - self._start_time
                )
            
    @override
    def end_game(self) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        # end em!!
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.survival_seconds)
        self.end(results=results)
