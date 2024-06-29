import datetime
import os, os.path
import pandas as pd
import mysql.connector

from abc import ABCMeta, abstractmethod

from event import MarketEvent

class DataHandler(object):
    """
    DataHandler is an abstract base class providing an interface for
    all subsequent (inherited) data handlers (both live and historic).

    The goal of a (derived) DataHandler object is to output a generated
    set of bars (OLHCVI) for each symbol requested. 

    This will replicate how a live strategy would function as current
    market data would be sent "down the pipe". Thus a historic and live
    system will be treated identically by the rest of the backtesting suite.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the latest_symbol list,
        or fewer if less bars are available.
        """
        raise NotImplementedError("Should implement get_latest_bars()")

    @abstractmethod
    def update_bars(self):
        """
        Pushes the latest bar to the latest symbol structure
        for all symbols in the symbol list.
        """
        raise NotImplementedError("Should implement update_bars()")

class HistoricCSVDataHandler(DataHandler):
    """
    HistoricCSVDataHandler is designed to read CSV files for
    each requested symbol from disk and provide an interface
    to obtain the "latest" bar in a manner identical to a live
    trading interface. 
    """


    def __init__(self, events ,csv_dir, symbol_list):
        """
        Initialises the historic data handler by requesting
        the location of the CSV files and a list of symbols.

        It will be assumed that all files are of the form
        'symbol.csv', where symbol is a string in the list.

        Parameters:
        events - The Event Queue.
        csv_dir - Absolute directory path to the CSV files.
        symbol_list - A list of symbol strings.
        """
        self.events = events
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list

        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continue_backtest = True       

        self._open_convert_csv_files()

    def _open_convert_csv_files(self):
        """
        Opens the CSV files from the data directory, converting
        them into pandas DataFrames within a symbol dictionary.

        For this handler it will be assumed that the data is
        taken from DTN IQFeed. Thus its format will be respected.
        """
        column_names = ['Date','Open','High','Low','Close', "Adj Close", 'Volume']
        # column_names = ['Date','Open','High','Low','Close','WAP','No. of Shares','No. of Trades','Total Turnover','Deliverable Quantity','% Deli. Qty to Traded Qty','Spread H-L','Spread C-O']
        
        comb_index = None
        for s in self.symbol_list:
            # Load the CSV file with no header information, indexed on date
            self.symbol_data[s] = pd.io.parsers.read_csv(
                                        os.path.join(self.csv_dir, '%s.csv' % s),
                                        header=0, index_col=0, 
                                        names= column_names
                                    )

            # Combine the index to pad forward values
            if comb_index is None:
                comb_index = self.symbol_data[s].index
            else:
                comb_index.union(self.symbol_data[s].index)

            self.latest_symbol_data[s] = []


        # Reindex the dataframes
        for s in self.symbol_list:
            self.symbol_data[s] = self.symbol_data[s].reindex(index=comb_index, method='pad').iterrows()

    def _get_new_bar(self, symbol):
            """
            Returns the latest bar from the data feed as a tuple of 
            (sybmbol, datetime, open, low, high, close, volume).
            """
            for b in self.symbol_data[symbol]:
                yield tuple([
                    symbol, datetime.datetime.strptime(b[0], '%Y-%m-%d').date(), b[1][0], b[1][1], b[1][2], b[1][3], b[1][4] , b[1][5]])

    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the latest_symbol list,
        or N-k if less available.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
            print('bars_list[-N:]', bars_list[-N:])
        except KeyError:
            print("That symbol is not available in the historical data set.")
        else:
            return bars_list[-N:]

    def update_bars(self):
        """
        Pushes the latest bar to the latest_symbol_data structure
        for all symbols in the symbol list.
        """
        for s in self.symbol_list:
            try:
                bar = self._get_new_bar(s).__next__()
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[s].append(bar)
        self.events.put(MarketEvent())


class HistoricMySQLDataHandler(DataHandler):
    """
    HistoricMySQLDataHandler is designed to read historical data for
    each requested symbol from a MySQL database and provide an interface
    to obtain the "latest" bar in a manner identical to a live
    trading interface. 
    """

    def __init__(self, events, db_config, symbol_list):
        """
        Initialises the historic data handler by requesting
        the database connection parameters and a list of symbols.

        Parameters:
        events - The Event Queue.
        db_config - A dictionary containing MySQL connection parameters.
        symbol_list - A list of symbol strings.
        """
        self.events = events
        self.db_config = db_config
        self.symbol_list = symbol_list

        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.symbol_generators = {}
        self.continue_backtest = True       

        self._open_convert_db_data()

    def _open_convert_db_data(self):
        """
        Opens the database connection, fetching historical data for each symbol
        and converting them into pandas DataFrames within a symbol dictionary.
        """
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor()

        for s in self.symbol_list:
            cursor.execute(f"SELECT * FROM {s}")
            rows = cursor.fetchall()

            # Ensure these column names match your database table column names
            columns = ['Date', 'open', 'high', 'low', 'close', 'adjClose', 'volume', 'industry', 'sector']

            df = pd.DataFrame(rows, columns=columns)
            df.set_index('Date', inplace=True)
            self.symbol_data[s] = df
            self.latest_symbol_data[s] = []
            self.symbol_generators[s] = self._create_symbol_generator(s)

        cursor.close()
        conn.close()

    def _create_symbol_generator(self, symbol):
        """
        Creates a generator that yields bars from the DataFrame.
        """
        for index, row in self.symbol_data[symbol].iterrows():
            yield tuple([
                symbol, index, row['open'], row['high'], row['low'], row['close'], row['adjClose'], row['volume'], row['industry'], row['sector']
            ])

    def _get_new_bar(self, symbol):
        """
        Returns the latest bar from the data feed as a tuple of 
        (symbol, datetime, open, low, high, close, adjClose, volume, industry, sector).
        """
        return next(self.symbol_generators[symbol], None)

    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the latest_symbol list,
        or N-k if less available.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
        else:
            return bars_list[-N:]

    def update_bars(self):
        """
        Pushes the latest bar to the latest_symbol_data structure
        for all symbols in the symbol list.
        """
        for s in self.symbol_list:
            bar = self._get_new_bar(s)
            print('bar', bar)
            if bar is not None:
                self.latest_symbol_data[s].append(bar)
            else:
                self.continue_backtest = False
        self.events.put(MarketEvent())