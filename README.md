# Memory Approximation Project

Memory approximation enables trading off quality/accuracy for performance or energy gain.
Application programmers are burdened with the difficult task of setting memory approximation knobs to tune/achieve the delivered QoS.
Our self-adaptive approach for memory approximation eases the programmer's burden:  simply specify the desired quality as a goal, with the system deploying a formal control-theoretic approach to tune the memory reliability knobs and deliver guaranteed QoS. 
We model quality configuration tracking as a formal quality control problem, and outline a System Identification technique that captures memory approximation effects with variations in application input and system architecture.

# Pre-requisite
In order to run the simulations, you will need a modified version of Sniper. We are currently working on a patch where Sniper is modified to support controlled BER for memory components. The patch is hosted on duttresearchgroup github in the [sniper-mem](https://github.com/duttresearchgroup/sniper-mem/tree/AddApproxKnobs) repository.
Please checkout the `AddApproxKnobs` branch as the changes have not been merged to master branch yet. This is a work-in-progress and we will follow a peer-review process before merging the changes to master.

# Steps
The folders are organized as below :

## 1. Generating the data for System Identification
We use HPC cluster at UCI to run simulations in parallel. The simulations make use of task arrays in order to generate the data. The results are pushed into a elastic stack running at deep.ics.uci.edu:9200. 
If starting a new instance of elastic, the mappings can be found in the file 'elastic.txt' which has the http POST required.

## 2. Matlab scripts for System Identification

## 3. Matlab scripts for creating the PID controller

## 4. Run the program in the simulated framework
To invoke the controller, run the command `make run`

## 5. Matlab scripts to plot the target tracking
The Matlab script will scan for all the csv files inside `data` folder and generate the tracking figures for all of them.
To invoke the script run the command `make`

# Note
Please note that this work is currently under review. Please contact us at drg@ics.uci.edu if you would like to use the framework.