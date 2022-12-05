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

from symdesign.core.Designer import Designer
from symdesign.core.Mission import MissionStage, MissionTarget
from symdesign.core.Performance import OptimizationParameter, OptimizationMode
from symdesign.parts import PartType, PartSubType
from symdesign.core.Activation import ActivationProfile, ActivationInterval
from symcad.parts.fixed import OceanBottomSeismometer
from pathlib import Path


# Custom water density model from STR
def water_density_model(_latitude_deg: float, _longitude_deg: float, depth_m: float) -> float:
   return 1030.0 + (20.0 * (depth_m / 4000.0))


if __name__ == '__main__':

   # STEP 0: Instantiate a new designer instance ----------------------------------------------------------------------
   print('\nSTEP 0: Instantiate a new designer instance...')

   designer = Designer()
   print('   Designer instance created with UUID: {}'.format(designer.id))



   # STEP 1: Create a set of mission stages and requirements ----------------------------------------------------------
   input('   Press ENTER to continue...')
   print('\nSTEP 1: Create a set of mission stages and requirements...')

   file_path = str(Path(__file__).parent.resolve())
   bathymetry_file_path = file_path + '/bathymetry/bathymetry_lat60-90.npz'
   currents_file_path = file_path + '/ocean_currents/ocean_currents.npz'
   waypoint_file_paths = {'departure': file_path + '/waypoints/departure_waypoints.pkl',
                          'payload_drop': file_path + '/waypoints/payload_drop_waypoints.pkl',
                          'return': file_path + '/waypoints/return_waypoints.pkl'}
   for stage_name, waypoint_file in waypoint_file_paths.items():
      print('   Creating Mission Stage "{}"'.format(stage_name))
      mission_stage = MissionStage(stage_name, [MissionTarget.EXACT_DISTANCE])
      mission_stage.maximum_depth = 1300.0
      mission_stage.maximum_roll_angle = 0.0
      mission_stage.maximum_pitch_angle = 30.0
      mission_stage.load_waypoints_and_custom_density(waypoint_file, bathymetry_file_path, currents_file_path, water_density_model)
      designer.add_mission_stage(mission_stage)
   designer.mission.maximum_average_horizontal_speed = 2.0
   designer.mission.maximum_duration = 60 * 24 * 60 * 60
   designer.mission.finalize()



   # STEP 2: Decide which performance metrics should be optimized -----------------------------------------------------
   input('   Press ENTER to continue...')
   print('\nSTEP 2: Decide which performance metrics should be optimized...')

   designer.optimize_for(OptimizationParameter.MASS, OptimizationMode.MINIMIZE)
   designer.optimize_for(OptimizationParameter.VOLUME, OptimizationMode.MINIMIZE)
   designer.optimize_for(OptimizationParameter.POWER_CONSUMPTION, OptimizationMode.MINIMIZE)
   designer.optimize_for(OptimizationParameter.POWER_RESERVE, OptimizationMode.TARGET, 0.2)
   designer.optimize_for(OptimizationParameter.PRESSURE_VESSEL_VOLUME_TO_MASS, OptimizationMode.MAXIMIZE)
   for metric, mode, value in designer.optimization_metrics:
      print('   Optimizer defined: {} {}{}{}'.format(mode.name, metric.name, ' to ' if value else '', value if value else ''))



   # STEP 3: Import any additional prefabricated sensors or components into parts library -----------------------------
   input('   Press ENTER to continue...')
   print('\nSTEP 3: Import any additional prefabricated sensors or components into parts library...')

   # TODO: Add OBS part details
   designer.create_new_part('Ocean Bottom Seismometer', PartType.SENSOR, PartSubType.GENERAL, OceanBottomSeismometer, None, [], {})
   print(designer.parts_library)



   # STEP 4: Choose all required sensors and components ---------------------------------------------------------------
   input('   Press ENTER to continue...')
   print('\nSTEP 4: Choose all required sensors and components...')

   sat_antenna_suggestions = designer.suggest_parts(PartType.ANTENNA, PartSubType.GPS | PartSubType.IRIDIUM)
   ins_sensor_suggestions = designer.suggest_parts(PartType.SENSOR, PartSubType.ROLL | PartSubType.PITCH | PartSubType.HEADING | PartSubType.POSITION)
   velocity_sensor_suggestions = designer.suggest_parts(PartType.SENSOR, PartSubType.GROUND_VELOCITY | PartSubType.WATER_VELOCITY | PartSubType.DEPTH | PartSubType.ALTITUDE)
   bottom_altitude_sensor_suggestions = designer.suggest_parts(PartType.SENSOR, PartSubType.ALTITUDE)
   acoustic_modem_suggestions = designer.suggest_parts(PartType.COMMUNICATIONS, PartSubType.ACOUSTIC)
   gps_receiver_suggestions = designer.suggest_parts(PartType.COMMUNICATIONS, PartSubType.GPS)
   iridium_modem_suggestions = designer.suggest_parts(PartType.COMMUNICATIONS, PartSubType.IRIDIUM)
   nav_computer_suggestions = designer.suggest_parts(PartType.PROCESSOR, PartSubType.GENERAL)
   thruster_suggestions = designer.suggest_parts(PartType.PROPULSION, PartSubType.ACTIVE)

   designer.add_part(sat_antenna_suggestions[0], 'sat_antenna')
   designer.add_part(ins_sensor_suggestions[2], 'ins_sensor')
   designer.add_part(velocity_sensor_suggestions[2], 'velocity_sensor')
   designer.add_part(bottom_altitude_sensor_suggestions[0], 'altitude_sensor')
   designer.add_part(acoustic_modem_suggestions[0], 'acoustic_modem')
   designer.add_part(gps_receiver_suggestions[0], 'gps_receiver')
   designer.add_part(iridium_modem_suggestions[0], 'iridium_modem')
   designer.add_part(nav_computer_suggestions[0], 'nav_computer')
   designer.add_part(thruster_suggestions[0], 'thruster')
   designer.add_part('Ocean Bottom Seismometer', 'obs_payload')

   print('   Satellite Antenna:', sat_antenna_suggestions[0].name)
   print('   INS Sensor:', ins_sensor_suggestions[2].name)
   print('   Velocity and Depth Sensor:', velocity_sensor_suggestions[2].name)
   print('   Altitude Sensor:', bottom_altitude_sensor_suggestions[0].name)
   print('   Acoustic Beacon Modem:', acoustic_modem_suggestions[0].name)
   print('   GPS Receiver:', gps_receiver_suggestions[0].name)
   print('   Iridium Modem:', iridium_modem_suggestions[0].name)
   print('   Navigation Computer:', nav_computer_suggestions[0].name)
   print('   Thruster:', thruster_suggestions[0].name)
   print('   Payload:', 'Ocean Bottom Seismometer')



   # STEP 5: Add or remove detachable parts from each mission stage ---------------------------------------------------
   input('   Press ENTER to continue...')
   print('\nSTEP 5: Add or remove detachable parts from each mission stage...')

   for stage in designer.mission:
      if stage.name == 'return':
         for part in designer.required_parts.parts_list:
            if part.name == 'obs_payload':
               part.remove_from_mission_stage(stage)
               print('   Removed "{}" from Mission Stage "{}"'.format(part.name, stage.name))



   # STEP 6: Set activation profiles for all energy consuming parts ---------------------------------------------------
   input('   Press ENTER to continue...')
   print('\nSTEP 6: Set activation profiles for all energy consuming parts...')

   # Create some reusable sensor activation profiles
   for stage in designer.mission:
      if stage.name == 'departure':
         departure_stage = stage
      elif stage.name == 'payload_drop':
         payload_stage = stage
      else:
         return_stage = stage
   departure_always_on_profile = ActivationProfile('').add_mission_stage_profile_percentage(departure_stage, 1, ActivationInterval.PER_MISSION_STAGE, 1.0)
   payload_always_on_profile = ActivationProfile('').add_mission_stage_profile_percentage(payload_stage, 1, ActivationInterval.PER_MISSION_STAGE, 1.0)
   return_always_on_profile = ActivationProfile('').add_mission_stage_profile_percentage(return_stage, 1, ActivationInterval.PER_MISSION_STAGE, 1.0)
   departure_always_off_profile = ActivationProfile('').add_mission_stage_profile_deactivated(departure_stage)
   payload_always_off_profile = ActivationProfile('').add_mission_stage_profile_deactivated(payload_stage)
   return_always_off_profile = ActivationProfile('').add_mission_stage_profile_deactivated(return_stage)

   # Set the activation profile for all sensors for each mission stage
   for part in designer.required_parts.parts_list:
      if part.name == 'ins_sensor' or part.name == 'velocity_sensor' or part.name == 'nav_computer':
         print('   Part:', part.name, '\n', '     Stage: departure, Activation: ALWAYS ON\n      Stage: payload_drop, Activation: ALWAYS_ON\n      Stage: return, Activation: ALWAYS_ON')
         part.set_activation_profile(departure_always_on_profile)
         part.set_activation_profile(payload_always_on_profile)
         part.set_activation_profile(return_always_on_profile)
      elif part.name == 'altitude_sensor':
         print('   Part:', part.name, '\n', '     Stage: departure, Activation: ALWAYS OFF\n      Stage: payload_drop, Activation: ALWAYS_ON\n      Stage: return, Activation: ALWAYS_OFF')
         part.set_activation_profile(departure_always_off_profile)
         part.set_activation_profile(payload_always_on_profile)
         part.set_activation_profile(return_always_off_profile)
      elif part.name == 'acoustic_modem':
         print('   Part:', part.name, '\n', '     Stage: departure, Activation: 3x PER DAY for 5 MINUTES EACH\n      Stage: payload_drop, Activation: ALWAYS_OFF\n      Stage: return, Activation: 3x PER DAY for 5 MINUTES EACH')
         part.set_activation_profile(ActivationProfile('').add_mission_stage_profile_concrete(departure_stage, 3, ActivationInterval.PER_DAY, 300))
         part.set_activation_profile(payload_always_off_profile)
         part.set_activation_profile(ActivationProfile('').add_mission_stage_profile_concrete(return_stage, 3, ActivationInterval.PER_DAY, 300))
      elif part.name == 'gps_receiver':
         print('   Part:', part.name, '\n', '     Stage: departure, Activation: 1x PER MISSION for 5 MINUTES\n      Stage: payload_drop, Activation: ALWAYS_OFF\n      Stage: return, Activation: ALWAYS_OFF')
         part.set_activation_profile(ActivationProfile('').add_mission_stage_profile_concrete(departure_stage, 1, ActivationInterval.PER_MISSION_STAGE, 300))
         part.set_activation_profile(payload_always_off_profile)
         part.set_activation_profile(return_always_off_profile)
      elif part.name == 'iridium_modem':
         print('   Part:', part.name, '\n', '     Stage: departure, Activation: ALWAYS OFF\n      Stage: payload_drop, Activation: ALWAYS_OFF\n      Stage: return, Activation: 1x PER MISSION for 5 MINUTES')
         part.set_activation_profile(departure_always_off_profile)
         part.set_activation_profile(payload_always_off_profile)
         part.set_activation_profile(ActivationProfile('').add_mission_stage_profile_concrete(return_stage, 1, ActivationInterval.PER_MISSION_STAGE, 300))



   # STEP 7: Select propulsion method ---------------------------------------------------------------------------------
   input('   Press ENTER to continue...')
   print('\nSTEP 7: Select propulsion method...')

   suggested_propulsion_type = designer.suggest_propulsion_type()
   designer.set_propulsion_type(suggested_propulsion_type)
   print('   Suggested propulsion type is {}'.format(suggested_propulsion_type.name))
   print('   Propulsion type set to {}'.format(suggested_propulsion_type.name))



   # STEP 8: Finalize list of non-predefined components and component types -------------------------------------------
   input('   Press ENTER to continue...')
   print('\nSTEP 8: Finalize list of non-predefined components and component types...')

   print('   Additional parts options:')
   variable_parts_options = designer.suggest_additional_parts()
   for option_number, parts_option in enumerate(variable_parts_options):
      print('      Option #{}:'.format(option_number))
      for part_option in parts_option:
         print('         {}'.format(part_option.name))
   designer.finalize_additional_parts_options(variable_parts_options)



   # STEP 9: Make discrete choices as necessary -----------------------------------------------------------------------
   input('   Press ENTER to continue...')
   print('\nSTEP 9: Make discrete choices as necessary...')

   discrete_choice_options = designer.suggest_discrete_choice_options()
   for part_type, material in discrete_choice_options.items():
      print('   Suggested material for {}: {}'.format(part_type, material.selected_option))
   designer.select_discrete_choice_options(discrete_choice_options)

   part_count_suggestions = designer.suggest_part_counts_to_explore()
   for part_type, counts in part_count_suggestions.items():
      print('   Suggested range of {} parts to explore: {}'.format(part_type, counts))
   designer.set_part_counts_to_explore(part_count_suggestions)
   input('   Press ENTER to continue...')

   print('\n   Final list of parts permutations:')
   for option_number, parts_option in enumerate(variable_parts_options):
      print('      Option #{}:'.format(option_number))
      for part_option in parts_option:
         print('         {}'.format(part_option.name))
   # TODO: Allow user to add additional attachment points/connection ports/constraints to each part



   # STEP 10: Determine which high-level architecture to explore further ----------------------------------------------
   input('   Press ENTER to continue...')
   print('\nSTEP 10: Determine which high-level architecture to explore further...')

   # TODO: Tool will provide a set of possible component types, placements, and arrangements in graphical form
   # TODO: Tool will provide a set of tradeoff studies in graph form



   # STEP 11: Determine which concrete design to explore further ------------------------------------------------------
   input('   Press ENTER to continue...')
   print('\nSTEP 11: Determine which concrete design to explore further...')

   # TODO: Properly size the propulsion engines, call set_input_voltage on all power consuming parts to make them match each other and battery packs
   # TODO: Allow user to add additional attachment points/connection ports/constraints to each part
   # TODO: Tool will generate point cloud of valid designs pruned along pareto fronts defined by the performance metrics to optimize, user can view tradeoff graphs
   # TODO: Allow user to select a concrete design and move parts around/change lengths/geometries for quick update with "correct" updated placements



   # STEP 12: Concretely define attachment mechanisms -----------------------------------------------------------------
   input('   Press ENTER to continue...')
   print('\nSTEP 12: Concretely define attachment mechanisms...')

   # TODO: Tool will suggest placement of screws and bolts
   # TODO: User can verify, change, or choose specific type of screw for each attachment



   # STEP 13: Adjust cable and wire routing ---------------------------------------------------------------------------
   input('   Press ENTER to continue...')
   print('\nSTEP 13: Adjust cable and wire routing...')



   # STEP 14: Retrieve final design -----------------------------------------------------------------------------------
   input('   Press ENTER to continue...')
   print('\nSTEP 14: Retrieve final design...')

   # TODO: Tool will highly optimize fairing shape and use resulting Cd values to minimally adjust internal components
   # TODO: Final cable routing
