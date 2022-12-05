#default.py
# Define our default class 
class Plugin:
    # Define static method, so no self parameter 
    def process(self, uuvDesign):
        "Each metric plugin must return a score between 0 and 10 and a comment that can be used to explain why the score was given, or to carry error messages."
        # Some prints to identify which plugin is been used
        print("This is my default plugin")
        
        retval = { "score" : 10, "comment" : "Default Metric" }
        return retval


        
