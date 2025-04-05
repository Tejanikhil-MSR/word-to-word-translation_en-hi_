#!bin/bash

# Create a new env using conda env -n <env_name> python=3.10

# install the required libraries using pip
echo "Installing required libraries..."
sleep 5
pip install -r requirements.txt

# install the muse dictionary pairs
echo "Installing muse dictionary"
sleep 5
./GeneratedDatasets/extract_muse_dict.sh

# install pytorch that supports cuda
echo "Installing pytorch with cuda support (version 12.1)"
echo -e "\e[33m⚠️ ensure that you have the correct version of cuda installed in your system\e[0m"
sleep 5
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121