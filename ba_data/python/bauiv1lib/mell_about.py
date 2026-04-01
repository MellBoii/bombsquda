"""Window used for showing info."""
from __future__ import annotations
import bauiv1 as bui
import babase as ba
from typing import override

class MellInfoWindow(bui.Window):
    """
    A simple window for text.
    It's supposed to be used to show info about
    a certain feature. Body text is the info text,
    and title text is the title (so something like 'About [FEATURE]')
    """
    def __init__(self, titletext: str | ba.Lstr, bodytext: str | ba.Lstr):
        assert bui.app.classic is not None

        uiscale = bui.app.ui_v1.uiscale

        # Base size (scaled slightly by UI scale)
        self._width = int(700 * (1.6 if uiscale is bui.UIScale.SMALL else 1.1))
        self._height = int(420 * (1.6 if uiscale is bui.UIScale.SMALL else 1.15))

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                transition='in_scale',
            ),
            prevent_main_window_auto_recreate=False,
        )

        pad = self._width * 0.05
        center_x = self._width * 0.5
        
        # Clamp text scale so resizing never breaks it
        title_scale = min(1.25, max(0.9, self._width / 700)) * (1.6 if uiscale is bui.UIScale.SMALL else 1.15)
        body_scale = min(0.9, max(0.6, self._width / 900)) * (1.6 if uiscale is bui.UIScale.SMALL else 1.15)

        max_text_width = self._width - pad * 2

        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(center_x, self._height - pad * 1.5),
            size=(0, 0),
            h_align='center',
            v_align='top',
            scale=title_scale,
            maxwidth=max_text_width,
            text=titletext,
            color=(1, 1, 1),
        )
        body_y = self._height - pad * 2.8

        self._body_text = bui.textwidget(
            parent=self._root_widget,
            position=(center_x, body_y),
            size=(0, 0),
            h_align='center',
            v_align='top',
            scale=body_scale,
            maxwidth=max_text_width,
            text=bodytext,
            color=(0.9, 0.9, 0.9),
        )

        button_width = min(300, self._width * 0.45)
        button_height = 80
        bx = center_x - button_width * 0.4
        if uiscale is bui.UIScale.SMALL:
            bx -= 60

        self._back_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=False,
            position=(bx, pad * 0.6),
            size=(button_width, button_height),
            scale=(0.8 if uiscale is not bui.UIScale.SMALL else 1.2),
            text_scale=1.2,
            label=ba.Lstr(resource='backText'),
            color=(0.75, 0.4, 0.4),
            textcolor=(1, 1, 1),
            on_activate_call=self.close,
        )

        bui.containerwidget(edit=self._root_widget, cancel_button=btn)

    # --------------------------------------------------
    # Close
    # --------------------------------------------------

    def close(self) -> None:
        if not self._root_widget or self._root_widget.transitioning_out:
            return
        bui.containerwidget(edit=self._root_widget, transition='out_scale')