from configparser import ConfigParser, ExtendedInterpolation


class Config:
    def __init__(self, config_file_path):
        self._config = ConfigParser(interpolation=ExtendedInterpolation())
        self._config.read(config_file_path)


class FlightPlanConfig(Config):
    # section
    _FLIGHT_PLAN = 'FLIGHT PLAN'

    # key
    _FLIGHT_PLAN_FILE_PATH = 'flight_plan_file_path'
    _TRAFFIC_HOUR = 'traffic_hour'
    _TRAFFIC_DAY = 'traffic_day'
    _EXCLUDE_NON_LOCAL = 'exclude_non_local'
    _EXCLUDE_RUNWAY = 'exclude_runway'
    _BINARY_FILE_PATH = 'binary_file_path'

    @property
    def flight_plan_file_path(self):
        return self._config.get(self._FLIGHT_PLAN, self._FLIGHT_PLAN_FILE_PATH)
    
    @property
    def traffic_hour(self):
        return self._config.getint(self._FLIGHT_PLAN, self._TRAFFIC_HOUR)
    
    @property
    def traffic_day(self):
        return self._config.getint(self._FLIGHT_PLAN, self._TRAFFIC_DAY)
    
    @property
    def exclude_non_local(self):
        return bool(self._config.get(self._FLIGHT_PLAN, self._EXCLUDE_NON_LOCAL))
    
    @property
    def exclude_runway(self):
        # return True
        return bool(self._config.get(self._FLIGHT_PLAN, self._EXCLUDE_RUNWAY))
    
    @property
    def binary_file_path(self):
        return self._config.get(self._FLIGHT_PLAN, self._BINARY_FILE_PATH)
    

class DCBEnvironmentConfig(Config):
    # section
    _DCB_ENVIRONMENT = 'DCB ENVIRONMENT'

    # key
    _DATA_FILE_PATH = 'data_file_path'
    _DATA_FILE_TYPE = 'data_file_type'
    _FACILITY_FILE_PATH = 'facility_file_path'
    _CAPACITY_MATRIX_FILE_PATH = 'capacity_matrix_file_path'
    _TIME_SLOT_DURATION = 'time_slot_duration'
    _MAX_ADVANCE_NUM = 'max_advance_num'
    _MAX_DELAY_NUM = 'max_delay_num'
    _DEFAULT_CAPACITY_NUM = 'default_capacity_num'
    _CAPACITY_MATRIX = 'capacity_matrix'
    _CAPACITY_CALCULATION = 'capacity_calculation'
    _SPILLOVER_PERCENTAGE = 'spillover_percentage'

    @property
    def data_file_path(self):
        return self._config.get(self._DCB_ENVIRONMENT, self._DATA_FILE_PATH)

    @property
    def data_file_type(self):
        return self._config.get(self._DCB_ENVIRONMENT, self._DATA_FILE_TYPE)

    @property
    def facility_file_path(self):
        return self._config.get(self._DCB_ENVIRONMENT, self._FACILITY_FILE_PATH)
    
    @property
    def capacity_matrix_file_path(self):
        return self._config.get(self._DCB_ENVIRONMENT, self._CAPACITY_MATRIX_FILE_PATH)

    @property
    def time_slot_duration(self):
        return self._config.getint(self._DCB_ENVIRONMENT, self._TIME_SLOT_DURATION)
    
    @property
    def max_advance_num(self):
        return self._config.getint(self._DCB_ENVIRONMENT, self._MAX_ADVANCE_NUM)

    @property
    def max_delay_num(self):
        return self._config.getint(self._DCB_ENVIRONMENT, self._MAX_DELAY_NUM)
    
    @property
    def default_capacity_num(self):
        return self._config.getint(self._DCB_ENVIRONMENT, self._DEFAULT_CAPACITY_NUM)

    @property
    def capacity_matrix(self):
        return self._config.get(self._DCB_ENVIRONMENT, self._CAPACITY_MATRIX)
    
    @property
    def capacity_calculation(self):
        return bool(self._config.get(self._DCB_ENVIRONMENT, self._CAPACITY_CALCULATION))
    
    @property
    def spillover_percentage(self):
        return float(self._config.get(self._DCB_ENVIRONMENT, self._SPILLOVER_PERCENTAGE))
    
