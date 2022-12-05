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
from .GlobalCoordinate import GlobalCoordinate
from ..models.Oceanic import OceanicModels
from typing import Callable, List, Tuple, Union
from enum import Flag, auto
from functools import reduce
from sympy import Expr, Symbol
import math, numpy, pickle


class MissionTarget(Flag):
   MINIMUM_DISTANCE = auto()
   EXACT_DISTANCE = auto()
   MAXIMUM_DISTANCE = auto()
   MINIMUM_DURATION = auto()
   EXACT_DURATION = auto()
   MAXIMUM_DURATION = auto()
   HORIZONTAL_SPEED = auto()


class MissionStage(object):
   """TODO: Documentation
   """

   # Public attributes ----------------------------------------------------------------------------

   name: str
   """Unique identifying name of the mission stage."""

   targets: MissionTarget
   """Performance target for the current mission stage."""

   maximum_pitch_angle: float
   """Absolute value of the maximum pitch angle required to be achievable for the current
   mission stage (in `deg`)."""

   maximum_roll_angle: float
   """Absolute value of the maximum roll angle required to be achievable for the current
   mission stage (in `deg`)."""

   maximum_net_buoyancy: float
   """Maximum net buoyancy required to be achievable for the current mission stage (in `N` if
   greater than 1, otherwise in `%` of vehicle mass)."""

   minimum_duration: float
   """Minimum duration of the mission stage (in `s`)."""

   target_duration: Union[float, Expr]
   """Target duration of the mission stage (in `s`)."""

   maximum_duration: float
   """Maximum duration of the mission stage (in `s`)."""

   minimum_distance: float
   """Minimum transit distance of the mission stage (in `km`)."""

   target_distance: Union[float, Expr]
   """Actual transit distance of the mission stage (in `km`)."""

   maximum_distance: float
   """Maximum transit distance of the mission stage (in `km`)."""

   minimum_average_horizontal_speed: float
   """Minimum allowable average horizontal speed during the mission stage (in `m/s`)."""

   target_average_horizontal_speed: Union[float, Expr]
   """Target average horizontal speed during the mission stage (in `m/s`)."""

   maximum_average_horizontal_speed: float
   """Maximum allowable average horizontal speed during the mission stage (in `m/s`)."""

   maximum_depth: float
   """Maximum expected dive depth during the current mission stage (in `m`)."""

   average_latitude: float
   """Average vehicle latitude for the current mission stage (in `decimal degrees`)."""

   minimum_salinity: float
   """Minimum salinity of the surrounding water during the mission stage (in 'ppt')."""

   maximum_salinity: float
   """Maximum salinity of the surrounding water during the mission stage (in 'ppt')."""

   minimum_temperature: float
   """Minimum temperature of the surrounding water during the mission stage (in 'C')."""

   maximum_temperature: float
   """Maximum temperature of the surrounding water during the mission stage (in 'C')."""

   minimum_density: float
   """Minimum density of the surrounding water during the current mission stage (in `kg/m^3`)."""

   maximum_density: float
   """Maximum density of the surrounding water during the current mission stage (in `kg/m^3`)."""

   expected_transit_slope: float
   """Absolute value of the average pitch angle of the vehicle path during transit (in `deg`)."""

   maximum_ocean_current_speed: float
   """Maximum opposing speed of the ocean currents required to be achievable during the
   mission stage (in `m/s`)."""


   # Constructor ----------------------------------------------------------------------------------

   def __init__(self, stage_name: str, stage_targets: List[MissionTarget]) -> None:
      """TODO: Documentation"""
      super().__init__()
      if not stage_targets:
         raise RuntimeError('At least 1 MissionTarget must be specified for Mission Stage "{}"'
                            .format(stage_name))
      self.name = stage_name
      self.targets = reduce(lambda a, b: a | b, stage_targets)
      self.maximum_pitch_angle = None
      self.maximum_roll_angle = None
      self.maximum_net_buoyancy = None
      self.minimum_duration = None
      self.target_duration = None
      self.maximum_duration = None
      self.minimum_distance = None
      self.target_distance = None
      self.maximum_distance = None
      self.minimum_average_horizontal_speed = None
      self.target_average_horizontal_speed = None
      self.maximum_average_horizontal_speed = None
      self.maximum_depth = None
      self.average_latitude = None
      self.minimum_salinity = None
      self.maximum_salinity = None
      self.minimum_temperature = None
      self.maximum_temperature = None
      self.minimum_density = None
      self.maximum_density = None
      self.expected_transit_slope = 35.0
      self.maximum_ocean_current_speed = None


   # Public methods -------------------------------------------------------------------------------

   def load_waypoints_and_ocean_data(self, waypoints_path: str,
                                           bathymetry_model: Union[str, Callable, None],
                                           ocean_currents_model: Union[str, Callable, None],
                                           salinity_model: Union[str, Callable, None],
                                           temperature_model: Union[str, Callable, None]) -> None:
      """
      TODO: Documentation, indicate which parameters this will overwrite/load

      Bathymetry model should be npz: data[latIdx][lonIdx] = depth, or callable(lat, lon) -> -depth
      Salinity model should be npz: data[latIdx][lonIdx][depth] = salinity, or callable(lat, lon, depth) -> salinity
      Temperature model should be npz: data[latIdx][lonIdx][depth] = temperature, or callable(lat, lon, depth) -> temperature
      """

      # Load the bathymetry model
      if isinstance(bathymetry_model, str):
         bathymetry_data = numpy.load(bathymetry_model)
         bath_lats = numpy.array(bathymetry_data['latIndex'])
         bath_lons = numpy.array(bathymetry_data['lonIndex'])
         bath_depths = numpy.array(bathymetry_data['zMat'])
         def get_bathymetry(latitude: float, longitude: float) -> float:
            lat_index = numpy.abs(bath_lats - latitude).argmin()
            lon_index = numpy.abs(bath_lons - longitude).argmin()
            return -bath_depths[lat_index][lon_index]
      elif callable(bathymetry_model):
         def get_bathymetry(latitude: float, longitude: float) -> float:
            return -bathymetry_model(latitude, longitude)
      else:
         def get_bathymetry(_latitude: float, _longitude: float) -> float:
            return 0.0

      # Load the salinity model
      if isinstance(salinity_model, str):
         salinity_data = numpy.load(salinity_model)
         sal_lats = numpy.array(salinity_data['latIndex'])
         sal_lons = numpy.array(salinity_data['lonIndex'])
         sal_depths = numpy.array(salinity_data['depthIndex'])
         salinities = numpy.array(salinity_data['data'])
         def get_salinity(latitude: float, longitude: float, depth: float) -> float:
            lat_index = numpy.abs(sal_lats - latitude).argmin()
            lon_index = numpy.abs(sal_lons - longitude).argmin()
            depth_index = numpy.abs(sal_depths - depth).argmin()
            return salinities[lat_index][lon_index][depth_index]
      elif callable(salinity_model):
         def get_salinity(latitude: float, longitude: float, depth: float) -> float:
            return salinity_model(latitude, longitude, depth)
      else:
         def get_salinity(_latitude: float, _longitude: float, _depth: float) -> float:
            return -1.0

      # Load the temperature model
      if isinstance(temperature_model, str):
         temperature_data = numpy.load(temperature_model)
         temp_lats = numpy.array(temperature_data['latIndex'])
         temp_lons = numpy.array(temperature_data['lonIndex'])
         temp_depths = numpy.array(temperature_data['depthIndex'])
         temperatures = numpy.array(temperature_data['data'])
         def get_temperature(latitude: float, longitude: float, depth: float) -> float:
            lat_index = numpy.abs(temp_lats - latitude).argmin()
            lon_index = numpy.abs(temp_lons - longitude).argmin()
            depth_index = numpy.abs(temp_depths - depth).argmin()
            return temperatures[lat_index][lon_index][depth_index]
      elif callable(temperature_model):
         def get_temperature(latitude: float, longitude: float, depth: float) -> float:
            return temperature_model(latitude, longitude, depth)
      else:
         def get_temperature(_latitude: float, _longitude: float, _depth: float) -> float:
            return -100.0

      # Load the ocean currents model
      if isinstance(ocean_currents_model, str):
         ocean_currents_data = numpy.load(ocean_currents_model)
         curr_lats = numpy.array(ocean_currents_data['latIndex'])
         curr_lons = numpy.array(ocean_currents_data['lonIndex'])
         curr_depths = numpy.array(ocean_currents_data['depthIndex'])
         u_mean_data = numpy.array(ocean_currents_data['uMeanData'])
         u_std_data = numpy.array(ocean_currents_data['uStdData'])
         v_mean_data = numpy.array(ocean_currents_data['vMeanData'])
         v_std_data = numpy.array(ocean_currents_data['vStdData'])
         def get_ocean_current(latitude: float, longitude: float, depth: float) -> Tuple[float, float]:
            lat_index = numpy.abs(curr_lats - latitude).argmin()
            lon_index = numpy.abs(curr_lons - longitude).argmin()
            depth_index = numpy.abs(curr_depths - depth).argmin()
            return math.sqrt(
                     (numpy.abs(u_mean_data[depth_index, lat_index, lon_index]) + (2.0 * u_std_data[depth_index, lat_index, lon_index]))**2 +
                     (numpy.abs(v_mean_data[depth_index, lat_index, lon_index]) + (2.0 * v_std_data[depth_index, lat_index, lon_index]))**2)
      elif callable(ocean_currents_model):
         def get_ocean_current(latitude: float, longitude: float, depth: float) -> Tuple[float, float]:
            return ocean_currents_model(latitude, longitude, depth)
      else:
         def get_ocean_current(_latitude: float, _longitude: float, _depth: float) -> Tuple[float, float]:
            return 0.0

      # Iterate through all waypoints
      transit_distance = 0.0
      min_salinity = min_temp = min_latitude = 100.0
      max_salinity = max_temp = max_current = -100.0
      max_depth = self.maximum_depth if self.maximum_depth is not None else -100.0
      with open(waypoints_path, 'rb') as waypoint_file:
         waypoints = pickle.load(waypoint_file)
         waypoint, previous_waypoint = GlobalCoordinate(), GlobalCoordinate()
         if len(waypoints) > 0:
            previous_waypoint.set_llh(waypoints[0][0], waypoints[0][1], waypoints[0][2])
            min_latitude = max_latitude = previous_waypoint.latitude
            max_depth = max(max_depth, get_bathymetry(waypoints[0][0], waypoints[0][1]))
            min_salinity = get_salinity(waypoints[0][0], waypoints[0][1], 0.0)
            max_salinity = get_salinity(waypoints[0][0], waypoints[0][1], max_depth)
            min_temp = get_temperature(waypoints[0][0], waypoints[0][1], max_depth)
            max_temp = get_temperature(waypoints[0][0], waypoints[0][1], 0.0)
            max_current = get_ocean_current(waypoints[0][0], waypoints[0][1], 10.0)
            for i in range(1, len(waypoints)):
               waypoint.set_llh(waypoints[i][0], waypoints[i][1], waypoints[i][2])
               min_latitude = min(min_latitude, waypoint.latitude)
               max_latitude = max(max_latitude, waypoint.latitude)
               depth = get_bathymetry(waypoints[i][0], waypoints[i][1])
               max_depth = max(max_depth, depth)
               min_salinity = min(min_salinity, get_salinity(waypoints[i][0], waypoints[i][1], 0.0))
               max_salinity = max(max_salinity, get_salinity(waypoints[i][0], waypoints[i][1], depth))
               min_temp = min(min_temp, get_temperature(waypoints[i][0], waypoints[i][1], depth))
               max_temp = max(max_temp, get_temperature(waypoints[i][0], waypoints[i][1], 0.0))
               max_current = max(max_current, get_ocean_current(waypoints[i][0], waypoints[i][1], 10.0))
               transit_distance += waypoint.compute_distance(previous_waypoint)
               previous_waypoint.copy_from(waypoint)

      # Update a subset of the mission stage parameters
      self.targets |= MissionTarget.EXACT_DISTANCE
      if min_latitude < 100.0:
         self.average_latitude = 90.0 * (min_latitude + max_latitude) / math.pi
         self.target_distance = self.minimum_distance = self.maximum_distance = 0.001 * transit_distance
      if min_salinity >= 0.0 and min_salinity < 100.0:
         self.minimum_salinity = min_salinity
      if max_salinity >= 0.0 and max_salinity < 100.0:
         self.maximum_salinity = max_salinity
      if min_temp > -10.0 and min_temp < 100.0:
         self.minimum_temperature = min_temp
      if max_temp > -10.0 and max_temp < 100.0:
         self.maximum_temperature = max_temp
      if max_current >= 0.0:
         self.maximum_ocean_current_speed = max_current
      if max_depth >= 0.0:
         self.maximum_depth = max_depth


   def load_waypoints_and_custom_density(self, waypoints_path: str,
                                               bathymetry_model: Union[str, Callable, None],
                                               ocean_currents_model: Union[str, Callable, None],
                                               density_model: Union[str, Callable, None]) -> None:
      """
      TODO: Documentation
      """

      # Load the bathymetry model
      if isinstance(bathymetry_model, str):
         bathymetry_data = numpy.load(bathymetry_model)
         bath_lats = numpy.array(bathymetry_data['latIndex'])
         bath_lons = numpy.array(bathymetry_data['lonIndex'])
         bath_depths = numpy.array(bathymetry_data['zMat'])
         def get_bathymetry(latitude: float, longitude: float) -> float:
            lat_index = numpy.abs(bath_lats - latitude).argmin()
            lon_index = numpy.abs(bath_lons - longitude).argmin()
            return -bath_depths[lat_index][lon_index]
      elif callable(bathymetry_model):
         def get_bathymetry(latitude: float, longitude: float) -> float:
            return -bathymetry_model(latitude, longitude)
      else:
         def get_bathymetry(_latitude: float, _longitude: float) -> float:
            return 0.0

      # Load the ocean currents model
      if isinstance(ocean_currents_model, str):
         ocean_currents_data = numpy.load(ocean_currents_model)
         curr_lats = numpy.array(ocean_currents_data['latIndex'])
         curr_lons = numpy.array(ocean_currents_data['lonIndex'])
         curr_depths = numpy.array(ocean_currents_data['depthIndex'])
         u_mean_data = numpy.array(ocean_currents_data['uMeanData'])
         u_std_data = numpy.array(ocean_currents_data['uStdData'])
         v_mean_data = numpy.array(ocean_currents_data['vMeanData'])
         v_std_data = numpy.array(ocean_currents_data['vStdData'])
         def get_ocean_current(latitude: float, longitude: float, depth: float) -> Tuple[float, float]:
            lat_index = numpy.abs(curr_lats - latitude).argmin()
            lon_index = numpy.abs(curr_lons - longitude).argmin()
            depth_index = numpy.abs(curr_depths - depth).argmin()
            return math.sqrt(
                     (numpy.abs(u_mean_data[depth_index, lat_index, lon_index]) + (2.0 * u_std_data[depth_index, lat_index, lon_index]))**2 +
                     (numpy.abs(v_mean_data[depth_index, lat_index, lon_index]) + (2.0 * v_std_data[depth_index, lat_index, lon_index]))**2)
      elif callable(ocean_currents_model):
         def get_ocean_current(latitude: float, longitude: float, depth: float) -> Tuple[float, float]:
            return ocean_currents_model(latitude, longitude, depth)
      else:
         def get_ocean_current(_latitude: float, _longitude: float, _depth: float) -> Tuple[float, float]:
            return 0.0

      # Load the density model
      if isinstance(density_model, str):
         density_data = numpy.load(density_model)
         dens_lats = numpy.array(density_data['latIndex'])
         dens_lons = numpy.array(density_data['lonIndex'])
         dens_depths = numpy.array(density_data['depthIndex'])
         densities = numpy.array(density_data['data'])
         def get_density(latitude: float, longitude: float, depth: float) -> float:
            lat_index = numpy.abs(dens_lats - latitude).argmin()
            lon_index = numpy.abs(dens_lons - longitude).argmin()
            depth_index = numpy.abs(dens_depths - depth).argmin()
            return densities[lat_index][lon_index][depth_index]
      elif callable(density_model):
         def get_density(latitude: float, longitude: float, depth: float) -> float:
            return density_model(latitude, longitude, depth)
      else:
         def get_density(_latitude: float, _longitude: float, _depth: float) -> float:
            return 0.0

      # Iterate through all waypoints
      transit_distance = 0.0
      min_density = min_latitude = 100000.0
      max_density = max_current = -100.0
      max_depth = self.maximum_depth if self.maximum_depth is not None else -100.0
      with open(waypoints_path, 'rb') as waypoint_file:
         waypoints = pickle.load(waypoint_file)
         waypoint, previous_waypoint = GlobalCoordinate(), GlobalCoordinate()
         if len(waypoints) > 0:
            previous_waypoint.set_llh(waypoints[0][0], waypoints[0][1], waypoints[0][2])
            min_latitude = max_latitude = previous_waypoint.latitude
            max_depth = max(max_depth, get_bathymetry(waypoints[0][0], waypoints[0][1]))
            min_density = get_density(waypoints[0][0], waypoints[0][1], 0.0)
            max_density = get_density(waypoints[0][0], waypoints[0][1], max_depth)
            max_current = get_ocean_current(waypoints[0][0], waypoints[0][1], 10.0)
            for i in range(1, len(waypoints)):
               waypoint.set_llh(waypoints[i][0], waypoints[i][1], waypoints[i][2])
               min_latitude = min(min_latitude, waypoint.latitude)
               max_latitude = max(max_latitude, waypoint.latitude)
               depth = get_bathymetry(waypoints[i][0], waypoints[i][1])
               max_depth = max(max_depth, depth)
               min_density = min(min_density, get_density(waypoints[i][0], waypoints[i][1], 0.0))
               max_density = max(max_density, get_density(waypoints[i][0], waypoints[i][1], depth))
               max_current = max(max_current, get_ocean_current(waypoints[i][0], waypoints[i][1], 10.0))
               transit_distance += waypoint.compute_distance(previous_waypoint)
               previous_waypoint.copy_from(waypoint)

      # Update a subset of the mission stage parameters
      self.targets |= MissionTarget.EXACT_DISTANCE
      if min_latitude < 100.0:
         self.average_latitude = 90.0 * (min_latitude + max_latitude) / math.pi
         self.target_distance = self.minimum_distance = self.maximum_distance = 0.001 * transit_distance
      if min_density > 0.0 and min_density < 50000.0:
         self.minimum_density = min_density
      if max_density > 0.0 and max_density < 50000.0:
         self.maximum_density = max_density
      if max_current >= 0.0:
         self.maximum_ocean_current_speed = max_current
      if max_depth >= 0.0:
         self.maximum_depth = max_depth


   def finalize(self) -> None:
      """
      TODO: Documentation, Ensure all parameters have valid values.
      """
      if self.minimum_density is None:
         if self.minimum_salinity is None or self.maximum_temperature is None:
            raise RuntimeError('Parameter "{}" cannot be None while "{}" or "{}" are also None '
                               'for Mission Stage {}'.format('minimum_density', 'minimum_salinity',
                               'maximum_temperature', self.name))
         minimum_pressure = OceanicModels.pressure_at_depth(0.0)
         self.minimum_density = OceanicModels.water_density(self.maximum_temperature,
                                                            self.minimum_salinity,
                                                            minimum_pressure)
      if self.maximum_density is None:
         if self.maximum_salinity is None or self.minimum_temperature is None:
            raise RuntimeError('Parameter "{}" cannot be None while "{}" or "{}" are also None '
                               'for Mission Stage {}'.format('maximum_density', 'maximum_salinity',
                               'minimum_temperature', self.name))
         maximum_pressure = OceanicModels.pressure_at_depth(self.maximum_depth)
         self.maximum_density = OceanicModels.water_density(self.minimum_temperature,
                                                            self.maximum_salinity,
                                                            maximum_pressure)
      if self.maximum_depth is None:
         raise RuntimeError('Parameter "maximum_depth" cannot be None for Mission Stage {}'
                            .format(self.name))
      if self.maximum_pitch_angle is None:
         raise RuntimeError('Parameter "maximum_pitch_angle" cannot be None for Mission Stage {}'
                            .format(self.name))
      if self.maximum_roll_angle is None:
         raise RuntimeError('Parameter "maximum_roll_angle" cannot be None for Mission Stage {}'
                            .format(self.name))
      if self.maximum_ocean_current_speed is None:
         self.maximum_ocean_current_speed = 0.0
      if self.maximum_net_buoyancy is None:
         self.maximum_net_buoyancy = (self.maximum_density / self.minimum_density) - 1.0
      elif self.maximum_net_buoyancy < 1.0:
         self.maximum_net_buoyancy = max(self.maximum_net_buoyancy, (self.maximum_density / self.minimum_density) - 1.0)

      if MissionTarget.EXACT_DISTANCE in self.targets:
         if self.target_distance is None:
            raise RuntimeError('For Mission Stage "{}" with EXACT_DISTANCE target, target_distance must be specified.')
         self.minimum_distance = self.maximum_distance = self.target_distance
      else:
         if MissionTarget.MINIMUM_DISTANCE in self.targets and self.minimum_distance is None:
            duration = self.target_duration if self.target_duration is not None else self.minimum_duration
            speed = self.target_average_horizontal_speed if self.target_average_horizontal_speed is not None else self.minimum_average_horizontal_speed
            if duration is not None and speed is not None:
               self.minimum_distance = 0.001 * duration * speed
            else:
               raise RuntimeError('For Mission Stage "{}" with MINIMUM_DISTANCE target, minimum_distance must be specified or calculable.')
         if MissionTarget.MAXIMUM_DISTANCE in self.targets and self.maximum_distance is None:
            duration = self.target_duration if self.target_duration is not None else self.maximum_duration
            speed = self.target_average_horizontal_speed if self.target_average_horizontal_speed is not None else self.maximum_average_horizontal_speed
            if duration is not None and speed is not None:
               self.maximum_distance = 0.001 * duration * speed
            else:
               raise RuntimeError('For Mission Stage "{}" with MAXIMUM_DISTANCE target, maximum_distance must be specified or calculable.')
      if MissionTarget.EXACT_DURATION in self.targets:
         if self.target_duration is None:
            raise RuntimeError('For Mission Stage "{}" with EXACT_DURATION target, target_duration must be specified.')
         self.minimum_duration = self.maximum_duration = self.target_duration
      else:
         if MissionTarget.MINIMUM_DURATION in self.targets and self.minimum_duration is None:
            distance = self.target_distance if self.target_distance is not None else self.minimum_distance
            speed = self.target_average_horizontal_speed if self.target_average_horizontal_speed is not None else self.maximum_average_horizontal_speed
            if distance is not None and speed is not None:
               self.minimum_duration = 1000.0 * distance / speed
            else:
               raise RuntimeError('For Mission Stage "{}" with MINIMUM_DURATION target, minimum_duration must be specified or calculable.')
         elif MissionTarget.MAXIMUM_DURATION in self.targets and self.maximum_duration is None:
            distance = self.target_distance if self.target_distance is not None else self.maximum_distance
            speed = self.target_average_horizontal_speed if self.target_average_horizontal_speed is not None else self.minimum_average_horizontal_speed
            if distance is not None and speed is not None:
               self.maximum_duration = 1000.0 * distance / speed
            else:
               raise RuntimeError('For Mission Stage "{}" with MAXIMUM_DURATION target, maximum_duration must be specified or calculable.')
      if MissionTarget.HORIZONTAL_SPEED in self.targets:
         if self.target_average_horizontal_speed is None:
            raise RuntimeError('For Mission Stage "{}" with HORIZONTAL_SPEED target, target_average_horizontal_speed must be specified.')
         self.minimum_average_horizontal_speed = self.maximum_average_horizontal_speed = self.target_average_horizontal_speed
      else:
         if self.target_duration is not None and self.target_distance is not None:
            self.minimum_average_horizontal_speed = self.maximum_average_horizontal_speed = self.target_average_horizontal_speed = 1000.0 * self.target_distance / self.target_duration
         min_distance = self.target_distance if self.target_distance is not None else self.minimum_distance
         min_duration = self.target_duration if self.target_duration is not None else self.minimum_duration
         max_distance = self.target_distance if self.target_distance is not None else self.maximum_distance
         max_duration = self.target_duration if self.target_duration is not None else self.maximum_duration
         if self.minimum_average_horizontal_speed is None and min_distance is not None and max_duration is not None:
            self.minimum_average_horizontal_speed = 1000.0 * min_distance / max_duration
         if self.maximum_average_horizontal_speed is None and max_distance is not None and min_duration is not None:
            self.maximum_average_horizontal_speed = 1000.0 * max_distance / min_duration


class MissionIterator(object):

   def __init__(self, mission: Mission) -> None:
      super().__init__()
      self._mission = mission
      self._index = 0

   def __next__(self) -> MissionStage:
      if self._index < len(self._mission.stages):
         result = self._mission.stages[self._index]
         self._index += 1
         return result
      raise StopIteration


class Mission(object):
   """TODO: Documentation
   """

   # Public attributes ----------------------------------------------------------------------------

   stages: List[MissionStage]
   """List of unique stages within the mission."""

   minimum_duration: float
   """Minimum duration of the entire mission (in `s`)."""

   maximum_duration: float
   """Maximum duration of the entire mission (in `s`)."""

   minimum_distance: float
   """Minimum transit distance of the entire mission (in `km`)."""

   maximum_average_horizontal_speed: float
   """Maximum average horizontal speed for the entire mission (in `m/s`)."""


   # Constructor ----------------------------------------------------------------------------------

   def __init__(self) -> None:
      super().__init__()
      self.stages = []
      self.minimum_duration = None
      self.maximum_duration = None
      self.minimum_distance = None
      self.maximum_average_horizontal_speed = None


   # Built-in methods -----------------------------------------------------------------------------

   def __iter__(self):
      return MissionIterator(self)


   # Public methods -------------------------------------------------------------------------------

   def add_stage(self, stage: MissionStage) -> None:
      stage.finalize()
      self.stages.append(stage)


   def finalize(self) -> None:

      # Ensure that all mission stage speeds are correct
      if self.maximum_average_horizontal_speed is not None:
         for stage in self.stages:
            if stage.maximum_average_horizontal_speed is None or stage.maximum_average_horizontal_speed > self.maximum_average_horizontal_speed:
               stage.maximum_average_horizontal_speed = self.maximum_average_horizontal_speed
               stage.finalize()

      # Attempt to compute the total minimum mission distance
      stage_distances = [stage.minimum_distance for stage in self.stages if stage.minimum_distance is not None]
      if self.minimum_distance is None:
         if len(stage_distances) == len(self.stages):
            self.minimum_distance = sum(stage_distances)
      else:
         if len(stage_distances) == len(self.stages) - 1:
            for stage in self.stages:
               if stage.minimum_distance is None:
                  stage.minimum_distance = self.minimum_distance - sum(stage_distances)
                  stage.finalize()
         elif len(stage_distances) == len(self.stages):
            self.minimum_distance = max(self.minimum_distance, stage_distances)

      # Attempt to compute the total minimum mission duration
      stage_durations = [stage.minimum_duration for stage in self.stages if stage.minimum_duration is not None]
      if self.minimum_duration is None:
         if len(stage_durations) == len(self.stages):
            self.minimum_duration = sum(stage_durations)
      else:
         if len(stage_durations) == len(self.stages) - 1:
            for stage in self.stages:
               if stage.minimum_duration is None:
                  stage.minimum_duration = self.minimum_duration - sum(stage_durations)
                  stage.finalize()
         elif len(stage_durations) == len(self.stages):
            self.minimum_duration = max(self.minimum_duration, stage_durations)

      # Attempt to compute the total maximum mission duration
      stage_durations = [stage.maximum_duration for stage in self.stages if stage.maximum_duration is not None]
      if self.maximum_duration is None:
         if len(stage_durations) == len(self.stages):
            self.maximum_duration = sum(stage_durations)
      else:
         if len(stage_durations) == len(self.stages) - 1:
            for stage in self.stages:
               if stage.maximum_duration is None:
                  stage.maximum_duration = self.maximum_duration - sum(stage_durations)
                  stage.finalize()
         elif len(stage_durations) == len(self.stages):
            self.maximum_duration = min(self.maximum_duration, stage_durations)

      # Ensure that the total mission parameters are at least greater than the sum of the individual stage parts
      stage_distances = sum([stage.minimum_distance for stage in self.stages if stage.minimum_distance is not None])
      stage_min_durations = sum([stage.minimum_duration for stage in self.stages if stage.minimum_duration is not None])
      stage_max_durations = sum([stage.maximum_duration for stage in self.stages if stage.maximum_duration is not None])
      # TODO: Add back: if self.minimum_distance is not None and self.minimum_distance < stage_distances:
      #   self.minimum_distance = stage_distances
      if self.minimum_duration is not None and self.minimum_duration < stage_min_durations:
         self.minimum_duration = stage_min_durations
      if self.maximum_duration is not None and self.maximum_duration < stage_max_durations:
         self.maximum_duration = stage_max_durations

      # Attempt to fill in any missing average horizontal speeds for all mission stages
      if self.minimum_distance is not None and self.maximum_duration is not None:
         min_speed = 1000.0 * self.minimum_distance / self.maximum_duration
         for stage in self.stages:
            if stage.minimum_average_horizontal_speed is None or stage.minimum_average_horizontal_speed < min_speed:
               stage.minimum_average_horizontal_speed = min_speed
               stage.finalize()

      # Symbolize any missing target mission parameters for all mission stages
      for stage in self.stages:
         if stage.target_distance is None:
            stage.target_distance = Symbol(stage.name + '_distance')
         if stage.target_duration is None:
            stage.target_duration = Symbol(stage.name + '_duration')
         if stage.target_average_horizontal_speed is None:
            stage.target_average_horizontal_speed = Symbol(stage.name + '_average_speed')

# TODO: If glider, alter max_net_buoyancy to achieve required speeds at all depths
