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

class PowerProfile(object):

   input_voltage_range: Tuple[float, float]
   """Allowable supply voltage range for the part (in `V`)."""

   current_range: Tuple[float, float]
   """Average current draw for the part (in `A`)."""

   input_voltage: float
   """Supply voltage for the part (in `V`)."""


   def __init__(self, voltage_range: Tuple[float, float], current_range: Tuple[float, float]) -> None:
      super().__init__()
      self.input_voltage_range = voltage_range
      self.current_range = current_range
      self.input_voltage = 0.5 * (voltage_range[0] + voltage_range[1])

   def set_input_voltage(self, voltage: float) -> None:
      # TODO: Simple re-enable this after the hackathon
      #if voltage < self.input_voltage_range[0] or voltage > self.input_voltage_range[1]:
      #   raise RuntimeError('Voltage {}V is outside of the allowable voltage range: {}-{}V'
      #                      .format(voltage, self.input_voltage_range[0], self.input_voltage_range[1]))
      self.input_voltage = voltage

   def get_wattage(self) -> float:
      if self.input_voltage_range[0] == self.input_voltage_range[1]:
         return self.input_voltage * self.current_range[0]
      else:
         return self.input_voltage * \
            ((((self.input_voltage - self.input_voltage_range[0]) / (self.input_voltage_range[1] - self.input_voltage_range[0])) *
            (self.current_range[1] - self.current_range[0])) + self.current_range[0])
