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
        showcase_mode: bool = False
        ):
        bui.set_party_window_open(True)
        self._width = 0
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._height= 0
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                transition='in_scale',
            ),
            transition=transition,
            origin_widget=origin_widget,
        )
        if showcase_mode:
            return
        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(0, -150),
            size=(0, 0),
            scale=1.8,
            text=ba.Lstr(resource='pressStart'),
            color=(1, 1, 1),
            h_align='center',
            v_align='center',
        )
        self.play_button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(-1000, -600),
            size=(2000, 1500),
            mesh_transparent=None,
            mesh_opaque=None,
            texture=bui.gettexture('empty'),
            textcolor=(1, 1, 1),
            scale=1.0,
            text_scale=1.3,
            label='',
            enable_sound=False,
            on_activate_call=self.close,
        )
        self.quit_btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(-600, -310),
            size=(200, 80),
            textcolor=(1, 1, 1),
            color=(0.8, 0.4, 0.4),
            scale=0.8,
            text_scale=1.3,
            label=ba.Lstr(resource='quitFuckinGame'),
            on_activate_call=self.quit_window,
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=self.quit_btn)
        
    def close(self) -> None:
        """Close the window."""
        # no-op if we're not currently in control.
        rsfx = [
            'voicelines/spaz/death04',
            'voicelines/noise/sound2',
            'voicelines/homer/sound3',
            'voicelines/mell/sound6',
            'punchSFX/punchStrong01',
            'punchSFX/punchStrong03',
            'screams/scream1',
            'mbm/yeehaw1',
            'shatter',
            'smaash',
            'thunder',
            'swish',
            'okitem',
            'gibbed2',
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
        
    def quit_window(self):
        # pylint: disable=cyclic-import
        from bauiv1lib.confirm import QuitWindow

        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return

        # Note: Normally we should go through bui.quit(confirm=True) but
        # invoking the window directly lets us scale it up from the
        # button.
        QuitWindow(origin_widget=self.quit_btn)
        
    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )
