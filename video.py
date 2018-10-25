# Program To Read video 
# and Extract Frames 
import cv2 
import subprocess
import ConfigParser
import os

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


input = ConfigSectionMap("Video")['source']
skipFrames = int(ConfigSectionMap("Video")['skipframes'])
sigma = ConfigSectionMap("Canny")['sigma']
tl = ConfigSectionMap("Canny")['tl']
th = ConfigSectionMap("Canny")['th']
sniperPath = ConfigSectionMap("Sniper")['path']
appPath = ConfigSectionMap("Sniper")['app']
affected = ConfigSectionMap("FaultInjector")['affected']
read_ber = ConfigSectionMap("FaultInjector")['read_ber']
write_ber = ConfigSectionMap("FaultInjector")['write_ber']

# Function to extract frames 
def FrameCapture(path): 
    # Path to video file 
    vidObj = cv2.VideoCapture(path) 
  
    # Used as counter variable 
    count = 0
  
    # checks whether frames were extracted 
    success = 1
    file_number = 0

    while success: 
  
        # vidObj object calls read 
        # function extract frames 
        success, image = vidObj.read() 
  
        # Saves the frames with frame-count 
        # if (count%skipFrames == 0):
        if (count == 0):
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            cv2.imwrite("in/frame%d.pgm" % file_number, gray_image)
            
            # unmod canny without approx
            # subprocess.call(["/workspace/Approximation/Original/canny-orig/canny_edge","/workspace/Approximation/Modified/PID/in/frame%d.pgm"  % file_number,sigma,tl, th])
            
            #Modified sniper with modified canny
            subprocess.call([
                sniperPath+"/run-sniper",
                "-n","1",
                "-c", "gainestown",
                "-g", "fault_injection/injector=\"range\"",
                "-g", "fault_injection/type=\"toggle\"",
                "-g", "fault_injection/affected="+affected,
                "--cache-only",
                # "--gdb-wait",
                "--", appPath,
                "-in", "in/frame%d.pgm" % file_number,
                "-out", "out/frame%d.pgm" % file_number,
                "-sigma", sigma,
                "-tlow", tl,
                "-thigh", th,
                "-num-frames", "1",
                "-save-output",
                "-read-ber", read_ber,
                "-write-ber", write_ber,
                "-report-error",
                "-sampling-freq", "1",
                "-repeat-frame", "1",
                "-control-mode", "0"
                ])

            subprocess.call(["rm","-rf","in/frame%d.pgm" % file_number])
            file_number+=1
            print("Processed %d" % file_number)
        
        count += 1
  
# Driver Code 
if __name__ == '__main__': 
    subprocess.call("rm -rf in", shell=True)
    subprocess.call("rm -rf out", shell=True)
    os.mkdir("in")
    os.mkdir("out")

    # Extract frames and perform the task on each 
    FrameCapture(input) 