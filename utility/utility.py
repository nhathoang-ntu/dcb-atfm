import pandas as pd

class FlightPlanUtility:
    @classmethod
    def set_flight_type(df: pd.DataFrame) -> pd.DataFrame:
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
    
    """
    This class is used to convert the input flight plan data into a format that can be used in the environment.
    """
    @classmethod
    def encode_flightplan(cls, data: pd.DataFrame) -> pd.DataFrame:
        """
        Encode the data into a format that can be used in the environment.
        """
        return data

    @classmethod
    def decode_flightplan(cls, data: pd.DataFrame) -> pd.DataFrame:
        """
        Decode the data back to the original format.
        """

        return data
    
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