import xarray as xr
import numpy as np
import requests
from datetime import datetime




def date_format(timestamp):
    date_time_obj = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    # Format as 'YYYYDDD'
    formatted_date = date_time_obj.strftime("%Y%j")
    return(formatted_date)


stat_date= '1960-01-01T00:00:00Z'#'2024-02-01T23:59:59Z'#
end_date= '2024-01-31T23:59:59Z'
# The API URL
Fobs_url = f'https://kp.gfz-potsdam.de/app/json/?start={stat_date}&end={end_date}&index=Fobs&status=def'
Kp_url = f'https://kp.gfz-potsdam.de/app/json/?start={stat_date}&end={end_date}&index=Kp&status=def'
# Make a GET request to the API
response_Fobs = requests.get(Fobs_url)
response_Kp = requests.get(Kp_url)

# Check if the request was successful
if response_Fobs.status_code == 200 and response_Kp.status_code == 200:
    # Parse the JSON data
    Fobs_data = response_Fobs.json()
    Kp_data = response_Kp.json()
    # Print the data
    #print(Fobs_data)
    #print(Kp_data)
else:
    print(f"Fpbs status code: {response_Fobs.status_code}")
    print(f"Kp status code: {response_Kp.status_code}")

def compare_days_with_actual(years_count, actual_days_in_year):
    """
    Compare the counted days in each year from the list with the actual number of days in those years.

    Args:
    - years_count (dict): A dictionary with years as keys and the count of days from the list as values.
    - actual_days_in_year (dict): A dictionary with years as keys and the actual number of days in those years as values.

    Returns:
    - discrepancies (dict): A dictionary with years as keys and the differences between actual days and counted days as values.
    """
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

# Example usage



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
    print(years_count, actual_days_in_year)
    compare_days_with_actual(years_count, actual_days_in_year)


print(len(Fobs_data['datetime']))
print(len(Kp_data['datetime'])/8)
# Process F107 data
year_day = np.array([date_format(dt) for dt in Fobs_data['datetime']])
f107d = np.array(Fobs_data['Fobs'])
#counter(year_day)

year_day, missing_date, missing_date_index =find_missing_dates(year_day)
print(missing_date)
#print(missing_date_index)
for i,l_index in enumerate(missing_date_index):
    f107d = np.insert(f107d,i+l_index+1,-1)
#print(len(dates),dates[0],dates[len(dates)-1])
#print(len(year_day),year_day[0],year_day[len(year_day)-1])


f107a = np.zeros_like(f107d)

for i in range(40, len(f107d) - 40):
    f107a[i] = np.mean(f107d[i-40:i+41])

# Process KP data
unique_dates = sorted(set([dt[:10] for dt in Kp_data['datetime']])) # Unique dates in KP data

kp = []

for date in unique_dates:
    print(date)
    # Extract KP values for the current date
    daily_kps = [Kp_data['Kp'][i] for i, dt in enumerate(Kp_data['datetime']) if dt.startswith(date)]
    kp.append(daily_kps[:8]) # Ensure only the first 8 values are taken for each day
    print(len(kp))
kp = np.array(kp)

print(len(year_day),year_day[0],year_day[len(year_day)-1])
print(len(f107d))
print(len(f107a))
print(len(kp))
#print(year_day, f107d,f107a, kp)



# Create an xarray Dataset
ds = xr.Dataset({
    'year_day': (['ndays'], year_day, {'long_name': '4-digit year followed by 3-digit day'}),
    'f107d': (['ndays'], f107d, {'long_name': 'daily 10.7 cm solar flux'}),
    'f107a': (['ndays'], f107a, {'long_name': '81-day average 10.7 cm solar flux'}),
    'kp': (['ndays', 'nkp'], kp, {'long_name': '3-hourly kp index'})
}, coords={
    'ndays': year_day,
    'nkp': np.arange(kp.shape[1])
})

# Adding global attributes
ds.attrs['title'] = 'Geophysical Indices, obtained from NGDC'
ds.attrs['yearday_beg'] = year_day[0]
ds.attrs['yearday_end'] = year_day[len(year_day)-1]  # Assuming the end day is the same as the start day for this single entry
ds.attrs['ncar_mss_path'] = '/TGCM/data/gpi_1960001-2015365.nc'
ds.attrs['data_source_url'] = 'ftp://ftp.ngdc.noaa.gov/STP/GEOMAGNETIC_DATA/INDICES/KP_AP/'
ds.attrs['hao_file_write_source'] = '/home/tgcm/mkgpi/mkncgpi.f'
ds.attrs['info'] = 'Yearly ascii data files obtained from data_source_url; nc file written by hao_file_write_source.'

# Specify the path where you want to save the file
file_path = '/glade/u/home/nikhilr/GPI/test3.nc'

# Save the dataset as a NetCDF file
ds.to_netcdf(path=file_path)

print(f"NetCDF file created and saved at: {file_path}")
