# modules/traffic/traffic_data_processor.py
import pandas as pd

class TrafficDataProcessor:
    """Processes raw traffic volume data.

    Args:
        traffic_volume_file (str): Path to traffic volume CSV.
        traffic_settings (dict): Dictionary of traffic settings.
        logger: Logger instance.
    """
    def __init__(self, tmc_data_file: str, svc_data_file: str, traffic_settings: dict, logger) -> None:
        self.tmc_data_file = tmc_data_file
        self.svc_data_file = svc_data_file

        self.logger = logger
        self.begin_time = traffic_settings['begin_time']
        self.end_time = traffic_settings['end_time']
        self.num_intervals = traffic_settings['num_intervals']
        self.threshold_value = traffic_settings['threshold_value']
        self.epsilon_value = traffic_settings['epsilon_value']

    def time_to_seconds(self, time_str: str) -> int:
        """Convert a timestamp string to seconds."""
        time_obj = pd.to_datetime(time_str).time()
        return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second

    def preprocess_tmc_data(self, mode: str) -> pd.DataFrame:
        """Preprocesses TMC dataset for intersection-based turning movement counts."""
        self.logger.info(f"Processing TMC data for mode: {mode}")
        tmc_df = pd.read_csv(self.tmc_data_file)

        # Convert time fields to seconds
        tmc_df['time_start'] = tmc_df['start_time'].apply(self.time_to_seconds)
        tmc_df['time_end'] = tmc_df['end_time'].apply(self.time_to_seconds)
        
        # Validate time intervals and drop invalid ones
        invalid_intervals = tmc_df['time_start'] >= tmc_df['time_end']
        if invalid_intervals.any():
            self.logger.warning(f"Dropping {invalid_intervals.sum()} rows with invalid time intervals")
            tmc_df = tmc_df[~invalid_intervals]
        
        # Select relevant columns
        common_features = ['centreline_id', 'location_name', 'longitude', 'latitude', 'count_date', 'time_start', 'time_end']
        features = [col for col in tmc_df.columns if mode in col]
        
        filtered_tmc = tmc_df[
            (tmc_df['time_start'] >= self.begin_time) & (tmc_df['time_end'] <= self.end_time)
        ][common_features + features]

        if mode == 'cars':
            filtered_tmc.columns = filtered_tmc.columns.str.replace('_t', '_s')
        if mode == 'truck':
            filtered_tmc.columns = filtered_tmc.columns.str.replace('k_t', 'k_s')

        return self.pad_traffic_records(filtered_tmc)
    
    def preprocess_svc_data(self) -> pd.DataFrame:
        """Preprocesses SVC dataset for midblock speed and volume counts."""
        self.logger.info("Processing SVC data")
        svc_df = pd.read_csv(self.svc_data_file)
        
        # Convert time fields to seconds
        svc_df['time_start'] = svc_df['time_start'].apply(self.time_to_seconds)
        svc_df['time_end'] = svc_df['time_end'].apply(self.time_to_seconds)
        
        # Validate time intervals and drop invalid ones
        invalid_intervals = svc_df['time_start'] >= svc_df['time_end']
        if invalid_intervals.any():
            self.logger.warning(f"Dropping {invalid_intervals.sum()} rows with invalid time intervals")
            svc_df = svc_df[~invalid_intervals]
        
        # Filter by simulation time range
        filtered_svc = svc_df[
            (svc_df['time_start'] >= self.begin_time) & (svc_df['time_end'] <= self.end_time)
        ][['centreline_id', 'location_name', 'longitude', 'latitude', 'time_start', 'time_end', 'direction', 'volume_15min']]
        
        return self.pad_traffic_records(filtered_svc)
    
    def pad_traffic_records(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensures that each location has complete time intervals by padding missing records."""
        def pad_group(group: pd.DataFrame) -> pd.DataFrame:
            if len(group) >= self.num_intervals:
                return group.head(self.num_intervals)
            else:
                additional_records_needed = self.num_intervals - len(group)
                last_record = group.iloc[-1].to_dict()
                additional_records = pd.DataFrame([last_record] * additional_records_needed)
                return pd.concat([group, additional_records], ignore_index=True)
        
        return df.groupby('centreline_id').apply(pad_group).reset_index(drop=True)


