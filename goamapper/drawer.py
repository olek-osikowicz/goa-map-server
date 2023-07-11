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


street_info = {
    "base_width": 1,
    "types": {
        "footway": {
            "stroke": "#ff2500",
            "relative_width": 1
        },
        "pedestrian": {
            "stroke": "#ff3a00",
            "relative_width": 2
        },
        "unclassified": {
            "stroke": "#ff5000",
            "relative_width": 2
        },
        "service": {
            "stroke": "#ff6500",
            "relative_width": 2
        },
        "living_street": {
            "stroke": "#ff7a00",
            "relative_width": 3
        },
        "residential": {
            "stroke": "#ff7a00",
            "relative_width": 3
        },
        "cycleway": {
            "stroke": "#ff9000",
            "relative_width": 3.5
        },
        "tertiary": {
            "stroke": "#ffa600",
            "relative_width": 3.5
        },
        "secondary": {
            "stroke": "#ffbb00",
            "relative_width": 4
        },
        "primary": {
            "stroke": "#ffd100",
            "relative_width": 4.5
        },
        "trunk": {
            "stroke": "#ffe600",
            "relative_width": 5
        },
        "motorway": {
            "stroke": "#ffff00",
            "relative_width": 5
        }
    }
}


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
    base_width = street_info['base_width']
    types = street_info['types']

    for name ,v in types.items():
        print(f"{name}, {v['stroke']}, {v['relative_width']}")
