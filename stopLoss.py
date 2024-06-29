import pandas as pd
import math
from datetime import datetime
from event import SignalEvent
from strategy import Strategy
import warnings
warnings.filterwarnings("ignore")
# from strategies.strategy import Strategy

class StopLossStrategy(Strategy):
    def __init__(self, data, events,short_period, portfolio):
        self.data = data
        self.symbol_list = self.data.symbol_list
        self.events = events
        self.portfolio = portfolio
        self.short_period = short_period

        self.name = 'Stop Loss'
        self.symbolDictionary = {}
        self.bought = self._calculate_initial_bought()
        self.signals = self._setup_signals()
        self.strategy = self._setup_strategy()
        self.bought = self._setup_initial_bought()

        self.stop_loss = self._set_initial_stop_loss()
        self.price_target = self.calculate_price_target()
        

        self.symbol_data = self._set_symbol_data()
        self.price_short_array = []

    def _setup_signals(self):
        signals = {}
        for symbol in self.symbol_list:
            signals[symbol] = pd.DataFrame(columns=['Date', 'Signal'])

        return signals

    def _setup_strategy(self):
        strategy = {}
        for symbol in self.symbol_list:
            strategy[symbol] = pd.DataFrame(columns=['Date', 'Short', 'Long'])

        return strategy

    def _setup_initial_bought(self):
        bought = {}
        for symbol in self.symbol_list:
            bought[symbol] = False

        return bought

    def _calculate_initial_bought(self):
        bought = {}
        for symbol in self.symbol_list:
            bought[symbol] = False

        return bought

    def _set_initial_stop_loss(self):
        stop_loss = {}
        for symbol in self.symbol_list:
            stop_loss[symbol] = 0

        return stop_loss
    
    def calculate_price_target(self):
        price_target = {}
        for symbol in self.symbol_list:
            price_target[symbol] = 0.0

        return price_target

    def _set_symbol_data(self):
        self.symbol_data = {}
        columns = ['Symbol','Date','Open','High','Low','Close','WAP','No. of Shares','No. of Trades','Total Turnover','Deliverable Quantity','% Deli. Qty to Traded Qty','Spread H-L','Spread C-O']

        drop_columns = ['WAP','No. of Shares','No. of Trades','Total Turnover','Deliverable Quantity','% Deli. Qty to Traded Qty','Spread H-L','Spread C-O']

        for symbol in self.symbol_list:
            self.symbolDictionary[symbol] = 1
            print('>>>>>>>>>>',symbol,self.symbolDictionary[symbol])
        
        for symbol in self.symbol_list:
            self.symbolDictionary[symbol] = pd.DataFrame(columns=columns)
            self.symbolDictionary[symbol].set_index('Date', inplace=True)
            # self.symbolDictionary[symbol] = self.symbolDictionary[symbol].drop(drop_columns, axis=1)

        return self.symbol_data

    def calculate_long_short(self, df):
        print('df:: ', df)
        price_short = None

        # price_short = df['Close'].ewm(span=self.short_period, min_periods=self.short_period, adjust=False).mean()[-1]

        # print('Dataframe rows',df.head)
        price_short = df[5].rolling(window= self.short_period, min_periods=self.short_period).mean().iat[-1]
        self.price_short_array.append(price_short)
        
        # print(len(df['Close']))
        # print('Closing Price',df['Close'].iat[-1])
        # print('Closing Price and Date and Symbol',df[5].iat[-1], df[1].iat[-1] , df[0].iat[-1])
        # print('Symbol Closing, Price and Date ',df[0].iat[-1], df[5].iat[-1] , df[1].iat[-1])
        price_short_percentage_high = price_short + price_short * 2.5/100
        price_short_percentage_low = price_short - price_short * 2/100

        return price_short, price_short_percentage_high, price_short_percentage_low, self.price_short_array
        # return price_short

        

    def calculate_signals(self, event):
        if event.type == 'MARKET':

            columns = ['Symbol','Date','Open','High','Low','Close','WAP','No. of Shares','No. of Trades','Total Turnover','Deliverable Quantity','% Deli. Qty to Traded Qty','Spread H-L','Spread C-O']

            drop_columns = ['WAP','No. of Shares','No. of Trades','Total Turnover','Deliverable Quantity','% Deli. Qty to Traded Qty','Spread H-L','Spread C-O']

            for symbol in self.symbol_list:

                data = self.data.get_latest_bars(symbol, N=1)
                print('Data:: ', data)

                self.symbolDictionary[symbol] = self.symbolDictionary[symbol].append(data)

                if data is not None and len(self.symbolDictionary[symbol]) >= self.short_period:

                    # set all conditions and set objects to strategy object

                    #---------------------------------------------------------------- 
                    price_short, price_short_percentage_high, price_short_percentage_low, price_short_array = self.calculate_long_short(self.symbolDictionary[symbol])
                    #---------------------------------------------------------------- 
                    date = self.symbolDictionary[symbol][1].iat[-1]

                    open_price_l = self.symbolDictionary[symbol][2].iat[-1]
                    high_price_l = self.symbolDictionary[symbol][3].iat[-1]
                    low_price_l = self.symbolDictionary[symbol][4].iat[-1]
                    close_price_l = self.symbolDictionary[symbol][5].iat[-1]

                    open_price = self.symbolDictionary[symbol][2].iat[-2]
                    high_price = self.symbolDictionary[symbol][3].iat[-2]
                    low_price = self.symbolDictionary[symbol][4].iat[-2]
                    close_price = self.symbolDictionary[symbol][5].iat[-2]


                    low_price2 = self.symbolDictionary[symbol][4].iat[-3]
                    close_price2 = self.symbolDictionary[symbol][5].iat[-3]
                    
                    # is_bullish =  close_price > open_price

                    min_price = min(open_price,high_price,low_price,close_price)
                    max_price = max(open_price,high_price,low_price,close_price)

                    self.strategy[symbol] = self.strategy[symbol].append({'Date': date, 'Short': price_short}, ignore_index=True)


                    condition1 = (open_price > price_short_percentage_high and low_price < price_short and low_price > price_short_percentage_high)#low > 44
                    condition2 = (open_price < price_short_percentage_high and close_price > open_price and close_price >= price_short)



                    condition3 = high_price_l > high_price

                    high_price_per = high_price + high_price * 0.2/100

                    condition5 = high_price_l > high_price_per

                    lenghtCondition = len(self.price_short_array) > 3

                    # if(len(price_short_array) > 3):
                        # print("date,",date,price_short_array)
                        # condition6 = price_short_array[-3] < price_short_array[-2] < price_short_array[-1] 
                    condition6 = lenghtCondition and self.price_short_array[-1] > self.price_short_array[-2] > self.price_short_array[-3]

                    exitCondition1 = (close_price >= self.price_target[symbol]) or (low_price >= self.price_target[symbol]) or (high_price >= self.price_target[symbol]) or (low_price >= self.price_target[symbol])
                                        

                    # if(condition6):
                    #     print("date,",date,self.price_short_array[-1],self.price_short_array[-3])
                        # print("date,",date,self.price_short_array[-1],self.)

                    # else:
                    #     condition6 = False
                    #     print("date,",date,price_short_array[-1],price_short_array[-3])
                    #     # print("date: ",date,price_short_array[-1])
                    #     pass

                    

                    # if(close_price_l > close_price > close_price2):
                    #     condition4 = True
                    # else:
                    #     condition4 = False
                    

                    risk_Amount = self.portfolio.current_holdings['cash'] / 2/100

                    entry_price = high_price_per
                    stop_loss = min(low_price_l,low_price)

                    # check all the conditions
                    if self.bought[symbol] == False and (condition1 or condition2) and condition5 and condition6:

                        # going long price
                        self.stop_loss[symbol] = stop_loss
                        quantity = risk_Amount/ (entry_price - stop_loss)
                        self.price_target[symbol] = entry_price + 2 * (entry_price - stop_loss)
                        signal = SignalEvent(symbol, date, 'LONG', quantity)
                        self.events.put(signal)
                        self.bought[symbol] = True
                        print("Long:", date, entry_price,symbol)
                        print("Stop Loss:", self.stop_loss[symbol])
                        # if self.verbose: print("Long", date, close_price)
                        # going long price

                    
                    elif self.bought[symbol] == True:
                        # exiting trade
                        if(high_price_l < self.stop_loss[symbol] > low_price_l):
                            quantity = self.portfolio.current_positions[symbol]
                            signal = SignalEvent(symbol, date, 'EXIT', quantity)
                            self.events.put(signal)
                            self.bought[symbol] = False
                            self.signals[symbol] = self.signals[symbol].append({'Signal': -quantity, 'Date': date}, ignore_index=True)
                            print("EXIT LOSS: ", date, low_price_l, self.stop_loss[symbol])
                            print("Price Target : ",self.price_target[symbol])
                            print()

                            self.price_target[symbol] = 0.0
                            self.stop_loss[symbol] = 0.0

                        elif(exitCondition1):
                        # elif(high_price_l < self.price_target[symbol] > low_price_l):
                        # elif(self.price_target[symbol]):
                            quantity = self.portfolio.current_positions[symbol]
                            signal = SignalEvent(symbol, date, 'EXIT', quantity)
                            self.events.put(signal)
                            self.bought[symbol] = False
                            self.signals[symbol] = self.signals[symbol].append({'Signal': -quantity, 'Date': date}, ignore_index=True)
                            print("EXIT PROFIT: ", date, high_price_l)
                            print("Price Target : ",self.price_target[symbol])
                            print()

                            self.price_target[symbol] = 0.0
                            self.stop_loss[symbol] = 0.0


                        # TO BE IMPLEMENTED:: trailing the stop loss
                        
                        # else:
                        #     data = self.data.get_latest_bars(symbol, N=2)
                        #     if data is not None and len(data) > 1:
                        #         if data[-1][self.data.price_col] > data[0][self.data.price_col] and self.stop_loss_percentage * data[-1][self.data.price_col] > self.stop_loss[symbol]:
                        #             self.stop_loss[symbol] = self.stop_loss_percentage * data[-1][self.data.price_col]