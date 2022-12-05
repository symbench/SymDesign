
# Define our mass metric class 
import pandas as pd

class Plugin:
    # Scoring - smaller is better.  Using an S curve to allow open ended ranges, but tailored to put the slope in the expected range.
    def process(self, uuvDesign):
        score = 0
        comment="Smaller is better"
        try: 
            mass = uuvDesign['uuv']['mass']

            # S-curve - stretched way out
            score =((10)/(1 + 0.95 ** (-0.03 * (mass-2000))))
        except Exception as e:
            # print(f"Error computing metric.")
            comment = "Error computing metric.  " + str(e)
        finally:
            # print(f"Score is {score}")
            noop = 0
            
        retval = { "score" : score, "comment" : comment, "value" :  mass }
        return retval
