import pandas as pd
import geopandas
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os
from datetime import datetime

from companies.models.store import Store
from companies.models.company import Company

def generate_store_map(company_name=None):
    """
    Fetches stores from the database and generates a map of their locations.

    Args:
        company_name (str, optional): The name of a specific company to plot.
                                      If None, all stores will be plotted.
    """
    stores_query = Store.objects.filter(latitude__isnull=False, longitude__isnull=False).select_related('company')

    if company_name:
        # Check if the company exists
        try:
            company_obj = Company.objects.get(name__iexact=company_name)
            stores_query = stores_query.filter(company=company_obj)
            title = f'{company_obj.name} Store Locations'
            filename_part = company_obj.name.lower().replace(' ', '_')
        except Company.DoesNotExist:
            print(f"Error: Company '{company_name}' not found.")
            return None
    else:
        title = 'All Company Store Locations Across Australia'
        filename_part = 'all_companies'

    if not stores_query.exists():
        print("No stores with valid coordinates found for the given criteria.")
        return None

    # Prepare data for GeoDataFrame
    data = {
        'company': [store.company.name for store in stores_query],
        'latitude': [float(store.latitude) for store in stores_query],
        'longitude': [float(store.longitude) for store in stores_query]
    }
    df = pd.DataFrame(data)

    # Create GeoDataFrame
    gdf = geopandas.GeoDataFrame(
        df, geometry=geopandas.points_from_xy(df.longitude, df.latitude)
    )
    gdf.set_crs(epsg=4326, inplace=True)

    # Create a color map for companies
    companies = sorted(df['company'].unique())
    colors = plt.cm.get_cmap('tab10', len(companies))
    color_map = {company: colors(i) for i, company in enumerate(companies)}

    # Create the plot
    fig = plt.figure(figsize=(15, 12))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    ax.set_extent([112, 154, -44, -10], crs=ccrs.PlateCarree()) # Australia extent

    # Add map features
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.STATES, linestyle=':')

    # Plot each company's stores
    for company, color in color_map.items():
        subset = gdf[gdf['company'] == company]
        ax.scatter(subset.geometry.x, subset.geometry.y, 
                   transform=ccrs.PlateCarree(), color=color, 
                   label=company, s=15, alpha=0.7, edgecolors='k', linewidths=0.5)

    ax.set_title(title)
    ax.legend(title='Company')
    ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)

    # Create directory and save the figure
    output_dir = os.path.join('api', 'data', 'analysis', 'company_maps')
    os.makedirs(output_dir, exist_ok=True)
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    output_filename = f"{date_str}_{filename_part}.png"
    output_path = os.path.join(output_dir, output_filename)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return output_path
