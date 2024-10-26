import numpy as np
import pandas as pd

from config.config import FlightPlanConfig, DCBEnvironmentConfig
from utility.utility import FlightPlanUtility


def get_data_config(config_file: str) -> FlightPlanConfig:
    config = FlightPlanConfig(config_file)

    data_config = {
        'flight_plan_file_path': config.flight_plan_file_path,
        'traffic_hour': config.traffic_hour,
        'traffic_day': config.traffic_day,        
        'exclude_non_local': config.exclude_non_local,
        'exclude_runway': config.exclude_runway,
        'binary_file_path': config.binary_file_path
    }
    return data_config

def get_env_config(config_file: str) -> DCBEnvironmentConfig:
    config = DCBEnvironmentConfig(config_file)

    env_config = {
        'data_file_path': config.data_file_path,
        'data_file_type': config.data_file_type,
        'facility_file_path': config.facility_file_path,
        'capacity_matrix_file_path': config.capacity_matrix_file_path,
        'time_slot_duration': config.time_slot_duration,
        'max_advance_num': config.max_advance_num,
        'max_delay_num': config.max_delay_num,
        'default_capacity_num': config.default_capacity_num,
        'capacity_matrix': config.capacity_matrix,
        'capacity_calculation': config.capacity_calculation,
        'spillover_percentage': config.spillover_percentage
    }

    return env_config

if __name__ == "__main__":
    # get data config
    data_config = get_data_config('config/sample_config.cfg')
    #load data
    data = FlightPlanUtility(**data_config)
    # set additional features (airlines, flight types, etc.)
    data.set_additional_features()
    # extract data based on selected features
    data.extract_data(csv_file_path='data/extracted_data_sample.csv')
    print('data extraction completed')

    # export data for analysis

    # print completion message

    #process data for environment
    env_config = get_env_config('config/sample_config.cfg')

    print('data processing completed')