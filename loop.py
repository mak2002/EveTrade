import queue
import time
import os, os.path
import datetime
import warnings
warnings.filterwarnings("ignore")

from event import (
    MarketEvent,
    SignalEvent,
    OrderEvent,
    FillEvent
)
from data import HistoricCSVDataHandler
# from strategy import BuyAndHoldStrategy
from portfolio import NaivePortfolio, Portfolio
from execution import SimulatedExecutionHandler
from stopLoss import StopLossStrategy

start_date = datetime.date(2019, 5, 5)

CSV_DIR = os.path.join('csvs')

event_queue = queue.Queue()

symbolList = ['BALRAMPUR CHINI MILLS  ']

data = HistoricCSVDataHandler(event_queue,CSV_DIR,symbolList)
portfolio = NaivePortfolio(data, event_queue, start_date,symbolList)
strategy = StopLossStrategy(data,event_queue,44,portfolio)
broker = SimulatedExecutionHandler(event_queue)

while True:
    if data.continue_backtest is True:
        # data.update_latest_data()
        data.update_bars()
    else:
        break

    while True:
        try:
            event = event_queue.get(block=False)
        except queue.Empty:
            break

        if event is not None:
            if isinstance(event, MarketEvent):
                strategy.calculate_signals(event)
                portfolio.update_timeindex(event)

            elif isinstance(event, SignalEvent):
                portfolio.update_signal(event)
                
            elif isinstance(event, OrderEvent):
                broker.execute_order(event)

            elif isinstance(event, FillEvent):
                portfolio.update_fill(event)

    stats = portfolio.output_summary_stats()    
    # time.sleep(10)

stats = portfolio.output_summary_stats()

print(stats)
