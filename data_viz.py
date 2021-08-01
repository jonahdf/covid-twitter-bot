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
    if(rolling):
        y1 = data.iloc[:,1].rolling(7).mean()
        ax.plot(x, y0, alpha=.3, color=plot_color)
        ax.plot(x, y1, color=plot_color)
        ax.fill_between(x, y1, 0, facecolor=plot_color, color=plot_color, alpha=0.2)
    else:
        ax.plot(x, y0, color=plot_color)
        ax.fill_between(x, y0, 0, facecolor=plot_color, color=plot_color, alpha=0.2)
    ax.set_title(label, fontdict={'size': 20})
    subtext = []
    for i in [-1,-2,-7]:
        last_update_day = x.iloc[i].strftime('%b-%d')
        last_val = round(y0.iloc[i], 1)
        last_val_formatted = '{:,}'.format(last_val)
        subtext.append(f" {last_update_day}: {last_val_formatted}")

    ax.text(.5, 0.97, subtext[0], ha='center', transform=ax.transAxes, fontdict=font)
    ax.text(.5, 0.94, subtext[1], ha='center',transform=ax.transAxes, fontdict=font)
    ax.text(.5, 0.91, subtext[2], ha='center',transform=ax.transAxes, fontdict=font)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b \'%y'))
    ax.grid(alpha=.4)
    ax.set_ylim(0)
    return ax


"""
plot_graphs
Plots 4 graphs with 7 day average lines
-Test positivity, cases, deaths, hospitalizations

region: Region to plot. Regions defined in definitions.py
start_date: Date to start plot
end_date: Date to end plot
"""
def plot_graphs(region="USA", start_date=pd.Timestamp(2020,3,1), end_date=pd.Timestamp.today()):
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


    fig, axs = plt.subplots(1,4, figsize=(25,10))
    plot(pos, axs[0], plot_color="purple", label=f"Test Positivity")
    plot(case, axs[1], plot_color="red", label=f"Cases")
    plot(hosp, axs[2], plot_color="blue", label=f"In Hospital")
    plot(death, axs[3], plot_color="black", label=f"Deaths")
    fig.autofmt_xdate()
    fig.suptitle(f"{region} COVID Data {end_date.strftime('%m/%d/%y')}", fontweight="bold", fontsize=23)
    plt.savefig(f"images/graphs/{region}.png", transparent=False, dpi=200, bbox_inches='tight', pad_inches=.1)
    print(f"LOG: Plotted graphs for {region}")
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
plot_graphs
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
    plot_table(death, axs[1][0], plot_color=("xkcd:purplish", "xkcd:light lavender"))
    plot_table(hosp, axs[1][1], plot_color=("xkcd:steel grey", "xkcd:light grey"))
    plot_table(pos, axs[0][1], plot_color=("xkcd:sea blue", "xkcd:pale blue"))
    fig.suptitle(f"{region} COVID Data {end_date.strftime('%m/%d/%y')}\n All Numbers are 7-day Rolling Averages", fontweight="bold")
    plt.savefig(f"images/tables/{region}.png", bbox_inches='tight', pad_inches=.1, facecolor='white')
    print(f"LOG: Plotted tables for {region}")