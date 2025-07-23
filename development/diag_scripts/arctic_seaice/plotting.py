import xarray as xr
import iris
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import numpy as np

import arctic_seaice.utils as utils

from arctic_seaice.utils import Loader

class SeasonalCycle(Loader):
    ''' 
    Load seasonal cycle data from a dataset and variable, if neccesary multiply by area and/or sum, and provide function to plot it.

    Loading and region subsetting is handled by utils.Loader, which this class inherits from.

    Keyword arguments:
    input_data (dict) -- dictionary of input data
    dataset (str) -- dataset name (dataset name from ESGF)
    variable (str) -- variable name (short CMOR name)
    aliases (list) -- list of aliases for the various dataset entries (i.e. ['Mean', 'Min', 'Max']) (default [None])
    region (str) -- region to plot the seasonal cycle for (default None)
    '''
    def __init__(self, input_data, dataset, variable, aliases=[None], region=None):
        ''' Initialise the SeasonalCycle object. '''

        # Initialise from Loader, which assigns attributes and loads the data
        super().__init__(input_data, dataset, variable, aliases, region=region)

        print('SeasonalCycle: __init__: ')
        print('For dataset %s and variable %s' % (self.dataset, self.variable))
        print('With region %s' % self.region)
        print('With aliases for datasets %s' % self.aliases)

        # Add generic seasonal cycle attributes
        self.plot_description = 'Seasonal cycle'
        self.timerange = utils.get_timerange_from_input_data(self.input_data)
   
        # Add variable specific attributes and perform variable specific procesing steps
        # The data passed by the loader should be gridded, 2D, and have been preprocessed into monthly means for each gridcell
        # ----- siconc
        if self.variable == 'siconc':
            self.multiply_by_area()
            self.sum_over_area()
            self.update_units(10**-14) # units after integrating are 10**-2 m2 in the input data. Multiply these by 10**-14 to get Mkm2
            self.yvar_description = 'sum of sea ice area [Mkm^2]'

        # Make caption for the figure
        self.caption = utils.make_figure_caption(self.plot_description, self.yvar_description, self.region, self.timerange)
        print(self.caption)

    def plot(self, ax, line_parameters=None, add_labels=True):
        ''' Plot the seasonal cycle data.
        
        Keyword arguments:
        ax (matplotlib.axes) -- axis object to plot on
        line_parameters (dict) -- dictionary of line parameters (default None)
        add_labels (bool) -- add labels to the plot (default True)
        '''
        print('Plotting: SeasonalCycle: plot: ')
        print(self.plot_type)

        xvar = self.data['main'].coord('month_number').points

        if line_parameters is None:
            colour = 'k'
        else:
            colour = line_parameters['colour']
        if self.plot_type == 'single':
            ax.plot(xvar, self.data['main'].data, colour, label=self.input_files['main']['alias'])
        elif self.plot_type == 'range':
            ax.plot(xvar, self.data['main'].data, '-' + colour, label=self.input_files['main']['alias'])
            ax.fill_between(xvar, self.data['min'].data, self.data['max'].data, color=colour, alpha=0.2)
        elif self.plot_type == 'no_data':
            print('No data found for %s %s' % (self.dataset, self.variable))
        else:
            print('Use case for more than three files in seasonal cycle not defined')

        plt.legend()
        
        if add_labels:
            ax.set_xlabel('Month')
            ax.set_ylabel(self.yvar_description)
            ax.set_xticks(range(1,13))
            ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])

class GeoMap(Loader):
    ''' Load map data from a dataset and variable and provide function to plot it.

    Keyword arguments:
    input_data (dict) -- dictionary of input data
    dataset (str) -- dataset name (dataset name from ESGF)
    variable (str) -- variable name (short CMOR name)
    alias (str) -- alias for the dataset entry (default None)
    map_parameters (dict) -- dictionary of parameters to define map properties (default None)
    '''
    def __init__(self, input_data, dataset, variable, aliases=None, map_parameters=None, region=None):
        # Initialise from SeasonalCycle
        super().__init__(input_data, dataset, variable, aliases, region=region)
        # Add map parameters
        self.map_parameters = map_parameters

    def add_map_axes(self, fig):
        ''' Add map axes to a figure.

        Keyword arguments:
        fig (matplotlib.figure) -- figure object to plot on
        '''
        if self.map_parameters is None:
            self.map_parameters = {'projection': ccrs.NorthPolarStereo(),
                                   'extent': [0, 360, 60, 90],
                                   'coastlines': True,
                                   'gridlines': True}
        
        ax = fig.add_subplot(111, projection=self.map_parameters['projection'])
        ax.set_extent(self.map_parameters['extent'], ccrs.PlateCarree())
        if self.map_parameters['coastlines']:
            ax.coastlines()
        if self.map_parameters['gridlines']:
            ax.gridlines()
        return ax
    
    def get_month_slice(self, time_slice, statistics='time_mean'):
        # Ensure time slice is a list
        if not isinstance(time_slice, list):
            time_slice = [time_slice]

        # Make string of timeslice for variable naming
        time_slice_name = statistics
        for ts in time_slice:
            time_slice_name += str(ts)  
        time_slice_data = utils.extract_months_using_datetime(self.data['main'], time_slice)

        if statistics == 'time_mean':
            self.data[time_slice_name] = time_slice_data.mean(dim='time')

        return time_slice_name
    
    def plot(self, ax, subset='main'):
        '''Plot the map data.
        
        Keyword arguments:
        ax (matplotlib.axes) -- axis object to plot on
        '''
        xr.plot.pcolormesh(self.data[subset], 'lon', 'lat', transform=ccrs.PlateCarree(), cmap='viridis', ax=ax)
        ax.set_title(self.variable + ' ' + self.dataset + ' ' + subset)
        
class Timeseries(Loader):
    ''' Load timeseries data from a dataset and variable and provide function to plot it.

    Keyword arguments:
    input_data (dict) -- dictionary of input data
    dataset (str) -- dataset name (dataset name from ESGF)
    variable (str) -- variable name (short CMOR name)
    aliases (list) -- list of aliases for the various dataset entries (i.e. ['Mean', 'Min', 'Max']) (default [None])
    '''
    def __init__(self, input_data, dataset, variable, aliases=[None], region=None):
        ''' Initialise the Timeseries object. '''
        super().__init__(input_data, dataset, variable, aliases, region=region)
        # TODO: make the following timeseries specific
        # TODO: eventually move the plot class initialisation code to utils as its largely shared accross plots
        print('Timeseries: __init__: ')
        print('For dataset %s and variable %s' % (self.dataset, self.variable))
        print('With region %s' % self.region)
        print('With aliases for datasets %s' % self.aliases)

        # Add generic timeseries attributes
        self.plot_description = 'Timeseries'
        self.timerange = utils.get_timerange_from_input_data(self.input_data)
   
        # Add variable specific attributes and perform variable specific procesing steps
        # The data passed by loader should be gridded, 2D, and have a monthly time dimension
        # ----- siconc
        if self.variable == 'siconc':
            self.multiply_by_area()
            self.sum_over_area()
            self.update_units(10**-14) # units after integrating are 10**-2 m2 in the input data. Multiply these by 10**-14 to get Mkm2
            self.yvar_description = 'sum of sea ice area [Mkm^2]'

        # Make caption for the figure
        self.caption = utils.make_figure_caption(self.plot_description, self.yvar_description, self.region, self.timerange)
        print(self.caption)

        print(self.data['main'].coord('time').points)
        print(type(self.data['main'].coord('time').points))

        # Make time axis
        self._make_timeseries_xaxis()

        


    def _make_timeseries_xaxis(self):
        ''' Make the time variable for plotting.'''
        # if self.dataset == 'HadISST': # HadISST time variable will plot fine
        #     self.plot_time = self.data['main'].coord('time').points
        # elif 'HadGEM' in self.dataset: # HadGEM time variable needs converting
        #     #self.plot_time = utils.convert_cftime_to_datetime(self.data['main'].coords('time').points)
        self.plot_time = self.data['main'].coord('time').units.num2date(self.data['main'].coord('time').points)

    def plot(self, ax, line_parameters=None, add_labels=True):
        ''' Plot the timeseries data.
        
        Keyword arguments:
        ax (matplotlib.axes) -- axis object to plot on
        line_parameters (dict) -- dictionary of line parameters (default None)
        add_labels (bool) -- add labels to the plot (default True)
        '''
        print('Plotting: Timeseries: plot: ')
        print(self.plot_type)

        if line_parameters is None:
            colour = 'k'
        else:
            colour = line_parameters['colour']
        if self.plot_type == 'single':
            print('Plotting Single')
            xvar = [str(t) for t in self.plot_time]
            ax.plot(xvar, self.data['main'].data) #, colour, label=self.input_files['main']['alias'])
            #ax.plot([1,2,3,4,5], self.data['main'].data[:5])
            print('Plotted Single')
        elif self.plot_type == 'range':
            ax.plot(self.plot_time, self.data['main'].data, '-' + colour, label=self.input_files['main']['alias'])
            ax.fill_between(self.plot_time, self.data['min'].data, self.data['max'].data, color=colour, alpha=0.2)
        elif self.plot_type == 'no_data':
            print('No data found for %s %s' % (self.dataset, self.variable))
        else:
            print('Use case for more than three files in timeseries not defined')

        plt.legend()
        
        if add_labels:
            ax.set_xlabel('Time')
            ax.set_ylabel(self.variable)

class StraitFluxPlotter(Loader):
    ''' Load strait flux data from a dataset and variable and provide function to plot it.

    Keyword arguments:
    input_data (dict) -- dictionary of input data
    dataset (str) -- dataset name (dataset name from ESGF)
    variable (str) -- variable name (short CMOR name) - this should be the t grid variable (i.e. 'thetao' or 'so')
    aliases (list) -- list of aliases for the various dataset entries (i.e. ['Mean', 'Min', 'Max']) (default [None])
    '''
    def __init__(self, input_data, dataset, variable, aliases=[None], salinity=False):
        super().__init__(input_data, dataset, variable, aliases)
        # Store salinity flag, which decides if an so file is loaded to via file_s
        self.salinity = salinity
        # Add input files for uo, vo, and thkcello
        self.strait_flux_inputs = self.get_strait_flux_files()
        # Make time axis
        self.make_timeseries_xaxis()
        # Make dict to store eventual transports and crosssections
        self.transports = {}
        self.crosssections = {}
        


    def get_strait_flux_files(self):
        if self.variable in ['thetao', 'so']:
            raw_input_file_T = utils.select_input_data_entry(self.input_data, self.dataset, self.variable)
            raw_input_file_uo = utils.select_input_data_entry(self.input_data, self.dataset, 'uo')
            raw_input_file_vo = utils.select_input_data_entry(self.input_data, self.dataset, 'vo')
            raw_input_file_z = utils.select_input_data_entry(self.input_data, self.dataset, 'thkcello')
            if self.salinity:
                raw_input_file_s = utils.select_input_data_entry(self.input_data, self.dataset, 'so')
                new_inputs = {'t': raw_input_file_T, 'uo': raw_input_file_uo, 'vo': raw_input_file_vo, 'z': raw_input_file_z, 's': raw_input_file_s}
            else:
                new_inputs = {'t': raw_input_file_T, 'uo': raw_input_file_uo, 'vo': raw_input_file_vo, 'z': raw_input_file_z}
        elif self.variable == 'siconc':
            raw_input_file_sic = utils.select_input_data_entry(self.input_data, self.dataset, self.variable)
            raw_input_file_siu = utils.select_input_data_entry(self.input_data, self.dataset, 'siu')
            raw_input_file_siv = utils.select_input_data_entry(self.input_data, self.dataset, 'siv')
            raw_input_file_sit = utils.select_input_data_entry(self.input_data, self.dataset, 'sithick')
            raw_input_file_z = utils.select_input_data_entry(self.input_data, self.dataset, 'thkcello')
            raw_input_file_t = utils.select_input_data_entry(self.input_data, self.dataset, 'thetao')
            new_inputs = {'sic': raw_input_file_sic, 'siu': raw_input_file_siu, 'siv': raw_input_file_siv, 'sit': raw_input_file_sit, 'z': raw_input_file_z, 't': raw_input_file_t}

        return new_inputs
    
    def call_strait_flux_integrated(self, master_function, parameters):
        # Select the correct function based on the product (ice or ocean, with a section for including salinity or not)
        if parameters['product'] == 'ice': # NOT WORKING due to issue with strait flux package
            transport = master_function(product=parameters['product'],
                                    strait=parameters['strait'],
                                    model=parameters['model'],
                                    file_sic=self.strait_flux_inputs['sic'],
                                    file_u=self.strait_flux_inputs['siu'],
                                    file_v=self.strait_flux_inputs['siv'],
                                    file_sit=self.strait_flux_inputs['sit'],
                                    time_start=parameters['time_start'],
                                    time_end=parameters['time_end'],
                                    Arakawa=parameters['Arakawa'],
                                    file_t=self.strait_flux_inputs['t'],
                                    file_z=self.strait_flux_inputs['z'])
        # If product isn't ice it's ocean
        elif parameters['product'] == 'salt': # If salinity is included, we need to pass the salinity file
            transport = master_function(product=parameters['product'],
                                    strait=parameters['strait'],
                                    model=parameters['model'],
                                    file_u=self.strait_flux_inputs['uo'],
                                    file_v=self.strait_flux_inputs['vo'],
                                    file_t=self.strait_flux_inputs['t'],
                                    file_z=self.strait_flux_inputs['z'],
                                    file_s=self.strait_flux_inputs['s'],
                                    time_start=parameters['time_start'],
                                    time_end=parameters['time_end'],
                                    Arakawa=parameters['Arakawa'])
        else: # Otherwise, we just pass the temperature file
            transport = master_function(product=parameters['product'],
                                    strait=parameters['strait'],
                                    model=parameters['model'],
                                    file_u=self.strait_flux_inputs['uo'],
                                    file_v=self.strait_flux_inputs['vo'],
                                    file_t=self.strait_flux_inputs['t'],
                                    file_z=self.strait_flux_inputs['z'],
                                    time_start=parameters['time_start'],
                                    time_end=parameters['time_end'],
                                    Arakawa=parameters['Arakawa'])
            
        # The data are stores in an xarray DS accessible witb the name of the model, but we make a DA for each transport
        self.transports[parameters['product']] = transport[parameters['model']]
        return self.transports[parameters['product']]
    
    def call_strait_flux_cross_uv(self, master_function, parameters):
        uv = master_function(strait=parameters['strait'],
                                    model=parameters['model'],
                                    file_u=self.strait_flux_inputs['uo'],
                                    file_v=self.strait_flux_inputs['vo'],
                                    file_t=self.strait_flux_inputs['t'],
                                    file_z=self.strait_flux_inputs['z'],
                                    time_start=parameters['time_start'],
                                    time_end=parameters['time_end'],
                                    Arakawa=parameters['Arakawa'])
        self.crosssections[parameters['product']] = uv[parameters['product']]
        return self.crosssections[parameters['product']]
    
    def call_strait_flux_cross_TS(self, master_function, parameters):
        if self.salinity:
            T_or_S = master_function(product=parameters['product'],
                                    strait=parameters['strait'],
                                    model=parameters['model'],
                                    file_t=self.strait_flux_inputs['t'],
                                    file_u=self.strait_flux_inputs['uo'],
                                    time_start=parameters['time_start'],
                                    time_end=parameters['time_end'],
                                    file_s=self.strait_flux_inputs['s'])
        else:
            T_or_S = master_function(product=parameters['product'],
                                    strait=parameters['strait'],
                                    model=parameters['model'],
                                    file_t=self.strait_flux_inputs['t'],
                                    file_u=self.strait_flux_inputs['uo'],
                                    time_start=parameters['time_start'],
                                    time_end=parameters['time_end'])

        self.crosssections[parameters['product']] = T_or_S[parameters['product']]
        return self.crosssections[parameters['product']]
    
    def make_params(self, product='heat', strait='Fram', model='HadGEM3-GC31-LL', time_start='1979-01', time_end='1981-12', Arakawa='Arakawa-C'):
        return {'product': product,
                'strait': strait,
                'model': model,
                'time_start': time_start,
                'time_end': time_end,
                'Arakawa': Arakawa}
    
    def correct_units(self, transports):
        self.units = {'heat': 'W', 'volume': 'm^3', 'salt': 'g/kg'}
        for transport in transports:
            if transport == 'volume':
                self.transports[transport] = self.transports[transport] / 1e6
                self.units[transport] = 'Sv'
            elif transport == 'heat':
                self.transports[transport] = self.transports[transport] / 1e12
                self.units[transport] = 'TW'
    
    def plot_timeseries(self, ax, transport, line_parameters=None, add_x_labels=True, add_y_labels=True, label=None):
        
        if line_parameters is None:
            colour = 'k'
        else:
            colour = line_parameters['colour']
        
        ax.plot(self.plot_time, self.transports[transport], colour, label=label)
        
        if add_x_labels:
            ax.set_xlabel('Time')
        else:
            ax.set_xticklabels([])

        if add_y_labels:
            ax.set_ylabel(transport +' / ' + self.units[transport])

    def plot_crosssection(self, ax, crosssection, line_parameters=None, add_x_labels=True, add_y_labels=True, label=None):
            
        if line_parameters is None:
            colour = 'k'
        else:
            colour = line_parameters['colour']

        data = self.crosssections[crosssection]
        
        a = ax.contourf(data.x, data.depth, data.mean(dim='time'))

        ax.invert_yaxis()

        plt.colorbar(a, ax=ax)

        if add_x_labels:
            ax.set_xlabel('Cross-section')
        else:
            ax.set_xticklabels([])

        if add_y_labels:
            ax.set_ylabel('depth / z')
    
class RegionPlotter(Loader):
    ''' Calculate region masks from a dataset and allow plotting as a QC figure. We only need to do this once per model.

    Keyword arguments:
    input_data (dict) -- dictionary of input data
    dataset (str) -- dataset name (dataset name from ESGF)
    variable (str) -- variable name (short CMOR name)
    aliases (list) -- list of aliases for the various dataset entries (i.e. ['Mean', 'Min', 'Max']) (default [None])
    '''
    def __init__(self, input_data, dataset, variable, regions, region_centers, aliases=[None], map_parameters=None):
        super().__init__(input_data, dataset, variable, aliases)
        self.lon2d = self.data['main'].lon
        self.lat2d = self.data['main'].lat
        self.map_parameters = map_parameters
        self.regions = regions
        self.region_centers = region_centers
        self.masks = self.make_region_masks()

    # TODO: move add_map_axes out of class so it can be called here and in geomap without repitition
    def add_map_axes(self, fig):
        ''' Add map axes to a figure.

        Keyword arguments:
        fig (matplotlib.figure) -- figure object to plot on
        '''
        if self.map_parameters is None:
            self.map_parameters = {'projection': ccrs.NorthPolarStereo(),
                                   'extent': [0, 360, 60, 90],
                                   'coastlines': True,
                                   'gridlines': True}
        
        ax = fig.add_subplot(111, projection=self.map_parameters['projection'])
        ax.set_extent(self.map_parameters['extent'], ccrs.PlateCarree())
        if self.map_parameters['coastlines']:
            ax.coastlines()
        if self.map_parameters['gridlines']:
            ax.gridlines()
        return ax
    

    def make_region_masks(self):
        ''' Make region masks for the regions defined in the input data.'''
        masks = {}
        for region in self.regions:
            masks[region] = utils.make_region_mask(region, self.lon2d, self.lat2d) # boolean array with similar shape to nav_lat/lon
        return masks

    def plot_one_region(self, ax, region, color, alpha=0.5, vmin=0, vmax=1, transform=ccrs.PlateCarree()):
        mask = self.masks[region] # 2D array of 1s and 0s for the region mask
        plot_mask = np.ma.masked_where(mask == 0, mask) # Mask the region
        ax.pcolormesh(self.lon2d, self.lat2d, plot_mask * color, alpha=alpha, vmin=vmin, vmax=vmax, transform=transform)
    
    def plot_all_regions(self, ax, alpha=0.5, vmin=0, vmax=1, transform=ccrs.PlateCarree()):
        n_regions = len(self.regions)
        for i, region in enumerate(self.regions):
            color = 0 + i / n_regions
            self.plot_one_region(ax, region, color, alpha=alpha, vmin=vmin, vmax=vmax, transform=transform)
            # TODO: add label to each region center
            centers = self.region_centers[i]
            lat, lon = centers[0], centers[1]
            self.label_region_center(ax, lon, lat, region)

    def label_region_center(self, ax, lon, lat, text, fontsize=10):
        ''' Label a region center on the map. '''
        ax.text(lon, lat, text, 
                fontsize=fontsize, transform=ccrs.PlateCarree(), ha='center', va='center', color='black', 
                bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))
        
    def apply_mask_to_data(self, dataloader, region):
        pass



    
    