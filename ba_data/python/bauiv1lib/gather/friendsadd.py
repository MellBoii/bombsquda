# Released under the MIT License. See LICENSE for details.
#
"""UI functionality for entering promo codes."""

from __future__ import annotations

import time
import logging
from typing import TYPE_CHECKING, override

import bauiv1 as bui
import bascenev1 as bs
import fromgoverhaul.mell_resources as mell

if TYPE_CHECKING:
    from typing import Any


class AddFriendsWindow(bui.Window):
    """Window for adding friends."""
    def __init__(
        self,
        modal: bool = False,
        transition: str | None = 'in_scale',
    ):
        width = 600
        height = 300

        self._modal = modal
        self._r = 'friendsTab'

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
                transition=transition,
            ),
        )

        btn = bui.buttonwidget(
            parent=self._root_widget,
            scale=0.5,
            position=(40, height - 40),
            size=(60, 60),
            label='',
            on_activate_call=self.close,
            autoselect=True,
            color=(0.55, 0.5, 0.6),
            icon=bui.gettexture('crossOut'),
            iconscale=1.2,
        )

        v = height - 74
        v -= 20
        bui.textwidget(
            parent=self._root_widget,
            text=bui.Lstr(resource=f'{self._r}.addFriendTitle'),
            maxwidth=width * 0.9,
            position=(width * 0.5, v),
            size=(0, 0),
            scale=1.0,
            h_align='center',
            v_align='center',
        )
        v -= 20
        v -= 80

        self._text_field = bui.textwidget(
            parent=self._root_widget,
            position=(125, v),
            size=(380, 46),
            text='',
            h_align='left',
            v_align='center',
            max_chars=64,
            color=(0.9, 0.9, 0.9, 1.0),
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
                resource=f'promoCodeWindow.enterText'
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

        return bui.BasicMainWindowState(
            create_call=lambda transition: cls(
                transition=transition,
            )
        )
    
    def close(self) -> None:
        """Close the window."""
        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.containerwidget(edit=self._root_widget, transition='out_scale')

    def _activate_enter_button(self) -> None:
        self._enter_button.activate()

    def _do_enter(self) -> None:
        # pylint: disable=cyclic-import
        # from bauiv1lib.settings.advanced import AdvancedSettingsWindow

        plus = bui.app.plus
        assert plus is not None

        description: Any = bui.textwidget(query=self._text_field)
        assert isinstance(description, str)
        self.close()
        self.name_entered(description)
    
    def name_entered(self, name: str):
        response = mell.send_friend_request(name)
        if response.get('status') in ['error', 'fail'] or response.get('error'):
            full_error = (
                f'{response.get('status', '')}{'\n' if response.get('status') else ''}'
                f'{response.get('error', '')}{'\n' if response.get('error') else ''}{response.get('message', '')}'
            )
            bui.screenmessage(
                bui.Lstr(
                    r=f'{self._r}.errorAddingFriendText',
                    s=[('${ERROR}', full_error)],
                ),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
        else:
            bui.screenmessage(
                bui.Lstr(
                    r=f'{self._r}.requestSentText',
                    s=[('${NAME}', name)],
                ),
                color=(0, 1, 0),
            )
            bui.getsound('ding').play()
        
    