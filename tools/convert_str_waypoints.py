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
   if len(sys.argv) != 3 or '--output=' not in sys.argv[1]:
      print('\nUSAGE: ./convert_str_waypoints.py --output=[pkl,csv] WAYPOINT_FILE.pkl\n')
      sys.exit(-1)
   if not Path(sys.argv[2]).exists:
      print('\nERROR: The specified file does not exist: {}'.format(sys.argv[2]))
      sys.exit(-2)
   output_format = sys.argv[1].split('--output=')[1]

   # Open and parse the STR waypoints file
   with open(sys.argv[2], 'rb') as input_file:
      data = pickle.load(input_file)
      if 'navigation' in data and 'target' in data and 'posGeo' in data['navigation'] and \
                                  'posGeo' in data['target'] and len(data['navigation']['posGeo']) > 0:
         if output_format == 'csv':
            with open(os.path.splitext(sys.argv[2])[0] + '_part1.csv', 'w', newline='') as output_file1:
               with open(os.path.splitext(sys.argv[2])[0] + '_part2.csv', 'w', newline='') as output_file2:
                  with open(os.path.splitext(sys.argv[2])[0] + '_part3.csv', 'w', newline='') as output_file3:
                     csv_writer = csv.writer(output_file1, delimiter=',')
                     for waypoint in data['navigation']['posGeo']:
                        csv_writer.writerow(waypoint)
                        if waypoint == data['target']['posGeo']:
                           csv_writer = csv.writer(output_file2, delimiter=',')
                           csv_writer.writerow(waypoint)
                           csv_writer = csv.writer(output_file3, delimiter=',')
                           csv_writer.writerow(waypoint)
         elif output_format == 'pkl':
            with open(os.path.splitext(sys.argv[2])[0] + '_part1.pkl', 'wb') as output_file1:
               with open(os.path.splitext(sys.argv[2])[0] + '_part2.pkl', 'wb') as output_file2:
                  with open(os.path.splitext(sys.argv[2])[0] + '_part3.pkl', 'wb') as output_file3:
                     part1, part2, part3 = [], [], []
                     current_part = part1
                     for waypoint in data['navigation']['posGeo']:
                        current_part.append(waypoint)
                        if waypoint == data['target']['posGeo']:
                           part2.append(waypoint)
                           part3.append(waypoint)
                           current_part = part3
                     pickle.dump(part1, output_file1, protocol=pickle.HIGHEST_PROTOCOL)
                     pickle.dump(part2, output_file2, protocol=pickle.HIGHEST_PROTOCOL)
                     pickle.dump(part3, output_file3, protocol=pickle.HIGHEST_PROTOCOL)
