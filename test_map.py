#!/usr/bin/env python
import xyzservices.providers as xyz
from bokeh.plotting import figure, show
from bokeh.tile_providers import get_provider
import numpy as np


RADIUS = 6378137.0 # in meters on the equator
def lat2y(a):
  return np.log(np.tan(np.pi / 4 + np.radians(a) / 2)) * RADIUS

def lon2x(a):
  return np.radians(a) * RADIUS


#tile_provider = get_provider(xyz.Esri.WorldTerrain)
tile_provider = get_provider(xyz.Esri.WorldPhysical)
# range bounds supplied in web mercator coordinates
p = figure(x_range=(lon2x(92), lon2x(93.5)), y_range=(lat2y(4), lat2y(10)),
           x_axis_type="mercator", y_axis_type="mercator")
p.add_tile(tile_provider)

show(p)
