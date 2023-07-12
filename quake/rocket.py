# I'm too lazy to work with this mod :(
# type: ignore
"""Quake Game Rocket weapon"""
from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bauiv1 as bui
import bascenev1 as bs

from bascenev1lib.actor.bomb import Blast
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Optional, Any
    from bascenev1lib.actor.spaz import Spaz

STORAGE_ATTR_NAME = f'_shared_{__name__}_factory'


class RocketFactory:
    """Quake Rocket factory"""

    def __init__(self) -> None:
        self.ball_material = bs.Material()

        self.ball_material.add_actions(
            conditions=((('we_are_younger_than', 5), 'or',
                         ('they_are_younger_than', 5)), 'and',
                        ('they_have_material',
                         SharedObjects.get().object_material)),
            actions=('modify_node_collision', 'collide', False))

        self.ball_material.add_actions(
            conditions=('they_have_material',
                        SharedObjects.get().pickup_material),
            actions=('modify_part_collision', 'use_node_collide', False))

        self.ball_material.add_actions(actions=('modify_part_collision',
                                                'friction', 0))

        self.ball_material.add_actions(
            conditions=(('they_have_material',
                         SharedObjects.get().footing_material), 'or',
                        ('they_have_material',
                         SharedObjects.get().object_material)),
            actions=('message', 'our_node', 'at_connect', ImpactMessage()))

    @classmethod
    def get(cls):
        """Get factory if exists else create new"""
        activity = bs.getactivity()
        if hasattr(activity, STORAGE_ATTR_NAME):
            return getattr(activity, STORAGE_ATTR_NAME)
        factory = cls()
        setattr(activity, STORAGE_ATTR_NAME, factory)
        return factory


class RocketLauncher:
    """Very dangerous weapon"""

    def __init__(self):
        self.last_shot: Optional[int, float] = 0

    def give(self, spaz: Spaz) -> None:
        """Give spaz a rocket launcher"""
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

            mag = 10.0 / babase.Vec3(*direction).length()
            vel = [v * mag for v in direction]
            Rocket(position=spaz.node.position,
                   velocity=vel,
                   owner=spaz.getplayer(bs.Player),
                   source_player=spaz.getplayer(bs.Player),
                   color=spaz.node.color).autoretain()


class ImpactMessage:
    """Rocket touched something"""


class Rocket(bs.Actor):
    """Epic rocket from rocket launcher"""

    def __init__(self,
                 position=(0, 5, 0),
                 velocity=(1, 0, 0),
                 source_player=None,
                 owner=None,
                 color=(1.0, 0.2, 0.2)) -> None:
        super().__init__()
        self.source_player = source_player
        self.owner = owner
        self._color = color
        factory = RocketFactory.get()

        self.node = bs.newnode('prop',
                               delegate=self,
                               attrs={
                                   'position': position,
                                   'velocity': velocity,
                                   'mesh': bs.getmesh('impactBomb'),
                                   'body': 'sphere',
                                   'color_texture': bs.gettexture(
                                       'bunnyColor'),
                                   'mesh_scale': 0.2,
                                   'is_area_of_interest': True,
                                   'body_scale': 0.8,
                                   'materials': [
                                       SharedObjects.get().object_material,
                                       factory.ball_material]
                               })  # yapf: disable
        self.node.extra_acceleration = (self.node.velocity[0] * 200, 0,
                                        self.node.velocity[2] * 200)

        self._life_timer = bs.Timer(
            5, bs.WeakCall(self.handlemessage, bs.DieMessage()))

        self._emit_timer = bs.Timer(0.001, bs.WeakCall(self.emit), repeat=True)
        self.base_pos_y = self.node.position[1]

        bs.camerashake(0.2)

    def emit(self) -> None:
        """Emit a trace after rocket"""
        bs.emitfx(position=self.node.position,
                  scale=0.4,
                  spread=0.01,
                  chunk_type='spark')
        if not self.node:
            return
        self.node.position = (self.node.position[0], self.base_pos_y,
                              self.node.position[2])  # ignore y
        bs.newnode('explosion',
                   owner=self.node,
                   attrs={
                       'position': self.node.position,
                       'radius': 0.2,
                       'color': self._color
                   })

    def handlemessage(self, msg: Any) -> Any:
        """Message handling for rocket"""
        super().handlemessage(msg)
        if isinstance(msg, ImpactMessage):
            self.node.handlemessage(bs.DieMessage())

        elif isinstance(msg, bs.DieMessage):
            if self.node:
                Blast(position=self.node.position,
                      blast_radius=2,
                      source_player=self.source_player)

                self.node.delete()
                self._emit_timer = None

        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())
