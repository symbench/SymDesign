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

from pathlib import Path
import numpy, pickle, sys

if __name__ == '__main__':

   # Verify command-line parameters
   if len(sys.argv) != 8:
      print('\nUSAGE: ./convert_str_currents.py LAT_GRID.pkl LON_GRID.pkl DEPTH_GRID.pkl U_MEAN.pkl U_STD.pkl V_MEAN.pkl V_STD.pkl\n')
      sys.exit(-1)
   for i in range(1, 8):
      if not Path(sys.argv[i]).exists:
         print('\nERROR: The specified file does not exist: {}'.format(sys.argv[i]))
         sys.exit(-2)
   output_path = str(Path(sys.argv[1]).parent.resolve()) + '/ocean_currents.npz'

   # Load the various ocean current data
   with open(sys.argv[1], 'rb') as file: lat_data = numpy.array(pickle.load(file))
   with open(sys.argv[2], 'rb') as file: lon_data = numpy.array(pickle.load(file))
   with open(sys.argv[3], 'rb') as file: depth_data = numpy.array(pickle.load(file))
   with open(sys.argv[4], 'rb') as file: umean_data = numpy.array(pickle.load(file)) * 0.01
   with open(sys.argv[5], 'rb') as file: ustd_data = numpy.array(pickle.load(file)) * 0.01
   with open(sys.argv[6], 'rb') as file: vmean_data = numpy.array(pickle.load(file)) * 0.01
   with open(sys.argv[7], 'rb') as file: vstd_data = numpy.array(pickle.load(file)) * 0.01

   # Create a numpy array structure containing all the data
   with open(output_path, 'wb') as file:
      numpy.savez_compressed(file, latIndex=lat_data, lonIndex=lon_data, depthIndex=depth_data,
                                   uMeanData=umean_data, uStdData=ustd_data, vMeanData=vmean_data, vStdData=vstd_data)
