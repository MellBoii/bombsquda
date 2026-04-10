# Released under the MIT License. See LICENSE for details.
#
"""Defines the about tab in the gather UI."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from bauiv1lib.gather import GatherTab
import bauiv1 as bui

if TYPE_CHECKING:
    from bauiv1lib.gather import GatherWindow


class AboutGatherTab(GatherTab):
    """The about tab in the gather UI"""

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
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-positional-arguments

        plus = bui.app.plus
        assert plus is not None

        try_tickets = plus.get_v1_account_misc_read_val(
            'friendTryTickets', None
        )

        show_message = True
        # Squish message as needed to get things to fit nicely at
        # various scales.
        uiscale = bui.app.ui_v1.uiscale
        message_height = (
            210
            if uiscale is bui.UIScale.SMALL
            else 305 if uiscale is bui.UIScale.MEDIUM else 370
        )
        # Let's not talk about sharing in vr-mode; its tricky to fit more
        # than one head in a VR-headset.
        show_message_extra = False
        message_extra_height = 60
        show_invite = False
        invite_height = 80
        show_discord = False

        c_height = 0
        if show_message:
            c_height += message_height
        if show_message_extra:
            c_height += message_extra_height
        if show_invite:
            c_height += invite_height

        party_button_label = bui.charstr(bui.SpecialChar.TOP_BUTTON)
        message = bui.Lstr(
            resource='gatherWindow.aboutDescriptionText',
            subs=[
                ('${PARTY}', bui.charstr(bui.SpecialChar.PARTY_ICON)),
                ('${BUTTON}', party_button_label),
            ],
        )

        scroll_widget = bui.scrollwidget(
            parent=parent_widget,
            position=(region_left, region_bottom),
            size=(region_width, region_height),
            highlight=False,
            border_opacity=0,
        )

        container = bui.containerwidget(
            parent=scroll_widget,
            position=(
                region_left,
                region_bottom + (region_height - c_height) * 0.5,
            ),
            size=(region_width, c_height),
            background=False,
            selectable=show_invite or show_discord,
        )
        # Allows escaping if we select the container somehow (though
        # shouldn't be possible when buttons are present).
        bui.widget(edit=container, up_widget=tab_button)

        y = c_height * 0.1
        getres = bui.app.lang.get_resource
        msc_scale = getres('gatherWindow.aboutDescriptionScale')
        if show_message:
            scaling = 700
            bui.textwidget(
                parent=container,
                position=(region_width * 0.5, y),
                color=(0.6, 1.0, 0.6),
                scale=msc_scale,
                size=(0, 0),
                maxwidth=scaling,
                max_height=scaling,
                h_align='center',
                v_align='center',
                text=message,
            )

        if show_invite:
            bui.textwidget(
                parent=container,
                position=(region_width * 0.57, y),
                color=(0, 1, 0),
                scale=0.6,
                size=(0, 0),
                maxwidth=region_width * 0.5,
                h_align='right',
                v_align='center',
                flatness=1.0,
                text=bui.Lstr(
                    resource='gatherWindow.inviteAFriendText',
                    subs=[('${COUNT}', str(try_tickets))],
                ),
            )
            invite_button = bui.buttonwidget(
                parent=container,
                position=(region_width * 0.59, y - 25),
                size=(230, 50),
                color=(0.54, 0.42, 0.56),
                textcolor=(0, 1, 0),
                label=bui.Lstr(
                    resource='gatherWindow.inviteFriendsText',
                    fallback_resource='gatherWindow.getFriendInviteCodeText',
                ),
                autoselect=True,
                on_activate_call=bui.WeakCall(self._invite_to_try_press),
                up_widget=tab_button,
                show_buffer_top=500,
            )
            y -= invite_height
        else:
            invite_button = None

        return scroll_widget

    def _invite_to_try_press(self) -> None:
        from bauiv1lib.account.signin import show_sign_in_prompt
        from bauiv1lib.appinvite import handle_app_invites_press

        plus = bui.app.plus
        assert plus is not None

        if plus.get_v1_account_state() != 'signed_in':
            show_sign_in_prompt()
            return
        handle_app_invites_press()