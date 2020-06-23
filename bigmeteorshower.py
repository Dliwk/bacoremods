# ba_meta require api 6

from __future__ import annotations

from typing import TYPE_CHECKING

from bastd.game.meteorshower import MeteorShowerGame, Player, Team
from bastd.actor.bomb import Bomb

if TYPE_CHECKING:
    from typing import Sequence


# ba_meta export game
class BigMeteorShowerGame(MeteorShowerGame):
    name = 'Big Meteor Shower'

    def _drop_bomb(self, position: Sequence[float], velocity: Sequence[float]) -> None:
        Bomb(position=position, velocity=velocity, bomb_scale=3).autoretain()
