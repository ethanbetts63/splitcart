import pandas as pd
import geopandas
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import os
from datetime import datetime

from companies.models import Store, Company, StoreGroup
from .base_map_generator import BaseMapGenerator

class ClusterMapGenerator(BaseMapGenerator):
    """
    Generates a map of store locations for a company, colored by cluster group.
    """
    def __init__(self, company_name):
        super().__init__(company_name)
        self.num_clusters = 0
        self.num_outliers = 0

    def _prepare_data(self):
        """Fetches and prepares store data, separating outliers from clustered stores."""
        try:
            company_obj = Company.objects.get(name__iexact=self.company_name)
        except Company.DoesNotExist:
            print(f"Error: Company '{self.company_name}' not found.")
            return

        stores = Store.objects.filter(
            company=company_obj, 
            latitude__isnull=False, 
            longitude__isnull=False
        ).select_related('group_membership__group')

        if not stores.exists():
            return

        data = []
        for store in stores:
            group_id = store.group_membership.group.id if hasattr(store, 'group_membership') and store.group_membership is not None else -1
            data.append({
                'latitude': float(store.latitude),
                'longitude': float(store.longitude),
                'group_id': group_id
            })
        
        df = pd.DataFrame(data)
        self.gdf = geopandas.GeoDataFrame(
            df, geometry=geopandas.points_from_xy(df.longitude, df.latitude)
        )
        self.gdf.set_crs(epsg=4326, inplace=True)

        self.num_clusters = len(df[df['group_id'] != -1]['group_id'].unique())
        self.num_outliers = len(df[df['group_id'] == -1])

        # Set output path
        output_dir = os.path.join('data_management', 'data', 'analysis', 'cluster_maps')
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename_part = self.company_name.lower().replace(' ', '_')
        output_filename = f"{date_str}_{filename_part}_clusters.png"
        self.output_path = os.path.join(output_dir, output_filename)

    def _plot_data(self):
        """Plots clustered stores, adding top 10 largest clusters to the legend."""
        # Plot outliers first
        outliers = self.gdf[self.gdf['group_id'] == -1]
        if not outliers.empty:
            self.ax.scatter(outliers.geometry.x, outliers.geometry.y,
                            transform=ccrs.PlateCarree(), color='k',
                            label=f'Outliers ({self.num_outliers})', s=10, alpha=0.6, marker='x')

        # Plot clustered stores
        clustered = self.gdf[self.gdf['group_id'] != -1]
        if not clustered.empty:
            # Identify top 10 largest clusters
            cluster_counts = clustered['group_id'].value_counts()
            top_10_clusters = cluster_counts.nlargest(10).index.tolist()

            unique_groups = sorted(clustered['group_id'].unique())
            colors = plt.cm.get_cmap('turbo', len(unique_groups))
            color_map = {group_id: colors(i) for i, group_id in enumerate(unique_groups)}

            for group_id, color in color_map.items():
                subset = clustered[clustered['group_id'] == group_id]
                count = len(subset)
                label = None  # Default to no label

                # Only create a label for the top 10 clusters
                if group_id in top_10_clusters:
                    try:
                        # Fetch the group name for a more descriptive label
                        group_name = StoreGroup.objects.get(id=group_id).name
                        label = f"{group_name} ({count})"
                    except StoreGroup.DoesNotExist:
                        label = f"Cluster {group_id} ({count})"

                self.ax.scatter(subset.geometry.x, subset.geometry.y,
                                transform=ccrs.PlateCarree(), color=color,
                                label=label, s=20, alpha=0.8, edgecolors='k', linewidths=0.5)

    def _set_title_and_legend(self):
        """Sets the title and a legend for the top clusters."""
        title = f'{self.company_name} Geographic Clusters\n'
        title += f'({self.num_clusters} clusters found, {self.num_outliers} outliers)'
        self.ax.set_title(title)

        # Create a legend for the labeled items (top 10 clusters + outliers)
        self.ax.legend(title="Top 10 Clusters & Outliers")

def generate_cluster_map(company_name):
    """Wrapper function to instantiate and run the ClusterMapGenerator."""
    if not company_name:
        print("Error: A company name must be provided.")
        return None
    generator = ClusterMapGenerator(company_name=company_name)
    return generator.generate()