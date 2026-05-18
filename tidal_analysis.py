"""UK Tidal Analysis Module.

this script reads, processes, and analyzes raw tide gauge data from the 
British Oceangraphic Data Centre (BODC). it automates the calculation of
relative sea level rise trends over time and extracts continuous operational 
observation intervals for further mathematical or astronomical study.
"""

# Copyright 2026 by Kai Ern Lim. CC-BY-SA.
# import the modules we need
import os
import argparse
import glob
import datetime #pylint: disable=unused-import
import pandas as pd
import numpy as np
import uptide
from scipy import stats
import matplotlib.dates as mdates


def read_tidal_data(filename):
    """
    reads tidal data from a text file, cleans flag markers, and format dates.
    """
    # skip metadata headers
    tide_data = pd.read_csv(filename, sep=r'\s+', skiprows=11, header=None, engine='python',
                            names=['LineNum', 'Date', 'Time', 'Sea Level', 'Residual'])
    tide_data['DateTime'] = pd.to_datetime(tide_data['Date'] + ' ' + tide_data['Time'],
                                           format="%Y/%m/%d %H:%M:%S")
    tide_data = tide_data.set_index('DateTime')

    #strip flags (M,N,T)
    tide_data['Sea Level'] = tide_data['Sea Level'].astype(str)
    tide_data.replace(to_replace=r".*[MNT]$", value={'Sea Level': np.nan}, regex=True, inplace=True)
    #convert to numeric data
    tide_data['Sea Level'] = pd.to_numeric(tide_data['Sea Level'], errors='coerce')
    tide_data['Sea Level'] = tide_data['Sea Level'].mask(tide_data['Sea Level'] < -10)

    return tide_data [['Sea Level', 'Time']].copy()

def extract_single_year_remove_mean(year, data):
    """
    extracts data for a target year and centers the sea levels around zero.
    """
    year_data = data.loc[str(year)].copy()
    #remove mean to oscillate ard zero
    mmm = year_data['Sea Level'].mean()
    year_data['Sea Level'] = year_data['Sea Level'] - mmm

    return year_data


def extract_section_remove_mean(start, end, data):
    """
    slices a specific timeframe from the dataset and substract its mean.
    """
    year_data = data.loc[start:end, ['Sea Level']].copy()
    mmm = year_data['Sea Level'].mean()
    year_data['Sea Level'] = year_data['Sea Level'] - mmm

    return year_data


def join_data(data1, data2):
    """
    combine two seperate tidal data into chronologically sorted set.
    """
    combined = pd.concat([data1, data2])
    #avoid duplicated
    combined = combined[~combined.index.duplicated(keep='first')]
    combined = combined.sort_index()
    return combined

def sea_level_rise(data):
    """
    calculates the long-term relative sea level rise using linear regression.
    """
    #clean data as linear regression cant proceed with NaNs
    clean_data = data.dropna(subset=['Sea Level'])
    if len(clean_data) == 0:
        return 0.0, 1.0
    #x-axis(Time in days)
    time_days = mdates.date2num(clean_data.index)
    #y-axis(Sea Level)
    sea_levels = clean_data['Sea Level'].values
    #linear regression
    slope, _, _, p_value, _ = stats.linregress(time_days, sea_levels)

    return slope, p_value

def tidal_analysis(data, constituents, start_datetime):
    """
    performs harmonic analysis to determine tidal constituent behaviors.
    """
    #create Tides object with consituents ['M2', 'S2']
    tide = uptide.Tides(constituents)
    start_dt = pd.Timestamp(start_datetime)
    tide.set_initial_time(start_dt.tz_localize(None).to_pydatetime())

    clean_data = data.dropna(subset=['Sea Level'])

    #localize index to UTC, use tz_convert if it's already
    if start_dt.tzinfo is not None:
        if clean_data.index.tz is None:
            aligned_index = clean_data.index.tz_localize(start_dt.tzinfo)
        else:
            aligned_index = clean_data.index.tz_convert(start_dt.tzinfo)
    else:
        if clean_data.index.tz is not None:
            aligned_index = clean_data.index.tz_convert(None)
        else:
            aligned_index = clean_data.index
    seconds_since = (aligned_index - start_dt).total_seconds().to_numpy()

    elevations = clean_data['Sea Level'].to_numpy()
    amp, pha = uptide.harmonic_analysis(tide, elevations, seconds_since)

    return amp, pha

def get_longest_contiguous_data(data):
    """
    identifies and extracts longest sequential segment of records unbroken by NaN or Null indicators
    """
    not_null = data['Sea Level'].notnull()

    groups = (not_null != not_null.shift()).cumsum()
    contiguous_blocks = data[not_null].groupby(groups)

    if not_null.any():
        longest_group_id = contiguous_blocks.size().idxmax()
        return contiguous_blocks.get_group(longest_group_id)

    return data.iloc[0:0]

def main(args_list=None):
    """
    organise the reading of the UK Tidal Analysis file and the tracking of statistical execution.
    """
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

    dirname = dirname.rstrip(os.sep)

    search_path = os.path.join(dirname, "**", "*.txt")
    files = sorted(glob.glob(search_path, recursive=True))

    if not files:
        if verbose:
            print(f"No valid records detected inside directory target: {dirname}")
        return

    combined_data = None
    for file in files:
        if verbose:
            #emitting tracking alerts safely allows verbose tests to output beyond 50
            print(f"Loading data sequence from target path: {os.path.basename(file)}...")

        data = read_tidal_data(file)
        combined_data = data if combined_data is None else join_data(combined_data, data)

        if combined_data is not None:
            slope, p_value = sea_level_rise(combined_data)
            longest_block = get_longest_contiguous_data(combined_data)

            amp, _ = tidal_analysis(combined_data, ['M2', 'S2'], combined_data.index.min())

            if args.verbose:
                print("\n" + "="*45)
                print(
                    f"Tidal Analysis Execution Results for: "
                    f"{os.path.basename(dirname.strip('/'))}"
                    )
                print("="*45)
                print(f"Total Combined Measurements: {len(combined_data)}")
                print(f"Longest Unbroken Continuous Window: {len(longest_block)} intervals")
                if len(longest_block) > 0:
                    print(
                        f"Unbroken Period Bounds: {longest_block.index.min()}"
                        f" to {longest_block.index.max()}"
                        )
                print(f"Relative Sea Level Rise Trend: {slope: .6e} m/day")
                print(f"Analysis Significance (P-value): {p_value: .5f}")
                print(f"M2 Amplitude: {amp[0]: .3f} m")
                print(f"S2 Amplitude: {amp[1]: .3f} m")
                print("="*45)

if __name__ == '__main__':
    main()
