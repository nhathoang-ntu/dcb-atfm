import numpy as np
import pandas as pd

from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional

@dataclass(init=True, repr=True, eq=True)
class Facility:
    def __init__(
        self,
        name: str = None,
        id: int = None,
        time_slot: Optional[List] = None,
        demand_list: Optional[List[int]] = None,
        capacity: Optional[int] = None,
        capacity_list: Optional[List[int]] = None
    ):
        self.name = name
        self.id = id
        self.time_slot = time_slot
        self.demand_list = demand_list
        self._capacity = capacity
        self._capacity_list = capacity_list

    def calculate_capacity(
        self,
        demand_list: List[int] = None,
        peak_duration: int = 12,
        overload_percentage: float = 0.1
    ):
        demand_list = sorted(demand_list)
        average_demand = np.mean(demand_list[:peak_duration])
        self._capacity = int(average_demand / (1 + overload_percentage))
        self._capacity_list = [self._capacity] * len(self.time_slot)

    @property
    def capacity_list(self):
        if not self._capacity_list:
            self.calculate_capacity()
        return self._capacity_list
    
    @property
    def default_cpacity(self):
        return self._capacity

    @property
    def time_slot_ids(self):
        return self.time_slot
    