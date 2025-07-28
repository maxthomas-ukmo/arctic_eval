#!/bin/bash -l
cd "$(dirname "$0")"
#SBATCH --mem=100G
#SBATCH --ntasks=8
#SBATCH --output=./seaice_eval.log
#SBATCH --time=60
#SBATCH --export=NONE
conda activate arctic_eval
esmvaltool run recipe_arctic_seaice.yml --config_file ../config/config-user.yml
