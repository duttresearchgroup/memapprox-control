#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

#include "MiniPID.h"
#include "PID.h"
#include "recalibrate.h"

#include <fstream>
#include <cstdlib>
#include <iostream>
using namespace std;

double getScore()
{
    ifstream ifile("../tmp.txt", ios::in);

    //check to see that the file was opened correctly:
    if (!ifile.is_open()) {
        std::cerr << "There was a problem opening the input file!\n";
        exit(1);//exit or do additional error checking
    }

    double num = 0.0;
    //keep storing values from the text file so long as data exists:
    ifile >> num;

    return num;
}

int main(int argc, char *argv[])
{
    char buff[1000];
    int repeat_frame = 1;
    int num_frames=1000;

    int control_mode = 0; // 0: PID, 1: Recalibration

    bool enable_calibration = true;
    int sampling_frequency = 1;
    bool report_errors = false;

    int set_point_ptr = -1;
    int max_set_points = 3;
    int frames_set_point[] = {1, 400, 800};
    double set_points[] = {0.010, 0.001, 0.005};

    double ctrl_out_adjustment = 5.0002e-04;
    double set_point = 0.02;

    double current_read_ber = 0;
    double current_write_ber = 0;

    /****************************************************************************
     * Controllers.
     ****************************************************************************/

    // Controller 1
    #define MA_DEPTH 40
    typedef Controllers::SISO<double,
                              Filters::Error<double, 1>,
                              Filters::Average<double, MA_DEPTH>>
    PIDController;
    PIDController ctrl;
    ctrl.pid.gains(0.001,
                   0.005,
                   0);
    ctrl.pid.period(0.033);
    ctrl.errorFilter.ref(set_point);

    double weights[MA_DEPTH];

    for (int i = 0; i < MA_DEPTH; i++)
    {
        weights[i] = 1 / double(MA_DEPTH);
    }

    ctrl.inputFilter.weight(weights);

    // Controller 2
    MiniPID pid = MiniPID(0.001,
                          0.005,
                          0);
    pid.setSetpoint(set_point);

    double knob1, knob2;

    if (system(NULL)) puts ("Ok");
        else exit (EXIT_FAILURE);

    /****************************************************************************
    * Main loop
    *****************************************************************************/

    for (int i = 1; i <= num_frames; i++)
    {
        /****************************************************************************
         * Control stuff: change setpoint
         ****************************************************************************/
        if (set_point_ptr < max_set_points - 1)
        {
            if (i == frames_set_point[set_point_ptr + 1])
            {
                set_point_ptr++;
                set_point = set_points[set_point_ptr];
                ctrl.errorFilter.ref(set_point); //Controller 1
                pid.setSetpoint(set_point);      //Controller 2
            }
        }

        printf("i : %d \t set_point: %lf\n", i,set_point);
        
        /****************************************************************************
         * Control stuff: repeat frames
         ****************************************************************************/
        double error = 0;
        for (int j = 1; j <= repeat_frame; j++)
        {
            /****************************************************************************
             * Control stuff
             ****************************************************************************/
            int perform_calibration = (i % sampling_frequency == 0);

            if (report_errors || (perform_calibration && enable_calibration))
            {
                //printf("Please enter the current error (within repeat stage) : ");
                //scanf("%lf",&a);

                snprintf(buff, sizeof(buff), 
                "cd .. && python pi_runSniper.py %s=%lf %s=%lf %s=%lf %s=%lf %s=%s %s=%d %s=%lf",
                    "knob1", knob1, 
                    "knob2", knob2,
                    "read_ber", current_read_ber,
                    "write_ber", current_write_ber,
                    "isCalibrateFrame", "true",
                    "jump_to_frame", i,
                    "set_point", set_point
                );
                
                cout << buff <<endl;

                int ret=system(buff);
                double a = getScore();

                printf ("The score returned was: %lf\n",a);

                error += a;
                if (j == repeat_frame)
                {
                    printf("frame = %04d, error_me = %f, current_knob = %f, set_point = %f\n",
                           i, error / (double)repeat_frame, current_write_ber, set_point);
                }
            }

            if (perform_calibration && (j == repeat_frame))
            {
                double new_ber;
                if (control_mode == 0)
                { 
                    // PID
                    // get new settings from PID controller
                    knob1 = pid.getOutput(error / (double)j, set_point);
                    printf("knob1 setting = %f\n", knob1);

                    knob2 = ctrl.nextInput(error / (double)j);
                    printf("knob2 setting = %f\n", knob2);

                    new_ber = knob2;
                    new_ber += ctrl_out_adjustment;
                }
                else
                { 
                    // Manual Recalibration
                    double knob3 = manual_calibrations(current_write_ber, error, set_point);
                    new_ber = knob3;
                }

                new_ber = new_ber < 0 ? 0 : new_ber;
                // printf("new_ber = %f\n", new_ber);

                if (enable_calibration)
                {
                    // current_read_ber = new_ber;
                    current_write_ber = new_ber;
                }
            }
        }
    }
}