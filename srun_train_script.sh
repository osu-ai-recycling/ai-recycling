# cd ~/hpc-share/ai-recycling/ai-recycling/

date >> ~/hpc-share/ai-recycling/log_srun.log

srun -p gpu,dgxh --gres=gpu:1 --time=1-00:00:00 --pty ~/hpc-share/ai-recycling/ai-recycling/training_script.sh >> ~/hpc-share/ai-recycling/log_srun.log 2>> ~/hpc-share/ai-recycling/log_srun.log
#srun -p gpu,dgxh,dgx2 -t 4 --gres=gpu:1 --mem=10g --time=1-00:00:00 --pty ~/hpc-share/ai-recycling/ai-recycling/training_script.sh >> ~/hpc-share/ai-recycling/log_srun.log 2>> ~/hpc-share/ai-recycling/log_srun.log
# srun ~/hpc-share/ai-recycling/ai-recycling/training_script.sh >> ~/hpc-share/ai-recycling/log_srun.log 2>> ~/hpc-share/ai-recycling/log_srun.log

echo "──────────────────────────────────────────" >> ~/hpc-share/ai-recycling/log_srun.log
echo >> ~/hpc-share/ai-recycling/log_srun.log
