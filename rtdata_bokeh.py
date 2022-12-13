 #!/usr/bin/env python3
from obspy import Stream, UTCDateTime, read_inventory
import obspy.clients.seedlink.easyseedlink as sl
import threading, time
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, DatetimeTickFormatter, Range1d
from datetime import datetime, timedelta
from bokeh.layouts import gridplot, GridBox
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
#ii = int(np.floor(end - start)/trace.stats.delta)
#t1 = trace.stats.starttime
#t2 = trace.stats.endtime
#if t1 < start:
#    continue
#tt = [start+ i*trace.stats.delta for i in range(ii)]
#data = [np.nan for i in range(ii)]
#for i in range(len(tt)):
#    if tt[i]>= t1:
#        jj = i
#        break
#data[jj:jj+trace.stats.npts] = trace.data
#ttm = [t.datetime for t in tt]

tr = Stream()
client = sl.create_client('rtserve.iris.washington.edu', on_data=handle_data)
client.select_stream('G','*','BHZ')
thread = threading.Thread(target=client.run)
thread.setDaemon(True)
thread.start()

inv = read_inventory('G.xml')
channels = [ "%s.%s.%s.%s" %(nt.code, sta.code, ch.location_code, ch.code) 
    for nt in inv for sta in nt.stations for ch in sta.channels if ch.code=='BHZ']

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
        figures.append(figure(background_fill_color =bgc))
    else:
        figures.append(figure(x_range=figures[0].x_range, background_fill_color=bgc,
        plot_width=1500, plot_height=60))
    figures[i].line(x="x", y="y", color="black",legend_label=channels[i], line_width = 1, source=sources[i])
    figures[i].legend.location = "left"
    figures[i].legend.background_fill_alpha = 0.0
    figures[i].yaxis.major_label_orientation = np.radians(45)
    figures[i].xaxis.visible = False
    figures[i].yaxis.visible = False
    figures[i].ygrid.visible = False
    figures[i].min_border = 0
date_pattern = ["%Y-%m-%d\n%H:%M:%S"]
figures[0].xaxis.visible = True
figures[0].xaxis.formatter = DatetimeTickFormatter(
    seconds = date_pattern,
    minsec = date_pattern,
    minutes = date_pattern,
    hourmin = date_pattern,
    hours =date_pattern,
    days =date_pattern,
    months = date_pattern,
    years =  date_pattern
)
grid = gridplot(figures, ncols=1,sizing_mode= "scale_both",width=1500, height=25)
GridBox(spacing=0)
curdoc().add_root(grid)
curdoc().add_periodic_callback(update,5000)