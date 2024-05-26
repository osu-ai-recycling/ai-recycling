date >> ~/hpc-share/ai-recycling/log_srun.log

echo "sbatch ~/hpc-share/ai-recycling/ai-recycling/training_script.sh $@"

sbatch ~/hpc-share/ai-recycling/ai-recycling/training_script.sh $@ &>> ~/hpc-share/ai-recycling/log_srun.log

echo "──────────────────────────────────────────" >> ~/hpc-share/ai-recycling/log_srun.log
echo >> ~/hpc-share/ai-recycling/log_srun.log
