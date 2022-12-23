# from _typeshed import Self

class Event(object):
    pass

class MarketEvent(Event):

    def __init__(self):
        self.type = 'MARKET'

class SignalEvent(Event):

    def __init__(self,symbol,datetime,signal_type,quantity):

        self.type = 'SIGNAL'
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type
        self.quantity = quantity

class OrderEvent(Event):

    def __init__(self,symbol,order_type,quantity,direction):
        
        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction

    def print_order(self):

        print("Order: Symbol=%s, Type=%s, Quantity=%s, Direction=%s") % \
            (self.symbol, self.order_type, self.quantity, self.direction)

class FillEvent(Event):

    def __init__(self,timeindex,symbol,exchange,quantity,direction,fill_cost, commision=True):

        self.type = 'FILL'
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost
        self.commision = commision

        if commision is None:
            self.commision = self._calculate_commision()
        else:
            self.commission = commision

    def _calculate_commision(self):
        """
        TODO: Commission fees to be implemented
        """
        # between 1 and 2%
        return max(1.5, 0.015 * self.quantity)