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
from symcad.core import Coordinate
from typing import Any, Dict, List, Union
from ..parts import PartType, PartSubType, Listings
from ..parts.PartListing import PartListing
from .Power import PowerProfile
from .BasePart import BasePart
from .Mission import Mission
from .Performance import Metrics


class PartsLibrary(object):

   library: Dict[PartType, Dict[PartSubType, List[PartListing]]]
   """TODO:"""

   simple_library: List[PartListing]
   """TODO:"""


   # Constructor ----------------------------------------------------------------------------------

   def __init__(self) -> None:
      super().__init__()
      self.library = {}
      self.simple_library = []
      for part_type in PartType:
         self.library[part_type] = { subtype: [] for subtype in PartSubType }
      def add_to_library(listings: List[PartListing]) -> None:
         for listing in listings:
            self.simple_library.append(listing)
            for part_type in PartType:
               if part_type in listing.part_type:
                  for subtype in PartSubType:
                     if subtype in listing.part_subtype:
                        self.library[part_type][subtype].append(listing)
      add_to_library(Listings.get_fixed_part_listings())
      add_to_library(Listings.get_dynamic_part_listings())


   # Build-in methods -----------------------------------------------------------------------------

   def __repr__(self) -> str:
      output = ''
      for part_type, part_types in self.library.items():
         part_type_printed = False
         for subtype, subtypes in part_types.items():
            part_subtype_printed = False
            for part in subtypes:
               if not part_type_printed:
                  part_type_printed = True
                  output += '   ' + part_type.name + ':\n'
               if not part_subtype_printed:
                  part_subtype_printed = True
                  output += '      ' + subtype.name + ':\n'
               output += '         ' + part.name + '\n'
      return output


   # Public methods -------------------------------------------------------------------------------

   def add_new_part(self, part_name: str, part_type: PartType, part_subtype: PartSubType, symcad_model: str, power_profile: Union[PowerProfile, None], attachment_points: List[Coordinate], extra_parameters: Dict[str, Any]) -> None:
      listing = PartListing(part_name, part_type, part_subtype, symcad_model, power_profile, attachment_points, extra_parameters)
      self.library[part_type][part_subtype].append(listing)
      self.simple_library.append(listing)

   def create_part(self, part_description: Union[PartListing, str], identifier: str, mission: Mission, **kwargs) -> BasePart:
      if isinstance(part_description, PartListing):
         part_listing = part_description
      else:
         part_listing = None
         for part in self.simple_library:
            if part.name == part_description:
               part_listing = part
         if part_listing is None:
            raise RuntimeError('The specified part ("{}") does not exist '
                              'in the library'.format(part_description))
      return part_listing.create_part(identifier, mission, **kwargs)

   def get_part_suggestions(self, part_type: PartType, part_subtype: PartSubType, mission: Mission, metrics: Metrics) -> List[PartListing]:
      # TODO: Something intelligent here, actually change this to just take a list of required types/subtypes and come up with a comprehensive list of multiple parts that work together
      part_suggestions = set()
      for part in self.simple_library:
         if part_type in part.part_type and part_subtype in part.part_subtype:
            part_suggestions.add(part)
      result = list(part_suggestions)
      result.sort(key=lambda part: part.name)
      return result


class Parts(object):

   parts_list: List[BasePart]

   def __init__(self) -> None:
      super().__init__()
      self.parts_list = []

   def clear(self) -> None:
      self.parts_list.clear()

   def add_part(self, part: BasePart) -> Parts:
      self.parts_list.append(part)
      return self

   def get_by_type(self, part_type: PartType, part_subtype: PartSubType) -> List[BasePart]:
      return [part for part in self.parts_list if part_type in part.types and part_subtype in part.subtypes]
