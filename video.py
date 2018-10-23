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
        if (count%skipFrames == 0):
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            cv2.imwrite("in/frame%d.pgm" % file_number, gray_image)
            
            subprocess.call(["/workspace/Approximation/Original/canny-orig/canny_edge","/workspace/Approximation/Modified/PID/in/frame%d.pgm"  % file_number,sigma,tl, th])

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