""" i dunno """

from __future__ import annotations

from typing import TYPE_CHECKING, override
import logging

import bauiv1 as bui
import bascenev1 as bs
from bauiv1lib.popup import PopupMenu
import babase as ba
import random

if TYPE_CHECKING:
    from typing import Any, Callable


class TitleWindow(bui.MainWindow):
    def __init__(
        self, 
        origin_widget: bui.Widget | None = None,
        transition: str | None = 'in_right',
        ):
        bui.set_party_window_open(True)
        self._width = 0
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._height= 0
        blmsh = bui.getmesh('shield')
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                transition='in_scale',
            ),
            transition=transition,
            origin_widget=origin_widget,
        )
        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(10, -100),
            size=(0, 0),
            scale=1.8,
            text='press to start twinny',
            color=(1, 1, 1),
            h_align='center',
            v_align='center',
        )
        self.play_button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(-120, -220),
            size=(200, 200),
            mesh_transparent=blmsh,
            mesh_opaque=blmsh,
            textcolor=(1, 1, 1),
            scale=9999,
            text_scale=1.3,
            label='',
            enable_sound=False,
            on_activate_call=self.close,
        )
    def close(self) -> None:
        """Close the window."""
        # no-op if we're not currently in control.
        rsfx = [
            'randomnoises/noisePolution5',
            'voicelines/spaz/spazDeath04',
            'learnPSI',
            'punchStrong01',
            'punchStrong03',
            'shatter',
            'smaash',
            'thunder',
            'swish',
            'okitem',
            'mel06',
            'mbmYeehaw1',
            'luigi_burning',
            'homer3',
            'gibbed2',
            'agent2',
            'healthPowerup',
        ]
        bui.getsound(random.choice(rsfx)).play()
        if not self.main_window_has_control():
            return
        from bauiv1lib.mainmenu import MainMenuWindow
        self.main_window_replace(
            MainMenuWindow(
                origin_widget=self._root_widget,
            )
        )
    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )
