#!/bin/bash

# specify the Q run in; MODIFY based on the output of 'q'
# so you can submit to an underused Q
#$ -q free128

# the qstat job name; this name -> $JOB_NAME variable
# MODIFY to reflect your run
#$ -N task-dram-write

# use the real bash shell - KEEP
#$ -S /bin/bash

# execute the job out of the current dir and direct the error
# (.e) and output (.o) to the same directory ...
# Generally, KEEP, unless you have good reason NOT to use it.
#$ -cwd

# ... Except, in this case, merge the output (.o) and error (.e) into one file
# If you're submitting LOTS of jobs, this halves the filecount and also allows
# you to see what error came at what point in the job.
# KEEP unless there's
# good reason NOT to use it.
#$ -j y

#!! NB: that the .e and .o files noted above are the STDERR and STDOUT, not necessarily
#!! the programmatic output that you might be expecting.  That output may well be sent to
#!! other files, depending on how the app was written.

#  !! ABSOLUTELY DO NOT USE email notificationa for TASK ARRAYS !!
#  !! THIS IS A TASK ARRAY !!

# and here we define the range of the TASK ARRAY index, from 1 to 40
# Remember the variable that carries this variables is called '$SGE_TASK_ID'.
#$ -t 1-144

###### END SGE PARAMETERS  ######

###### BEGIN BASH CODE  ######
#  no more hiding them behind '#$'

# uncomment the following line for testing in a bash shell prior to submitting it to SGE
# then RE-comment it when you qsub it.
# SGE_TASK_ID=5
# format the $SGE_TASK_ID to the format required (5 digits, with leading zeros)
# in the format string "%05d", the '0' means to pad with zeros, the '5' means 5 digits,
# the 'd' means to format as an integer (no decimal point).  If for some reason you wanted to
# to format as a floating point number, "%09.4f" would print '66' as '0066.0000'
# (9 characters, 4 decimal points, leading zeros to pad it out)

SGE_TASK_ID=$((SGE_TASK_ID-1))

nbr=$(printf "0.%08d" $((SGE_TASK_ID*25)))
idx=$(printf "%08d" $SGE_TASK_ID)

# let's define an output dir & create it.
OUTDIR=/pub/$USER/test_task_dir_write_dram/$idx
mkdir -p  $OUTDIR
mkdir -p  $OUTDIR/out
FILENAME="marymax_${nbr}.sh"
echo '#!/bin/bash' >  $OUTDIR/$FILENAME

for i in `seq 0 9`;
    do
        echo 'python /data/users/maityb/Modified/PID/video.py write_ber='$nbr' read_ber=0.0 index='$idx$i' frameName=marymax_8 >/dev/null 2>&1' >>  $OUTDIR/$FILENAME
    done

echo "# Running on `hostname`" >> $OUTDIR/$FILENAME
cp config_dram.ini $OUTDIR/config.ini
# cp image_o.pgm $OUTDIR/out
cd $OUTDIR
bash $FILENAME