#!/bin/bash -l
#SBATCH --mem=20G
#SBATCH --ntasks=8
#SBATCH --output=./transport_test.log
#SBATCH --time=60
#SBATCH --export=NONE
cd /home/users/max.thomas/projects/esmvaltool/development
#module load scitools/community/esmvaltool/2.10.0
conda activate esmvaltool-2.11.0-strait_flux
esmvaltool run recipe_arctic_transport.yml --config_file ./config-user.yml
 
