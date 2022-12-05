#core.py
import importlib
import json

class Oracle:
    # We are going to receive a list of plugins as parameter
    def __init__(self, plugins:list=[]):
        # Checking if plugin were sent
        if plugins != []:
            # create a list of plugins
            self._plugins = [
                importlib.import_module(plugin,".").Plugin() for plugin in plugins
            ]
        else:
            # If no plugin were set we use our default
            self._plugins = [importlib.import_module('default',".").Plugin()]


    def run(self, uuvDesign, metricPlugins):
        totalScore = 0
        perfectScore = 0
        metricReports = []
        for i in metricPlugins['metrics']:
            #print(i['pythonFile'])
            plugin = importlib.import_module(i['pythonFile'],".").Plugin()
            hasTgt = True
            try:
                tgtVal = i['targetValue']
            except Exception as e:
                hasTgt = False

            if (hasTgt == True) :
                metric = plugin.process(uuvDesign, tgtVal)
            else:
                metric = plugin.process(uuvDesign)
                
            weight = i['weight']
            weightedScore = metric['score'] * weight
            maxScore = 10 * weight
            metricReport = {
                "name" : i['name'],
                "description" : i['description'],
                "score" : metric['score'],
                "weightedScore" : weightedScore,
                "maxScore" : maxScore,
                "comment" : metric['comment'],
                "value" : metric['value']
            }
            metricReports.append(metricReport)
            totalScore = totalScore + weightedScore
            perfectScore = perfectScore + maxScore
            

        fullReport = {
            "totalScore" : totalScore,
            "perfectScore" : perfectScore,
            "details" : metricReports
        } 

        json_object = json.dumps(fullReport, indent = 4) 
        print(json_object)

        print()

        
