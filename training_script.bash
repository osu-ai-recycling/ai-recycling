#!/bin/bash
#SBATCH -J recycling        # name of my job
#SBATCH -p dgxh         # name of partition/queue to use
#SBATCH --time=1-00:00:00   # time needed for job
#SBATCH --gres=gpu:1        # consumable resources needed for job
#SBATCH --mem=20G           # memory needed for job
#SBATCH -o recycling_%j.out    # name of output file for batch script
#SBATCH -e recycling_%j.err    # name of error file for batch script

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
#module load anaconda
#source `which activate`

# run my job
date
echo "Running ai-recycling from bash shell"
echo

echo PATH
echo $PATH

# Load/update environment
#/nfs/stak/a1/rhel5apps/anaconda/2023.03/bin/conda init
#/nfs/stak/a1/rhel5apps/anaconda/2023.03/bin/conda activate recyclingEnv
# pip install -q -r ./requirements.txt
#source /nfs/stak/users/keel/hpc-temp/envs/recyclingEnv/bin/activate
source recyclingEnv/bin/activate
conda deactivate
echo $PATH
whereis pip

# Run training
file="../output_$(date +"%Y_%m_%d_%I_%M_%p")"
echo "python3 train.py --noplots $@ $file.log"
python3 train.py --noplots $@ &> $file.log

# Deactivate environment
#conda deactivate

# Copy new files to austin's server
# WIP: move copies of training exp to s3 due to low storage on ec2
# rsync -a --ignore-existing ~/hpc-share/ai-recycling/ai-recycling/runs/train/* austin:~/outputs
# scp "../$file" austin:~/outputs

date

mv $repo_dir/recycling_$SLURM_JOB_ID.out $file.out
mv $repo_dir/recycling_$SLURM_JOB_ID.err $file.err
