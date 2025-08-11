# Development of Arctic evaluation tools 
# *Author: Max Thomas*
---
## Overview
This repository contains ESMValTool recipes for evaluating climate models with an Arctic focus.

There are three evaulation tools for the Arctic:
- *sea ice*: with a focus on sea-ice data
- *transports*: which uses the StraitFlux package to calculate volume, heat, and salt fluxes through Arctic gateways
- *ocean*: which just updates an existing recipe with centrally stored diagnostic scripts to take HadGEM3 data

## Getting started
First get the public repository.
```
cd
git clone git@github.com:maxthomas-ukmo/arctic_eval.git
```
Installing into ```~``` should mean the recipes work out of the box. 

Then create the required environment.
```
cd arctic_eval
conda create --name arctic_eval --file environment/arctic_eval.lock
```
The *arctic_eval* environment duplicates the Met Office's internal scitools/community/esmvaltool-2.11.0 and adds dependencies for StraitFlux. Activate the environment using 
```conda activate arctic_eval```, or let the run scripts (below) do that for you.

The next step is to edit the ```config/config-user.yml``` file and make paths appropriate for the given user. Out of the box, the paths should just work from the MO providing ```arctic_eval``` is in ```~```.

The easiest way to run a recipe is by running
```./run.sh```. Alternatively, a user can get started by running in a terminal. I reccomend starting with
```
cd code
./run.sh recipe_arctic_seaice
```
which will run ```recipes/recipe_arctic_seaice.yml``` via an ```srun``` command. Memory can be configured at the command line but there's no need for initial testing, as it's generous.

If the recipe runs sucessfully, terminal or log output (```code/recipe_arctic_seaice.log``` by default) should contain a path to the recipe output, like:
```
INFO    Wrote recipe output to:
file://<path/to/recipe output>/index.html
```
Inspect this with ```firefox /<path/to/recipe output>/index.html```.

Recipe output can be archived to ~/public_html/ using
```
./archive_recipe.sh recipe_arctic_<seaice/transport/ocean>_<YYYYMMDD_HHMMSS> <name for archive, like recipe_arctic_seaice-initial_test>
```

---
## Overview
The directory structure is:
```
arctic_eval
├── code
│   ├── archive_recipe.sh
│   ├── diag_scripts
│   │   ├── arctic_eval.py
│   │   ├── arctic_seaice
│   │   ├── __init__.py
│   │   └── StraitFlux
│   ├── plot_formatting.yml
│   ├── readme
│   ├── recipe_arctic_ocean.log
│   ├── recipe_arctic_seaice.log
│   ├── recipe_arctic_transport.log
│   ├── recipes
│   │   ├── recipe_arctic_ocean.yml
│   │   ├── recipe_arctic_seaice.yml
│   │   └── recipe_arctic_transport.yml
│   ├── run_esmvaltool.sh
│   └── run.sh
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
code/recipe_arctic_seaice.yml
code/diag_scripts/arctic_eval.py
code/diag_scripts/utils.py
code/diag_scripts/plotting.py
```

The run script is just loaded the environment and runs the recipe via Spice. The recipe calls ```arctic_eval.py``` several times, and passes a configuration file telling it what to do. 

Each analysis type exists as a class in ```plotting.py```, and typically one instance of a class is made for each dataset in each panel.

Each class in ```plotting.py``` inherits from a the ```Loader``` class in ```utils.py```. The loader finds the netcdfs that ESMValTool has created, loads them to ```iris``` cubes, and does some processing requested by the recipe. 

For example, a seasonal cycle plot of integrated sea-ice area for HadGEM3-GC3.1-LL and HadISST reanalysis, for the Amerasian and Eurasian basins, would go through these steps:
- ```arctic_eval.py``` would loop over the regions, producing a figure object for each. It would then loop over the datasets (min, mean, and max as one dataset for the model ensemble, plus one dataset for the reanalysis).
- An instance of ```SeasonalCycle``` would be called from ```plotting.py``` for each dataset and region.
- That instance would initalise from ```Loader```, which would find, load, and organise the relavent data. For siconc, this would include areacello as an extra dataset. It would also make and apply a region mask.
- The ```SeasonalCycle``` instance would so all the variable specific processing, like multiplying through by area and summing. 
- ```arctic_eval.py``` would use the pre-defined plot function in the ```SeasonalCycle``` instance to add data to the figure, then do the provenance logging and figure saving.

# Transports evaluation
The python is identical for ```recipe_arctic_transport.yml``` (though it may be best to separate transport and sea ice evaluation in future).

The recipe gets *vo*, *uo*, *thetao*, and *so* from a given dataset. Calculation of transports from these is done using the StraitFlux package:
https://github.com/susannawinkelbauer/StraitFlux, as documented here:
https://doi.org/10.5194/gmd-17-4603-2024. 

The volume, heat, and salt transport are calculated as timeseries accross straits defined by name (e.g. 'Fram') in the recipe.

# Ocean evaluation
```recipe_arctic_ocean.yml`` is previously published and its python is stored in the central ESMValTool space at the MO.


## Running
The best way to run the code is
```
./run.sh recipe_arctic_<seaice, transports, ocean>
```
Alternatively, the environment can be loaded and a recipe run using
```
esmvaltool run recipe_arctic_<seaice, transports, ocean>.yml --config_file <path to config-user.yml>
```

## Modifying the code
The formatting of the plots can be defined in ```code/plot_formatting.yml```. This gets read into a dictionary which can be passed through the scripts to define colours etc on plots.

Many things can be changed via the recipe. The regional subsetting, model datasets, observational datasets, variables, and statistics applied by ESMValTool can all be altered here. Some of these will require code alteration in the loading and plotting classed, or in ```arctic_eval.py```, others won't.

To add a new region the ```get_region_indicies``` function in ```utils.py``` must be modified by adding a case with logic based on the required latitude and longitude conditions, and then added to the ```regions``` entry in the recipe files, as desired.

## Things to do
- Create, maintain, and load some central environment
- Define logic to process variable within plotting based on some list of final outputs, rather than input variables. This would allow, e.g., sicon to be passed to SeasonalCycle, and define in the recipe if integrated area or extent was required.
- There's no technical reason to confine this to the Arctic. Either adding Southern Ocean regions or having a ```recipe_southernocean_<seaice, transports, ocean>.yml``` would be easy.

