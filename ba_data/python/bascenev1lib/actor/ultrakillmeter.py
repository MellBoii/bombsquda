"""Class for an Ultrakill-style meter"""
# WELCOME TO ULTRA JANK HELL!
import bascenev1 as bs
import babase as ba
# List of our ranks (a letter corresponding to a string and color).
SCORE_RANKS = {
    'D': (bs.Lstr(resource='ultrakillMeterRankD'), (1, 0.5, 0)),
    'C': (bs.Lstr(resource='ultrakillMeterRankC'), (0, 0.8, 0.2)),
    'B': (bs.Lstr(resource='ultrakillMeterRankB'), (0.8, 0.8, 0)),
    'A': (bs.Lstr(resource='ultrakillMeterRankA'), (1, 0.5, 0)),
    'S': (bs.Lstr(resource='ultrakillMeterRankS'), (1, 0.3, 0.3)),
    'SS': (bs.Lstr(resource='ultrakillMeterRankSS'), (1, 0.1, 0.1)),
    'SSS': (bs.Lstr(resource='ultrakillMeterRankSSS'), (1, 0, 0)),
    'U': (bs.Lstr(resource='ultrakillMeterRankU'), (1.2, 1.2, 0)),
    None: ('', (0, 0, 0)),
}
RANK_ORDER = [None, 'D', 'C', 'B', 'A', 'S', 'SS', 'SSS', 'U']

class UltrakillMeter(bs.Actor):
    """
    A style-meter based on Ultrakill's.
    It handles ranking and a bar that depletes over time.
    WARNING: The bar depends on the width of the window.
    So make sure it isn't too wide or too skinny.
    """

    # Determines the freshness of a player.
    # This should be determined by if they're swapping kill methods
    # (bomb, then punch, then back to bomb,
    # etc, so they don't just punch infinitely for points).
    freshness: float = 1.5

    # Multiplies the amount of points you get.
    # This should be determined by a 
    # Spaz being mid-air and other factors.
    multiplier: int = 1

    def __init__(
        self, 
        position: tuple[float, float] = (400, 0),
        scale: tuple[float, float] = (480, 600),
    ):
        super().__init__()
        self.texts = []
        self.bar_timer: bs.Timer | None = None
        self._bar: bs.Node | None = None
        self._rank_text: bs.Node | None = None
        self._rank: str | None = None
        self.node = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('windowHSmallVMed'),
                'position': position,
                'scale': scale,
                'color': (0.2, 0.2, 0.2),
                'opacity': 0.6,
                'absolute_scale': True,
            },
            delegate=self,
        )
        width = scale[0] - 25
        height = 15
        barscale = 0.8
        self._width = width * barscale
        self._height = height * barscale
        self._bar_width = 10 * barscale
        self._bar_height = height * barscale
        self._bar_tex = self._backing_tex = bs.gettexture('bar')
        self.score: int = 0
        self._rank_index = 0  # corresponds to None
        self.text_spacing = 30

    def create_bar(self):
        ps = self.node.position
        sc = self.node.scale
        self._backing = bs.NodeActor(
            bs.newnode(
                'image',
                attrs={
                    'scale': (self._width, self._height),
                    'opacity': 1.0,
                    'color': (0.1, 0.1, 0.1),
                    'texture': self._backing_tex,
                },
            )
        )

        self._barcolor = (1, 0, 0)
        self._bar = bs.NodeActor(
            bs.newnode(
                'image',
                attrs={
                    'opacity': 0.7,
                    'color': (0.8, 0.8, 0.8),
                    'texture': self._bar_tex,
                },
            )
        )

        self._bar_scale = bs.newnode(
            'combine',
            owner=self._bar.node,
            attrs={
                'size': 2,
                'input0': self._bar_width,
                'input1': self._bar_height,
            },
        )
        assert self._bar.node
        self._bar_scale.connectattr('output', self._bar.node, 'scale')
        self._bar_position = bs.newnode(
            'combine',
            owner=self._bar.node,
            attrs={
                'size': 2, 
                'input0': self.node.position[0] - 25, 
                'input1': self.node.position[1] + self.node.scale[1] * 0.35
            },
        )
        self._bar_position.connectattr('output', self._bar.node, 'position')
        self._bar_position.connectattr('output', self._backing.node, 'position')

    def add_bar_length(self, length: int | float):
        if self._bar is None:
            self.create_bar()
        if self._bar_scale is not None:
            self._bar_scale.input0 += length
            self._bar_width += length
    
    def set_bar_length(self, length: int | float):
        if self._bar is None:
            self.create_bar()
        if self._bar_scale is not None:
            self._bar_scale.input0 = length
            self._bar_width = length
    
    def style_text(
        self, 
        styletext: bs.Lstr | str, 
        points: int = 30,
        color: tuple[float, float, float] = (1, 1, 1),
    ):
        y = self.node.scale[1] * 0.28
        for text in self.texts:
            y -= self.text_spacing
        ourpos = self.node.position
        textnode = bs.newnode(
            'text',
            attrs={
                'text': styletext,
                'position': (ourpos[0] - 180, ourpos[1] + y),
                'color': color,
                'h_align': 'left',
                'v_align': 'center',
                'scale': 1.0,
                'maxwidth': self.node.scale[0] - 180,
            },
        )
        self.texts.append(textnode)
        self.on_score_callback(points)
        bs.timer(3.5, lambda: self.delete_text(textnode))

    def delete_text(self, textnode):
        if textnode in self.texts:
            textnode.delete()
            self.texts.remove(textnode)
        for textnode in self.texts:
            textnode.position = (textnode.position[0], textnode.position[1] + self.text_spacing)

    def on_score_callback(self, newscore):
        self.score += newscore
        if self.bar_timer is None:
            self.bar_timer = bs.Timer(0.1, self.bar_tick, repeat=True)
        self.add_bar_length(newscore)
   
    def _apply_rank(self):
        rank = RANK_ORDER[self._rank_index]
        self._rank = rank
        rank_lstr, color = SCORE_RANKS[rank]
        self.set_rank(rank_lstr, color)
    
    def bar_tick(self):
        """Slowly reduce the bar length over time."""
        # Rank up
        if self._bar_width >= self._width and self._rank_index < len(RANK_ORDER) - 1:
            self._rank_index += 1
            self._apply_rank()
            self.set_bar_length(50)
        
        # Decrease bar length RAPIDLY if over the limit
        if self._bar_width >= self._width:
            self.add_bar_length(-10)

        # Rank down
        if self._bar_width <= 1 and self._rank_index > 0:
            self._rank_index -= 1
            self._apply_rank()
            self.set_bar_length(self._width - 20)
        # reduce the bar length
        self.add_bar_length(-1)
    
    def set_rank(self, rank: str | bs.Lstr | None = None, color: tuple[float, float, float] = (1, 1, 1)):
        big = 1.7
        normal = 1.3
        animdict = {
            0: normal,
            0.05: big,
            0.1: big,
            0.5: normal,
        }
        if not self._rank_text:
            sc = self.node.scale
            ps = self.node.position
            self._rank_text = bs.newnode(
                'text',
                attrs={
                    'text': rank,
                    'position': (ps[0] - 30, ps[1] + sc[1] * 0.4),
                    'color': color,
                    'h_align': 'center',
                    'v_align': 'center',
                    'scale': normal,
                    'maxwidth': 200,
                },
            )
            bs.animate(
                self._rank_text, 
                'scale',
                animdict
            )
        else:
            self._rank_text.text = rank
            self._rank_text.color = color
            # Scale up our text briefly to show that 
            # we've ranked up.
            bs.animate(
                self._rank_text, 
                'scale',
                animdict
            )