
from pm4py.objects.log.importer.xes import importer as xes_importer
import pm4py.objects.conversion.log
from pm4py.objects.conversion.log import converter
from pm4py.objects.log.util import dataframe_utils
from pathlib import Path
import pandas as pd
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
from jupyterthemes import jtplot
jtplot.style(theme='oceans16', fscale=2.); sns.set_palette('seismic_r', 3);
import matplotlib.pyplot as plt
from IPython.display import display_html
import sys
import re
from warnings import filterwarnings; filterwarnings('ignore');  # has to 

data_path = Path('../data/')
DD = 'domestic declarations'
ID = 'international declarations'
PT = 'prepaid travel costs'
RP = 'request for payment'
TP = 'travel permitions'

names = [DD, ID, PT, RP, TP]
datasets = [data_path / x for x in names]  


'''further funcs supposed to be class methods in future versions'''


def display_inline(*args, start=0, stop=10):
    html_str=''
    for df in args:
        df = df.iloc[start:stop]
        html_str+=df.to_html()
    display_html(html_str.replace('table','table style="display:inline"'), raw=True)

def atoi_like(s, option='first'):
    """parser of ANY numeric data from str ones; output is in str format"""
    
    try:
        num_str = s.strip()
        num_str = re.findall(r"[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", num_str)
        if option == 'all': return num_str 
        else: return int(num_str[0])  # functional can be upgraded later
    except (IndexError, TypeError, ValueError, AttributeError): return s
    
    
def mem_usage(pandas_obj):
    if isinstance(pandas_obj,pd.DataFrame):
        usage_b = pandas_obj.memory_usage(deep=True).sum()
    else: # we assume if not a df it's a series
        usage_b = pandas_obj.memory_usage(deep=True)
    usage_mb = usage_b / 1024 ** 2 # convert bytes to megabytes
    return "{:03.2f} MB".format(usage_mb)
    
    
def readme_logs():
    """the same as xes_event_logs for readme files; saves in var desc"""
    try:
        data = globals()['desc']
    except KeyError:
        data = dict()
        for _dir in datasets:
            for dataset in _dir.iterdir():
                readme = open(str(dataset))
                data[str(_dir.relative_to(data_path))] = readme.read() if\
                    str(dataset).endswith('txt') else data.get(str(_dir.relative_to(data_path)));
                readme.close()

    return data
    
    
def xes_event_logs():  # !TODO  modify inprogress widget desc
    """pulls .xes files from dirs and saves to pm4py Event_log; saves in var logs"""
    
    try:
        data = globals()['logs']
    except KeyError:
        data = dict()
        for _dir in datasets:
            for dataset in _dir.iterdir():
                data[str(_dir.relative_to(data_path))] = xes_importer.apply(str(dataset)) if\
                    str(dataset).endswith('xes') else data.get(str(_dir.relative_to(data_path)));
    
    return data


def xes2dataframe(xes_file, configuration, sortby, dt_ops, year_period):  # needs to be simpler one
    """represents .xes file as pandas dataframe with opportunity of exporting options choice;
    implemented for performance achievment either;  
    it's not recommended to use 'sortby' option with 'default' mode;
    does job from scratch"""
    
    variant = converter.Variants.TO_DATA_FRAME
    params = {variant.value.Parameters.DEEP_COPY: True}  # can be reconsidered
    print(f'converting event log {xes_file} to dataframe')
    try:
        xes_file = globals()['logs'][xes_file]
    except KeyError:
        print('accesing ".xes" data failed. xes_event_logs must be invoked')
        return
    
    dataframe = converter.apply(xes_file,\
                variant=variant, parameters=params)  # just conversion
    
    '''tuning section start'''
    if configuration == 'convenient':
        print('applying cosmetic changes')
        for symb in [':', ' ']:
            dataframe.rename(columns={name: name.replace(symb, '_') for\
                                      name in dataframe.columns}, inplace=True) # just renaming columns
        
        for col in dataframe.columns[np.where(dataframe.columns == 'id',False,True)]:  # taking all but id 
            dataframe[col] = dataframe[col].apply(lambda x: atoi_like(x))  # removing extraneous data before declaration number
        '''rebuilding id'''
        id_cat = pd.DataFrame(dataframe.id.apply(lambda x: f'{x.split()[0]}_class_{x.split("_")[-1]}'))\
                                    .rename(columns={'id': 'id_cat'})
        dataframe.id = dataframe.id.apply(lambda x: atoi_like(x))
        dataframe = pd.merge(id_cat, dataframe, on=dataframe.index,  # always use on with index, otherwise you get dups
                       how='right').drop('key_0', axis=1)  # made it with id categories 
        
        if not dt_ops:  # managing datetime
            pass
        else:
            dataframe['tz'] = dataframe.time_timestamp.apply(lambda dt: dt.tzinfo)  # time zone column
            dataframe.time_timestamp = pd.to_datetime(dataframe.time_timestamp, utc=True)
            dataframe['date'] = dataframe.time_timestamp.dt.date  # date column
            dataframe['time'] = dataframe.time_timestamp.dt.time # UTC time column
            dataframe.time_timestamp = dataframe.time_timestamp.dt.tz_localize(None)  # casting to datetime[ns] without utc
            dataframe['week_delta'] = dataframe.time_timestamp.dt.to_period('W')  # week period when action was
        
        num_fields = dataframe.select_dtypes(include=['int', 'float'])  # casting numeric fields to float64
        num_fields = pd.DataFrame({col: pd.to_numeric(num_fields[f'{col}'], errors='coerce', downcast='unsigned') for col in num_fields.columns})
        dataframe[num_fields.columns] = num_fields
        
        obj_fields = dataframe.select_dtypes(include=['object']).copy()
        for col in obj_fields.columns:  # categorizing object fields for performance objective
            num_unique_values, num_total_values = len(obj_fields[col].unique()), len(obj_fields[col])
            obj_fields.loc[:,col] = obj_fields[col].astype('category') if num_unique_values / num_total_values < 0.2 else obj_fields.loc[:,col]
        dataframe[obj_fields.columns] = obj_fields
        
        if not year_period:  # slice data on year
            pass
        else:
            dataframe = dataframe.query(f'time_timestamp.dt.year >= {year_period[0]} and time_timestamp.dt.year < {year_period[1]}')
        
        if not sortby:  # if to sort by field
            pass
        else:
            dataframe = dataframe.sort_values(sortby)  # sorting by column parameter
        '''tuning section end'''
    
    elif configuration == 'default':
        print('proceeding with standard pm4py event <-> df conversion')
        
    print('MEM consumption:\t', mem_usage(dataframe))
    return dataframe

    
def all_dataframes(configuration='convenient', sortby=False, dt_ops=False, year_period=None):  # inprogress widget
    """gets all dataframes at once and saves in var all_dfs"""
        
    try:  # want it to be fancier
        df_dict = globals()['all_dfs']
        xes_files = globals()['logs']
        for _ in tqdm(iter(xes_files.keys()),\
                      desc='TRAVERSING LOGS IN DICT OF DATAFRAMES'):
                print('current log:\t', _)
                df_dict[_] = xes2dataframe(_, configuration=configuration, sortby=sortby, dt_ops=dt_ops, year_period=year_period) if df_dict[_] is None else df_dict[_];
                
    except:
        df_dict = dict()
        xes_event_logs()
        all_dataframes()
        
    return df_dict


'''PLOTTER CODE'''

def apply(func, *args, **kwargs):
    return func(*args, **kwargs)

def ax_plot(plotter, ax, data, name, size, nbins, xscale, yscale):
    '''axes object custom options for sns plots
        plot_axes_attrs: x, y, hue, label e.t.c.'''
    ax.set_xlabel('xlabel', fontsize=size * 1.4, labelpad=size * 1.2)
    ax.set_ylabel('ylabel', fontsize=size * 1.4, labelpad=size * 1.2)
    ax.tick_params('both', pad=size // 1.5)
    ax.locator_params(nbins=nbins, tight=True)
    ax.set_title(f'{plotter.__name__.capitalize()} for {name}', fontsize=size * 2.3, pad=size * 2.4)    
    ax.set_yscale(yscale)
    ax.set_xscale(xscale)
    try:  # tried to modify kwargs; its too hard, so get this)))
        apply(plotter, data=data, **plot_axes_attrs, ax=ax, label=name)
    except TypeError:
        apply(plotter, a=data, **plot_axes_attrs, ax=ax, label=name)
    plt.tight_layout(w_pad=size * .36, h_pad=size * .17)

    
def grid_plot(nrows=2, ncols=2, size=16, nbins=10, xscale='linear', yscale='linear', frameon=True, xrotation=0, yrotation=0):
    '''specify the size and number of axes params and this func will automatically make
        fancy tight layout plot according to the size'''
    wsize = size * ncols
    hsize = size * nrows
    figsize = (1. * wsize, .5 * hsize)
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, frameon=frameon)
    axes = np.array(axes).reshape(-1)
    try:
        gen = (ax_plot(plotter, axes[i], plot_data[i], plot_data_names[i], size, nbins, xscale, yscale) for i in range(axes.shape[0]))
        for g in range(axes.shape[0]): next(gen)
    except IndexError:
        pass
    plt.setp(map(lambda ax: ax.get_xticklabels(), axes), rotation=xrotation);
    plt.setp(map(lambda ax: ax.get_yticklabels(), axes), rotation=yrotation);
    
    return fig


'''WIDGET CODE'''
    
from ipywidgets import Dropdown, Output, HBox, VBox, Tab
from IPython.display import display, Markdown


default = 'CLOSED'
options = ['CLOSED', 'domestic declarations', 'international declarations',\
            'prepaid travel costs', 'request for payment', 'travel permitions']


dropdown_ta = Dropdown(options=options, value=default,
                   description='Table')
dropdown_ke = Dropdown(options=options, value=default,
                   description='Key table')
dropdown_am = Dropdown(options=options, value=default,
                   description='Unique vals')
dropdown_in = Dropdown(options=options, value=default,
                   description='INFO')

output_ta = Output()
output_ke = Output()
output_am = Output()
output_in = Output()


def main_eventhandler(table, key_table, amount, info):
    output_ta.clear_output()
    output_ke.clear_output()
    output_am.clear_output()  # amount should be as table too
    output_in.clear_output()
    
    if table == default:
        view = Markdown("<font color='#A0BBEE' size=4><center>Nothing to display for tables</center></font>")
        with output_ta:
            display(view)
    else:
        view = all_dfs[table].sample(frac=1).head(8)  # 8 random rows
        with output_ta:
            display(view.style.applymap(lambda x: 'color: orange'))
    if key_table == default:
        view = Markdown("<font color='#A0BBEE' size=4><center>Nothing to display for key tables</center></font>")
        with output_ke:
            display(view)
    else:
        view = pd.concat([all_dfs[key_table]], keys=all_dfs[key_table].id_cat).\
                        sample(frac=1).head(8)  # 12 random rows for grouped on id cat
        with output_ke:
            display(view.style.applymap(lambda x: 'color: orange'))
    if amount == default:
        amount = Markdown("<font color='#A0BBEE' size=4><center>Nothing to display for unique fields</center></font>")
        with output_am:
            display(amount)
    else:
        with output_am:
            display(Markdown(f'{amount}.md'))
    if info == default:
        info = Markdown("<font color='#A0BBEE' size=4><center>Nothing to display for info</center></font>")
        with output_in:
            display(info)
    else:  # FIXME
        info1 = all_dfs[table].describe()
        info2 = all_dfs[table].info()
        with output_in:
            display(info1)
            display(info2)

            
def tables_eventhandler(option):
    main_eventhandler(option.new, dropdown_ke.value, dropdown_am.value, dropdown_in.value)
def keytables_eventhandler(option):
    main_eventhandler(dropdown_ta.value, option.new, dropdown_am.value, dropdown_in.value)
def amounts_eventhandler(option):
    main_eventhandler(dropdown_ta.value, dropdown_ke.value, option.new, dropdown_in.value)
def information_eventhandler(option):
    main_eventhandler(dropdown_ta.value, dropdown_ke.value, dropdown_am.value, option.new)
