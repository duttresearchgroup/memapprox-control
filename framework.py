# Program To Launch approximation framework
import cv2
import subprocess
import ConfigParser
import os
import eval
import json
import urllib2
import sys

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
frameName = (os.path.basename(input))
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

index = 0

elasticData={}

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
        #"--gdb-wait",
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

    elasticData['frame'] = frameName
    elasticData['writeError'] = write_ber
    elasticData['readError'] = read_ber
    elasticData['scoreMe'] = scoreMe
    elasticData['affected'] = affected
    elasticData['index'] = index
    
    print elasticData

    if(upload_to_elastic):
        req = urllib2.Request('http://deep.ics.uci.edu:9200/approx/model/')
        req.add_header('Content-Type', 'application/json')
        response = urllib2.urlopen(req, json.dumps(elasticData))

# Function to extract frames and process them
def processVideo(path):
    global write_ber
    global read_ber

    # Path to video file
    vidObj = cv2.VideoCapture(path)

    # Used as counter variable
    count = 0

    # checks whether frames were extracted
    success = 1

    while success:
        # vidObj object calls read
        # function extract frames
        success, image = vidObj.read()

        # Saves the frames with frame-count
        if (count == jump_to_frame):
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            cv2.imwrite("in/%s_%d.pgm" % (frameName, count), gray_image)

            # unmodified canny without approx
            # subprocess.call(["/workspace/Approximation/Original/canny-orig/canny_edge","/workspace/Approximation/Modified/PID/in/frame%d.pgm"  % file_number,sigma,tl, th])

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
            scoreMe = eval.score_me("out/%s_o_%d.pgm" % (frameName, count), "out/%s_%d.pgm" % (frameName, count))
            print scoreMe
            
            elasticData['frame'] = frameName
            elasticData['writeError'] = write_ber
            elasticData['readError'] = read_ber
            elasticData['scoreMe'] = scoreMe
            elasticData['affected'] = affected
            elasticData['index'] = count

            print elasticData

            if(upload_to_elastic):            
                req = urllib2.Request('http://deep.ics.uci.edu:9200/approx/model/')
                req.add_header('Content-Type', 'application/json')
                response = urllib2.urlopen(req, json.dumps(elasticData))
            
        count += 1

    print ("total frames: ", count)
  
def main(argv):
    global write_ber
    global read_ber
    global index
    global frameName
    global jump_to_frame

    for x in argv[1:]:
        key=x.partition("=")[0]
        value=x.partition("=")[2]
        if(key=='write_ber'):
          write_ber=value  
        if(key=='read_ber'):
          read_ber=value
        if(key=='index'):
          index=value
          jump_to_frame=int(value)
        if(key=='frameName'):
          frameName=value

    if "mp4" not in input:
        processImage(input)
    else:
        # Extract frames and perform the task on each 
        # subprocess.call("rm -rf in", shell=True)
        # os.mkdir("in")
        # subprocess.call("rm -rf out", shell=True)
        # os.mkdir("out")
        if not os.path.exists("in"):
            os.makedirs("in")
        if not os.path.exists("out"):
            os.makedirs("out")
            
        print ("Processing Video")
        processVideo(input) 
        # subprocess.call("rm -rf in", shell=True)

if __name__ == "__main__":
    main(sys.argv)