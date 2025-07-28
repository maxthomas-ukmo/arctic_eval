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

The next step is to edit the ```config-user.yml``` file and make paths appropriate for the given user.

There is a run script for each of the recipes. Once the environment is created, a user can get started by
```
cd code
./run_arctic_seaice
```
which loads the environment and runs ```recipe_arctic_seaice.yaml```

---
## Sea-ice evaluation
### Running
### Overview of code
### Modifying the code
### Adding a region

## Things to do
- Create, maintain, and load some central environment

