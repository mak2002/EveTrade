import datetime
import queue

from abc import ABCMeta, abstractmethod

from event import FillEvent, OrderEvent



class ExecutionAbstractClass(metaclass = ABCMeta):
    #Abstract class providing an interface for all inherited strategy objects
    
    @abstractmethod
    def execute_order(self, event):
        pass

class SimulatedExecutionHandler(ExecutionAbstractClass):
    
    #Simply converts all OrderEvents to FillEvents with no latency or slippage
    
    def __init__(self, event_queue):
        self.event_queue = event_queue
        self.i = 0
    
        
    def execute_order(self, event):
        
        #the fill_cost is set to None as this is accounted for in the NaivePortfolio
        
        if isinstance(event, OrderEvent):
            fill_event = FillEvent(datetime.datetime.utcnow(), event.symbol, "EXCHANGE", event.quantity, event.direction, None)
            self.event_queue.put(fill_event)