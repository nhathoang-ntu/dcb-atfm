from copy import deepcopy
import numpy as np

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional


@dataclass(init=True, repr=True, eq=True)
class Plan:
    """
    Defines a plan of one flight.
    A plan is a pair of space-time coordinates of a flight at a specific time (in seconds) in a specific sector.
    A flight plan is a sequence of plans of a flight.
    - When the schedule of a flight changes, the entry and exit time of all plans will be updated accordingly.
    - When the route of a flight changes, longitude and latitude of some particular plans will be updated accordingly.
    - When the flight level of a flight changes, the altitude of some particular plans will be updated accordingly.

    This includes functions for:
    - Rescheduling (Re-allocating) the plan to a specific number of time slots.
    """
    call_sign: str
    facility: str
    time_entry: int
    time_exit: int
    altitude_entry: int
    altitude_exit: int
    longitude_entry: float
    longitude_exit: float
    latitude_entry: float
    latitude_exit: float
    runway_use: str = None      # can get values: 'departure', 'arrival'
    fir: str = None


    def reschedule(
        self, 
        num_timeslot: int
    ):
        """Rescheduling the plan to a specific number of time slots. This will change the entry and exit time of the plan.
        A plan can be rescheduled to the future or the past:
        - if num_timeslot > 0, delay the plan to later time slot(s).
        - if num_timeslot < 0, advance the plan to earlier time slot(s).

        Args:
            num_timeslot (int): The amount of time to re-schedule (re-allocate) the plan.

        Returns:
            None. Shifting inplace.
        """
        self.time_entry += num_timeslot
        self.time_exit += num_timeslot

    def to_dict(self):
        return vars(self)


@dataclass(init=True, repr=True, eq=True)
class FlightPlan:
    """Defines a flight plan. A flight plan is a sequence of plans of a flight.

    This includes functions for:
    - Adding the plan to the flight plan.
    - Rescheduling the plan to a specific number of time slots.
    """
    callsign: str
    flight_type: str = 'local'
    airline: str = callsign[:2]
    plans: List[Plan]

    def sorted(self, in_place=True):
        """Sort the plan of the flight plan in place

        Returns:
            Sorted plans if not sorted in place
        """
        sorted_plans = sorted(self.plans, key=lambda x: x.time_entry)
        if in_place:
            self.plans = sorted_plans
        else:
            return sorted_plans

    def add(self, 
            plan: Plan
    ):
        """Adds the plan into the flight plan.

        Args:
            plan (Plan): A specific Plan to add to the flight plan.

        Returns:
            None. Adding inplace.
        """
        if self.plans and plan.call_sign != self.plans[0].call_sign:
            raise ValueError('PLan is not in the same flight plan')

        self.plans.append(plan)
        self.sorted()

    def reschedule(
        self, 
        num_timeslot: int
    ):
        """Reschedule the flight a specific number of time slots.
        This function calls the reschedule method of each plan object.

       Args:
            num_timeslot (int): The number of time slots to reschedule the flight plan.

        Returns:
            None. Rescheduling inplace.
        """
        for plan in self.plans:
            plan.reschedule(num_timeslot)

    @property
    def call_sign(self) -> str:
        return self.plans[0].call_sign

    @property
    def start_time(self):
        return self.get_start_time()

    @property
    def end_time(self):
        return self.get_end_time()

    @property
    def time_period(self) -> Tuple[float, float]:
        return self.start_time, self.end_time

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    @property
    def facilities_passed(self) -> List[str]:
        return [plan.facility for plan in self.plans]

    @property
    def facility_entry_exit_times(self) -> List[Tuple[str, int, int]]:
        return [
            (plan.facility, plan.time_entry, plan.time_exit)
            for plan in self.plans
        ]

    @property
    def flight_type(self):
        if self.flight_type:
            return self.flight_type
        else:
            return (
                'local' if self.plans[0].runway_use == 'departure' and self.plans[-1].runway_use == 'arrival' else
                'outbound' if self.plans[0].runway_use == 'departure' else
                'inbound' if self.plans[-1].runway_use == 'arrival' else
                'unknown'
            )

    @property
    def num_facilities(self) -> int:
        return len(self.plans)

    @property
    def length(self) -> int:
        return len(self.plans)

    def get_start_time(self) -> float:
        return self.plans[0].time_entry

    def get_end_time(self) -> float:
        return self.plans[-1].time_exit

    def to_list(self):
        return [plan.to_dict() for plan in self.plans]

    def trim_runway(self):
        """Remove the runway plan from the flight plan."""
        obj_copy = deepcopy(self)
        if obj_copy.plans[0].runway_use:
            obj_copy.plans.pop(0)
        if obj_copy.plans[-1].runway_use:
            obj_copy.plans.pop(-1)

        return obj_copy

    def __len__(self):
        return len(self.plans)


@dataclass(init=True, repr=True, eq=True)
class EncodedFlightPlan:
    """
    The encoded format of the flight plan, to be used in the simulation.
    An original facilities and time slots are encoded as indexes (in a list) in the simulation.\n
    """
    # call sign of the flight plan
    callsign: str
    # The encoded call sign
    flight_id: int
    # The type of the flight, either 'local', 'inbound', 'outbound'
    flight_type: str
    # List of ids of the facilities the flight passes through
    facility_ids: List[int] = field(default_factory=list)
    # List of ids of the FIRs the flight passes through
    fir_ids: List[int] = field(default_factory=list)
    # List of time slot ids of the scenario the flight passes through
    time_slot_ids: np.ndarray = field(default_factory=lambda: np.array([]))
    # The sequence of time slot ids of the flight.
    flight_plan: Dict[int, np.ndarray] = field(default_factory=dict)

    # The original time slot of the flight. Used to calculate the different in schedule of the flight plan.
    original_time_slot: int = None
    # Departed
    departed: bool = False

    # Number of holdings of the flight, used in GDP
    num_hold: int = 0
    # Number of overcapacity slots that the flights passes through
    num_overcapacity: int = 0

    @property
    def id_pairs(self):
        """Returns the sequence of facility and time slot id pairs of the flight plan."""
        return self._get_facility_timeslot_id_pairs()

    def add_plan(
        self, 
        facility_id: int, 
        time_slot_ids: List[int]
    ) -> None:
        """Adds encoded plan to the actual plan.
        
        Args:
            facility_id (int): The sector id.
            time_slot_ids (List[int]): The list of time slot ids a flight in a sector.
            
        Returns:
            None.
        """
        self.time_slot_ids = np.append(self.time_slot_ids, np.array(time_slot_ids))
        # self.original_time_slot = self.time_slot_ids[0]
        self.facility_ids.extend([facility_id] * len(time_slot_ids))

        # Add the plan to the flight plan in dictionary, can be removed if unnecessary
        self.flight_plan[facility_id] = np.array(time_slot_ids)

    def advance(
        self, 
        num_timeslot: int
    ) -> Tuple[set, set]:
        """Shift BACKWARD the departure of the flight a specific time_slot_amount.
            a.k.a the flight departs EARLIER"""
        facilities_time_slots_former = set(zip(self.facility_ids, self.time_slot_ids))
        self.time_slot_ids -= num_timeslot

        facilities_time_slots_later = set(zip(self.facility_ids, self.time_slot_ids))

        decreasing_demand_facilities_time_slots = facilities_time_slots_former.difference(
            facilities_time_slots_later
        )
        increasing_demand_facilities_time_slots = facilities_time_slots_later.difference(
            facilities_time_slots_former
        )

        for facility in self.flight_plan:
            # Each value of facility in flight plans is the time slot ids,
            # the time slot ids are ascending by time.
            # Therefore, shifting is just substracting the time slot amount.
            self.flight_plan[facility] -= num_timeslot


        return decreasing_demand_facilities_time_slots, increasing_demand_facilities_time_slots

    def hold(
        self, 
        num_timeslot: int
    ) -> Tuple[set, set]:
        """Shift FORWARD the departure of the flight a specific time_slot_amount.
            a.k.a the flight departs LATER"""
        # Get the facility and time slot pairs before the shift
        facilities_time_slots_former = set(zip(self.facility_ids, self.time_slot_ids))
        self.time_slot_ids += num_timeslot

        # Get the facility and time slot pairs after the shift
        facilities_time_slots_later = set(zip(self.facility_ids, self.time_slot_ids))

        decreasing_demand_facilities_time_slots = facilities_time_slots_former.difference(
            facilities_time_slots_later
        )
        increasing_demand_facilities_time_slots = facilities_time_slots_later.difference(
            facilities_time_slots_former
        )

        for facility in self.flight_plan:
            # Each value of facility in flight plans is the time slot ids,
            # the time slot ids are ascending by time.
            # Therefore, shifting is just adding the time slot amount.
            self.flight_plan[facility] += num_timeslot

        return decreasing_demand_facilities_time_slots, increasing_demand_facilities_time_slots

    def depart(self):
        self.departed = True
        return self.id_pairs
    
    def reschedule(
        self, 
        num_timeslot:int,
        delay: bool = True
    ) -> None:
        """Reschedule the departure time of the flight a specific number of time slots.
        (This function is a wrapper of the advance and hold functions.)

        Args:
            num_timeslot (int): The number of time slots to rechedule the departure time.
            delay (bool): If True, the flight is delayed. If False, the flight is advanced.

        Returns:
            None.
        """
        if num_timeslot == 0:
            return
        
        if delay:
            self.hold(num_timeslot)
        else:
            self.advance(num_timeslot)

    def _get_facility_timeslot_id_pairs(self):
        # facility_id, timeslot_id pair
        return list(zip(self.facility_ids, self.time_slot_ids))

    def to_dict(self):
        return deepcopy(vars(self))

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, item):
        return getattr(self, item)

    @property
    def departure_time_slot(self):
        return self.time_slot_ids[0]
