
import pandas as pd

class Plugin:
    # Define static method, so no self parameter
    def process(self, uuvDesign, targetValue):
        comment = "All PV depth ratings must meet target value of {targetValue}"
        try: 
            score = 10
            pvs = uuvDesign['uuv']['pressureVessels']
            num = len(pvs)
            minRating = float('inf')
            # print(f"{num} pressure vessels.")
            for pv in pvs:
                depth = pv['depth']
                name = pv['name']
                if (depth < minRating):
                    minRating = depth
                if (depth < targetValue):
                    score = 0
                    comment = comment + " PV " + name + " depth rating is too low."
                    
        except Exception as e:
            # print(f"Error computing metric.")
            comment = "Error computing metric.  " + str(e)
        finally:
            # print(f"Score is {score}")
            noop = 0
            
        retval = { "score" : score, "comment" : comment, "value" : minRating }
        return retval
