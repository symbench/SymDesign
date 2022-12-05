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

import math, sympy

class OceanicModels(object):

   MAXIMUM_EARTH_GRAVITATIONAL_ACCELERATION = 9.83  # m/s^2
   AVERAGE_DEEP_OCEAN_TEMPERATURE = 4.0  # C
   AVERAGE_DEEP_OCEAN_SALINITY = 35.0  # ppt

   @staticmethod
   def gravitational_acceleration(latitude_deg):
      return 9.780318 * (1.0 + (5.2788e-3 + 2.36e-5 * sympy.sin(latitude_deg * math.pi / 180.0)**2) * sympy.sin(latitude_deg * math.pi / 180.0)**2)  # in m/s^2

   @staticmethod
   def pressure_at_depth(depth_m):
      return 10000 * (2.398599584e05 - sympy.sqrt(5.753279964e10 - (4.833657881e05 * depth_m)))  # in Pa = kg/(m*s^2)

   @staticmethod
   def water_density(temperature_c, salinity_ppt, pressure_kg_m_s2):
      return 1000 + ((((((((((((5.2787e-8 * temperature_c) - 6.12293e-6) * temperature_c) + 8.50935e-5) + \
         ((((9.1697e-10 * temperature_c) + 2.0816e-8) * temperature_c) - 9.9348e-7) * salinity_ppt) * pressure_kg_m_s2 * 1e-5) + \
         ((((1.91075e-4 * sympy.sqrt(salinity_ppt)) + ((((-1.6078e-6 * temperature_c) - 1.0981e-5) * temperature_c) + 2.2838e-3)) * salinity_ppt) + \
         ((((((-5.77905e-7 * temperature_c) + 1.16092e-4) * temperature_c) + 1.43713e-3) * temperature_c) + 3.239908))) * pressure_kg_m_s2 * 1e-5) + \
         ((((((((-5.3009e-4 * temperature_c) + 1.6483e-2) * temperature_c) + 7.944e-2) * sympy.sqrt(salinity_ppt)) + \
         ((((((-6.1670e-5 * temperature_c) + 1.09987e-2) * temperature_c) - 0.603459) * temperature_c) + 54.6746)) * salinity_ppt) + \
         ((((((((-5.155288e-5 * temperature_c) + 1.360477e-2) * temperature_c) - 2.327105) * temperature_c) + 148.4206) * temperature_c) + 19652.21))) * \
         ((((4.8314e-4 * salinity_ppt) + (((((-1.6546e-6 * temperature_c) + 1.0227e-4) * temperature_c) - 5.72466e-3) * sympy.sqrt(salinity_ppt)) + \
         ((((((((5.3875e-9 * temperature_c) - 8.2467e-7) * temperature_c) + 7.6438e-5) * temperature_c) - 4.0899e-3) * temperature_c) + 0.824493)) * salinity_ppt) + \
         (((((((((6.536332e-9 * temperature_c) - 1.120083e-6) * temperature_c) + 1.001685e-4) * temperature_c) - 9.095290e-3) * temperature_c) + 6.793952e-2) * temperature_c - 0.157406))) + \
         (pressure_kg_m_s2 * 1e-2)) / ((((((((((5.2787e-8 * temperature_c) - 6.12293e-6) * temperature_c) + 8.50935e-5) + \
         ((((9.1697e-10 * temperature_c) + 2.0816e-8) * temperature_c) - 9.9348e-7) * salinity_ppt) * pressure_kg_m_s2 * 1e-5) + \
         ((((1.91075e-4 *sympy. sqrt(salinity_ppt)) + ((((-1.6078e-6 * temperature_c) - 1.0981e-5) * temperature_c) + 2.2838e-3)) * salinity_ppt) + \
         ((((((-5.77905e-7 * temperature_c) + 1.16092e-4) * temperature_c) + 1.43713e-3) * temperature_c) + 3.239908))) * pressure_kg_m_s2 * 1e-5) + \
         ((((((((-5.3009e-4 * temperature_c) + 1.6483e-2) * temperature_c) + 7.944e-2) * sympy.sqrt(salinity_ppt)) + \
         ((((((-6.1670e-5 * temperature_c) + 1.09987e-2) * temperature_c) - 0.603459) * temperature_c) + 54.6746)) * salinity_ppt) + \
         ((((((((-5.155288e-5 * temperature_c) + 1.360477e-2) * temperature_c) - 2.327105) * temperature_c) + 148.4206) * temperature_c) + 19652.21))) - \
         (pressure_kg_m_s2 * 1e-5)))  # in kg/m^3

   @staticmethod
   def freshwater_absolute_viscosity(temperature_c):
      return ((0.00000000000277388442 * temperature_c**6) - (0.00000000124359703683 * temperature_c**5) + (0.00000022981389243372 * temperature_c**4) - \
         (0.00002310372106867350 * temperature_c**3) + (0.00143393546700877000 * temperature_c**2) - (0.06064140920049450000 * temperature_c) + \
         1.79157254681817000000) / 1000  # in Pa*s = kg/(m*s)

   @staticmethod
   def seawater_absolute_viscosity(temperature_c, salinity_ppt):
      return OceanicModels.freshwater_absolute_viscosity(temperature_c) * (1.0 + ((1.541 + (1.998e-2 * temperature_c) - (9.52e-5 * temperature_c**2)) * \
         salinity_ppt * 0.001) + ((7.974 - (7.561e-2 * temperature_c) + (4.724e-4 * temperature_c**2)) * (salinity_ppt * 0.001)**2))  # in Pa*s = kg/(m*s)

   @staticmethod
   def seawater_kinematic_viscosity(temperature_c, salinity_ppt, pressure_kg_m_s2):
      return OceanicModels.seawater_absolute_viscosity(temperature_c, salinity_ppt) / OceanicModels.water_density(temperature_c, salinity_ppt, pressure_kg_m_s2)
