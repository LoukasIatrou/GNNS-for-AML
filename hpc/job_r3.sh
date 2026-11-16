#!/bin/bash
# Role 3 GNN re-run on the Bocconi HPC (SLURM). Usage, from a clone of this repository:
#   bash hpc/setup.sh            # once: conda env in ~/aml_gnn/env + dataset download
#   cd hpc && sbatch job_r3.sh   # ~3 min on one GPU slice; writes hpc/r3out/
#SBATCH --job-name=aml_gnn
#SBATCH --partition=stud
#SBATCH --gres=gpu:4g.40gb:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=%x_%j.log
module load miniconda3
source activate ~/aml_gnn/env 2>/dev/null || conda activate ~/aml_gnn/env
export DATA_DIR=$(ls -d ~/.cache/kagglehub/datasets/ellipticco/elliptic-data-set/versions/1)
nvidia-smi -L
cd "$SLURM_SUBMIT_DIR"; mkdir -p r3out
python run_r3.py
