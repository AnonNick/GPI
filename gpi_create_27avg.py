import xarray as xr
import numpy as np
import requests
from datetime import datetime, timedelta
import sys
import time
import os
import json

def download_file(url, file_path):
    # Send a GET request to the URL
    response = requests.get(url)
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Open a file with the specified path and write binary data to it
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"File downloaded successfully: {file_path}")
    else:
        print(f"Failed to download the file. Status code: {response.status_code}")

def find_starting_line(file_path, start_date):
    """Find the starting line index in the file based on a given start date."""
    with open(file_path, 'r') as file:
        for index, line in enumerate(file):
            if line.startswith('#'):
                continue
            parts = line.split()
            file_date = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
            if file_date >= start_date:
                return index
    return -1

def extract_kp_values(file_path, start_line):
    """Read the file from the starting line and extract Kp values."""
    kp_values = []
    with open(file_path, 'r') as file:
        for index, line in enumerate(file):
            if index < start_line:
                continue
            parts = line.split()
            kp_values.extend(parts[7:15])  # Extract Kp1 to Kp8 values
    return [float(kp) for kp in kp_values]

def generate_datetimes(start_date, num_days):
    """Generate datetime strings for each Kp value."""
    datetime_list = []
    current_date = start_date
    for _ in range(num_days):
        for _ in range(0, 24, 3):
            datetime_str = current_date.strftime('%Y-%m-%dT%H:00:00Z')
            datetime_list.append(datetime_str)
            current_date += timedelta(hours=3)
    return datetime_list

def process_kp_data(input_file, output_file, start_date):
    """Process Kp data starting from a specific date and write to a JSON file."""
    starting_line_index = find_starting_line(input_file, start_date)
    if starting_line_index == -1:
        print("No data found for the start date.")
        return

    kp_values = extract_kp_values(input_file, starting_line_index)
    num_days = len(kp_values) // 8
    datetimes = generate_datetimes(start_date, num_days)

    # Create the JSON structure
    kp_data = {
        "meta": {
            "source": "GFZ Potsdam",
            "license": "CC BY 4.0"
        },
        "datetime": datetimes,
        "Kp": kp_values
    }
    
    # Write the data to a JSON file
    with open(output_file, 'w') as json_file:
        json.dump(kp_data, json_file, indent=4)
    print(f"Kp data starting from {start_date.strftime('%Y-%m-%d')} has been successfully written to {output_file}")


def read_f107_data(file_path):
    """Reads F10.7 data from a file and returns a list of (date, F10.7obs) tuples."""
    data = []
    with open(file_path, 'r') as file:
        for line in file:
            if not line.startswith('#'):  # Skip header lines
                parts = line.split()
                year, month, day = map(int, parts[0:3])
                f107obs = float(parts[-3])  # Assuming F10.7obs is the third last element in each line
                date = datetime(year, month, day)
                data.append((date, f107obs))
    return data

def filter_f107_data(data, start_date):
    """Filters the F10.7 data to include only entries from start_date onwards."""
    return [(date.strftime("%Y-%m-%dT00:00:00Z"), f107obs) for date, f107obs in data if date >= start_date]

def process_f107_data(input_file, output_file, start_date):
    """Coordinates the reading, filtering, and writing of F10.7 data."""
    data = read_f107_data(input_file)
    filtered_data = filter_f107_data(data, start_date)
    
    # Prepare the data for JSON output
    fobs_data = {
        "meta": {
            "source": "GFZ Potsdam",
            "license": "CC BY 4.0"
        },
        "datetime": [entry[0] for entry in filtered_data],
        "Fobs": [entry[1] for entry in filtered_data]
    }
    
    # Write the data to a JSON file
    with open(output_file, 'w') as json_file:
        json.dump(fobs_data, json_file, indent=4)
    print(f"F10.7obs data starting from {start_date.strftime('%Y-%m-%d')} has been successfully written to {output_file}")


def date_format(timestamp):
    date_time_obj = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    # Format as 'YYYYDDD'
    formatted_date = date_time_obj.strftime("%Y%j")
    return(formatted_date)


yesterday_date = (datetime.now() - timedelta(days=1)).replace(hour=23, minute=59, second=59).strftime("%Y-%m-%dT%H:%M:%SZ")
end_date = yesterday_date #'2024-01-31T23:59:59Z'
#start_date = '1960-01-01T00:00:00Z'
start_date = '2024-01-01T00:00:00Z'
start_dates_remove = 27
start_date= (datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%SZ') - timedelta(days=start_dates_remove)).strftime("%Y-%m-%dT%H:%M:%SZ")
file_path = os.getcwd()#f'/glade/u/home/nikhilr/GPI'


# URL of the file to download
url = "https://kp.gfz-potsdam.de/app/files/Kp_ap_Ap_SN_F107_since_1932.txt"
# Local path to save the downloaded file
source_file_path = "Kp_ap_Ap_SN_F107_since_1932.txt"
download_file(url, source_file_path)



kp_output_file = 'Kp_data_27.json'


# Call the main processing function
process_kp_data(source_file_path, kp_output_file, datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ"))

f107_output_file = 'Fobs_data.json'

# Process the F10.7 observation data
process_f107_data(source_file_path, f107_output_file, datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ"))

with open(f107_output_file, 'r') as file:
    Fobs_data = json.load(file)

with open(kp_output_file, 'r') as file:
    Kp_data = json.load(file)


def compare_days_with_actual(years_count, actual_days_in_year):
    discrepancies = {}

    for year, count in years_count.items():
        if year in actual_days_in_year:
            discrepancies[year] = actual_days_in_year[year] - count

    print( discrepancies)

def find_missing_dates(date_time_array):

    from datetime import datetime, timedelta

    # Convert to datetime objects
    dates = [datetime.strptime(str(date), '%Y%j') for date in date_time_array]

    missing_dates = []
    new_dates=[]
    missing_date_index = []
    # Check each consecutive pair of dates for missing days
    for i in range(len(dates) - 1):
        current_date = dates[i]
        next_date = dates[i + 1]
        # Calculate the gap between the two dates, excluding the start date
        delta_days = (next_date - current_date).days
        new_dates.append(int(current_date.strftime("%Y%j")))
        # If there's more than one day between the two, add the missing dates
        for day in range(1, delta_days):
            missing_date = current_date + timedelta(days=day)
            missing_dates.append(int(missing_date.strftime('%Y%j')))
            new_dates.append(int(missing_date.strftime('%Y%j')))
            missing_date_index.append(i)
        if i == len(dates) - 2:
            new_dates.append(int(next_date.strftime("%Y%j")))
    return new_dates, missing_dates, missing_date_index



def counter(date_time_array):
    from collections import Counter
    from datetime import datetime, timedelta

    # Sample datetime array


    # Convert to datetime objects
    dates = [datetime.strptime(str(date), '%Y%j') for date in date_time_array]

    # Count the number of days in each year from the array
    years_count = Counter(date.year for date in dates)

    # Actual number of days in each year (considering leap years)
    actual_days_in_year = {year: 366 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 365 for year in years_count}
    #print(years_count, actual_days_in_year)
    #compare_days_with_actual(years_count, actual_days_in_year)


year_day = np.array([date_format(dt) for dt in Fobs_data['datetime']])
f107d = np.array(Fobs_data['Fobs'])
#counter(year_day)

year_day, missing_dates, missing_date_index =find_missing_dates(year_day)
for i,l_index in enumerate(missing_date_index):
    missing_index = i+l_index+1
    #f107_avg = (np.mean(f107d[missing_index-40:missing_index])+np.mean(f107d[missing_index+1:missing_index+41]))/2
    if f107d[missing_index +1] == -1:
        f107d_upper = f107d[missing_index +2]
    else:
        f107d_upper = f107d[missing_index +1]
    if f107d[missing_index -1] == -1:
        f107d_lower = f107d[missing_index -2]
    else:
        f107d_lower = f107d[missing_index -1]
    f107_avg = (f107d_upper+f107d_lower)/2
    print(year_day[missing_index],missing_index,f107_avg)
    f107d = np.insert(f107d,missing_index,f107_avg)

f107a = np.zeros_like(f107d)
for i in range(27, len(f107d)):
    f107a[i] = np.mean(f107d[i-27:i])

# Process KP data
unique_dates = sorted(set([dt[:10] for dt in Kp_data['datetime']])) # Unique dates in KP data

kp = []
extra_dates_in_KP=0
extra_dates_in_Fobs =0
end_dates_remove = 0
if len(unique_dates) != len(year_day):
    Fobs_dates = [datetime.strptime(str(date), '%Y%j') for date in year_day]
    Kp_dates = [datetime.strptime(date, '%Y-%m-%d') for date in unique_dates]
    if Kp_dates[-1].date() == Fobs_dates[-1].date():
        print("Both lists end on the same date.")
    else:
        print(Kp_dates[-1].date(),Fobs_dates[-1].date())
        Kp_last_date =  Kp_dates[-1].date()
        Fobs_lsat_date = Fobs_dates[-1].date()
        time_delta = Kp_last_date - Fobs_lsat_date
        if Kp_last_date > Fobs_lsat_date:
            extra_dates_in_KP = abs(int(time_delta.days))
        elif Fobs_lsat_date > Kp_last_date:
            extra_dates_in_Fobs = abs(int(time_delta.days))
        else:
            extra_dates_in_KP = 0
            extra_dates_in_Fobs= 0
        #extra_dates_in_KP = len([date for date in Kp_dates if date.date() not in [d.date() for d in Fobs_dates]])
        #extra_dates_in_Fobs = len([date for date in Fobs_dates if date.date() not in [d.date() for d in Kp_dates]])
        print("Extra dates in KP_dates:", extra_dates_in_KP)
        print("Extra dates in Fobs_dates:", extra_dates_in_Fobs)

Kp_end_dates_remove = 0
Fobs_end_dates_remove = 0
'''
if extra_dates_in_Fobs != 0:
    if extra_dates_in_Fobs <= 40:
        Fobs_end_dates_remove = 40
        Kp_end_dates_remove =  40 - extra_dates_in_Fobs     
    else:
        Fobs_end_dates_remove = extra_dates_in_Fobs
        Kp_end_dates_remove =  extra_dates_in_Fobs 
elif extra_dates_in_KP !=0:
    Fobs_end_dates_remove = 40
    Kp_end_dates_remove =  extra_dates_in_KP + 40 
else:
    Fobs_end_dates_remove = 40
    Kp_end_dates_remove =  40 
'''
for date in unique_dates:
    formatted_string = "[%-*s] %d%% Date:%s" % (50, '=' * int((len(kp)) / len(unique_dates) * 50), (len(kp)) / len(unique_dates) * 100, date)
    # Writing the formatted string to stdout
    sys.stdout.write('\r')
    sys.stdout.write(formatted_string)
    sys.stdout.flush()
    daily_kps = [Kp_data['Kp'][i] for i, dt in enumerate(Kp_data['datetime']) if dt.startswith(date)]
    kp.append(daily_kps[:8]) 


kp = np.array(kp)
year_day = year_day[start_dates_remove:]
f107d = f107d[start_dates_remove:]
f107a = f107a[start_dates_remove:]
kp = kp[start_dates_remove:]






# Create an xarray Dataset
ds = xr.Dataset({
    'year_day': (['ndays'], year_day, {'long_name': '4-digit year followed by 3-digit day'}),
    'f107d': (['ndays'], f107d, {'long_name': 'daily 10.7 cm solar flux'}),
    'f107a': (['ndays'], f107a, {'long_name': '27-day average 10.7 cm solar flux'}),
    'kp': (['ndays', 'nkp'], kp, {'long_name': '3-hourly kp index'})
}, coords={
    'ndays': year_day,
    'nkp': np.arange(kp.shape[1])
})

# Adding global attributes
ds.attrs['title'] = 'Geophysical Indices, obtained from gfz-potsdam'
ds.attrs['yearday_beg'] = year_day[0]
ds.attrs['yearday_end'] = year_day[len(year_day)-1]  
ds.attrs['ncar_mss_path'] = '/TGCM/data/gpi_1960001-2015365.nc'
ds.attrs['data_source_url'] = 'https://kp.gfz-potsdam.de/'
ds.attrs['hao_file_write_source'] = 'https://github.com/AnonNick/GPI'
ds.attrs['info'] = 'Yearly ascii data files obtained from data_source_url; nc file written by hao_file_write_source.'
ds.attrs['F107_missing'] = missing_dates


if Fobs_end_dates_remove >= Kp_end_dates_remove:
    end_dates_remove = Fobs_end_dates_remove
else:
    end_dates_remove = Kp_end_dates_remove
end_date_str = (datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%SZ') - timedelta(days=end_dates_remove)).strftime("%Y-%m-%dT%H:%M:%SZ")
start_date_str = (datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%SZ') + timedelta(days=start_dates_remove)).strftime("%Y-%m-%dT%H:%M:%SZ")

file_name=f'gpi_{date_format(start_date_str)}-{date_format(end_date_str)}.nc'
file_path = f'{file_path}/{file_name}'

# Save the dataset as a NetCDF file
ds.to_netcdf(path=file_path)

print(f"\nNetCDF file created and saved at: {file_path}")
