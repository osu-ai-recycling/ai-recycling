#!/bin/bash
#SBATCH -J recycling        # name of my job
#SBATCH -p gpu,dgxh         # name of partition/queue to use
#SBATCH -o recycling.out    # name of output file for batch script
#SBATCH -e recycling.err    # name of error file for batch script
#SBATCH -c 1                # number of cores per task
#SBATCH -t 0                # number of threads per task
#SBATCH --time=1-00:00:00   # time needed for job
#SBATCH --mem=10g           # memory needed for job
#SBATCH --gres=gpu:1        # consumable resources needed for job
#SBATCH --mem=10g           # memory needed for job

cd ~/hpc-share/ai-recycling/ai-recycling

# gather basic information, can be useful for troubleshooting
hostname
echo $SLURM_JOBID
showjob $SLURM_JOBID

# load modules needed for job
module load slurm
module restore recycling_module

# run my job
date
echo "Running ai-recycling from bash shell"
echo

# Load/update environment
source ./.recyclingEnv/bin/activate
#python3 -m pip install --upgrade pip
pip install -q -r ./requirements.txt

# Run training
file="output_$(date +"%Y_%m_%d_%I_%M_%p").log"
python3 train.py --noplots $@ &> "../$file"

# Copy new files to austin's server
rsync -a --ignore-existing ~/hpc-share/ai-recycling/ai-recycling/runs/train/* austin:~/outputs
scp "../$file" austin:~/outputs

date
