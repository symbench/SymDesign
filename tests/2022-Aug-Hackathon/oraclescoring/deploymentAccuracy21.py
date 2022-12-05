
# Define our deploymentAccuracy class 
import pandas as pd

class Plugin:
    # Define static method, so no self parameter
    # Target requirement - deploy within 300m of target lat/lon.
    # Scoring - 10 for inside 100m, down to 0 outside 300.
    def process(self, uuvDesign):
        comment = "Deployment failed."
        score = 0
        rangeToTarget = float('inf')
        try: 
            simOutputFile = uuvDesign['uuv']['mission2.1']['outputCsvFile']
            uuv_df = pd.read_csv(simOutputFile)
            get_column_value = lambda key: uuv_df[key][0]
            completed = get_column_value("missionComplete")

            if (completed == True) : 
                rangeToTarget = get_column_value("deploymentAccuracy (km)")
                rangeToTarget = rangeToTarget * 1000  # km to m

                #print(f"Range to target {rangeToTarget}")
                comment = "Range to target deployment (m) is " + str(rangeToTarget)
                if (rangeToTarget < 100) :
                    score = 10
                elif (rangeToTarget > 300) :
                    score = 0
                else:
                    # Linear slope from 100 to 301
                    # y=(-10/201)x + 3010/201
                    score = ((-10/201) * rangeToTarget) + (3010/201)
                    
        except Exception as e:
            # print(f"Error computing metric.")
            comment = "Error computing metric.  " + str(e)
        finally:
            # print(f"Score is {score}")
            noop = 0
            
        retval = { "score" : score, "comment" : comment, "value" : rangeToTarget }
        return retval
