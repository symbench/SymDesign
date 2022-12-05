
import pandas as pd

class Plugin:
    # Define static method, so no self parameter
    def process(self, uuvDesign):
        comment = ""
        score = 0
        completed = False
        success = "false"
        try: 
            simOutputFile = uuvDesign['uuv']['mission2.1']['outputCsvFile']
            uuv_df = pd.read_csv(simOutputFile)
            get_column_value = lambda key: uuv_df[key][0]
            completed = get_column_value("validPath")
            if (completed == True) : 
                success = "true"
                
            if (completed) :
                score = 10
                comment = "Mission was valid."
            else:
                score = 0
                comment = "Mission path was not valid."
        except Exception as e:
            # print(f"Error computing metric.")
            comment = "Error computing metric.  " + str(e)
        finally:
            noop = 0
            
        retval = { "score" : score, "comment" : comment, "value" : success }
        return retval
