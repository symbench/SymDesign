

Usage:
python main.py <uuvdesign.json> metricsPlugins.json


This utility is a prototype grading system for scoring UUV designs.
Each key performance parameter (KPP) of a UUV design is evaluated by a
separate metric algorithm coded as a Python plugin.  This allows the
metrics to be dynamically created and loaded, with no dependencies
other than the UUV design itself.

The UUV design is expressed as a JSON file, with KPPs defined at the
system and subsystem levels.  The JSON file is parsed into a Python
dictionary, which is very easy to read, using the data['name'] idiom.

The metricsPlugins.json file defines the metric with a name and
description, the Python file that implements it, and the weight to be
applied to that metric in the overall score.

Each plugin takes an input the UUV design Python dictionary, and thus
has access to the whole design.  The plugin computes a score for the
metric from 0-10, 10 being the best.  The score and a comment, which
may help a human understand a low score or an error message, are
returned.  See default.py for a simple plugin implementation.  

Weighted scores are summed up for all metrics into an overall score.
In addition, an ideal score is also computed, so the score could be
normalized to a 0-100 scale.  The overall and detailed results are
printed to standard out in JSON format.

Note that many of the metrics are scored using an S-curve, using 10 as
an aymptotic bound on the score.  Thus a perfect score is not
possible.  S-curve scoring allows for continuous scoring for an
open-ended range of possible values and also is always increasing (or
decreasing, depending on the metric) to direct the AI via comparisons.
The S-curve results in bonus points being awarded for exceeding a
target metric, but with eventual diminishing returns beyond the range
of values expected by SMEs, thus preventing overfitting of one metric
over others.


Example files:

uuvdesign.json - nemo.json
metricsPlugins.json - metricsPlugins.json
results - output.json



uuvdesign.json

This section desribes the design features collected in the uuvdesign.json file.

UUV Features
"mass"  - the dry mass of UUV, fairing, and all components (kg)
"displacement" - the displacement of the UUV, in m^3.  For flooded UUVs, this will be less than the fairing volume.
"volume" :  - m^3, the total volume of the vehicle.
"hullFairing" - information about the fairing
  "boundingBox" : - the bounding box of the UUV, capturing the ranges on length (x), width (y) and height (z), in meters (m)
  "stlFile" :  - the STL file representing the UUV, for visualization and CFD analysis
"zeroPitch": - positions of center of buoyancy (CB) and center of gravity (CG) with pitch controls set to neutral/zero pitch.  CB and CG points are relative to the origin, in meteres (m), located at the nose of the UUV.
"downPitch" - CB/CG points with pitch controls set to max down pitch.
"upPitch" - CB/CG points with pitch controls set to max up pitch.

"phase1Demo" - simulation data regarding the phase 1B demo mission for OBS deployment
  "guidance" : - the Python file used to guide the UUV through the mission
  "outputCsvFile" :  - The mission results CSV file

"pressureVessels" : - the designs of all pressure vessels in the UUV
  PV Features
  "name": - the name of the PV
  "shape": - the shape, either SPHERE or CYLINDER
  "internalRadius": - meters. The internal radius of the PV
  "sphereThickness": - meters. the thickness of the PV housing for sphere and spherical end caps of cylinders
  "cylinderThickness": - meters. the thickness of the PV housing for cylinders.  Does not apply to SPHERE shapes.
  "length": - meters. length of a cylinder PV.  Does not apply to SPHERE shapes.
  "internalVolume": - Liters.  The internal volume of the PV.  For complex PVs, eg with ribs, this is required.  If not included, the internal volume is calculated with the other pV dimensions.  
  "mass": - kg. The dry mass of the empty PV itself.
  "material": - material of the PV.  
  "depth": - meters.  depth rating of the PV.


