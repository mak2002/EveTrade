import datetime
import numpy as np
import pandas as pd
import queue

from abc import ABCMeta, abstractmethod
from math import floor

from event import FillEvent, OrderEvent, SignalEvent

from performance import create_sharpe_ratio, create_drawdowns

class Portfolio(object):
    """
    The Portfolio class handles the positions and market
    value of all instruments at a resolution of a "bar",
    i.e. secondly, minutely, 5-min, 30-min, 60 min or EOD.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def update_signal(self, event):
        """
        Acts on a SignalEvent to generate new orders 
        based on the portfolio logic.
        """
        raise NotImplementedError("Should implement update_signal()")

    @abstractmethod
    def update_fill(self, event):
        """
        Updates the portfolio current positions and holdings 
        from a FillEvent.
        """
        raise NotImplementedError("Should implement update_fill()")

class NaivePortfolio(Portfolio):
    """
    The NaivePortfolio object is designed to send orders to
    a brokerage object with a constant quantity size blindly,
    i.e. without any risk management or position sizing. It is
    used to test simpler strategies such as BuyAndHoldStrategy.
    """
    
    def __init__(self, data, events, start_date, symbolList, initial_capital=100000.0):
        """
        Initialises the portfolio with bars and an event queue. 
        Also includes a starting datetime index and initial capital 
        (USD unless otherwise stated).

        Parameters:
        data - The DataHandler object with current market data.
        events - The Event Queue object.
        start_date - The start date (bar) of the portfolio.
        initial_capital - The starting capital in USD.
        """
        self.events = events
        self.data = data
        self.start_date = start_date
        self.initial_capital = initial_capital

        self.symbolList = symbolList
        self.symbol_list = self.symbolList

        self.all_positions = self.construct_all_positions()
        self.current_positions = {symbol: 0 for symbol in self.symbol_list}

        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()
    
    def construct_all_positions(self):
        """
        Constructs the positions list using the start_date
        to determine when the time index will begin.
        """
        positions = {symbol: 0 for symbol in self.symbol_list}
        positions['datestamp'] = self.start_date
        return [positions]

    def construct_all_holdings(self):
        """
        Constructs the holdings list using the start_date
        to determine when the time index will begin.
        """

        holdings = {symbol: 0 for symbol in self.symbol_list}
        holdings['datestamp'] = self.start_date
        holdings['cash'] = self.initial_capital
        holdings['commission'] = 0
        holdings['total'] = self.initial_capital
        return [holdings]

    def construct_current_holdings(self):
        """
        This constructs the dictionary which will hold the instantaneous
        value of the portfolio across all symbols.
        """
        holdings = {symbol: 0 for symbol in self.symbol_list}
        holdings['cash'] = self.initial_capital
        holdings['commission'] = 0
        holdings['total'] = self.initial_capital
        return holdings

    def update_timeindex(self, event):
        """
        Adds a new record to the positions matrix for the current
        market data bar. This reflects the PREVIOUS bar, i.e. all
        current market data at this stage is known (OHLCV).
        Makes use of a MarketEvent from the events queue.
        """
        
        data = {s: self.data.get_latest_bars(s) for s in self.symbol_list}
        
        datestamp = data[self.symbol_list[0]][0][1]  #newest datestamp

       
        # Update positions
        # ================
        # Dictionary comprehension list with all symbol keys updated by current_positions values
        positions = {symbol: self.current_positions[symbol] for symbol in self.symbol_list}
        positions["datetime"] = datestamp
        # Append the current positions
        self.all_positions.append(positions)

        # Update holdings
        # ===============
        holdings = {symbol: 0.0 for symbol in self.symbol_list}
        holdings["datetime"] = datestamp
        holdings["cash"] = self.current_holdings["cash"]
        holdings["commission"] = self.current_holdings["commission"]
        holdings["total"] = self.current_holdings["cash"]

        # Update market value and pnl for all symbols
        # ==============
        for symbol in self.symbol_list:
            # Approximation to the real value --> market_value = adj close price * position_size
            market_value = self.current_positions[symbol] * data[symbol][0][3]
            holdings[symbol] = market_value

            # print(symbol,holdings[symbol])
            
            
            holdings["total"] += market_value

        # Append the current holdings
        
        self.all_holdings.append(holdings)

        
    
    def update_positions_from_fill(self, event):
        
        #Takes a FillEvent from the broker and updates current_positions dictionary by
        #adding/subtracting the correct quantity of shares
        
        #Check whether the fill was a buy or sell
        fill_dir = 0
        
        if event.direction == 'BUY':
            fill_dir = 1
        else:
            fill_dir = -1
            
        self.current_positions[event.symbol] += fill_dir * event.quantity
    
    def update_holdings_from_fill(self, event):
        #Takes a FillEvent from the broker and updates current_holdings dictionary by
        #adding/subtracting the correct cost
        #In reality a broker would give us the event.fill_cost - the price at which the trade was made
        #We will assume that the fill cost is the current adj. close price
        
        #Check whether the fill was a buy or sell
        fill_dir = 0
        
        if event.direction == 'BUY':
            fill_dir = 1
        else:
            fill_dir = -1
            
        fill_cost = self.data.get_latest_bars(event.symbol)[0][3]
        cost = fill_dir*fill_cost*event.quantity
        self.current_holdings[event.symbol] += cost   
        self.current_holdings['commission'] += event.commision
        self.current_holdings['cash'] -= (cost + event.commision)
        self.current_holdings['total'] -= (cost + event.commision)
    
    def update_fill(self, event):
        """
        Updates the portfolio current positions and holdings 
        from a FillEvent.
        """
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)

    def generate_naive_order(self, signal):
        """
        Simply files an Order object as a constant quantity
        sizing of the signal object
        Parameters:
        signal - The tuple containing Signal information.
        """
        order = None
        symbol = signal.symbol
        direction = signal.signal_type
        # strength = signal.strength
        strength = 1

        mkt_quantity = floor(100 * strength)
        current_quantity = self.current_positions[symbol]
        order_type = "MKT"

        if direction == "LONG" and current_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, "BUY")
        if direction == "SHORT" and current_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, "SELL")

        if direction == "EXIT" and current_quantity > 0:
            order = OrderEvent(symbol, order_type, abs(current_quantity), "SELL")
        if direction == "EXIT" and current_quantity < 0:
            order = OrderEvent(symbol, order_type, abs(current_quantity), "BUY")

        return order

    def update_signal(self, event):   
            #Receives a SignalEvent and creates an OrderEvent based on portfolio logic
            #and puts it in the queue
            
            if isinstance(event, SignalEvent):
                order = self.generate_naive_order(event)
                self.events.put(order)

    def create_equity_curve(self):
        #creates a dataframe from the all_holdings list of dictionaries

        curve = pd.DataFrame(self.all_holdings)
        curve.set_index('datestamp', inplace = True)
        
        #creates a new column which calculates the % change/100 from one datestamp to the next
        curve['returns'] = curve['total'].pct_change()
        
        #creates a new column which calculates the scaling from the initial captial to the total for each datestamp
        curve['equity_curve'] = (1.0 + curve['returns']).cumprod()

        return curve

    def output_summary_stats(self):
        
        
        #Returns a list of tuples
        
        self.equity_curve = self.create_equity_curve()
        total_return = self.equity_curve['equity_curve'][-1]
        returns = self.equity_curve['returns']

        equity_curve = self.equity_curve['equity_curve']
        
        sharpe_ratio = create_sharpe_ratio(returns)
        max_drawdown, duration = create_drawdowns(self.equity_curve)

        self.equity_curve["drawdown"] = max_drawdown

        stats = [('Total Return', '{}'.format((total_return - 1)*100)), 
                ('Sharpe Ratio', '{}'.format(sharpe_ratio)),
                ('Max Drawdown', '{}'.format(max_drawdown)),
                ('Drawdown Duration', '{}'.format(duration))]

        self.equity_curve.to_csv("equity.csv")
        
        return stats