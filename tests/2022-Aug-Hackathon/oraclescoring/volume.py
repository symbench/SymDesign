
# Define our volume metric class 
import pandas as pd

class Plugin:
    # Define static method, so no self parameter
    # Scoring - smaller is better.  Using an S curve to allow open ended ranges, but tailored to put the slope in the expected range.
    def process(self, uuvDesign):
        score = 0
        comment="Smaller is better"
        try: 
            volume = uuvDesign['uuv']['volume']

            # S-curve - stretched way out
            # Adjust by entering the formula into https://www.geogebra.org/graphing?lang=en and tuning the parameters
            score = ((10)/(1 + 0.255 ** (-0.7 * (volume-4))))
        except Exception as e:
            # print(f"Error computing metric.")
            comment = "Error computing metric.  " + str(e)
        finally:
            # print(f"Score is {score}")
            noop = 0
            
        retval = { "score" : score, "comment" : comment, "value" :  volume }
        return retval
