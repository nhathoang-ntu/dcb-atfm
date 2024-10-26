import numpy as np
import pandas as pd
import pickle
import json

from typing import Dict, Tuple, List

from abstract.flightplan import FlightPlan
from utility.plan_extractor import FlightPlanExtractor

class FlightPlanUtility:
    def __init__(
        self, 
        flight_plan_file_path: str, 
        traffic_hour: int | None = None,
        traffic_day: int | None = None,
        exclude_non_local: bool = False, 
        exclude_runway: bool = True,
        binary_file_path: str | None = None
    ):
        self.flight_plan_file_path = flight_plan_file_path
        self.traffic_hour = traffic_hour
        self.traffic_day = traffic_day
        self.exclude_non_local = exclude_non_local
        self.exclude_runway = exclude_runway
        self.output_file_path = binary_file_path

        self.data = pd.read_csv(self.flight_plan_file_path, na_filter=False, index_col=False)

    @staticmethod
    def _set_flight_type(df: pd.DataFrame) -> pd.DataFrame:
        # set local flights (departure and arrival within the region)
        local_flight_id = df.groupby('id').filter(lambda x: len(x) >= 2 and 'departure' in x['rwyuse'].values and 'arrival' in x['rwyuse'].values)['id'].tolist()
        # set outbound flights (arrival outside the region)
        outbound_flight_id = df.groupby('id').filter(lambda x: len(x) >= 2 and 'arrival' not in x['rwyuse'].values and 'departure' in x['rwyuse'].values)['id'].tolist()
        # set inbound flights (departure outside the region)
        inbound_flight_id = df.groupby('id').filter(lambda x: len(x) >= 2 and 'departure' not in x['rwyuse'].values and 'arrival' in x['rwyuse'].values)['id'].tolist()

        df['flight_type'] = np.where(df['id'].isin(outbound_flight_id), 'outbound', 'unknown')
        df['flight_type'] = np.where(df['id'].isin(inbound_flight_id), 'inbound', df['flight_type'])
        df['flight_type'] = np.where(df['id'].isin(local_flight_id), 'local', df['flight_type'])
        
        return df

    @classmethod
    # this due to some inconsistency in the data, where the time_exit is before time_entry (potential simulation error)
    def exclude_negative_flights(data: pd.DataFrame) -> pd.DataFrame:
            data['time(mins)'] = (data['time_exit'] - data['time_entry'])/60
            investigate_df = data.sort_values('time(mins)', ascending=True)
            investigate_df = investigate_df[investigate_df['time(mins)'] < 0]
            flight_id = investigate_df['id'].tolist()

            return data[~data['id'].isin(flight_id)]
    
    @staticmethod
    def _set_airline(df: pd.DataFrame) -> pd.DataFrame:
        # set airline based on the first3 characters of the call sign
        df['airline'] = df['id'].str[:3]
        return df

    @classmethod
    def decode_flightplan(cls, data: pd.DataFrame) -> pd.DataFrame:
        """
        Decode the data back to the original format.
        """

        return data
    
    def set_additional_features(self):
        """
        Set additional features to the data.
        """
        data = self._set_airline(self.data)
        if 'flight_type' in data.columns:
            data.drop('flight_type', axis=1, inplace=True)
            data['flight_type'] = None
        data = self._set_flight_type(data)
        #data = cls.exclude_negative_flights(data)
        return data
    
    def extract_data(self, csv_file_path: str | None = None) -> Dict[str, FlightPlan]:
        # na_filter = False since some simulation data column is empty
        # flight_plan_df = pd.read_csv(self.flight_plan_file_path, na_filter=False, index_col=False)

        if self.traffic_day is not None and self.traffic_hour is not None:
            self.data = self.data[(self.data['day'] == self.traffic_day) & (self.data['hour'] < self.traffic_hour)]

        if not self.exclude_non_local:
            self.data = self.data[self.data['flight_type'] == 'local']

        if self.exclude_runway:
            # trim the runway, only keep the row with rwyuse = None
            self.data = self.data[self.data['rwyuse'] == '']

        if csv_file_path:
            with open(csv_file_path, 'w') as f:
                self.data.to_csv(f, index=False)

        flight_plans = FlightPlanExtractor.extract_from_pandas_df(self.data)

        if self.output_file_path:
            with open(self.output_file_path, 'wb') as fwb:
                pickle.dump(flight_plans, fwb)

        print(f'Num flight extracted: {len(flight_plans)}')

        return flight_plans
    
class FacilityUtility:
     @classmethod
     def calculate_capacity(
         cls, 
         default_capacity: int,
         facility_array: List[str],
         demand_matrix: Dict[Tuple[int, int], int]
    ) -> Dict[Tuple[int, int], int]:
        # self.capacity_array = [self.default_capacity] * len(self.facility_ids)
        # self.capacity_constraint_matrix = {}
        # #get top highest demands for each facility from the actual demand matrix
        # for facility in self.facility_ids:
        #     #get the demand of the facility
        #     facility_demand = [self.actual_demand_matrix_computed.get((facility, time), 0) for time in self.time_slot_ids]
        #     facility_demand = sorted(facility_demand, reverse=True)
        #     self.capacity_array[facility] = max(int(sum(facility_demand[:top]) / top / (1 + percentage_exceed)) + 1, self.capacity_array[facility])
        
        # # Set the capacity constraint matrix
        # for time in range(len(self.time_slot_ids)):
        #     for facility in range(len(self.facility_ids)):
        #         self.capacity_constraint_matrix[(facility, time)] = self.capacity_array[facility]
        pass
     
     @classmethod
     def create_capacity_matrix(cls, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create the capacity matrix.
        """
        return data
     
class DataExtractor:
    @staticmethod
    def extract_data(
        input_file_path: str,
        output_file_path: str,
        facility_file_path: str,
        volume: str = 'current',
        routing: str = 'ats',
        trim_runway: bool = True,
    ):
        #read the data from the csv file
        data = pd.read_csv(input_file_path)

        data = data[(data['volume'] == volume) & (data['routing'] == routing)]
        data.drop(['volume', 'routing'], axis=1, inplace=True)

        with open(facility_file_path) as f:
            data_dict = json.load(f)

        facility_list = list(data_dict.values())
        facility_list = [item for sublist in facility_list for item in sublist]
        print(facility_list)

        df = data[data['facility'].isin(facility_list)]

        # create a airline column, which is the first 3 characters of the flight id
        df['airline'] = df['id'].str[:3]

        # set local flights (departure and arrival within the region)
        local_flight_id = df.groupby('id').filter(lambda x: len(x) >= 2 and 'departure' in x['rwyuse'].values and 'arrival' in x['rwyuse'].values)['id'].tolist()
        # set outbound flights (arrival outside the region)
        outbound_flight_id = df.groupby('id').filter(lambda x: len(x) >= 2 and 'arrival' not in x['rwyuse'].values and 'departure' in x['rwyuse'].values)['id'].tolist()
        # set inbound flights (departure outside the region)
        inbound_flight_id = df.groupby('id').filter(lambda x: len(x) >= 2 and 'departure' not in x['rwyuse'].values and 'arrival' in x['rwyuse'].values)['id'].tolist()

        df['flight_type'] = np.where(df['id'].isin(outbound_flight_id), 'outbound', 'unknown')
        df['flight_type'] = np.where(df['id'].isin(inbound_flight_id), 'inbound', df['flight_type'])
        df['flight_type'] = np.where(df['id'].isin(local_flight_id), 'local', df['flight_type'])

        if trim_runway:
            df = df[~df['rwyuse'].isin(['arrival', 'departure'])]


        df.to_csv(output_file_path, index=False)
        print('data extraction completed')