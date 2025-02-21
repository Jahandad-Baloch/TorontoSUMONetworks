import requests
import os
from modules.core.simulation_task import SimulationTask

class DatasetDownloader(SimulationTask):
    """Downloads configured datasets from external sources.

    This task fetches dataset metadata and downloads files as specified in the configuration.
    """

    def __init__(self, app_context):
        """Initializes the DatasetDownloader with the shared AppContext.

        Args:
            app_context (AppContext): Shared application context.
        """
        super().__init__(app_context)
        self.app_context = app_context
        self.config = app_context.config
        self.logger = app_context.logger
        self.download_dir = self.config['paths']['raw_data']
        self.api_base_url = "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_show"
        os.makedirs(self.download_dir, exist_ok=True)

    def execute(self):
        """Executes the task to download all configured datasets."""
        try:
            self.logger.info("Starting data download process")
            for dataset_name, details in self.config['transportation_datasets'].items():
                if details['fetch_data']:
                    self.download_dataset(dataset_name, details['target_files'])
            self.logger.info("Data download completed successfully")
        except Exception as e:
            self.logger.error(f"Failed to download data: {e}")
            raise

    def fetch_dataset_metadata(self, dataset_name):
        """Fetches metadata for a dataset from Toronto Open Data.

        Args:
            dataset_name (str): The name of the dataset.

        Returns:
            dict or None: Dataset metadata if successful; otherwise, None.
        """
        try:
            response = requests.get(self.api_base_url, params={"id": dataset_name})
            data = response.json()
            if not data.get('success'):
                self.logger.error(f"Failed to fetch metadata for {dataset_name}")
                return None
            return data['result']
        except Exception as e:
            self.logger.error(f"API error for {dataset_name}: {e}")
            return None

    def download_resource(self, resource, dataset_dir):
        """Downloads a single resource file from a dataset.

        Args:
            resource (dict): Resource metadata.
            dataset_dir (str): Directory to save the downloaded file.
        """
        file_name = resource['name'].replace(' ', '_').lower()
        resource_format = resource['format'].lower()
        if '.' in file_name:
            file_name, _ = file_name.rsplit('.', 1)
        file_path = os.path.join(dataset_dir, f"{file_name}.{resource_format}")
        if os.path.exists(file_path):
            self.logger.info(f"File exists: {file_path}")
            return
        try:
            response = requests.get(resource['url'], stream=True)
            response.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            self.logger.info(f"Downloaded: {file_path}")
        except Exception as e:
            self.logger.error(f"Download failed for {file_name}: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)

    def download_dataset(self, dataset_name, target_files):
        """Downloads a specific dataset and its required files.

        Args:
            dataset_name (str): The dataset identifier.
            target_files (dict): Mapping of keywords to file details.
        """
        self.logger.info(f"Processing dataset: {dataset_name}")
        metadata = self.fetch_dataset_metadata(dataset_name)
        if not metadata:
            return
        dataset_dir = os.path.join(self.download_dir, dataset_name)
        os.makedirs(dataset_dir, exist_ok=True)
        for resource in metadata['resources']:
            file_name = resource['name'].lower()
            resource_format = resource['format'].lower()
            for keyword, details in target_files.items():
                if str(keyword) in file_name and details['format'] == resource_format:
                    self.download_resource(resource, dataset_dir)
                    break

