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

from flask import Flask
from flask_restful import Api
from . import endpoints

if __name__ == '__main__':

   # Create the server application and API
   app = Flask(__name__)
   api = Api(app)

   # Add REST endpoints to the API
   api.add_resource(endpoints.New, '/new')
   api.add_resource(endpoints.Get, '/get')

   # Run the server application
   app.run(debug=True)
