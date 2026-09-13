# CSC 4792 Group 33 - Mwense Town Council Dataset
Run top to bottom to reproduce `outputs/db-unza26-csc4792-*.csv` (pipe-separated).
conda create -n csc4792 python=3.14 -y && conda activate csc4792
pip install -r requirements.txt
python -m jupyter nbconvert --to notebook --execute mwense-town-council-data-analysis.ipynb --output /tmp/test.ipynb --allow-errors
