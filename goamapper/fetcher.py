# import prettymaps
import osmnx as ox
from shapely.geometry import (
    box,
    Point,
    Polygon,
    MultiPolygon,
    LineString,
    MultiLineString,
    LinearRing,
)
import pandas as pd
import geopandas as gpd
from geopandas import GeoDataFrame
from shapely.affinity import rotate
import logging as log

# CONSTANS

MERCATOR_CRS = "EPSG:3857"
GEO_2D_CRS = "EPSG:4326"
SEA_WATER_POLYGONS_PATH = "assets/water-polygons-split-4326/water_polygons.shx"

WATER_TAGS = {
    "natural": [
        "water",
        "bay"
    ]
}


class Fetcher():
    def __init__(self, map_space_dims: list, bbox: list = None, place_name: str = None, radius: int = 10_000) -> None:

        if bbox:
            log.debug("Using explicit bouding box")
            self.set_area_from_bbox(bbox)
        elif place_name:
            log.debug("Geocoding bouding box")
            self.set_area_from_place_and_radius(place_name, radius)
        else:
            raise ValueError("Invalid area to be mapped!")


        self.map_space_dims = map_space_dims
        self.set_scale()

    def set_area_from_bbox(self, bbox_cords):
        self.bbox_cords = bbox_cords
        log.debug(f"{bbox_cords = }")
        self.bbox_pol = box(*bbox_cords)
        self.bbox_gdf = GeoDataFrame(geometry=[self.bbox_pol],
                                     crs=GEO_2D_CRS).to_crs(MERCATOR_CRS)

        self.mercator_bbox = self.bbox_gdf.total_bounds
        self.centroid_mercator = self.bbox_gdf.geometry.centroid.iloc[0]


    def set_area_from_place_and_radius(self, place_name: str, radius: int):
        point = ox.geocode(place_name)
        gdf = GeoDataFrame(geometry=[Point(point[::-1])], crs=GEO_2D_CRS)
        gdf = gdf.to_crs(MERCATOR_CRS)

        gdf = gdf.buffer(radius, cap_style=3)
        self.bbox_gdf = gdf

        self.mercator_bbox = self.bbox_gdf.total_bounds
        self.centroid_mercator = self.bbox_gdf.geometry.centroid.iloc[0]

        gdf = gdf.to_crs(GEO_2D_CRS)

        self.bbox_cords = gdf.total_bounds
        log.debug(f"{self.bbox_cords = }")
        self.bbox_pol = box(*self.bbox_cords)


    def mergeGeometries(self, gdf: GeoDataFrame):
        shape = gdf.geometry.unary_union
        if shape:
            gdf = gpd.GeoDataFrame(geometry=[shape], crs=GEO_2D_CRS)
            gdf = gdf.explode(index_parts=False)

        return gdf

    def set_scale(self):
        bounds = self.mercator_bbox
        width = bounds[2]-bounds[0]
        height = bounds[3]-bounds[1]
    
        # hole-width
        s1 = self.map_space_dims[2]/width

        # hole-heigh
        s2 = self.map_space_dims[3]/height
        self.s = max(s1,s2)

    def transformGDF(self, gdf: GeoDataFrame):
        gdf = (gdf
               .reset_index()
               .clip_by_rect(*self.bbox_cords)
               .explode(index_parts=False))

        gdf = gdf[gdf.geom_type == 'Polygon']

        # merge polygons
        gdf = self.mergeGeometries(gdf)
        gdf = gdf.to_crs(MERCATOR_CRS)

        return gdf

    def get_osmGDF(self, tags, scale=True):

        try:
            osm_gdf = ox.features_from_polygon(
                self.bbox_pol, tags=tags)
        except Exception:
            #return empty geometry if something goes wrong
            return gpd.GeoSeries([])

        osm_gdf = self.transformGDF(osm_gdf)

        if scale:
            osm_gdf = self.scaleToPoster(osm_gdf)
        return osm_gdf

    def scaleToPoster(self, gdf):

        #center of map canvas
        map_space_center_x = self.map_space_dims[0] + self.map_space_dims[2]/2
        map_space_center_y = self.map_space_dims[1] + self.map_space_dims[3]/2
        log.debug(f"{map_space_center_x = }, {map_space_center_y = }")

        if not gdf.geometry.empty:
            gdf['geometry'] = (gdf['geometry']
                .translate(xoff=-self.centroid_mercator.x, yoff=-self.centroid_mercator.y)

                # inverse Y- axis
                .scale(xfact=1, yfact=-1, zfact=1.0, origin=(0, 0))

                # scale to fit poster
                .scale(xfact=self.s, yfact=self.s, zfact=1.0, origin=(0, 0))

                # shift to poster center
                .translate(xoff=map_space_center_x, yoff=map_space_center_y))
        
        return gdf

    def get_waterGDF(self):
        log.debug("Retrieving sea water polygons")
        sea_water_gdf = gpd.read_file(SEA_WATER_POLYGONS_PATH, bbox=self.bbox_pol)
        log.debug("Sea water polygons retrieved")
        sea_water_gdf = self.transformGDF(sea_water_gdf)
        log.debug("Sea water transformed")

        #no scaling as we are not done transforming yet
        inland_water_gdf = self.get_osmGDF(WATER_TAGS, scale=False)
        log.debug("Inland water retrieved")
            
        if inland_water_gdf.empty:
            gdf = sea_water_gdf
        else:
            gdf = pd.concat([inland_water_gdf, sea_water_gdf])

        log.debug("Appended")
        gdf = self.mergeGeometries(gdf)
        log.debug("Water merged")

        gdf = self.scaleToPoster(gdf)
        log.debug("Scaled to poster")

        return gdf

    def get_streetsGDF(self, street_types: list):

        tags = {"highway": street_types}
        gdf = ox.features_from_polygon(self.bbox_pol, tags=tags)

        def unpack_lists(highway_type):
            if isinstance(highway_type, str):
                return highway_type
            
            return highway_type[0]

        gdf['highway'] = gdf['highway'].apply(unpack_lists)

        gdf = gdf.reset_index()[['highway', 'geometry']]
        gdf = gdf.explode(index_parts=False)
        gdf = gdf[gdf.geom_type == 'LineString']
        gdf = gdf.drop_duplicates()
        # .clip_by_rect(*self.bbox_cords)
        gdf = gdf.rename(columns={'highway': 'way_type'})
        gdf = gdf.to_crs(MERCATOR_CRS)
        gdf = self.scaleToPoster(gdf)

        return gdf

if __name__ == "__main__":

    pass