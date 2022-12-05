
# Define our forwardPitch class
import numpy as np

class Plugin:
    # Define static method, so no self parameter
    def process(self, uuvDesign):
        "Pitch up and down should be 30 degrees.  Using S-curve to grade."
        score = 0
        density = 0
        comment = ""
        try: 
            zcb = uuvDesign['uuv']['zeroPitch']['centerBuoyancy']
            zcg = uuvDesign['uuv']['zeroPitch']['centerGravity']
            cbz = zcb['z']
            cgz = zcg['z']

            cb = np.array([zcb['x'], zcb['y'], zcb['z']])
            cg = np.array([zcg['x'],  zcg['y'], zcg['z']])
            zeroVector = cb - cg
            
            #print(f"Zero CB/CG line {zeroVector}.")
            vec1 = zeroVector

            
            upcb = uuvDesign['uuv']['upPitch']['centerBuoyancy']
            upcg = uuvDesign['uuv']['upPitch']['centerGravity']

            cb = np.array([upcb['x'], upcb['y'], upcb['z']])
            cg = np.array([upcg['x'], upcg['y'], upcg['z']])
            upVector = cb - cg
            #print(f"Pitch up CB/CG line {upVector}.")
            vec2 = upVector

            downcb = uuvDesign['uuv']['downPitch']['centerBuoyancy']
            downcg = uuvDesign['uuv']['downPitch']['centerGravity']

            cb = np.array([downcb['x'], downcb['y'], downcb['z']])
            cg = np.array([downcg['x'], downcg['y'], downcg['z']])
            downVector = cb - cg
            #print(f"Pitch down CB/CG line {downVector}.")
            vec3 = downVector

            
            angle=np.arccos(np.dot(vec1,vec2)/(np.linalg.norm(vec1)*np.linalg.norm(vec2)))
            udeg = np.degrees(angle)
            #print(f"Angle between zero and up vectors is {udeg}.")
            
            
            angle=np.arccos(np.dot(vec1,vec3)/(np.linalg.norm(vec1)*np.linalg.norm(vec3)))
            ddeg = np.degrees(angle)
            #print(f"Angle between zero and down vectors is {ddeg}.")

            # S-curve
            # f: y=((10)/(1+0.75^(0.7 (x-15))))
            upScore =   ((5)/(1+0.75 ** (0.7 * (udeg-15))))
            downScore = ((5)/(1+0.75 ** (0.7 * (ddeg-15))))
            score = upScore + downScore
            comment = "Pitch up at " + str(udeg) + " degrees.  Pitch down at " + str(ddeg) + " degrees."
            
        except BaseException as err:
            #print(f"Error computing metric.")
            comment = "Error computing metric. {0}".format(err)
        finally:
            noop = 0
            #print(f"Score is {score}")

        retval = { "score" : score, "comment" : comment, "value" :  { "up" : udeg, "down" : ddeg }  }
        return retval
