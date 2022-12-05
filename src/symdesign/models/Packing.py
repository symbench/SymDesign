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

from typing import Union
from sympy import Expr, floor

class Packing(object):

   @staticmethod
   def maximize_packed_cylinders_in_cylinder(container_diameter_m: Union[Expr, float],
                                             container_length_m: Union[Expr, float],
                                             packed_item_diameter_m: Union[Expr, float],
                                             packed_item_length_m: Union[Expr, float]) -> int:
      # TODO: Implement this, also constraint_prog can't handle the floor function
      #return 788 * floor(container_length_m / packed_item_length_m)
      return 788 * (container_length_m / packed_item_length_m)
