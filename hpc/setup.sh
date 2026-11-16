# One-time environment for hpc/job_r3.sh (conda-forge channel, CUDA 12.1 PyTorch wheels).
module load miniconda3
conda create -y -q -p ~/aml_gnn/env -c conda-forge --override-channels python=3.11
source activate ~/aml_gnn/env 2>/dev/null || conda activate ~/aml_gnn/env
pip install -q torch==2.5.1 --index-url https://download.pytorch.org/whl/cu121
pip install -q torch_geometric "scikit-learn==1.8.0" "pandas==2.2.3" "numpy<2.3" kagglehub matplotlib
python -c "import kagglehub;print(kagglehub.dataset_download(\"ellipticco/elliptic-data-set\"))"
python -c "import torch,torch_geometric,sklearn;print(torch.__version__,torch_geometric.__version__,sklearn.__version__)"
echo SETUP_DONE
