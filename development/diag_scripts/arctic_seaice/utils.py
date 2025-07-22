import os
import yaml
import datetime

import numpy as np
#import xarray as xr
import iris

from esmvaltool.diag_scripts.shared import ProvenanceLogger

class Loader():
    '''
    Loader class to load data passed by ESMValTool recipe.

    The loader is designed to be inherited by classes that need to load data for plotting or analysis.

    Data are loaded, and subset to a region if specified. Areacello data are also loaded and subset if passed by the recipe.

    Further processing (i.e. multiplying by area) is done in the inheriting class.

    Args:
        input_data (dict): Dictionary containing the input data.
        dataset (str): Dataset name (e.g. HadGEM3-GC31-LL).
        variable (str): Variable name (e.g. siconc).
        aliases (list): List of aliases for the various dataset entries (i.e. ['Mean', 'Min', 'Max']) (default [None]).
        called_by (str): Name of the class that called the loader (default 'SeasonalCycle').
        region (str): Region to subset the data to (default None). If None, we subset to the whole Arctic.

    '''
    def __init__(self, input_data, dataset, variable, aliases=[None], called_by='SeasonalCycle', region=None):
        print('Initialising loader')
        # Read arguments into self
        self.input_data = input_data
        self.variable = variable
        self.dataset = dataset
        self.aliases = aliases
        self.called_by = called_by
        # Add alternate variable name if needed
        self.alternate_variable = self._add_alternate_variable()
        # Get required file names in a useful dict and save a list for provenance logging
        self.input_files, self.provenance_list = self._get_input_file()
        # Load data into self.data
        if not self.input_files is None:
            self._load_data()
            # Update observational data if needed
            self._update_obs_data()
            # Rename variable if needed
            self._rename_variable()
            # Replace OBS alias with dataset name if needed
            self._replace_obs_alias()
        
        # If it has been passed as a file, load areacello data to data['areacello']
        self._get_areacello()
        
        # Make region mask
        self.region = region
        self._make_region_mask()

        # Subset data to region if needed
        if self.region is not None:
            self._subset_data()

        # Print loader summary
        self._print_summary()

    def _print_summary(self):
        '''Print a summary of the loader.'''
        print('Loader summary:')
        print('Called by: %s' % self.called_by)
        print('Dataset: %s' % self.dataset)
        print('Variable: %s' % self.variable)
        print('Aliases: %s' % self.aliases)
        print('Input files: %s' % self.input_files)
        if 'areacello' in self.data:
            print('Areacello data found.')
        else:
            print('No areacello data found.')
        if self.region is not None:
            print('Region: %s' % self.region)
        else:
            print('No region specified.')
        
    def _get_areacello(self):
        '''Load areacello data for the specified dataset if it has been passed.'''
        print('IN _get_areacello')
        try:
            self.data['areacello'] = self._get_area_data()
            self.area = True
        except:
            print('No areacello data found for %s' % self.dataset)
            self.data['areacello'] = None 
            self.area = False
        
    def _get_input_file(self):
        '''
        Get input files for the specified dataset and variable, and return a dictionary of input files and a list of provenance entries.
        
        The input files are selected based on the aliases provided. If no data is found, None is returned. 
        Aliases could be a statistic name (i.e. Mean), OBS to indicate observational data, or some other flag.
        Aliases appear in the filename of the netcdfs produced by valtool.
        '''

        # Find the required files
        raw_input_files = []
        used_aliases = []
        for alias in self.aliases:
            used_aliases.append(alias)
            raw_input_file = select_input_data_entry(self.input_data, self.dataset, self.variable, alias)
            if raw_input_file is not None:
                raw_input_files.append(raw_input_file)
                print('%s: Data found for %s %s %s' % (self.called_by, self.dataset, self.variable, alias))
            else:
                print('%s: No data found for %s %s %s' % (self.called_by, self.dataset, self.variable, alias))

        # If there are no file, flag an error
        if len(raw_input_files) == 0:
            input_files = None
            provenance_list = []
            print('Data Loading Error: _get_input_file returned None')
            print('These were the input_data:')
            print(self.input_data)

        # Else if there is only one file we assume that's the main data
        elif len(raw_input_files) == 1:
            input_files = {'main': {'file': raw_input_files[0], 'alias': used_aliases[0]}}
            provenance_list = raw_input_files

        # Otherwise we store the input files based on their individual aliases
        else:
            input_files = {}
            provenance_list = []
            for raw_input_file, alias in zip(raw_input_files, used_aliases):
                
                if 'Mean' in raw_input_file:
                    input_files['main'] = {'file': raw_input_file, 'alias': alias}
                elif 'Min' in raw_input_file:
                    input_files['min'] = {'file': raw_input_file, 'alias': alias}
                elif 'Max' in raw_input_file:
                    input_files['max'] = {'file': raw_input_file, 'alias': alias}
                else:
                    input_files[alias] = {'file': raw_input_file, 'alias': alias}
               
                provenance_list.append(raw_input_file)

        return input_files, provenance_list
    
    def _get_area_data(self):
        ''' Get areacello data, or not.'''
        for key in self.input_data:
            data = self.input_data[key]
            if data['dataset'] == self.dataset and data['short_name'] == 'areacello':
                area_file = key
        if area_file is None:
            print('No areacello data found for %s' % self.dataset)
            return None
        else:
            # return xr.open_dataset(area_file)['areacello']
            return iris.load_cube(area_file)
        
    def _load_data(self):
        ''' Load data from input files into self.data.
        '''
        if self.input_files is None:
            print('No data found for %s %s' % (self.dataset, self.variable))
            self.plot_type = 'no_data'
        elif len(self.input_files) == 1:
            self.data = {'main': iris.load_cube(self.input_files['main']['file'])}
            print('1234567')
            print(self.data['main'])
            self.plot_type = 'single'
        elif len(self.input_files) == 3:
            self.data = {'main': iris.load_cube(self.input_files['main']['file']),
                         'min': iris.load_cube(self.input_files['min']['file']),
                         'max': iris.load_cube(self.input_files['max']['file'])}
            self.plot_type = 'range'
            print(self.data['main'])
        else:
            print('Use case for more than three files in seasonal cycle not defined')

    
    def _add_alternate_variable(self):
        ''' Add alternate variable name if needed because of incomplete cmorization.'''
        # sicon HadISST is names sic in HadISST
        if self.dataset == 'HadISST' and self.variable == 'siconc':
            return 'sic'
        # PIOMAS is sithick, rather than sivol
        elif self.dataset == 'PIOMAS' and self.variable == 'sivol':
            return 'sithick'
        else:
            return self.variable
        
    def _update_obs_data(self):
        ''' If we need to, update observational data.'''
        if self.dataset == 'PIOMAS':
            # PIOMAS contains thickness data, so multiply by area to get volume
            if self.variable == 'sivol':
                piomas_area_file = select_input_data_entry(self.input_data, 'PIOMAS', 'areacello', 'OBS')
                self.data['area'] = iris.load_cube(piomas_area_file)['areacello']
                self.data['main'] = self.data['main'] * self.data['area']
               
    def _rename_variable(self):
        ''' Rename variable if needed because of incomplete cmorization.'''
        if self.dataset == 'HadISST' and self.variable == 'siconc':
            self.data['main'].rename('siconc')
        if self.dataset == 'PIOMAS' and self.variable == 'sivol':
            self.data['main'].rename('sivol')
        
    def _replace_obs_alias(self):
        ''' Replace OBS alias with dataset name, or do nothing for model dataset.'''
        if self.input_files['main']['alias'] == 'OBS':
            self.input_files['main']['alias'] = self.dataset

    def _make_region_mask(self):
        ''' 
        Make a region mask for the specified region.
        
        The numpy array mask is broadcast to an xarray DataArray with the same dimensions as the data.
        Two versions are needed, one bradcast to time dims and one not (for areacello).
        '''
        # This work is done by a function external to the loader
        region_mask = make_region_mask(self.region, self.data['main'].coord('longitude').points, self.data['main'].coord('latitude').points)

        # Broadcast the region mask to the shape of the data
        region_mask_b = np.broadcast_to(region_mask, self.data['main'].data.shape)

        self.region_mask, self.region_mask_b = region_mask, region_mask_b

    def _subset_data(self):    
        ''' Subset data to the specified region using the region mask.'''
        for ds in ['main', 'min', 'max']:

            try:
                self.data[ds].data = np.ma.masked_where(~self.region_mask_b, self.data[ds].data)
            except:
                print('No %s data found for %s so no mask applied' % (ds, self.dataset))

            # Now try for areacello which needs an unbroadcast mask
            if 'areacello' in self.data:
                try:
                    self.data['areacello'].data = np.ma.masked_where(~self.region_mask, self.data['areacello'].data)
                except:
                    print('No areacello data found for %s so no mask applied' % (self.dataset))


def get_format_properties(plot_formatting='/home/users/max.thomas/projects/esmvaltool/development/plot_formatting.yml', properties=['colour']):
    '''Reads format properties from a YAML file.
    
    Args:
        plot_formats (str): Path to the YAML file containing the format properties (default: 'plot_formatter.yml').
        
    Returns:
        dict: Dictionary containing the format properties.
    '''
    with open(plot_formatting, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)    

def save_object(object_handle, object_name, cfg, record):
    '''Saves an object to a file and logs the provenance record.
    
    Args:
        object_handle (object): Object to save. [[currently only works with figures]]
        object_name (str): Name of the object with suffix (i.e. siconc_seasonal_cycle.png).
        cfg (dict): Configuration dictionary.
        record (dict): Provenance record.
    '''
    object_path = os.path.join(cfg['plot_dir'], object_name)
    object_handle.savefig(object_path)
    with ProvenanceLogger(cfg) as provenance_logger:
        provenance_logger.log(object_path, record)

class ProvenanceRecord():
    '''Class to create a provenance record.
    
    '''
    def __init__(self, caption='dummy caption', region='whole Arctic', authors=['koldunov_nikolay'], references=['contact_authors'], ancestors=[]):
        self.record = {
            'caption': caption,
            'region': region,
            'authors': authors,
            'references': references,
            'ancestors': ancestors
        }
        
    def get_record(self):
        return self.record
    
    def add_ancestors(self, ancestors):
        self.record['ancestors'].extend(ancestors)

def select_file_from_attributes(input_data, attributes):

    for key in input_data:
        data = input_data[key]
        data_found = True
        for attribute in attributes:
            if attributes[attribute] != data[attribute]:
                data_found = False
        if data_found:
            return key
            break
    if not data_found:
        print('No data found with the attributes %s' % attributes)
        return None
    
def get_variables_from_input_data(input_data):
    variables = []

    for key in input_data:
        if not input_data[key]['short_name'] in variables:
            variables.append(input_data[key]['short_name'])

    return variables

def get_datasets_from_input_data(input_data):
    datasets = []

    for key in input_data:
        if not input_data[key]['dataset'] in datasets:
            datasets.append(input_data[key]['dataset'])

    return datasets

def select_input_data_entry(input_data, dataset, variable, alias=None):
    '''Selects the input data entry from the input_data dictionary based on the dataset, variable and (optionally) alias.
    
    TODO: NEEDS UPDATING

    Args:
        input_data (dict): Dictionary containing the input data.
        dataset (str): Dataset name.
        variable (str): Variable name.
        alias (str): Alias modifier (default: None). 
                     If only a single dataset, this should be the statistic name (e.g. MultiModelMean).
                     If multiple datasets, this should be the dataset followed by a short statistic name (e.g. HadGEM3-GC31-LLMean).
        
    Returns:
        str: Key of the input data entry, or None if no entry is found.'''
    
    # dirty fix for HadISST sic, which is not the CMOR name. SeasonalCycle fixes this in the data in __init__
    if dataset == 'HadISST' and variable == 'siconc':
        variable = 'sic'
    elif dataset == 'PIOMAS' and variable == 'sivol':
        variable = 'sithick'

    for key in input_data:
        data = input_data[key]
        if alias is None:
            if data['dataset'] == dataset and data['short_name'] == variable:
                return key
                break
        else:
            if data['dataset'] == dataset and data['short_name'] == variable and data['alias'] == alias:
                return key
                break
    return None

# TODO: update to be consistent with iris
def extract_months_using_datetime(da, months):
    # Extract the month(s) from the xarray data array
    if not isinstance(months, list): # Ensure months is a list
        months = [months]
    return da.where(da.time.dt.month.isin(months), drop=True)

# TODO: update to be consistent with iris
def convert_cftime_to_datetime(cftime_array):
    # Convert cftime to datetime
    date_time_converted = [datetime.datetime(t.year, t.month, t.day) for t in cftime_array]
    return date_time_converted

def get_region_indicies(region, lon2d, lat2d):
    """Define regions for data selection.

    Note, this function is adapted from the ESMValTool recipe_arctic_ocean.

    Parameters
    ----------
    region: str
        the name of the region
    lon2d: 2d numpy array
    lat2d: 2d numpy array

    Returns
    -------
    indexesi: 1d numpy array
        i indexes of the selected points
    indexesj: 1d numpy array
        j indexes of the selected points
    """
    if region == 'EB':
        # Eurasian Basin of the Arctic Ocean
        indi, indj = np.where((lon2d > 300) & (lat2d > 80))
        indi2, indj2 = np.where((lon2d < 100) & (lat2d > 80))
        indi3, indj3 = np.where((lon2d > 100) & (lon2d < 140) & (lat2d > 66))

        indexesi = np.hstack((indi, indi2, indi3))
        indexesj = np.hstack((indj, indj2, indj3))
    elif region == 'AB':
        # Amerasian basin of the Arctic Ocean
        indi, indj = np.where((lon2d >= 260) & (lon2d <= 300) & (lat2d >= 80))
        indi2, indj2 = np.where((lon2d >= 140) & (lon2d < 260) & (lat2d > 66))

        indexesi = np.hstack((indi, indi2))
        indexesj = np.hstack((indj, indj2))
    elif region == 'Barents_sea':

        indi, indj = np.where((lon2d >= 20) & (lon2d <= 55) & (lat2d >= 70)
                              & (lat2d <= 80))

        indexesi = indi
        indexesj = indj
    elif region == 'North_sea':
        # Amerasian basin of the Arctic Ocean
        indi, indj = np.where((lon2d >= 355) & (lon2d <= 360) & (lat2d >= 50)
                              & (lat2d <= 60))
        indi2, indj2 = np.where((lon2d >= 0) & (lon2d <= 10) & (lat2d >= 50)
                                & (lat2d <= 60))

        indexesi = np.hstack((indi, indi2))
        indexesj = np.hstack((indj, indj2))
    else:
        print('Region {} is not recognized'.format(region))
        print('Defaulting to whole Arctic')
        indi, indj = np.where(lat2d >= 60)

        indexesi = indi
        indexesj = indj

    return indexesi, indexesj

def make_region_mask(region, lons, lats):
    print('Making region mask for region: %s' % region)

    # If lons and lats are 1D, we need to meshgrid them
    if len(lons.shape) == 1 and len(lats.shape) == 1:
        print('Making HadISST 2d coords')
        lon2d, lat2d = np.meshgrid(lons, lats)
        print(lon2d)
    elif len(lons.shape) == 2 and len(lats.shape) == 2:
        lon2d, lat2d = lons, lats
    else:
        raise ValueError('lons and lats must be 1D or 2D arrays')

    indexesi, indexesj = get_region_indicies(region, lon2d, lat2d)
    mask = np.zeros_like(lon2d, dtype=bool)
    mask[indexesi, indexesj] = True
    return mask

def get_timerange_from_input_data(input_data, key_index=0):
    key = list(input_data.keys())[key_index]
    timerange = input_data[key]['timerange']
    return timerange

def make_figure_caption(plot_type, yvar_description, region, timerange, model_datasets=None, obs_datasets=None):
    caption = f"{plot_type} of {yvar_description} in {region} region for {timerange} time mean."
    if model_datasets:
        caption += f"\n - Models: {', '.join(model_datasets)}"
    if obs_datasets:
        caption += f"\n - Observations: {', '.join(obs_datasets)}"
    return caption