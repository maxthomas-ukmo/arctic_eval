# Development of Arctic evaluation tools 
# *Author: Max Thomas*
---
## Overview
This repository contains ESMValTool recipes for evaluating climate models with an Arctic focus.

There are three evaulation tools for the Arctic:
- *sea ice*: with a focus on sea-ice data
- *transports*: which uses the StraitFlux package to calculate volume, heat, and salt fluxes through Arctic gateways
- *ocean*: which just updates an existing recipe to take HadGEM3 data

## Getting started
First get the public repository.
```
git clone git@github.com:maxthomas-ukmo/arctic_eval.git
```
Then create the required environment.
```
cd arctic_eval
conda create --name arctic_eval --file environment/arctic_eval.lock
```
The *arctic_eval* environment duplicates the Met Office's internal scitools/community/esmvaltool-2.11.0 and adds dependencies for StraitFlux. Activate the environment using 
```conda activate arctic_eval```, or let the run scripts (below) do that for you.

The next step is to edit the ```config/config-user.yml``` file and make paths appropriate for the given user.

There is a run script for each of the recipes. Once the environment is created, a user can get started by
```
cd code
./run_arctic_seaice.sh
```
which loads the environment and runs ```recipe_arctic_seaice.yaml```. If the recipe runs sucessfully, terminal output should contain a path to the recipe output, like:
```
INFO    Wrote recipe output to:
file://<path/to/recipe output>/index.html
```
Inspect this with ```firefox /<path/to/recipe output>/index.html```.

---
## Overview
The directory structure is:
```
├── code
│   ├── archive_recipe.sh
│   ├── diag_scripts
│   │   ├── arctic_eval.py
│   │   ├── arctic_seaice
│   │   │   ├── arctic_seaice.py
│   │   │   ├── __init__.py
│   │   │   ├── plotting.py
│   │   │   └── utils.py
│   │   └── __init__.py
│   ├── plot_formatting.yml
│   ├── readme
│   ├── recipe_arctic_ocean.yml
│   ├── recipe_arctic_seaice.yml
│   ├── recipe_arctic_transport.yml
│   ├── run_arctic_ocean.sh
│   ├── run_arctic_seaice.sh
│   └── run_arctic_transport.sh
├── config
│   └── config-user.yml
├── environment
│   ├── arctic_eval.lock
│   ├── arctic_eval.yaml
│   ├── duplicate_a_scitools_env.sh
│   ├── esmvaltool-2.11.0.lock
│   └── readme
└── README.md
```

## Sea-ice evaluation
The key files for the sea-ice evaluation are:
```
code/run_arctic_seaice.sh
code/recipe_arctic_seaice.yaml
code/diag_scripts/arctic_eval.py
code/diag_scripts/utils.py
code/diag_scripts/plotting.py
```

The run script is just loadsd the environment and runs the recipe via Spice. The recipe calls ```arctic_eval.py``` several times, and passes a configuration file telling it what to do. 

Each analysis type exists as a class in ```plotting.py```, and typically one instance of a class is made for each dataset in each panel.

Each class in ```plotting.py``` inherits from a the ```Loader``` class in ```utils.py```. The loader finds the netcdfs that ESMValTool has created, loads them to ```iris``` cubes, and does some processing requested by the recipe. 

For example, a seasonal cycle plot of integrated sea-ice area for HadGEM3-GC3.1-LL and HadISST reanalysis, for the Amerasian and Eurasian basins, would go through these steps:
- ```arctic_eval.py``` would loop over the regions, producing a figure for each. It would then loop over the datasets (min, mean, and max as one dataset for the model ensemble, plus one dataset for the reanalysis).
- An instance of ```SeasonalCycle``` would be called from ```plotting.py``` for each dataset and region.
- That instance would initalise from ```Loader```, which would find, load, and organise the relavent data. For siconc, this would include areacello as an extra dataset. It would also make and apply a region mask.
- The ```SeasonalCycle``` instance would so all the variable specific processing, like multiplying through by area and summing.
- ```arctic_eval.py``` would use the pre-defined plot function in the ```SeasonalCycle``` instance to add data to the figure, then do the provenance logging and figure saving.

### Running
### Overview of code
### Modifying the code
### Adding a region

## Things to do
- Create, maintain, and load some central environment

