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

from symcad.core import Assembly
from symcad.parts.fairing import CylinderWithConicalEnds
from symcad.parts.fixed import TeledyneTasman600kHzDvl, TeledyneBenthosATM926AcousticModem, TecnadyneModel2061Thruster, iXbluePhinsCompactC7Ins
from symcad.parts.fixed import TridentSensorsDualGpsIridiumAntenna, NortekDVL1000_4000mDvl, OceanBottomSeismometer, Garmin15HGpsReceiver
from symcad.parts.fixed import IridiumCore9523Radio, RaspberryPiZero2Computer, CatPumps3CP1221Pump
from symcad.parts.generic import Cone, Cylinder, EllipsoidalCap, Fin
from symcad.parts.composite import SemiellipsoidalCapsule, CrossFormAirfoils
from symdesign.parts.internal.MassBasedBuoyancyEngine import MassBasedBuoyancyEngine
import math

if __name__ == '__main__':

   # Create test parts and components
   downward_dvl = TeledyneTasman600kHzDvl('downward_dvl_sensor')\
                  .add_attachment_point('attachment_front', x=0, y=0.5, z=(161.4/174.0))\
                  .add_attachment_point('attachment_center', x=0.5, y=0.5, z=(161.4/174.0))
   upward_dvl = NortekDVL1000_4000mDvl('upward_dvl_sensor')\
                  .add_attachment_point('attachment_front', x=1, y=0.5, z=(52.78/164.0))\
                  .add_attachment_point('attachment_center', x=0.5, y=0.5, z=(52.78/164.0))\
                  .add_attachment_point('antenna_attachment', x=-0.5, y=0.5, z=(52.78/164.0))\
                  .set_orientation(roll_deg=0, pitch_deg=180, yaw_deg=0)
   ins = iXbluePhinsCompactC7Ins('ins')\
         .add_attachment_point('attachment_pv', x=0.5, y=0.5, z=-0.1)\
         .set_orientation(roll_deg=0, pitch_deg=90, yaw_deg=0)
   acoustic_modem = TeledyneBenthosATM926AcousticModem('acoustic_modem')\
                    .add_attachment_point('attachment_center', x=0.5, y=0.5, z=0.5)\
                    .set_orientation(roll_deg=0, pitch_deg=180, yaw_deg=0)
   sat_antenna = TridentSensorsDualGpsIridiumAntenna('sat_antenna')\
                 .add_attachment_point('attachment_point', x=0, y=0.5, z=(19.0/169.0))
   thruster = TecnadyneModel2061Thruster('thruster')\
              .add_attachment_point('attachment_center', x=(280.0/342.0), y=0.5, z=0.5)\
              .set_orientation(roll_deg=0, pitch_deg=180, yaw_deg=0)
   rudders = CrossFormAirfoils('rudders')\
             .add_attachment_point('attachment_front', x=0, y=0.5, z=0.5)\
             .set_orientation(roll_deg=45, pitch_deg=0, yaw_deg=0)
   stability_fin = Fin('fin')\
                   .add_attachment_point('attachment_rear', x=1, y=0.5, z=0)
   obs_sensor = OceanBottomSeismometer('obs_sensor')\
                .add_attachment_point('attachment_front', x=0.5, y=0.5, z=0)\
                .add_attachment_point('attachment_back', x=0.5, y=0.5, z=1)\
                .add_attachment_point('back_bottom_middle', x=1, y=0.5, z=0.85)\
                .add_attachment_point('back_top_middle', x=0, y=0.5, z=0.85)\
                .set_orientation(roll_deg=0, pitch_deg=90, yaw_deg=0)
   syntactic_foam_cone = Cone('syntactic_foam_cone')\
                         .add_attachment_point('attachment_front', x=0.5, y=0.5, z=1)\
                         .add_attachment_point('attachment_back', x=0.5, y=0.5, z=0)\
                         .set_orientation(roll_deg=0, pitch_deg=-90, yaw_deg=0)
   syntactic_foam_cylinder = Cylinder('syntactic_foam_cylinder')\
                             .add_attachment_point('attachment_front', x=0.5, y=0.5, z=1)\
                             .add_attachment_point('attachment_back', x=0.5, y=0.5, z=0)\
                             .add_attachment_point('attachment_back_top', x=1, y=0.5, z=0)\
                             .add_attachment_point('attachment_back_bottom', x=0, y=0.5, z=0)\
                             .set_orientation(roll_deg=0, pitch_deg=-90, yaw_deg=0)
   syntactic_foam_hemicylinder = EllipsoidalCap('syntactic_foam_hemicylinder')\
                                 .add_attachment_point('attachment_front', x=0, y=0.5, z=0)\
                                 .add_attachment_point('attachment_back', x=1, y=0.5, z=0)\
                                 .add_attachment_point('attachment_top', x=0.5, y=0.5, z=1)\
                                 .add_attachment_point('attachment_bottom', x=0.5, y=0.5, z=0)\
                                 .set_orientation(roll_deg=0, pitch_deg=-90, yaw_deg=0)
   pv_low_voltage = SemiellipsoidalCapsule('pv_low_voltage')
   pv_low_voltage.add_attachment_point('bottom_front', x=0.3, y=0.5, z=0)\
                 .add_attachment_point('top_middle', x=0.5, y=0.5, z=1)\
                 .add_attachment_point('bottom_rear', x=1, y=0.5, z=0)\
                 .add_attachment_point('front_center', x=0, y=0.5, z=0.5)\
                 .add_attachment_point('front_center_external', x=0, y=0.5, z=0.5)\
                 .add_attachment_point('electronics', x=0.15, y=0.5, z=0.75)
   pv_high_voltage = SemiellipsoidalCapsule('pv_high_voltage')\
                    .add_attachment_point('bottom_rear', x=1, y=0.5, z=0)
   battery_pack_lw = Cylinder('battery_pack_low_voltage')\
                     .add_attachment_point('bottom_front', x=1, y=0.5, z=0)\
                     .set_orientation(roll_deg=0, pitch_deg=90, yaw_deg=0)
   gps_receiver = Garmin15HGpsReceiver('gps_receiver')\
                  .add_attachment_point('pv_attachment_point', x=0, y=0.5, z=0.5)\
                  .add_attachment_point('sensor1_attachment_point', x=0, y=1, z=0.5)\
                  .add_attachment_point('sensor2_attachment_point', x=0, y=0, z=0.5)\
                  .set_orientation(roll_deg=90, pitch_deg=90, yaw_deg=0)
   iridium_modem = IridiumCore9523Radio('iridium_modem')\
                   .add_attachment_point('sensor_attachment_point', x=0, y=0, z=0.5)\
                   .set_orientation(roll_deg=90, pitch_deg=90, yaw_deg=0)
   nav_computer = RaspberryPiZero2Computer('nav_computer')\
                  .add_attachment_point('sensor_attachment_point', x=0, y=1, z=0.5)\
                  .set_orientation(roll_deg=90, pitch_deg=90, yaw_deg=0)
   buoyancy_engine = MassBasedBuoyancyEngine('buoyancy_engine', pump_cad_model=CatPumps3CP1221Pump('pump'), motor_cad_model=CatPumps3CP1221Pump('motor'))\
                     .add_attachment_point('bottom_center', x=0.5, y=0.5, z=0)\
                     .add_attachment_point('bottom_back', x=0, y=0.5, z=0)\
                     .set_orientation(roll_deg=0, pitch_deg=0, yaw_deg=180)

   # Create test fairing and attachment points
   fairing = CylinderWithConicalEnds('fairing', 1000.0)
   fairing.add_attachment_point('nose_tip', x=0, y=0.5, z=0.5)
   fairing.add_attachment_point('body_bottom_front', x=fairing.geometry.nose_length/fairing.unoriented_length, y=0.5, z=0.02)
   fairing.add_attachment_point('body_top_front', x=fairing.geometry.nose_length/fairing.unoriented_length, y=0.5, z=1)
   fairing.add_attachment_point('body_bottom_quarter', x=(fairing.geometry.nose_length/fairing.unoriented_length)+(0.25*fairing.geometry.body_length/fairing.unoriented_length), y=0.5, z=0.02)
   fairing.add_attachment_point('body_top_quarter', x=(fairing.geometry.nose_length/fairing.unoriented_length)+(0.25*fairing.geometry.body_length/fairing.unoriented_length), y=0.5, z=1)
   fairing.add_attachment_point('body_bottom_middle', x=(fairing.geometry.nose_length/fairing.unoriented_length)+(0.5*fairing.geometry.body_length/fairing.unoriented_length), y=0.5, z=0.02)
   fairing.add_attachment_point('body_top_middle', x=(fairing.geometry.nose_length/fairing.unoriented_length)+(0.5*fairing.geometry.body_length/fairing.unoriented_length), y=0.5, z=1)
   fairing.add_attachment_point('body_bottom_back', x=1.0-(fairing.geometry.tail_length/fairing.unoriented_length), y=0.5, z=0.02)
   fairing.add_attachment_point('body_top_back', x=1.0-(fairing.geometry.tail_length/fairing.unoriented_length), y=0.5, z=1)
   fairing.add_attachment_point('tail_connection', x=1.0-(fairing.geometry.tail_length/fairing.unoriented_length), y=0.5, z=0.5)
   fairing.add_attachment_point('tail_quarter', x=1.0-(0.75*fairing.geometry.tail_length/fairing.unoriented_length), y=0.5, z=0.5)
   fairing.add_attachment_point('tail_tip', x=1, y=0.5, z=0.5)

   # Create test assembly
   assembly = Assembly('assembly')
   obs_sensor.attach('attachment_back', syntactic_foam_cylinder, 'attachment_front')
   pv_low_voltage.attach('electronics', gps_receiver, 'pv_attachment_point')
   pv_low_voltage.attach('front_center', ins, 'attachment_pv')
   pv_low_voltage.attach('bottom_front', buoyancy_engine, 'bottom_center')
   pv_low_voltage.attach('front_center_external', syntactic_foam_cylinder, 'attachment_back')
   buoyancy_engine.attach('bottom_back', battery_pack_lw, 'bottom_front')
   upward_dvl.attach('antenna_attachment', sat_antenna, 'attachment_point')
   gps_receiver.attach('sensor1_attachment_point', iridium_modem, 'sensor_attachment_point')
   gps_receiver.attach('sensor2_attachment_point', nav_computer,'sensor_attachment_point' )
   downward_dvl.attach('attachment_front', syntactic_foam_cylinder, 'attachment_back_bottom')
   upward_dvl.attach('attachment_front', syntactic_foam_cylinder, 'attachment_back_top')
   fairing.attach('nose_tip', acoustic_modem, 'attachment_center')
   fairing.attach('tail_tip', thruster, 'attachment_center')
   fairing.attach('tail_quarter', rudders, 'attachment_front')
   fairing.attach('body_top_back', stability_fin, 'attachment_rear')
   fairing.attach('body_bottom_front', obs_sensor, 'back_bottom_middle')
   fairing.attach('body_top_front', obs_sensor, 'back_top_middle')
   fairing.attach('body_bottom_back', pv_high_voltage, 'bottom_rear')
   assembly.add_part(downward_dvl)
   assembly.add_part(upward_dvl)
   assembly.add_part(ins)
   assembly.add_part(acoustic_modem)
   assembly.add_part(thruster)
   assembly.add_part(rudders)
   assembly.add_part(stability_fin)
   assembly.add_part(sat_antenna)
   assembly.add_part(obs_sensor)
   assembly.add_part(syntactic_foam_cylinder)
   assembly.add_part(pv_low_voltage)
   assembly.add_part(pv_high_voltage)
   assembly.add_part(gps_receiver)
   assembly.add_part(iridium_modem)
   assembly.add_part(nav_computer)
   assembly.add_part(buoyancy_engine)
   assembly.add_part(battery_pack_lw)
   assembly.add_part(fairing)

   # Specify the fairing dimensions
   fairing_thickness = 0.005
   fairing_nose_tip_radius = 0.1
   fairing_nose_length = (0.7 * acoustic_modem.unoriented_length) + obs_sensor.unoriented_height
   fairing_body_radius = (obs_sensor.unoriented_width / 2) + (2 * fairing_thickness)
   fairing_body_length = 3.0
   fairing_tail_tip_radius = 0.5 * thruster.unoriented_height
   fairing_tail_length = 0.5

   # Globally place the fairing and and export the assembly
   fairing.set_placement(placement=(0, 0, 0), local_origin=(0, 0.5, 0.5))
   concrete_assembly = assembly.make_concrete({
      'fairing_nose_tip_radius': fairing_nose_tip_radius,
      'fairing_nose_length': fairing_nose_length,
      'fairing_body_radius': fairing_body_radius,
      'fairing_body_length': fairing_body_length,
      'fairing_tail_tip_radius': fairing_tail_tip_radius,
      'fairing_tail_length': fairing_tail_length,
      'fairing_thickness': fairing_thickness,

      'rudders_span': 0.5 * fairing_body_radius,
      'rudders_curvature_tilt': 90.0 - math.degrees(math.atan2(fairing_tail_length, fairing_body_radius - fairing_tail_tip_radius)),
      'rudders_max_thickness': 0.1,
      'rudders_separation_radius': 0.75 * (fairing_body_radius + fairing_tail_tip_radius),
      'rudders_chord_length': 0.3,

      'fin_height': 0.7 * fairing_body_radius,
      'fin_lower_length': 0.3,
      'fin_upper_length': 0.1,
      'fin_thickness': 0.1,

      'syntactic_foam_cylinder_radius': 0.5 * obs_sensor.unoriented_width,
      'syntactic_foam_cylinder_height': 0.5 * obs_sensor.unoriented_height,

      'pv_low_voltage_cylinder_radius': (0.5 * obs_sensor.unoriented_width) - 0.015,
      'pv_low_voltage_cylinder_length': 0.6,
      'pv_low_voltage_cylinder_thickness': 0.01,
      'pv_low_voltage_endcap_thickness': 0.01,

      'pv_high_voltage_cylinder_radius': (0.5 * obs_sensor.unoriented_width) - 0.015,
      'pv_high_voltage_cylinder_length': 0.6,
      'pv_high_voltage_cylinder_thickness': 0.01,
      'pv_high_voltage_endcap_thickness': 0.01,

      'buoyancy_engine_reservoir_radius': (0.5 * obs_sensor.unoriented_width) - 0.015 - 0.02,
      'buoyancy_engine_reservoir_length': 0.2,

      'battery_pack_low_voltage_height': 0.3,
      'battery_pack_low_voltage_radius': (0.5 * obs_sensor.unoriented_width) - 0.015 - 0.02
   })
   #print(concrete_assembly.center_of_gravity())
   concrete_assembly.export('test.FCStd', 'freecad')
