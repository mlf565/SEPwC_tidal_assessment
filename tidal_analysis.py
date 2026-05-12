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
    tide_data = pd.read_csv(filename, sep=r'\s+', skiprows=11, header=None, engine='python')
    tide_data['Date'] = pd.to_datetime(tide_data[1] + ' ' + tide_data[2])
    tide_data = tide_data.rename(columns={3: "Sea Level"})
    
    tide_data = tide_data.set_index('Date')
    tide_data = tide_data[['Sea Level']].copy()
    
    tide_data['Sea Level'] = pd.to_numeric(tide_data['Sea Level'], errors='coerce')
    tide_data = tide_data.mask(tide_data['Sea Level'] < -10)
    
    return tide_data
    
def extract_single_year_remove_mean(year, data):
    year_string_start = str(year)+"-01-01"
    year_string_end = str(year)+"-12-31"
    year_data = data.loc[year_string_start:year_string_end, ['Sea Level']].copy()
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

    return 

def sea_level_rise(data):

    return

def tidal_analysis(data, constituents, start_datetime):

    return

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
