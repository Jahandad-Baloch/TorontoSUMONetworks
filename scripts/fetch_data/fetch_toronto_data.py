import requests
import os
from urllib.parse import urlparse
from scripts.common.utils import ConfigLoader, LoggerSetup
import requests
import os
from urllib.parse import urlparse
from scripts.common.utils import ConfigLoader, LoggerSetup
""" 
This script fetches data from the City of Toronto's Open Data Portal.
"""


class TorontoDataFetcher:
    def __init__(self, config_path):
        """
        Initialize the TorontoDataFetcher class.

        Args:
            config_path (str): The path to the configuration file.
        """
        self.config = ConfigLoader.load_config(config_path)
        self.logger = LoggerSetup.setup_logger('datasets_download', self.config['logging']['log_dir'], self.config['logging']['log_level'])
        self.download_dir = self.config['paths']['raw_data']
        os.makedirs(self.download_dir, exist_ok=True)

    def fetch_dataset_metadata(self, dataset_name):
        """
        Fetch the metadata of a dataset.

        Args:
            dataset_name (str): The name of the dataset.

        Returns:
            dict: The metadata of the dataset.
        """
        base_url = "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_show"
        params = {"id": dataset_name}
        response = requests.get(base_url, params=params)
        package_data = response.json()
        if not package_data.get('success'):
            self.logger.error(f"Failed to fetch data for {dataset_name}")
            return None
        return package_data['result']

    def download_resource(self, resource, dataset_dir):
        """
        Download a resource.

        Args:
            resource (dict): The resource to download.
            dataset_dir (str): The directory to save the downloaded resource.
        """
        file_name = resource['name']
        resource_format = resource['format'].lower()
        self.logger.info(f"Processing resource {file_name} with format {resource_format}")

        # if file name has extension, use it, otherwise use the format
        if '.' in file_name:
            file_name, _ = file_name.rsplit('.', 1)
            # replace spaces with underscores
            file_name = file_name.replace(' ', '_')
        file_path = os.path.join(dataset_dir, f"{file_name}.{resource_format}")

        if os.path.exists(file_path):
            self.logger.info(f"File {file_name}.{resource_format} already exists. Skipping download.")
            return

        response = requests.get(resource['url'])
        with open(file_path, 'wb') as file:
            file.write(response.content)
        self.logger.info(f"Downloaded {file_name}.{resource_format} to {file_path}")

    def download_dataset(self, dataset_name, target_files):
        """
        Download a dataset.

        Args:
            dataset_name (str): The name of the dataset.
            target_files (dict): The target files to download.
        """
        dataset_metadata = self.fetch_dataset_metadata(dataset_name)
        if dataset_metadata is None:
            return

        dataset_dir = os.path.join(self.download_dir, dataset_name)
        os.makedirs(dataset_dir, exist_ok=True)

        for resource in dataset_metadata['resources']:
            file_name = resource['name'].replace(' ', '_').lower()  # Normalize file names
            resource_format = resource['format'].lower()
            for keyword, details in target_files.items():
                if str(keyword) in file_name and details['format'] == resource_format:
                    self.download_resource(resource, dataset_dir)
                    break  # Break after first match to avoid multiple downloads of the same resource

    def fetch_datasets(self):
        """
        Fetch all datasets specified in the configuration file.
        """
        for dataset_name, details in self.config['transportation_datasets'].items():
            if details['fetch_data']:
                self.download_dataset(dataset_name, details['target_files'])
        self.logger.info("Data fetching process completed.")
        self.logger.info(f"\n.......................\n")

if __name__ == "__main__":
    fetcher = TorontoDataFetcher('configurations/main.yaml')
    fetcher.fetch_datasets()

