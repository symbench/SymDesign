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

from ..materials.PressureMaterial import PressureMaterial
from .Oceanic import OceanicModels
from typing import Union
from sympy import Expr
import sympy

class MaterialUnderPressure(object):

   @staticmethod
   def minimum_cylinder_thickness(material: PressureMaterial, depth_rating: float, radius: Union[float, Expr]):
      crush_pressure = OceanicModels.pressure_at_depth(depth_rating)
      cylinder_buckling_failure_thickness = sympy.Pow((0.5 * crush_pressure / material.get_youngs_modulus()) * (1.0 - material.get_poissons_ratio()**2), (1.0 / 3.0)) * radius * 2.0
      cylinder_yield_failure_thickness = (1.0 - sympy.sqrt(1.0 - (2.0 * crush_pressure / material.get_yield_stress()))) * radius
      return sympy.Max(cylinder_buckling_failure_thickness, cylinder_yield_failure_thickness)

   @staticmethod
   def minimum_spherical_endcap_thickness(material: PressureMaterial, depth_rating: float, radius: Union[float, Expr]):
      crush_pressure = OceanicModels.pressure_at_depth(depth_rating)
      endcap_buckling_failure_thickness = sympy.sqrt(crush_pressure * radius**2 / (0.365 * material.get_youngs_modulus()))
      endcap_yield_failure_thickness = (crush_pressure * radius) / (2.0 * material.get_yield_stress())
      return sympy.Max(endcap_yield_failure_thickness, endcap_buckling_failure_thickness)

   @staticmethod
   def minimum_semiellipsoidal_endcap_thickness(material: PressureMaterial, depth_rating: float, radius: Union[float, Expr]):
      crush_pressure = OceanicModels.pressure_at_depth(depth_rating)
      endcap_yield_failure_thickness = crush_pressure * radius / material.get_yield_stress()
      return endcap_yield_failure_thickness

   @staticmethod
   def minimum_flat_endcap_thickness(material: PressureMaterial, depth_rating: float, radius: Union[float, Expr]):
      crush_pressure = OceanicModels.pressure_at_depth(depth_rating)
      return sympy.sqrt(6.0 * (material.get_poissons_ratio() + 3.0) * radius**2 * crush_pressure / (16.0 * material.get_yield_stress()))
