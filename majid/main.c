#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

#include "MiniPID.h"
#include "PID.h"
#include "recalibrate.h"

main(int argc, char *argv[])
{
    int repeat_frame = 1;
    int control_mode = 0; // 0: PID, 1: Recalibration

    bool enable_calibration = false;
    int sampling_frequency = 1;
    bool report_errors = false;

    int set_point_ptr = -1;
    int max_set_points = 3;
    int frames_set_point[] = {1, 400, 800};
    double set_points[] = {0.01, 0.001, 0.005};

    double ctrl_out_adjustment = 5.0002e-04;
    double set_point = 0.02;

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

    /****************************************************************************
    * Main loop
    /****************************************************************************/

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
                unsigned char *edge_golden;

                double current_read_ber = 0;
                double current_write_ber = 0;

                get_read_ber(&current_read_ber);
                get_write_ber(&current_write_ber);

                set_read_ber(0);
                set_write_ber(0);

                canny(image, rows, cols, sigma, tlow, thigh, &edge_golden, dirfilename);

                set_read_ber(current_read_ber);
                set_write_ber(current_write_ber);

                error += score_me(edge_golden, edge, cols, rows);
                if (j == repeat_frame)
                {
                    printf("frame = %04d, error_me = %f, error_r = %f, current_knob = %f, set_point = %f\n",
                           i, error / (double)repeat_frame, score_r(edge_golden, edge, cols, rows), current_write_ber, set_point);
                }

                free(edge_golden);
            }

            if (perform_calibration && (j == repeat_frame))
            {
                double current_read_ber = 0;
                double current_write_ber = 0;

                get_read_ber(&current_read_ber);
                get_write_ber(&current_write_ber);

                double new_read_ber = 0;
                double new_write_ber = 0;

                if (control_mode == 0)
                { // PID
                    // get new settings from PID controller
                    double knob1 = pid.getOutput(error / (double)j, set_point);
                    //printf("knob1 setting = %f\n", knob1);

                    double knob2 = ctrl.nextInput(error / (double)j);
                    //printf("knob2 setting = %f\n", knob2);

                    new_write_ber = knob2;
                    new_write_ber += ctrl_out_adjustment;
                }
                else
                { // Manual Recalibration
                    double knob3 = manual_calibrations(current_write_ber, error, set_point);
                    new_write_ber = knob3;
                }

                new_write_ber = new_write_ber < 0 ? 0 : new_write_ber;
                // printf("new_write_ber = %f\n", new_write_ber);

                if (enable_calibration)
                {
                    // set_read_ber(new_read_ber);
                    set_write_ber(new_write_ber);
                }
            }
        }
    }
}