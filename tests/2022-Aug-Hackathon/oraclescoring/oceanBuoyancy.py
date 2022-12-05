
# Define our oceanBuoyancy class 
class Plugin:
    # Define static method, so no self parameter
    # partial score from 828 to 1028, score 10 if between 1028 and 1048, partial score to 1248, 0 otherwise
    def process(self, uuvDesign):
        score = 0
        density = 0
        comment = ""
        try: 
            # Some prints to identify which plugin is been used
            mass = uuvDesign['uuv']['mass']
            displacement = uuvDesign['uuv']['displacement']
            # print(f"Numbers are {mass} and {displacement}")
            density = mass / displacement
            if (density > 1248 or density < 828) :
                score = 0
            elif (density > 1048) :
                score = -1 * (density / 20) + 62.4
            elif (density < 1028) :
                score = (density / 20) - 41.4
            else:
                score = 10
        except:
            # print(f"Error computing metric.")
            comment = "Error computing metric."
        finally:
            # print(f"Density is {density}. Score is {score}")
            noop = 0
            
        retval = { "score" : score, "comment" : comment, "value" : density }
        return retval
