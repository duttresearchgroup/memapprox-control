#include <stdlib.h>
#include <math.h>
#include <string.h>

#include "MiniPID.h"
#include "PID.h"
#include "recalibrate.h"

#include <stdio.h>
#include <unistd.h>

#include "mpi.h"

#include <fstream>
#include <cstdlib>
#include <iostream>

using namespace std;

#define TERMINATE -1
#define MAX_FRAMES 100

char buff_pid[1000];
double getScore(int frame)
{
  ifstream ifile("../tmp" + to_string(frame) + ".txt", ios::in);

  //check to see that the file was opened correctly:
  if (!ifile.is_open())
  {
    std::cerr << "There was a problem opening the input file!\n";
    exit(1); //exit or do additional error checking
  }

  double num = 0.0;
  //keep storing values from the text file so long as data exists:
  ifile >> num;

  snprintf(buff_pid, sizeof(buff_pid), "rm -rf ../tmp%d.txt", frame);
  cout << buff_pid << endl;

  system(buff_pid);

  return num;
}

int main(int argc, char *argv[])
{
  // ********************************************
  // ********************************************
  int my_rank;
  int num_proc;
  int dest = 0;
  int tag = 0;
  int i;
  MPI_Status status;
  char host[80];  /* Hostname */
  char buff[200]; /* MPI Send & Receive buffer */

  MPI_Init(&argc, &argv);

  MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);  /* Get my_rank */
  MPI_Comm_size(MPI_COMM_WORLD, &num_proc); /* How many processes we have */

  gethostname(host, 40);
  // ********************************************

  // ********************************************
  // ********************************************
  int repeat_frame = 1;
  int num_frames = 1000;

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

  if (system(NULL))
    puts("Ok");
  else
    exit(EXIT_FAILURE);
  // ********************************************

  if (my_rank == 0)
  { /* We are the Main node */

    printf("Hello World.   I am the Master Node (%s) with Rank 0.\n", host);

    int frame = 0;
    while (frame < MAX_FRAMES)
    {
      /****************************************************************************
         * Control stuff: change setpoint
         ****************************************************************************/
      if (set_point_ptr < max_set_points - 1)
      {
        if (frame == frames_set_point[set_point_ptr + 1])
        {
          set_point_ptr++;
          set_point = set_points[set_point_ptr];
          ctrl.errorFilter.ref(set_point); //Controller 1
          pid.setSetpoint(set_point);      //Controller 2
        }

        printf("frame : %d \t set_point: %lf\n", frame, set_point);
      }

      for (i = 1; i < num_proc; i++)
      {
        MPI_Send(&frame, 1, MPI_INT, i, 0, MPI_COMM_WORLD);
        MPI_Send(&knob1, 1, MPI_DOUBLE, i, 0, MPI_COMM_WORLD);
        MPI_Send(&knob2, 1, MPI_DOUBLE, i, 0, MPI_COMM_WORLD);
        MPI_Send(&current_write_ber, 1, MPI_DOUBLE, i, 0, MPI_COMM_WORLD);
        MPI_Send(&current_read_ber, 1, MPI_DOUBLE, i, 0, MPI_COMM_WORLD);
        MPI_Send(&set_point, 1, MPI_DOUBLE, i, 0, MPI_COMM_WORLD);

        frame++;
      }

      double avgScore = 0;
      for (i = 1; i < num_proc; i++)
      {
        double score = 0;
        MPI_Recv(&score, 1, MPI_DOUBLE, i, tag, MPI_COMM_WORLD, &status);
        avgScore += score;

        cout << "Completed with " << score << endl;
      }

      avgScore /= (num_proc - 1);
      cout << "Average score at " << frame << " frames : " << avgScore << endl;

      double new_ber;
      if (control_mode == 0)
      {
        // PID
        // get new settings from PID controller
        knob1 = pid.getOutput(avgScore, set_point);
        printf("knob1 setting = %f\n", knob1);

        knob2 = ctrl.nextInput(avgScore);
        printf("knob2 setting = %f\n", knob2);

        new_ber = knob2;
        new_ber += ctrl_out_adjustment;
      }
      else
      {
        // Manual Recalibration
        double knob3 = manual_calibrations(current_write_ber, avgScore, set_point);
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

    for (i = 1; i < num_proc; i++)
    {
      int terminate = TERMINATE;
      MPI_Send(&terminate, 1, MPI_INT, i, 0, MPI_COMM_WORLD);
    }
  }
  else
  { /* We are the slave compute nodes */
    int task = 1;
    while (task != TERMINATE)
    {
      MPI_Recv(&task, 1, MPI_INT, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);

      if (task != TERMINATE)
      {
        double knob1_slave;
        double knob2_slave;
        double current_write_ber_slave;
        double current_read_ber_slave;
        double set_point_slave;

        // READ others
        MPI_Recv(&knob1_slave, 1, MPI_DOUBLE, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        MPI_Recv(&knob2_slave, 1, MPI_DOUBLE, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        MPI_Recv(&current_write_ber_slave, 1, MPI_DOUBLE, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        MPI_Recv(&current_read_ber_slave, 1, MPI_DOUBLE, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        MPI_Recv(&set_point_slave, 1, MPI_DOUBLE, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        
        snprintf(buff_pid, sizeof(buff_pid),
                 "cd .. && python pi_runSniper.py %s=%lf %s=%lf %s=%lf %s=%lf %s=%s %s=%d %s=%lf",
                 "knob1", knob1_slave,
                 "knob2", knob2_slave,
                 "read_ber", current_read_ber_slave,
                 "write_ber", current_write_ber_slave,
                 "isCalibrateFrame", "true",
                 "jump_to_frame", task,
                 "set_point", set_point_slave);

        system(buff_pid);
        double score_slave = getScore(task);
        MPI_Send(&score_slave, 1, MPI_DOUBLE, dest, tag, MPI_COMM_WORLD);
      }
    }
  }

  MPI_Finalize();
  return 0;
}
