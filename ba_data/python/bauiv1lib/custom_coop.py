"""UI related to the custom coop campaign in BombSquda."""

from __future__ import annotations

from typing import override

import bauiv1 as bui
import babase as ba
import bascenev1 as bs

class CustomCoopWindow(bui.MainWindow):
    """A menu for selecting play and some other stuff."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 450
        self._height = 400
        # xoffs = 70 if uiscale is bui.UIScale.SMALL else 0
        # yoffs = -45 if uiscale is bui.UIScale.SMALL else 0

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            1.55
            if uiscale is bui.UIScale.SMALL
            else 1.35 if uiscale is bui.UIScale.MEDIUM else 1.1
        )

        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        # target_width = min(self._width - 60, screensize[0] / scale)
        target_height = min(self._height - 100, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * self._height + 0.5 * target_height + 100.0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )
        bui.containerwidget(
            edit=self._root_widget,
            background=False,
        )
        activity = bs.get_foreground_host_activity()
        if activity:
            with activity.context:
                activity.hide_menu_text()
        
        button_width = 250
        xoffs = -30
        img_xoffs = 300
        image_scale = 0.7
        pos = self._width * 0.1
        yoffs += 90
        if uiscale is bui.UIScale.SMALL:
            yoffs -= 70
            image_scale = 0.9
        self._subcontainer = bui.containerwidget(
            parent=self._root_widget,
            size=(512 * image_scale + 50, self._height * 5),
            background=True,
            claims_left_right=False,
            position=(pos - xoffs - button_width - 30, -self._height),
        )
        bui.imagewidget(
            parent=self._root_widget,
            position=(pos - xoffs - button_width, yoffs - 200),
            size=(512 * image_scale, 128 * image_scale),
            texture=bui.gettexture('logo2'),
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(pos - xoffs - button_width + 200, yoffs - 230),
            scale=0.8,
            text=bui.Lstr(resource='customCampaignSubtitle'),
            h_align='center',
        )
        yoffs -= 100
        button_mult = 0.8
        if uiscale is bui.UIScale.SMALL:
            button_mult = 0.6
        bui.buttonwidget(
            autoselect=True,
            parent=self._root_widget,
            position=(pos - button_width * button_mult - xoffs, yoffs - 200),
            size=(button_width, 60),
            label=bui.Lstr(resource='playText'),
            on_activate_call=self._play_press,
        )
        yoffs -= 60
        btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(pos - button_width * button_mult - xoffs, yoffs - 200),
            autoselect=False,
            size=(button_width, 60),
            label=bui.Lstr(resource='backText'),
            on_activate_call=self.main_window_back,
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=btn)
    
    def _play_press(self):
        if not bool(False):
            bui.screenmessage(
                bui.Lstr(resource='mellNotDone'), 
                color=(1, 0, 0)
            )
            bui.getsound('error').play()
            return
        act = bs.get_foreground_host_activity()
        with act.context:
            act.fade_out_to_test()
        bui.containerwidget(edit=self._root_widget, transition='out_left')
    
    @override
    def main_window_back(self):
        super().main_window_back()
        activity = bs.get_foreground_host_activity()
        if activity:
            with activity.context:
                activity.show_menu_text()
    
    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

