#!/usr/bin/env python3
# Copyright (C) 2022, Will Hedgecock
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations
from ..parts import PartType, PartSubType
from .Material import Material
from .Mission import Mission, MissionStage
from .Activation import ActivationProfile
from .Power import PowerProfile
from typing import Any, Dict, List, Tuple, TypeVar, Union
from symcad.core import SymPart
from copy import deepcopy
from sympy import Expr
import abc

BasePartSubType = TypeVar('BasePartSubType', bound='BasePart')

class BasePart(metaclass=abc.ABCMeta):
   """TODO: Documentation
   """


   # Public attributes ----------------------------------------------------------------------------

   name: str
   """Unique identifying name of the `BasePart` instance."""

   types: PartType
   """Abstract types of the underlying `BasePart` instance."""

   subtypes: PartSubType
   """TODO:"""

   sympart: SymPart
   """Underlying `SymPart` representing the geometry and geometric properties
   of the `BasePart`."""

   configured_stage: MissionStage
   """Mission stage for which the BasePart is currently configured."""

   present_stages: List[str]
   """List of mission stages for which the BasePart is present."""

   power_usage_profile: Union[PowerProfile, None]
   """Power usage profile."""

   activation_profile: Union[ActivationProfile, None]
   """Power activation profile."""


   # Constructor ----------------------------------------------------------------------------------

   def __init__(self, identifier: str,
                      part_type: PartType,
                      part_subtype: PartSubType,
                      part: SymPart,
                      mission: Mission,
                      power_profile: PowerProfile,
                      extra_parameters: Dict[str, Any]) -> None:
      """Initializes an instance of a `BasePart`.

      TODO: Documentation

      Parameters
      ----------
      identifier : `str`
         Unique, identifying name for the BasePart.
      """
      super().__init__()
      self.name = identifier
      self.types = part_type
      self.subtypes = part_subtype
      self.sympart = part
      self.configured_stage = mission.stages[0] if len(mission.stages) > 0 else None
      self.present_stages = [stage.name for stage in mission.stages]
      self.power_usage_profile = power_profile
      self.activation_profile = None
      self.sympart.set_orientation(roll_deg=extra_parameters.get('roll_rotation_deg', 0.0),
                                   pitch_deg=extra_parameters.get('pitch_rotation_deg', 0.0),
                                   yaw_deg=extra_parameters.get('yaw_rotation_deg', 0.0))


   # Built-in method implementations --------------------------------------------------------------

   def __repr__(self) -> str:
      return self.name

   def __eq__(self, other: BasePart) -> bool:
      for key, val in self.__dict__items():
         if key != 'name' and (key not in other.__dict__ or val != getattr(other, key)):
            return False
      return type(self) == type(other)

   def __copy__(self) -> BasePartSubType:
      copy = self.__class__.__new__(self.__class__)
      copy.__dict__.update(self.__dict__)
      return copy

   def __deepcopy__(self, memo) -> BasePartSubType:
      copy = self.__class__.__new__(self.__class__)
      memo[id(self)] = copy
      for key, val in self.__dict__.items():
         setattr(copy, key, deepcopy(val, memo))
      return copy


   # Public methods -------------------------------------------------------------------------------

   def clone(self: BasePartSubType) -> BasePartSubType:
      """Returns an exact clone of this `BasePart` instance."""
      return deepcopy(self)


   def set_activation_profile(self, activation_profile: ActivationProfile) -> BasePartSubType:
      """TODO:
      """
      self.activation_profile = activation_profile
      return self


   def set_discrete_choices(self, choices: Dict[PartType, Material]) -> BasePartSubType:
      """TODO:
      """
      if PartType.BATTERY in self.types:
         self.set_battery_cell_type(choices[PartType.BATTERY])
      if PartType.CONTAINER in self.types:
         self.set_structural_material(choices[PartType.CONTAINER])
      if PartType.PRESSURIZED in self.types:
         self.set_structural_material(choices[PartType.PRESSURIZED])
      if PartType.DYNAMIC_BUOYANCY in self.types:
         self.set_incompressible_fluid_type(choices[PartType.DYNAMIC_BUOYANCY])
         self.set_structural_material(choices[PartType.CONTAINER])
      if PartType.FAIRING in self.types:
         self.set_structural_material(choices[PartType.FAIRING])
      if PartType.LIFT_GENERATION in self.types:
         self.set_structural_material(choices[PartType.CONTAINER])
      if PartType.PROPULSION in self.types and PartSubType.ACTIVE not in self.subtypes:
         self.set_fluid_type(choices[PartType.PROPULSION])
         self.set_structural_material(choices[PartType.CONTAINER])
      if PartType.PITCH_CONTROL in self.types:
         self.set_weight_material(choices[PartType.PITCH_CONTROL])
         self.set_structural_material(choices[PartType.CONTAINER])
      if PartType.ROLL_CONTROL in self.types:
         self.set_weight_material(choices[PartType.ROLL_CONTROL])
         self.set_structural_material(choices[PartType.CONTAINER])
      if PartType.STATIC_WEIGHT in self.types:
         self.set_weight_material(choices[PartType.STATIC_WEIGHT])
      if PartType.STATIC_BUOYANCY in self.types:
         self.set_buoyancy_material(choices[PartType.STATIC_BUOYANCY])
      return self


   def list_attachment_points(self: BasePartSubType) -> Dict[str, Tuple[float, float, float]]:
      return { point.name: (point.x, point.y, point.z) for point in self.sympart.attachment_points }


   def add_attachment_point(self: BasePartSubType,
                            attachment_point_id: str, *,
                            x: Union[float, Expr],
                            y: Union[float, Expr],
                            z: Union[float, Expr]) -> BasePartSubType:
      """TODO:"""
      self.sympart.add_attachment_point(attachment_point_id, x=x, y=y, z=z)
      return self


   def attach(self: BasePartSubType,
              local_attachment_id: str,
              remote_part: BasePart,
              remote_attachment_id: str) -> BasePartSubType:
      """TODO:"""
      self.sympart.attach(local_attachment_id, remote_part.sympart, remote_attachment_id)
      return self


   def set_geometry(self: BasePartSubType, **kwargs) -> BasePartSubType:
      self.sympart.set_geometry(**kwargs)
      return self


   def remove_from_mission_stage(self: BasePartSubType, stage: MissionStage) -> BasePartSubType:
      """TODO:
      """
      if stage.name in self.present_stages:
         self.present_stages.remove(stage.name)


   def set_mission_stage(self: BasePartSubType, stage: MissionStage) -> BasePartSubType:
      """Sets the mission stage for which all subsequent requests for a BasePart property
      should be retrieved.

      The concrete, overriding `BasePart` class may use this `stage` to alter its
      underlying properties.

      Parameters
      ----------
      stage : `MissionStage`
         Mission stage for which the BasePart should be configured.

      Returns
      -------
      self : `BasePart`
         The current BasePart being manipulated.
      """
      self.configured_stage = stage
      return self


   def set_state(self: BasePartSubType,
                 state_names: Union[List[str], None]) -> BasePartSubType:
      """Sets the geometric configuration of the BasePart according to the indicated
      `state_names`.

      The concrete, overriding `BasePart` class may use these `state_names` to alter its
      underlying geometric properties.

      Parameters
      ----------
      state_names : `Union[List[str], None]`
         List of geometric states for which the BasePart should be configured. If set to
         `None`, the BasePart will be configured in its default state.

      Returns
      -------
      self : `BasePart`
         The current BasePart being manipulated.
      """
      self.sympart.set_state(state_names)
      return self


   # BasePart properties ---------------------------------------------------------------------

   @property
   def mass(self) -> Union[float, Expr]:
      """Mass (in `kg`) of the BasePart (read-only)."""
      return self.sympart.mass

   @property
   def material_volume(self) -> Union[float, Expr]:
      """Material volume (in `m^3`) of the BasePart (read-only)."""
      return self.sympart.material_volume

   @property
   def displaced_volume(self) -> Union[float, Expr]:
      """Displaced volume (in `m^3`) of the BasePart (read-only)."""
      return self.sympart.displaced_volume

   @property
   def surface_area(self) -> Union[float, Expr]:
      """Surface/wetted area (in `m^2`) of the BasePart (read-only)."""
      return self.sympart.surface_area

   @property
   def center_of_gravity(self) -> Tuple[Union[float, Expr],
                                        Union[float, Expr],
                                        Union[float, Expr]]:
      """Center of gravity (in `m`) of the oriented BasePart (read-only)."""
      return self.sympart.oriented_center_of_gravity

   @property
   def center_of_buoyancy(self) -> Tuple[Union[float, Expr],
                                         Union[float, Expr],
                                         Union[float, Expr]]:
      """Center of buoyancy (in `m`) of the oriented BasePart (read-only)."""
      return self.sympart.oriented_center_of_buoyancy

   @property
   def allowable_voltage_range(self) -> Tuple[float, float]:
      """Allowable range of input voltages (in `V`) of the BasePart (read-only)."""
      return self.power_usage_profile.input_voltage_range \
         if self.power_usage_profile is not None else None

   @property
   def required_voltage(self) -> Union[float, Expr]:
      """Required supply voltage (in `V`) of the BasePart (read-only)."""
      return self.power_usage_profile.input_voltage \
         if self.power_usage_profile is not None else None

   @property
   def power_consumption(self) -> Union[float, Expr]:
      """Total power consumption (in `Wh`) of the BasePart (read-only)."""
      if self.power_usage_profile is not None and self.power_usage_profile.get_wattage() > 0.0:
         if self.activation_profile is None:
            raise RuntimeError('Part "{}" was specified as drawing power but no power activation '
                               'profile was set for the current Mission Stage "{}"'
                               .format(self.name, self.configured_stage.name))
         else:
            return self.activation_profile.get_num_total_seconds_activated(self.configured_stage) \
               * self.power_usage_profile.get_wattage() / 3600.0
      else:
         return 0.0
