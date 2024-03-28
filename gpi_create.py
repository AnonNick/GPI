import xarray as xr
import numpy as np
import requests
from datetime import datetime, timedelta
import sys
import time
import os


def date_format(timestamp):
    date_time_obj = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    # Format as 'YYYYDDD'
    formatted_date = date_time_obj.strftime("%Y%j")
    return(formatted_date)


yesterday_date = (datetime.now() - timedelta(days=1)).replace(hour=23, minute=59, second=59).strftime("%Y-%m-%dT%H:%M:%SZ")
end_date = yesterday_date #'2024-01-31T23:59:59Z'
stat_date = '1960-01-01T00:00:00Z'
start_dates_remove = 40
stat_date= (datetime.strptime(stat_date, '%Y-%m-%dT%H:%M:%SZ') - timedelta(days=start_dates_remove)).strftime("%Y-%m-%dT%H:%M:%SZ")
file_path = os.getcwd()#f'/glade/u/home/nikhilr/GPI'

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
else:
    print(f"Fpbs status code: {response_Fobs.status_code}")
    print(f"Kp status code: {response_Kp.status_code}")

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

for i in range(40, len(f107d) - 40):
    f107a[i] = np.mean(f107d[i-40:i+41])

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

for date in unique_dates:
    formatted_string = "[%-*s] %d%% Date:%s" % (50, '=' * int((len(kp)) / len(unique_dates) * 50), (len(kp)) / len(unique_dates) * 100, date)
    # Writing the formatted string to stdout
    sys.stdout.write('\r')
    sys.stdout.write(formatted_string)
    sys.stdout.flush()
    daily_kps = [Kp_data['Kp'][i] for i, dt in enumerate(Kp_data['datetime']) if dt.startswith(date)]
    kp.append(daily_kps[:8]) 

kp = np.array(kp)

year_day = year_day[start_dates_remove:-Fobs_end_dates_remove]
f107d = f107d[start_dates_remove:-Fobs_end_dates_remove]
f107a = f107a[start_dates_remove:-Fobs_end_dates_remove]
kp = kp[start_dates_remove:-Kp_end_dates_remove]


"""print(len(year_day),year_day[0],year_day[len(year_day)-1])
print(len(f107d))
print(len(f107a))
print(len(kp))"""




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
start_date_str = (datetime.strptime(stat_date, '%Y-%m-%dT%H:%M:%SZ') + timedelta(days=start_dates_remove)).strftime("%Y-%m-%dT%H:%M:%SZ")

file_name=f'gpi_{date_format(start_date_str)}-{date_format(end_date_str)}.nc'
file_path = f'{file_path}/{file_name}'

# Save the dataset as a NetCDF file
ds.to_netcdf(path=file_path)

print(f"NetCDF file created and saved at: {file_path}")
