This event driven backtester is based on guide on QuantStart. 

Code provided in QuantStart's guide does not run directly and modifications were done by me in order to execute it.


`loop.py` is the main Python program from which backtester is initialized.

`event.py` Contains 4 types of events, namely MARKET, SIGNAL, ORDER, FILL events. They use event queue in order to communicate with other components.

`execution.py` converts all OrderEvents to FillEvents with no latency or slippage.

`Performance.py` implements matrics like sharpe ratio and drawdowns.

`plotPerformance.py` plots charts like equity curve, backtesting results.

`portfolio.py` that keeps track of the positions within a portfolio.

`strategy.py` generates a signal event from custom strategy to place the orders.


This project is for educational purposes only.