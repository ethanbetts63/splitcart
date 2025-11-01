import pandas as pd
import geopandas
import os
import requests
from datetime import datetime
from django.conf import settings
from .base_map_generator import BaseMapGenerator

class CompanyMapGenerator(BaseMapGenerator):
    """
    Generates a map of store locations, filtered by company and colored by brand.
    """
    def __init__(self, command, company_name=None, dev=False):
        super().__init__(company_name)
        self.command = command
        self.title = ''
        self.dev = dev

    def _fetch_paginated_data(self, url, headers, data_type):
        """Fetches all pages of data from a paginated API endpoint."""
        all_results = []
        next_url = url
        while next_url:
            response = requests.get(next_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            all_results.extend(data['results'])
            next_url = data.get('next')
            self.command.stdout.write(f"  Fetched {len(all_results)} / {data['count']} {data_type}.")
        return all_results

    def _prepare_data(self):
        """Fetches and prepares store data from the API."""
        if self.dev:
            server_url = "http://127.0.0.1:8000"
            api_key = settings.INTERNAL_API_KEY
        else:
            try:
                server_url = settings.API_SERVER_URL
                api_key = settings.INTERNAL_API_KEY
            except AttributeError:
                self.command.stderr.write("API_SERVER_URL and INTERNAL_API_KEY must be set in settings.")
                return

        headers = {'X-Internal-API-Key': api_key, 'Accept': 'application/json'}
        self.command.stdout.write(self.command.style.SUCCESS(f"--- Starting Map Generation using API at {server_url} ---"))

        try:
            self.command.stdout.write("Fetching stores...")
            stores_data = self._fetch_paginated_data(f"{server_url}/api/export/stores/", headers, "stores")

        except requests.exceptions.RequestException as e:
            self.command.stderr.write(f"Failed to fetch data: {e}"); return
        except json.JSONDecodeError as e:
            self.command.stderr.write(f"Failed to decode JSON: {e}"); return

        stores_list = [
            store for store in stores_data
            if store['latitude'] is not None and store['longitude'] is not None
            and not (store['company'].lower() == 'coles' and store['division'] != 'Coles Supermarkets')
            and not (store['company'].lower() == 'woolworths' and store['division'] != 'SUPERMARKETS')
        ]

        filename_part = 'all_companies'
        if self.company_name:
            stores_list = [store for store in stores_list if store['company'].lower() == self.company_name.lower()]
            self.title = f'{self.company_name} Store Locations'
            filename_part = self.company_name.lower().replace(' ', '_')
        else:
            self.title = 'All Company Store Locations Across Australia'

        if not stores_list:
            return

        data = {
            'company': [store['company'] for store in stores_list],
            'latitude': [float(store['latitude']) for store in stores_list],
            'longitude': [float(store['longitude']) for store in stores_list]
        }
        df = pd.DataFrame(data)
        self.gdf = geopandas.GeoDataFrame(
            df, geometry=geopandas.points_from_xy(df.longitude, df.latitude)
        )
        self.gdf.set_crs(epsg=4326, inplace=True)

        # Set output path
        output_dir = os.path.join('data_management', 'data', 'analysis', 'company_maps')
        date_str = datetime.now().strftime('%Y-%m-%d')
        output_filename = f"{date_str}_{filename_part}.png"
        self.output_path = os.path.join(output_dir, output_filename)

    def _plot_data(self):
        """Plots the store data, color-coded by company brand."""
        brand_colors = {
            'Woolworths': '#00A651',
            'Coles': '#E4002B',
            'Aldi': '#007bff',
            'Iga': '#ffc107'
        }
        default_color = '#6c757d'

        companies_on_map = sorted(self.gdf['company'].unique())
        for company in companies_on_map:
            color = brand_colors.get(company, default_color)
            subset = self.gdf[self.gdf['company'] == company]
            count = len(subset)
            label = f"{company} ({count})"
            self.ax.scatter(subset.geometry.x, subset.geometry.y,
                            transform=ccrs.PlateCarree(), color=color,
                            label=label, s=15, alpha=0.7, edgecolors='k', linewidths=0.5)

    def _set_title_and_legend(self):
        """Sets the title and legend for the company map."""
        self.ax.set_title(self.title)
        self.ax.legend(title='Company (Store Count)')


def generate_store_map(command, company_name=None, dev=False):
    """Wrapper function to instantiate and run the CompanyMapGenerator."""
    generator = CompanyMapGenerator(command, company_name=company_name, dev=dev)
    return generator.generate()
