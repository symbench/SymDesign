
# Define our deploymentAccuracy class 
import pandas as pd

class Plugin:
    # Define static method, so no self parameter
    # Target requirement - deploy within 50km of target lat/lon.
    # Scoring - 10 for inside 5km, down to 0 outside 50.
    def process(self, uuvDesign):
        comment = ""
        score = 0
        rangeToTarget = float('inf')
        try: 
            simOutputFile = uuvDesign['uuv']['phase1Demo']['outputCsvFile']
            uuv_df = pd.read_csv(simOutputFile)
            get_column_value = lambda key: uuv_df[key][0]
            deployedLat = get_column_value("true_drop_lat")
            deployedLon = get_column_value("true_drop_lon")
            rangeToTarget = get_column_value("true_drop_range_m")

            #print(f"Range to target {rangeToTarget}")
            if (rangeToTarget < 5000) :
                score = 10
            elif (rangeToTarget > 50000) :
                score = 0
            else:
                # y=-1/4500x+100/9
                score = ((-1/4500) * rangeToTarget) + (100/9)
        except Exception as e:
            # print(f"Error computing metric.")
            comment = "Error computing metric.  " + str(e)
        finally:
            # print(f"Score is {score}")
            noop = 0
            
        retval = { "score" : score, "comment" : comment, "value" : rangeToTarget }
        return retval
