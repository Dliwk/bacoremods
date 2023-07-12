# I'm too lazy to work with this mod :(
# type: ignore
"""Quake Game Rocket weapon"""
from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bauiv1 as bui
import bascenev1 as bs

from bascenev1lib.actor.playerspaz import PlayerSpaz

if TYPE_CHECKING:
    from typing import Optional, Any
    from bascenev1lib.actor.spaz import Spaz

STORAGE_ATTR_NAME = f'_shared_{__name__}_factory'


class Railgun:
    """Very dangerous weapon"""

    def __init__(self) -> None:
        self.last_shot: Optional[int, float] = 0

    def give(self, spaz: Spaz) -> None:
        """Give spaz a railgun"""
        spaz.punch_callback = self.shot
        self.last_shot = bs.time()

    # FIXME
    # noinspection PyUnresolvedReferences
    def shot(self, spaz: Spaz) -> None:
        """Release a rocket"""
        time = bs.time()
        if time - self.last_shot > 0.6:
            self.last_shot = time
            center = spaz.node.position_center
            forward = spaz.node.position_forward
            direction = [
                center[0] - forward[0], forward[1] - center[1],
                center[2] - forward[2]
            ]
            direction[1] = 0.0

            RailBullet(position=spaz.node.position,
                       direction=direction,
                       owner=spaz.getplayer(bs.Player),
                       source_player=spaz.getplayer(bs.Player),
                       color=spaz.node.color).autoretain()


class TouchedToSpazMessage:
    """I hit!"""

    def __init__(self, spaz) -> None:
        self.spaz = spaz


class RailBullet(bs.Actor):
    """Railgun bullet"""

    def __init__(self,
                 position=(0, 5, 0),
                 direction=(0, 2, 0),
                 source_player=None,
                 owner=None,
                 color=(1, 1, 1)) -> None:
        super().__init__()
        self._color = color

        self.node = bs.newnode('light',
                               delegate=self,
                               attrs={
                                   'position': position,
                                   'color': self._color,
                                   'radius': 0,
                               })
        # bs.animate(self.node, 'radius', {0: 0, 0.1: 0.5, 0.5: 0})

        self.source_player = source_player
        self.owner = owner
        self._life_timer = bs.Timer(
            0.5, bs.WeakCall(self.handlemessage, bs.DieMessage()))

        pos = position
        vel = tuple(i / 5 for i in babase.Vec3(direction).normalized())
        ps = []
        for _ in range(500):  # Optimization :(
            node = bs.newnode('explosion',
                              owner=self.node,
                              attrs={
                                  'position': pos,
                                  'radius': 0.2,
                                  'color': self._color
                              })
            pos = (pos[0] + vel[0], pos[1] + vel[1], pos[2] + vel[2])
            p = node.position
            touched = False
            for node in bs.getnodes():
                if not node or node.getnodetype() != 'spaz':
                    continue
                    # pylint: disable=invalid-name
                    # pylint: enable=invalid-name
                    # distance between node and line
                dist = (babase.Vec3(*p) - babase.Vec3(*node.position)).length()
                if dist < 1:
                    if node and node != self.owner and node.getdelegate(
                            PlayerSpaz, True).getplayer(bs.Player,
                                                        True) != self.owner:
                        touched = True
                    if node and node != self.owner and node.getdelegate(
                            PlayerSpaz, True).getplayer(
                                bs.Player, True).team != self.owner.team:
                        node.handlemessage(babase.FreezeMessage())
                        pos = self.node.position
                        hit_dir = (0, 10, 0)
                        from bascenev1lib.actor.bomb import Blast
                        Blast(position=node.position,
                              blast_radius=1,
                              source_player=self.source_player)
                        break
            if touched:
                break

                #node.handlemessage(
                #    bs.HitMessage(pos=pos,
                #                  magnitude=50,
                #                  velocity_magnitude=50,
                #                  radius=0,
                #                  srcnode=self.node,
                #                  source_player=self.source_player,
                #                  force_direction=hit_dir))

    def handlemessage(self, msg: Any) -> Any:
        super().handlemessage(msg)
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()

        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())
