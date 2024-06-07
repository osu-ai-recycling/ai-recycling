#!/bin/bash
#SBATCH -J recycling        # name of my job
#SBATCH -p dgxh,dgxs,dgx2   # name of partition/queue to use
#SBATCH --time=1-00:00:00   # time needed for job
#SBATCH --gres=gpu:1        # consumable resources needed for job
#SBATCH --mem=20G           # memory needed for job
#SBATCH -o recycling_%j.out    # name of output file for batch script
#SBATCH -e recycling_%j.err    # name of error file for batch script
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=keel@oregonstate.edu

repo_dir=$HOME/hpc-share/ai-recycling/ai-recycling
cd $repo_dir

# Load Environment variables
source ~/.bashrc
source /etc/profile

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

# Load/update environment
source recyclingEnv/bin/activate

# Run training
file="../output_$(date +"%Y_%m_%d_%I_%M_%p")_$SLURM_JOB_ID"
echo "python3 train.py --noplots $@ $file.log"
python3 train.py --noplots $@ &> $file.log

# Deactivate environment
deactivate

date

mv $repo_dir/recycling_$SLURM_JOB_ID.out $file.out
mv $repo_dir/recycling_$SLURM_JOB_ID.err $file.err
