""" Activity and session for the online menu. """

# update, this probably will most likely not be used
# since it's pretty scuffed and i'd rather use the normal
# gather tab... X(
# it was basically supposed to be inspired by the ring racers
# online server thing, but probably waaaaay too hard to recreate.
# maybe i'll continue this??
# oh yeah, the main menu has a variable for debugging this if you wish
# to debug this for whatever reasons...
# update part 2!! im  going insane writing these 
# at the same time but continuing
# i'm still working on this... kinda.. i'll add this as a option

from __future__ import annotations
import bascenev1 as bs
import bauiv1 as bui
import babase as ba
from typing import TYPE_CHECKING, override
from bascenev1lib.actor.text import Text
import threading
import time
import socket


# player..
class Player(bs.Player):
    """Our player type for this game."""
    
# party fetcher...
class PartyFetcher:
    def __init__(self):
        self.parties: list[dict] = []
        self.refreshing = False

    def refresh(self):
        if self.refreshing:
            return
        self.refreshing = True

        plus = bui.app.plus
        plus.add_v1_account_transaction(
            {
                'type': 'PUBLIC_PARTY_QUERY',
                'proto': bs.protocol_version(),
                'lang': bui.app.lang.language,
            },
            callback=self._on_result,
        )
        plus.run_v1_account_transactions()

    def _on_result(self, result):
        self.refreshing = False
        if not result:
            self.parties = []
            return
        self.parties = result['l']

# session..
class OnlineMenuSession(bs.Session):
    def __init__(self):
        depsets: Sequence[bs.DependencySet] = [] 
        super().__init__(depsets)
        self.setactivity(bs.newactivity(OnlineSelection))
        
class OnlineSelection(bs.GameActivity[bs.Player, bs.Team]):
    name = ''
    description = ''
    suppress_zoomtext = True
    show_controls_guide = False
    allow_pausing = False
    
    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Nothing']
        
    def __init__(self, settings: dict):
        super().__init__(settings)
        # make a background!
        self.bg = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': bs.getmesh('DSspace'),
                    'color': (0.92, 0.91, 0.9),
                    'lighting': True,
                    'background': True,
                    'color_texture': bs.gettexture('DSspace'),
                },
            )
        )
        self.earth = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': bs.getmesh('spaceEarth'),
                    'color': (0.92, 0.91, 0.9),
                    'lighting': True,
                    'background': True,
                    'color_texture': bs.gettexture('spaceLevel'),
                },
            )
        )
                
    def on_transition_in(self) -> None:
        super().on_transition_in()
        
        gnode = self.globalsnode
        gnode.camera_mode = 'rotate'
        bs.setmusic(bs.MusicType.ONLINE, continuous=True)
        self.join_text = None
        self.menu_items = [
            {"id": "browse", "label": "Browse"},
            {"id": "host", "label": "Host Game"},
            {"id": "direct", "label": "Direct Connect"},
            {"id": "back", "label": "Back"},
        ]
        self.menu_nodes = []
        self.selected_index = 0

        x = -50
        start_y = 100
        spacing = 100
        button_offset = 550
        # background to make
        # it look nice
        self.background = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('windowHSmallVMed'),
                'position': (x + button_offset - 30, -15),
                'scale': (700, 1000),
                'color': (0.2, 0.2, 0.2),
                'opacity': 0.6,
            },
        )
        
        # logo
        self.logo = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('onlineIcon'),
                'position': (-300, 0),
                'scale': (500, 500),
            },
        )
        self.logo_text = bs.newnode(
                'text',
                attrs={
                    'text': 'SQUDA CHANNEL',
                    'position': (-300, -310),
                    'scale': 1.4,
                    'h_align': 'center',
                },
            )
            
        for i, item in enumerate(self.menu_items):
            y = start_y - i * spacing

            # bg button
            bg = bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture('buttonSquareWide'),
                    'position': (x + button_offset, y),
                    'scale': (500, 100),
                    'color': (0.2, 0.2, 0.2),
                    'opacity': 0.6,
                },
            )

            # le text
            text = bs.newnode(
                'text',
                attrs={
                    'text': item["label"],
                    'position': (x, y),
                    'scale': 1.4,
                    'color': (1, 1, 1),
                    'h_align': 'right',
                    'v_align': 'center',
                    'h_attach': 'right',
                    'shadow': 0.5,
                    'flatness': 0.3,
                },
            )
            # append to our menu nodes!
            self.menu_nodes.append({"bg": bg, "text": text})
        self.xpos = x
        self.button_offset = button_offset
        self._update_selection()
        # throw some controller info
        # on how to use the menu
        infoy = 30
        infox = 10
        self.backinfo = bs.newnode(
            'text',
            attrs={
                'text': (
                    f"{ba.charstr(ba.SpecialChar.RIGHT_BUTTON)} = "
                    f"{ba.charstr(ba.SpecialChar.BACK)}"
                ),
                'position': (infox, infoy),
                'scale': 2.0,
                'color': (1, 1, 1),
                'v_align': 'center',
                'h_align': 'left',
                'v_attach': 'bottom',
                'h_attach': 'left',
                'shadow': 0.5,
                'flatness': 0.3,
            },
        )
        if len(self.players) < 1:
            self.join_text = Text(
                'Please join the activity to continue...',
                h_align=Text.HAlign.CENTER,
                scale=1.5,
                position=(0, 300)
            )
    
    def _update_selection(self):
        select_offset = -70
        button_offset = self.button_offset
        
        for i, item in enumerate(self.menu_nodes):
            y = 100 - i * 100
            offset = select_offset if i == self.selected_index else 0

            item["text"].position = (self.xpos + offset, y)
            item["bg"].position   = (self.xpos + button_offset + offset, y)

            if i == self.selected_index:
                item["bg"].opacity = 1.0
            else:
                item["bg"].opacity = 0.6

    def up(self):
        self.selected_index = (self.selected_index - 1) % len(self.menu_nodes)
        self._update_selection()

    def down(self):
        self.selected_index = (self.selected_index + 1) % len(self.menu_nodes)
        self._update_selection()
    
    def back(self):
        from bascenev1lib.mainmenu import MainMenuSession
        bs.pushcall(lambda: bs.new_host_session(MainMenuSession))
        
    def select(self):
        item_id = self.menu_items[self.selected_index]["id"]

        if item_id == "browse":
            self.session.setactivity(bs.newactivity(ServerListActivity))
        elif item_id == "host":
            pass  # hosting menu
        elif item_id == "direct":
            self.session.setactivity(bs.newactivity(DirectConnectActivity))
        elif item_id == "back":
            self.back()
            
        
    @override
    def on_player_join(self, player: PlayerT) -> None:
        if self.join_text:
            self.join_text.node.delete()
        player.assigninput(
            (
                ba.InputType.JUMP_PRESS,
                ba.InputType.PUNCH_PRESS,
                ba.InputType.PICK_UP_PRESS,
            ),
            self.select,
        )
        player.assigninput(ba.InputType.UP_PRESS, self.up)
        player.assigninput(ba.InputType.DOWN_PRESS, self.down)
        player.assigninput(ba.InputType.BOMB_PRESS, self.back)
        
    def on_begin(self) -> None:
        super().on_begin()
        
class DirectConnectActivity(bs.GameActivity[bs.Player, bs.Team]):
    """Activity for showing online servers."""

    name = ''
    description = ''
    suppress_zoomtext = True
    show_controls_guide = False
    allow_pausing = False
    
    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Nothing']
        
    def __init__(self, settings: dict):
        super().__init__(settings)
        self.bg = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': bs.getmesh('DSspace'),
                    'color': (0.92, 0.91, 0.9),
                    'lighting': True,
                    'background': True,
                    'color_texture': bs.gettexture('DSspace'),
                },
            )
        )
        self.earth = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': bs.getmesh('spaceEarth'),
                    'color': (0.92, 0.91, 0.9),
                    'lighting': True,
                    'background': True,
                    'color_texture': bs.gettexture('spaceLevel'),
                },
            )
        )
        self.useinfo = bs.newnode(
            'text',
            attrs={
                'text': (
                    f"Please enter a address and port:\n"
                    'FORMATTING: IP:PORT'
                ),
                'position': (0, -250),
                'scale': 1.0,
                'shadow': 0.5,
                'flatness': 0.3,
                'v_attach': 'top',
                'h_align': 'center',
            },
        )
        self.entered_text = ""
        self.field_bg = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('buttonSquareWide'),
                'position': (0, 40),
                'scale': (500, 70),
                'opacity': 0.8,
            },
        )

        self.field_text = bs.newnode(
            'text',
            attrs={
                'text': '',
                'position': (0, 40),
                'h_align': 'center',
                'v_align': 'center',
                'scale': 1.3,
            },
        )
        KEYS = [
            "1234567890",
            ".:/<>",
        ]
        self.key_nodes = []
        start_y = -40

        for row_i, row in enumerate(KEYS):
            start_x = -len(row) * 22
            for col_i, char in enumerate(row):
                node = bs.newnode(
                    'text',
                    attrs={
                        'text': char,
                        'position': (start_x + col_i * 44, start_y - row_i * 50),
                        'scale': 1.0,
                    },
                )
                self.key_nodes.append((row_i, col_i, char, node))
        self.cur_row = 0
        self.cur_col = 0
    def _parse_address(self, text: str):
        text = text.strip()

        if ":" not in text:
            raise ValueError("Missing ':' separator")

        ip_part, port_part = text.split(":", 1)

        ip_part = ip_part.strip()
        port_part = port_part.strip()

        # Validate IP
        nums = ip_part.split(".")
        for n in nums:
            if not n.isdigit():
                raise ValueError("Invalid IP number")
            v = int(n)
            if not (0 <= v <= 255):
                raise ValueError("IP value out of range")

        # Validate Port
        if not port_part.isdigit():
            raise ValueError("Port must be a number")

        port = int(port_part)
        if not (1 <= port <= 65535):
            raise ValueError("Port out of range")

        return ip_part, port
        
    def _refresh_field(self):
        self.field_text.text = self.entered_text

    def _get_selected_char(self):
        for r, c, ch, _ in self.key_nodes:
            if r == self.cur_row and c == self.cur_col:
                return ch
        return None
        
    def select(self):
        char = self._get_selected_char()

        if char == '<':
            self.entered_text = self.entered_text[:-1]

        elif char == '>':
            self._connect(self.entered_text)
            return

        else:
            self.entered_text += char

        self._refresh_field()
        
    def _connect(self, text):
        try:
            ip, port = self._parse_address(text)
        except ValueError as e:
            self._show_error(str(e))
            return
        bs.connect_to_party(ip, port=port)
        
    def _show_error(self, msg):
        if hasattr(self, "error_text"):
            self.error_text.delete()

        self.error_text = bs.newnode(
            'text',
            attrs={
                'text': msg,
                'position': (0, -200),
                'color': (1, 0.3, 0.3),
                'scale': 0.9,
                'v_attach': 'top',
                'h_align': 'center',
            },
        )
        
    def _update_cursor(self):
        for r, c, _, node in self.key_nodes:
            node.color = (1,1,1)
            if r == self.cur_row and c == self.cur_col:
                node.color = (1.5,1.5,0)

    def on_move(self, dx, dy):
        self.cur_col += dx
        self.cur_row += dy
        self._update_cursor()
        
    def left(self):
        self.on_move(-1, 0)
    def right(self):
        self.on_move(1, 0)
    def up(self):
        self.on_move(0, -1)
    def down(self):
        self.on_move(0, 1)
    def back(self):
        if len(self.entered_text) == 0:
            self.session.setactivity(bs.newactivity(OnlineSelection))
        else:
            self.entered_text = self.entered_text[:-1]
            self._refresh_field()
    @override
    def on_player_join(self, player: PlayerT) -> None:
        player.assigninput(ba.InputType.JUMP_PRESS, self.select)
        player.assigninput(ba.InputType.UP_PRESS, self.up)
        player.assigninput(ba.InputType.DOWN_PRESS, self.down)
        player.assigninput(ba.InputType.RIGHT_PRESS, self.right)
        player.assigninput(ba.InputType.LEFT_PRESS, self.left)
        player.assigninput(ba.InputType.BOMB_PRESS, self.back)
        
    def on_transition_in(self) -> None:
        super().on_transition_in()
        
        gnode = self.globalsnode
        gnode.camera_mode = 'rotate'
        bs.setmusic(bs.MusicType.ONLINE, continuous=True)
        
    def on_begin(self) -> None:
        super().on_begin()

        
class ServerListActivity(bs.GameActivity[bs.Player, bs.Team]):
    """Activity for showing online servers."""

    name = ''
    description = ''
    suppress_zoomtext = True
    show_controls_guide = False
    allow_pausing = False
    
    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Nothing']
        
    def __init__(self, settings: dict):
        super().__init__(settings)
        # make a background!
        self.bg = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': bs.getmesh('DSspace'),
                    'color': (0.92, 0.91, 0.9),
                    'lighting': True,
                    'background': True,
                    'color_texture': bs.gettexture('DSspace'),
                },
            )
        )
        self.earth = bs.NodeActor(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': bs.getmesh('spaceEarth'),
                    'color': (0.92, 0.91, 0.9),
                    'lighting': True,
                    'background': True,
                    'color_texture': bs.gettexture('spaceLevel'),
                },
            )
        )
        self.join_text = None
        if len(self.players) < 1:
            self.join_text = Text(
                'Please join the activity to continue...',
                h_align=Text.HAlign.CENTER,
                scale=1.5,
            )
        self.fetcher = PartyFetcher()
        self.fetcher.refresh()
        self.selected_index = 0
        self.scroll_offset = 0
        self.VISIBLE_ROWS = 14   # tweak for your screen
        self.party_text_nodes: list[Text] = []
        self.pings = {}
        self.pinging = set()
        self.ping_state = {}
        self.MAX_PING_THREADS = 10

                
    def rebuild_list(self):
        for n in self.party_text_nodes:
            n.delete()
        self.party_text_nodes.clear()

        start_y = 320.0
        spacing = 50.0

        visible_parties = self.fetcher.parties[
            self.scroll_offset : self.scroll_offset + self.VISIBLE_ROWS
        ]

        for row, p in enumerate(visible_parties):
            index = self.scroll_offset + row
            y = start_y - row * spacing

            color = (1, 1, 1, 1) if index == self.selected_index else (0.5, 0.5, 0.5, 1)

            node = bs.newnode(
                'text',
                attrs={
                    'text': f"{p['n']}  {p['s']}/{p['sm']}, {p['pd']}ms",
                    'position': (0, y),
                    'scale': 1.4,
                    'color': color,
                    'h_align': 'center',
                    'v_align': 'center',
                    'shadow': 0.5,
                    'flatness': 0.3,
                },
            )

            self.party_text_nodes.append(node)

    def _ping_party(self, addr: str, port: int):
        import socket, time, threading

        key = (addr, port)
        if key in self.pinging:
            return

        if len(self.pinging) >= self.MAX_PING_THREADS:
            return

        self.pinging.add(key)
        self.ping_state[key] = "measuring"

        def do_ping():
            ping = None
            sock = None
            try:
                socket_type = socket.AF_INET6 if ":" in addr else socket.AF_INET
                sock = socket.socket(socket_type, socket.SOCK_DGRAM)
                sock.connect((addr, port))
                sock.settimeout(1)

                start = time.time()
                accessible = False

                for _ in range(3):
                    sock.send(b'\x0b')
                    try:
                        if sock.recv(10) == b'\x0c':
                            accessible = True
                            break
                    except Exception:
                        pass
                    time.sleep(0.3)

                if accessible:
                    ping = int((time.time() - start) * 1000)

            except Exception:
                pass
            finally:
                if sock:
                    sock.close()

            self.pings[key] = ping
            self.ping_state[key] = "done"
            self.pinging.discard(key)

        threading.Thread(target=do_ping, daemon=True).start()



    def refresh_parties(self):
        self.fetcher.refresh()
        for p in self.fetcher.parties:
            key = (p['a'], p['p'])

            if key not in self.ping_state:
                self._ping_party(p['a'], p['p'])

            if self.ping_state.get(key) != "done":
                p['pd'] = "…"
            else:
                val = self.pings.get(key)
                p['pd'] = val if val is not None else "N/A"
        bs.timer(0.3, self.rebuild_list)
        
    def on_transition_in(self) -> None:
        super().on_transition_in()
        
        gnode = self.globalsnode
        gnode.camera_mode = 'rotate'
        bs.setmusic(bs.MusicType.ONLINE, continuous=True)
        if self.players == 0:
            self.join_text = Text(
                'Please join the activity to continue...',
                h_align=Text.HAlign.CENTER,
                scale=1.5,
            )
        else:
            self.refresh_timer = bs.Timer(3.0, self.refresh_parties, repeat=True)
            self.refresh_parties()
        # background to make
        # it look nice
        self.background = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('windowHSmallVMed'),
                'position': (50, 0),
                'scale': (1000, 1000),
                'color': (0.2, 0.2, 0.2),
                'opacity': 0.6,
            },
        )
        infoy = 30
        infox = 10
        # throw some controller info
        # on how to use the menu
        self.backinfo = bs.newnode(
                'text',
                attrs={
                    'text': (
                        f"{ba.charstr(ba.SpecialChar.RIGHT_BUTTON)} = "
                        f"{ba.charstr(ba.SpecialChar.BACK)}"
                    ),
                    'position': (infox, infoy + 50),
                    'scale': 2.0,
                    'color': (1, 1, 1),
                    'v_align': 'center',
                    'h_align': 'left',
                    'v_attach': 'bottom',
                    'h_attach': 'left',
                    'shadow': 0.5,
                    'flatness': 0.3,
                },
            )
        self.playinfo = bs.newnode(
                'text',
                attrs={
                    'text': (
                        f"{ba.charstr(ba.SpecialChar.LEFT_BUTTON)}, "
                        f"{ba.charstr(ba.SpecialChar.TOP_BUTTON)}, "
                        f"{ba.charstr(ba.SpecialChar.BOTTOM_BUTTON)} = "
                        f"{ba.charstr(ba.SpecialChar.PLAY_BUTTON)}"
                    ),
                    'position': (infox, infoy),
                    'scale': 1.5,
                    'color': (1, 1, 1),
                    'v_align': 'center',
                    'h_align': 'left',
                    'v_attach': 'bottom',
                    'h_attach': 'left',
                    'shadow': 0.5,
                    'flatness': 0.3,
                },
            )

    def up(self):
        if self.selected_index > 0:
            self.selected_index -= 1

            if self.selected_index < self.scroll_offset:
                self.scroll_offset -= 1

            self.rebuild_list()


    def down(self):
        if self.selected_index < len(self.fetcher.parties) - 1:
            self.selected_index += 1

            if self.selected_index >= self.scroll_offset + self.VISIBLE_ROWS:
                self.scroll_offset += 1

            self.rebuild_list()

    def back(self):
        self.session.setactivity(bs.newactivity(OnlineSelection))

    def select(self):
        if not self.fetcher.parties:
            return
        p = self.fetcher.parties[self.selected_index]
        bs.connect_to_party(p['a'], port=p['p'])
        
    @override
    def on_player_join(self, player: PlayerT) -> None:
        if self.join_text:
            self.join_text.node.delete()
        player.assigninput(
            (
                ba.InputType.JUMP_PRESS,
                ba.InputType.PUNCH_PRESS,
                ba.InputType.PICK_UP_PRESS,
            ),
            self.select,
        )
        player.assigninput(ba.InputType.UP_PRESS, self.up)
        player.assigninput(ba.InputType.DOWN_PRESS, self.down)
        player.assigninput(ba.InputType.BOMB_PRESS, self.back)
        self.refresh_timer = bs.Timer(3.0, self.refresh_parties, repeat=True)
        self.refresh_parties()
        
    def on_begin(self) -> None:
        super().on_begin()
