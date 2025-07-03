import os
import yaml
import datetime

import numpy as np
import xarray as xr

from esmvaltool.diag_scripts.shared import ProvenanceLogger

class Loader():
    ''' Load data from preprocessed esmvaltool .nc files.

    Keyword arguments:
    input_data (dict) -- dictionary of input data
    dataset (str) -- dataset name (dataset name from ESGF)
    variable (str) -- variable name (short CMOR name)
    aliases (list) -- list of aliases for the various dataset entries (i.e. ['Mean', 'Min', 'Max']) (default [None])
    '''
    def __init__(self, input_data, dataset, variable, aliases=[None], debug_string='SeasonalCycle'):
        # Read arguments into self
        self.input_data = input_data
        self.variable = variable
        self.dataset = dataset
        self.aliases = aliases
        self.debug_string = debug_string
        # Add alternate variable name if needed
        self.alternate_variable = self.add_alternate_variable()
        # Get required file names in a useful dict and save a list for provenance logging
        self.input_files, self.provenance_list = self.get_input_files()
        # Load data into self.data
        if not self.input_files is None:
            self.load_data()
            # Update observational data if needed
            self.update_obs_data()
            # Rename variable if needed
            self.rename_variable()
            # Replace OBS alias with dataset name if needed
            self.replace_obs_alias()

    def get_input_files(self):
        raw_input_files = []
        used_aliases = []
        for alias in self.aliases:
            used_aliases.append(alias)
            raw_input_file = select_input_data_entry(self.input_data, self.dataset, self.variable, alias)
            if raw_input_file is not None:
                raw_input_files.append(raw_input_file)
                print('%s: Data found for %s %s %s' % (self.debug_string, self.dataset, self.variable, alias))
            else:
                print('%s: No data found for %s %s %s' % (self.debug_string, self.dataset, self.variable, alias))

        if len(raw_input_files) == 0:
            input_files = None
            provenance_list = []
            print('Data Loading Error: get_input_files returned None')
            print('These were the input_data:')
            print(self.input_data)
        elif len(raw_input_files) == 1:
            input_files = {'main': {'file': raw_input_files[0], 'alias': used_aliases[0]}}
            provenance_list = raw_input_files
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
        
    def load_data(self):
        ''' Load data from input files into self.data.
        '''
        if self.input_files is None:
            print('No data found for %s %s' % (self.dataset, self.variable))
            self.plot_type = 'no_data'
        elif len(self.input_files) == 1:
            self.data = {'main': xr.open_dataset(self.input_files['main']['file'])[self.alternate_variable]}
            self.plot_type = 'single'
        elif len(self.input_files) == 3:
            self.data = {'main': xr.open_dataset(self.input_files['main']['file'])[self.variable],
                         'min': xr.open_dataset(self.input_files['min']['file'])[self.variable],
                         'max': xr.open_dataset(self.input_files['max']['file'])[self.variable]}
            self.plot_type = 'range'
            print(self.data['main'])
        else:
            print('Use case for more than three files in seasonal cycle not defined')

    
    def add_alternate_variable(self):
        ''' Add alternate variable name if needed because of incomplete cmorization.'''
        # sicon HadISST is names sic in HadISST
        if self.dataset == 'HadISST' and self.variable == 'siconc':
            return 'sic'
        # PIOMAS is sithick, rather than sivol
        elif self.dataset == 'PIOMAS' and self.variable == 'sivol':
            return 'sithick'
        else:
            return self.variable
        
    def update_obs_data(self):
        ''' If we need to, update observational data.'''
        if self.dataset == 'PIOMAS':
            # PIOMAS contains thickness data, so multiply by area to get volume
            if self.variable == 'sivol':
                piomas_area_file = select_input_data_entry(self.input_data, 'PIOMAS', 'areacello', 'OBS')
                self.data['area'] = xr.open_dataset(piomas_area_file)['areacello']
                self.data['main'] = self.data['main'] * self.data['area']
        
        
    def rename_variable(self):
        ''' Rename variable if needed because of incomplete cmorization.'''
        if self.dataset == 'HadISST' and self.variable == 'siconc':
            self.data['main'] = self.data['main'].rename('sic') # I think this should rename to siconc
        if self.dataset == 'PIOMAS' and self.variable == 'sivol':
            self.data['main'] = self.data['main'].rename('sivol')
        
    def replace_obs_alias(self):
        ''' Replace OBS alias with dataset name, or do nothing for model dataset.'''
        if self.input_files['main']['alias'] == 'OBS':
            self.input_files['main']['alias'] = self.dataset

    def make_timeseries_xaxis(self):
        if self.dataset == 'HadISST': # HadISST time variable will plot fine
            self.plot_time = self.data['main']['time'].values
        elif 'HadGEM' in self.dataset: # HadGEM time variable needs converting
            self.plot_time = convert_cftime_to_datetime(self.data['main']['time'].values)

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
    
    NEEDS UPDATING

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

def extract_months_using_datetime(da, months):
    # Extract the month(s) from the xarray data array
    if not isinstance(months, list): # Ensure months is a list
        months = [months]
    return da.where(da.time.dt.month.isin(months), drop=True)

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
    return indexesi, indexesj

def make_region_mask(region, lon2d, lat2d):
    ii, ij = get_region_indicies(region, lon2d, lat2d)
    mask = np.zeros_like(lon2d, dtype=bool)
    mask[ii, ij] = True
    return mask 
