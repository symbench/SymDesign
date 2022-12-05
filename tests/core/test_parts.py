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

from symdesign.core.Activation import ActivationProfile, ActivationInterval
from symdesign.core.Parts import Parts, PartType, PartSubType, PartListing, PartsLibrary, PowerProfile
from symdesign.core.Mission import Mission, MissionStage, MissionTarget
from symdesign.core.BasePart import BasePart
from symcad.parts.fixed.TeledyneBenthosATM926AcousticModem import TeledyneBenthosATM926AcousticModem
from symcad.parts.generic import Sphere
from symcad.core import Coordinate

if __name__ == '__main__':

   # Create a test mission
   print('\nCreating a test mission with 1 stage...')
   mission = Mission()
   mission_stage = MissionStage('test_stage', [MissionTarget.EXACT_DISTANCE])
   mission_stage.maximum_depth = 4000.0
   mission_stage.maximum_roll_angle = 0.0
   mission_stage.maximum_pitch_angle = 45.0
   mission_stage.minimum_salinity = mission_stage.maximum_salinity = 34.0
   mission_stage.minimum_temperature = -2.0
   mission_stage.maximum_temperature = 2.0
   mission_stage.target_distance = 2000.0
   mission.add_stage(mission_stage)
   mission.maximum_average_horizontal_speed = 2.0
   mission.maximum_duration = 60 * 24 * 60 * 60
   mission.finalize()

   # Test creating a couple of PartListings
   listing1 = PartListing('Buoyancy Engine', PartType.DYNAMIC_BUOYANCY, PartSubType.PASSIVE, Sphere, None, [], {})
   listing2 = PartListing('Teledyne Benthos ATM 926 Modem', PartType.COMMUNICATIONS, PartSubType.ACOUSTIC, TeledyneBenthosATM926AcousticModem, PowerProfile((12.0, 36.0), (0.045833, 0.015278)), [Coordinate('AttachmentPoint', x=0.5, y=0.5, z=0.5)], {})
   print('\nPart Listings:')
   print('  ', listing1)
   print('  ', listing2)

   # Test creating concrete parts from the PartListings
   print('\nCreating parts...')
   buoyancy_engine: BasePart = listing1.create_part('buoyancy_engine', mission)
   acoustic_modem: BasePart = listing2.create_part('acoustic_modem', mission)
   print('\nCreated Parts:')
   print('  ', buoyancy_engine)
   print('  ', acoustic_modem)

   # Assign an activation profile to the Acoustic Modem
   modem_activation_profile = ActivationProfile('acoustic_modem_activations').add_mission_stage_profile_concrete(mission_stage, 12, ActivationInterval.PER_HOUR, 30)
   acoustic_modem.set_activation_profile(modem_activation_profile)

   # Test retrieving properties for the Buoyancy Engine
   print('\nBuoyancy Engine Properties:')
   print('   Mass:', buoyancy_engine.mass)
   print('   Material Volume:', buoyancy_engine.material_volume)
   print('   Displaced Volume:', buoyancy_engine.displaced_volume)
   print('   Surface Area:', buoyancy_engine.surface_area)
   print('   Center of Gravity:', buoyancy_engine.center_of_gravity)
   print('   Center of Buoyance:', buoyancy_engine.center_of_buoyancy)
   print('   Required Voltage:', buoyancy_engine.required_voltage)
   print('   Power Consumption:', buoyancy_engine.power_consumption)

   # Test retrieving properties for the Acoustic Modem
   print('\nAcoustic Modem Properties:')
   print('   Mass:', acoustic_modem.mass)
   print('   Material Volume:', acoustic_modem.material_volume)
   print('   Displaced Volume:', acoustic_modem.displaced_volume)
   print('   Surface Area:', acoustic_modem.surface_area)
   print('   Center of Gravity:', acoustic_modem.center_of_gravity)
   print('   Center of Buoyance:', acoustic_modem.center_of_buoyancy)
   print('   Required Voltage:', acoustic_modem.required_voltage)
   print('   Power Consumption:', acoustic_modem.power_consumption)
