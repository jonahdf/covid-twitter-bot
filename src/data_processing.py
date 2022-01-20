import pandas as pd
from sodapy import Socrata
import datetime
import definitions

# global variables for main data:
hhs_data, test_data, nyt_data_us, nyt_data_state, max_hosp_date = [],[],[],[],[]

"""
get_data()
Fetches data from API, filters, cleans, and combines with provisional.
After running, global variables are filled for use in subsequent functions
"""
def get_data():
    global nyt_data_us
    global nyt_data_state
    global test_data
    global hhs_data
    global max_hosp_date

    nyt_data_us = pd.read_csv("https://raw.githubusercontent.com/nytimes/covid-19-data/master/rolling-averages/us.csv")
    nyt_data_state = pd.read_csv("https://raw.githubusercontent.com/nytimes/covid-19-data/master/rolling-averages/us-states.csv")
    client = Socrata("healthdata.gov", None)
    results = client.get("g62h-syeh", limit=2000000)
    test_results = client.get("j8mb-icvb", limit=2000000)
    print("LOG: Fetched all raw data")

    # Filter data to get columns of interest
    hhs_data = pd.DataFrame.from_records(results)[['state', 'date', 'inpatient_beds_used_covid']]
    hhs_data.inpatient_beds_used_covid = hhs_data.inpatient_beds_used_covid.fillna(0)
    hhs_data = hhs_data.astype({'inpatient_beds_used_covid': 'int32'})
    test_data = pd.DataFrame.from_records(test_results)[['state', 'date', 'overall_outcome', 'new_results_reported']]
    test_data.new_results_reported = test_data.new_results_reported.fillna(0)
    test_data = test_data.astype({'new_results_reported': 'int32'})
    print("LOG: Filtered Data")

    # For provisional data, gets days since most recent update of HHS time series
    max_date = hhs_data.date.max()
    max_hosp_date = max_date
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
        if date > pd.Timestamp(max_date): # Avoids double counting if provisional update came after real update
            frames.append(df)
    frames.append(hhs_data)
    hhs_data = (pd.concat(frames))
    print("LOG: Added HHS Provisional data")


    # Make date columns in proper format
    # hhs_data.date = hhs_data.date.apply(lambda x: x[:10])
    hhs_data.date= pd.to_datetime(hhs_data.date)
    # hhs_data.to_csv("../data/hospitalizations.csv")
    print("LOG: Wrote HHS data to CSV")
    test_data.date = test_data.date.apply(lambda x: x[:10])
    test_data.date = pd.to_datetime(test_data.date)
    nyt_data_us.date = pd.to_datetime(nyt_data_us.date)
    nyt_data_state.date = pd.to_datetime(nyt_data_state.date)
    print("LOG: Done getting data")


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
def get_state_cases(state_codes, start_date = pd.Timestamp(2020,1,1), end_date = pd.Timestamp.today(), normalize=True):
    curr_date = start_date
    input_states = [definitions.states[s] for s in state_codes]
    state_data = nyt_data_state[nyt_data_state.state.isin(input_states)][:]
    max_date = state_data.date.max()
    states_population = sum([definitions.populations[s] for s in input_states])
    lst = []
    while(curr_date <= end_date and curr_date <= max_date):
        day_data = state_data[state_data.date == str(curr_date)]
        if normalize:
            case_sum = day_data.cases.sum() / states_population * 1000000
        else:
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
def get_state_deaths(state_codes, start_date = pd.Timestamp(2020,1,1), end_date = pd.Timestamp.today(), normalize=True):
    curr_date = start_date
    input_states = [definitions.states[s] for s in state_codes]
    state_data = nyt_data_state[nyt_data_state.state.isin(input_states)]
    max_date = state_data.date.max()
    states_population = sum([definitions.populations[s] for s in input_states])
    lst = []
    while(curr_date <= end_date and curr_date <= max_date):
        day_data = state_data[state_data.date == str(curr_date)]
        if normalize:
            case_sum = day_data.deaths.sum() / states_population * 1000000
        else:
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
def get_state_hospitalizations(state_codes, start_date = pd.Timestamp(2020,1,1), end_date = pd.Timestamp.today(), normalize=True):
    curr_date = start_date
    state_data = hhs_data[hhs_data.state.isin(state_codes)]
    input_states = [definitions.states[s] for s in state_codes]
    max_date = state_data.date.max()
    states_population = sum([definitions.populations[s] for s in input_states])
    lst = []
    while(curr_date <= end_date and curr_date <= max_date):
        day_data = state_data[state_data.date == str(curr_date)]
        if normalize:
            hosp_sum = day_data.inpatient_beds_used_covid.sum() / states_population * 1000000
        else:
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
    max_date = test_data_state.date.max()
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

    df = pd.DataFrame(lst) # Create dataframe with all dates and test positivity
    a = df.rolling(7).sum()
    df['avg'] = a.apply(lambda x: (100* (x.positive_tests / (x.positive_tests + x.negative_tests))) if (x.positive_tests + x.negative_tests) > 0 else None, axis=1)
    return df

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
        test_pos = test_data_curr[test_data_curr.overall_outcome == "Positive"].new_results_reported
        test_neg = test_data_curr[test_data_curr.overall_outcome == "Negative"].new_results_reported
        pos_sum = test_pos.sum() if test_pos.any() else 0
        neg_sum = test_neg.sum() if test_pos.any() else 0
        test_positivity = pos_sum / (pos_sum + neg_sum) * 100 if (pos_sum + neg_sum) > 0 else None
        newRow = {"date": curr_date, "test_positivity": test_positivity, "positive_tests" : pos_sum, "negative_tests": neg_sum}
        lst.append(newRow)
        curr_date += datetime.timedelta(1)
    df = pd.DataFrame(lst)
    # Calculates 7-day averages of test positivity using sums over the window
    a = df.rolling(7).sum()
    df['avg'] = a.apply(lambda x: (100* (x.positive_tests / (x.positive_tests + x.negative_tests))) if (x.positive_tests + x.negative_tests) > 0 else None, axis=1)
    return df

"""
get_all_state_hosps
Constructs a table of the most recent hospitalizations per capita for every State
returns: dataframe with state, hosp per million
"""
def get_all_state_hosps():
    state_hosps = pd.DataFrame(columns=['State', 'Hospitalizations'])
    for state in definitions.states.keys():
        state_data = hhs_data[hhs_data.state.isin([state])]
        state_data = state_data[state_data['date'] <= pd.Timestamp.today()]
        hosps = state_data[state_data['date'] == state_data['date'].max()].inpatient_beds_used_covid.values
        if not hosps:
            hosps = False
        else:
            hosps = hosps[0]/definitions.populations[definitions.states[state]]*1000000
            state_hosps = state_hosps.append({"State":state, "Hospitalizations per Million": float(hosps)}, ignore_index=True)
    return state_hosps

"""
get_all_state_cases
Constructs a table of the most recent cases per capita for every State
returns: dataframe with state, cases per million
"""
def get_all_state_cases():
    state_cases = pd.DataFrame(columns=['State', 'Cases'])
    for state in definitions.states.keys():
        state_data = get_state_cases([state], start_date=(pd.Timestamp.today() - pd.Timedelta(days=7)).date()) # adjust end date here
        if state_data.empty:
            cases = False
        else:
            cases = state_data.cases.sum() / len(state_data)
            state_cases = state_cases.append({"State":state, "Cases": float(cases)}, ignore_index=True)
    return state_cases

"""
get_all_state_rt
Constructs a table of the most recent rt for every State
returns: dataframe with state, rt
"""
def get_all_state_rt(avg=True):
    state_rt = pd.DataFrame(columns=['State', 'Rt'])
    for state in definitions.states.keys():
        data = get_state_hospitalizations(state_codes=[state], start_date=(pd.Timestamp.today() - pd.Timedelta(days=20)).date())
        if data.empty:
            rt = False
        else:
            rt= 1 + data.iloc[:,1].pct_change(periods=7)
            if(avg):
                y1 = rt.rolling(7).mean()
                rt = y1.iloc[-1]
            else:
                rt = rt.iloc[-1]
            state_rt = state_rt.append({"State":state, "Rt": float(rt)}, ignore_index=True)
    return state_rt
