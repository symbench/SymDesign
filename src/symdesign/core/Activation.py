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
from .Mission import MissionStage
from typing import Dict, Union
from enum import IntEnum, unique

# ACTIVATION INTERVAL ENUMERATION -------------------------------------------------------------------------------------

@unique
class ActivationInterval(IntEnum):
   DEACTIVATED = 0
   PER_MISSION_STAGE = 1
   PER_MONTH = 2
   PER_WEEK = 3
   PER_DAY = 4
   PER_HOUR = 5


# Class to hold the power profile for each mission stage
class MissionStageActivationProfile(object):
   num_activations: int
   activation_interval: ActivationInterval
   duration_percent_per_activation: Union[float, None]
   activation_duration_seconds: Union[int, None]

   def __init__(self, **kwargs) -> None:
      super().__init__()
      self.num_activations = kwargs.get('num_activations', 0)
      self.activation_interval = kwargs.get('activation_interval', ActivationInterval.DEACTIVATED)
      self.duration_percent_per_activation = kwargs.get('duration_percent_per_activation', None)
      self.activation_duration_seconds = kwargs.get('activation_duration_seconds', None)



# ACTIVATION PROFILE CLASS --------------------------------------------------------------------------------------------
# EXAMPLE: Four 2-minute activations per hour:
#    num_activations = 4
#    activation_interval = PER_HOUR
#    duration_percent_per_activation = 2.0 / 60.0

class ActivationProfile(object):

   # Aggregate power usage profile parameters
   name: str
   profiles: Dict[str, MissionStageActivationProfile]

   # Constructor
   def __init__(self, name) -> None:
      super().__init__()
      self.name = name
      self.profiles = {}

   # Methods to construct the power usage profile
   def add_mission_stage_profile_percentage(self, stage: MissionStage, num_activations: int, activation_interval: ActivationInterval, duration_percent_per_activation: float) -> ActivationProfile:

      # Verify that the specified mission stage exists
      if duration_percent_per_activation > 1.0:
         raise ValueError('Percentage value ({}) appears to be greater than 100% (1.0)'.format(duration_percent_per_activation))

      # Add the specified profile to the list of mission stage profiles
      self.profiles[stage.name] = MissionStageActivationProfile(num_activations=num_activations, activation_interval=activation_interval, duration_percent_per_activation=duration_percent_per_activation)
      return self

   def add_mission_stage_profile_concrete(self, stage: MissionStage, num_activations: int, activation_interval: ActivationInterval, activation_duration_seconds: int) -> ActivationProfile:

      # Add the specified profile to the list of mission stage profiles
      self.profiles[stage.name] = MissionStageActivationProfile(num_activations=num_activations, activation_interval=activation_interval, activation_duration_seconds=activation_duration_seconds)
      return self

   def add_mission_stage_profile_deactivated(self, stage: MissionStage) -> ActivationProfile:

      # Add the specified profile to the list of mission stage profiles
      self.profiles[stage.name] = MissionStageActivationProfile(activation_interval=ActivationInterval.DEACTIVATED)
      return self

   def get_num_total_seconds_activated(self, stage: MissionStage) -> float:

      # Compute the total number of active seconds given the current mission stage and duration
      profile = self.profiles[stage.name]
      duration = stage.target_duration
      if profile.activation_interval == ActivationInterval.DEACTIVATED:
         return 0
      elif profile.activation_interval == ActivationInterval.PER_MISSION_STAGE:
         num_intervals = 1.0
         total_seconds_per_interval = duration
      elif profile.activation_interval == ActivationInterval.PER_MONTH:
         total_seconds_per_interval = 60.0 * 60.0 * 24.0 * 30.0
         num_intervals = duration / total_seconds_per_interval
      elif profile.activation_interval == ActivationInterval.PER_WEEK:
         total_seconds_per_interval = 60.0 * 60.0 * 24.0 * 7.0
         num_intervals = duration / total_seconds_per_interval
      elif profile.activation_interval == ActivationInterval.PER_DAY:
         total_seconds_per_interval = 60.0 * 60.0 * 24.0
         num_intervals = duration / total_seconds_per_interval
      elif profile.activation_interval == ActivationInterval.PER_HOUR:
         total_seconds_per_interval = 60.0 * 60.0
         num_intervals = duration / total_seconds_per_interval
      seconds_activated_per_interval = (profile.num_activations * profile.activation_duration_seconds) \
         if profile.activation_duration_seconds is not None else \
            (profile.num_activations * profile.duration_percent_per_activation * total_seconds_per_interval)
      return seconds_activated_per_interval * num_intervals
