import logging
from copy import deepcopy
from typing import Dict, Iterable, List, Set, Tuple, Optional

import numpy as np
import pandas as pd
from intervaltree import Interval, IntervalTree

from abstract.flightplan import FlightPlan, EncodedFlightPlan
from utility.plan_extractor import FlightPlanExtractor


logger = logging.getLogger(__name__)
class DCBBaseEnv:
    def __init__(
        self,
        time_slot_duration: int = 900,
        max_advance_num: int = 6,
        max_delay_num: int = 6,
        default_capacity_num: int = 10,
        capacity_matrix: Optional[Dict[Tuple[int, int], int]] = None,
    ):
        
        # Input data attributes
        # TODO: later on the scenarios or a set of scenarios should be the input to the DCBEnv
        self.data_file_path: Optional[str] = None  # Set in the self._init_from_csv method
        self.flight_plans: Optional[Dict[str, FlightPlan]] = None  # Set in the self._init_from_flight_plan_dict method

        # Required environment attributes
        self.time_slot_duration = time_slot_duration  # in seconds, the duration of one time slot (typically 15 minutes (900 seconds))
        self.max_advance_num = max_advance_num  # in integer, the maximum number of time slots a flight can be advanced
        self.max_delay_num = max_delay_num  # in integer, the maximum number of time slots a flight can be delayed

        self.default_capacity_num = default_capacity_num  # The flat capacity constraint, same for all facilities
        self.capacity_matrix = capacity_matrix  # The capacity constraint matrix



        # Data attributes extracted from input data
        # Flight attributes
        # List of flights, set in the self._init_from_flight_plan_dict method
        self.flights: Optional[List[str]] = None
        # List of flight_ids, set in the self._init_from_flight_plan_dict method
        self.flight_ids: Optional[List[int]] = None
        self.call_sign_id_mappings: Optional[Dict[str, int]] # Mapping of call signs to ids
        # Facility attributes
        self.facilities: Optional[List[str]] = None  # List of facilities
        self.facility_ids: Optional[List[int]] = None  # List of facility ids
        self.facility_id_mappings: Optional[Dict[str, int]] = None  # Mappings of facility and its ID
        # Timeslot attributes
        self.time_slots: Optional[List[Interval]] = None  # List of time slot intervals
        self.time_slot_ids: Optional[List[int]] = None  # List of time slot ids
        self.time_slot_id_mappings: Optional[Dict[Interval, int]] = None  # Mappings of timeslot and its ID
        # The planned departure order of flight based on timeslot.
        #  Keys are timeslots. Values are lists of flight departure in that timeslot.
        self.time_slot_departure_order: Optional[Dict[int, List[str]]] = None

        # Data structure of the environment
        # The encoded flight plan based on facility ids and time slot ids
        self.encoded_flight_plans: Optional[Dict[str, EncodedFlightPlan]] = None
        # The matrix of computed actual demand per facility per timeslot
        self.actual_demand_matrix_computed: Optional[Dict[Tuple[int, int], int]] = None
        # The underlying data structure for searching time slot
        self.time_slot_interval_tree: Optional[IntervalTree] = None

        # Caches of data structure
        # Four data structure need to be cached:
        # - encoded_flight_plans
        # A cached encoded flight plan
        self._cached_encoded_flight_plans: Optional[Dict[str, EncodedFlightPlan]] = None
        # A Cache time_slot_departure_order
        self._cached_time_slot_departure_order: Optional[Dict[int, List[int]]] = None

        # A dict of overcapacity facilities, timeslots and the number of overcapacity
        self.overcapacity_matrix: Optional[Dict[Tuple[int, int], int]] = None
        # Environment scoring attributes
        # Score of the DCB problems
        self.total_overcapacity: Optional[int] = None

        # Optional environment attributes
        # The capacity constraint for each facility and time slot.
        # The facility and time slot are encoded by ID.
        self.capacity_constraint_matrix: Optional[Dict[Tuple[int, int], int]] = None

        # Helper attributes
        # start of time slot range, timestamp, in python is float, need to convert to int
        self.start_timestamp: Optional[int] = None
        # end of the time slot range, timestamp, in python is float, need to convert to int
        self.end_timestamp: Optional[int] = None

    def _set_scenarios_start_end_time(self):
        flight_plans_list = self.flight_plans.values()
        self.start_timestamp = min(
            flight_plan.start_time for flight_plan in flight_plans_list
        )
        self.end_timestamp = max(
            flight_plan.end_time for flight_plan in flight_plans_list
        )

    def _generate_time_slots_interval_tree(self):
        # Compute the time ranges of the data to produce the list of timeslots
        time_ranges = np.arange(
            start=self.start_timestamp,
            stop=self.end_timestamp + self.time_slot_duration,
            step=self.time_slot_duration
        )

        # Populate the list of time slots
        self.time_slots = list(zip(time_ranges[:-1], time_ranges[1:]))
        # Generate timeslot ids
        self.time_slot_ids = list(range(len(self.time_slots)))
        # Map timeslots to timeslot ids
        self.time_slot_id_mappings = {
            Interval(begin, end): idx for idx, (begin, end) in enumerate(self.time_slots)
        }

        # Compute the timeslot data structure (using IntervalTree)
        self.time_slot_interval_tree = IntervalTree.from_tuples(self.time_slots)

    def _set_facility_ids_and_mappings(self):
        # Init facility index
        facilities_index = 0
        self.facility_id_mappings = {}

        for flight_id, flight_plan in self.flight_plans.items():
            for facility in flight_plan.facilities_passed:
                # Add facility to facility id mapping and facility list
                if facility not in self.facility_id_mappings:
                    self.facility_id_mappings[facility] = facilities_index
                    facilities_index += 1

        self.facilities = list(self.facility_id_mappings.keys())
        self.facility_ids = list(range(len(self.facilities)))

    def _encode_flight_plan(self, flight_plan: FlightPlan):
        # Initiate encoded flight plan
        encoded_flight_plan = EncodedFlightPlan(
            call_sign=flight_plan.call_sign,
            flight_id=self.call_sign_id_mappings[flight_plan.call_sign],
            facility_ids=[],
            time_slot_ids=np.array([], dtype=int),
            flight_plan={},
            flight_type=flight_plan.flight_type,
            original_time_slot=None
        )

        facility_entry_exit_times = flight_plan.facility_entry_exit_times
        for facility, time_entry, time_exit in facility_entry_exit_times:
            facility_id = self.facility_id_mappings[facility]

            time_slot_overlapped_ids = []
            # Get the overlapped time slot
            overlapped_time_slots = self.time_slot_interval_tree.overlap(
                time_entry, time_exit
            )
            # Loop through each overlapped timeslot
            for overlapped_timeslot in overlapped_time_slots:
                # Get time slot id
                time_slot_id = self.time_slot_id_mappings[overlapped_timeslot]
                time_slot_overlapped_ids.append(time_slot_id)

            # The overlap function return the later time slot first
            time_slot_overlapped_ids = sorted(time_slot_overlapped_ids)

            # Add each encoded plan to the encoded flight plan
            encoded_flight_plan.add_plan(
                facility_id=facility_id, time_slot_ids=time_slot_overlapped_ids
            )

        return encoded_flight_plan

    def _encode_flight_plans(self):
        # Generate the encoded flight plans
        self.encoded_flight_plans = {
            flight_id: self._encode_flight_plan(flight_plan=flight_plan)
            for flight_id, flight_plan in self.flight_plans.items()
        }
        # Store a copy in cache
        self._cached_encoded_flight_plans = deepcopy(self.encoded_flight_plans)

    # NOTE: Only compute the potential demand matrix from flights which not yet depart.
    #  Since only not yet departed flight contribute to the potential demand matrix.
    def _compute_potential_demand_matrix(self):
        # Demand are represented by the set of flight_id
        self.potential_demand_matrix = {}
        # Demand are represented by integer (number of flight per facility per timeslot)
        self.potential_demand_matrix_computed = {}

        # Compute the potential demand matrix
        for encoded_flight_plan in self.encoded_flight_plans.values():
            # Only compute the potential demand from not yet depart flights
            if encoded_flight_plan.departed:
                continue

            for id_pair in encoded_flight_plan.id_pairs:
                # Compute the demand
                if id_pair not in self.potential_demand_matrix:
                    self.potential_demand_matrix[id_pair] = {encoded_flight_plan.callsign}  # a set of flight
                    self.potential_demand_matrix_computed[id_pair] = 1  # a computed demand, number of flight
                else:
                    self.potential_demand_matrix[id_pair].add(encoded_flight_plan.callsign)
                    self.potential_demand_matrix_computed[id_pair] += 1

        # Store a copy in cache
        self._cached_potential_demand_matrix = deepcopy(self.potential_demand_matrix)
        self._cached_potential_demand_matrix_computed = deepcopy(self.potential_demand_matrix_computed)

    def _compute_time_slot_departure_order(self):
        self.time_slot_departure_order = {}

        for encoded_flight_plan in self.encoded_flight_plans.values():
            if encoded_flight_plan.departed:
                continue

            departure_time_slot = encoded_flight_plan.departure_time_slot
            call_sign = encoded_flight_plan.callsign

            if departure_time_slot not in self.time_slot_departure_order:
                self.time_slot_departure_order[departure_time_slot] = [call_sign]
            else:
                self.time_slot_departure_order[departure_time_slot].append(call_sign)

        # Store a copy in a cache
        self._cached_time_slot_departure_order = deepcopy(self.time_slot_departure_order)

    def reset(self):
        # Set start, end timestamp attributes:
        # - self.start_timestamp
        # - self.end_timestamp
        if not self.start_timestamp or not self.end_timestamp:
            self._set_scenarios_start_end_time()

        # Set timeslot attributes:
        # - self.time_slots
        # - self.time_slot_ids
        # - self.time_slot_ids_mapping
        # - self.time_slots_interval_tree
        if not self.time_slot_id_mappings:
            self._generate_time_slots_interval_tree()

        # Set facility attributes:
        # - self.facilities
        # _ self.facility_ids
        # - self.facility_id_mappings
        if not self.facility_id_mappings:
            self._set_facility_ids_and_mappings()

        # Set encode_flight_plans attributes
        # - self.encoded_flight_plans
        # - self._cached_encoded_flight_plans
        # Encode the flight plans or reload from cache
        if not self._cached_encoded_flight_plans:
            self._encode_flight_plans()
        else:
            self.encoded_flight_plans = deepcopy(self._cached_encoded_flight_plans)

        # Set potential demand attributes:
        # - self.potential_demand_matrix
        # - self._cached_potential_demand_matrix
        # - self.potential_demand_matrix_computed
        # - self._cached_potential_demand_matrix_computed
        if not self._cached_potential_demand_matrix:
            self._compute_potential_demand_matrix()
        else:
            self.potential_demand_matrix = deepcopy(
                self._cached_potential_demand_matrix
            )
            self.potential_demand_matrix_computed = deepcopy(
                self._cached_potential_demand_matrix_computed
            )

        # Compute departure order based on timeslot
        if not self._cached_time_slot_departure_order:
            self._compute_time_slot_departure_order()
        else:
            self.time_slot_departure_order = deepcopy(
                self._cached_time_slot_departure_order
            )

        # Set actual demand
        self.actual_demand_matrix_computed = {}
        # There is no actual_demand_matrix which stores the set of call sign of departed flights.
        # Because if the flight is departed, there is nothing we can do about them.
        # Therefore, no need to store the call sign to interact with them,
        # at least for now.

        # TODO: Update overcapacity note 1. This is okay.
        self._update_capacity_info()

    def _init_from_csv(
        self,
        data_file_path: str,
    ):
        flight_plan_df = pd.read_csv(data_file_path, na_filter=False)
        self.data_file_path = data_file_path
        return self._init_from_pandas_df(
            flight_plan_df=flight_plan_df
        )

    def _init_from_pandas_df(
        self,
        flight_plan_df: pd.DataFrame
    ):
        flight_plan_dict = FlightPlanExtractor.extract_from_pandas_df(
            flight_plan_df=flight_plan_df
        )
        self._init_from_flight_plan_dict(
            flight_plan_dict=flight_plan_dict
        )

    def _init_from_flight_plan_dict(
        self,
        flight_plan_dict: Dict[str, FlightPlan]
    ):
        self.flight_plans = flight_plan_dict
        self.flights = list(flight_plan_dict.keys())
        self.flight_ids = list(range(len(self.flights)))
        self.call_sign_id_mappings = {
            call_sign: flight_id for flight_id, call_sign in enumerate(self.flights)
        }

        # Reset the environment
        self.reset()


    @classmethod
    def from_csv(cls, *args, **kwargs):
        # Get the parameters
        time_slot_duration = kwargs['time_slot_duration']  # int
        max_shift_times = kwargs['max_shift_times']  # int
        capacity_constraint_num = kwargs['capacity_constraint_num']  # int
        data_file_path = kwargs['data_file_path']  # str

        obj = cls(
            time_slot_duration=time_slot_duration,
            max_shift_times=max_shift_times,
            capacity_constraint_num=capacity_constraint_num
        )
        obj._init_from_csv(data_file_path=data_file_path)
        return obj

    @classmethod
    def from_pandas_df(cls, *args, **kwargs):
        # Get the parameters
        time_slot_duration = kwargs['time_slot_duration']  # int
        max_shift_times = kwargs['max_shift_times']  # int
        capacity_constraint_num = kwargs['capacity_constraint_num']  # int
        flight_plan_df = kwargs['flight_plan_df']  # pandas.DataFrame

        obj = cls(
            time_slot_duration=time_slot_duration,
            max_shift_times=max_shift_times,
            capacity_constraint_num=capacity_constraint_num
        )
        obj._init_from_pandas_df(flight_plan_df=flight_plan_df)
        return obj

    @classmethod
    def from_flight_plan_dict(cls, *args, **kwargs):
        # Get the parameters
        time_slot_duration = kwargs['time_slot_duration']  # int
        max_shift_times = kwargs['max_shift_times']  # int
        capacity_constraint_num = kwargs['capacity_constraint_num']  # int
        flight_plan_dict = kwargs['flight_plan_dict']  # dict

        obj = cls(
            time_slot_duration=time_slot_duration,
            max_shift_times=max_shift_times,
            capacity_constraint_num=capacity_constraint_num
        )
        obj._init_from_flight_plan_dict(
            flight_plan_dict=flight_plan_dict
        )
        return obj


    def _reschedule_flight_departure(self, flight_id: str, old_depart: int, new_depart: int):
        self.time_slot_departure_order[old_depart].remove(flight_id)

        if new_depart not in self.time_slot_departure_order:
            self.time_slot_departure_order[new_depart] = [flight_id]
        else:
            self.time_slot_departure_order[new_depart].append(flight_id)

    def _hold_flight(self, flight_id, num_time_slots_hold: int):
        old_departure_time_slot = self.encoded_flight_plans[flight_id].departure_time_slot

        decreasing_demand_set, increasing_demand_set = self.encoded_flight_plans[flight_id].hold(
            num_time_slots_hold
        )

        new_departure_time_slot = self.encoded_flight_plans[flight_id].departure_time_slot
        self._reschedule_flight_departure(flight_id, old_departure_time_slot, new_departure_time_slot)

    def _increase_actual_demand(self, id_pairs: Iterable[Tuple[int, int]]):
        for id_pair in id_pairs:
            if id_pair not in self.actual_demand_matrix_computed:
                self.actual_demand_matrix_computed[id_pair] = 1
            else:
                self.actual_demand_matrix_computed[id_pair] += 1

    def _depart_flight(self, flight_id):
        # facility_id, timeslot_id
        id_pairs = self.encoded_flight_plans[flight_id].depart()

        # The demand of a departed flight is not potential anymore, but actual
        self._increase_actual_demand(id_pairs)

        # Remove the flight from the departure order
        departure_time_slot = self.encoded_flight_plans[flight_id].departure_time_slot
        self.time_slot_departure_order[departure_time_slot].remove(flight_id)

    def _update_capacity_info(
        self,
        capacity_constraint_num: Optional[int] = None,
        capacity_constraint_matrix: Optional[Dict[Tuple[int, int], int]] = None
    ):
        if (
            self.capacity_constraint_matrix is not None and
            capacity_constraint_matrix is not None and
            self.capacity_constraint_num is not None and
            capacity_constraint_num is not None
        ):
            raise ValueError(
                "The facility traffic environment must have "
                "the capacity constraints information to score. "
                "Either specify the default capacity capacity_constraint (uniform capacity_constraint) "
                "or the capacity constraints dictionary."
            )

        # Added the new capacity capacity_constraint if any.
        # This will overwrite the old constraints
        if capacity_constraint_num:
            self.capacity_constraint_num = capacity_constraint_num

        if capacity_constraint_matrix:
            self.capacity_constraint_matrix = capacity_constraint_matrix


        # Since the total demand must be computed from both
        # potential (planned) flights and the actual (departed) flights
        id_pair_set = (
            self.potential_demand_matrix_computed.keys() |
            self.actual_demand_matrix_computed.keys()
        )

        # TODO: can only have a list of affected facility-timeslot
        #  and only calculate from those spot. This would improve speed a lot.
        # Traffic is a set of flight ID at that facility at that timeslot.
        total_overcapacity = 0
        overcapacity_matrix = {}
        for id_pair in id_pair_set:
            # total demand = potential demand + actual demand
            total_demand = (
                self.potential_demand_matrix_computed.get(id_pair, 0) +
                self.actual_demand_matrix_computed.get(id_pair, 0)
            )

            capacity_constraint = (
                self.capacity_constraint_matrix[id_pair]
                if self.capacity_constraint_matrix
                else self.capacity_constraint_num
            )

            num_overcapacity = max(total_demand - capacity_constraint, 0)
            if num_overcapacity > 0:
                overcapacity_matrix[id_pair] = num_overcapacity
                total_overcapacity += num_overcapacity

        self.overcapacity_matrix = overcapacity_matrix
        self.total_overcapacity = total_overcapacity