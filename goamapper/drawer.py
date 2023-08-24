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
import geopandas as gpd
from geopandas import GeoDataFrame
from shapely.affinity import rotate
import numpy as np
import drawsvg as dw
import logging as log


def drawPath(p: dw.Path, geom) -> dw.Path:
    points = list(geom.coords)
    first = points.pop(0)

    p.M(*first)  # move to first

    for point in points:
        p.L(*point)

    return p


def drawAreas(gdf: GeoDataFrame, fill='blue', id='water') -> dw.Group:

    group = dw.Group(id=id, fill=fill)



    for geom in gdf.geometry:

        p = dw.Path()

        # draw exterior
        p = drawPath(p, geom.exterior)

        # draw each hole
        for interior in geom.interiors:
            p = drawPath(p, interior)

        group.append(p)

    return group

def drawCircut(gdf: GeoDataFrame, layer_info: dict):
    # width = layer_info['width']
    # stroke = layer_info['stroke']
    group = dw.Group(id="circut", fill="none", close=False,
                    stroke_linecap='round', stroke_linejoin='round',**layer_info)
    

    for geom in gdf.geometry:
        p = dw.Path()
        p = drawPath(p, geom)
        group.append(p)

    return group

def drawWays(gdf: GeoDataFrame, layer_info: dict, id='ways'):

    main_group = dw.Group(id=id, fill="none", close=False,
                          stroke_linecap='round', stroke_linejoin='round',)

    base_width = layer_info['base_width']
    for street_type, v in layer_info['types'].items():
        # for each street type

        width = base_width*v['relative_width']
        street_group = dw.Group(
            id=street_type, stroke=v['stroke'], stroke_width=width, )

        street_data = gdf[gdf['way_type'] == street_type]

        for geom in street_data.geometry:
            p = dw.Path()
            p = drawPath(p, geom)
            street_group.append(p)

        main_group.append(street_group)

    return main_group


if __name__ == "__main__":
    pass