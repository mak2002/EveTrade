import pandas as pd
import numpy as np
from datetime import datetime
from event import SignalEvent
from strategy import Strategy
import warnings

warnings.filterwarnings("ignore")

class MovingAverageCrossoverStrategy(Strategy):
    def __init__(self, data, events, short_window=40, long_window=100):
        self.data = data
        self.symbol_list = self.data.symbol_list
        self.events = events
        self.short_window = short_window
        self.long_window = long_window
        self.bought = self._calculate_initial_bought()

    def _calculate_initial_bought(self):
        bought = {}
        for symbol in self.symbol_list:
            bought[symbol] = 'OUT'
        return bought

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for symbol in self.symbol_list:
                bars = self.data.get_latest_bars(symbol, N=self.long_window)

                if bars is not None and len(bars) >= self.long_window:
                    df = pd.DataFrame(bars, columns=['Symbol', 'Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume', 'Industry', 'Sector'])
                    df.set_index('Date', inplace=True)

                    # print('2 row>>>>>>>',df.head(2))

                    short_mavg = df['Close'].rolling(window=self.short_window, min_periods=1).mean()
                    long_mavg = df['Close'].rolling(window=self.long_window, min_periods=1).mean()

                    symbol_bought = self.bought[symbol]
                    if short_mavg.iloc[-1] > long_mavg.iloc[-1] and symbol_bought == 'OUT':
                        signal = SignalEvent(symbol, df.index[-1], 'LONG', 10)
                        self.events.put(signal)
                        self.bought[symbol] = 'LONG'
                    elif short_mavg.iloc[-1] < long_mavg.iloc[-1] and symbol_bought == 'LONG':
                        signal = SignalEvent(symbol, df.index[-1], 'EXIT', 10)
                        self.events.put(signal)
                        self.bought[symbol] = 'OUT'

# Example usage:
# data = YourDataHandlerClass(...)
# events = YourEventQueueClass(...)
# strategy = MovingAverageCrossoverStrategy(data, events)
