import pandas as pd

class TrafficDataProcessor:
    def __init__(self, traffic_volume_file: str, traffic_settings, logger):
        self.traffic_volume_file = traffic_volume_file
        self.logger = logger
        self.mode = traffic_settings['mode']
        self.begin_time = traffic_settings['begin_time']
        self.end_time = traffic_settings['end_time']
        self.num_intervals = traffic_settings['num_intervals']
        self.threshold_value = traffic_settings['threshold_value']
        self.epsilon_value = traffic_settings['epsilon_value']

    def preprocess_traffic_data(self):
        traffic_volume_df = pd.read_csv(self.traffic_volume_file)
        traffic_volume_df['time_start'] = pd.to_datetime(traffic_volume_df['time_start']).dt.time
        traffic_volume_df['time_end'] = pd.to_datetime(traffic_volume_df['time_end']).dt.time

        traffic_volume_df['time_start'] = traffic_volume_df['time_start'].apply(self.time_to_seconds)
        traffic_volume_df['time_end'] = traffic_volume_df['time_end'].apply(self.time_to_seconds)

        common_features = ['centreline_id', 'location_id', 'location', 'lng', 'lat', 'centreline_type',
                           'count_date', 'time_start', 'time_end']

        if self.mode == 'cars':
            features = [col for col in traffic_volume_df.columns if 'car' in col]
        elif self.mode == 'trucks':
            features = [col for col in traffic_volume_df.columns if 'truck' in col]
        else:
            features = [col for col in traffic_volume_df.columns if 'car' in col or 'truck' in col]

        filtered_traffic_volumes = traffic_volume_df[
            (traffic_volume_df['time_start'] >= self.begin_time) &
            (traffic_volume_df['time_end'] <= self.end_time)
        ][common_features + features]

        traffic_volume_df.columns = traffic_volume_df.columns.str.replace('_t', '_s')
        padded_traffic_volumes = self.pad_traffic_records(filtered_traffic_volumes)

        self.logger.info(f"Length of Traffic Volume DataFrame: {len(padded_traffic_volumes)}")
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
