 #!/usr/bin/env python3
from obspy import Stream, UTCDateTime, read_inventory
import obspy.clients.seedlink.easyseedlink as sl
import threading, time
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, DatetimeTickFormatter, Legend, Range1d
from datetime import datetime, timedelta
from bokeh.layouts import gridplot, GridBox
import xyzservices.providers as xyz
from bokeh.tile_providers import get_provider
from bokeh.transform import factor_cmap
import numpy as np

RADIUS = 6378137.0 # in meters on the equator
def lat2y(a):
  return np.log(np.tan(np.pi / 4 + np.radians(a) / 2)) * RADIUS

def lon2x(a):
  return np.radians(a) * RADIUS

def handle_data(trace):
    tr.append(trace)
    tr.merge()
def update_map():
    if len(tr) > 0:
        for trace in tr:
            t1 = trace.stats.starttime
            _tmp = trace.id.split('.')
            id = "%s.%s" %(_tmp[0],_tmp[1])            
            Last_data[id] = trace.stats.endtime
        tr.clear()
    tt = UTCDateTime()
    rollover = len(LAT)
    latancy = []
    for k in Last_data.keys():
        x = tt - Last_data[k]
        if x < 20:
            latancy.append(' < 20')
        elif x >=20 and x < 60:
            latancy.append(' (20,60]')
        elif x >=60 and x < 180:
            latancy.append(' (60,180]')
        elif x >=180 and x < 600:
            latancy.append(' (180,600]')
        elif x >=600 and x < 1800:
            latancy.append(' (600,1800]')
        elif x >=1800 and x < 43200:
            latancy.append(' (1800,0.5d]')
        elif x >=43200 and x < 86400:
            latancy.append(' (0.5d,1d]')
        else:
            latancy.append(' > 1d')
    indices = sorted(range(len(latancy)), key=lambda index: latancy[index])
    latancy.sort()
    X =  [LON[i] for i in indices]
    Y =  [LAT[i] for i in indices]
    new_data = {'x':X, 'y':Y, 'z':latancy}
    print(latancy)
    source.stream(new_data,rollover)

tr = Stream()
client = sl.create_client('172.16.4.91:18121', on_data=handle_data)
client.select_stream('IN','*','HHZ')
thread = threading.Thread(target=client.run)
thread.setDaemon(True)
thread.start()
client1 = sl.create_client('rtserve.iris.washington.edu', on_data=handle_data)
client1.select_stream('IN','*','HHZ')
thread = threading.Thread(target=client1.run)
thread.setDaemon(True)
thread.start()
client2 = sl.create_client('172.16.3.244:18003', on_data=handle_data)
client2.select_stream('IN','*','HHZ')
thread = threading.Thread(target=client2.run)
thread.setDaemon(True)
thread.start()

inv = read_inventory('IN_RTSMN.dataless.xml')
stations = [ "%s.%s" %(nt.code, sta.code) 
    for nt in inv for sta in nt.stations]
IDs = {id:i for i, id in enumerate(stations)}
Last_data = {id:UTCDateTime()-86400 for i, id in enumerate(IDs.keys())}
LAT = []
LON = []
for ndots in IDs.keys():
    ns = ndots.split('.')
    LAT.append(inv.select(network=ns[0],station=ns[1])[0].stations[0].latitude)
    LON.append(inv.select(network=ns[0],station=ns[1])[0].stations[0].longitude)
LON = [lon2x(x) for x in LON]
LAT = [lat2y(x) for x in LAT]
tt = UTCDateTime()
source = ColumnDataSource(data = dict(x = [], y = [], z = []))
tile_provider = get_provider(xyz.Esri.WorldTerrain)
p = figure(plot_width=800, plot_height=650, x_range=(lon2x(65), lon2x(100)), y_range=(lat2y(5), lat2y(35)),
           x_axis_type="mercator", y_axis_type="mercator")
p.add_tile(tile_provider)
cmap = ['#00FFFF', '#00FF00', '#FFFF00', '#FFA500', '#FF0000', '#BEBDB8', '#828282', '#000000']
#latancy_sorted =[' < 20', ' (20,60)', ' > 1d']
latancy_sorted =[' < 20', ' (20,60]', ' (60,180]', ' (180,600]', ' (600,1800]', 
' (1800,0.5d]',' (0.5d,1d]',' > 1d']
p.triangle(x='x',y='y',size=14, source=source, legend_field="z", color=factor_cmap("z", cmap, latancy_sorted),
line_width=0.45,line_color='#000000')
p.legend.background_fill_color='white'
p.legend.border_line_width = 0.35
p.legend.border_line_color = 'black'
p.legend.title = "Latancy in s"

# Andaman
p1 = figure(plot_width=200, plot_height=650, x_range=(lon2x(91.5), lon2x(95)), y_range=(lat2y(6.5), lat2y(13.5)),
           x_axis_type="mercator", y_axis_type="mercator")
p1.add_tile(tile_provider)
cmap = ['#00FFFF', '#00FF00', '#FFFF00', '#FFA500', '#FF0000', '#BEBDB8', '#828282', '#000000']
#latancy_sorted =[' < 20', ' (20,60)', ' > 1d']
latancy_sorted =[' < 20', ' (20,60]', ' (60,180]', ' (180,600]', ' (600,1800]', 
' (1800,0.5d]',' (0.5d,1d]',' > 1d']
p1.triangle(x='x',y='y',size=14, source=source, color=factor_cmap("z", cmap, latancy_sorted),
line_width=0.45,line_color='#000000')
grid = gridplot([p,p1],merge_tools=True, ncols=2,sizing_mode= "fixed")
curdoc().add_root(grid)
curdoc().add_periodic_callback(update_map,2000)