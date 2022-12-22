#!/bin/bash -l
# NOTE the -l flag!

#payload.sh
 
# Where to send mail...
#To send emails, set the adcdress below and remove one of the "#" signs.
#SBATCH --mail-user=mac9908@rit.edu
 
# notify on state change: BEGIN, END, FAIL or ALL
##SBATCH --mail-type=FAIL
 
# Request 5 minutes run time MAX, if the job runs over it will be KILLED
#SBATCH --time 0-6:00:0 #Time limit day-hrs:min:sec
##SBATCH --gres=gpu --constraint="vram40|vram32"

# Put the job in the partition associated with the account and request one core
#SBATCH --account quality-of-life
#SBATCH --partition tier3
#SBATCH --ntasks=1 #This option advises the Slurm controller that job steps run within the allocation will launch a maximum of number tasks and to provide for sufficient resources.
#SBATCH -c 8
# Job memory requirements in MB=m (default), GB=g, TB=t
#SBATCH --mem=64GB
## SBATCH --output=run-%J.out
## SBATCH --error=run-%J.err
 
echo "I am processing job number $start for the Youtube Channel $network"
echo "And now I'm going to run the python script"
echo $(awk '$3=="kB"{$2=$2/1024^2;$3="GB";} 1' /proc/meminfo | column -t | grep MemTotal)
python clara_script.py /home/mac9908/clara/dataset
# $start $network

echo "All done with my work.  Exiting."
# sbatch  --job-name youtube --output explode-out.txt payload.sh