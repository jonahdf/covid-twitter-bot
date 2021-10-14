import pandas as pd
import matplotlib.pyplot as plt
import datetime
import matplotlib.dates as mdates
import data_processing as dp
import definitions
import math


"""
plot
Plots data with 7 day average

data: dataframe time series with column 'date' and data in 1st column
plot_color: Color to use for plot
label: string of plot label
rolling: Boolean, True to overlay 7-day average
"""
def plot(data, ax=None, plot_color="blue", label="", rolling=True, font={ 'size':13, 'weight':'light'}):
    ax = ax or plt.gca()
    x, y0 = data.date, data.iloc[:,1]
    ax.margins(y=.12, x=.01)
    if(rolling):
        # If graphing test positivity, make sure to use summed data as 7DA rather than each individual day's measurement
        if label == "Test Positivity":
            y1 = data.avg
        else:
            y1 = data.iloc[:,1].rolling(7).mean()
        ax.plot(x, y0, alpha=.3, color=plot_color)
        ax.plot(x, y1, color=plot_color)
        ax.fill_between(x, y1, 0, facecolor=plot_color, color=plot_color, alpha=0.2)
    else:
        ax.plot(x, y0, color=plot_color)
        ax.fill_between(x, y0, 0, facecolor=plot_color, color=plot_color, alpha=0.2)
    ax.set_title(label, fontdict={'size': 20})
    subtext = []
    for i in [-1,-8]:
        last_update_day = x.iloc[i].strftime('%b-%d')
        last_val = round(y0.iloc[i], 1)
        last_val_formatted = '{:,}'.format(last_val)
        subtext.append(f" {last_update_day}: {last_val_formatted}")
    ax.text(.5, 0.96, subtext[0], ha='center', transform=ax.transAxes, fontdict=font)
    ax.text(.5, 0.92, subtext[1], ha='center',transform=ax.transAxes, fontdict=font)
    if rolling:
        if label == "Test Positivity":
            avg = round(y1.iloc[-1], 1)
        else:
            avg = int(round(y1.iloc[-1]))
        avg_formatted = '{:,}'.format(avg)
        subtext.append(f" 7-day Average: {avg_formatted}")
        ax.text(.5, 0.88, subtext[2], ha='center',transform=ax.transAxes, fontdict=font)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b \'%y'))
    ax.grid(alpha=.4)
    ax.set_ylim(0, y1.max()*1.18)
    return ax


"""
plot_graphs
Plots 4 graphs with 7 day average lines
-Test positivity, cases, deaths, hospitalizations

region: Region to plot. Regions defined in definitions.py
start_date: Date to start plot
end_date: Date to end plot
"""
def plot_graphs(region="USA", start_date=pd.Timestamp(2020,4,1), end_date=pd.Timestamp.today()):
    if region == "USA":
        pos = dp.get_us_positivity(start_date, end_date)
        case = dp.get_us_cases(start_date, end_date)
        death = dp.get_us_deaths(start_date, end_date)
        hosp = dp.get_us_hospitalizations(start_date, end_date)
    else:
        pos = dp.get_state_positivity(definitions.regions[region], start_date, end_date)
        case = dp.get_state_cases(definitions.regions[region], start_date, end_date)
        death = dp.get_state_deaths(definitions.regions[region], start_date, end_date)
        hosp = dp.get_state_hospitalizations(definitions.regions[region], start_date, end_date)


    fig, axs = plt.subplots(2,2, figsize=(20,14))
    plot(pos, axs[0][1], plot_color="purple", label=f"Test Positivity")
    plot(case, axs[0][0], plot_color="red", label=f"Cases")
    plot(hosp, axs[1][1], plot_color="blue", label=f"In Hospital")
    plot(death, axs[1][0], plot_color="black", label=f"Deaths")
    # fig.autofmt_xdate()
    fig.patch.set_facecolor('white')
    fig.suptitle(f"{region} COVID Data {end_date.strftime('%m/%d/%y')}", fontweight="bold", fontsize=23)
    fig.tight_layout()
    plt.subplots_adjust(top=0.92)
    plt.savefig(f"images/graphs/{region}.png", transparent=False, dpi=200, bbox_inches='tight', pad_inches=.1)
    print(f"LOG: Plotted graphs for {region}")
    plt.close(fig)



"""
plot_rt
Individual Rt plots using hospitalizations
"""
def plot_rt(data, ax=None, plot_color="black", font={ 'size':13, 'weight':'light'}, showPeak=False):
    ax = ax or plt.gca()
    x, y0 = data.date, data.iloc[:,1]
    ax.margins(y=.12, x=.03)

    y1 = data.iloc[:,1].rolling(7).mean()
    ax.plot(x, y0, alpha=.3, color=plot_color)
    ax.plot(x, y1, color=plot_color)
    # Fills between 1 and plot
    ax.fill_between(x, y1, 1, where=(y1>1), color='red', alpha=0.2)
    ax.fill_between(x, y1, 1, where=(y1<1), color='green', alpha=0.2)
    
    # Get numbers for today and last week
    subtext = []
    for i in [-1,-8]:
        last_update_day = x.iloc[i].strftime('%b-%d')
        last_val = round(y0.iloc[i], 2)
        last_val_formatted = '{:,}'.format(last_val)
        subtext.append(f" {last_update_day}: {last_val_formatted}")
    ax.text(.5, 0.97, subtext[0], ha='center', transform=ax.transAxes, fontdict=font)
    ax.text(.5, 0.94, subtext[1], ha='center',transform=ax.transAxes, fontdict=font)
    
    # Find numbers for 7 day average and delta
    avg_formatted = round(y1.iloc[-1],2)
    avg_delta = y1.iloc[-1] - y1.iloc[-2]
    avg_delta_formatted = round(avg_delta,2)
    subtext.append(f" 7-day Average: {avg_formatted}")
    subtext.append(f" Change in 7-day Average from yesterday: {avg_delta_formatted}")
    # If region is US, calculate time to peak/trough
    if(showPeak):
        avg_delta_diff, avg_delta_diff2 = 0,0
        for i in range(1,6):
            avg_delta_diff += y0.iloc[0-i] - y0.iloc[0-i-1]
            avg_delta_diff2 += y1.iloc[0-i] - y1.iloc[0-i-1]
        avg_delta_diff /= 5
        avg_delta_diff2 /= 5
        time_to_peak_opt = int(round((1 - y0.iloc[-2]) / avg_delta_diff))
        time_to_peak_con = int(round((1 - y1.iloc[-2]) / avg_delta_diff2))
        if(min(time_to_peak_opt,time_to_peak_con) < 0 or max(time_to_peak_opt,time_to_peak_con) > 30):
            subtext.append(f" Rough time to peak/trough: Unknown")
        else:
            subtext.append(f" Rough time to peak/trough at current rate: ~{round(sum([time_to_peak_opt,time_to_peak_con])/2)} days")
        ax.text(.5, 0.85, subtext[4], ha='center',transform=ax.transAxes, fontdict=font)

    ax.text(.5, 0.91, subtext[2], ha='center',transform=ax.transAxes, fontdict=font)
    ax.text(.5, 0.88, subtext[3], ha='center',transform=ax.transAxes, fontdict=font)

    ax.grid(alpha=.4)
    ax.axhline(1, linestyle="--", color='black')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b \'%y'))
    ax.set_xlabel("* Dark line is 7-day average. Recent days might be artificially lower due to reporting")
    if(showPeak):
        ax.set_xlabel("* Dark line is 7-day average. Recent days might be artificially lower due to reporting\n\nProjected peak is calculated using average change in last 5 days of Rt.")
    return ax
"""
generate_rt
Generates hospitalization reproduction rate image
"""
def generate_rt(region="USA", regionString=False, start_date=pd.Timestamp(2020,9,1), end_date=pd.Timestamp.today(), showPeak=False):
    if(not regionString):
        regionString = region
    label=f"{regionString} Weekly Growth in Hospitalizations"
    if(region == "USA"):
        data = dp.get_us_hospitalizations(start_date=start_date, end_date=end_date)
        data['pct_chg'] = 1 + data.iloc[:,1].pct_change(periods=7)
    else:
        if(isinstance(region, list)):
            data= dp.get_state_hospitalizations(state_codes=region, start_date=start_date, end_date=end_date)
        else:
            data = dp.get_state_hospitalizations(state_codes=definitions.regions[region], start_date=start_date, end_date=end_date)
        # data['avg'] = data.iloc[:,1].rolling(7).mean() # For double smoothing
        data['pct_chg'] = 1 + data.iloc[:,1].pct_change(periods=7)
    
    fig,ax = plt.subplots(dpi=100, figsize=(15,10))
    plot_rt(data[['date', 'pct_chg']], showPeak=showPeak)
    fig.autofmt_xdate()
    fig.suptitle(label, fontsize=24)
    plt.savefig(f"images/rt/{region}.png", bbox_inches='tight', pad_inches=.1, facecolor='white')
    print(f"LOG: Plotted rt for {region}")
    plt.close(fig)

"""
plot_table
Plots table of input data. Data must be 3 x 7

data: Dataframe of 3 columns, 7 rows. Extracted in get_table below
ax: Axis to draw the table on
plot_color: 2-tuple of the header color, cell color
"""
def plot_table(data, ax=None, plot_color=("xkcd:light red", "xkcd:pale pink")):
    ax.axis('off')
    ax.axis('tight')
    #create table
    table = ax.table(cellText=data.values, colLabels=data.columns, cellLoc='center', loc='center', cellColours=[[plot_color[1]]*3]*7, colColours=[plot_color[0]]*3)


"""
get_table
Creates table as required in plot_table from dataframe

data: Dataframe of 2 columns: Date and metric (cases, deaths, etc)
name: Name for metric in table
"""
def get_table(data, name="cases"):
    data.iloc[:,1] = data.iloc[:,1].rolling(7).mean()
    if name == "Test Positivity":
        data.iloc[:,1] = data.avg
    maxDate = data['date'].max()
    recentNum = data[data.date == maxDate].iloc[:,1].item()
    if "Test Positivity" in name:
        recentNumFormat = round(recentNum,1)
    else:
        recentNumFormat = '{:,}'.format(round(recentNum))
    lst = []
    newRow = {'Date': maxDate.strftime("%m/%d/%y"), name: recentNumFormat, 'Change': '-'}
    lst.append(newRow)
    peakRow = data.iloc[:,1].idxmax()
    peakDate = data.iloc[peakRow].iloc[0]
    peakDaysBack = (peakDate - maxDate).days
    peakDateFormat = peakDate.strftime("%m/%d/%y")
    for label, daysBack in [("1 wk ago", -7), ("2 wks ago", -14), ("1 mo ago", -30), ("2 mo ago", -60), ("1 yr ago", -365), (f"Peak ({peakDateFormat})", peakDaysBack)]:
        newDate = (maxDate + datetime.timedelta(daysBack))
        newNum = data[data.date == newDate].iloc[:,1]
        if(newNum.size == 1):
            newNum = newNum.item()
        else:
            newNum = math.nan
        if not math.isnan(newNum):
            if "Test Positivity" in name:
                numFormat = round(newNum,1)
            else:
                numFormat = '{:,}'.format(round(newNum))
            change = round(-1 * (1 - (recentNum / newNum)) * 100, 1)
        else:
            numFormat = "N/A"
            change = "N/A"

        newRow = {'Date': label, name: numFormat, 'Change': f"{change}%"}
        lst.append(newRow)
    return pd.DataFrame(lst)


"""
plot_tables
Plots 4 tables with 7 day averages for timeframes and peak
-Test positivity, cases, deaths, hospitalizations

region: Region to plot. Regions defined in definitions.py
start_date: Date to start plot
end_date: Date to end plot
"""
def plot_tables(region="USA", start_date=pd.Timestamp(2020,1,1), end_date=pd.Timestamp.today()):
    if region == "USA":
        pos = get_table(dp.get_us_positivity(start_date, end_date), name="Test Positivity")
        case = get_table(dp.get_us_cases(start_date, end_date), name="Cases")
        death = get_table(dp.get_us_deaths(start_date, end_date), name="Deaths")
        hosp = get_table(dp.get_us_hospitalizations(start_date, end_date), name="In Hospital")
    else:
        pos = get_table(dp.get_state_positivity(definitions.regions[region], start_date, end_date), name="Test Positivity")
        case = get_table(dp.get_state_cases(definitions.regions[region], start_date, end_date), name="Cases")
        death = get_table(dp.get_state_deaths(definitions.regions[region], start_date, end_date), name="Deaths")
        hosp = get_table(dp.get_state_hospitalizations(definitions.regions[region], start_date, end_date), name="In Hospital")

    fig, axs = plt.subplots(2,2, dpi=300, figsize=[6.4,3.6], subplot_kw={'fc':'white'})
    plt.subplots_adjust(wspace=0.05, hspace=0, bottom=0)
    plot_table(case, axs[0][0], plot_color=("xkcd:light red", "xkcd:pale pink"))
    plot_table(pos, axs[0][1], plot_color=("xkcd:purplish", "xkcd:light lavender"))
    plot_table(death, axs[1][0], plot_color=("xkcd:steel grey", "xkcd:light grey"))
    plot_table(hosp, axs[1][1], plot_color=("xkcd:sea blue", "xkcd:pale blue"))
    fig.suptitle(f"{region} COVID Data {end_date.strftime('%m/%d/%y')}\n All Numbers are 7-day Rolling Averages", fontweight="bold")
    plt.savefig(f"images/tables/{region}.png", bbox_inches='tight', pad_inches=.1, facecolor='white')
    print(f"LOG: Plotted tables for {region}")
    plt.close(fig)

"""
generate
generates all tables and graphs to post
 regions: List of regions (defined in definitions.regions)
"""
def generate(regions = definitions.regions.keys()):
    for region in regions:
        plot_tables(region=region)
        plot_graphs(region=region)
        generate_rt(region=region, showPeak=True)
