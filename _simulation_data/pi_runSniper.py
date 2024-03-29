# Program To Launch approximation framework
import cv2
import subprocess
import ConfigParser
import os
import eval
import json
import urllib2
import sys
import random
from elasticsearch import Elasticsearch 

Config = ConfigParser.ConfigParser()
Config.read("config.ini")

es=Elasticsearch([{'host':'deep.ics.uci.edu','port':9200}])

def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

input = ConfigSectionMap("Source")['path']
frameName =os.path.splitext(os.path.basename(input))[0]
jump_to_frame = int(ConfigSectionMap("Source")['jump_to_frame'])
upload_to_elastic = (ConfigSectionMap("Source")['upload_to_elastic'] == 'true')
sigma = ConfigSectionMap("Canny")['sigma']
tl = ConfigSectionMap("Canny")['tl']
th = ConfigSectionMap("Canny")['th']
sniperPath = ConfigSectionMap("Sniper")['path']
appPath = ConfigSectionMap("Sniper")['app']
affected = ConfigSectionMap("FaultInjector")['affected']
read_ber = float(ConfigSectionMap("FaultInjector")['read_ber'])
write_ber = float(ConfigSectionMap("FaultInjector")['write_ber'])

isCalibrateFrame='false'
knob1=0
knob2=0
finalScore=0
target_ber=0
kp=0
ki=0
isManual=0
sampling=0

def launchCannyInSniper(inputImage, outputImage):
    # Modified sniper with modified canny
    subprocess.call([
        sniperPath+"/run-sniper",
        "-n", "1",
        "-c", "gainestown",
        "-g", "fault_injection/injector=\"range\"",
        "-g", "fault_injection/type=\"toggle\"",
        "-g", "fault_injection/affected="+affected,
        "-g", "perf_model/cache/levels=2",
        "--cache-only",
        "--power",
        # "--gdb-wait",
        "--", appPath,
        "-in", inputImage,
        "-out", outputImage,
        "-sigma", sigma,
        "-tlow", tl,
        "-thigh", th,
        "-read-ber", str(read_ber),
        "-write-ber", str(write_ber)
        ])

def launchCanny(inputImage, outputImage):
    subprocess.call([
        appPath,
        "-in", inputImage,
        "-out", outputImage,
        "-sigma", sigma,
        "-tlow", tl,
        "-thigh", th,
        "-read-ber", "0",
        "-write-ber", "0"
        ])

elasticData={}

# Function to process images
def processImage(inputPath):
    launchCannyInSniper(inputPath, "out/%s_%s_w%s_r%s.pgm" % (frameName, affected, str(write_ber), str(read_ber)))
    # When running in HPC, we use a fixed copy, so not required to do this iteratively 
    launchCanny(inputPath, "out/%s_o.pgm" % frameName)

    #Evaluate
    print("Processed " + inputPath +
          " having WBER " + str(write_ber) + " with score : "),

    scoreMe = eval.score_me("out/%s_%s_w%s_r%s.pgm" % (frameName, affected, str(write_ber), str(read_ber)), "out/%s_o.pgm" %frameName)
    print scoreMe


def process(path):
    global finalScore
    global write_ber
    global read_ber

    print (path)
    
    #  ************************************************************
    #  Sniper code goes here***************************************
    vidObj = cv2.VideoCapture(path)
    count = 0
    success = 1

    if not os.path.exists("in"):
      os.makedirs("in")
    if not os.path.exists("out"):
      os.makedirs("out")

    while success:
        success, image = vidObj.read()
        if (count == jump_to_frame):
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            cv2.imwrite("in/%s_%d.pgm" % (frameName, count), gray_image)

            print(str(write_ber))
            print(str(read_ber))

            launchCannyInSniper(
                "in/%s_%d.pgm" % (frameName, count),
                "out/%s_%d.pgm" % (frameName, count)
                )

            launchCanny(
                "in/%s_%d.pgm" % (frameName, count),
                "out/%s_o_%d.pgm" % (frameName, count)
            )
            
            #Evaluate
            print("Processed %s having WBER %s with score : " % (str(count+1), str(write_ber)) ),
            finalScore = eval.score_me("out/%s_o_%d.pgm" % (frameName, count), "out/%s_%d.pgm" % (frameName, count))
        count += 1
    print ("total frames: ", count)
    #  ************************************************************

    print (finalScore)

    elasticData['dataset'] = frameName
    elasticData['affected'] = affected
    elasticData['frame'] = jump_to_frame
    elasticData['readError']  = read_ber
    elasticData['writeError'] = write_ber
    elasticData['scoreMe'] = finalScore
    elasticData['isCalibrateFrame'] = isCalibrateFrame
    elasticData['knob']  = knob1
    elasticData['knob2'] = knob2
    elasticData['kp'] = kp
    elasticData['target'] = float(target_ber)
    elasticData['ki'] = ki
    elasticData['manual'] = isManual
    elasticData['sampling'] = sampling
    

    with open('energyData.txt') as json_file:  
      energyData = json.load(json_file)

    elasticData.update(energyData)
    print (elasticData)
    res=es.index(index='siso',body=elasticData)
    print (res)

def returnScore():
  f = open("tmp"+str(jump_to_frame)+".txt", "w")
  f.write(str(finalScore))

def main(argv):
    global write_ber
    global read_ber

    global frameName
    global jump_to_frame
    global isCalibrateFrame
    global target_ber
    global knob1
    global knob2
    global kp
    global ki
    global isManual
    global sampling

    for x in argv[1:]:
        key=x.partition("=")[0]
        value=x.partition("=")[2]
        if(key=='write_ber'):
          write_ber=float(value)
        if(key=='read_ber'):
          read_ber=float(value)
        if(key=='jump_to_frame'):
          jump_to_frame=int(value)
        if(key=='isCalibrateFrame'):
          isCalibrateFrame=value
        if(key=='knob1'):
          knob1=float(value)
        if(key=='knob2'):
          knob2=float(value)
        if(key=='set_point'):
          target_ber=float(value)
        if(key=='kp'):
          kp=float(value)
        if(key=='ki'):
          ki=float(value)
        if(key=='isManual'):
          isManual=value
        if(key=='sampling'):
          sampling=value

    if "mp4" in input:
      process(input)
    else:
      processImage(input)

    returnScore()

if __name__ == "__main__":
    main(sys.argv)