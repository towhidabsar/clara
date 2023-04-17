#!/bin/bash
basejobname="clara"

# Another constant variable used to name the slurm submission file that
#   this script is going to submit to slurm.
jobfile="payload.sh"

# param_limit_alpha=17280
param_limit_alpha=275808

# Make an output directory if it doesn't already exist.
mkdir --p output

# Load all the required packages
#  1023  spack load py-pip
# spack load /u64kqpe /qwjltbh /i7uffxz /rtjl5w4
# Loop and submit all the jobs
echo
echo " * Getting ready to submit a number of jobs:"

for start in $(seq 0 1000 $param_limit_alpha); do
    jobname=$basejobname-$start
    echo "Submitting job $jobname"
    end=$((start+1000))
    outfile=output/output-$start.txt
    export start;
    export end;

    # Actually submit the job.
    sbatch  --job-name $jobname --output $outfile $jobfile
done

echo
echo " * Done submitting all those jobs (whew!)"
echo " * Now you can run the following command to see your jobs in the queue:"
echo
echo " $ squeue"
echo