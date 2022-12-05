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

from flask_restful import Resource, reqparse

class New(Resource):

   def __init__(self) -> None:
      super().__init__()

   def get(self):
      return {'data': None}, 200

   def post(self):

      # Parse POST args
      parser = reqparse.RequestParser()
      parser.add_argument('designName', required=True)
      args = parser.parse_args()

      # Do something with args
      print(args['designName'])
      return {'data': None}, 200

   def put(self):

      # Parse PUT args
      parser = reqparse.RequestParser()
      parser.add_argument('designName', required=True)
      args = parser.parse_args()

      # Do something with args
      print(args['designName'])
      return {'data': None}, 200
