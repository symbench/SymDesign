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

from constraint_prog.point_cloud import PointFunc
from symdesign.core.Designer import Designer, PropulsionType
from symdesign.core.Mission import MissionStage, MissionTarget
from symdesign.core.Performance import OptimizationParameter, OptimizationMode
from symdesign.materials import BallastMaterial, BatteryCell, BuoyancyMaterial
from symdesign.materials import IncompressibleFluid, PressureMaterial, StructuralMaterial
from symdesign.models.MaterialUnderPressure import MaterialUnderPressure
from symdesign.models.Energy import get_power_consumption, get_vehicle_drag
from symdesign.parts import PartType
from symdesign.core.Activation import ActivationProfile, ActivationInterval
from symcad.parts import CatPumps3CP1221Pump
from typing import Dict, Tuple, Union
from pathlib import Path
import json, math, sympy, sys

# Custom constants from STR
REFERENCE_COEFFICIENT_OF_DRAG = 0.00277
INTER_SENSOR_SPACING_M = 0.375
TOWED_ARRAY_DIAMETER_M = 0.0075

# Custom water density model from STR
def water_density_model(_latitude_deg: float, _longitude_deg: float, depth_m: float) -> float:
   return 1030.0 + (20.0 * (depth_m / 4000.0))

# Custom standoff distance for TowedArray from STR
def calculate_additional_transit_distance_km(num_localization_points: int,
                                             localization_point_distance_from_waypoints_m: float,
                                             allowable_localization_error_m: float,
                                             num_towed_sensors: Union[sympy.Expr, int]) -> Union[sympy.Expr, float]:
   return 0.001 * 2.0 * num_localization_points * \
      (localization_point_distance_from_waypoints_m - (0.5 * (allowable_localization_error_m * num_towed_sensors)))

# Custom TowedArray drag model from STR
def calculate_additional_drag(water_density_kg_per_m3: float,
                              towed_array_diameter_m: float,
                              inter_sensor_spacing_m: float,
                              reference_coefficient_of_drag: float,
                              speed_m_per_sec: Union[sympy.Expr, float],
                              num_towed_sensors: Union[sympy.Expr, int]) -> Union[sympy.Expr, float]:
   towed_array_length_m = (num_towed_sensors - 1) * inter_sensor_spacing_m
   return (0.5 * water_density_kg_per_m3 * speed_m_per_sec**1.931 * math.pi *
           towed_array_diameter_m * towed_array_length_m * reference_coefficient_of_drag) + \
          (2.96 * speed_m_per_sec**1.963)

def determine_neutral_cg_cb_values(designer: Designer, concrete_values: Dict[str, float]) -> Tuple[Tuple[float, float, float]]:
   equations = {}
   for stage in designer.mission:
      equations[stage.name] = {}
      designer.set_mission_stage(stage)
      if 'payload' not in stage.name:
         cg_cb_x_diff = 1000000
         for i in range(1, 99):
            designer.set_state(['buoyancy_percent_' + str(i)])
            cg = designer.center_of_gravity(stage, concrete_values)
            cb = designer.center_of_buoyancy(stage, concrete_values)
            if abs(cg.x - cb.x) < cg_cb_x_diff:
               cg_cb_x_diff = abs(cg.x - cb.x)
               equations[stage.name]['stage_neutral_angle_mass_percent'] = i
               equations[stage.name]['neutral_center_of_gravity'] = cg
               equations[stage.name]['neutral_center_of_buoyancy'] = cb
   departure_neutral_cg = equations[departure_stage.name]['neutral_center_of_gravity']
   departure_neutral_cb = equations[departure_stage.name]['neutral_center_of_buoyancy']
   return_neutral_cg = equations[return_stage.name]['neutral_center_of_gravity']
   return_neutral_cb = equations[return_stage.name]['neutral_center_of_buoyancy']
   departure_neutral_cg = float(departure_neutral_cg.x), float(departure_neutral_cg.y), float(departure_neutral_cg.z)
   departure_neutral_cb = float(departure_neutral_cb.x), float(departure_neutral_cb.y), float(departure_neutral_cb.z)
   return_neutral_cg = float(return_neutral_cg.x), float(return_neutral_cg.y), float(return_neutral_cg.z)
   return_neutral_cb = float(return_neutral_cb.x), float(return_neutral_cb.y), float(return_neutral_cb.z)
   return departure_neutral_cg, departure_neutral_cb, return_neutral_cg, return_neutral_cb


if __name__ == '__main__':

   # Determine whether this design should use an internal or external towed array
   if len(sys.argv) != 2:
      print('USAGE: python3 ./tests/2022-Aug-Hackathon/design.py [TOWED_ARRAY_IS_INTERNAL]')
      sys.exit(0)
   is_towed_array_internal = sys.argv[1] == '1' or sys.argv[1].lower() == 'true' or sys.argv[1].lower() == 'yes'
   power_consumption_model_name = 'internal' if is_towed_array_internal else 'external'

   # Instantiate designer instance for prop-based propulsion
   designer = Designer()
   designer.set_propulsion_type(PropulsionType.PROPELLER)

   # Instantiate STR-based custom requirements
   num_towed_array_sensors = sympy.Symbol('num_towed_array_sensors')

   # Instantiate mission stages and requirements
   file_path = str(Path(__file__).parent.resolve())
   bathymetry_file_path = file_path + '/bathymetry/bathymetry_lat60-90.npz'
   currents_file_path = file_path + '/ocean_currents/ocean_currents.npz'
   waypoint_file_paths = {'departure': file_path + '/waypoints/departure_waypoints.pkl',
                          'payload_drop': file_path + '/waypoints/payload_drop_waypoints.pkl',
                          'return': file_path + '/waypoints/return_waypoints.pkl'}
   for stage_name, waypoint_file in waypoint_file_paths.items():
      mission_stage = MissionStage(stage_name, [MissionTarget.EXACT_DISTANCE])
      if stage_name == 'departure':
         num_acoustic_beacons = 5
         departure_stage = mission_stage
      elif stage_name == 'payload_drop':
         num_acoustic_beacons = 0
         payload_stage = mission_stage
      else:
         num_acoustic_beacons = 6
         return_stage = mission_stage
      mission_stage.maximum_depth = 1300.0
      mission_stage.maximum_roll_angle = 0.0
      mission_stage.maximum_pitch_angle = 30.0
      mission_stage.load_waypoints_and_custom_density(waypoint_file, bathymetry_file_path, currents_file_path, water_density_model)
      mission_stage.target_distance = mission_stage.minimum_distance = mission_stage.maximum_distance = \
         mission_stage.target_distance + calculate_additional_transit_distance_km(num_acoustic_beacons, 20000.0, 100.0, num_towed_array_sensors)
      designer.add_mission_stage(mission_stage)
   designer.mission.maximum_average_horizontal_speed = 2.0
   designer.mission.maximum_duration = 60 * 24 * 60 * 60
   designer.mission.finalize()

   # Define desired optimizations
   designer.optimize_for(OptimizationParameter.MASS, OptimizationMode.MINIMIZE)
   designer.optimize_for(OptimizationParameter.VOLUME, OptimizationMode.MINIMIZE)
   designer.optimize_for(OptimizationParameter.POWER_CONSUMPTION, OptimizationMode.MINIMIZE)
   designer.optimize_for(OptimizationParameter.POWER_RESERVE, OptimizationMode.TARGET, 0.2)
   designer.optimize_for(OptimizationParameter.PRESSURE_VESSEL_VOLUME_TO_MASS, OptimizationMode.MAXIMIZE)

   # Instantiate all required parts
   dvl = designer.add_part('Teledyne Tasman DVL 600kHz', 'dvl')
   ins = designer.add_part('iXblue Phins Compact C7', 'ins')
   acoustic_modem = designer.add_part('Teledyne Benthos ATM 926 Modem', 'acoustic_modem')
   sat_antenna = designer.add_part('Trident Sensors Dual GPS/Iridium Antenna', 'sat_antenna')
   gps_receiver = designer.add_part('Garmin 15H GPS Receiver', 'gps_receiver')
   iridium_radio = designer.add_part('Iridium Core 9523 Radio', 'iridium_radio')
   nav_computer = designer.add_part('Raspberry Pi Zero 2W', 'nav_computer')
   thruster = designer.add_part('Tecnadyne Model 2061', 'thruster')
   obs_payload = designer.add_part('Ocean Bottom Seismometer', 'obs_payload')
   obs_counterweight = designer.add_part('Cylindrical Syntactic Foam Pack', 'obs_counterweight')
   stabilizer_fin = designer.add_part('Stabilizer Fin', 'stabilizer_fin')
   control_rudders = designer.add_part('X-Form Rudders', 'control_rudders')
   buoyancy_engine = designer.add_part('Mass-Based Buoyancy Engine', 'buoyancy_engine',
                                                                     pump_cad_model=CatPumps3CP1221Pump('pump'),
                                                                     motor_cad_model=CatPumps3CP1221Pump('motor'))
   pv_small_elec = designer.add_part('Pressurized Container Vessel', 'pressure_vessel_small_elec')
   pv_large_elec = designer.add_part('Pressurized Container Vessel', 'pressure_vessel_large_elec')
   battery_low_voltage = designer.add_part('Static Battery Pack', 'battery_pack_low_voltage')
   battery_high_voltage = designer.add_part('Static Battery Pack', 'battery_pack_high_voltage')
   buoyancy_pack = designer.add_part('Cylindrical Syntactic Foam Pack', 'buoyancy_pack')
   fairing = designer.add_part('Base Fairing Shape', 'fairing')

   # Define when the payload is dropped
   designer.remove_part_from_mission_stage(obs_payload, return_stage)
   designer.remove_part_from_mission_stage(obs_counterweight, return_stage)

   # Set the activation profile for all sensors for each mission stage
   for part in designer.required_parts.parts_list:
      if part.name == 'ins' or part.name == 'nav_computer':
         profile = ActivationProfile('')
         profile.add_mission_stage_profile_percentage(departure_stage, 1, ActivationInterval.PER_MISSION_STAGE, 1.0)
         profile.add_mission_stage_profile_percentage(payload_stage, 1, ActivationInterval.PER_MISSION_STAGE, 1.0)
         profile.add_mission_stage_profile_percentage(return_stage, 1, ActivationInterval.PER_MISSION_STAGE, 1.0)
         part.set_activation_profile(profile)
      elif part.name == 'dvl':
         profile = ActivationProfile('')
         profile.add_mission_stage_profile_percentage(departure_stage, 1, ActivationInterval.PER_MISSION_STAGE, 0.8)
         profile.add_mission_stage_profile_percentage(payload_stage, 1, ActivationInterval.PER_MISSION_STAGE, 1.0)
         profile.add_mission_stage_profile_percentage(return_stage, 1, ActivationInterval.PER_MISSION_STAGE, 0.8)
         part.set_activation_profile(profile)
      elif part.name == 'acoustic_modem':
         profile = ActivationProfile('')
         profile.add_mission_stage_profile_concrete(departure_stage, 3, ActivationInterval.PER_DAY, 300)
         profile.add_mission_stage_profile_deactivated(payload_stage)
         profile.add_mission_stage_profile_concrete(return_stage, 3, ActivationInterval.PER_DAY, 300)
         part.set_activation_profile(profile)
      elif part.name == 'gps_receiver':
         profile = ActivationProfile('')
         profile.add_mission_stage_profile_concrete(departure_stage, 1, ActivationInterval.PER_MISSION_STAGE, 300)
         profile.add_mission_stage_profile_deactivated(payload_stage)
         profile.add_mission_stage_profile_deactivated(return_stage)
         part.set_activation_profile(profile)
      elif part.name == 'iridium_radio':
         profile = ActivationProfile('')
         profile.add_mission_stage_profile_deactivated(departure_stage)
         profile.add_mission_stage_profile_deactivated(payload_stage)
         profile.add_mission_stage_profile_concrete(return_stage, 1, ActivationInterval.PER_MISSION_STAGE, 300)
         part.set_activation_profile(profile)

   # Make all necessary discrete choices
   best_foam_material = None
   max_depth = max([stage.maximum_depth for stage in designer.mission])
   for option_name, option_parameters in BuoyancyMaterial().options.items():
      if option_parameters['depth_rating_m'] > max_depth:
         best_foam_material = BuoyancyMaterial().select(option_name)
         break
   designer.select_discrete_choice_options({
      PartType.BATTERY: BatteryCell().select('DD'),
      PartType.CONTAINER: StructuralMaterial().select('Carbon-Graphite'),
      PartType.DYNAMIC_BUOYANCY: IncompressibleFluid().select('Seawater'),
      PartType.FAIRING: StructuralMaterial().select('Carbon-Graphite'),
      PartType.PRESSURIZED: PressureMaterial().select('Aluminum-6061-T6'),
      PartType.PROPULSION: IncompressibleFluid().select('Seawater'),
      PartType.PITCH_CONTROL: BallastMaterial().select('Lead'),
      PartType.ROLL_CONTROL: BallastMaterial().select('Lead'),
      PartType.STATIC_WEIGHT: BallastMaterial().select('Lead'),
      PartType.STATIC_BUOYANCY: best_foam_material
   })

   # Determine required battery pack voltages
   battery_voltage_requirements = []
   voltage_ranges = [part.allowable_voltage_range for part in designer.required_parts.parts_list if part.allowable_voltage_range]
   while voltage_ranges:
      valid_sets = {}
      for voltage in range(int(min(map(min, voltage_ranges))), int(0.5 + max(map(max, voltage_ranges))) + 1):
         valid_sets[voltage] = { voltage_idx for voltage_idx, voltage_range in enumerate(voltage_ranges)
                                 if voltage >= voltage_range[0] and voltage <= voltage_range[1] }
      valid_voltages = [ voltage for voltage, indices in valid_sets.items()
                           if len(indices) == max([len(val) for val in valid_sets.values()]) ]
      min_voltage = max_voltage = valid_voltages[0]
      for voltage in valid_voltages:
         if valid_sets[voltage] == valid_sets[min_voltage] and max_voltage >= (voltage - 1):
            max_voltage = voltage
      battery_voltage_requirements.append((min_voltage, max_voltage))
      for range_idx in reversed(list(valid_sets[min_voltage])):
         voltage_ranges.pop(range_idx)
      designer.battery_pack_voltages = [sum(ranges) / 2 for ranges in battery_voltage_requirements]
   low_voltage_level = sorted(designer.battery_pack_voltages)[1]
   high_voltage_level = sorted(designer.battery_pack_voltages)[2]
   for part in designer.required_parts.parts_list:
      if part.allowable_voltage_range is not None:
         part.power_usage_profile.set_input_voltage(low_voltage_level if part.allowable_voltage_range[0] < 42 else high_voltage_level)

   # Force any geometric constants
   fairing_thickness = 0.005
   fairing_nose_tip_radius = 0.1
   fairing_nose_length = (0.7 * acoustic_modem.sympart.unoriented_length) + obs_payload.sympart.unoriented_height
   fairing_body_radius = (0.5 * obs_payload.sympart.unoriented_width) + fairing_thickness
   fairing_tail_tip_radius = 0.5 * thruster.sympart.unoriented_height
   fairing_tail_length = 0.5
   pv_small_cylinder_thickness = MaterialUnderPressure.minimum_cylinder_thickness(PressureMaterial().select('Aluminum-6061-T6'), 1300.0, (0.5 * obs_payload.sympart.unoriented_width))
   pv_large_cylinder_thickness = MaterialUnderPressure.minimum_cylinder_thickness(PressureMaterial().select('Aluminum-6061-T6'), 1300.0, (0.5 * obs_payload.sympart.unoriented_width))
   pv_small_endcap_thickness = MaterialUnderPressure.minimum_semiellipsoidal_endcap_thickness(PressureMaterial().select('Aluminum-6061-T6'), 1300.0, (0.5 * obs_payload.sympart.unoriented_width))
   pv_large_endcap_thickness = MaterialUnderPressure.minimum_semiellipsoidal_endcap_thickness(PressureMaterial().select('Aluminum-6061-T6'), 1300.0, (0.5 * obs_payload.sympart.unoriented_width))
   required_counterweight_volume = (obs_payload.mass - (obs_payload.displaced_volume * water_density_model(0, 0, 600))) / (water_density_model(0, 0, 600) - obs_counterweight.buoyancy_material.get_density())
   required_counterweight_height = required_counterweight_volume / (math.pi * (0.5 * obs_payload.sympart.unoriented_width)**2)
   control_rudders.set_geometry(max_thickness_percent=0.1, chord_length_m=0.3, span_m=(0.5*fairing_body_radius), separation_radius_m=(0.75 * (fairing_body_radius + fairing_tail_tip_radius)), curvature_tilt_deg=(90.0 - math.degrees(math.atan2(fairing_tail_length, fairing_body_radius - fairing_tail_tip_radius))))
   stabilizer_fin.set_geometry(height_m=(0.7 * fairing_body_radius), lower_length_m=0.3, thickness_m=0.1, upper_length_m=0.1)
   obs_counterweight.set_geometry(radius_m=(0.5 * obs_payload.sympart.unoriented_width), height_m=required_counterweight_height)
   buoyancy_engine.set_geometry(reservoir_radius_m=(0.5 * obs_payload.sympart.unoriented_width)-pv_small_cylinder_thickness, reservoir_length_m=None)
   buoyancy_pack.set_geometry(radius_m=(0.5 * obs_payload.sympart.unoriented_width), height_m=None)
   battery_low_voltage.set_geometry(radius_m=(0.5 * obs_payload.sympart.unoriented_width)-pv_small_cylinder_thickness, height_m=0.112)
   battery_high_voltage.set_geometry(radius_m=(0.5 * obs_payload.sympart.unoriented_width)-pv_large_cylinder_thickness, height_m=None)
   pv_small_elec.set_geometry(cylinder_radius_m=(0.5 * obs_payload.sympart.unoriented_width), cylinder_length_m=((0.0*battery_low_voltage.sympart.unoriented_height)+(1.0*buoyancy_engine.sympart.unoriented_length)), cylinder_thickness_m=pv_small_cylinder_thickness, endcap_thickness_m=pv_small_endcap_thickness, endcap_radius_m=None)
   pv_large_elec.set_geometry(cylinder_radius_m=(0.5 * obs_payload.sympart.unoriented_width), cylinder_length_m=None, cylinder_thickness_m=pv_large_cylinder_thickness, endcap_thickness_m=pv_large_endcap_thickness, endcap_radius_m=None)
   fairing.set_geometry(nose_tip_radius_m=fairing_nose_tip_radius, nose_length_m=fairing_nose_length, body_radius_m=fairing_body_radius, body_length_m=(pv_small_elec.sympart.unoriented_length+pv_large_elec.sympart.unoriented_length+buoyancy_pack.sympart.unoriented_height+obs_counterweight.sympart.unoriented_height), tail_tip_radius_m=fairing_tail_tip_radius, tail_length_m=fairing_tail_length, thickness_m=fairing_thickness)

   # Define any additional required attachment points
   fairing.add_attachment_point('nose_tip', x=0, y=0.5, z=0.5)
   fairing.add_attachment_point('tail_tip', x=1, y=0.5, z=0.5)
   fairing.add_attachment_point('tail_quarter', x=1.0-(0.75*fairing.sympart.geometry.tail_length/fairing.sympart.unoriented_length), y=0.5, z=0.5)
   fairing.add_attachment_point('body_front_center', x=fairing.sympart.geometry.nose_length/fairing.sympart.unoriented_length, y=0.5, z=0.5)
   fairing.add_attachment_point('body_top_back', x=1.0-(fairing.sympart.geometry.tail_length/fairing.sympart.unoriented_length), y=0.5, z=1)
   dvl.add_attachment_point('attachment_front', x=0, y=0.5, z=(161.4/174.0))
   ins.add_attachment_point('attachment_pv', x=0.5, y=0.5, z=-0.1)
   acoustic_modem.add_attachment_point('attachment_center', x=0.5, y=0.5, z=0.5)
   sat_antenna.add_attachment_point('attachment_point', x=0, y=0.5, z=(19.0/169.0))
   thruster.add_attachment_point('attachment_center', x=(280.0/342.0), y=0.5, z=0.5)
   control_rudders.add_attachment_point('attachment_front', x=0, y=0.5, z=0.5)
   stabilizer_fin.add_attachment_point('attachment_rear', x=1, y=0.5, z=0)
   obs_payload.add_attachment_point('attachment_back', x=0.5, y=0.5, z=1)\
              .add_attachment_point('back_center_middle', x=0.5, y=0.5, z=0.85)
   obs_counterweight.add_attachment_point('attachment_front', x=0.5, y=0.5, z=1)\
                    .add_attachment_point('attachment_back', x=0.5, y=0.5, z=0)\
                    .add_attachment_point('attachment_back_top', x=1, y=0.5, z=0)\
                    .add_attachment_point('attachment_back_bottom', x=0, y=0.5, z=0)
   pv_small_elec.add_attachment_point('body_center_back', x=1.0-(pv_small_elec.sympart.geometry.endcap_radius/pv_small_elec.sympart.unoriented_length), y=0.5, z=0.5)\
                .add_attachment_point('front_center', x=0, y=0.5, z=0.5)\
                .add_attachment_point('rear_center', x=1, y=0.5, z=0.5)\
                .add_attachment_point('front_center_external', x=0, y=0.5, z=0.5)\
                .add_attachment_point('electronics', x=0.15, y=0.5, z=0.75)
   pv_large_elec.add_attachment_point('center', x=0.5, y=0.5, z=0.5)\
                .add_attachment_point('front_center', x=0, y=0.5, z=0.5)
   battery_low_voltage.add_attachment_point('bottom_front', x=1, y=0.5, z=0)\
                      .add_attachment_point('center_back', x=0.5, y=0.5, z=1)
   battery_high_voltage.add_attachment_point('center', x=0.5, y=0.5, z=0.5)
   gps_receiver.add_attachment_point('pv_attachment_point', x=0, y=0.5, z=0.5)\
               .add_attachment_point('sensor1_attachment_point', x=0, y=1, z=0.5)\
               .add_attachment_point('sensor2_attachment_point', x=0, y=0, z=0.5)
   iridium_radio.add_attachment_point('sensor_attachment_point', x=0, y=0, z=0.5)
   nav_computer.add_attachment_point('sensor_attachment_point', x=0, y=1, z=0.5)
   buoyancy_pack.add_attachment_point('front_center', x=0.5, y=0.5, z=1)\
                .add_attachment_point('rear_center', x=0.5, y=0.5, z=0)
   buoyancy_engine.add_attachment_point('bottom_back', x=0, y=0.5, z=0)

   # Make all static attachments
   obs_payload.attach('attachment_back', obs_counterweight, 'attachment_front')
   pv_small_elec.attach('electronics', gps_receiver, 'pv_attachment_point')
   pv_small_elec.attach('front_center', ins, 'attachment_pv')
   pv_small_elec.attach('body_center_back', battery_low_voltage, 'center_back')
   pv_small_elec.attach('front_center_external', obs_counterweight, 'attachment_back')
   pv_large_elec.attach('center', battery_high_voltage, 'center')
   buoyancy_engine.attach('bottom_back', battery_low_voltage, 'bottom_front')
   buoyancy_pack.attach('front_center', pv_small_elec, 'rear_center')
   buoyancy_pack.attach('rear_center', pv_large_elec, 'front_center')
   gps_receiver.attach('sensor1_attachment_point', iridium_radio, 'sensor_attachment_point')
   gps_receiver.attach('sensor2_attachment_point', nav_computer,'sensor_attachment_point' )
   dvl.attach('attachment_front', obs_counterweight, 'attachment_back_bottom')
   sat_antenna.attach('attachment_point', obs_counterweight, 'attachment_back_top')
   fairing.attach('nose_tip', acoustic_modem, 'attachment_center')
   fairing.attach('tail_tip', thruster, 'attachment_center')
   fairing.attach('tail_quarter', control_rudders, 'attachment_front')
   fairing.attach('body_top_back', stabilizer_fin, 'attachment_rear')
   fairing.attach('body_front_center', obs_payload, 'back_center_middle')

   # Update Towed Array length if internal to fairing
   if is_towed_array_internal:
      num_sensors = 1.0 + ((fairing_nose_length + fairing.sympart.geometry.body_length + fairing_tail_length) / INTER_SENSOR_SPACING_M)
      for stage in designer.mission:
         stage.target_distance = stage.target_distance.subs(num_towed_array_sensors, num_sensors)
         stage.minimum_distance = stage.minimum_distance.subs(num_towed_array_sensors, num_sensors)
         stage.maximum_distance = stage.maximum_distance.subs(num_towed_array_sensors, num_sensors)
      num_towed_array_sensors = num_sensors

   # Create and retrieve some useful equations for each mission stage
   stage_based_equations = {}
   water_density_at_surface = water_density_model(0, 0, 0)
   water_density_near_surface = water_density_model(0, 0, 10)
   water_density_at_depth = water_density_model(0, 0, 1300)
   return_stage.target_average_horizontal_speed = departure_stage.target_average_horizontal_speed
   for stage in designer.mission:
      designer.set_mission_stage(stage)
      if 'payload' not in stage.name:
         stage_based_equations[stage.name] = {}
         stage_based_equations[stage.name]['displaced_water_mass_at_depth'] = designer.displaced_volume(stage) * water_density_at_depth
         stage_based_equations[stage.name]['displaced_water_mass_near_surface'] = designer.displaced_volume(stage) * water_density_near_surface
         stage_based_equations[stage.name]['displaced_water_mass_at_surface'] = designer.displaced_volume(stage) * water_density_at_surface
         stage_based_equations[stage.name]['low_voltage_power_consumption'] = designer.power_consumption(stage, 0, 41)
         stage_based_equations[stage.name]['high_voltage_power_consumption'] = designer.power_consumption(stage, 42, 4000)
         stage_based_equations[stage.name]['distance'] = 1000.0 * stage.target_distance
         stage_based_equations[stage.name]['duration'] = stage.target_duration
         designer.set_state(['buoyancy_percent_99'])
         stage_based_equations[stage.name]['max_mass'] = designer.mass(stage)
         stage_based_equations[stage.name]['max_mass_center_of_gravity'] = designer.center_of_gravity(stage)
         stage_based_equations[stage.name]['max_mass_center_of_buoyancy'] = designer.center_of_buoyancy(stage)
         designer.set_state(['buoyancy_percent_90'])
         stage_based_equations[stage.name]['near_max_mass'] = designer.mass(stage)
         stage_based_equations[stage.name]['near_max_mass_center_of_gravity'] = designer.center_of_gravity(stage)
         stage_based_equations[stage.name]['near_max_mass_center_of_buoyancy'] = designer.center_of_buoyancy(stage)
         designer.set_state(['buoyancy_percent_1'])
         stage_based_equations[stage.name]['min_mass'] = designer.mass(stage)
         stage_based_equations[stage.name]['min_displaced_volume'] = designer.displaced_volume(stage)
         stage_based_equations[stage.name]['min_mass_center_of_gravity'] = designer.center_of_gravity(stage)
         stage_based_equations[stage.name]['min_mass_center_of_buoyancy'] = designer.center_of_buoyancy(stage)
         stage_based_equations[stage.name]['buoyancy_engine_min_mass'] = buoyancy_engine.mass
         stage_based_equations[stage.name]['buoyancy_engine_min_material_volume'] = buoyancy_engine.material_volume
   battery_low_voltage_remaining = battery_low_voltage.power_supply_capacity - sum([equations['low_voltage_power_consumption'] for equations in stage_based_equations.values()])
   battery_high_voltage_remaining = battery_high_voltage.power_supply_capacity - sum([equations['high_voltage_power_consumption'] for equations in stage_based_equations.values()]) - get_power_consumption(power_consumption_model_name, fairing_nose_length, fairing.sympart.geometry.body_length, fairing_tail_length, fairing_body_radius, departure_stage.target_average_horizontal_speed, num_towed_array_sensors)
   battery_low_voltage_remaining_percent = battery_low_voltage_remaining / battery_low_voltage.power_supply_capacity
   battery_high_voltage_remaining_percent = battery_high_voltage_remaining / battery_high_voltage.power_supply_capacity
   total_distance = sum([equations['distance'] for equations in stage_based_equations.values()])
   total_duration = sum([equations['duration'] for equations in stage_based_equations.values()])
   max_mass_departure_cg = stage_based_equations[departure_stage.name]['max_mass_center_of_gravity']
   max_mass_departure_cb = stage_based_equations[departure_stage.name]['max_mass_center_of_buoyancy']
   min_mass_departure_cg = stage_based_equations[departure_stage.name]['min_mass_center_of_gravity']
   min_mass_departure_cb = stage_based_equations[departure_stage.name]['min_mass_center_of_buoyancy']
   near_max_mass_departure_cg = stage_based_equations[departure_stage.name]['near_max_mass_center_of_gravity']
   near_max_mass_departure_cb = stage_based_equations[departure_stage.name]['near_max_mass_center_of_buoyancy']
   max_mass_return_cg = stage_based_equations[return_stage.name]['max_mass_center_of_gravity']
   max_mass_return_cb = stage_based_equations[return_stage.name]['max_mass_center_of_buoyancy']
   min_mass_return_cg = stage_based_equations[return_stage.name]['min_mass_center_of_gravity']
   min_mass_return_cb = stage_based_equations[return_stage.name]['min_mass_center_of_buoyancy']
   near_max_mass_return_cg = stage_based_equations[return_stage.name]['near_max_mass_center_of_gravity']
   near_max_mass_return_cb = stage_based_equations[return_stage.name]['near_max_mass_center_of_buoyancy']
   departure_min_pitch_angle_tan = (max_mass_departure_cg.x - max_mass_departure_cb.x) / (max_mass_departure_cb.z - max_mass_departure_cg.z)
   departure_max_pitch_angle_tan = (min_mass_departure_cg.x - min_mass_departure_cb.x) / (min_mass_departure_cb.z - min_mass_departure_cg.z)
   departure_neutral_pitch_angle_tan = (near_max_mass_departure_cg.x - near_max_mass_departure_cb.x) / (near_max_mass_departure_cb.z - near_max_mass_departure_cg.z)
   return_min_pitch_angle_tan = (max_mass_return_cg.x - max_mass_return_cb.x) / (max_mass_return_cb.z - max_mass_return_cg.z)
   return_max_pitch_angle_tan = (min_mass_return_cg.x - min_mass_return_cb.x) / (min_mass_return_cb.z - min_mass_return_cg.z)
   return_neutral_pitch_angle_tan = (near_max_mass_return_cg.x - near_max_mass_return_cb.x) / (near_max_mass_return_cb.z - near_max_mass_return_cg.z)
   vehicle_length = fairing_nose_length + fairing.sympart.geometry.body_length + fairing_tail_length
   vehicle_diameter = 2.0 * fairing_body_radius

   # Define constraints using symbolic assembly
   designer.add_constraint('mission_time_total', sympy.Le(total_duration, designer.mission.maximum_duration))
   designer.add_constraint('mission_time_and_speed_total', sympy.Eq(departure_stage.target_average_horizontal_speed * total_duration, total_distance))
   designer.add_constraint('mission_time_and_speed_departure', sympy.Eq(departure_stage.target_average_horizontal_speed * stage_based_equations[departure_stage.name]['duration'], stage_based_equations[departure_stage.name]['distance']))
   designer.add_constraint('mission_time_and_speed_return', sympy.Eq(return_stage.target_average_horizontal_speed * stage_based_equations[return_stage.name]['duration'], stage_based_equations[return_stage.name]['distance']))
   designer.add_constraint('battery_reserve_high_voltage', sympy.Eq(battery_high_voltage_remaining_percent, designer.optimization_metrics.optimizing_metrics[OptimizationParameter.POWER_RESERVE][1]))
   designer.add_constraint('departure_buoyancy_at_depth', sympy.Le(stage_based_equations[departure_stage.name]['displaced_water_mass_at_depth'], stage_based_equations[departure_stage.name]['max_mass']))
   designer.add_constraint('departure_buoyancy_at_surface', sympy.Ge(stage_based_equations[departure_stage.name]['displaced_water_mass_at_surface'],  stage_based_equations[departure_stage.name]['min_mass']))
   designer.add_constraint('return_buoyancy_at_depth', sympy.Le(stage_based_equations[return_stage.name]['displaced_water_mass_at_depth'], stage_based_equations[return_stage.name]['max_mass']))
   designer.add_constraint('return_buoyancy_at_surface', sympy.Ge(stage_based_equations[return_stage.name]['displaced_water_mass_at_surface'],  stage_based_equations[return_stage.name]['min_mass']))
   designer.add_constraint('min_pitch_angle_departure', sympy.Le(departure_min_pitch_angle_tan, math.tan(-departure_stage.maximum_pitch_angle * math.pi / 180.0)))
   designer.add_constraint('max_pitch_angle_return', sympy.Ge(return_max_pitch_angle_tan, math.tan(return_stage.maximum_pitch_angle * math.pi / 180.0)))
   #designer.add_constraint('departure_neutral_pitch', sympy.Eq(departure_neutral_pitch_angle_tan, 0.0))
   #designer.add_constraint('departure_neutral_buoyancy', sympy.Eq(stage_based_equations[departure_stage.name]['displaced_water_mass_near_surface'], stage_based_equations[departure_stage.name]['near_max_mass']))

   # Define any pareto pruning functions
   pareto_pruning_functions = PointFunc({
      'mass_kg': stage_based_equations[departure_stage.name]['min_mass'],
      'duration_s': total_duration
      #'min_pitch_departure_tan': departure_min_pitch_angle_tan
      #'volume_m3': fairing.displaced_volume
   })
   positive_pareto_vars = []
   negative_pareto_vars = ['mass_kg', 'duration_s', 'min_pitch_departure_tan']

   # Define the free parameter bounds, resolutions, and derived values of interest
   bounds = {
      'pressure_vessel_large_elec_cylinder_length': (0.0, 2.0),
      'battery_pack_high_voltage_height': (0.2, 2.0),
      'battery_pack_low_voltage_height': (0.112, 1.0),
      'buoyancy_engine_reservoir_length': (0.1, 2.0),
      'buoyancy_pack_height': (0.0, 1.0),
      'departure_duration': (400000.0, 1000000.0),
      'return_duration': (1800000.0, 4500000.0),
      'departure_average_speed': (0.8, 2.0),
      'num_towed_array_sensors': (1.0, 400.0)
   }
   resolutions = {
      'pressure_vessel_large_elec_cylinder_length': 0.001,
      'battery_pack_high_voltage_height': 0.001,
      'battery_pack_low_voltage_height': 0.001,
      'buoyancy_engine_reservoir_length': 0.001,
      'buoyancy_pack_height': 0.001,
      'departure_duration': 1,
      'return_duration': 1,
      'departure_average_speed': 0.01,
      'num_towed_array_sensors': 1.0
   }
   derived_values = {
      'fairing_nose_length': fairing_nose_length,
      'fairing_body_length': fairing.sympart.geometry.body_length,
      'fairing_tail_length': fairing_tail_length,
      'fairing_volume': ((math.pi/3.0) * fairing_nose_length *
                           (fairing_nose_tip_radius**2 + fairing_body_radius**2 +
                              (fairing_nose_tip_radius * fairing_body_radius))) + \
                        ((math.pi/3.0) * fairing_tail_length *
                           (fairing_tail_tip_radius**2 + fairing_body_radius**2 +
                              (fairing_tail_tip_radius * fairing_body_radius))) + \
                        (math.pi * fairing_body_radius**2 * fairing.sympart.geometry.body_length),
      'min_displaced_volume': stage_based_equations[departure_stage.name]['min_displaced_volume'],
      'vehicle_length': vehicle_length,
      'vehicle_diameter': vehicle_diameter,
      'vehicle_drag_original': get_vehicle_drag(fairing_nose_length, fairing.sympart.geometry.body_length, fairing_tail_length, fairing_body_radius, departure_stage.target_average_horizontal_speed),
      'vehicle_drag_optimized': 0.6 * get_vehicle_drag(fairing_nose_length, fairing.sympart.geometry.body_length, fairing_tail_length, fairing_body_radius, departure_stage.target_average_horizontal_speed),
      'departure_duration_days': departure_stage.target_duration / 60 / 60 / 24,
      'return_duration_days': return_stage.target_duration / 60 / 60 / 24,
      'total_duration_days': total_duration / 60 / 60 / 24,
      'energy_low_voltage_capacity': battery_low_voltage.power_supply_capacity,
      'energy_low_voltage_usage': sum([equations['low_voltage_power_consumption'] for equations in stage_based_equations.values()]),
      'energy_low_voltage_remaining': battery_low_voltage_remaining,
      'energy_low_voltage_remaining_percent': battery_low_voltage_remaining_percent,
      'energy_high_voltage_capacity': battery_high_voltage.power_supply_capacity,
      'energy_high_voltage_usage': sum([equations['high_voltage_power_consumption'] for equations in stage_based_equations.values()]) + get_power_consumption(power_consumption_model_name, fairing_nose_length, fairing.sympart.geometry.body_length, fairing_tail_length, fairing_body_radius, departure_stage.target_average_horizontal_speed, num_towed_array_sensors),
      'energy_high_voltage_remaining': battery_high_voltage_remaining,
      'energy_high_voltage_remaining_percent': battery_high_voltage_remaining_percent,
      'departure_neutral_buoyancy_mass': stage_based_equations[departure_stage.name]['near_max_mass'],
      'departure_dry_mass_min': stage_based_equations[departure_stage.name]['min_mass'],
      'departure_dry_mass_max': stage_based_equations[departure_stage.name]['max_mass'],
      'return_dry_mass_min': stage_based_equations[return_stage.name]['min_mass'],
      'return_dry_mass_max': stage_based_equations[return_stage.name]['max_mass'],
      'pressure_vessel_low_voltage_cylinder_length': pv_small_elec.sympart.geometry.cylinder_length,
      'pressure_vessel_low_voltage_endcap_length': pv_small_elec.sympart.geometry.endcap_radius,
      'pressure_vessel_low_voltage_total_length': pv_small_elec.sympart.unoriented_length,
      'pressure_vessel_low_voltage_radius': pv_small_elec.sympart.geometry.cylinder_radius,
      'pressure_vessel_low_voltage_cylinder_thickness': pv_small_cylinder_thickness,
      'pressure_vessel_low_voltage_endcap_thickness': pv_small_endcap_thickness,
      'pressure_vessel_low_voltage_dry_mass': pv_small_elec.mass,
      'pressure_vessel_low_voltage_wet_mass_at_surface': pv_small_elec.mass - (pv_small_elec.displaced_volume * water_density_at_surface),
      'pressure_vessel_low_voltage_wet_mass_at_depth': pv_small_elec.mass - (pv_small_elec.displaced_volume * water_density_at_depth),
      'pressure_vessel_high_voltage_cylinder_length': pv_large_elec.sympart.geometry.cylinder_length,
      'pressure_vessel_high_voltage_endcap_length': pv_large_elec.sympart.geometry.endcap_radius,
      'pressure_vessel_high_voltage_total_length': pv_large_elec.sympart.unoriented_length,
      'pressure_vessel_high_voltage_radius': pv_large_elec.sympart.geometry.cylinder_radius,
      'pressure_vessel_high_voltage_cylinder_thickness': pv_large_cylinder_thickness,
      'pressure_vessel_high_voltage_endcap_thickness': pv_large_endcap_thickness,
      'pressure_vessel_high_voltage_dry_mass': pv_large_elec.mass,
      'pressure_vessel_high_voltage_wet_mass_at_surface': pv_large_elec.mass - (pv_large_elec.displaced_volume * water_density_at_surface),
      'pressure_vessel_high_voltage_wet_mass_at_depth': pv_large_elec.mass - (pv_large_elec.displaced_volume * water_density_at_depth),
      'departure_min_wet_mass_at_depth': stage_based_equations[departure_stage.name]['min_mass'] - stage_based_equations[departure_stage.name]['displaced_water_mass_at_depth'],
      'departure_max_wet_mass_at_depth': stage_based_equations[departure_stage.name]['max_mass'] - stage_based_equations[departure_stage.name]['displaced_water_mass_at_depth'],
      'departure_min_wet_mass_at_surface': stage_based_equations[departure_stage.name]['min_mass'] - stage_based_equations[departure_stage.name]['displaced_water_mass_at_surface'],
      'departure_max_wet_mass_at_surface': stage_based_equations[departure_stage.name]['max_mass'] - stage_based_equations[departure_stage.name]['displaced_water_mass_at_surface'],
      'return_min_wet_mass_at_depth': stage_based_equations[return_stage.name]['min_mass'] - stage_based_equations[return_stage.name]['displaced_water_mass_at_depth'],
      'return_max_wet_mass_at_depth': stage_based_equations[return_stage.name]['max_mass'] - stage_based_equations[return_stage.name]['displaced_water_mass_at_depth'],
      'return_min_wet_mass_at_surface': stage_based_equations[return_stage.name]['min_mass'] - stage_based_equations[return_stage.name]['displaced_water_mass_at_surface'],
      'return_max_wet_mass_at_surface': stage_based_equations[return_stage.name]['max_mass'] - stage_based_equations[return_stage.name]['displaced_water_mass_at_surface'],
      'departure_min_pitch_angle_cg_x': max_mass_departure_cg.x,
      'departure_min_pitch_angle_cg_y': max_mass_departure_cg.y,
      'departure_min_pitch_angle_cg_z': max_mass_departure_cg.z,
      'departure_min_pitch_angle_cb_x': max_mass_departure_cb.x,
      'departure_min_pitch_angle_cb_y': max_mass_departure_cb.y,
      'departure_min_pitch_angle_cb_z': max_mass_departure_cb.z,
      'departure_neutral_pitch_angle_cg_x': near_max_mass_departure_cg.x,
      'departure_neutral_pitch_angle_cg_y': near_max_mass_departure_cg.y,
      'departure_neutral_pitch_angle_cg_z': near_max_mass_departure_cg.z,
      'departure_neutral_pitch_angle_cb_x': near_max_mass_departure_cb.x,
      'departure_neutral_pitch_angle_cb_y': near_max_mass_departure_cb.y,
      'departure_neutral_pitch_angle_cb_z': near_max_mass_departure_cb.z,
      'return_max_pitch_angle_cg_x': min_mass_return_cg.x,
      'return_max_pitch_angle_cg_y': min_mass_return_cg.y,
      'return_max_pitch_angle_cg_z': min_mass_return_cg.z,
      'return_max_pitch_angle_cb_x': min_mass_return_cb.x,
      'return_max_pitch_angle_cb_y': min_mass_return_cb.y,
      'return_max_pitch_angle_cb_z': min_mass_return_cb.z,
      'departure_min_pitch_angle': sympy.atan(departure_min_pitch_angle_tan) * 180.0 / math.pi,
      'departure_max_pitch_angle': sympy.atan(departure_max_pitch_angle_tan) * 180.0 / math.pi,
      'return_min_pitch_angle': sympy.atan(return_min_pitch_angle_tan) * 180.0 / math.pi,
      'return_max_pitch_angle': sympy.atan(return_max_pitch_angle_tan) * 180.0 / math.pi,
      'pv_small_material_volume': pv_small_elec.material_volume,
      'pv_small_displaced_volume': pv_small_elec.displaced_volume,
      'pv_large_material_volume': pv_large_elec.material_volume,
      'pv_large_displaced_volume': pv_large_elec.displaced_volume,
      'stability_fin_dry_mass': stabilizer_fin.mass,
      'stability_fin_wet_mass': stabilizer_fin.mass - (stabilizer_fin.displaced_volume * 1027),
      'stability_fin_material_volume': stabilizer_fin.material_volume,
      'stability_fin_displaced_volume': stabilizer_fin.displaced_volume,
      'rudders_dry_mass': control_rudders.mass,
      'rudders_wet_mass': control_rudders.mass - (control_rudders.displaced_volume * 1027),
      'rudders_material_volume': control_rudders.material_volume,
      'rudders_displaced_volume': control_rudders.displaced_volume,
      'batt1_mass': battery_low_voltage.mass,
      'batt1_material_volume': battery_low_voltage.material_volume,
      'batt2_mass': battery_high_voltage.mass,
      'batt2_material_volume': battery_high_voltage.material_volume,
      'buoyancy_engine_mass': stage_based_equations[departure_stage.name]['buoyancy_engine_min_mass'],
      'buoyancy_engine_material_volume': stage_based_equations[departure_stage.name]['buoyancy_engine_min_material_volume'],
      'num_towed_sensors': num_towed_array_sensors
   }

   # Code segment to allow recreating an existing design
   seed_design = None
   recreate_existing_design = False
   if recreate_existing_design:
      designer.set_mission_stage(departure_stage)
      designer.set_state(['buoyancy_percent_50'])
      seed_design = {
         'pressure_vessel_large_elec_cylinder_length': 0.47315773,
         'battery_pack_high_voltage_height': 0.2,
         'battery_pack_low_voltage_height': 0.112,
         'buoyancy_engine_reservoir_length': 1.012551,
         'buoyancy_pack_height': 0.0,
         'departure_duration': 884876.9,
         'return_duration': 4017228.0,
         'departure_average_speed': 0.8955026,
         'num_towed_array_sensors': 400.0
      }
      #designer.generate_assembly(seed_design).export('Design-{}'.format(str(designer.id)), 'freecad')
      for name, value in derived_values.items():
         try:
            print('{}: {}'.format(name, value.evalf(subs=seed_design) if not isinstance(value, float) and not isinstance(value, int) else value))
         except Exception:
            continue
      departure_neutral_cg, departure_neutral_cb, return_neutral_cg, return_neutral_cb = determine_neutral_cg_cb_values(designer, seed_design)
      print('departure_neutral_cg: {}'.format(departure_neutral_cg))
      print('departure_neutral_cb: {}'.format(departure_neutral_cb))
      print('return_neutral_cg: {}'.format(return_neutral_cg))
      print('return_neutral_cb: {}'.format(return_neutral_cb))
      for part in designer.required_parts.parts_list:
         if part.power_usage_profile is not None:
            print(part.name, part.power_usage_profile.get_wattage())
      exit(0)

   # Generate point cloud of valid designs and pick best design
   designs = designer.generate_valid_designs(True, bounds, resolutions, derived_values, pareto_pruning_functions, positive_pareto_vars, negative_pareto_vars, seed_design)
   design_number = int(input('Enter the index of the design to generate: '))

   # Generate and store the CAD assembly
   optimized_params = designs[design_number]
   departure_neutral_cg, departure_neutral_cb, return_neutral_cg, return_neutral_cb = determine_neutral_cg_cb_values(designer, optimized_params)
   designer.set_mission_stage(departure_stage)
   designer.set_state(['buoyancy_percent_50'])
   assembly = designer.generate_assembly(optimized_params)
   assembly.export('Design-{}'.format(str(designer.id)), 'freecad')

   # Generate the STR-required JSON file
   derived = {}
   for name, value in derived_values.items():
      try:
         derived[name] = float(value.evalf(subs=optimized_params)) if not isinstance(value, float) and not isinstance(value, int) else value
      except Exception:
         continue
   str_json = { 'uuv': {
      'mass': derived['departure_dry_mass_min'],
      'displacement': derived['min_displaced_volume'],
      'volume': derived['fairing_volume'],
      'initialBatteryCapacitykWhr': 0.001 * derived['energy_high_voltage_capacity'],
      'minMass': derived['departure_dry_mass_min'],
      'maxMass': derived['departure_dry_mass_max'],
      'minDisplacement': derived['min_displaced_volume'],
      'maxDisplacement': derived['min_displaced_volume'],
      'zeroPitch': {
         'centerBuoyancy': {
            'x': departure_neutral_cb[0],
            'y': departure_neutral_cb[1],
            'z': departure_neutral_cb[2]
         },
         'centerGravity': {
            'x': departure_neutral_cg[0],
            'y': departure_neutral_cg[1],
            'z': departure_neutral_cg[2]
         }
      },
      'downPitch': {
         'centerBuoyancy': {
            'x': derived['departure_min_pitch_angle_cb_x'],
            'y': derived['departure_min_pitch_angle_cb_y'],
            'z': derived['departure_min_pitch_angle_cb_z']
         },
         'centerGravity': {
            'x': derived['departure_min_pitch_angle_cg_x'],
            'y': derived['departure_min_pitch_angle_cg_y'],
            'z': derived['departure_min_pitch_angle_cg_z']
         }
      },
      'upPitch': {
         'centerBuoyancy': {
            'x': derived['return_max_pitch_angle_cb_x'],
            'y': derived['return_max_pitch_angle_cb_y'],
            'z': derived['return_max_pitch_angle_cb_z']
         },
         'centerGravity': {
            'x': derived['return_max_pitch_angle_cg_x'],
            'y': derived['return_max_pitch_angle_cg_y'],
            'z': derived['return_max_pitch_angle_cg_z']
         }
      },
      'mission2.2': {
         'guidance': 'controlUUV.py',
         'outputCsvFile': 'summary.csv',
         'logfile': 'debug.csv',
         'energyConsumedkWhr': 0,  # TODO: FILL THIS IN: 0.001 * derived_values['energy_high_voltage_usage'],
         'duration_hrs': 24.0 * derived['total_duration_days'],
         'distanceTraveledkm': float(total_distance.evalf(subs=optimized_params)) if not isinstance(total_distance, float) else total_distance
      },
      'hullFairing': {
         'boundingBox': {
            'x': float(fairing.sympart.unoriented_length.evalf(subs=optimized_params)),
            'y': float(fairing.sympart.unoriented_width),
            'z': float(fairing.sympart.unoriented_height)
         },
         'stlFile': 'vanderbilt.stl',
         'cfdResults': [
            {
               'speed': 1.0,
               'angleOfAttack': 0.0,
               'cd': {
                  'pressure': 0,
                  'viscous': 0
               },
               'dragForce': {
                  'pressure': 0,
                  'viscous': 0
               }
            },
            {
               'speed': 1.5,
               'angleOfAttack': 0.0,
               'cd': {
                  'pressure': 0,
                  'viscous': 0
               },
               'dragForce': {
                  'pressure': 0,
                  'viscous': 0
               }
            },
            {
               'speed': 2.0,
               'angleOfAttack': 0.0,
               'cd': {
                  'pressure': 0,
                  'viscous': 0
               },
               'dragForce': {
                  'pressure': 0,
                  'viscous': 0
               }
            }
         ]
      },
      'pressureVessels': [
         {
            'name': 'LV_Container',
            'shape': 'CYLINDER',
            'internalRadius': derived['pressure_vessel_low_voltage_radius'] - derived['pressure_vessel_low_voltage_cylinder_thickness'],
            'sphereThickness': derived['pressure_vessel_low_voltage_endcap_thickness'],
            'cylinderThickness': derived['pressure_vessel_low_voltage_cylinder_thickness'],
            'length': derived['pressure_vessel_low_voltage_total_length'],
            'mass': derived['pressure_vessel_low_voltage_dry_mass'],
            'material': '6061 Aluminum',
            'depth': 1300
         },
         {
            'name': 'HV_Container',
            'shape': 'CYLINDER',
            'internalRadius': derived['pressure_vessel_high_voltage_radius'] - derived['pressure_vessel_high_voltage_cylinder_thickness'],
            'sphereThickness': derived['pressure_vessel_high_voltage_endcap_thickness'],
            'cylinderThickness': derived['pressure_vessel_high_voltage_cylinder_thickness'],
            'length': derived['pressure_vessel_high_voltage_total_length'],
            'mass': derived['pressure_vessel_high_voltage_dry_mass'],
            'material': '6061 Aluminum',
            'depth': 1300
         }
      ]
   }}
   with open('Design-{}.json'.format(str(designer.id)), 'w') as file:
      json.dump(str_json, file, indent=3)
