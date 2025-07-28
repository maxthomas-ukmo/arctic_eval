#!/bin/bash -l
cd "$(dirname "$0")"
#SBATCH --mem=20G
#SBATCH --ntasks=8
#SBATCH --output=./MWOA-test.log
#SBATCH --time=60
#SBATCH --export=NONE
conda activate arctic_eval
esmvaltool run recipe_arctic_ocean.yml --config_file ../config/config-user.yml
