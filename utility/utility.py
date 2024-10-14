import pandas as pd
import pickle

from typing import Dict

from abstract.flightplan import FlightPlan
from plan_extractor import FlightPlanExtractor

class FlightPlanUtility:
    def __init__(
        self, 
        flight_plan_file_path: str, 
        traffic_hour: int | None = None,
        traffic_day: int | None = None,
        exclude_non_local: bool = True, 
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

    @classmethod
    def _set_flight_type(df: pd.DataFrame) -> pd.DataFrame:
        # set local flights (departure and arrival within the region)
        local_flight_id = df.groupby('id').filter(lambda x: len(x) >= 2 and 'departure' in x['rwyuse'].values and 'arrival' in x['rwyuse'].values)['id'].tolist()
        # df['flight_type'] = np.where(df['id'].isin(local_flight_id), 'local')
        df.loc[df['id'].isin(local_flight_id), 'flight_type'] = 'local'

        # set outbound flights (arrival outside the region)
        outbound_flight_id = df.groupby('id').filter(lambda x: len(x) >= 2 and 'departure' in x['rwyuse'].values and 'arrival' not in x['rwyuse'].values)['id'].tolist()
        df.loc[df['id'].isin(outbound_flight_id), 'flight_type'] = 'outbound'

        # set inbound flights (departure outside the region)
        inbound_flight_id = df.groupby('id').filter(lambda x: len(x) >= 2 and 'departure' not in x['rwyuse'].values and 'arrival' in x['rwyuse'].values)['id'].tolist()
        df.loc[df['id'].isin(inbound_flight_id), 'flight_type'] = 'inbound'
        
        return df

    @classmethod
    # this due to some inconsistency in the data, where the time_exit is before time_entry (potential simulation error)
    def exclude_negative_flights(data: pd.DataFrame) -> pd.DataFrame:
            data['time(mins)'] = (data['time_exit'] - data['time_entry'])/60
            investigate_df = data.sort_values('time(mins)', ascending=True)
            investigate_df = investigate_df[investigate_df['time(mins)'] < 0]
            flight_id = investigate_df['id'].tolist()

            return data[~data['id'].isin(flight_id)]
    

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
        data = self.data
        data = self._set_airline(data)
        data = self._set_flight_type(data)
        #data = cls.exclude_negative_flights(data)
        return data
    
    def extract_data(self, csv_file_path: str | None = None) -> Dict[str, FlightPlan]:
        # na_filter = False since some simulation data column is empty
        flight_plan_df = pd.read_csv(self.flight_plan_file_path, na_filter=False, index_col=False)

        if self.traffic_day is not None and self.traffic_hour is not None:
            flight_plan_df = flight_plan_df[(flight_plan_df['day'] == self.traffic_day) & (flight_plan_df['hour'] < self.traffic_hour)]

        if self.exclude_non_local:
            flight_plan_df = flight_plan_df[flight_plan_df['flight_type'] == 'local']

        if self.exclude_runway:
            # trim the runway, only keep the row with rwyuse = None
            flight_plan_df = flight_plan_df[flight_plan_df['rwyuse'].isnull()]

        if csv_file_path:
            with open(csv_file_path, 'w') as f:
                flight_plan_df.to_csv(f, index=False)

        flight_plans = FlightPlanExtractor.extract_from_pandas_df(flight_plan_df)

        if self.output_file_path:
            with open(self.output_file_path, 'wb') as fwb:
                pickle.dump(flight_plans, fwb)

        print(f'Num flight extracted: {len(flight_plans)}')

        return flight_plans
    
class FacilityUtility:
     @classmethod
     def calculate_capacity(cls, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate the capacity of the facility.
        """
        return data
     
     @classmethod
     def create_capacity_matrix(cls, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create the capacity matrix.
        """
        return data