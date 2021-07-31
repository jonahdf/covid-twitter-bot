import pandas as pd
from sodapy import Socrata
import datetime
import definitions

# Get all raw data
nyt_data_us = pd.read_csv("https://raw.githubusercontent.com/nytimes/covid-19-data/master/rolling-averages/us.csv")
nyt_data_state = pd.read_csv("https://raw.githubusercontent.com/nytimes/covid-19-data/master/rolling-averages/us-states.csv")
client = Socrata("healthdata.gov", None)
results = client.get("g62h-syeh", limit=2000000)
test_results = client.get("j8mb-icvb", limit=2000000)

# Filter data to get columns of interest
hhs_data = pd.DataFrame.from_records(results)[['state', 'date', 'inpatient_beds_used_covid']]
hhs_data.inpatient_beds_used_covid = hhs_data.inpatient_beds_used_covid.fillna(0)
hhs_data = hhs_data.astype({'inpatient_beds_used_covid': 'int32'})
test_data = pd.DataFrame.from_records(test_results)[['state', 'date', 'overall_outcome', 'new_results_reported']]
test_data.new_results_reported = test_data.new_results_reported.fillna(0)
test_data = test_data.astype({'new_results_reported': 'int32'})

# For provisional data, gets days since most recent update of HHS time series
max_date = hhs_data.date.max()
provisional = client.get("4cnb-m4rz", limit=2000000, where=f"update_date > '{max_date}'")
hhs_provisional = pd.DataFrame.from_records(provisional)[['update_date', 'archive_link']]
hhs_provisional.update_date = hhs_provisional.update_date.apply(lambda x: x[:10])
hhs_provisional.update_date = pd.to_datetime(hhs_provisional.update_date)

# Gets last archive of every day
group = hhs_provisional.groupby(['update_date'])
hhs_provisional = group.last()

# Add provisional data to HHS data
frames = []
for a in hhs_provisional.iterrows():
    date = a[0]
    url = a[1].item()['url']
    df = pd.read_csv(url)[['state', 'inpatient_beds_used_covid']]
    df['date']=date
    frames.append(df)
frames.append(hhs_data)
hhs_data = (pd.concat(frames))

# Make date columns in proper format
# hhs_data.date = hhs_data.date.apply(lambda x: x[:10])
hhs_data.date= pd.to_datetime(hhs_data.date)
test_data.date = test_data.date.apply(lambda x: x[:10])
test_data.date = pd.to_datetime(test_data.date)
nyt_data_us.date = pd.to_datetime(nyt_data_us.date)
nyt_data_state.date = pd.to_datetime(nyt_data_state.date)

"""
get_state_cases
Creates dataframe of time series date and cases for given state
inputs:
 state_codes: List of 2-letter codes of states to query
 start_date (pd.Timestamp): starting date, defaults to 1-1-2020
 end_date (pd.Timestamp): ending date, defaults to today 
returns:
 df with 'date' and 'test_positivity'
"""
def get_state_cases(state_codes, start_date = pd.Timestamp(2020,1,1), end_date = pd.Timestamp.today()):
    curr_date = start_date
    input_states = [definitions.states[s] for s in state_codes]
    state_data = nyt_data_state[nyt_data_state.state.isin(input_states)]
    max_date = state_data.date.max()
    lst = []
    while(curr_date <= end_date and curr_date <= max_date):
        day_data = state_data[state_data.date == str(curr_date)]
        case_sum = day_data.cases.sum()
        newRow = {'date': curr_date, 'cases': case_sum}
        lst.append(newRow)
        curr_date += datetime.timedelta(1)
    return pd.DataFrame(lst)

def get_us_cases(start_date = pd.Timestamp(2020,1,1), end_date = pd.Timestamp.today()):
    us_data = nyt_data_us[(nyt_data_us.date >= start_date) & (nyt_data_us.date <= end_date)]
    return us_data[['date', 'cases']]

"""
get_state_deaths
Same as above, deaths
"""
def get_state_deaths(state_codes, start_date = pd.Timestamp(2020,1,1), end_date = pd.Timestamp.today()):
    curr_date = start_date
    input_states = [definitions.states[s] for s in state_codes]
    state_data = nyt_data_state[nyt_data_state.state.isin(input_states)]
    max_date = state_data.date.max()
    lst = []
    while(curr_date <= end_date and curr_date <= max_date):
        day_data = state_data[state_data.date == str(curr_date)]
        case_sum = day_data.deaths.sum()
        newRow = {'date': curr_date, 'deaths': case_sum}
        lst.append(newRow)
        curr_date += datetime.timedelta(1)
    return pd.DataFrame(lst)

def get_us_deaths(start_date = pd.Timestamp(2020,1,1), end_date = pd.Timestamp.today()):
    us_data = nyt_data_us[(nyt_data_us.date >= start_date) & (nyt_data_us.date <= end_date)]
    return us_data[['date', 'deaths']]

"""
get_state_hospitalizations
Same as above, hospitalizations
"""
def get_state_hospitalizations(state_codes, start_date = pd.Timestamp(2020,1,1), end_date = pd.Timestamp.today()):
    curr_date = start_date
    state_data = hhs_data[hhs_data.state.isin(state_codes)]
    max_date = state_data.date.max()
    lst = []
    while(curr_date <= end_date and curr_date <= max_date):
        day_data = state_data[state_data.date == str(curr_date)]
        hosp_sum = day_data.inpatient_beds_used_covid.sum()
        newRow = {'date': curr_date, 'hospitalizations': hosp_sum}
        lst.append(newRow)
        curr_date += datetime.timedelta(1)
    return pd.DataFrame(lst)
"""
get_us_hospitalizations
Same as above, hospitalizations
"""
def get_us_hospitalizations(start_date = pd.Timestamp(2020,1,1), end_date = pd.Timestamp.today()):
    curr_date = start_date
    max_date = hhs_data.date.max()
    lst = []
    while(curr_date <= end_date and curr_date <= max_date):
        day_data = hhs_data[hhs_data.date == str(curr_date)]
        hosp_sum = day_data.inpatient_beds_used_covid.sum()
        newRow = {'date': curr_date, 'inpatient_beds_used_covid': hosp_sum}
        lst.append(newRow)
        curr_date += datetime.timedelta(1)
    return pd.DataFrame(lst)

"""
get_state_positivity
Creates dataframe of time series date and test positivity for given state
inputs:
 state_code: list of 2-letter codes of states
 start_date (pd.Timestamp): starting date, defaults to 1-1-2020
 end_date (pd.Timestamp): ending date, defaults to today 
returns:
 df with 'date' and 'test_positivity'
"""
def get_state_positivity(state_codes, start_date = pd.Timestamp(2020,1,1), end_date = pd.Timestamp.today()):
    test_data_state = test_data[test_data.state.isin(state_codes)] # Get only data from input State
    max_date = test_data.date.max()
    curr_date = start_date
    lst = []
    while(curr_date <= end_date and curr_date <= max_date): # Loop through all unique dates
        day_data = test_data_state[test_data_state.date == str(curr_date)]
        test_pos = day_data[day_data.overall_outcome == "Positive"].new_results_reported # Get num positive tests
        test_pos = test_pos.sum() if test_pos.any() else 0 # Extract number if exists
        test_neg = day_data[day_data.overall_outcome == "Negative"].new_results_reported # Get num negative tests
        test_neg = test_neg.sum() if test_neg.any() else 0 # Extract number if exists
        if(test_pos == 0 and test_neg == 0):
            test_pct = 0 # Fixes divide by zero issue
        else:
            test_pct = test_pos/ (test_pos + test_neg) * 100
        newRow = {"date": curr_date, "test_positivity": test_pct, "positive_tests" : test_pos, "negative_tests" : test_neg}
        lst.append(newRow)
        curr_date += datetime.timedelta(1)

    return pd.DataFrame(lst) # Create dataframe with all dates and test positivity

"""
get_us_positivity
Constructs a data table of the entire US test positivity

start_date (datetime.date) : Starting date of table
end_date (datetime.date) : Ending date of table
returns: dataframe with date, test positivity

"""
def get_us_positivity(start_date = pd.Timestamp(2020,1,1), end_date = pd.Timestamp.today()):
    curr_date = start_date
    max_date = test_data.date.max()
    lst = []
    while (curr_date <= end_date and curr_date <= max_date):
        test_data_curr = test_data[test_data.date==str(curr_date)]
        test_pos = test_data_curr[test_data_curr.overall_outcome == "Positive"]
        test_neg = test_data_curr[test_data_curr.overall_outcome == "Negative"]
        pos_sum = test_pos.new_results_reported.sum()
        neg_sum = test_neg.new_results_reported.sum()
        test_positivity = pos_sum / (pos_sum + neg_sum) * 100
        newRow = {"date": curr_date, "test_positivity": test_positivity}
        lst.append(newRow)
        curr_date += datetime.timedelta(1)
    return pd.DataFrame(lst)




