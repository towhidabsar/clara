#!/bin/bash

#many-jobs.sh

# This is an example script that loops over two parameters
# (from 1 to 5 for each) and submits 25 jobs to the slurm
# cluster.
#
# Author:  Ralph Bean

# Just a constant variable used throughout the script to name our jobs
#   in a meaningful way.
#SBATCH --account quality-of-life --partition debug
# basejobname="tweet_kbp"
basejobname="clara"

# Another constant variable used to name the slurm submission file that
#   this script is going to submit to slurm.
jobfile="payload.sh"

param_limit_alpha=29265

# Make an output directory if it doesn't already exist.
mkdir --p output

# Load all the required packages
#  1023  spack load py-pip
# spack load /u64kqpe /qwjltbh /i7uffxz /rtjl5w4
# Loop and submit all the jobs
echo
echo " * Getting ready to submit a number of jobs:"
# plist=(1152 1592 334 1672 232 1280 1286 836 1319 1352 1522 170 644 1888 1318 452 560 976 1011 1464 930 1988 1251 211 88 1398 295 423 1707 1393 957 1545 1142 1321 1615 199 1252 1499 1245 1804 1650 1071 513 625 694 565 1815 802 1807 1839 25 65 118 1683 1240 1536 1571 740 299 1354 686 1348 1263 93 878 91 181 1690 1642 1363 1254 1454 437 1780 1582 958 1268 214 77 1508 1618 559 1448 1378 2002 20 1375 830 1350 1828 163 1575 1725 220 695 787 1778 1066 953 872 206 828 818 789 1625 905 572 64 555 1340 1123 813 1930 845 1419 1407 1695 0 464 302 1556 1357 1462 33 75 1332 1463 492 1616)
for start in $(seq 0 1000 $param_limit_alpha); do
# for alpha in ${plist[@]}; do
        # Give our job a meaningful name
    jobname=$basejobname-$start
    echo "Submitting job $jobname"
    end=$((start+1000))
    # Setup where we want the output from each job to go
    outfile=output/output-$start.txt

    # "exporting" variables in bash make them available to your slurm
    # workload.
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