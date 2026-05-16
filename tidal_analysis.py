# import the modules we need
import pandas as pd
import datetime
import os
import numpy as np
import uptide
import pytz
import math
from scipy import stats
import matplotlib.dates as mdates
import argparse


def read_tidal_data(filename):
    # skip metadata headers
    tide_data = pd.read_csv(filename, sep=r'\s+', skiprows=11, header=None, engine='python',
                            names=['LineNum', 'Date', 'Time', 'Sea Level', 'Residual'])
    
    tide_data['DateTime'] = pd.to_datetime(tide_data['Date'] + ' ' + tide_data['Time'], format="%Y/%m/%d %H:%M:%S")
    tide_data = tide_data.set_index('DateTime')
    
    #strip flags (M,N,T)
    tide_data['Sea Level'] = tide_data['Sea Level'].astype(str)
    tide_data.replace(to_replace=r".*[MNT]$", value={'Sea Level': np.nan}, regex=True, inplace=True)
    #convert to numeric data
    tide_data['Sea Level'] = pd.to_numeric(tide_data['Sea Level'], errors='coerce')
    tide_data['Sea Level'] = tide_data['Sea Level'].mask(tide_data['Sea Level'] < -10)
    
    return tide_data [['Sea Level', 'Time']].copy()
    
def extract_single_year_remove_mean(year, data):
    year_data = data.loc[str(year)].copy()
    #remove mean to oscillate ard zero
    mmm = year_data['Sea Level'].mean()
    year_data['Sea Level'] = year_data['Sea Level'] - mmm
    
    return year_data


def extract_section_remove_mean(start, end, data):
    year_data = data.loc[start:end, ['Sea Level']].copy()
    mmm = year_data['Sea Level'].mean()
    year_data['Sea Level'] = year_data['Sea Level'] - mmm

    return year_data


def join_data(data1, data2):
    combined = pd.concat([data1, data2])
    combined = combined[~combined.index.duplicated(keep='first')]
    combined = combined.sort_index()
    return combined 

def sea_level_rise(data):
    #clean data as linear regression cant proceed with NaNs
    clean_data = data.dropna(subset=['Sea Level'])
    if len(clean_data) == 0: return 0.0, 1.0
    
    #x-axis(Time in days)
    t0 = pd.Timestamp(year=clean_data.index.year.min(), month=1, day=1)
    time_days = (clean_data.index - t0).total_seconds() / 86400
    #y-axis(Sea Level)
    sea_levels = clean_data['Sea Level'].values
    #linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(time_days, sea_levels)

    return slope, p_value 

def tidal_analysis(data, constituents, start_datetime):
    #create Tides object with consituents ['M2', 'S2']
    tide = uptide.Tides(constituents)
    tide.set_initial_time(start_datetime.replace(tzinfo=None))
    
    clean_data = data.dropna(subset=['Sea Level'])
    
    #localize index to UTC, use tz_convert if it's already
    if clean_data.index.tz is None:
        aware_index = clean_data.index.tz_localize("UTC")
    else:
        aware_index = clean_data.index.tz_convert("UTC")

    seconds_since = (aware_index - start_datetime).total_seconds().to_numpy()
    
    elevations = clean_data['Sea Level'].to_numpy()
    amp, pha = uptide.harmonic_analysis(tide, elevations, seconds_since)
    
    return amp, pha 

def get_longest_contiguous_data(data):

    return 


def main(args_list=None):

    parser = argparse.ArgumentParser(
                     prog="UK Tidal analysis",
                     description="Calculate tidal constiuents and RSL from tide gauge data",
                     )

    parser.add_argument("directory",
                    help="the directory containing txt files with data")
    parser.add_argument('-v', '--verbose',
                    action='store_true',
                    default=False,
                    help="Print progress")

    args = parser.parse_args(args_list)
    dirname = args.directory
    verbose = args.verbose

    print("Add your code here to do things!")
    

if __name__ == '__main__':
    main()
