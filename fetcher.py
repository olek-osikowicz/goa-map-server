# import prettymaps
from matplotlib import pyplot as plt
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
import geopandas as gpd
from geopandas import GeoDataFrame
from shapely.affinity import rotate
import numpy as np
import drawsvg as dw
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
    def __init__(self, bbox_cords: list, map_space_dims: list) -> None:

        #Process bbox
        self.bbox_cords = bbox_cords
        self.bbox_pol = box(*bbox_cords)
        self.bbox_gdf = GeoDataFrame(geometry=[self.bbox_pol],
                                     crs=GEO_2D_CRS).to_crs(MERCATOR_CRS)

        self.mercator_bbox = self.bbox_gdf.total_bounds
        self.centroid_mercator = self.bbox_gdf.geometry.centroid.iloc[0]

        self.map_space_dims = map_space_dims
        self.set_scale()

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
        osm_gdf = ox.geometries_from_polygon(
            self.bbox_pol, tags={tags: True} if type(tags) == str else tags)

        osm_gdf = self.transformGDF(osm_gdf)

        if scale:
            osm_gdf = self.scaleToPoster(osm_gdf)
        return osm_gdf

    def scaleToPoster(self, gdf):

        #center of map canvas
        map_space_center_x = self.map_space_dims[0] + self.map_space_dims[2]/2
        map_space_center_y = self.map_space_dims[1] + self.map_space_dims[3]/2
        log.debug(f"{map_space_center_x = }, {map_space_center_y = }")

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
        sea_water_gdf = gpd.read_file(SEA_WATER_POLYGONS_PATH)
        log.debug("Sea water polygons retrieved")
        sea_water_gdf = self.transformGDF(sea_water_gdf)
        log.debug("Sea water transformed")

        #no scaling as we are not done transforming yet
        inland_water_gdf = self.get_osmGDF(WATER_TAGS, scale=False)
        log.debug("Inland water retrieved")

        if sea_water_gdf.empty:
            log.debug("Sea water is empty, only inland water avalable")
            return inland_water_gdf

        gdf = sea_water_gdf.append(inland_water_gdf)
        log.debug("Appended")
        gdf = self.mergeGeometries(gdf)
        log.debug("Water merged")

        gdf = self.scaleToPoster(gdf)
        log.debug("Scaled to poster")

        return gdf

    def get_streetsGDF(self):
        graph = ox.graph_from_polygon(
            self.bbox_pol,
            truncate_by_edge=True,
        )

        gdf = ox.graph_to_gdfs(graph, nodes=False)

        def unpack_lists(highway_type):
            if isinstance(highway_type, str):
                return highway_type
            
            return highway_type[0]

        gdf['highway'] = gdf['highway'].apply(unpack_lists)
        gdf = gdf.reset_index()[['highway', 'geometry']]
        gdf = gdf.drop_duplicates()
        # .clip_by_rect(*self.bbox_cords)
        gdf = gdf.rename(columns={'highway': 'way_type'})
        gdf = gdf.to_crs(MERCATOR_CRS)
        gdf = self.scaleToPoster(gdf)

        return gdf

if __name__ == "__main__":

    f = Fetcher(bbox_cords=[4.4525568, 51.8582984, 4.5445646, 51.9585962])
    x = f.getWaterGDF()
    log.debug(x)
