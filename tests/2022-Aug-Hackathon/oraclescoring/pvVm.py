
import pandas as pd
import math

class Plugin:
    # Total UUV pressure vessels usable internal volume to mass ratio
    # Larger is better, provided the PV meets depth requirements.  Depth is another metric.
    # Using an S curve to allow open ended ranges, but tailored to put the slope in the expected range.
    # Currently expects internalVolume and mass to be given.  May compute given other parameters later.
    def process(self, uuvDesign):
        score = 0
        comment="Bigger is better."
        try: 
            pvs = uuvDesign['uuv']['pressureVessels']
            num = len(pvs)
            # print(f"{num} pressure vessels.")
            iVolume = 0
            mass = 0
            for pv in pvs:
                shape = pv['shape']
                try:
                    iVolume = iVolume + pv['internalVolume']
                    #print(f"Pressure vessel volume {pv['internalVolume']}.")
                except Exception as e:
                    # compute instead from dimensions, assuming standard internal structure
                    if (shape == "SPHERE"):
                        r = pv['internalRadius']
                        vol = 1000 * (4 * math.pi * r**3)/3
                        iVolume = iVolume + vol
                        #print(f"Pressure vessel volume {vol}.")
                        
                    if (shape == "CYLINDER"):
                        r = pv['internalRadius']
                        length = pv['length']
                        cylVol =  1000 * math.pi * r**2 * length
                        sphereVol = 1000 * (4 * math.pi * r**3)/3 
                        iVolume = iVolume + sphereVol + cylVol
                        #print(f"Pressure vessel volume {sphereVol + cylVol}.")
                        
                mass = mass + pv['mass']

            ratio = iVolume / mass
            # S-curve - linear range from 1-5
            # f: y=((10)/(1+0.255^(0.7 (x-3))))
            score =((10)/(1 + 0.255 ** (0.7 * (ratio-3))))
            comment = "PVs:" + str(num) + " internalV/mass:" + str(ratio) + ".  Bigger is better."
        except Exception as e:
            # print(f"Error computing metric.")
            comment = "Error computing pvVm metric.  " + str(e)
        finally:
            # print(f"Score is {score}")
            noop = 0
            
        retval = { "score" : score, "comment" : comment, "value" : ratio }
        return retval
