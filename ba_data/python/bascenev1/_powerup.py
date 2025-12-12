# Released under the MIT License. See LICENSE for details.
#
"""Powerup related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from typing import Sequence

    import bascenev1
import babase as ba


@dataclass
class PowerupMessage:
    """A message telling an object to accept a powerup.

    This message is normally received by touching a
    bascenev1.PowerupBox.
    """

    poweruptype: str
    """The type of powerup to be granted (a string).
       See bascenev1.Powerup.poweruptype for available type values."""

    sourcenode: bascenev1.Node | None = None
    """The node the powerup game from, or None otherwise.
       If a powerup is accepted, a bascenev1.PowerupAcceptMessage should be
       sent back to the sourcenode to inform it of the fact. This will
       generally cause the powerup box to make a sound and disappear or
       whatnot."""


@dataclass
class PowerupAcceptMessage:
    """A message informing a bascenev1.Powerup that it was accepted.

    This is generally sent in response to a bascenev1.PowerupMessage to
    inform the box (or whoever granted it) that it can go away.
    """


def get_default_powerup_distribution() -> Sequence[tuple[str, int]]:
    """Standard set of powerups."""
    debug_powerup = None
    return (
        ('triple_bombs', 9999 if debug_powerup == 'triple_bombs' else 3),
        ('ice_bombs', 9999 if debug_powerup == 'ice_bombs' else 3),
        ('punch', 9999 if debug_powerup == 'punch' else 3),
        ('impact_bombs', 9999 if debug_powerup == 'impact_bombs' else 3),
        ('land_mines', 9999 if debug_powerup == 'land_mines' else 2),
        ('sticky_bombs', 9999 if debug_powerup == 'sticky_bombs' else 3),
        ('shield', 9999 if debug_powerup == 'shield' else 2),
        ('health', 9999 if debug_powerup == 'health' else 2),
        ('curse', 9999 if debug_powerup == 'curse' else 1),
        ('metal', 9999 if debug_powerup == 'metal' else 1),
        ('random', 9999 if ba.app.config.get("squda_gamblingmode", True) else 1),
        ('spongebob', 9999 if debug_powerup == 'spongebob' else 2),
        ('strong', 9999 if debug_powerup == 'strong' else 3),
    )
