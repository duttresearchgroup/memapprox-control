/* Simple MPI Hello World demo program.
 5/2006  J. Farran
*/

#include <stdio.h>
#include <unistd.h>

#include "mpi.h"

#include <iostream>
using namespace std;

#define TERMINATE -1
#define MAX_FRAMES 100

int main(int argc, char *argv[])
{
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

  if (my_rank == 0)
  { /* We are the Main node */

    printf("Hello World.   I am the Master Node (%s) with Rank 0.\n", host);

    int frame = 0;
    while (frame < MAX_FRAMES)
    {
      for (i = 1; i < num_proc; i++)
      {
        MPI_Send(&frame, 1, MPI_INT, i, 0, MPI_COMM_WORLD);
        frame++;
      }

      double avgScore = 0;
      for (i = 1; i < num_proc; i++)
      {
        double score = 0;
        MPI_Recv(&score, 1, MPI_DOUBLE, i, tag, MPI_COMM_WORLD, &status);
        avgScore += score;

        cout << "Completed with " << score << endl;

        // MPI_Recv(buff, 100, MPI_CHAR, i, tag, MPI_COMM_WORLD, &status);
        // printf("Hello World.   %s\n", buff);
      }

      avgScore /= (num_proc-1);
      cout << "Average score at " << frame << " frames : " << avgScore << endl;
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
      // printf("%d received task %d\n", my_rank, task);

      if (task != TERMINATE)
      {
        double score = 1.234 * my_rank;
        MPI_Send(&score, 1, MPI_DOUBLE, dest, tag, MPI_COMM_WORLD);

        // sprintf(buff, "I am compute Node (%s) with Rank %d", host, my_rank);
        //   MPI_Send(buff, 100, MPI_CHAR, dest, tag, MPI_COMM_WORLD);
      }
    }
  }

  MPI_Finalize();
  return 0;
}
