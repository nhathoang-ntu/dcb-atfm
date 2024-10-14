from typing import Dict, Optional

import pandas as pd
from abstract.flightplan import FlightPlan, Plan

callsign = str

class PlanExtractor:
    """Defines the logic to extract the flight plan from input data
    """

    @classmethod
    def plan_from_pd_series(
        cls,
        plan_in_series: pd.Series,
        mapping_dict: Optional[dict] = None,
    ):
        """Extracts plan from a Pandas Series.

        The Plan attributes and the pandas series object attributes are
        matched according to the mapping below:

        Args:
            plan_in_series (Pandas Series): The plan in pandas series format.
            mapping_dict (dict): A dictionary to mapping the Plan attributes
                to the series elements.

        Returns:
            Plan object
        """
        # Set the default mapping
        # key: pandas series attributes name
        # value: corresponding Plan attributes name
        if not mapping_dict:
            mapping_dict = {
                'id': 'call_sign',
                'airline': 'airline',
                'flight_type': 'flight_type',
                'facility': 'facility',
                'time_entry': 'time_entry',
                'time_exit': 'time_exit',
                'altitude_entry': 'altitude_entry',
                'altitude_exit': 'altitude_exit',
                'longitude_entry': 'longitude_entry',
                'longitude_exit': 'longitude_exit',
                'latitude_entry': 'latitude_entry',
                'latitude_exit': 'latitude_exit',
                'rwyuse': 'runway_use'
            }

        value_dict = {
            key2: plan_in_series.get(key1)
            for key1, key2 in mapping_dict.items()
        }

        return Plan(**value_dict)


class FlightPlanExtractor:
    """Defines the procedure to extract flight plan from data.
    Assuming each call sign represents a single flight.
    """

    @classmethod
    def extract_from_pandas_df(
        cls,
        flight_plan_df: pd.DataFrame
    ) -> Dict[callsign, FlightPlan]:
        flight_plans_dict = {}
        for row_index, row in flight_plan_df.iterrows():
            # Extract plan from Pandas row
            plan = PlanExtractor.plan_from_pd_series(row)
            if plan.call_sign not in flight_plans_dict:
                # Create a new flight plan with the call sign
                flight_plans_dict[plan.call_sign] = FlightPlan([plan])
            else:
                flight_plans_dict[plan.call_sign].add(plan)

        return flight_plans_dict
