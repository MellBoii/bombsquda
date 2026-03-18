# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to classic game tips.

These can be shown at opportune times such as between rounds."""
from __future__ import annotations

from typing import TYPE_CHECKING

import babase

if TYPE_CHECKING:
    pass

# note; should move this to lstrs instead of strs that get translated into lstrs
# - mell
def get_all_tips() -> list[str]:
    """Return the complete list of tips."""
    tips = ['tipText' + str(i + 1) + '' for i in range(7)]
    tips.extend('tipGarbage' + str(i + 1) + '' for i in range(15))
    return tips
