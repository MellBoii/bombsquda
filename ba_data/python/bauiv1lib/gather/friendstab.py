# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=too-many-lines
"""Defines the public tab in the gather UI."""

from __future__ import annotations

import copy
import time
import logging
from threading import Thread
from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast, override

from bauiv1lib.gather import GatherTab
from bauiv1lib.confirm import ConfirmWindow
from bauiv1lib.gather.friendschat import FriendChatWindow
from bauiv1lib.gather.friendsadd import AddFriendsWindow
import fromgoverhaul.mell_resources as mell
import bauiv1 as bui
import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Callable, Any

    from bauiv1lib.gather import GatherWindow

class FriendsTab(GatherTab):
    """A tab that gets all the user's friends and formats
    them into a nice interactable UI."""

    def __init__(self, window: GatherWindow) -> None:
        super().__init__(window)
        self._r = 'friendsTab'
        self.friends_list = None

        self._subcontainer = None
        self._scrollwidget = None

    @override
    def on_activate(
        self,
        parent_widget: bui.Widget,
        tab_button: bui.Widget,
        region_width: float,
        region_height: float,
        region_left: float,
        region_bottom: float,
    ) -> bui.Widget:
        # pylint: disable=too-many-positional-arguments
        self.c_width = c_width = region_width
        self.c_height = c_height = region_height - 20
        self._container = bui.containerwidget(
            parent=parent_widget,
            position=(
                region_left,
                region_bottom + (region_height - c_height) * 0.5,
            ),
            size=(c_width, c_height),
            background=False,
            selection_loops_to_parent=True,
        )
        s_width = c_width - 100
        s_height = c_height - 50
        sub_width = min(500, s_width * 0.95)
        self._scrollwidget = bui.scrollwidget(
            parent=self._container,
            size=(s_width, s_height),
            position=(50, 20),
            simple_culling_v=20.0,
            highlight=False,
            center_small_content_horizontally=True,
            selection_loops_to_parent=True,
            border_opacity=0.4,
        )
        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(sub_width, 0),
            background=False,
            selection_loops_to_parent=True,
        )
        status_text = bui.textwidget(
            parent=self._container,
            text='',
            size=(0, 0),
            scale=0.9,
            flatness=1.0,
            shadow=0.0,
            h_align='center',
            v_align='center',
            maxwidth=c_width,
            color=(0.6, 0.6, 0.6),
            position=(c_width * 0.5, c_height * 0.5),
        )
        if bui.app.config.get('squda_noonline'):
            full_error = bui.Lstr(r='noOnlineError')
            bui.textwidget(
                edit=status_text,
                text=bui.Lstr(
                    resource=f'{self._r}.errorText',
                    subs=[('${ERROR}', full_error)], 
                ),
            )
            return self._container
        test = mell.get_friends()
        if test.get('status') in ['error', 'fail'] or test.get('error'):
            full_error = (
                f'{test.get('status', '')}{'\n' if test.get('status') else ''}'
                f'{test.get('error', '')}{'\n' if test.get('error') else ''}{test.get('message', '')}'
            )
            bui.textwidget(
                edit=status_text,
                text=bui.Lstr(
                    resource=f'{self._r}.errorGettingFriendsText',
                    subs=[('${ERROR}', full_error)], 
                ),
            )
            return self._container
        bui.buttonwidget(
            parent=self._container,
            position=(s_width * 0.92, s_height * 0.88),
            size=(60, 60),
            scale=1.2,
            label='',
            icon=bui.gettexture('addFriendIcon'),
            on_activate_call=bui.Call(self.add_friends_ui),
        )
        self.recreate()
        return self._container

    @override
    def on_deactivate(self) -> None:
        pass
    
    def respond_request(self, id: str, accept: bool):
        if accept:
            bui.getsound('powerup01').play()
        else:
            bui.getsound('powerdown01').play()
        mell.respond_friend_request(id, accept)
        self.recreate()
    
    def remove_friend(self, id: str, name: str):
        def do_it():
            bui.getsound('shieldDown').play()
            mell.remove_friend(id)
            self.recreate()
        ConfirmWindow(
            text=bui.Lstr(
                r=f'{self._r}.confirmRemoveFriend',
                s=[('${NAME}', name)],
            ),
            action=bui.Call(do_it),
            origin_widget=self._container,
        )
    
    def add_friends_ui(self):
        AddFriendsWindow()
    
    def chat_with(self, id: str):
        FriendChatWindow(id)
    
    def recreate(self) -> None:
        if not self._subcontainer or not self._subcontainer.exists():
            return

        # delete old widgets
        self._subcontainer.delete()

        sub_width = self._scrollwidget.get_screen_space_center()[0]
        sub_width = min(500, (self.c_width - 100) * 0.95)

        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(sub_width, 0),
            background=False,
            selection_loops_to_parent=True,
        )

        self.friends_list = flist = mell.get_friends()
        self.friend_requests = flist['requests']
        self.friend_list = flist['friends']

        friend_height = 150
        spacing = 20
        tdelay_inc = 0.1
        tdelay = 0.5

        total_height = (
            len(self.friend_list) * (friend_height + spacing)
        ) + spacing

        bui.containerwidget(
            edit=self._subcontainer,
            size=(sub_width, total_height),
        )

        current_y = total_height - friend_height - spacing

        for friend in self.friend_list:
            info = mell.get_info_from_id(friend)

            friend_width = sub_width - 20

            container = bui.containerwidget(
                parent=self._subcontainer,
                size=(friend_width, friend_height),
                position=(20, current_y),
                background=False,
                selection_loops_to_parent=True,
            )

            bui.imagewidget(
                parent=container,
                size=(friend_width, friend_height),
                position=(0, 0),
                color=(0.1, 0.3, 0.6),
                texture=bui.gettexture('buttonSquareWide'),
                transition_delay=tdelay,
            )

            name = info.get(
                'username',
                info.get('account_name', 'Unknown'),
            )

            avatar = info.get('avatar', 'null')

            bui.textwidget(
                parent=container,
                text=str(name),
                size=(0, 0),
                scale=1.1,
                flatness=1.0,
                shadow=0.0,
                h_align='left',
                v_align='center',
                maxwidth=friend_width * 0.7,
                position=(110, friend_height - 40),
                transition_delay=tdelay,
            )

            bui.imagewidget(
                parent=container,
                size=(80, 80),
                position=(5, 35),
                texture=bui.gettexture(avatar),
                mask_texture=bui.gettexture('characterIconMask'),
                transition_delay=tdelay,
            )

            bui.buttonwidget(
                parent=container,
                position=(friend_width * 0.8, friend_height * 0.1),
                size=(60, 60),
                label='',
                color=(0.2, 0.4, 0.7),
                texture=bui.gettexture('buttonSquare'),
                icon=bui.gettexture('trashIcon'),
                on_activate_call=bui.Call(self.remove_friend, friend, name),
                transition_delay=tdelay,
            )

            bui.buttonwidget(
                parent=container,
                position=(friend_width * 0.65, friend_height * 0.1),
                size=(60, 60),
                label='',
                color=(0.2, 0.4, 0.7),
                texture=bui.gettexture('buttonSquare'),
                icon=bui.gettexture('chatIcon'),
                on_activate_call=bui.Call(self.chat_with, friend),
                transition_delay=tdelay,
            )

            current_y -= friend_height + spacing
            tdelay += tdelay_inc
        for request in self.friend_requests:
            info = mell.get_info_from_id(request)

            friend_width = sub_width - 20

            container = bui.containerwidget(
                parent=self._subcontainer,
                size=(friend_width, friend_height),
                position=(20, current_y),
                background=False,
                selection_loops_to_parent=True,
            )

            bui.imagewidget(
                parent=container,
                size=(friend_width, friend_height),
                position=(0, 0),
                color=(0.3, 0.6, 0.3),
                texture=bui.gettexture('buttonSquareWide'),
                transition_delay=tdelay,
            )

            name = info.get(
                'username',
                info.get('account_name', 'Unknown'),
            )

            avatar = info.get('avatar', 'null')

            bui.textwidget(
                parent=container,
                text=bui.Lstr(
                    r=f'{self._r}.friendRequestFromUser',
                    subs=[('${NAME}', name)]
                ),
                size=(0, 0),
                scale=1.1,
                flatness=1.0,
                shadow=0.0,
                h_align='left',
                v_align='center',
                maxwidth=friend_width * 0.7,
                position=(110, friend_height - 40),
                transition_delay=tdelay,
            )

            bui.imagewidget(
                parent=container,
                size=(80, 80),
                position=(5, 35),
                texture=bui.gettexture(avatar),
                mask_texture=bui.gettexture('characterIconMask'),
                transition_delay=tdelay,
            )

            bui.buttonwidget(
                parent=container,
                position=(friend_width * 0.8, friend_height * 0.1),
                size=(60, 60),
                label='',
                color=(0.4, 0.7, 0.4),
                texture=bui.gettexture('buttonSquare'),
                icon=bui.gettexture('crossOut'),
                on_activate_call=bui.Call(self.respond_request, request, False),
                transition_delay=tdelay,
            )

            bui.buttonwidget(
                parent=container,
                position=(friend_width * 0.65, friend_height * 0.1),
                size=(60, 60),
                label='',
                color=(0.4, 0.7, 0.4),
                texture=bui.gettexture('buttonSquare'),
                icon=bui.gettexture('acceptIcon'),
                on_activate_call=bui.Call(self.respond_request, request, True),
                transition_delay=tdelay,
            )

            current_y -= friend_height + spacing
            tdelay += tdelay_inc