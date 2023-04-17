import pandas as pd
from sodapy import Socrata
import datetime
import definitions


class DataSets:
    def __init__(self, to_csv=False, from_csv=False):
        self.cdc_data = self.get_cdc(from_csv)
        self.hospitalization_data = self.get_hosps(from_csv)
        self.test_data = self.get_tests(from_csv)
        if to_csv:
            self.write_csv()

    def get_cdc(self, from_csv):
        if from_csv:
            cdc_loaded = pd.read_csv("data/cdc.csv")
            cdc_loaded.start_date = pd.to_datetime(cdc_loaded.end_date)
            cdc_loaded.end_date = pd.to_datetime(cdc_loaded.end_date)
            return cdc_loaded

        cdc_client = Socrata("data.cdc.gov", None)
        cdc_state_raw = cdc_client.get(
            "pwn4-m3yp",
            select="state, start_date, end_date, new_cases, new_deaths",
            limit=2000000,
        )
        cdc_state_df = pd.DataFrame.from_records(cdc_state_raw)
        cdc_state_df.start_date = pd.to_datetime(cdc_state_df.start_date)
        cdc_state_df.end_date = pd.to_datetime(cdc_state_df.end_date)
        cdc_state_df.new_cases = cdc_state_df.new_cases.astype(float)
        cdc_state_df.new_deaths = cdc_state_df.new_deaths.astype(float)
        return cdc_state_df

    def get_hosps(self, from_csv):
        if from_csv:
            hhs_data_loaded = pd.read_csv("data/hosps.csv")
            hhs_data_loaded.date = pd.to_datetime(hhs_data_loaded.date)
            return hhs_data_loaded

        # Get raw data
        client = Socrata("healthdata.gov", None)
        hosp_results = client.get("g62h-syeh", limit=2000000)

        # Filter data to get columns of interest
        hhs_data = pd.DataFrame.from_records(hosp_results)[
            ["state", "date", "inpatient_beds_used_covid"]
        ]
        hhs_data.inpatient_beds_used_covid = hhs_data.inpatient_beds_used_covid.fillna(
            0
        )
        hhs_data = hhs_data.astype({"inpatient_beds_used_covid": "int32"})

        # For provisional data, gets days since most recent update of HHS time series
        max_date = hhs_data.date.max()
        provisional = client.get(
            "4cnb-m4rz", limit=2000000, where=("update_date > '" + max_date + "'")
        )
        hhs_provisional = pd.DataFrame.from_records(provisional)[
            ["update_date", "archive_link"]
        ]
        hhs_provisional.update_date = hhs_provisional.update_date.apply(
            lambda x: x[:10]
        )
        hhs_provisional.update_date = pd.to_datetime(hhs_provisional.update_date)

        # Gets last archive of every day
        group = hhs_provisional.groupby(["update_date"])
        hhs_provisional = group.last()

        # Add provisional data to HHS data
        frames = []
        for a in hhs_provisional.iterrows():
            date = a[0]
            url = a[1].item()["url"]
            df = pd.read_csv(url)[["state", "inpatient_beds_used_covid"]]
            df["date"] = date
            if date > pd.Timestamp(
                max_date
            ):  # Avoids double counting if provisional update came after real update
                frames.append(df)
        frames.append(hhs_data)
        hhs_data = pd.concat(frames)
        print("LOG: Added HHS Provisional data")
        return hhs_data

    def get_tests(self, from_csv):
        if from_csv:
            test_data_loaded = pd.read_csv("data/test.csv")
            test_data_loaded.date = pd.to_datetime(test_data_loaded.date)
            return test_data_loaded

        client = Socrata("healthdata.gov", None)
        test_results = client.get("j8mb-icvb", limit=2000000)
        test_data = pd.DataFrame.from_records(test_results)[
            ["state", "date", "overall_outcome", "new_results_reported"]
        ]
        test_data.new_results_reported = test_data.new_results_reported.fillna(0)
        test_data = test_data.astype({"new_results_reported": "int32"})
        return test_data

    def write_csv(self):
        self.hospitalization_data.to_csv("data/hosps.csv", index=False)
        self.test_data.to_csv("data/test.csv", index=False)
        self.cdc_data.to_csv("data/cdc.csv", index=False)
        print("LOG: Wrote to CSV")


# global_data = DataSets(from_csv=True)

"""
get_state_hospitalizations
"""


def get_state_hospitalizations(
    state_codes,
    dataset,
    start_date=pd.Timestamp(2020, 1, 1),
    end_date=pd.Timestamp.today(),
    normalize=True,
):
    curr_date = start_date
    state_data = dataset[dataset.state.isin(state_codes)]
    input_states = [definitions.states[s] for s in state_codes]
    max_date = state_data.date.max()
    states_population = sum([definitions.populations[s] for s in input_states])
    lst = []
    while curr_date <= end_date and curr_date <= max_date:
        day_data = state_data[state_data.date == str(curr_date)]
        if normalize:
            hosp_sum = (
                day_data.inpatient_beds_used_covid.sum() / states_population * 1000000
            )
        else:
            hosp_sum = day_data.inpatient_beds_used_covid.sum()
        newRow = {"date": curr_date, "hospitalizations": hosp_sum}
        lst.append(newRow)
        curr_date += datetime.timedelta(1)
    return pd.DataFrame(lst)


"""
get_us_hospitalizations
Same as above, hospitalizations
"""


def get_us_hospitalizations(
    dataset,
    start_date=pd.Timestamp(2020, 1, 1),
    end_date=pd.Timestamp.today(),
    normalize=True,
):
    curr_date = start_date
    max_date = dataset.date.max()
    lst = []
    while curr_date <= end_date and curr_date <= max_date:
        day_data = dataset[dataset.date == str(curr_date)]
        if normalize:
            hosp_sum = (
                day_data.inpatient_beds_used_covid.sum()
                / sum(definitions.populations.values())
                * 1000000
            )
        else:
            hosp_sum = day_data.inpatient_beds_used_covid.sum()
        newRow = {"date": curr_date, "inpatient_beds_used_covid": hosp_sum}
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


def get_state_positivity(
    state_codes,
    dataset,
    start_date=pd.Timestamp(2020, 1, 1),
    end_date=pd.Timestamp.today(),
):
    test_data_state = dataset[
        dataset.state.isin(state_codes)
    ]  # Get only data from input State
    max_date = test_data_state.date.max()
    curr_date = start_date
    lst = []
    while (
        curr_date <= end_date and curr_date <= max_date
    ):  # Loop through all unique dates
        day_data = test_data_state[test_data_state.date == str(curr_date)]
        test_pos = day_data[
            day_data.overall_outcome == "Positive"
        ].new_results_reported  # Get num positive tests
        test_pos = test_pos.sum() if test_pos.any() else 0  # Extract number if exists
        test_neg = day_data[
            day_data.overall_outcome == "Negative"
        ].new_results_reported  # Get num negative tests
        test_neg = test_neg.sum() if test_neg.any() else 0  # Extract number if exists
        if test_pos == 0 and test_neg == 0:
            test_pct = 0  # Fixes divide by zero issue
        else:
            test_pct = test_pos / (test_pos + test_neg) * 100
        newRow = {
            "date": curr_date,
            "test_positivity": test_pct,
            "positive_tests": test_pos,
            "negative_tests": test_neg,
        }
        lst.append(newRow)
        curr_date += datetime.timedelta(1)

    df = pd.DataFrame(lst)  # Create dataframe with all dates and test positivity
    a = df.rolling(7).sum()
    df["avg"] = a.apply(
        lambda x: (100 * (x.positive_tests / (x.positive_tests + x.negative_tests)))
        if (x.positive_tests + x.negative_tests) > 0
        else None,
        axis=1,
    )
    return df


"""
get_us_positivity
Constructs a data table of the entire US test positivity

start_date (datetime.date) : Starting date of table
end_date (datetime.date) : Ending date of table
returns: dataframe with date, test positivity

"""


def get_us_positivity(
    dataset, start_date=pd.Timestamp(2020, 1, 1), end_date=pd.Timestamp.today()
):
    curr_date = start_date
    max_date = dataset.date.max()
    lst = []
    while curr_date <= end_date and curr_date <= max_date:
        test_data_curr = dataset[dataset.date == str(curr_date)]
        test_pos = test_data_curr[
            test_data_curr.overall_outcome == "Positive"
        ].new_results_reported
        test_neg = test_data_curr[
            test_data_curr.overall_outcome == "Negative"
        ].new_results_reported
        pos_sum = test_pos.sum() if test_pos.any() else 0
        neg_sum = test_neg.sum() if test_pos.any() else 0
        test_positivity = (
            pos_sum / (pos_sum + neg_sum) * 100 if (pos_sum + neg_sum) > 0 else None
        )
        newRow = {
            "date": curr_date,
            "test_positivity": test_positivity,
            "positive_tests": pos_sum,
            "negative_tests": neg_sum,
        }
        lst.append(newRow)
        curr_date += datetime.timedelta(1)
    df = pd.DataFrame(lst)
    # Calculates 7-day averages of test positivity using sums over the window
    a = df.rolling(7).sum()
    df["avg"] = a.apply(
        lambda x: (100 * (x.positive_tests / (x.positive_tests + x.negative_tests)))
        if (x.positive_tests + x.negative_tests) > 0
        else None,
        axis=1,
    )
    return df


"""
get_all_state_hosps
Constructs a table of the most recent hospitalizations per capita for every State
returns: dataframe with state, hosp per million
"""


def get_all_state_hosps(dataset):
    state_hosps = pd.DataFrame(columns=["State", "Hospitalizations"])
    for state in definitions.states.keys():
        state_data = dataset[dataset.state.isin([state])]
        state_data = state_data[state_data["date"] <= pd.Timestamp.today()]
        hosps = state_data[
            state_data["date"] == state_data["date"].max()
        ].inpatient_beds_used_covid.values
        if not hosps:
            hosps = False
        else:
            hosps = (
                hosps[0] / definitions.populations[definitions.states[state]] * 1000000
            )
            state_hosps = state_hosps.append(
                {"State": state, "Hospitalizations per Million": float(hosps)},
                ignore_index=True,
            )
    return state_hosps


"""
get_all_state_rt
Constructs a table of the most recent rt for every State
returns: dataframe with state, rt
"""


def get_all_state_rt(dataset, avg=True):
    state_rt = pd.DataFrame(columns=["State", "Rt"])
    for state in definitions.states.keys():
        data = get_state_hospitalizations(
            state_codes=[state],
            dataset = dataset,
            start_date=(pd.Timestamp.today() - pd.Timedelta(days=20)).date(),
        )
        if data.empty:
            rt = False
        else:
            rt = 1 + data.iloc[:, 1].pct_change(periods=7)
            if avg:
                y1 = rt.rolling(7).mean()
                rt = y1.iloc[-1]
            else:
                rt = rt.iloc[-1]
            state_rt = state_rt.append(
                {"State": state, "Rt": float(rt)}, ignore_index=True
            )
    return state_rt


"""
get_state_data 
Creates dataframe of time series weekly date and data for given state
inputs:
 state_codes: List of 2-letter codes of states to query
 start_date (pd.Timestamp): starting date, defaults to 1-1-2020
 end_date (pd.Timestamp): ending date, defaults to today 
 normalize: boolean, whether to normalize by state population
 dataset: dataset to use, defaults to CDC dataset
 colName: Name of column containing data to add to dataframe
returns:
 df with 'week_start_date', 'week_end_date', and data
"""


def get_state_data_weekly(
    state_codes,
    dataset,
    start_date=pd.Timestamp(2020, 1, 1),
    end_date=pd.Timestamp.today(),
    normalize=True,
    colName="new_cases",
):
    curr_date = start_date
    input_states = [definitions.states[s] for s in state_codes]
    state_data = dataset[dataset.state.isin(state_codes)][:]
    max_date = state_data.end_date.max()
    states_population = sum([definitions.populations[s] for s in input_states])
    lst = []
    while curr_date <= end_date and curr_date <= max_date:
        if not (curr_date in state_data["end_date"].values):
            curr_date += datetime.timedelta(1)
            continue
        week_data = state_data[state_data.end_date == curr_date]
        if normalize:
            data_sum = week_data[colName].sum() / states_population * 1000000
        else:
            data_sum = week_data[colName].sum()
        newRow = {
            "week_start_date": curr_date - datetime.timedelta(6),
            "week_end_date": curr_date,
            colName: data_sum,
        }
        lst.append(newRow)
        curr_date += datetime.timedelta(1)
    return pd.DataFrame(lst)


"""
get_all_state_data 
Creates dataframe of time series weekly date and data for all USA combined
inputs:
 start_date (pd.Timestamp): starting date, defaults to 1-1-2020
 end_date (pd.Timestamp): ending date, defaults to today 
 normalize: boolean, whether to normalize by state population
 dataset: dataset to use, defaults to CDC dataset
 colName: Name of column containing data to add to dataframe
returns:
 df with 'week_start_date', 'week_end_date', and data
"""


def get_all_state_data_weekly(
    dataset,
    start_date=pd.Timestamp(2020, 1, 1),
    end_date=pd.Timestamp.today(),
    normalize=True,
    colName="new_cases",
):
    return get_state_data_weekly(
        definitions.states.keys(), dataset, start_date, end_date, normalize, colName
    )
