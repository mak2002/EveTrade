import numpy as np
import pandas as pd

def create_sharpe_ratio(returns, periods = 252):
    
    #Create the Sharpe ratio for the strategy, based on a 
    #benchmark of zero (i.e. no risk-free rate)
    
    #returns - a pandas series representing period percentage returns
    #period - daily (252), hourly (252*6.5), minutely (252*6.5*60)
    
    # print(returns)
    return (np.sqrt(periods) * np.mean(returns))/np.std(returns)

def create_drawdowns(equity_curve):
    
    #calculates the maximum drawdown: the largest peak to trough decline in equity curve
    #calculates the drawdown duration: the time over which this occured
    #equity_curve - a pandas series representing equity curve
    
    max_drawdown = equity_curve['equity_curve'].max() - equity_curve['equity_curve'].min()
    duration = abs(equity_curve['equity_curve'].argmax() - equity_curve['equity_curve'].argmin())
    
    return max_drawdown, duration
