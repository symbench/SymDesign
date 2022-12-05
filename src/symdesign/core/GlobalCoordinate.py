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
from typing import Tuple
import math


# Helper constants for XYZ-to-LLH conversion
EARTH_EQUATORIAL_RADIUS = 6378137.0
EARTH_POLAR_RADIUS = 6356752.0
EARTH_ECCENTRICITY_2 = 0.00669437999014
A1 = EARTH_EQUATORIAL_RADIUS * EARTH_ECCENTRICITY_2
A2 = A1 * A1
A3 = 0.5 * EARTH_EQUATORIAL_RADIUS * EARTH_ECCENTRICITY_2 * EARTH_ECCENTRICITY_2
A4 = (5.0/2.0) * A2
A5 = A1 + A3
A6 = 1.0 - EARTH_ECCENTRICITY_2


class GlobalCoordinate(object):
   """
   TODO: Documentation
   """


   # Public attributes ----------------------------------------------------------------------------

   x: float
   """TODO (in ``)."""

   y: float
   """TODO (in ``)."""

   z: float
   """TODO (in ``)."""

   latitude: float
   """TODO (in `rad`)."""

   longitude: float
   """TODO (in `rad`)."""

   height: float
   """TODO (in `m`)."""


   # Constructor ----------------------------------------------------------------------------------

   def __init__(self) -> None:
      super().__init__()
      self.x = self.y = self.z = self.earth_rad = 0.0
      self.latitude = self.longitude = self.height = 0.0


   # Built-in method implementations --------------------------------------------------------------

   def __repr__(self) -> str:
      return '({}, {}, {})'.format(self.latitude * 180.0 / math.pi,
                                   self.longitude * 180.0 / math.pi,
                                   self.height)

   def __str__(self) -> str:
      return self.__repr__()

   def __eq__(self, other) -> bool:
      return abs(self.x - other.x) < 0.0001 and \
             abs(self.y - other.y) < 0.0001 and \
             abs(self.z - other.z) < 0.0001


   # Helper methods -------------------------------------------------------------------------------

   @staticmethod
   def _earth_radius(latitude_rad: float) -> float:
      """TODO: Documentation"""
      cos_lat = math.cos(latitude_rad)
      sin_lat = math.sin(latitude_rad)
      a = EARTH_EQUATORIAL_RADIUS * EARTH_EQUATORIAL_RADIUS * cos_lat * cos_lat
      b = EARTH_POLAR_RADIUS * EARTH_POLAR_RADIUS * sin_lat * sin_lat
      return math.sqrt(((EARTH_EQUATORIAL_RADIUS * EARTH_EQUATORIAL_RADIUS * a) + (EARTH_POLAR_RADIUS * EARTH_POLAR_RADIUS * b)) / (a + b))

   def _xyz2llh(self) -> GlobalCoordinate:

      # Calculate intermediate variables
      positive_z = abs(self.z)
      W2 = ((self.x * self.x) + (self.y * self.y))
      Z2 = self.z * self.z
      W = math.sqrt(W2)
      R2 = W2 + Z2
      R = math.sqrt(R2)
      S = positive_z / R
      C = W / R
      U = A2 / R
      V = A3 - (A4 / R)
      S2 = S * S
      C2 = C * C

      # Compute longitude
      self.longitude = math.atan2(self.y, self.x)

      # Compute latitude differently depending on its nearness to the Earth's poles
      if C2 > 0.3:
         S *= (1.0 + (C2 * (A1 + U + (S2 * V)) / R))
         self.latitude = math.asin(S)
         S2 = S*S
         C = math.sqrt(1.0 - S2)
      else:
         C *= (1.0 - (S2 * (A5 - U - (C2 * V)) / R))
         self.latitude = math.acos(C)
         S2 = 1.0 - C*C
         S = math.sqrt(S2)

      # Compute height
      G = 1.0 - (EARTH_ECCENTRICITY_2 * S2)
      R1 = EARTH_EQUATORIAL_RADIUS / math.sqrt(G)
      r_f = A6 * R1
      U = W - (R1 * C)
      V = positive_z - (r_f * S)
      F = (C * U) + (S * V)
      M = (C * V) - (S * U)
      P = M / ((r_f / G) + F)
      self.latitude += P
      self.height = F + (0.5 * M * P)
      if self.z < 0.0:
         self.latitude = -self.latitude
      self.earth_rad = self._earth_radius(self.latitude)
      return self

   def _llh2xyz(self) -> GlobalCoordinate:

      sin_lat = math.sin(self.latitude)
      N = EARTH_EQUATORIAL_RADIUS / math.sqrt(1.0 - (EARTH_ECCENTRICITY_2 * sin_lat * sin_lat))
      common_param = (N + self.height) * math.cos(self.latitude)

      self.x = common_param * math.cos(self.longitude)
      self.y = common_param * math.sin(self.longitude)
      self.z = ((N * (1.0 - EARTH_ECCENTRICITY_2)) + self.height) * sin_lat
      self.earth_rad = self._earth_radius(self.latitude)
      return self


   # Setter methods -------------------------------------------------------------------------------

   def set_xyz(self, x: float, y: float, z: float) -> GlobalCoordinate:
      self.x = x
      self.y = y
      self.z = z
      return self._xyz2llh()

   def set_llh(self, latitude_deg: float, longitude_deg: float, height_m: float) -> GlobalCoordinate:
      self.latitude = latitude_deg * math.pi / 180.0
      self.longitude = longitude_deg * math.pi / 180.0
      self.height = height_m
      return self._llh2xyz()

   def copy_from(self, other: GlobalCoordinate) -> GlobalCoordinate:
      self.x = other.x
      self.y = other.y
      self.z = other.z
      self.latitude = other.latitude
      self.longitude = other.longitude
      self.height = other.height
      self.earth_rad = other.earth_rad


   # Getter methods -------------------------------------------------------------------------------

   def get_llh(self) -> Tuple[float, float, float]:
      return self.latitude * 180.0 / math.pi, self.longitude * 180.0 / math.pi, self.height

   def get_xyz(self) -> Tuple[float, float, float]:
      return self.x, self.y, self.z

   def get_latitude(self) -> float:
      return self.latitude * 180.0 / math.pi

   def get_longitude(self) -> float:
      return self.longitude * 180.0 / math.pi

   def get_height(self) -> float:
      return self.height

   def get_x(self) -> float:
      return self.x

   def get_y(self) -> float:
      return self.y

   def get_z(self) -> float:
      return self.z


   # Public methods -------------------------------------------------------------------------------

   def compute_distance(self, target: GlobalCoordinate) -> float:
      """Method to find the distance between two coordinates using Bowring formulas."""

      # Compute common calculations for reuse
      ref_lat_rotation = self.latitude - (0.5 * math.pi)
      ref_lon_rotation = self.longitude - math.pi
      cos_ref_lat_rotation = math.cos(ref_lat_rotation)
      sin_ref_lat_rotation = math.sin(ref_lat_rotation)
      cos_ref_lon_rotation = math.cos(ref_lon_rotation)
      sin_ref_lon_rotation = math.sin(ref_lon_rotation)

      # ECEF distance vector
      x_diff = target.x - self.x
      y_diff = target.y - self.y
      z_diff = target.z - self.z

      # Translate distance vector into ENU coordinates
      x = sin_ref_lon_rotation*x_diff - cos_ref_lon_rotation*y_diff
      y = cos_ref_lat_rotation*cos_ref_lon_rotation*x_diff + cos_ref_lat_rotation*sin_ref_lon_rotation*y_diff - sin_ref_lat_rotation*z_diff
      z = sin_ref_lat_rotation*cos_ref_lon_rotation*x_diff + sin_ref_lat_rotation*sin_ref_lon_rotation*y_diff + cos_ref_lat_rotation*z_diff

      # Return 3-D distance
      return math.sqrt((x * x) + (y * y) + (z * z))


   def compute_initial_bearing(self, target: GlobalCoordinate):
      """Method to determine the initial bearing toward a target coordinate."""

      cos_target_lat_radians = math.cos(target.latitude)
      lon_diff_radians = target.longitude - self.longitude

      y = math.sin(lon_diff_radians) * cos_target_lat_radians
      x = (math.cos(self.latitude) * math.sin(target.latitude)) - (math.sin(self.latitude) * cos_target_lat_radians * math.cos(lon_diff_radians))
      return ((math.atan2(y, x) * 180.0 / math.pi) + 360.0) % 360.0


   def compute_final_bearing(self, target: GlobalCoordinate):
      """Method to determine the final bearing toward a target coordinate."""
      return (target.compute_initial_bearing(self) + 180.0) % 180.0
