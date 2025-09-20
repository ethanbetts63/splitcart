import pandas as pd
import geopandas
import os
from datetime import datetime
from django.db.models import Q

from companies.models import Store, Company
from .base_map_generator import BaseMapGenerator

class CompanyMapGenerator(BaseMapGenerator):
    """
    Generates a map of store locations, filtered by company and colored by brand.
    """
    def __init__(self, company_name=None):
        super().__init__(company_name)
        self.title = ''

    def _prepare_data(self):
        """Fetches and prepares store data based on the specified company."""
        stores_query = Store.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        ).exclude(
            Q(company__name__iexact="Coles") & ~Q(division__name="Coles Supermarkets") |
            Q(company__name__iexact="Woolworths") & ~Q(division__name="SUPERMARKETS")
        ).select_related('company', 'division')

        filename_part = 'all_companies'
        if self.company_name:
            try:
                company_obj = Company.objects.get(name__iexact=self.company_name)
                stores_query = stores_query.filter(company=company_obj)
                self.title = f'{company_obj.name} Store Locations'
                filename_part = company_obj.name.lower().replace(' ', '_')
            except Company.DoesNotExist:
                print(f"Error: Company '{self.company_name}' not found.")
                return
        else:
            self.title = 'All Company Store Locations Across Australia'

        stores_list = list(stores_query)
        if not stores_list:
            return

        data = {
            'company': [store.company.name for store in stores_list],
            'latitude': [float(store.latitude) for store in stores_list],
            'longitude': [float(store.longitude) for store in stores_list]
        }
        df = pd.DataFrame(data)
        self.gdf = geopandas.GeoDataFrame(
            df, geometry=geopandas.points_from_xy(df.longitude, df.latitude)
        )
        self.gdf.set_crs(epsg=4326, inplace=True)

        # Set output path
        output_dir = os.path.join('api', 'data', 'analysis', 'company_maps')
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


def generate_store_map(company_name=None):
    """Wrapper function to instantiate and run the CompanyMapGenerator."""
    generator = CompanyMapGenerator(company_name=company_name)
    return generator.generate()
