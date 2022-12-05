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

from symdesign.core.Mission import Mission, MissionStage
from pathlib import Path

def water_density_model(_latitude_deg: float, _longitude_deg: float, depth_m: float) -> float:
   return 1030.0 + (20.0 * (depth_m / 4000.0))

if __name__ == '__main__':

   mission = Mission()
   tests_path = str(Path(__file__).parent.parent.resolve())
   bathymetry_file_path = tests_path + '/2022-Aug-Hackathon/bathymetry/bathymetry_lat60-90.npz'
   currents_file_path = tests_path + '/2022-Aug-Hackathon/ocean_currents/ocean_currents.npz'
   waypoint_file_paths = {'departure': tests_path + '/2022-Aug-Hackathon/waypoints/departure_waypoints.pkl',
                          'payload_drop': tests_path + '/2022-Aug-Hackathon/waypoints/payload_drop_waypoints.pkl',
                          'return': tests_path + '/2022-Aug-Hackathon/waypoints/return_waypoints.pkl'}
   for stage_name, waypoint_file in waypoint_file_paths.items():
      print('\nCreating Mission Stage "{}"'.format(stage_name))
      mission_stage = MissionStage(stage_name)
      mission_stage.maximum_roll_angle = 0.0
      mission_stage.maximum_pitch_angle = 30.0
      print('Loading waypoints...')
      mission_stage.load_waypoints_and_custom_density(waypoint_file, bathymetry_file_path, currents_file_path, water_density_model)
      print('Adding stage to mission...')
      mission.add_stage(mission_stage)
   mission.maximum_duration = 60 * 24 * 60 * 60
   print('Finalizing mission...')
   mission.finalize()

   print('\nMission stages:\n')
   for stage in mission:
      print(stage.__dict__)
      print()
   print('Mission min distance: {:.3f} km'.format(mission.minimum_distance))
   print('Mission min duration: {} s'.format(mission.minimum_duration))
   print('Mission max duration: {} s'.format(mission.maximum_duration))
