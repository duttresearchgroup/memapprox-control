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

Config = ConfigParser.ConfigParser()
Config.read("config.ini")

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
index = 0
knob1=0
knob2=0
finalScore=0

def launchCannyInSniper(inputImage, outputImage):
    # Modified sniper with modified canny
    subprocess.call([
        sniperPath+"/run-sniper",
        "-n", "1",
        "-c", "gainestown",
        "-g", "fault_injection/injector=\"range\"",
        "-g", "fault_injection/type=\"toggle\"",
        "-g", "fault_injection/affected="+affected,
        # "-g", "perf_model/cache/levels=0",
        "--cache-only",
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

def process(path):
    global finalScore

    #  ************************************************************
    #  Sniper code goes here***************************************
    global write_ber
    global read_ber

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

    print finalScore

    elasticData['dataset'] = frameName
    elasticData['affected'] = affected
    elasticData['frame'] = jump_to_frame
    elasticData['readError']  = read_ber
    elasticData['writeError'] = write_ber
    elasticData['scoreMe'] = finalScore
    elasticData['isCalibrateFrame'] = isCalibrateFrame
    elasticData['knob']  = knob1
    elasticData['knob2'] = knob2

    print elasticData
    if (upload_to_elastic):
      req = urllib2.Request('http://deep.ics.uci.edu:9200/siso/siso_map/')
      req.add_header('Content-Type', 'application/json')
      response = urllib2.urlopen(req, json.dumps(elasticData))

def returnScore():
  f = open("tmp.txt", "w")
  f.write(str(finalScore))

def main(argv):
    global write_ber
    global read_ber
    global index
    global frameName
    global jump_to_frame
    global isCalibrateFrame

    global knob1
    global knob2

    for x in argv[1:]:
        key=x.partition("=")[0]
        value=x.partition("=")[2]
        if(key=='write_ber'):
          write_ber=value  
        if(key=='read_ber'):
          read_ber=value
        if(key=='jump_to_frame'):
          jump_to_frame=int(value)
        if(key=='isCalibrateFrame'):
          isCalibrateFrame=value
        if(key=='knob1'):
          knob1=value
        if(key=='knob2'):
          knob2=value
            
    if "mp4" in input:
      process(input)
  
    returnScore()

if __name__ == "__main__":
    main(sys.argv)