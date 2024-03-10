date >> ~/hpc-share/ai-recycling/log_srun.log

srun -p gpu,dgxh --gres=gpu:1 --mem=20g --time=1-00:00:00 --pty ~/hpc-share/ai-recycling/ai-recycling/test_server_script.sh $@ &>> ~/hpc-share/ai-recycling/log_srun.log

echo "──────────────────────────────────────────" >> ~/hpc-share/ai-recycling/log_srun.log
echo >> ~/hpc-share/ai-recycling/log_srun.log
