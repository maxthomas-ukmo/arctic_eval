# An example of adding a variable to the Arctic evaluation tool
## Max Thomas

Currently, the Arctic evaluation tool managed by ```recipe_arctic_seaice.yml``` plots *siconc* (or integrated area), *sithick* (or integrated volume), or *sisnthick*. These variables are derived and plotted for seasonal cycles, timeseries, and geographical maps. This note documents the steps I took to add *sisnthick*, aiming at helping future users add variables.

The steps are detailed cronologically to highlight the troubleshooting.

The below assumes the ```arctic_eval``` repository is functional for the user, and ```recipe_arctic_seaice.yml``` has been run succesfully.

## 1. Get data
*sisnthick* is the thickness of snow averaged over the snow-covered part of the sea ice. to test the recipe I gathered HadGEM3-GC31-LL *sisnthick* data for historical ensemble members using the *manage cmip* tool

```managecmip get --model=HadGEM3-GC31-LL --mip-era=CMIP6 --mip-table=SImon --experiment=historical --ensemble-member=r1i1p1f3 --grid=gn --variable-name=sisnthick```

for r{1:5}.

## 2. Open development environment

Now open the valtool directory and start editing in dev branch
```
cd ~/arctic_eval
git checkout dev
```

You don't need to, but I would strongly recommend working in vscode as git copilot is integrated with it the layout of everything is excellent. To do that you just type 
```code .```, and the gui opens.

## 3. Modify the recipe 
### To make it run fast (optional)
These steps don't need to be done, but it makes everything quicker by drastically reducing the time of one run during testing by removing diagnostics and -MM data.

In ```code/recipes/recipe_arctic_seaice.yml```

Comment out this line: 

```  - {dataset: HadGEM3-GC31-MM, project: CMIP6} ```

Change these lines in seasonal_cycle:

```
model_datasets: [HadGEM3-GC31-LL, HadGEM3-GC31-MM]
```
to 
```
model_datasets: [HadGEM3-GC31-LL]
 ```

Comment out everything after seasonal_cycle (from the Maps section onwards).

### To add sisnthick
In the seasonal_cycle variable definition, add
```
sisnthick:
        <<: *seasonalcycle_var 
```
For speed-up, replace
```
variables_to_plot: [siconc, sivol]
``` 
with
```
variables_to_plot: [sisnthick]
```
or simply add *sisnthick* to the variables_to_plot list.

## 4. Modify the diagnostics
Now, the relevant scripts are 
```
code/diag_scripts/arctic_eval.py
code/diag_scripts/arctic_seaice/plotting.py
code/diag_scripts/arctic_seaice/utils.py
```

```utils.py``` and ```arctic_eval.py``` should only need editing in special cases, like where variable names differ between observations and model output. Other things can crop up too, around units etc.

### Start by modifying plotting.py
In the ```SeasonalCycle``` class, we need to add variable processing steps in the ```__init__``` section, after the line starting *# ADD VARIABLE PROCESSING…*.

We need to decide what we actually want here. We can't sum *sisnthick*, and need to take the mean for the seasonal cycle. We need that mean to be weighted by the gridcell area. 

The functionality for that doesn't exist yet, so we need to implement it. It doesn't go in ```SeasonalCycle```, as it will likely be needed by other classes, so we put it in ```utils.py``` (see later)

For now we can add the processing for *sisnthick* in ```SeasonalCycle```, imagining ```cell_area_weighted_mean``` functionality exists
```
elif self.variable == 'sisnthick':
            self.cell_area_weighted_mean()
            self.yvar_description = 'sea ice thickness [m]'
```

### Add required functionality to utils.py
The new function goes in ```utils.py``` in the ```Loader``` class, because the ```Loader``` class is inherited by all the plotting classes.

After ```def sum_over_area(…``` we add:
```
def cell_area_weighted_mean(self):
        '''
        Calculate the cell area weighted mean of the main variable.
        If min and max exist, perform the same processing for those.
        self.data are updated directly, resulting in units of the original variable.
        '''
        print('Calculating cell area weighted mean of %s.' % self.variable)
        self.data['main'] = self.data['main'].collapsed(['latitude', 'longitude'], iris.analysis.MEAN, weights=self.data['areacello'])
        if 'min' in self.data:
            self.data['min'] = self.data['min'].collapsed(['latitude', 'longitude'], iris.analysis.MEAN, weights=self.data['areacello'])
            self.data['max'] = self.data['max'].collapsed(['latitude', 'longitude'], iris.analysis.MEAN, weights=self.data['areacello'])
```

Note that I just typed 'def cell_area_weighted_mean(' and git copilot autocompleted the function based on previous code in Loader and what it knows about iris. The function had an error (see below), but was a good first guess.

## 5. Try to run and troubleshoot
Make sure all the modified files are saved, and run

```./run.sh recipe_arctic_seaice```

The run failed, so we inspect the log 

```/data/users/max.thomas/esmvaltool/esmvaltool_output/recipe_arctic_seaice_20250905_091251/run/seasonal_cycle/seasonal_cycle/log.txt```

The error is 

``` File "/home/users/max.thomas/arctic_eval/code/diag_scripts/arctic_eval.py", line 238, in plot_seasonal_cycles
    provenance_record.record['caption'] = seasonal_cycle.caption
                                          ^^^^^^^^^^^^^^
UnboundLocalError: cannot access local variable 'seasonal_cycle' where it is not associated with a valu
```

This is an annoying one, because it basically tells you the instance of ```seasonal_cycle``` hasn't been created. 

We can see in the log that data were found:
```
Plotting seasonal cycles for region: Arctic
Initialising loader
SeasonalCycle: Data found for HadGEM3-GC31-LL sisnthick HadGEM3-GC31-LLMean
SeasonalCycle: Data found for HadGEM3-GC31-LL sisnthick HadGEM3-GC31-LLMin
SeasonalCycle: Data found for HadGEM3-GC31-LL sisnthick HadGEM3-GC31-LLMax
surface_snow_thickness / (m)              (month_number: 12; cell index along second
``` 

So that's good. But we also see:
```
__main__,216 No data found for sisnthick HadGEM3-GC31-LL
```

Which tells us that the ```try``` block for creating the ```seasonal_cycle``` instance in ```arctic_eval.py``` failed (I actually updated the error statement here as it's wrong in this case where we found data). Probably this whole try/except block should be rewritten as it's confusing for the loader to fail but still carry on with the script.

It looks like the last print before the error is in the ```cell_area_weighted_mean``` function, which makes sense, so I added a print in there 
```
print('GGGGGGGGGGGGGGGGGGGG')
print(self.data['main'])
print('GGGGGGGGGGGGGGGGGGGG')
```
And ran again

The print statement was never reached, so the error was in the line:
```
self.data['main'] = self.data['main'].collapsed(['lati…
```

I made a jupyter notebook, loaded in the relevant data files
```
data['main'] = iris.load_cube('/data/users/max.thomas/esmvaltool/esmvaltool_output/recipe_arctic_seaice_20250905_093956/preproc/seasonal_cycle/sisnthick/CMIP6_HadGEM3-GC31-LL_historical_HadGEM3-GC31-LLMean_SImon_sisnthick_1979-2001.nc')
data['areacello'] = iris.load_cube('/data/users/max.thomas/esmvaltool/esmvaltool_output/recipe_arctic_seaice_20250905_093956/preproc/seasonal_cycle/areacello/CMIP6_HadGEM3-GC31-LL_Ofx_piControl_r1i1p1f1_areacello_gn.nc')
```

And replicated the error. The issue was with the weights (*areacello*) not having the same shape as the data (which had a *month_number* coord). I added the following code to the function, which broadcasts the shape of the data to the weights.

```
# Broadcast areacello if necessary to get weights of the right shape
if self.data['areacello'].shape != self.data['main'].shape:
    weights = np.broadcast_to(self.data['areacello'].data, self.data['main'].data.shape)
```

Now
```./run.sh recipe_arctic_seaice ``` was successful, producing graphs like this in the index.html.
![alt text](figs/image.png)

## 6. Get the timeseries and maps working
Getting the seasonal cycle to plot is most of the battle.

Next, I added the data processing steps to the Timeseries class in ```plotting.py```. Then I added *sisnthick* to ```timeseries``` and ```maps``` in ```recipe_arctic_seaice.yml```, and commented out references to -MM (as the data don’t exist at MO yet and it takes a long time to run with them anyway).

```./run.sh recipe_arctic_seaice``` then crashed.

The error was to do with the 'mip' field for *sisnthick* being 'OImon'. 

This has cropped up before, and is a useful error to document. The yaml anchor for the ```map_var``` and ```timeseries_var``` was being set with *siconc*, which has an ```additional_dataset``` field for HadISST. That additional dataset is passed by the anchor to *sisnthick*, which then tries to find obs that don't exist. (previously this wasn't an issue as ```additional_dataset``` was being overwritten by other additional datasets).
    
The fix is to define the anchor on a variable with no additional dataset field. I used *sisnthick* in this case.
    
```./run.sh recipe_arctic_seaice``` then works fine, producing timeseries and maps for *sisnthick*. See [recipe output here](figs/recipe_arctic_seaice.pdf).

## 7. Tidying up
I archived the recipe using
```
./archive_recipe.sh recipe_arctic_seaice_20250905_102247 recipe_arctic_seaice-first_sisnthick
```

I added all the HadGEM3-GC31-MM calls back into ```recipe_arctic_seaice.yml```, and started the process of downloading them via manage cmip.

Finally, we need to tidy up. ```Git status``` tells us
```
On branch dev
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   diag_scripts/arctic_eval.py
        modified:   diag_scripts/arctic_seaice/plotting.py
        modified:   diag_scripts/arctic_seaice/utils.py
        modified:   recipes/recipe_arctic_seaice.yml
```

The changes are quite light, with 41 lines added and 6 deleted accross four files.
```
git commit -am "Got snow thickness (sisnthick) working."
git checkout main
git merge dev
```

```
Fast-forward
 code/diag_scripts/arctic_eval.py            |  2 +-
 code/diag_scripts/arctic_seaice/plotting.py |  8 ++++++++
 code/diag_scripts/arctic_seaice/utils.py    | 19 +++++++++++++++++++
 code/recipes/recipe_arctic_seaice.yml       | 18 +++++++++++++-----
 4 files changed, 41 insertions(+), 6 deletions(-)
 ```

And we're finished. All in all it took about 3 hours, but a lot of that was spent adding the new function and debugging. Existing functionality should now cover most variables.




