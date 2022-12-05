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
from typing import Any, Dict

class Material(object):

   options: Dict[str, Dict[str, Any]]
   """List of available options."""

   selected_option: str
   """Name of the currently selected option."""


   def __init__(self) -> None:
      super().__init__()
      self.options = {}
      self.selected_option = None


   def add_option(self, name: str, parameters: Dict[str, Any]) -> None:
      self.options[name] = parameters


   def select(self, name: str) -> Material:
      if name not in self.options:
         raise RuntimeError('The specified name "{}" is not a valid material option'.format(name))
      self.selected_option = name
      return self


   def get_selection(self) -> Dict[str, Any]:
      if self.selected_option is None:
         raise RuntimeError('No concrete selection was made for the type of material')
      return self.options[self.selected_option]
