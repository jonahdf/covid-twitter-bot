import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path

matplotlib.use("Agg")
import matplotlib.dates as mdates
import data_processing as dp
import definitions
import math
import plotly.io as pio
import plotly.express as px
import kaleido

"""
plot_daily
Plots data with 7 day average

data: dataframe time series with column 'date' and data in 1st column
plot_color: Color to use for plot
label: string of plot label
rolling: Boolean, True to overlay 7-day average
"""


def plot_daily(
    data,
    ax=None,
    plot_color="blue",
    label="",
    rolling=True,
    font={"size": 13, "weight": "light"},
):
    ax = ax or plt.gca()
    x, y0 = data.date, data.iloc[:, 1]
    ax.margins(y=0.12, x=0.01)
    if rolling:
        # If graphing test positivity, make sure to use summed data as 7DA rather than each individual day's measurement
        if label == "Test Positivity":
            y1 = data.avg
        else:
            y1 = data.iloc[:, 1].rolling(7).mean()
        ax.plot(x, y0, alpha=0.3, color=plot_color)
        ax.plot(x, y1, color=plot_color)
        if not label == "Test Positivity":
            ax.fill_between(x, y1, 0, facecolor=plot_color, color=plot_color, alpha=0.2)
    else:
        ax.plot(x, y0, color=plot_color)
        if not label == "Test Positivity":
            ax.fill_between(x, y0, 0, facecolor=plot_color, color=plot_color, alpha=0.2)
    ax.set_title(label, fontdict={"size": 20}, color="black")
    subtext = []
    for i in [-1, -8]:
        last_update_day = x.iloc[i].strftime("%b-%d")
        last_val = round(y0.iloc[i], 1)
        last_val_formatted = "{:,}".format(last_val)
        subtext.append(f" {last_update_day}: {last_val_formatted}")
    if rolling:
        if label == "Test Positivity" or "per" in label:
            avg = round(y1.iloc[-1], 1)
        else:
            avg = int(round(y1.iloc[-1]))
        avg_formatted = "{:,}".format(avg)
        subtext.append(f" 7-day Average: {avg_formatted}")
    t = ax.text(
        0.5,
        0.88,
        "\n".join(subtext),
        ha="center",
        transform=ax.transAxes,
        fontdict=font,
        color="black",
    )
    t.set_bbox(dict(facecolor="white", alpha=0.9, edgecolor="black"))
    ax.set_ylim(0, y1.max() * 1.18)
    return ax


"""
plot_weekly
Plots data for weekly datasets

data: dataframe time series with column 'date' and data in 1st column
plot_color: Color to use for plot
label: string of plot label
rolling: Boolean, True to overlay 7-day average
"""


def plot_weekly(
    data, ax=None, plot_color="blue", label="", font={"size": 13, "weight": "light"}
):
    ax = ax or plt.gca()
    x, y0 = data.week_end_date, data.iloc[:, 2]
    ax.plot(x, y0, color=plot_color)
    ax.fill_between(x, y0, 0, facecolor=plot_color, color=plot_color, alpha=0.2)
    ax.set_title(label, fontdict={"size": 20}, color="black")
    subtext = []
    for i in [-1, -2]:
        last_update_day = x.iloc[i].strftime("%b-%d")
        last_val = round(y0.iloc[i], 1)
        last_val_formatted = "{:,}".format(last_val)
        subtext.append(f" Week ending on {last_update_day}: {last_val_formatted}")
    daily_avg = round((y0.iloc[i]) / 7, 1)
    daily_avg_formatted = "{:,}".format(daily_avg)
    subtext.append(f" Daily average: {daily_avg_formatted}")
    t = ax.text(
        0.5,
        0.88,
        "\n".join(subtext),
        ha="center",
        transform=ax.transAxes,
        fontdict=font,
        color="black",
    )
    t.set_bbox(dict(facecolor="white", alpha=0.9, edgecolor="black"))
    ax.set_ylim(0, y0.max() * 1.18)
    return ax


"""
plot_graphs
Plots 4 graphs with 7 day average lines
-Test positivity, cases, deaths, hospitalizations

region: Region to plot. Regions defined in definitions.py
start_date: Date to start plot
end_date: Date to end plot
"""


def plot_graphs(
    data,
    region="USA",
    start_date=pd.Timestamp(2020, 4, 1),
    end_date=pd.Timestamp.today(),
    path="",
):
    if region == "USA":
        pos = dp.get_us_positivity(data.test_data, start_date, end_date)
        case = dp.get_all_state_data_weekly(
            data.cdc_data, start_date, end_date, normalize=True, colName="new_cases"
        )
        death = dp.get_all_state_data_weekly(
            data.cdc_data, start_date, end_date, normalize=True, colName="new_deaths"
        )
        hosp = dp.get_us_hospitalizations(
            data.hospitalization_data, start_date, end_date, normalize=True
        )

    else:
        pos = dp.get_state_positivity(
            definitions.regions[region], data.test_data, start_date, end_date
        )
        case = dp.get_state_data_weekly(
            definitions.regions[region],
            data.cdc_data,
            start_date,
            end_date,
            normalize=True,
            colName="new_cases",
        )
        death = dp.get_state_data_weekly(
            definitions.regions[region],
            data.cdc_data,
            start_date,
            end_date,
            normalize=True,
            colName="new_deaths",
        )
        hosp = dp.get_state_hospitalizations(
            definitions.regions[region],
            data.hospitalization_data,
            start_date,
            end_date,
            normalize=True,
        )

    fig, axs = plt.subplots(2, 2, figsize=(20, 14))
    plot_daily(pos, axs[0][1], plot_color="purple", label="Test Positivity")
    plot_weekly(case, axs[0][0], plot_color="red", label="Weekly Cases per Million")
    plot_daily(hosp, axs[1][1], plot_color="blue", label="In Hospital per Million")
    plot_weekly(death, axs[1][0], plot_color="black", label="Weekly Deaths per Million")
    for ax in axs.flatten():
        ax.spines[:].set_linewidth(1)
        ax.spines[:].set_color("black")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
        ax.grid(alpha=0.4)
        ax.margins(y=0.12, x=0.01)
        ax.grid(True, color="gray", zorder=1)
        ax.set_facecolor("white")

    fig.set_facecolor("white")
    fig.suptitle(
        f"{region} COVID Data {end_date.strftime('%m/%d/%y')}",
        fontweight="bold",
        fontsize=23,
        color="black",
    )
    fig.tight_layout()
    plt.subplots_adjust(top=0.92)
    plt.draw()

    plt.savefig(
        f"{path}images/graphs/{region}.png",
        transparent=False,
        dpi=200,
        bbox_inches="tight",
        pad_inches=0.1,
        facecolor=fig.get_facecolor(),
    )
    print(f"LOG: Plotted graphs for {region}")
    plt.close(fig)


"""
plot_rt
Individual Rt plots using hospitalizations
"""


def plot_rt(
    data,
    ax=None,
    plot_color="black",
    font={"size": 13, "weight": "light"},
    showPeak=False,
):
    ax = ax or plt.gca()
    x, y0 = data.date, data.iloc[:, 1]
    ax.margins(y=0.12, x=0.03)

    y1 = data.iloc[:, 1].rolling(7).mean()
    ax.plot(x, y0, alpha=0.3, color=plot_color)
    ax.plot(x, y1, color=plot_color)
    # Fills between 1 and plot
    ax.fill_between(x, y1, 1, where=(y1 > 1), color="red", alpha=0.2)
    ax.fill_between(x, y1, 1, where=(y1 < 1), color="green", alpha=0.2)

    # Get numbers for today and last week
    subtext = []
    for i in [-1, -8]:
        last_update_day = x.iloc[i].strftime("%b-%d")
        last_val = round(y0.iloc[i], 2)
        last_val_formatted = "{:,}".format(last_val)
        subtext.append(f" {last_update_day}: {last_val_formatted}")

    # Find numbers for 7 day average and delta
    avg_formatted = round(y1.iloc[-1], 2)
    avg_delta = y1.iloc[-1] - y1.iloc[-2]
    avg_delta_formatted = round(avg_delta, 2)
    subtext.append(f" 7-day Average: {avg_formatted}")
    subtext.append(f" Change in 7-day Average from yesterday: {avg_delta_formatted}")
    # If region is US, calculate time to peak/trough
    if showPeak:
        avg_delta_diff, avg_delta_diff2 = 0, 0
        for i in range(1, 6):
            avg_delta_diff += y0.iloc[0 - i] - y0.iloc[0 - i - 1]
            avg_delta_diff2 += y1.iloc[0 - i] - y1.iloc[0 - i - 1]
        avg_delta_diff /= 5
        avg_delta_diff2 /= 5
        time_to_peak_opt = int(round((1 - y0.iloc[-2]) / avg_delta_diff))
        time_to_peak_con = int(round((1 - y1.iloc[-2]) / avg_delta_diff2))
        if (
            min(time_to_peak_opt, time_to_peak_con) < 0
            or max(time_to_peak_opt, time_to_peak_con) > 30
        ):
            subtext.append(f" Rough time to peak/trough: Unknown")
        else:
            subtext.append(
                f" Rough time to peak/trough at current rate: ~{round(sum([time_to_peak_opt,time_to_peak_con])/2)} days"
            )

    t = ax.text(
        0.5,
        0.84,
        "\n".join(subtext),
        ha="center",
        transform=ax.transAxes,
        fontdict=font,
    )
    t.set_bbox(dict(facecolor="white", alpha=0.7, edgecolor=None))

    ax.grid(alpha=0.4)
    ax.axhline(1, linestyle="--", color="black")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.set_xlabel(
        "* Dark line is 7-day average. Recent days might be artificially lower due to reporting"
    )
    if showPeak:
        ax.set_xlabel(
            "* Dark line is 7-day average. Recent days might be artificially lower due to reporting\n\nProjected peak is calculated using average change in last 5 days of Rt."
        )
    return ax


"""
generate_rt
Generates hospitalization reproduction rate image
"""


def generate_rt(
    datasets,
    region="USA",
    regionString=False,
    start_date=pd.Timestamp(2020, 9, 1),
    end_date=pd.Timestamp.today(),
    showPeak=False,
    path="",
):
    if not regionString:
        regionString = region
    label = f"{regionString} Weekly Growth in Hospitalizations"
    if region == "USA":
        data = dp.get_us_hospitalizations(
            dataset=datasets.hospitalization_data,
            start_date=start_date,
            end_date=end_date,
        )
        data["pct_chg"] = 1 + data.iloc[:, 1].pct_change(periods=7)
    else:
        if isinstance(region, list):
            data = dp.get_state_hospitalizations(
                state_codes=region,
                dataset=datasets.hospitalization_data,
                start_date=start_date,
                end_date=end_date,
            )
        else:
            data = dp.get_state_hospitalizations(
                state_codes=definitions.regions[region],
                dataset=datasets.hospitalization_data,
                start_date=start_date,
                end_date=end_date,
            )
        # data['avg'] = data.iloc[:,1].rolling(7).mean() # For double smoothing
        data["pct_chg"] = 1 + data.iloc[:, 1].pct_change(periods=7)

    fig, ax = plt.subplots(dpi=200, figsize=(15, 10))
    plot_rt(data[["date", "pct_chg"]], showPeak=showPeak)
    fig.autofmt_xdate()
    fig.suptitle(label, fontsize=24)
    plt.savefig(
        f"{path}images/rt/{region}.png",
        bbox_inches="tight",
        pad_inches=0.1,
        facecolor="white",
    )
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
    ax.axis("off")
    ax.axis("tight")
    # create table
    table = ax.table(
        cellText=data.values,
        colLabels=data.columns,
        cellLoc="center",
        loc="center",
        cellColours=[[plot_color[1]] * 3] * 7,
        colColours=[plot_color[0]] * 3,
    )


"""
get_table
Creates table as required in plot_table from dataframe

data: Dataframe of 2 columns: Date and metric (cases, deaths, etc)
name: Name for metric in table
"""


def get_table(
    data, name="cases", dateName="date", valColNum=1, dateColNum=0, daily=True
):
    if "Hospital" in name:
        data.iloc[:, valColNum] = data.iloc[:, valColNum].rolling(7).mean()
    if name == "Test Positivity":
        data.iloc[:, 1] = data.avg
    maxDate = data[dateName].max()
    recentNum = data[data[dateName] == maxDate].iloc[:, valColNum].item()
    if "Test Positivity" in name or "/" in name and "Cases" not in name:
        recentNumFormat = "{:,}".format(round(recentNum, 1))
    else:
        recentNumFormat = "{:,}".format(round(recentNum))
    lst = []
    newRow = {
        "Date": maxDate.strftime("%m/%d/%y"),
        name: recentNumFormat,
        "Change": "-",
    }
    lst.append(newRow)
    peakRow = data.iloc[:, valColNum].idxmax()
    peakDate = data.iloc[peakRow].iloc[dateColNum]
    peakDateFormat = peakDate.strftime("%m/%d/%y")
    if daily:
        RowsBackList = [
            ("1 wk ago", -7),
            ("2 wks ago", -14),
            ("1 mo ago", -30),
            ("2 mo ago", -60),
            ("1 yr ago", -365),
            (f"Peak ({peakDateFormat})", peakRow),
        ]
    else:
        RowsBackList = [
            ("1 wk ago", -2),
            ("2 wks ago", -3),
            ("1 mo ago", -5),
            ("2 mo ago", -9),
            ("1 yr ago", -53),
            (f"Peak ({peakDateFormat})", peakRow),
        ]

    for label, rowsBack in RowsBackList:
        newRow = data.iloc[rowsBack]
        newVal = newRow[valColNum]
        if newVal.size == 1:
            newVal = newVal.item()
        else:
            newVal = math.nan
        if not (math.isnan(newVal) or newVal == 0):
            if "Test Positivity" in name or "Million" in name and "Cases" not in name:
                numFormat = "{:,}".format(round(newVal, 1))
            else:
                numFormat = "{:,}".format(round(newVal))
            change = round(-1 * (1 - (recentNum / newVal)) * 100, 1)
        else:
            numFormat = "N/A"
            change = "N/A"

        newRow = {"Date": label, name: numFormat, "Change": f"{change}%"}
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


def plot_tables(
    datasets,
    region="USA",
    start_date=pd.Timestamp(2020, 1, 1),
    end_date=pd.Timestamp.today(),
    path="",
):
    if region == "USA":
        pos = get_table(
            dp.get_us_positivity(datasets.test_data, start_date, end_date),
            name="Test Positivity",
        )
        case = get_table(
            dp.get_all_state_data_weekly(
                datasets.cdc_data, start_date, end_date, colName="new_cases"
            ),
            name="Weekly Cases/Million",
            dateName="week_end_date",
            valColNum=2,
            dateColNum=1,
            daily=False,
        )
        death = get_table(
            dp.get_all_state_data_weekly(
                datasets.cdc_data, start_date, end_date, colName="new_deaths"
            ),
            name="Weekly Deaths/Million",
            dateName="week_end_date",
            valColNum=2,
            dateColNum=1,
            daily=False,
        )
        hosp = get_table(
            dp.get_us_hospitalizations(
                datasets.hospitalization_data, start_date, end_date
            ),
            name="In Hospital/Million",
        )
    else:
        pos = get_table(
            dp.get_state_positivity(
                definitions.regions[region], datasets.test_data, start_date, end_date
            ),
            name="Test Positivity",
        )
        case = get_table(
            dp.get_state_data_weekly(
                definitions.regions[region],
                datasets.cdc_data,
                start_date,
                end_date,
                colName="new_cases",
            ),
            name="Weekly Cases/Million",
            dateName="week_end_date",
            valColNum=2,
            dateColNum=1,
            daily=False,
        )
        death = get_table(
            dp.get_state_data_weekly(
                definitions.regions[region],
                datasets.cdc_data,
                start_date,
                end_date,
                colName="new_deaths",
            ),
            name="Weekly Deaths/Million",
            dateName="week_end_date",
            valColNum=2,
            dateColNum=1,
            daily=False,
        )
        hosp = get_table(
            dp.get_state_hospitalizations(
                definitions.regions[region],
                datasets.hospitalization_data,
                start_date,
                end_date,
            ),
            name="In Hospital/Million",
        )

    fig, axs = plt.subplots(
        2, 2, dpi=300, figsize=[6.4, 3.6], subplot_kw={"fc": "white"}
    )
    plt.subplots_adjust(wspace=0.05, hspace=0, bottom=0)
    plot_table(case, axs[0][0], plot_color=("xkcd:light red", "xkcd:pale pink"))
    plot_table(pos, axs[0][1], plot_color=("xkcd:purplish", "xkcd:light lavender"))
    plot_table(death, axs[1][0], plot_color=("xkcd:steel grey", "xkcd:light grey"))
    plot_table(hosp, axs[1][1], plot_color=("xkcd:sea blue", "xkcd:pale blue"))
    fig.suptitle(
        f"{region} COVID Data {end_date.strftime('%m/%d/%y')}\n Cases and deaths are weekly totals",
        fontweight="bold",
    )
    plt.savefig(
        f"{path}images/tables/{region}.png",
        bbox_inches="tight",
        pad_inches=0.1,
        facecolor="white",
    )
    print(f"LOG: Plotted tables for {region}")
    plt.close(fig)


def generate_maps(data, path=""):
    state_rt = dp.get_all_state_rt(dataset=data.hospitalization_data)
    state_hosps = dp.get_all_state_hosps(dataset=data.hospitalization_data)
    hosp_fig = px.choropleth(
        state_hosps,
        locations="State",
        locationmode="USA-states",
        color="Hospitalizations per Million",
        scope="usa",
        range_color=(0, 500),
        color_continuous_scale="YlOrRd",
    )
    hosp_fig.update_layout(
        title={
            "text": f"USA Hospitalizations per Million\n{pd.Timestamp.today().date()}",
            "y": 0.9,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        coloraxis_colorbar_title="",
        margin={"l": 0, "r": 0, "b": 0, "t": 0},
    )

    rt_fig = px.choropleth(
        state_rt,
        locations="State",
        locationmode="USA-states",
        color="Rt",
        scope="usa",
        color_continuous_scale="balance",
        color_continuous_midpoint=1,
        range_color=(0.7, 1.3),
    )
    rt_fig.update_layout(
        title={
            "text": f"USA Weekly Growth in Hospitalizations\n{pd.Timestamp.today().date()}",
            "y": 0.9,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        coloraxis_colorbar_title="Rt",
        margin={"l": 0, "r": 0, "b": 0, "t": 0},
    )
    pio.kaleido.scope.default_scale = 10
    rt_fig.write_image(f"{path}images/maps/rt.png")
    hosp_fig.write_image(f"{path}images/maps/hosp.png")
    print(f"LOG: Plotted maps")


"""
generate
generates all tables and graphs to post
 regions: List of regions (defined in definitions.regions)
"""
def generate(data, regions=definitions.regions.keys(), path=""):
    Path("./images/maps").mkdir(parents=True, exist_ok=True)
    Path("./images/tables").mkdir(parents=True, exist_ok=True)
    Path("./images/graphs").mkdir(parents=True, exist_ok=True)
    Path("./images/rt").mkdir(parents=True, exist_ok=True)

    generate_maps(data, path=path)
    start_date = pd.Timestamp(2020, 4, 1)
    for region in regions:
        plot_tables(data, region=region, path=path)
        plot_graphs(data, start_date=start_date, region=region, path=path)
        generate_rt(data, region=region, showPeak=False, path=path)
