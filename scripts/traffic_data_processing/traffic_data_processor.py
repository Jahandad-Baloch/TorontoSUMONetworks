import pandas as pd

class TrafficDataProcessor:
    def __init__(self, traffic_volume_file: str, traffic_settings, logger):
        self.traffic_volume_file = traffic_volume_file
        self.logger = logger
        self.begin_time = traffic_settings['begin_time']
        self.end_time = traffic_settings['end_time']
        self.num_intervals = traffic_settings['num_intervals']
        self.threshold_value = traffic_settings['threshold_value']
        self.epsilon_value = traffic_settings['epsilon_value']

    def preprocess_traffic_data_old(self, mode):


        traffic_volume_df = pd.read_csv(self.traffic_volume_file)
        traffic_volume_df['time_start'] = pd.to_datetime(traffic_volume_df['time_start']).dt.time
        traffic_volume_df['time_end'] = pd.to_datetime(traffic_volume_df['time_end']).dt.time

        traffic_volume_df['time_start'] = traffic_volume_df['time_start'].apply(self.time_to_seconds)
        traffic_volume_df['time_end'] = traffic_volume_df['time_end'].apply(self.time_to_seconds)

        common_features = ['centreline_id', 'location_id', 'location', 'lng', 'lat', 'centreline_type',
                           'count_date', 'time_start', 'time_end']


        features = [col for col in traffic_volume_df.columns if mode in col]
        filtered_traffic_volumes = traffic_volume_df[
            (traffic_volume_df['time_start'] >= self.begin_time) &
            (traffic_volume_df['time_end'] <= self.end_time)
        ][common_features + features]

        if mode == 'cars':
            filtered_traffic_volumes.columns = filtered_traffic_volumes.columns.str.replace('_t', '_s')
        if mode == 'truck':
            filtered_traffic_volumes.columns = filtered_traffic_volumes.columns.str.replace('k_t', 'k_s')

        padded_traffic_volumes = self.pad_traffic_records(filtered_traffic_volumes)
        return padded_traffic_volumes

    def pad_traffic_records(self, df):
        def pad_group(group):
            if len(group) >= self.num_intervals:
                return group.head(self.num_intervals)
            else:
                additional_records_needed = self.num_intervals - len(group)
                last_record = group.iloc[-1].to_dict()
                additional_records = pd.DataFrame([last_record] * additional_records_needed)
                return pd.concat([group, additional_records], ignore_index=True)

        result = df.groupby('centreline_id').apply(pad_group).reset_index(drop=True)
        return result

    def time_to_seconds(self, time_obj):
        return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second

    
    def preprocess_traffic_data(self, mode):
        traffic_volume_df = pd.read_csv(self.traffic_volume_file)
        traffic_volume_df['time_start'] = pd.to_datetime(traffic_volume_df['time_start']).dt.time
        traffic_volume_df['time_end'] = pd.to_datetime(traffic_volume_df['time_end']).dt.time

        traffic_volume_df['time_start'] = traffic_volume_df['time_start'].apply(self.time_to_seconds)
        traffic_volume_df['time_end'] = traffic_volume_df['time_end'].apply(self.time_to_seconds)

        common_features = ['centreline_id', 'location_id', 'location', 'lng', 'lat', 'centreline_type',
                           'count_date', 'time_start', 'time_end']

        # Ensure consistency in column types
        traffic_volume_df = traffic_volume_df.astype({
            'centreline_id': 'int',
            'location_id': 'int',
            'location': 'str',
            'lng': 'float',
            'lat': 'float',
            'count_date': 'str',
            'time_start': 'int',
            'time_end': 'int'
        })
        features = [col for col in traffic_volume_df.columns if mode in col]
        filtered_traffic_volumes = traffic_volume_df[
            (traffic_volume_df['time_start'] >= self.begin_time) &
            (traffic_volume_df['time_end'] <= self.end_time)
        ][common_features + features]

        if mode == 'cars':
            filtered_traffic_volumes.columns = filtered_traffic_volumes.columns.str.replace('_t', '_s')
        if mode == 'truck':
            filtered_traffic_volumes.columns = filtered_traffic_volumes.columns.str.replace('k_t', 'k_s')
        padded_traffic_volumes = self.pad_traffic_records(filtered_traffic_volumes)
        return padded_traffic_volumes
