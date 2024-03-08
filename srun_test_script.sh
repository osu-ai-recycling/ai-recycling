# cd ~/hpc-share/ai-recycling/ai-recycling/

date >> ~/hpc-share/ai-recycling/log_srun.log

srun -p gpu,dgx2,dgxh,share --gres=gpu:1 --mem=20g --time=1-00:00:00 --pty ~/hpc-share/ai-recycling/ai-recycling/test_server_script.sh >> ~/hpc-share/ai-recycling/log_srun.log 2>> ~/hpc-share/ai-recycling/log_srun.log
# srun -p gpu,dgxh,share -t 4 --gres=gpu:1 --mem=10g --time=1-00:00:00 --pty ~/hpc-share/ai-recycling/ai-recycling/test_server_script.sh >> ~/hpc-share/ai-recycling/log_srun.log 2>> ~/hpc-share/ai-recycling/log_srun.log
# srun ~/hpc-share/ai-recycling/ai-recycling/test_server_script.sh >> ~/hpc-share/ai-recycling/log_srun.log 2>> ~/hpc-share/ai-recycling/log_srun.log

echo "──────────────────────────────────────────" >> ~/hpc-share/ai-recycling/log_srun.log
echo >> ~/hpc-share/ai-recycling/log_srun.log
