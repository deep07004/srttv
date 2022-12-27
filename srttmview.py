import sys, os, yaml
from obspy import Stream, UTCDateTime, read_inventory, Inventory
import obspy.clients.seedlink.easyseedlink as sl
import threading, time
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, DatetimeTickFormatter, Legend, Range1d
from datetime import datetime, timedelta
from bokeh.layouts import gridplot, GridBox, row
import xyzservices.providers as xyz
from bokeh.tile_providers import get_provider
from bokeh.transform import factor_cmap
import numpy as np

def read(filepath):
    with open(filepath, 'r') as _f:
        return yaml.load(_f, Loader=yaml.FullLoader)

# Functions to convert lat/ lon to web mercator
RADIUS = 6378137.0 # in meters on the equator
def lat2y(a):
  return np.log(np.tan(np.pi / 4 + np.radians(a) / 2)) * RADIUS

def lon2x(a):
  return np.radians(a) * RADIUS

def stinfo(cfg):
    inv = Inventory()
    #for data in cfg["Inventory"]:
    #    _tmp = read_inventory(os.path.join(cfg["ROOT"],data[0]))
    #    inv.extend(_tmp)
    #stations = [ "%s.%s" %(nt.code, sta.code) for nt in inv for sta in nt.stations]
    #stations = list(set(stations))
    #stations.sort()
    stations = []
    prev_inv = ""
    for data in cfg["Inventory"]:
        if data[0] == prev_inv:
            continue
        _tmp = read_inventory(os.path.join(cfg["ROOT"],data[0]))
        inv.extend(_tmp)
        sta = [ "%s.%s" %(nt.code, sta.code) for nt in _tmp for sta in nt.stations]
        sta.sort()
        for ss in sta:
            stations.append(ss)
        prev_inv = data[0]
    IDs = {id:i for i, id in enumerate(stations)}
    Last_data = {id:UTCDateTime() - 86400 for i, id in enumerate(IDs.keys())}
    LAT = []
    LON = []
    for ndots in IDs.keys():
        ns = ndots.split('.')
        LAT.append(inv.select(network=ns[0],station=ns[1])[0].stations[0].latitude)
        LON.append(inv.select(network=ns[0],station=ns[1])[0].stations[0].longitude)
    LON = [lon2x(x) for x in LON]
    LAT = [lat2y(x) for x in LAT]
    return(stations, IDs, Last_data, LON, LAT)

def handle_data(trace):
    tr.append(trace)
    tr.merge()
def update():
    end = UTCDateTime()
    start = end - 300
    for f in figures:
        f.x_range.end = end.datetime
    trace_present =[]
    if len(tr) > 0:
        tr.trim(start,end)
        for trace in tr:
            _tmp = trace.id.split('.')
            id = "%s.%s" %(_tmp[0],_tmp[1])
            t1 = trace.stats.starttime
            rollover = int(900.0/trace.stats.delta)
            if t1 < start or id not in Last_data.keys():
                continue
            ii = 0
            if (t1 - Last_data[id]) > 1 and (t1 - Last_data[id]) < 1800:
                ii = int((t1 - Last_data[id])/trace.stats.delta)
                t1 = Last_data[id]
                Last_data[id] = trace.stats.endtime
            else:
                Last_data[id] = trace.stats.endtime
            st = datetime(t1.year,t1.month, t1.day,t1.hour, t1.minute, t1.second, t1.microsecond)
            tt = sorted([ st + timedelta(seconds =(j * trace.stats.delta)) for j in range(trace.stats.npts+ii)])
            if ii > 0:
                ndata = [np.nan for i in range(ii)]
                data = np.array(ndata)
            else:
                data = np.array([])
            data = np.append(data,trace.data)
            new_data = {'x':tt, 'y':data}
            sources[IDs[id]].stream(new_data,rollover)
            trace_present.append(id)
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
    xx = list(Last_data.keys())
    codes = [xx[i] for i  in indices] 
    new_data = {'x':X, 'y':Y, 'z':latancy,'code': codes}
    source_map.stream(new_data,rollover)

cfg = read("config.yaml")
tr = Stream()
# Connetct to the seedlink server and fetch data ...
for s in cfg["Inventory"]:
    client = sl.create_client(s[1],on_data=handle_data)
    client.select_stream('IN','*',s[2])
    thread = threading.Thread(target=client.run)
    thread.setDaemon(True)
    thread.start()


stations, IDs, Last_data, LON, LAT = stinfo(cfg)
sources = []
figures = []
date_pattern = ["%Y-%m-%d\n%H:%M:%S"]
for i in range(len(stations)):
    if i%2 ==0:
        bgc = '#fafafa'
    else:
        bgc = '#e1e1e1'
    sources.append(ColumnDataSource(data = dict(x = [], y = [])))
    if i==0:
        figures.append(figure(background_fill_color =bgc,x_axis_location="above",
        plot_width=500, plot_height=51,tools=""))
    elif i==len(stations)-1:
        figures.append(figure(background_fill_color =bgc, x_range=figures[0].x_range,plot_width=500, 
        plot_height=41,tools=""))
    else:
        figures.append(figure(x_range=figures[0].x_range, background_fill_color=bgc,
        plot_width=500, plot_height=11, tools=""))
    r = figures[i].line(x="x", y="y", color="black", line_width = 1,
        source=sources[i])
    legend = Legend(items=[(stations[i], [r])], location="center")
    figures[i].add_layout(legend, 'left')
    figures[i].legend.background_fill_alpha = 0.0
    figures[i].xaxis.visible = False
    figures[i].yaxis.visible = False
    figures[i].ygrid.visible = False
    figures[i].min_border_left = 0
    figures[i].x_range.follow = "end"
    figures[i].x_range.follow_interval = 600000 # Should be same as rollover miliseconds
    figures[i].x_range.range_padding = 0
    #figures[i].x_range.only_visible = True
    if not i == 0 or i == len(stations):
        figures[i].min_border = 0
for i in [0,-1]:
    figures[i].xaxis.visible = True
    figures[i].xaxis.formatter = DatetimeTickFormatter(
        seconds = date_pattern,
        minsec = date_pattern,
        minutes = date_pattern,
        hourmin = date_pattern,
        hours =date_pattern,
        days =date_pattern,
        months = date_pattern,
        years =  date_pattern
    )
TOOLTIPS = [("Staion:", "@code")]
source_map = ColumnDataSource(data = dict(x = [], y = [], z = [], code = []))
xyz.MapTiler.Satellite["key"]  = "NpGj1MyZ7hw1J2ovQAEF"
tile_provider = get_provider(xyz.MapTiler.Satellite)
#tile_provider = get_provider(xyz.Esri.WorldPhysical)
p = figure(plot_width=700, plot_height=700, x_range=(lon2x(65), lon2x(100)), y_range=(lat2y(5), lat2y(35)),
           x_axis_type="mercator", y_axis_type="mercator",tools="pan,wheel_zoom,reset",tooltips=TOOLTIPS,
           title="RTSMN")
p.add_tile(tile_provider)
cmap = ['#00FFFF', '#00FF00', '#FFFF00', '#FFA500', '#FF0000', '#BEBDB8', '#828282', '#000000']
#latancy_sorted =[' < 20', ' (20,60)', ' > 1d']
latancy_sorted =[' < 20', ' (20,60]', ' (60,180]', ' (180,600]', ' (600,1800]', 
' (1800,0.5d]',' (0.5d,1d]',' > 1d']
p.triangle(x='x',y='y',size=16, source=source_map, legend_field="z", color=factor_cmap("z", cmap, latancy_sorted),
line_width=0.45,line_color='#000000')
p.xgrid.visible=False
p.ygrid.visible=False
p.legend.background_fill_color='white'
p.legend.border_line_width = 0.35
p.legend.border_line_color = 'black'
p.legend.title = "Latancy in s"
p.title.align = "center"
p.title.text_font_size = "18px"

# Andaman
tile_provider = get_provider(xyz.Esri.WorldPhysical)
pa = figure(plot_width=200, plot_height=700, x_range=(lon2x(91.5), lon2x(95)), y_range=(lat2y(6.5), lat2y(13.5)),
           x_axis_type="mercator", y_axis_type="mercator",tools="pan,wheel_zoom,reset",tooltips=TOOLTIPS,
           title ="Andaman SMA")
pa.add_tile(tile_provider)
pa.title.align = "center"
pa.title.text_font_size = "18px"
cmap = ['#00FFFF', '#00FF00', '#FFFF00', '#FFA500', '#FF0000', '#BEBDB8', '#828282', '#000000']
#latancy_sorted =[' < 20', ' (20,60)', ' > 1d']
latancy_sorted =[' < 20', ' (20,60]', ' (60,180]', ' (180,600]', ' (600,1800]', 
' (1800,0.5d]',' (0.5d,1d]',' > 1d']
pa.triangle(x='x',y='y',size=14, source=source_map, color=factor_cmap("z", cmap, latancy_sorted),
line_width=0.45,line_color='#000000')
grid = gridplot(figures,merge_tools=True, toolbar_options={"logo":None}, ncols=1,sizing_mode= "scale_both")
GridBox(spacing=0)
grid1 = gridplot([p,pa],merge_tools=True, toolbar_options={"logo":None}, ncols=2,sizing_mode= "fixed")
curdoc().add_root(row(grid1,grid))
curdoc().add_periodic_callback(update,2000)