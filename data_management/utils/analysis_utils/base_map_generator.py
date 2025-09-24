from abc import ABC, abstractmethod
import os
from datetime import datetime
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

class BaseMapGenerator(ABC):
    """
    An abstract base class for generating maps of Australia with store data.
    """
    def __init__(self, company_name=None):
        self.company_name = company_name
        self.fig = None
        self.ax = None
        self.gdf = None
        self.output_path = None

    def generate(self):
        """Public method to orchestrate the map generation process."""
        self._prepare_data()
        if self.gdf is None or self.gdf.empty:
            print("No data available to plot.")
            return None

        self._setup_figure()
        self._add_map_features()
        self._plot_data()
        self._set_title_and_legend()
        return self._save_figure()

    def _setup_figure(self):
        """Initializes the Matplotlib figure and axes with a map projection."""
        self.fig = plt.figure(figsize=(15, 12))
        self.ax = self.fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        self.ax.set_extent([112, 154, -44, -10], crs=ccrs.PlateCarree()) # Australia extent

    def _add_map_features(self):
        """Adds common geographic features to the map."""
        self.ax.add_feature(cfeature.LAND)
        self.ax.add_feature(cfeature.OCEAN)
        self.ax.add_feature(cfeature.COASTLINE)
        self.ax.add_feature(cfeature.BORDERS, linestyle=':')
        self.ax.add_feature(cfeature.STATES, linestyle=':')
        self.ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)

    def _save_figure(self):
        """Saves the generated map to a file."""
        if self.fig and self.output_path:
            output_dir = os.path.dirname(self.output_path)
            os.makedirs(output_dir, exist_ok=True)
            self.fig.savefig(self.output_path, dpi=300, bbox_inches='tight')
            plt.close(self.fig)
            return self.output_path
        return None

    @abstractmethod
    def _prepare_data(self):
        """Abstract method for subclasses to fetch and prepare their data.

        This method should set self.gdf (a GeoDataFrame) and self.output_path.
        """
        pass

    @abstractmethod
    def _plot_data(self):
        """Abstract method for subclasses to implement their specific plotting logic."""
        pass

    @abstractmethod
    def _set_title_and_legend(self):
        """Abstract method for subclasses to set the map's title and legend."""
        pass
