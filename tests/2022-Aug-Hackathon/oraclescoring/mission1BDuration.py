
import pandas as pd

class Plugin:
    # Define static method, so no self parameter
    # Target of 60 days to complete mission.  Bonus points for faster completion.
    def process(self, uuvDesign):
        comment = ""
        score = 0
        missionDuration_d = float('inf')
        try: 
            simOutputFile = uuvDesign['uuv']['phase1Demo']['outputCsvFile']
            uuv_df = pd.read_csv(simOutputFile)
            get_column_value = lambda key: uuv_df[key][0]
            missionDuration_s = get_column_value("mission_end_time_s")
            secPerDay = 60*60*24
            missionDuration_d = missionDuration_s / secPerDay
            
            # S-curve - linear range from
            # y=((10)/(1+0.85^(-0.7 (x-57))))
            score =((10)/(1 + 0.85 ** (-0.7 * (missionDuration_d-57))))
            comment = "Mission duration of " + str(missionDuration_d) + " days."
        except Exception as e:
            # print(f"Error computing metric.")
            comment = "Error computing metric.  " + str(e)
        finally:
            noop = 0
            
        retval = { "score" : score, "comment" : comment, "value" : missionDuration_d }
        return retval
