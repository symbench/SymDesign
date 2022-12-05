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

# TODO: REPLACE THIS WITH CORRECT IMPLEMENTATION IMMEDIATELY

from __future__ import annotations
from pathlib import Path
from typing import Union
from sympy import Expr
from constraint_prog.sympy_func import NeuralFunc
import torch.nn.functional as F
import torch.nn as nn
import torch

nose_len_ranges = [500, 3000]
body_len_ranges = [20, 3000]
tail_len_ranges = [500, 3000]
radius_ranges = [100, 750]
velocity_ranges = [0.5, 5]
drag_input_ranges = nose_len_ranges + body_len_ranges + tail_len_ranges + radius_ranges + velocity_ranges

drag_ranges = [25, 200]
speed_ranges = [0.85, 2]
num_sensor_ranges = [10, 400]
power_input_ranges = drag_ranges + speed_ranges + num_sensor_ranges

HIDDEN1_UNITS = 128
HIDDEN2_UNITS = 64
HIDDEN3_UNITS = 64
HIDDEN4_UNITS = 32
HIDDEN5_UNITS = 32
HIDDEN6_UNITS = 64
HIDDEN7_UNITS = 64
HIDDEN8_UNITS = 8

class SNet(nn.Module):

   def __init__(self, input_size, output_size):
      super().__init__()
      self.fc1 = nn.Linear(input_size, HIDDEN1_UNITS)
      self.prelu= nn.PReLU()
      self.fc2 = nn.Linear(HIDDEN1_UNITS, HIDDEN2_UNITS)
      self.fc3 = nn.Linear(HIDDEN2_UNITS, HIDDEN3_UNITS)
      self.fc4 = nn.Linear(HIDDEN3_UNITS, HIDDEN4_UNITS)
      self.fc5 = nn.Linear(HIDDEN4_UNITS, HIDDEN5_UNITS)
      self.fc6 = nn.Linear(HIDDEN5_UNITS, HIDDEN6_UNITS)
      self.fc7 = nn.Linear(HIDDEN6_UNITS, HIDDEN7_UNITS)
      self.fc8 = nn.Linear(HIDDEN7_UNITS, HIDDEN8_UNITS)
      self.fc9 = nn.Linear(HIDDEN8_UNITS, output_size)

   def forward(self, x):
      x=self.fc1(x)
      x1=F.relu(x)
      x1 = self.fc2(x1)
      x2=F.relu(x1)
      x2 = self.fc3(x2)
      x3=F.relu(x2)
      x3=torch.add(x2, x3)
      nn.Dropout(p=0.2)
      x3 = self.fc4(x3)
      x4=F.relu(x3)
      x4 = self.fc5(x4)
      x5=F.relu(x4)
      x5 = self.fc6(x5)
      x5=F.relu(x5)
      nn.Dropout(p=0.2)
      x5 = self.fc7(x5)
      x5=F.relu(x5)
      x5 = self.fc8(x5)
      x5=F.relu(x5)
      x5 = self.fc9(x5)
      return x5

device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')

drag_model = SNet(5, 1)
drag_model.load_state_dict(torch.load(Path(__file__).parent.joinpath('cfd_surrogate.pt'), map_location=device))
drag_model.to(device)
drag_model.eval()
sympy_drag_model = type('drag_surrogate', (NeuralFunc,), {'arity': 5, 'network': drag_model})

power_model_internal = SNet(3, 1)
power_model_external = SNet(3, 1)
power_model_internal.load_state_dict(torch.load(Path(__file__).parent.joinpath('power_inside_surrogate.pt'), map_location=device))
power_model_external.load_state_dict(torch.load(Path(__file__).parent.joinpath('power_outside_surrogate.pt'), map_location=device))
power_model_internal.to(device)
power_model_external.to(device)
power_model_internal.eval()
power_model_external.eval()
sympy_power_model_internal = type('power_internal_surrogate', (NeuralFunc,), {'arity': 3, 'network': power_model_internal})
sympy_power_model_external = type('power_external_surrogate', (NeuralFunc,), {'arity': 3, 'network': power_model_external})


def get_vehicle_drag(nose_len_m: Union[float, Expr],
                     body_len_m: Union[float, Expr],
                     tail_len_m: Union[float, Expr],
                     radius_m: Union[float, Expr],
                     velocity_m_per_s: Union[float, Expr]) -> float:
   input_data = [1000.0 * nose_len_m,
                 1000.0 * body_len_m,
                 1000.0 * tail_len_m,
                 1000.0 * radius_m,
                 velocity_m_per_s]
   for i in range(len(input_data)):
      input_data[i] = (input_data[i] - drag_input_ranges[2*i]) / (drag_input_ranges[2*i+1] - drag_input_ranges[2*i])
   return sympy_drag_model(*input_data)

def get_power_consumption(model_name: str,
                          nose_len_m: Union[float, Expr],
                          body_len_m: Union[float, Expr],
                          tail_len_m: Union[float, Expr],
                          radius_m: Union[float, Expr],
                          velocity_m_per_s: Union[float, Expr],
                          num_towed_array_sensors: Union[float, Expr]) -> float:
   drag = get_vehicle_drag(nose_len_m, body_len_m, tail_len_m, radius_m, velocity_m_per_s) * 0.6  # TODO: The 0.6 is hardcoded expectation that Harsh will optimize the drag
   speed = velocity_m_per_s

   if model_name == 'baseline':

      total_power = (-2.2444446164469936
                     +5.337294894204587*speed
                     -4.014997961076415*speed**2
                     +0.9565315298637402*speed**3
                     +0.06292278451628497*drag
                     -0.14123529144493607*drag*speed
                     +1200.5504235054598*drag*speed**2
                     -0.026004253707533346*drag*speed**3
                     -0.00026030162454859784*drag**2
                     +0.0005985500595193649*drag**2*speed
                     -0.00043867903516359164*drag**2*speed**2
                     +0.00010197116367471892*drag**2*speed**3)
   else:

      input_data = [drag, speed, num_towed_array_sensors]
      for i in range(len(input_data)):
         input_data[i] = (input_data[i] - power_input_ranges[2*i]) / (power_input_ranges[2*i+1] - power_input_ranges[2*i])

      if model_name == 'internal':
         total_power = sympy_power_model_internal(*input_data)
      elif model_name == 'external':
         total_power = sympy_power_model_external(*input_data)
      else:
         raise RuntimeError('No known power consumption model with name "{}"'.format(model_name))

   return total_power
