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
from typing import Dict, Optional, Tuple, Union
from enum import IntEnum, auto, unique

@unique
class OptimizationParameter(IntEnum):
   """TODO: Documentation

   Mass: Target or minimum or maximum mass
   Pitch Maneuverability: Target rate of pitch change
   Directional Maneuverability: Target rate of horizontal direction change
   Stability: Target or minimum Cb/Cg separation
   Volume: Target or minimum or maximum volume
   Power Consumption: Target or minimum average total power consumption
   Power Reserve: Target or minimum or maximum remaining power reserve
   Mission Duration: Target or minimum or maximum mission duration
   Transit Distance: Target or minimum or maximum transit distance
   """
   MASS = auto()
   VOLUME = auto()
   VOLUME_TO_MASS_RATIO = auto()
   PITCH_MANEUVERABILITY = auto()
   DIRECTIONAL_MANEUVERABILITY = auto()
   STABILITY = auto()
   POWER_CONSUMPTION = auto()
   POWER_RESERVE = auto()
   MISSION_DURATION = auto()
   TRANSIT_DISTANCE = auto()
   PRESSURE_VESSEL_MASS = auto()
   PRESSURE_VESSEL_VOLUME = auto()
   PRESSURE_VESSEL_VOLUME_TO_MASS = auto()

@unique
class OptimizationMode(IntEnum):
   """TODO: Documentation"""
   MINIMIZE = auto()
   MAXIMIZE = auto()
   TARGET = auto()


class MetricsIterator(object):

   def __init__(self, metrics: Metrics) -> None:
      super().__init__()
      self._metrics = metrics.optimizing_metrics
      self._index = 0

   def __next__(self) -> Tuple[OptimizationParameter, OptimizationMode, Union[float, None]]:
      if self._index < len(self._metrics):
         metric = list(self._metrics)[self._index]
         result = self._metrics[metric]
         self._index += 1
         return metric, result[0], result[1]
      raise StopIteration


class Metrics(object):
   """TODO: Documentation
   """

   # Public attributes ----------------------------------------------------------------------------

   optimizing_metrics: Dict[OptimizationParameter, Tuple[OptimizationMode, Union[float, None]]]
   """List of TODO"""


   # Constructor ----------------------------------------------------------------------------------

   def __init__(self) -> None:
      """TODO: Documentation"""
      super().__init__()
      self.optimizing_metrics = {}


   # Built-in methods -----------------------------------------------------------------------------

   def __iter__(self):
      return MetricsIterator(self)


   # Public methods -------------------------------------------------------------------------------

   def optimize_for(self, parameter: OptimizationParameter,
                          mode: OptimizationMode,
                          value: Optional[float] = None) -> None:
      self.optimizing_metrics[parameter] = (mode, value)
