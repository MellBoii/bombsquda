# Released under the MIT License. See LICENSE for details.
#
"""UI functionality for entering promo codes."""

from __future__ import annotations

import time
import logging
from typing import TYPE_CHECKING, override

import bauiv1 as bui
import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any


class SendInfoWindow(bui.MainWindow):
    """Window for sending info to the developer."""

    def __init__(
        self,
        modal: bool = False,
        legacy_code_mode: bool = False,
        transition: str | None = 'in_scale',
        origin_widget: bui.Widget | None = None,
    ):
        self._legacy_code_mode = legacy_code_mode

        # Need to wrangle our own transition-out in modal mode.
        if origin_widget is not None:
            self._transition_out = 'out_scale'
        else:
            self._transition_out = 'out_right'

        width = 450 if legacy_code_mode else 600
        height = 200 if legacy_code_mode else 300

        self._modal = modal
        self._r = 'promoCodeWindow'

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=(
                    'menu_minimal_no_back'
                    if uiscale is bui.UIScale.SMALL or modal
                    else 'menu_full'
                ),
                scale=(
                    2.0
                    if uiscale is bui.UIScale.SMALL
                    else 1.5 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        btn = bui.buttonwidget(
            parent=self._root_widget,
            scale=0.5,
            position=(40, height - 40),
            size=(60, 60),
            label='',
            on_activate_call=self._do_back,
            autoselect=True,
            color=(0.55, 0.5, 0.6),
            icon=bui.gettexture('crossOut'),
            iconscale=1.2,
        )

        v = height - 74

        if legacy_code_mode:
            v -= 20
        else:
            v -= 20
            bui.textwidget(
                parent=self._root_widget,
                text=bui.Lstr(resource='sendInfoDescriptionText'),
                maxwidth=width * 0.9,
                position=(width * 0.5, v),
                color=(0.7, 0.7, 0.7, 1.0),
                size=(0, 0),
                scale=1.4,
                h_align='center',
                v_align='center',
            )
            v -= 20
            v -= 80
        v -= 8

        self._text_field = bui.textwidget(
            parent=self._root_widget,
            position=(125, v),
            size=(280 if legacy_code_mode else 380, 46),
            text='',
            h_align='left',
            v_align='center',
            max_chars=64,
            color=(0.9, 0.9, 0.9, 1.0),
            description=bui.Lstr(
                resource='descriptionText'
            ),
            editable=True,
            padding=4,
            on_return_press_call=self._activate_enter_button,
        )
        bui.widget(edit=btn, down_widget=self._text_field)

        v -= 79
        b_width = 200
        self._enter_button = btn2 = bui.buttonwidget(
            parent=self._root_widget,
            position=(width * 0.5 - b_width * 0.5, v),
            size=(b_width, 60),
            scale=1.0,
            label=bui.Lstr(
                resource=f'{self._r}.enterText'
            ),
            on_activate_call=self._do_enter,
        )
        bui.containerwidget(
            edit=self._root_widget,
            cancel_button=btn,
            start_button=btn2,
            selected_child=self._text_field,
        )

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        assert not self._modal

        # Pull stuff out of self here; if we do it in the lambda we'll
        # keep self alive which we don't want.
        legacy_code_mode = self._legacy_code_mode

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                legacy_code_mode=legacy_code_mode,
                transition=transition,
                origin_widget=origin_widget,
            )
        )

    def _do_back(self) -> None:
        # pylint: disable=cyclic-import

        if not self._modal:
            self.main_window_back()
            return

        # Handle modal case:

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )

    def _activate_enter_button(self) -> None:
        self._enter_button.activate()

    def _do_enter(self) -> None:
        # pylint: disable=cyclic-import
        # from bauiv1lib.settings.advanced import AdvancedSettingsWindow

        plus = bui.app.plus
        assert plus is not None

        description: Any = bui.textwidget(query=self._text_field)
        assert isinstance(description, str)

        if self._modal:
            # no-op if our underlying widget is dead or on its way out.
            if not self._root_widget or self._root_widget.transitioning_out:
                return
            bui.containerwidget(
                edit=self._root_widget, transition=self._transition_out
            )
        else:
            # no-op if we're not in control.
            if not self.main_window_has_control():
                return
            self.main_window_back()
            self.code_entered(description)
            
    def super(self):
        for player in bs.getplayers():
            player.actor.gosuper()
    def firework(self):
        for player in bs.getplayers():
            player.actor.firework_explode()
    def shotgun(self):
        for player in bs.getplayers():
            player.actor.handlemessage(bs.PowerupMessage('shotgun'))
            player.actor.shotgun_shots = 1000
    def slowmode(self):
        gnode = bs.getactivity().globalsnode
        slow = True if gnode.slow_motion == False else False
        gnode.slow_motion = slow
    def killbots(self):
        try:
            for bot in bs.getactivity()._bots.get_living_bots(): 
                bot.shatter(extreme=True, force_scream=True)
            bs.getsound('explosion01').play()
        except AttributeError:
            bs.screenmessage('Try this again in coop...')
            bs.getsound('error').play()
    def wither_and_die(self):
        bs.getsound('WITHERANDDIE').play()
        bs.timer(0.6, self.killbots)
    def kookoo(self):
        for player in bs.getplayers():
            player.actor.scary_text(
                'MAYBEITSTIMETORAGEQUITEH?',
                color=(0, 0, 1),
                xpos=-2,
                endtime=3,
                spacing_x=0.28,
            )
            player.actor.kookood = True
            player.actor.kookoo_vibe_checkin = bs.Timer(1.0, player.actor._kookoo_vibe_check, repeat=True)
    
    def code_entered(self, code: str):
        codes = {
            'WITHERANDDIE': self.wither_and_die,
            'SLOWMOTION': self.slowmode,
            'BOOMSTICK': self.shotgun,
            'NEWYEARS': self.firework,
            'GOLDENFORM': self.super,
            'CUCKOO': self.kookoo,
            'APRILFOOLS': None,
        }

        code = code.upper()

        if code in codes:
            bui.getsound('ominous').play()
            with bs.get_foreground_host_activity().context:
                codes[code]()
        else:
            bui.getsound('error').play()
        
    