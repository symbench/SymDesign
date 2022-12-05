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

class StructuralMaterial(Material):

   def __init__(self) -> None:
      super().__init__()
      self.add_option('Plastic-ABS', { 'density_kg_m3': 1037.0 })
      self.add_option('Fiberglass-Polyester', { 'density_kg_m3': 1522.4 })
      self.add_option('Titanium-6AL4V', { 'density_kg_m3': 4429.0 })
      self.add_option('Carbon-Graphite', { 'density_kg_m3': 1450.0 })
      self.add_option('PVC-ThinWall', { 'density_kg_m3': 1300.0 })
      self.add_option('Beryllium', { 'density_kg_m3': 1840.0 })

   def get_density(self) -> float:
      return self.get_selection()['density_kg_m3']
