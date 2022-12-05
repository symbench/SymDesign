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

class BuoyancyMaterial(Material):

   def __init__(self) -> None:
      super().__init__()
      self.add_option('Macro-Foam-20', { 'depth_rating_m': 500.0, 'density_kg_m3': 320.0 })
      self.add_option('MZ-22', { 'depth_rating_m': 1000.0, 'density_kg_m3': 350.0 })
      self.add_option('BZ-24', { 'depth_rating_m': 2000.0, 'density_kg_m3': 385.0 })
      self.add_option('BZ-26', { 'depth_rating_m': 3000.0, 'density_kg_m3': 416.0 })
      self.add_option('AZ-29', { 'depth_rating_m': 4000.0, 'density_kg_m3': 465.0 })
      self.add_option('AZ-31', { 'depth_rating_m': 5000.0, 'density_kg_m3': 495.0 })
      self.add_option('AZ-34', { 'depth_rating_m': 6000.0, 'density_kg_m3': 545.0 })

   def get_depth_rating(self) -> float:
      return self.get_selection()['depth_rating_m']

   def get_density(self) -> float:
      return self.get_selection()['density_kg_m3']
