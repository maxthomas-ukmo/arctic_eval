import matplotlib.pyplot as plt
import logging
import pickle

logger = logging.getLogger(__name__)

from esmvaltool.diag_scripts.shared import run_diagnostic

from plotting import SeasonalCycle, GeoMap, Timeseries

from utils import save_object, get_format_properties
from utils import ProvenanceRecord 

def dummy_plot():
    fig = plt.figure()
    plt.plot([1,2,3],[3,4,5])
    plt.savefig('dummy.png')

def plot_seasonal_cycles(cfg):
    '''Plot seasonal cycle for a list of variables and datasets given in config dictionary from esmvaltool recipe.'''

    # Print input data files
    input_data= cfg['input_data']
    for key in input_data:
        print(key)
        print(input_data[key])
        print('==============================================')

    # Get formatting properties from YAML file
    formatting = get_format_properties()
    
    # Loop over variables
    for variable in cfg['variables_to_plot']:
        # Create figure for one variable
        fig = plt.figure(dpi=300)
        ax = fig.add_subplot(111)
        print('NNNNNNNNNN')

        # Create provenance record for one variable
        provenance_record = ProvenanceRecord()

        # Loop over model datasets
        for dataset in cfg['model_datasets']:
            # Get colour for dataset
            colour = formatting['dataset'][dataset]['colour']
            try:
                # Create seasonal cycle object for dataset and variable
                seasonal_cycle = SeasonalCycle(input_data, dataset, variable, aliases=[dataset+'Mean', dataset+'Min', dataset+'Max'])
                # Plot seasonal cycle to axes for that variable
                print('MMMMMMMMMMMMMMMM')
                seasonal_cycle.plot(ax, line_parameters={'colour': colour})
                # Add ancestors to provenance record
                provenance_record.add_ancestors(seasonal_cycle.provenance_list)
            except:
                logger.warning('No data found for %s %s' % (variable, dataset))

        # Loop over observational datasets
        if cfg['obs_datasets']:
            for dataset in cfg['obs_datasets']:
                # Get colour for dataset
                colour = formatting['dataset'][dataset]['colour']
                try:
                    # Create seasonal cycle object for observational dataset and variable
                    seasonal_cycle = SeasonalCycle(input_data, dataset, variable, aliases=['OBS'])
                    # Plot seasonal cycle to axes for that variable                 
                    seasonal_cycle.plot(ax, line_parameters={'colour': colour})
                    # Add ancestors to provenance record
                    provenance_record.add_ancestors(seasonal_cycle.provenance_list)
                except:
                    logger.warning('No data found for %s %s' % (variable, dataset))
        
        # Save figure to output dir and add it to provenance record
        save_object(fig, variable+'_seasonal_cycle.png', cfg, provenance_record.record)

def plot_geographical_maps(cfg):
    '''Plot geographical map for a list of variables and datasets given in config dictionary from esmvaltool recipe.'''

    # Print input data files
    input_data= cfg['input_data']
    for key in input_data:
        print(key)
        print(input_data[key])
        print('==============================================')

    # Get formatting properties from YAML file
    formatting = get_format_properties()

    # Loop over desired time slices
    for time_slice in cfg['months']:
        # Loop over variables
        for variable in cfg['variables_to_plot']:

            for dataset in cfg['model_datasets']:
                # Create figure for each dataset, variable, and time slice
                fig = plt.figure(dpi=300)

                geo_map = GeoMap(input_data, dataset, variable, aliases=[dataset+'Mean'])

                # Make a new data variable in geo_map.data. In this case we take a monthly slice
                subset = geo_map.get_month_slice(time_slice, statistics='time_mean')

                ax = geo_map.add_map_axes(fig)

                # Plot the subset data
                geo_map.plot(ax, subset)

                # Create provenance record for one variable
                provenance_record = ProvenanceRecord()

                fig_name = variable + '_geographical_map_' + dataset + '_' + subset + '.png'
                # Save figure to output dir and add it to provenance record
                save_object(fig, fig_name, cfg, provenance_record.record)

            for dataset in cfg['obs_datasets']:
                # Create figure for each dataset, variable, and time slice
                fig = plt.figure(dpi=300)

                geo_map = GeoMap(input_data, dataset, variable, aliases=['OBS'])

                # Make a new data variable in geo_map.data. In this case we take a monthly slice
                subset = geo_map.get_month_slice(time_slice, statistics='time_mean')

                ax = geo_map.add_map_axes(fig)

                # Plot the subset data
                geo_map.plot(ax, subset)

                # Create provenance record for one variable
                provenance_record = ProvenanceRecord()

                fig_name = variable + '_geographical_map_' + dataset + '_' + subset + '.png'
                # Save figure to output dir and add it to provenance record
                save_object(fig, fig_name, cfg, provenance_record.record)

def plot_timeseries(cfg):
    '''Plot timeseries for a list of variables and datasets given in config dictionary from esmvaltool recipe.'''
    # Print input data files
    input_data = cfg['input_data']
    for key in input_data:
        print(key)
        print(input_data[key])
        print('==============================================')

    # Get formatting properties from YAML file
    formatting = get_format_properties()

    # Loop over variables
    for variable in cfg['variables_to_plot']:
        # Create figure for one variable
        fig = plt.figure(dpi=300)
        ax = fig.add_subplot(111)

        # Create provenance record for one variable
        provenance_record = ProvenanceRecord()

        # Loop over model datasets
        for dataset in cfg['model_datasets']:
            # Get colour for dataset
            colour = formatting['dataset'][dataset]['colour']
            try:
                # Create timeseries object for dataset and variable
                timeseries = Timeseries(input_data, dataset, variable, aliases=[dataset+'Mean'])
                # Plot timeseries to axes for that variable
                timeseries.plot(ax, line_parameters={'colour': colour})
                # Add ancestors to provenance record
                provenance_record.add_ancestors(timeseries.provenance_list)
            except:
                logger.warning('No data found for %s %s' % (variable, dataset))

        # Loop over observational datasets
        if cfg['obs_datasets']:
            for dataset in cfg['obs_datasets']:
                # Get colour for dataset
                colour = formatting['dataset'][dataset]['colour']
                try:
                    # Create timeseries object for observational dataset and variable
                    timeseries = Timeseries(input_data, dataset, variable, aliases=['OBS'])
                    # Plot timeseries to axes for that variable                 
                    timeseries.plot(ax, line_parameters={'colour': colour})
                    # Add ancestors to provenance record
                    provenance_record.add_ancestors(timeseries.provenance_list)
                except:
                    logger.warning('No data found for %s %s' % (variable, dataset))
        
        # Save figure to output dir and add it to provenance record
        save_object(fig, variable+'_timeseries.png', cfg, provenance_record.record)


def main(cfg):
    ''' Execute the diagnostoc for a given configuration dictionary from esmvaltool recipe.'''

    if cfg['script'] == 'seasonal_cycle':
        plot_seasonal_cycles(cfg)

    if 'geo_map' in cfg['script']:
        plot_geographical_maps(cfg)

    if cfg['script'] == 'timeseries':
        plot_timeseries(cfg)



if __name__ == '__main__':

    with run_diagnostic() as config:
        # Save config
        with open(config['run_dir'] + '/config.pkl', 'wb') as f:
            pickle.dump(config, f)
        # Run diagnostic
        main(config)



