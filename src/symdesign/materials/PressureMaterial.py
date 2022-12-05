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
from ..core.Material import Material

class PressureMaterial(Material):

   def __init__(self) -> None:
      super().__init__()
      self.add_option('Aluminum-6061-T6', { 'density_kg_m3': 1000.0 * 2.7, 'youngs_modulus_Pa': 6.89e10, 'yield_stress_Pa': 2.76e8, 'poissons_ratio': 0.33 })
      self.add_option('Aluminum-7075-T73', { 'density_kg_m3': 1000.0 * 2.81, 'youngs_modulus_Pa': 7.20e10, 'yield_stress_Pa': 4.39e8, 'poissons_ratio': 0.33 })
      self.add_option('Glass-Borosilicate', { 'density_kg_m3': 1000.0 * 2.23, 'youngs_modulus_Pa': 6.30e10, 'yield_stress_Pa': 2.5e9, 'poissons_ratio': 0.2 })
      self.add_option('Stainless-Steel-304', { 'density_kg_m3': 1000.0 * 8.0, 'youngs_modulus_Pa': 1.93e11, 'yield_stress_Pa': 2.15e8, 'poissons_ratio': 0.29 })
      self.add_option('Titanium-Ti6Al4V', { 'density_kg_m3': 1000.0 * 4.429, 'youngs_modulus_Pa': 1.14e11, 'yield_stress_Pa': 1.10e9, 'poissons_ratio': 0.33 })

   def get_density(self) -> float:
      return self.get_selection()['density_kg_m3']

   def get_youngs_modulus(self) -> float:
      return self.get_selection()['youngs_modulus_Pa']

   def get_yield_stress(self) -> float:
      return self.get_selection()['yield_stress_Pa']

   def get_poissons_ratio(self) -> float:
      return self.get_selection()['poissons_ratio']
