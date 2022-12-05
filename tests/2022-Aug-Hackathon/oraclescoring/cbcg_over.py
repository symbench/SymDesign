
# Define our cbcg_over class 
class Plugin:
    # Define static method, so no self parameter
    def process(self, uuvDesign):
        "CB above CG - 10, 0 otherwise"
        score = 0
        density = 0
        comment = ""
        correctOrientation = False
        try: 
            # Some prints to identify which plugin is been used
            #print("This is my cbcg_over plugin")
            cb = uuvDesign['uuv']['zeroPitch']['centerBuoyancy']
            cg = uuvDesign['uuv']['zeroPitch']['centerGravity']
            cbz = cb['z']
            cgz = cg['z']
            correctOrientation = "true"
            if (cbz > cgz) :
                score = 10
                correctOrientation = "true"
            else:
                score = 0
                comment = "CB should be above CG or the thing will flip over."
                correctOrientation = "false"
        except BaseException as err:
            #print(f"Error computing metric.")
            comment = "Error computing metric. {0}".format(err)
        finally:
            noop = 0
            #print(f"Score is {score}")

        retval = { "score" : score, "comment" : comment, "value" : correctOrientation  }
        return retval
