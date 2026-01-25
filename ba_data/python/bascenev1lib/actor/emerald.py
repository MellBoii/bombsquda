"""Actor for a chaos emerald."""
import random
import bascenev1 as bs
from typing import Any, Sequence, override
from bascenev1lib.gameutils import SharedObjects

# Note: Need to suppress an undefined variable here because our pylint
# plugin clears type-arg declarations (which we don't require to be
# present at runtime) but keeps parent type-args (which we sometimes use
# at runtime).
class TouchedMsg:
    pass
    
class EmeraldActor(bs.Actor):
    """
    The actor for a chaos emerald.
    To every actor that touches it, it gives out a
    EmeraldMessage() with the type we have.
    """
    node: bs.Node
    
    def __init__(
        self,
        position: Sequence[float] = (0.0, 5.0, 0.0),
    ):
        super().__init__()
        self.mesh = bs.getmesh('chaosEmerald')
        self.texname = self.get_fairest_emerald()
        self.tex = bs.gettexture(self.texname)
        self.material = bs.Material()
        self.emeralds_die = True
        if self.emeralds_die:
            self.deathTimer = bs.Timer(5, self.scheduled_die_message)
        self.material.add_actions(
            conditions=('they_have_material', SharedObjects.get().player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True),
                ('message', 'our_node', 'at_connect', TouchedMsg()),
            ),
        )
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'box',
                'body_scale': 0.3,
                'position': position,
                'mesh': self.mesh,
                'light_mesh': self.mesh,
                'shadow_size': 0.5,
                'color_texture': self.tex,
                'reflection': 'powerup',
                'reflection_scale': [1.0],
                'materials': (self.material, SharedObjects.get().object_material),
            },
        )
        bs.animate(self.node, 'mesh_scale', {0: 0, 0.5: 0.7})
        
    def scheduled_die_message(self):
        if not self.node:
            return
        self.handlemessage(bs.DieMessage())
        
    def get_fairest_emerald(self) -> str:
        from bascenev1lib.actor.spaz import Spaz
        all_types = [f"emerald{i}" for i in range(1, 8)]

        bs.debprint(f"\n{self}: Calculating fairest emerald...")

        # Initialize counts
        counts = {e: 0 for e in all_types}

        # Count emeralds from *all* spazzes in the activity
        # (not just players; bots too)
        for node in bs.getnodes():
            actor = node.getdelegate(Spaz)
            
            if not actor:
                continue

            emeralds = getattr(actor, "emeralds", [])
            bs.debprint(f"  Spaz {actor} has: {emeralds}")

            for e in emeralds:
                if e in counts:
                    counts[e] += 1

        bs.debprint("  Ownership counts:")
        for e, c in counts.items():
            bs.debprint(f"    {e}: {c}")

        min_count = min(counts.values())
        bs.debprint(f"  Minimum ownership count: {min_count}")

        candidates = [e for e, c in counts.items() if c == min_count]
        bs.debprint(f"  Candidate emeralds: {candidates}")

        chosen = random.choice(candidates)
        bs.debprint(f"  >>> Selected emerald: {chosen}\n")

        return chosen
    # msg must be any so we don't get circular import issues
    # altho maybe this WILL allow msg to be anything...
    def _handle_hit(self, msg: Any) -> None:
        if msg.hit_type == 'explosion': # exploded? just die
            bs.debprint(f'{self} was hit by a explosion, so it will die now')
            self.scheduled_die_message()
        # likely hit by a punch; apply impulse
        self.node.handlemessage(
            'impulse',
            msg.pos[0],
            msg.pos[1],
            msg.pos[2],
            msg.velocity[0],
            msg.velocity[1],
            msg.velocity[2],
            msg.magnitude,
            msg.velocity_magnitude,
            msg.radius,
            0,
            msg.velocity[0],
            msg.velocity[1],
            msg.velocity[2],
        )
        
    @override
    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired
        if isinstance(msg, bs.DieMessage):
            if self.node:
                if msg.immediate:
                    self.node.delete()
                else:
                    bs.animate(self.node, 'mesh_scale', {0: 0.7, 0.1: 0})
                    bs.timer(0.1, self.node.delete)
                self.deathTimer = None
        elif isinstance(msg, TouchedMsg):
            if not self.node:
                return
            toucher = bs.getcollision().opposingnode
            isspaz = toucher.getnodetype() == 'spaz'
            actor = toucher.getdelegate(bs.Actor)
            if not toucher:
                bs.debprint(f'{self}: no toucher')
                return
            if not actor:
                bs.debprint(f'{self}: no toucher')
                return
            if isspaz:
                bs.debprint(f'{self}: A spaz touched us, so we\'re gonna die.')
                from bascenev1lib.actor.spaz import EmeraldMessage
                toucher.handlemessage(EmeraldMessage(self.texname))
                if not actor.issuper: # FIXME: make the spaz tell us if we should die?
                    self.handlemessage(bs.DieMessage())
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage(immediate=True))
        elif isinstance(msg, bs.HitMessage):
            self._handle_hit(msg)