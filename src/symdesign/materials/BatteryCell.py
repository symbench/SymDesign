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
import math

class BatteryCell(Material):

   def __init__(self) -> None:
      super().__init__()
      self.add_option('A', { 'radius_m': 0.017, 'length_m': 0.005, 'voltage_V': 1.5, 'capacity_Wh': 1.0, 'mass_kg': 0.032 })
      self.add_option('AA', { 'radius_m': 0.0145, 'length_m': 0.005, 'voltage_V': 1.5, 'capacity_Wh': 2.0, 'mass_kg': 0.021 })
      self.add_option('AAA', { 'radius_m': 0.0105, 'length_m': 0.0445, 'voltage_V': 1.5, 'capacity_Wh': 3.0, 'mass_kg': 0.01 })
      self.add_option('AAAA', { 'radius_m': 0.0083, 'length_m': 0.0425, 'voltage_V': 1.5, 'capacity_Wh': 4.0, 'mass_kg': 0.01 })
      self.add_option('C', { 'radius_m': 0.0255, 'length_m': 0.005, 'voltage_V': 1.5, 'capacity_Wh': 8.0, 'mass_kg': 0.072 })
      self.add_option('D', { 'radius_m': 0.0342, 'length_m': 0.0615, 'voltage_V': 1.5, 'capacity_Wh': 40.0, 'mass_kg': 0.105 })
      self.add_option('DD', { 'radius_m': 0.01675, 'length_m': 0.112, 'voltage_V': 3.6, 'capacity_Wh': 97.2, 'mass_kg': 0.213 })
      self.add_option('F', { 'radius_m': 0.033, 'length_m': 0.091, 'voltage_V': 1.5, 'capacity_Wh': 5.0, 'mass_kg': 0.231 })
      self.add_option('14500', { 'radius_m': 0.014, 'length_m': 0.005, 'voltage_V': 3.7, 'capacity_Wh': 10.0, 'mass_kg': 0.020 })
      self.add_option('21700', { 'radius_m': 0.021, 'length_m': 0.007, 'voltage_V': 3.7, 'capacity_Wh': 11.0, 'mass_kg': 0.060 })
      self.add_option('32650', { 'radius_m': 0.032, 'length_m': 0.065, 'voltage_V': 3.2, 'capacity_Wh': 12.0, 'mass_kg': 0.075 })
      self.add_option('SubC', { 'radius_m': 0.0222, 'length_m': 0.0429, 'voltage_V': 1.2, 'capacity_Wh': 2.4, 'mass_kg': 0.052 })

   def get_radius(self) -> float:
      return self.get_selection()['radius_m']

   def get_length(self) -> float:
      return self.get_selection()['length_m']

   def get_volume(self) -> float:
      selection = self.get_selection()
      return math.pi * selection['radius_m']**2 * selection['length_m']

   def get_voltage(self) -> float:
      return self.get_selection()['voltage_V']

   def get_capacity(self) -> float:
      return self.get_selection()['capacity_Wh']

   def get_mass(self) -> float:
      return self.get_selection()['mass_kg']
