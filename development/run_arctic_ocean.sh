#!/bin/bash -l
#SBATCH --mem=20G
#SBATCH --ntasks=8
#SBATCH --output=./MWOA-test.log
#SBATCH --time=60
#SBATCH --export=NONE
cd /home/users/max.thomas/projects/esmvaltool/development
module load scitools/community/esmvaltool/2.10.0
esmvaltool run recipe_arctic_ocean.yml --config_file ./config-user.yml
 