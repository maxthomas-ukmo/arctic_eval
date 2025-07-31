#!/bin/bash -l

# This is the recipe name, to be searched for in /recipes 
recipe=$1

# Add .yml if missing
if [[ ! $recipe == *.yml ]]; then
    recipe="$recipe.yml"
fi

# Load environment with conda. 
# TODO: -> module load scitools/...
source ~/.bashrc
conda init bash
conda activate arctic_eval

# Run recipe
esmvaltool run recipes/$recipe --config_file ../config/config-user.yml
