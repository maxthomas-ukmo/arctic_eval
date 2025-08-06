import matplotlib.pyplot as plt
import logging
import pickle

logger = logging.getLogger(__name__)

from esmvaltool.diag_scripts.shared import run_diagnostic

from arctic_seaice.plotting import SeasonalCycle, GeoMap, Timeseries, StraitFluxPlotter, RegionPlotter

from arctic_seaice.utils import save_object, get_format_properties
from arctic_seaice.utils import ProvenanceRecord 

from StraitFlux import masterscript_line as sf_line
from StraitFlux import masterscript_cross as sf_cross


def dummy_plot():
    fig = plt.figure()
    plt.plot([1,2,3],[3,4,5])
    plt.savefig('dummy.png')

def plot_ocean_strait_flux_timeseries(cfg):
    print('SF timeseries')
    input_data= cfg['input_data']
    for key in input_data:
        print(key)
        print(input_data[key])

    formatting = get_format_properties()

    compiled_data = {}
    for model in cfg['model_datasets']:
        compiled_data[model] = {}
        for strait in cfg['strait']:
            compiled_data[model][strait] = []

    for strait in cfg['strait']:
        # Loop over model datasets
        for model in cfg['model_datasets']:
            # Create figure for each strait and model. This fig will also show the strait indicies
            fig = plt.figure(dpi=300, figsize=(10,15))
            # One panel for each variable, plus an extra to take the strait indicies plot
            gs = fig.add_gridspec(4, 1)
            ax1 = fig.add_subplot(gs[0, 0])
            ax2 = fig.add_subplot(gs[1, 0])
            ax3 = fig.add_subplot(gs[2, 0])
            ax4 = fig.add_subplot(gs[3, 0]) # this is just a dummy axis otherwise the auto-generated map get put ontop of a timeseries
            
            color = formatting['dataset'][model]['colour']

            # Load in data for primary variable (salinity flag true to search for a so file path too)
            sf_loader = StraitFluxPlotter(input_data, model, 'thetao')

            # Make provenance record
            provenance_record = ProvenanceRecord()

            # Calculate transported heat 
            #sf_params = sf_loader.make_params(product='ice', Arakawa='Arakawa-B')
            sf_params = sf_loader.make_params(product='heat', strait=strait, model=model)
            heat_transport = sf_loader.call_strait_flux_integrated(sf_line.transports, sf_params)
            # Calculate transported salt
            sf_params['product'] = 'salt'
            salt_transport = sf_loader.call_strait_flux_integrated(sf_line.transports, sf_params)

            # Calculate transported volume
            sf_params['product'] = 'volume'
            volume_transport = sf_loader.call_strait_flux_integrated(sf_line.transports, sf_params)
            # Correct units
            sf_loader.correct_units(['volume','heat'])

            # Add ancestors to provenance record
            provenance_record.add_ancestors(sf_loader.provenance_list)

            # Plot transports
            sf_loader.plot_timeseries(ax1, 'volume', label='Volume transport', color=color, add_x_labels=False)
            sf_loader.plot_timeseries(ax2, 'heat', label='Heat transport', color=color, add_x_labels=False)
            sf_loader.plot_timeseries(ax3, 'salt', label='Salt transport', color=color, add_x_labels=True)

            # Add data to compiled data
            compiled_data[model][strait] = sf_loader


            # Save figure to output dir and add it to provenance record
            #ax3.set_title('Map of strait indicies')
            fig.suptitle('Timeseries of fluxes throug ' + strait + ' strait for ' + model)
            fig.tight_layout()
            save_object(fig, strait + '_' + model + '_transports_timeseries.png', cfg, provenance_record.record)

    # ================================================
    # Add figure for each strait with multiple models

    for strait in cfg['strait']:
        # Create figure for each strait and model. This fig will also show the strait indicies
        fig = plt.figure(dpi=300, figsize=(10,15))
        # One panel for each variable
        gs = fig.add_gridspec(4, 1)
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[1, 0])
        ax3 = fig.add_subplot(gs[2, 0])


        for model in cfg['model_datasets']:
            color = formatting['dataset'][model]['colour']
            # Plot volume transport for each model and strait
            sf_loader = compiled_data[model][strait]
            sf_loader.plot_timeseries(ax1, 'volume', label=model + ' volume transport', color=color, add_x_labels=False)
            sf_loader.plot_timeseries(ax2, 'heat', label=model + ' heat transport', color=color, add_x_labels=False)
            sf_loader.plot_timeseries(ax3, 'salt', label=model + ' salt transport', color=color, add_x_labels=True)

            provenance_record = ProvenanceRecord()
            # Add ancestors to provenance record
            provenance_record.add_ancestors(sf_loader.provenance_list)
        
        fig.suptitle('Timeseries of fluxes throug ' + strait + ' strait')
        fig.tight_layout()
        save_object(fig, strait + '_transports_timeseries.png', cfg, provenance_record.record)


def plot_ocean_strait_flux_crosssection(cfg):
    print('SF crosssection')
    input_data= cfg['input_data']
    for key in input_data:
        print(key)
        print(input_data[key])

    for strait in cfg['strait']:
        # Loop over model datasets
        for model in cfg['model_datasets']:
            # Create figure for each strait and model
            fig = plt.figure(dpi=300, figsize=(5,10))
            # One panel for each variable
            gs = fig.add_gridspec(4, 1)
            ax1 = fig.add_subplot(gs[0, 0])
            ax2 = fig.add_subplot(gs[1, 0])
            ax3 = fig.add_subplot(gs[2, 0])


            # Load in data for primary variable (salinity flag true to search for a so file path too)
            sf_loader = StraitFluxPlotter(input_data, model, 'thetao')

            # Make provenance record
            provenance_record = ProvenanceRecord()

            # Calculate transported volume 
            sf_params = sf_loader.make_params(strait=strait, model=model, time_start=cfg['time_start'], time_end=cfg['time_end'], depth=cfg['strait_depths'][strait])
            

            # Calculate temperature crosssection
            sf_params['product'] = 'T'
            T_cross = sf_loader.call_strait_flux_cross_TS(sf_cross.TS_interp, sf_params)

            sf_params['product'] = 'S'
            S_cross = sf_loader.call_strait_flux_cross_TS(sf_cross.TS_interp, sf_params)
            # Correct units
            # sf_loader.correct_units(['volume','heat'])

            sf_params['product'] = 'uv'
            uv_cross = sf_loader.call_strait_flux_cross_uv(sf_cross.vel_projection, sf_params)

            # Add ancestors to provenance record
            provenance_record.add_ancestors(sf_loader.provenance_list)

            # Plot transports
            sf_loader.plot_crosssection(ax1, 'uv', label='Volume transport', depth=sf_params['depth'], cmap=cfg['product_cmaps']['volume'], add_x_labels=False)
            sf_loader.plot_crosssection(ax2, 'T', label='Heat transport', depth=sf_params['depth'], cmap=cfg['product_cmaps']['heat'], add_x_labels=False)
            sf_loader.plot_crosssection(ax3, 'S', label='Salt transport', depth=sf_params['depth'], cmap=cfg['product_cmaps']['salt'], add_x_labels=True)

            # Save figure to output dir and add it to provenance record
            fig.suptitle(model + ' - ' + strait)
            fig.tight_layout()
            save_object(fig, strait + '_' + model + '_cross.png', cfg, provenance_record.record)

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

    # Get regions to plot
    regions = cfg['regions']
    if not regions:
        regions = ['Arctic']

    # Loop over regions
    for region in regions:
        print('Plotting seasonal cycles for region: %s' % region)

        # Loop over variables
        for variable in cfg['variables_to_plot']:
            # Create figure for one variable
            fig = plt.figure(dpi=300)
            ax = fig.add_subplot(111)

            # Create provenance record for one variable
            provenance_record = ProvenanceRecord(region=region)

            # Loop over model datasets
            for dataset in cfg['model_datasets']:
                # Get colour for dataset
                colour = formatting['dataset'][dataset]['colour']
                try:
                    # Create seasonal cycle object for dataset and variable
                    seasonal_cycle = SeasonalCycle(input_data, dataset, variable, aliases=[dataset+'Mean', dataset+'Min', dataset+'Max'], region=region)
                    # Plot seasonal cycle to axes for that variable
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
                        seasonal_cycle = SeasonalCycle(input_data, dataset, variable, aliases=['OBS'], region=region)
                        # Plot seasonal cycle to axes for that variable                 
                        seasonal_cycle.plot(ax, line_parameters={'colour': colour})
                        # Add ancestors to provenance record
                        provenance_record.add_ancestors(seasonal_cycle.provenance_list)
                    except:
                        logger.warning('No data found for %s %s' % (variable, dataset))
                        for key in input_data:
                            print(input_data[key])
            
            provenance_record.record['caption'] = seasonal_cycle.caption
            # Save figure to output dir and add it to provenance record
            save_object(fig, variable + '_' + region + '_seasonal_cycle.png', cfg, provenance_record.record)

def plot_geographical_maps(cfg):
    '''Plot geographical map for a list of variables and datasets given in config dictionary from esmvaltool recipe.'''

    print('Making Geographical Maps')
    print('maps------------------------------->')
    # Print input data files
    input_data= cfg['input_data']
    for key in input_data:
        print(key)
        print(input_data[key])
        print('==============================================')

    # Get formatting properties from YAML file
    formatting = get_format_properties()

    # Get regions to plot
    # Regions would only be useful here if we want zooms or Antarctic and Arctic
    regions = cfg['regions']
    if not regions:
        regions = ['Arctic']

    for region in regions:
        
        # Loop over variables
        for variable in cfg['variables_to_plot']:

            for dataset in cfg['model_datasets']:
                # Create figure for each region, dataset, and variable
                fig = plt.figure(dpi=300)
                # Add gridspec for the figure
                gs = fig.add_gridspec(nrows=1, ncols=len(cfg['months']))

                # Loop over desired time slices
                for igs, time_slice in enumerate(cfg['months']):
                
                    geo_map = GeoMap(input_data, dataset, variable, aliases=[dataset+'Mean'], region=region)

                    # Make a new data variable in geo_map.data. In this case we take a monthly slice
                    subset = geo_map.get_month_slice(time_slice, statistics='time_mean')

                    ax = geo_map.add_map_axes(fig, gs[0, igs])

                    # Plot the subset data
                    geo_map.plot(ax, subset)

                    # Create provenance record for one variable
                    provenance_record = ProvenanceRecord(region=region, caption=geo_map.caption)

                fig_name = variable + '_' + region + '_geographical_map_' + dataset + '.png'
                # Save figure to output dir and add it to provenance record
                save_object(fig, fig_name, cfg, provenance_record.record)

            # If the variable has been specified to plot an observational dataset, we plot that here
            if variable in cfg['variables_to_plot_obs']:
                obs_dataset = cfg['obs_datasets'][variable]
                # Create figure for each region, dataset, and variable
                fig = plt.figure(dpi=300)
                # Add gridspec for the figure
                gs = fig.add_gridspec(nrows=1, ncols=len(cfg['months']))

                # Loop over desired time slices
                for igs, time_slice in enumerate(cfg['months']):
                    
                    # We try passing two aliases here to make things more general
                    # If there is only one OBS dataset, it gets passed as 'OBS' by valtool, but if there are more they get passed as OBS_<dataset>
                    try:
                        geo_map = GeoMap(input_data, obs_dataset, variable, aliases=['OBS'], region=region)
                    except:
                        print('Trying with alias OBS_' + obs_dataset)
                        geo_map = GeoMap(input_data, obs_dataset, variable, aliases=['OBS_' + obs_dataset], region=region)

                    # Make a new data variable in geo_map.data. In this case we take a monthly slice
                    subset = geo_map.get_month_slice(time_slice, statistics='time_mean')

                    ax = geo_map.add_map_axes(fig, gs[0, igs])

                    # Plot the subset data
                    geo_map.plot(ax, subset)

                # Create provenance record for the obs dataset
                provenance_record = ProvenanceRecord(region=region, caption=geo_map.caption)

                fig_name = variable + '_' + region + '_geographical_map_' + obs_dataset + '.png'
                # Save figure to output dir and add it to provenance record
                save_object(fig, fig_name, cfg, provenance_record.record)

        # TODO: replace obs looping with targeted obs plotting
        # for dataset in cfg['obs_datasets']:
        #     # Create figure for each dataset and variable,
        #     fig = plt.figure(dpi=300)
        #     # Add gridspec for the figure
        #     gs = fig.add_gridspec(nrows=1, ncols=len(cfg['months']))

        #     for igs, time_slice in enumerate(cfg['months']):
        #         geo_map = GeoMap(input_data, dataset, variable, aliases=['OBS'], region=region)

        #         # Make a new data variable in geo_map.data. In this case we take a monthly slice
        #         subset = geo_map.get_month_slice(time_slice, statistics='time_mean')

        #         ax = geo_map.add_map_axes(fig, gs[0, igs])

        #         # Plot the subset data
        #         geo_map.plot(ax, subset)

        #         # Create provenance record for one variable
        #         provenance_record = ProvenanceRecord(region=region, caption=geo_map.caption)

        #     fig_name = variable + '_' + region + '_geographical_map_' + dataset + '.png'
        #     # Save figure to output dir and add it to provenance record
        #     save_object(fig, fig_name, cfg, provenance_record.record)

    print('Geographical Maps done')
    print('<-----------------------------------')

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

    # Get regions to plot
    regions = cfg['regions']
    if not regions:
        region = ['Arctic']
    
    # Loop over regions
    for region in regions:
        print('Plotting seasonal cycles for region: %s' % region)

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
                    timeseries = Timeseries(input_data, dataset, variable, aliases=[dataset+'Mean'], region=region)
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
                        timeseries = Timeseries(input_data, dataset, variable, aliases=['OBS'], region=region)
                        # Plot timeseries to axes for that variable                 
                        timeseries.plot(ax, line_parameters={'colour': colour})
                        # Add ancestors to provenance record
                        provenance_record.add_ancestors(timeseries.provenance_list)
                    except:
                        logger.warning('No data found for %s %s' % (variable, dataset))
            
            provenance_record.record['caption'] = timeseries.caption
            # Save figure to output dir and add it to provenance record
            save_object(fig, variable + '_' + region + '_timeseries.png', cfg, provenance_record.record)

def plot_regions(cfg):
    # For each model, plot one axes with all regions
    # Print input data files
    input_data = cfg['input_data']
    for key in input_data:
        print(key)
        print(input_data[key])
        print('==============================================')

    # for imodel, model in enumerate(models):
    for dataset in cfg['model_datasets']:
        fig = plt.figure(dpi=300)
        # create a provenance record for the regions fig
        provenance_record = ProvenanceRecord()

        region_plotter = RegionPlotter(input_data, dataset, 'siconc', cfg['regions'], cfg['region_centers'])
        ax = region_plotter.add_map_axes(fig)
        region_plotter.plot_all_regions(ax)

        # Add caption to provenance record
        provenance_record.record['caption'] = region_plotter.caption
        # Save figure to output dir and add it to provenance record
        save_object(fig, dataset +'_regions.png', cfg, provenance_record.record)

    for dataset in cfg['obs_datasets']:
        fig = plt.figure(dpi=300)
        # create a provenance record for the regions fig
        provenance_record = ProvenanceRecord()

        region_plotter = RegionPlotter(input_data, dataset, 'siconc', cfg['regions'], cfg['region_centers'])
        ax = region_plotter.add_map_axes(fig)
        region_plotter.plot_all_regions(ax)

        # Add caption to provenance record
        provenance_record.record['caption'] = region_plotter.caption
        # Save figure to output dir and add it to provenance record
        save_object(fig, dataset +'_regions.png', cfg, provenance_record.record)


def main(cfg):
    ''' Execute the diagnostoc for a given configuration dictionary from esmvaltool recipe.'''

    if cfg['script'] == 'seasonal_cycle':
        plot_seasonal_cycles(cfg)

    if 'geo_map' in cfg['script']:
        plot_geographical_maps(cfg)

    if cfg['script'] == 'timeseries':
        plot_timeseries(cfg)

    if cfg['script'] == 'strait_flux':
        if 'timeseries' in cfg['plot_type']:
            plot_ocean_strait_flux_timeseries(cfg)
        if 'crosssection' in cfg['plot_type']:
            plot_ocean_strait_flux_crosssection(cfg)

    if cfg['script'] == 'regions':
        plot_regions(cfg)


if __name__ == '__main__':

    with run_diagnostic() as config:
        # Save config
        with open(config['run_dir'] + '/config.pkl', 'wb') as f:
            pickle.dump(config, f)
        # Run diagnostic
        main(config)



