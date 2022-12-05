
import pandas as pd
import math

class Plugin:
    # Define static method, so no self parameter
    def process(self, uuvDesign):
        comment = ""
        score = 0
        missionDuration_d = float('inf')
        percentRemaining = -1.0
        try: 
            simOutputFile = uuvDesign['uuv']['mission2.1']['outputCsvFile']
            uuv_df = pd.read_csv(simOutputFile)
            get_column_value = lambda key: uuv_df[key][0]
            energyUsed = get_column_value("energyConsumed (kWhr)")
            energyRemaining = get_column_value("energyRemaining (kWhr)")
            energyCapacity = energyUsed + energyRemaining
            percentRemaining = 100 * (energyRemaining / energyCapacity)

            if (energyRemaining < 0):
                comment = "Vehicle energy ran out during the mission.  "
                score = 0
                percentRemaining = 0;
            else:
                # Bell-curve centered on 15 percent
                # https://www.geogebra.org/graphing
                # g(x)=((50)/(2 sqrt(2 pi))) e^(((-(x-20)^(2))/(2*2^(2))))
                score = ((50)/(2 * math.sqrt(2 * math.pi))) * (math.e ** (((-(percentRemaining-20)**(2))/(2*2 ** (2)))))
                comment = "energyUsed: " + str(energyUsed) + " energyRemaining " + str(energyRemaining) + " energyCapacity " + str(energyCapacity) + " Energy reserve is " + str(percentRemaining) + "%."
                
        except Exception as e:
            # print(f"Error computing metric.")
            comment = "Error computing metric.  " + str(e)
        finally:
            noop = 0
            
        retval = { "score" : score, "comment" : comment, "value" : percentRemaining }
        return retval
