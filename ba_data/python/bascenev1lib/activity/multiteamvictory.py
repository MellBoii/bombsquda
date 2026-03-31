# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to the final screen in multi-teams sessions."""

from __future__ import annotations

from typing import override, TYPE_CHECKING

import bascenev1 as bs
import random
from bascenev1lib.actor.bomb import Bomb
from bascenev1lib.actor.nodejumper import ImageJumper

from bascenev1lib.activity.multiteamscore import MultiTeamScoreScreenActivity

if TYPE_CHECKING:
    from typing import Any


class TeamSeriesVictoryScoreScreenActivity(MultiTeamScoreScreenActivity):
    """Final score screen for a team series."""

    # Don't play music by default; (we do manually after a delay).
    default_music = None

    def __init__(self, settings: dict):
        super().__init__(settings=settings)
        self._min_view_time = 10.0
        self._is_ffa = isinstance(self.session, bs.FreeForAllSession)
        self._allow_server_transition = True
        self._tips_text = None
        self._default_show_tips = False
        self._ffa_top_player_info: list[Any] | None = None
        self._ffa_top_player_rec: bs.PlayerRecord | None = None
        self.bomb_timer = None
    
    def _drop_bomb_cluster(self) -> None:
        # Random note: code like this is a handy way to plot out extents
        # and debug things.
        loc_test = False
        if loc_test:
            bs.newnode('locator', attrs={'position': (8, 6, -5.5)})
            bs.newnode('locator', attrs={'position': (8, 6, -2.3)})
            bs.newnode('locator', attrs={'position': (-7.3, 6, -5.5)})
            bs.newnode('locator', attrs={'position': (-7.3, 6, -2.3)})

        # Drop several bombs in series.
        delay = 0.0
        for _i in range(random.randrange(1, 3)):
            # Drop them somewhere within our bounds with velocity pointing
            # toward the opposite side.
            pos = (
                -7.3 + 15.3 * random.random(),
                11,
                random.randint(-9, 6),
            )
            dropdir = -1.0 if pos[0] > 0 else 1.0
            vel = (
                (-5.0 + random.random() * 30.0) * dropdir,
                random.uniform(-3.066, -4.12),
                random.randint(-4, 3),
            )
            self._drop_bomb(pos, vel)

    def _drop_bomb(
        self, position: Sequence[float], velocity: Sequence[float]
    ) -> None:
        Bomb(position=position, velocity=velocity, nosound=True).autoretain()
    
    def start_bombs(self):
        self.bomb_timer = bs.Timer(
            0.1, 
            self._drop_bomb_cluster, 
            repeat=True
        )

    @override
    def on_begin(self) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        from bascenev1lib.actor.text import Text
        from bascenev1lib.actor.image import Image

        bs.set_analytics_screen(
            'FreeForAll Series Victory Screen'
            if self._is_ffa
            else 'Teams Series Victory Screen'
        )
        assert bs.app.classic is not None
        self._show_up_next = False
        self._custom_continue_message = ''
        super().on_begin()
        winning_sessionteam = self.settings_raw['winner']

        # Pause a moment before playing victory music.
        bs.timer(0.4, bs.WeakCall(self._play_victory_music))
        bs.timer(
            4.3, bs.WeakCall(self._show_winner, self.settings_raw['winner'])
        )
        bs.timer(4.3, self._score_display_sound.play)
        bs.timer(4.3, lambda: bs.getsound('achievement').play())
        bs.timer(4.3, lambda: bs.getsound('cheer2').play())
        bs.timer(4.3, self.start_bombs)
        bs.timer(38.0, lambda: bs.setmusic(bs.MusicType.SCORES))

        # Score / Name / Player-record.
        player_entries: list[tuple[int, str, bs.PlayerRecord]] = []

        # Note: for ffa, exclude players who haven't entered the game yet.
        if self._is_ffa:
            for _pkey, prec in self.stats.get_records().items():
                if prec.player.in_game:
                    player_entries.append(
                        (
                            prec.player.sessionteam.customdata['score'],
                            prec.getname(full=True),
                            prec,
                        )
                    )
            player_entries.sort(reverse=True, key=lambda x: x[0])
            if len(player_entries) > 0:
                # Store some info for the top ffa player so we can
                # show winner info even if they leave.
                self._ffa_top_player_info = list(player_entries[0])
                self._ffa_top_player_info[1] = self._ffa_top_player_info[
                    2
                ].getname()
                self._ffa_top_player_info[2] = self._ffa_top_player_info[
                    2
                ].get_icon()
        else:
            for _pkey, prec in self.stats.get_records().items():
                player_entries.append((prec.score, prec.name_full, prec))
            player_entries.sort(reverse=True, key=lambda x: x[0])

        ts_height = 300.0
        ts_h_offs = -390.0
        tval = 6.4
        t_incr = 0.12

        always_use_first_to = bs.app.lang.get_resource(
            'bestOfUseFirstToInstead'
        )

        session = self.session
        if self._is_ffa:
            assert isinstance(session, bs.FreeForAllSession)
            txt = bs.Lstr(
                value='${A}:',
                subs=[
                    (
                        '${A}',
                        bs.Lstr(
                            resource='firstToFinalText',
                            subs=[
                                (
                                    '${COUNT}',
                                    str(session.get_ffa_series_length()),
                                )
                            ],
                        ),
                    )
                ],
            )
        else:
            assert isinstance(session, bs.MultiTeamSession)

            # Some languages may prefer to always show 'first to X' instead of
            # 'best of X'.
            # FIXME: This will affect all clients connected to us even if
            #  they're not using this language. Should try to come up
            #  with a wording that works everywhere.
            if always_use_first_to:
                txt = bs.Lstr(
                    value='${A}:',
                    subs=[
                        (
                            '${A}',
                            bs.Lstr(
                                resource='firstToFinalText',
                                subs=[
                                    (
                                        '${COUNT}',
                                        str(
                                            session.get_series_length() / 2 + 1
                                        ),
                                    )
                                ],
                            ),
                        )
                    ],
                )
            else:
                txt = bs.Lstr(
                    value='${A}:',
                    subs=[
                        (
                            '${A}',
                            bs.Lstr(
                                resource='bestOfFinalText',
                                subs=[
                                    (
                                        '${COUNT}',
                                        str(session.get_series_length()),
                                    )
                                ],
                            ),
                        )
                    ],
                )

        Text(
            txt,
            v_align=Text.VAlign.CENTER,
            maxwidth=300,
            color=(0.5, 0.5, 0.5, 1.0),
            position=(0, 310),
            scale=1.2,
            transition=Text.Transition.IN_TOP_SLOW,
            h_align=Text.HAlign.CENTER,
            transition_delay=t_incr * 4,
        ).autoretain()

        win_score = (session.get_series_length() - 1) // 2 + 1
        lose_score = 0
        for team in self.teams:
            if team.sessionteam.customdata['score'] != win_score:
                lose_score = team.sessionteam.customdata['score']

        if not self._is_ffa:
            Text(
                bs.Lstr(
                    resource='gamesToText',
                    subs=[
                        ('${WINCOUNT}', str(win_score)),
                        ('${LOSECOUNT}', str(lose_score)),
                    ],
                ),
                color=(0.5, 0.5, 0.5, 1.0),
                maxwidth=160,
                v_align=Text.VAlign.CENTER,
                position=(0, -215),
                scale=1.8,
                transition=Text.Transition.IN_LEFT,
                h_align=Text.HAlign.CENTER,
                transition_delay=4.8 + t_incr * 4,
            ).autoretain()

        if self._is_ffa:
            v_extra = 120
        else:
            v_extra = 0

        mvp: bs.PlayerRecord | None = None
        mvp_name: str | None = None

        # Show game MVP.
        if not self._is_ffa:
            mvp, mvp_name = None, None
            for entry in player_entries:
                if entry[2].team == winning_sessionteam:
                    mvp = entry[2]
                    mvp_name = entry[1]
                    break
            if mvp is not None:
                Text(
                    bs.Lstr(resource='mostValuablePlayerText'),
                    color=(0.5, 0.5, 0.5, 1.0),
                    v_align=Text.VAlign.CENTER,
                    maxwidth=300,
                    position=(180, ts_height / 2 + 15),
                    transition=Text.Transition.IN_LEFT,
                    h_align=Text.HAlign.LEFT,
                    transition_delay=tval,
                ).autoretain()
                tval += 4 * t_incr

                Image(
                    mvp.get_icon(),
                    position=(230, ts_height / 2 - 55 + 14 - 5),
                    scale=(70, 70),
                    transition=Image.Transition.IN_LEFT,
                    transition_delay=tval,
                ).autoretain()
                assert mvp_name is not None
                Text(
                    bs.Lstr(value=mvp_name),
                    position=(280, ts_height / 2 - 55 + 15 - 5),
                    h_align=Text.HAlign.LEFT,
                    v_align=Text.VAlign.CENTER,
                    maxwidth=170,
                    scale=1.3,
                    color=bs.safecolor(mvp.team.color + (1,)),
                    transition=Text.Transition.IN_LEFT,
                    transition_delay=tval,
                ).autoretain()
                tval += 4 * t_incr
        xoffs = 0
        if self._is_ffa:
            xoffs = 150
        # Most violent.
        most_kills = 0
        for entry in player_entries:
            if entry[2].kill_count >= most_kills:
                mvp = entry[2]
                mvp_name = entry[1]
                most_kills = entry[2].kill_count
        if mvp is not None:
            Text(
                bs.Lstr(resource='mostViolentPlayerText'),
                color=(0.5, 0.5, 0.5, 1.0),
                v_align=Text.VAlign.CENTER,
                maxwidth=300,
                position=(180 + xoffs, ts_height / 2 - 150 + v_extra + 15),
                transition=Text.Transition.IN_LEFT,
                h_align=Text.HAlign.LEFT,
                transition_delay=tval,
            ).autoretain()
            Text(
                bs.Lstr(
                    value='(${A})',
                    subs=[
                        (
                            '${A}',
                            bs.Lstr(
                                resource='killsTallyText',
                                subs=[('${COUNT}', str(most_kills))],
                            ),
                        )
                    ],
                ),
                position=(260 + xoffs, ts_height / 2 - 150 - 15 + v_extra),
                color=(0.3, 0.3, 0.3, 1.0),
                scale=0.6,
                h_align=Text.HAlign.LEFT,
                transition=Text.Transition.IN_LEFT,
                transition_delay=tval,
            ).autoretain()
            tval += 4 * t_incr

            Image(
                mvp.get_icon(),
                position=(233 + xoffs, ts_height / 2 - 150 - 30 - 46 + 25 + v_extra),
                scale=(50, 50),
                transition=Image.Transition.IN_LEFT,
                transition_delay=tval,
            ).autoretain()
            assert mvp_name is not None
            Text(
                bs.Lstr(value=mvp_name),
                position=(270 + xoffs, ts_height / 2 - 150 - 30 - 36 + v_extra + 15),
                h_align=Text.HAlign.LEFT,
                v_align=Text.VAlign.CENTER,
                maxwidth=180,
                color=bs.safecolor(mvp.team.color + (1,)),
                transition=Text.Transition.IN_LEFT,
                transition_delay=tval,
            ).autoretain()
            tval += 4 * t_incr

        # Most killed.
        most_killed = 0
        mkp, mkp_name = None, None
        for entry in player_entries:
            if entry[2].killed_count >= most_killed:
                mkp = entry[2]
                mkp_name = entry[1]
                most_killed = entry[2].killed_count
        if mkp is not None:
            Text(
                bs.Lstr(resource='mostDestroyedPlayerText'),
                color=(0.5, 0.5, 0.5, 1.0),
                v_align=Text.VAlign.CENTER,
                maxwidth=300,
                position=(180 + xoffs, ts_height / 2 - 300 + v_extra + 15),
                transition=Text.Transition.IN_LEFT,
                h_align=Text.HAlign.LEFT,
                transition_delay=tval,
            ).autoretain()
            Text(
                bs.Lstr(
                    value='(${A})',
                    subs=[
                        (
                            '${A}',
                            bs.Lstr(
                                resource='deathsTallyText',
                                subs=[('${COUNT}', str(most_killed))],
                            ),
                        )
                    ],
                ),
                position=(260 + xoffs, ts_height / 2 - 300 - 15 + v_extra),
                h_align=Text.HAlign.LEFT,
                scale=0.6,
                color=(0.3, 0.3, 0.3, 1.0),
                transition=Text.Transition.IN_LEFT,
                transition_delay=tval,
            ).autoretain()
            tval += 4 * t_incr
            Image(
                mkp.get_icon(),
                position=(233 + xoffs, ts_height / 2 - 300 - 30 - 46 + 25 + v_extra),
                scale=(50, 50),
                transition=Image.Transition.IN_LEFT,
                transition_delay=tval,
            ).autoretain()
            assert mkp_name is not None
            Text(
                bs.Lstr(value=mkp_name),
                position=(270 + xoffs, ts_height / 2 - 300 - 30 - 36 + v_extra + 15),
                h_align=Text.HAlign.LEFT,
                v_align=Text.VAlign.CENTER,
                color=bs.safecolor(mkp.team.color + (1,)),
                maxwidth=180,
                transition=Text.Transition.IN_LEFT,
                transition_delay=tval,
            ).autoretain()
            tval += 4 * t_incr

        # Now show individual scores.
        tdelay = tval
        if self._is_ffa:
            ts_h_offs -= xoffs
        Text(
            bs.Lstr(resource='finalScoresText'),
            color=(0.5, 0.5, 0.5, 1.0),
            position=(ts_h_offs, ts_height / 2),
            transition=Text.Transition.IN_RIGHT,
            transition_delay=tdelay,
        ).autoretain()
        tdelay += 4 * t_incr

        v_offs = 0.0
        tdelay += len(player_entries) * 8 * t_incr
        for _score, name, prec in player_entries:
            tdelay -= 4 * t_incr
            v_offs -= 40
            Text(
                (
                    str(prec.team.customdata['score'])
                    if self._is_ffa
                    else str(prec.score)
                ),
                color=(0.5, 0.5, 0.5, 1.0),
                position=(ts_h_offs + 230, ts_height / 2 + v_offs),
                h_align=Text.HAlign.RIGHT,
                transition=Text.Transition.IN_RIGHT,
                transition_delay=tdelay,
            ).autoretain()
            tdelay -= 4 * t_incr

            Image(
                prec.get_icon(),
                position=(ts_h_offs - 72, ts_height / 2 + v_offs + 15),
                scale=(30, 30),
                transition=Image.Transition.IN_LEFT,
                transition_delay=tdelay,
            ).autoretain()
            Text(
                bs.Lstr(value=name),
                position=(ts_h_offs - 50, ts_height / 2 + v_offs + 15),
                h_align=Text.HAlign.LEFT,
                v_align=Text.VAlign.CENTER,
                maxwidth=180,
                color=bs.safecolor(prec.team.color + (1,)),
                transition=Text.Transition.IN_RIGHT,
                transition_delay=tdelay,
            ).autoretain()
        self.entries = player_entries
        if self._is_ffa:
            places = []
            for i in range(3):  # change 3 to however many places you want
                try:
                    places.append(player_entries[i][2])
                except IndexError:
                    places.append(None)
            self.p1, self.p2, self.p3 = places
            self._show_places()
        else:
            # we do a specific cutscene later for teams...
            pass
        bs.timer(15.0, bs.WeakCall(self._show_tips))

    def _show_tips(self) -> None:
        from bascenev1lib.actor.tipstext import TipsText

        self._tips_text = TipsText(offs_y=70)

    def _play_victory_music(self) -> None:
        # Make sure we don't stomp on the next activity's music choice.
        if not self.is_transitioning_out():
            bs.setmusic(bs.MusicType.VICTORY)
    
    def _show_places(self):
        from bascenev1lib.actor.spazfactory import SpazFactory
        fac = SpazFactory.get()

        scale = 1.1
        start_y = -700

        def _spawn_place(player, x, final_y, delay, name, xoffset):
            if not player:
                return

            def _create():
                node = bs.newnode(
                    'image',
                    attrs={
                        'texture': bs.gettexture('white'),
                        'position': (x, start_y),
                        'scale': (128 * scale, 128 * scale),
                        'opacity': 1.0,
                        'absolute_scale': True,
                        'attach': 'center',
                    },
                )

                node.texture = fac.get_media(player.character)['earthportrait']

                podium = bs.newnode(
                    'image',
                    attrs={
                        'texture': bs.gettexture('white'),
                        'position': (x + xoffset, start_y - 384 * scale),
                        'scale': (128 * scale, 512 * scale),
                        'opacity': 1.0,
                        'absolute_scale': True,
                        'attach': 'center',
                    },
                )
                podium.color = player.player.color

                mathnode = bs.newnode(
                    'math',
                    owner=node,
                    attrs={'input1': (x + xoffset, -324 * scale), 'operation': 'add'},
                )

                node.connectattr('position', mathnode, 'input2')
                mathnode.connectattr('output', podium, 'position')

                bs.animate_array(
                    node,
                    'position',
                    2,
                    {
                        0: (x, start_y),
                        3: (x, final_y),
                    },
                )

                setattr(self, f"{name}node", node)
                setattr(self, f"{name}podium", podium)

            bs.timer(delay, _create)
        
        eh = 240
        p1_y = 240 - eh
        p2_y = 190 - eh
        p3_y = 140 - eh

        # spawn order (3rd → 2nd → 1st)
        if self.p3:
            _spawn_place(self.p3, -180, p3_y, 0.0, "p3", 180)
        if self.p2:
            _spawn_place(self.p2, 180, p2_y, 0.5, "p2", -180)
        if self.p1:
            _spawn_place(self.p1, 0, p1_y, 1.0, "p1", 0)
        

    def _show_winner(self, team: bs.SessionTeam) -> None:
        from bascenev1lib.actor.image import Image
        from bascenev1lib.actor.zoomtext import ZoomText
        from bascenev1lib.actor.spazfactory import SpazFactory
        fac = SpazFactory.get()
        
        ZoomText(
            bs.Lstr(resource='winsSeriesPlayerText', subs=[('${NAME}', team.name)]),
            position=(0, 220),
            color=team.color,
            scale=1.15,
            jitter=1.2,
            maxwidth=800,
        ).autoretain()
        if self.p1:
            self.p1node.texture = fac.get_media(self.p1.player.character)['EBwin']
            random.choice(fac.get_media(self.p1.player.character)['victory_sounds']).play()
        if self.p2 and not self.p3:
            self.p2node.texture = fac.get_media(self.p2.player.character)['EBlose']
            if self.p2.player.character == 'John Grace':
                bs.getsound('gibbed').play()
                ImageJumper.jump_image(self.p2node, 620, 230, -1100)
            bs.timer(0.8, random.choice(fac.get_media(self.p2.player.character)['death_sounds']).play)
        if self.p3:
            self.p3node.texture = fac.get_media(self.p3.player.character)['EBlose']
            if self.p3.player.character == 'John Grace':
                bs.getsound('gibbed').play()
                ImageJumper.jump_image(self.p3node, 620, 230, -1100)
            bs.timer(0.8, random.choice(fac.get_media(self.p3.player.character)['death_sounds']).play)