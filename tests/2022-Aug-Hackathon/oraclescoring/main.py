#main.py
# This is a main file which will initialise and execute the run method of our application

# Importing our application file
import sys
import json
from core import Oracle

if __name__ == "__main__":
    # command line
    n = len(sys.argv)
    #print("Total arguments passed:", n)

    if (n != 3):
        print("Usage: python main.py <design.json> <plugins.json>")
        exit()

    #print("\nArguments passed:", end = " ")
    #for i in range(1, n):
    #    print(sys.argv[i], end = " ")
    #print("")

    # UUV design
    f = open(sys.argv[1])
    uuvDesign = json.load(f)
    f.close()
    
    # metrics plugins
    f = open(sys.argv[2])
  
    # returns JSON object as 
    # a dictionary
    plugInData = json.load(f)
    f.close()
    
    plugins = []
    for i in plugInData['metrics']:
        #print(i['pythonFile'])
        plugins.append(i['pythonFile'])
    
    # Initialising our application
    app = Oracle(plugins)

    # Running our application 
    app.run(uuvDesign, plugInData)

