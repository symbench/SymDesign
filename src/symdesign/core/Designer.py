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
from enum import IntEnum, auto
from sympy import Expr
from symcad.core import Assembly, Coordinate
from typing import Any, Dict, List, Optional, Tuple, Union
from constraint_prog.point_cloud import PointCloud, PointFunc
from .Performance import Metrics, OptimizationMode, OptimizationParameter
from .Material import Material
from .Mission import Mission, MissionStage
from .Parts import Parts, PartsLibrary
from .Power import PowerProfile
from ..materials import BallastMaterial, BatteryCell, BuoyancyMaterial
from ..materials import IncompressibleFluid, PressureMaterial, StructuralMaterial
from ..parts import PartType, PartSubType, Listings
from ..parts.PartListing import PartListing
from .BasePart import BasePart
import copy, itertools, uuid
import numpy, torch

class PropulsionType(IntEnum):
   GLIDER = auto()
   PROPELLER = auto()
   HYBRID = auto()


class Designer(object):
   id: uuid.UUID
   mission: Mission
   propulsion_type: PropulsionType
   optimization_metrics: Metrics
   parts_library: PartsLibrary
   required_parts: Parts
   variable_parts: Dict[PartType, List[BasePart]]
   variable_parts_list: List[List[PartListing]]
   battery_pack_voltages: List[int]
   discrete_choice_selections: Dict[PartType, Material]
   constraints: Dict[str, Expr]
   assembly: Assembly


   def __init__(self) -> None:
      super().__init__()
      self.id = uuid.uuid4()
      self.mission = Mission()
      self.propulsion_type = PropulsionType.PROPELLER
      self.optimization_metrics = Metrics()
      self.parts_library = PartsLibrary()
      self.required_parts = Parts()
      self.variable_parts = {}
      self.variable_parts_list = []
      self.battery_pack_voltages = []
      self.discrete_choice_selections = {}
      self.constraints = {}
      self.assembly = Assembly('Design-' + str(self.id))

   def create_new_part(self, part_name: str, part_type: PartType, part_subtype: PartSubType, symcad_model: str, power_profile: Union[PowerProfile, None], attachment_points: List[Coordinate], extra_parameters: Dict[str, Any]) -> None:
      self.parts_library.add_new_part(part_name, part_type, part_subtype, symcad_model, power_profile, attachment_points, extra_parameters)

   def add_mission_stage(self, stage: MissionStage) -> None:
      self.mission.add_stage(stage)

   def add_part(self, part_description: Union[PartListing, str], identifier: str, **kwargs) -> BasePart:
      part = self.parts_library.create_part(part_description, identifier, self.mission, **kwargs)
      self.required_parts.add_part(part)
      self.assembly.add_part(part.sympart, part.present_stages)
      return part

   def remove_part_from_mission_stage(self, part: BasePart, stage: MissionStage) -> None:
      part.remove_from_mission_stage(stage)
      self.assembly.remove_part_from_collection(part.sympart, stage.name)

   def optimize_for(self, parameter: OptimizationParameter, mode: OptimizationMode, value: Optional[float] = None) -> None:
      self.optimization_metrics.optimize_for(parameter, mode, value)

   def suggest_parts(self, part_type: PartType, part_subtype: PartSubType) -> List[PartListing]:
      return self.parts_library.get_part_suggestions(part_type, part_subtype, self.mission, self.optimization_metrics)

   def suggest_propulsion_type(self) -> PropulsionType:
      # TODO: Have tool parse mission stages and sensors and suggest prop-type
      return PropulsionType.PROPELLER

   def set_propulsion_type(self, propulsion_type: PropulsionType) -> None:
      self.propulsion_type = propulsion_type

   def suggest_additional_parts(self) -> List[List[PartListing]]:

      # Determine how many battery packs are required and their voltages
      battery_voltage_requirements = []
      voltage_ranges = [part.allowable_voltage_range for part in self.required_parts.parts_list if part.allowable_voltage_range]
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
      self.battery_pack_voltages = [sum(ranges) / 2 for ranges in battery_voltage_requirements]

      # Determine lists of options for the various additional part types
      battery_options = []
      pitch_control_options = []
      yaw_control_options = []
      full_control_options = []
      pv_options = []
      stability_fin_options = []
      static_buoyancy_options = []
      dynamic_buoyancy_options = []
      for listing in Listings.get_dynamic_part_listings():
         if PartType.BATTERY in listing.part_type and PartType.ROLL_CONTROL not in listing.part_type:
            battery_options.append(listing)
         if PartType.PITCH_CONTROL in listing.part_type and PartType.ROLL_CONTROL not in listing.part_type and PartType.YAW_CONTROL not in listing.part_type:
            pitch_control_options.append(listing)
         if (PartType.PRESSURIZED | PartType.CONTAINER) in listing.part_type:
            pv_options.append(listing)
         if PartType.STATIC_BUOYANCY in listing.part_type:
            if PartType.ATTACHMENT not in listing.part_type:
               static_buoyancy_options.append(listing)
            else:
               stability_fin_options.append(listing)
         if PartType.DYNAMIC_BUOYANCY in listing.part_type:
            dynamic_buoyancy_options.append(listing)
         if PartType.YAW_CONTROL in listing.part_type and PartType.ROLL_CONTROL not in listing.part_type and PartType.PITCH_CONTROL not in listing.part_type:
            yaw_control_options.append(listing)
         if (PartType.PITCH_CONTROL | PartType.YAW_CONTROL) in listing.part_type:
            full_control_options.append(listing)

      # Ensure that all resulting options do not contain multiples of the same functional type
      parts_options = list(itertools.product(battery_options, pitch_control_options, yaw_control_options, pv_options, stability_fin_options, static_buoyancy_options, dynamic_buoyancy_options))
      for i, parts_option_tuple in enumerate(parts_options):
         parts_option = list(parts_option_tuple)
         battery_found = pitch_control_found = pv_found = static_buoyancy_found = dynamic_buoyancy_found = yaw_control_found = stability_fin_found = False
         for idx, part in enumerate(parts_option):
            battery_found_local = pitch_control_found_local = pv_found_local = static_buoyancy_found_local = dynamic_buoyancy_found_local = yaw_control_found_local = stability_fin_found_local = False
            if PartType.BATTERY in part.part_type:
               if battery_found:
                  parts_option[idx] = None
                  continue
               else:
                  battery_found_local = True
            if PartType.PITCH_CONTROL in part.part_type:
               if pitch_control_found:
                  parts_option[idx] = None
                  continue
               else:
                  pitch_control_found_local = True
            if PartType.PRESSURIZED in part.part_type:
               if pv_found:
                  parts_option[idx] = None
                  continue
               else:
                  pv_found_local = True
            if PartType.STATIC_BUOYANCY in part.part_type and PartType.ATTACHMENT not in part.part_type:
               if static_buoyancy_found:
                  parts_option[idx] = None
                  continue
               else:
                  static_buoyancy_found_local = True
            if PartType.STATIC_BUOYANCY in part.part_type and PartType.ATTACHMENT in part.part_type:
               if stability_fin_found:
                  parts_option[idx] = None
                  continue
               else:
                  stability_fin_found_local = True
            if PartType.DYNAMIC_BUOYANCY in part.part_type:
               if dynamic_buoyancy_found:
                  parts_option[idx] = None
                  continue
               else:
                  dynamic_buoyancy_found_local = True
            if PartType.YAW_CONTROL in part.part_type:
               if yaw_control_found:
                  parts_option[idx] = None
                  continue
               else:
                  yaw_control_found_local = True
            battery_found = battery_found or battery_found_local
            pitch_control_found = pitch_control_found or pitch_control_found_local
            pv_found = pv_found or pv_found_local
            static_buoyancy_found = static_buoyancy_found or static_buoyancy_found_local
            dynamic_buoyancy_found = dynamic_buoyancy_found or dynamic_buoyancy_found_local
            yaw_control_found = yaw_control_found or yaw_control_found_local
            stability_fin_found = stability_fin_found or stability_fin_found_local
         if not battery_found or not pitch_control_found or not pv_found or not static_buoyancy_found or not dynamic_buoyancy_found or not yaw_control_found or not stability_fin_found:
            parts_options[i] = None
         else:
            parts_options[i] = [option for option in parts_option if option is not None]
      parts_options = [option for option in parts_options if option is not None]

      # Remove all duplicate options
      for idx1 in range(len(parts_options)):
         for idx2 in range(idx1 + 1, len(parts_options)):
            if parts_options[idx1] == parts_options[idx2]:
               parts_options[idx1] = None
      parts_options = [listing for listing in parts_options if listing is not None]

      # Add combined control surface options
      new_options = []
      for i, parts_option in enumerate(parts_options):
         skip_part = False
         option_copy = copy.deepcopy(parts_option)
         for idx, part in enumerate(option_copy):
            if (PartType.BATTERY | PartType.PITCH_CONTROL) in part.part_type:
               skip_part = True
            if PartType.PITCH_CONTROL in part.part_type or PartType.YAW_CONTROL in part.part_type:
               option_copy[idx] = None
         if not skip_part:
            option_copy = [option for option in option_copy if option is not None]
            for full_control_option in full_control_options:
               new_option = copy.deepcopy(option_copy)
               new_option.append(full_control_option)
               new_options.append(new_option)
      parts_options.extend(new_options)

      # TODO: Don't need roll control if mission stage roll == 0.0 for all, same for pitch
      # TODO: Battery pack voltage ranges dictate which additional power-consuming parts are available (should match a battery voltage that already exists, if possible)
      # TODO: Determine what parts are released per mission stage, dictates if we need additional syntactic foam (syntactic foam may need to be jettisonably as well), or additional ballast if payload is buoyant, check that net buoyancy requirements don't change after payload is released
      return parts_options

   def finalize_additional_parts_options(self, parts_list: List[List[PartListing]]) -> None:
      self.variable_parts_list = parts_list

   def suggest_discrete_choice_options(self) -> Dict[PartType, Material]:
      # TODO: Make intelligest suggestions here, not just predefined numbers
      needs_battery = needs_container_material = needs_buoyancy_fluid = needs_pitch_weight = needs_roll_weight = False
      needs_pressure_material = needs_propulsion_fluid = needs_ballast_material = needs_syntactic_foam = False
      for parts_option in self.variable_parts_list:
         for part in parts_option:
            if PartType.BATTERY in part.part_type:
               needs_battery = True
            if PartType.CONTAINER in part.part_type and PartType.PRESSURIZED not in part.part_type:
               needs_container_material = True
            if PartType.DYNAMIC_BUOYANCY in part.part_type:
               needs_buoyancy_fluid = True
            if PartType.PITCH_CONTROL in part.part_type and PartType.BATTERY not in part.part_type and PartType.ATTACHMENT not in part.part_type:
               needs_pitch_weight = needs_container_material = True
            if PartType.PRESSURIZED in part.part_type:
               needs_pressure_material = True
            if PartType.PROPULSION in part.part_type and PartSubType.ACTIVE not in part.part_subtype:
               needs_propulsion_fluid = needs_container_material = True
            if PartType.ROLL_CONTROL in part.part_type and PartType.BATTERY not in part.part_type and PartType.ATTACHMENT not in part.part_type:
               needs_roll_weight = needs_container_material = True
            if PartType.STATIC_WEIGHT in part.part_type:
               needs_ballast_material = True
            if PartType.STATIC_BUOYANCY in part.part_type:
               needs_syntactic_foam = True
      discrete_options = { PartType.FAIRING: StructuralMaterial().select('Carbon-Graphite') }
      if needs_battery:
         discrete_options[PartType.BATTERY] = BatteryCell().select('DD')
      if needs_container_material:
         discrete_options[PartType.CONTAINER] = StructuralMaterial().select('Carbon-Graphite')
      if needs_buoyancy_fluid:
         discrete_options[PartType.DYNAMIC_BUOYANCY] = IncompressibleFluid().select('Oil')
      if needs_pitch_weight:
         discrete_options[PartType.PITCH_CONTROL] = BallastMaterial().select('Lead')
      if needs_pressure_material:
         discrete_options[PartType.PRESSURIZED] = PressureMaterial().select('Aluminum-6061-T6')
      if needs_propulsion_fluid:
         discrete_options[PartType.PROPULSION] = IncompressibleFluid().select('Oil')
      if needs_roll_weight:
         discrete_options[PartType.ROLL_CONTROL] = BallastMaterial().select('Lead')
      if needs_ballast_material:
         discrete_options[PartType.STATIC_WEIGHT] = BallastMaterial().select('Lead')
      if needs_syntactic_foam:
         max_depth = max([stage.maximum_depth for stage in self.mission])
         for option_name, option_parameters in BuoyancyMaterial().options.items():
            if option_parameters['depth_rating_m'] > max_depth:
               discrete_options[PartType.STATIC_BUOYANCY] = BuoyancyMaterial().select(option_name)
               break
      return discrete_options

   def select_discrete_choice_options(self, options: Dict[PartType, Material]) -> None:
      self.discrete_choice_selections = options
      for part in self.required_parts.parts_list:
         part.set_discrete_choices(options)

   def suggest_part_counts_to_explore(self) -> Dict[PartType, Tuple[int, int]]:
      # TODO: Something intelligent here
      # TODO: Determine what parts are released per mission stage, dictates if we need additional syntactic foam (syntactic foam may need to be jettisonably as well), or additional ballast if payload is buoyant, check that net buoyancy requirements don't change after payload is released
      return {
         PartType.BATTERY: [len(self.battery_pack_voltages), len(self.battery_pack_voltages)],
         PartType.CONTAINER: [0, 0],
         PartType.STATIC_WEIGHT: [0, 0],
         PartType.STATIC_BUOYANCY: [1, 3],
         PartType.PRESSURIZED: [1, 1 + int(len(self.battery_pack_voltages) / 2)]
      }

   def set_part_counts_to_explore(self, part_counts: Dict[PartType, Tuple[int, int]]) -> None:

      battery_options, container_options, pv_options, static_buoyancy_options, static_weight_options = [], [], [], [], []
      for listing in Listings.get_dynamic_part_listings():
         if PartType.BATTERY in listing.part_type and PartType.ROLL_CONTROL not in listing.part_type:
            battery_options.append(listing)
         if PartType.CONTAINER in listing.part_type and PartType.PRESSURIZED not in listing.part_type:
            container_options.append(listing)
         if (PartType.PRESSURIZED | PartType.CONTAINER) in listing.part_type:
            pv_options.append(listing)
         if PartType.STATIC_BUOYANCY in listing.part_type and PartType.ATTACHMENT not in listing.part_type:
            static_buoyancy_options.append(listing)
         if PartType.STATIC_WEIGHT in listing.part_type and PartType.ATTACHMENT not in listing.part_type:
            static_weight_options.append(listing)

      for idx in range(len(self.variable_parts_list)):
         for _ in range(part_counts[PartType.BATTERY][1] - 1):
            self.variable_parts_list[idx].append(battery_options[0])
      for option in copy.deepcopy(self.variable_parts_list):
         for num_additional_parts in range(max(0, part_counts[PartType.CONTAINER][0] - 1), part_counts[PartType.CONTAINER][1]):
            if num_additional_parts > 0:
               new_option = copy.deepcopy(option)
               for _ in range(num_additional_parts):
                  new_option.append(container_options[0])
               self.variable_parts_list.append(new_option)
      for option in copy.deepcopy(self.variable_parts_list):
         for num_additional_parts in range(max(0, part_counts[PartType.PRESSURIZED][0] - 1), part_counts[PartType.PRESSURIZED][1]):
            if num_additional_parts > 0:
               new_option = copy.deepcopy(option)
               for _ in range(num_additional_parts):
                  new_option.append(pv_options[0])
               self.variable_parts_list.append(new_option)
      for option in copy.deepcopy(self.variable_parts_list):
         for num_additional_parts in range(max(0, part_counts[PartType.STATIC_BUOYANCY][0] - 1), part_counts[PartType.STATIC_BUOYANCY][1]):
            if num_additional_parts > 0:
               new_option = copy.deepcopy(option)
               for _ in range(num_additional_parts):
                  new_option.append(static_buoyancy_options[0])
               self.variable_parts_list.append(new_option)
      for option in copy.deepcopy(self.variable_parts_list):
         for num_additional_parts in range(max(0, part_counts[PartType.STATIC_WEIGHT][0] - 1), part_counts[PartType.STATIC_WEIGHT][1]):
            if num_additional_parts > 0:
               new_option = copy.deepcopy(option)
               for _ in range(num_additional_parts):
                  new_option.append(static_weight_options[0])
               self.variable_parts_list.append(new_option)

      max_part_type_and_counts = {}
      for parts_option in self.variable_parts_list:
         part_and_type_counts = {}
         for part in parts_option:
            if part.part_type not in part_and_type_counts:
               part_and_type_counts[part.part_type] = [part, 0]
            part_and_type_counts[part.part_type][1] += 1
         for part_type, part_and_count in part_and_type_counts.items():
            if part_type not in max_part_type_and_counts:
               max_part_type_and_counts[part_type] = [part_and_count[0], 0]
            max_part_type_and_counts[part_type] = [part_and_count[0], max(max_part_type_and_counts[part_type][1], part_and_count[1])]
      for part_type, part_and_count in max_part_type_and_counts.items():
            if part_type not in self.variable_parts:
               self.variable_parts[part_type] = []
            for i in range(len(self.variable_parts[part_type]), part_and_count[1]):
               part = part_and_count[0].create_part(part_and_count[0].name.replace(' ', '_').lower() + str(i), self.mission)
               part.set_discrete_choices(self.discrete_choice_selections)
               self.variable_parts[part_type].append(part)

   def get_num_part_permutations(self) -> int:
      return len(self.variable_parts_list)

   def get_part_permutation(self, permutation_index: int) -> Parts:
      parts = Parts()
      for part in self.required_parts.parts_list:
         parts.add_part(part)
      variable_parts = copy.deepcopy(self.variable_parts)
      for part in self.variable_parts_list[permutation_index]:
         parts.add_part(variable_parts[part.part_type].pop(0))
      return parts

   def add_constraint(self, name: str, constraint: Expr) -> None:
      self.constraints[name] = constraint

   def generate_valid_designs(self, save_design_output: bool, bounds, resolutions, derived_values, pareto_pruning_functions, positive_pareto_vars, negative_pareto_vars, seed_design: Optional[Dict[str, float]] = None) -> List[Dict[str, float]]:

      # Collect constraint equations
      constraints = PointFunc(self.constraints)
      bounds = {key: bounds[key] for key in constraints.input_names if key in bounds.keys()}
      resolutions = {key: resolutions[key] for key in constraints.input_names if key in resolutions.keys()}
      assert list(bounds.keys()) == list(constraints.input_names), 'bounds is missing the following keys: {}'.format(list(set(constraints.input_names) - set(bounds.keys())))
      assert list(resolutions.keys()) == list(constraints.input_names), 'resolutions is missing the following keys: {}'.format(list(set(constraints.input_names) - set(resolutions.keys())))

      # Generate lots of random points
      print('\tGenerating initial design points...')
      if seed_design is not None:
         seed_design = {key: seed_design[key] for key in constraints.input_names if key in seed_design.keys()}
         float_data = torch.tensor(numpy.array([list(seed_design.values())]), dtype=torch.float32)
         points = PointCloud(float_vars=seed_design.keys(), float_data=float_data)
         points.add_mutations(resolutions, 10000, multiplier=2.0)
      else:
         points = PointCloud.generate(bounds, 10000)

      # Set up pareto-pruning specifications
      dirs = []
      if len(pareto_pruning_functions.output_names):
         for var in points.extend(pareto_pruning_functions(points)).float_vars:
            if var in positive_pareto_vars:
               dirs.append(1.0)
            elif var in negative_pareto_vars:
               dirs.append(-1.0)
            else:
               dirs.append(0.0)

      # Minimize errors with Newton-Raphson
      print('\tMinimizing constraint errors...')
      points = points.newton_raphson(constraints, bounds)
      errors = constraints(points)

      # Check constraints with loose tolerance
      print('\tPruning and combining optimized results...')
      points = points.prune_by_tolerances(errors, 0.5)
      pareto_pruned = points.extend(pareto_pruning_functions(points)).prune_pareto_front(dirs) if len(pareto_pruning_functions.output_names) else points
      print('\tNum initial design points: {} (pareto pruned to {})'.format(points.num_points, pareto_pruned.num_points))
      points = pareto_pruned

      # Repeat constraint solving 4 more times
      for step in range(5):
         points.add_mutations(resolutions, 10000, multiplier=1.0)
         points = points.newton_raphson(constraints, bounds)
         points = points.prune_by_tolerances(constraints(points), 0.5 if step <= 2 else 0.1)
         points = points.prune_close_points2(resolutions)
         pareto_pruned = points.extend(pareto_pruning_functions(points)).prune_pareto_front(dirs) if len(pareto_pruning_functions.output_names) else points
         print('\tNum mutated design points: {} (pareto pruned to {})'.format(points.num_points, pareto_pruned.num_points))
         points = pareto_pruned

      # Store point cloud to a CSV file and return all design points
      designs = []
      derived_value_function = PointFunc(derived_values)
      if points.num_points:
         points_full_params = points.extend(derived_value_function(points, equs_as_float=False)) if len(derived_values) > 0 else points
         if save_design_output:
            points_full_params.save('Designs-{}.csv'.format(str(self.id)))
            # points_full_params.plot2d("mass_kg", "total_duration_days")
            # points_full_params.plot2d("mass_kg", "departure_average_speed")
            # points_full_params.plot2d("mass_kg", "energy_high_voltage_usage")
            # points_full_params.plot2d("mass_kg", "departure_min_pitch_angle")
            # points_full_params.plot2d("energy_high_voltage_usage", "departure_average_speed")
            # points_full_params.plot2d("energy_high_voltage_usage", "departure_min_pitch_angle")
            # points_full_params.plot2d("mass_kg", "num_towed_sensors")
            # points_full_params.plot2d("total_duration_days", "num_towed_sensors")
            # points_full_params.plot2d("energy_high_voltage_usage", "num_towed_sensors")
         data = points_full_params.float_data.detach().float().cpu().numpy()
      else:
         data = []
      for datum in data:
         designs.append({ param: datum[i] for i, param in enumerate(points_full_params.float_vars) })
      return designs

   def generate_assembly(self, known_params: Dict[str, float]) -> Assembly:
      return self.assembly.make_concrete(known_params)

   def set_mission_stage(self, stage: MissionStage) -> None:
      for part in self.required_parts.parts_list:
         part.set_mission_stage(stage)

   def set_state(self, state_names: Union[List[str], None]) -> None:
      for part in self.required_parts.parts_list:
         part.sympart.set_state(state_names)



   def mass(self, for_mission_stage: MissionStage) -> Union[float, Expr]:
      mass = 0.0
      for part in self.required_parts.parts_list:
         if for_mission_stage.name in part.present_stages:
            mass += part.mass
      return mass

   def displaced_volume(self, for_mission_stage: MissionStage) -> Union[float, Expr]:
      volume = 0.0
      for part in self.required_parts.parts_list:
         if for_mission_stage.name in part.present_stages:
            volume += part.displaced_volume
      return volume

   def center_of_gravity(self, for_mission_stage: MissionStage, concrete_values: Optional[Dict] = None) -> Union[float, Expr]:
      assembly = self.assembly.make_concrete(concrete_values)
      valid_parts = { part.sympart.name: part for part in self.required_parts.parts_list if for_mission_stage.name in part.present_stages }
      mass, center_of_gravity_x, center_of_gravity_y, center_of_gravity_z = (0.0, 0.0, 0.0, 0.0)
      for part in assembly.parts:
         if part.name in valid_parts:
            part_mass = valid_parts[part.name].mass.evalf(subs=concrete_values) if concrete_values and not isinstance(valid_parts[part.name].mass, float) and not isinstance(valid_parts[part.name].mass, int) else valid_parts[part.name].mass
            part_placement = part.static_placement
            part_center_of_gravity = part.oriented_center_of_gravity
            center_of_gravity_x += ((part_placement.x + part_center_of_gravity[0]) * part_mass)
            center_of_gravity_y += ((part_placement.y + part_center_of_gravity[1]) * part_mass)
            center_of_gravity_z += ((part_placement.z + part_center_of_gravity[2]) * part_mass)
            mass += part_mass
      return Coordinate(assembly.name + '_center_of_gravity',
                        x=center_of_gravity_x / mass,
                        y=center_of_gravity_y / mass,
                        z=center_of_gravity_z / mass)

   def center_of_buoyancy(self, for_mission_stage: MissionStage, concrete_values: Optional[Dict] = None) -> Union[float, Expr]:
      assembly = self.assembly.make_concrete(concrete_values)
      valid_parts = { part.sympart.name: part for part in self.required_parts.parts_list if for_mission_stage.name in part.present_stages }
      displaced_volume, center_of_buoyancy_x, center_of_buoyancy_y, center_of_buoyancy_z = (0.0, 0.0, 0.0, 0.0)
      for part in assembly.parts:
         if part.is_exposed and part.name in valid_parts:
            part_placement = part.static_placement
            part_displaced_volume = valid_parts[part.name].displaced_volume.evalf(subs=concrete_values) if concrete_values and not isinstance(valid_parts[part.name].displaced_volume, float) and not isinstance(valid_parts[part.name].displaced_volume, int) else valid_parts[part.name].displaced_volume
            part_center_of_buoyancy = part.oriented_center_of_buoyancy
            center_of_buoyancy_x += ((part_placement.x + part_center_of_buoyancy[0])
                                    * part_displaced_volume)
            center_of_buoyancy_y += ((part_placement.y + part_center_of_buoyancy[1])
                                    * part_displaced_volume)
            center_of_buoyancy_z += ((part_placement.z + part_center_of_buoyancy[2])
                                    * part_displaced_volume)
            displaced_volume += part_displaced_volume
      return Coordinate(assembly.name + '_center_of_buoyancy',
                        x=center_of_buoyancy_x / displaced_volume,
                        y=center_of_buoyancy_y / displaced_volume,
                        z=center_of_buoyancy_z / displaced_volume)

   def power_consumption(self, for_mission_stage: MissionStage, min_voltage: float, max_voltage: float) -> Union[float, Expr]:
      power = 0.0
      for part in self.required_parts.parts_list:
         if for_mission_stage.name in part.present_stages and part.required_voltage and \
               part.required_voltage <= max_voltage and min_voltage <= part.required_voltage:
            power += part.power_consumption
      return power
