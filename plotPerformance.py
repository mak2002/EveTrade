import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import datetime as dt

# Function to plot performance from equity curve saved in csv format
if __name__ == "__main__":
    data = pd.io.parsers.read_csv(
        "equity.csv", header=0, parse_dates=True, index_col=0)

    data['datetime'] = pd.to_datetime(data["datetime"], format="%Y/%m/%d")

    # y = data['equity_curve']

    # plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y'))
    # plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    # plt.plot(data['datetime'],data[''])
    # plt.show()
    # plt.gcf().autofmt_xdate()

    # date_array = data['datetime']
    # print(date_array)

    data["datetime"] = pd.to_datetime(data["datetime"], format="%Y/%m/%d")

    # data.set_index(['datetime'],inplace=True)
    # plt.plot(data)

    print(data.describe())

    # print(data['datetime'],data['drawdown'].describe())
    plt.plot(data['datetime'], data['drawdown'])
    plt.show()

    fig, (ax1, ax2, ax3) = plt.subplots(nrows=3, sharex=True)
    # Set the outer colour to white
    fig.patch.set_facecolor("white")
    # Plot the equity curve
    ax1.set_ylabel("Portfolio value, %")
    data["equity_curve"].plot(ax=ax1, color="blue", lw=2.)
    ax1.grid(True)
    # Plot the returns
    ax2.set_ylabel("Period returns, %")
    data["returns"].plot(ax=ax2, color="black", lw=2.)
    ax2.grid(True)
    # Plot the returns
    ax3.set_ylabel("Drawdowns, %")
    data["drawdown"].plot(ax=ax3, color="red", lw=2.)
    ax3.grid(True)

    plt.subplots_adjust(hspace=0.3)
    plt.show()
