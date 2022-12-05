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
import csv, pickle, os, sys

if __name__ == '__main__':

   # Verify command-line parameters
   if len(sys.argv) != 2:
      print('\nUSAGE: ./convert_csv_waypoints.py WAYPOINT_FILE.csv\n')
      sys.exit(-1)
   if not Path(sys.argv[1]).exists:
      print('\nERROR: The specified file does not exist: {}'.format(sys.argv[1]))
      sys.exit(-2)

   # Open and parse the CSV waypoints file
   with open(sys.argv[1], 'rb') as input_file:
      data = []
      data_reader = csv.reader(input_file, delimiter=',')
      for line in data_reader:
         data.append(line)
      with open(os.path.splitext(sys.argv[1])[0] + '_symdesign.pkl', 'wb') as output_file:
         pickle.dump(data, output_file, protocol=pickle.HIGHEST_PROTOCOL)
