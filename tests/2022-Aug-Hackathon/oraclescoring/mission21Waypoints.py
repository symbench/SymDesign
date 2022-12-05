
import pandas as pd

class Plugin:
    # Define static method, so no self parameter
    def process(self, uuvDesign, targetValue):
        comment = "All " + str(targetValue) + " waypoints should be crossed as part of the mission path."
        waypointsHit = 0
        score = 10
        try: 
            simOutputFile = uuvDesign['uuv']['mission2.1']['outputCsvFile']
            uuv_df = pd.read_csv(simOutputFile)
            get_column_value = lambda key: uuv_df[key][0]
            waypointsHit = get_column_value("numNavPointsTraversed")
            # print(f"waypointsHit {waypointsHit} targetValue {targetValue}")
            
            if (waypointsHit <= targetValue):
                score = 10 * waypointsHit / targetValue

        except Exception as e:
            # print(f"Error computing metric.")
            comment = "Error computing metric.  " + str(e)
            score = 0
        finally:
            # print(f"Score is {score}")
            noop = 0
            
        retval = { "score" : score, "comment" : comment, "value" : str(waypointsHit) }
        return retval
