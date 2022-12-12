 #!/usr/bin/env python3
from obspy import Stream, UTCDateTime, read_inventory
import obspy.clients.seedlink.easyseedlink as sl
import threading, time
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, DatetimeTickFormatter, Range1d
from datetime import datetime, timedelta
from bokeh.layouts import gridplot
import numpy as np

def handle_data(trace):
    tr.append(trace)
    tr.merge()
def update():
    end = UTCDateTime()
    start = end - 300
    if len(tr) > 0:
        tr.trim(start,end)
        for trace in tr:
            t1 = trace.stats.starttime
            if t1 < start:
                continue
            st = datetime(t1.year,t1.month, t1.day,t1.hour, t1.minute, t1.second, t1.microsecond)
            tt = sorted([ st + timedelta(seconds =(j * trace.stats.delta)) for j in range(trace.stats.npts)])
            data = trace.data
            new_data = {'x':tt, 'y':data}
            sources[IDs[trace.id]].stream(new_data,30000)
        tr.clear()
    #for i in range(3):
    #    figures[i].x_range=Range1d(datetime.utcnow()-timedelta(seconds=300), datetime.utcnow())
#    else:
#        new_data = {'x':[], 'y':[]}
#        source.stream(new_data,3000)
    
tr = Stream()
client = sl.create_client('172.16.4.91:18121', on_data=handle_data)
client.select_stream('IN','*','HHZ')
thread = threading.Thread(target=client.run)
thread.setDaemon(True)
thread.start()

inv = read_inventory('IN_RTSMN.dataless.xml')
channels = [ "%s.%s.%s.%s" %(nt.code, sta.code, ch.location_code, ch.code) 
    for nt in inv for sta in nt.stations for ch in sta.channels if ch.code[-1]=='Z']

IDs = {id:i for i, id in enumerate(channels)}
sources = []
figures = []
for i in range(len(channels)):
    if i%2 ==0:
        bgc = '#fafafa'
    else:
        bgc = '#e1e1e1'
    sources.append(ColumnDataSource(data = dict(x = [], y = [])))
    if i==0:
        figures.append(figure(background_fill_color =bgc,title="Left Title", title_location="left"))
    else:
        figures.append(figure(x_range=figures[0].x_range, background_fill_color=bgc))
    figures[i].line(x="x", y="y", color="black",legend_label=channels[i], line_width = 1, source=sources[i])
    figures[i].legend.location = "left"
    figures[i].yaxis.major_label_orientation = np.radians(45)
    figures[i].xaxis.visible = False
    figures[i].yaxis.visible = False
date_pattern = ["%Y-%m-%d\n%H:%M:%S"]
figures[1].xaxis.visible = True
figures[1].xaxis.formatter = DatetimeTickFormatter(
    seconds = date_pattern,
    minsec = date_pattern,
    minutes = date_pattern,
    hourmin = date_pattern,
    hours =date_pattern,
    days =date_pattern,
    months = date_pattern,
    years =  date_pattern
)
grid = gridplot(figures, ncols=1, width=1500, height=60)
curdoc().add_root(grid)
curdoc().add_periodic_callback(update,5000)