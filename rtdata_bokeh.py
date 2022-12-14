 #!/usr/bin/env python3
from obspy import Stream, UTCDateTime, read_inventory
import obspy.clients.seedlink.easyseedlink as sl
import threading, time
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, DatetimeTickFormatter, Legend, Range1d
from datetime import datetime, timedelta
from bokeh.layouts import gridplot, GridBox
import numpy as np

def handle_data(trace):
    tr.append(trace)
    tr.merge()
def update():
    end = UTCDateTime()
    start = end - 300
    trace_present =[]
    if len(tr) > 0:
        tr.trim(start,end)
        for trace in tr:
            t1 = trace.stats.starttime
            rollover = int(900.0/trace.stats.delta)
            if t1 < start:
                continue
            ii = 0
            if (t1 - Last_data[trace.id]) > 1 :
                ii = int((t1 - Last_data[trace.id])/trace.stats.delta)
                t1 = Last_data[trace.id]
                Last_data[trace.id] = trace.stats.endtime
            else:
                Last_data[trace.id] = trace.stats.endtime
            st = datetime(t1.year,t1.month, t1.day,t1.hour, t1.minute, t1.second, t1.microsecond)
            tt = sorted([ st + timedelta(seconds =(j * trace.stats.delta)) for j in range(trace.stats.npts+ii)])
            if ii > 0:
                ndata = [np.nan for i in range(ii)]
                data = np.array(ndata)
            else:
                data = np.array([])
            data = np.append(data,trace.data)
            new_data = {'x':tt, 'y':data}
            sources[IDs[trace.id]].stream(new_data,rollover)
            trace_present.append(trace.id)
        tr.clear()
    

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
channels = [ "%s.%s.%s.%s" %(nt.code, sta.code, ch.location_code, ch.code) 
    for nt in inv for sta in nt.stations for ch in sta.channels if ch.code=='HHZ']
IDs = {id:i for i, id in enumerate(channels)}
Last_data = {id:UTCDateTime() for i, id in enumerate(channels)}
sources = []
figures = []
date_pattern = ["%Y-%m-%d\n%H:%M:%S"]
for i in range(len(channels)):
    if i%2 ==0:
        bgc = '#fafafa'
    else:
        bgc = '#e1e1e1'
    sources.append(ColumnDataSource(data = dict(x = [], y = [])))
    if i==0:
        figures.append(figure(background_fill_color =bgc,x_axis_location="above",
        plot_width=1500, plot_height=72))
    elif i==len(channels)-1:
        figures.append(figure(background_fill_color =bgc, x_range=figures[0].x_range,plot_width=1500, plot_height=69))
    else:
        figures.append(figure(x_range=figures[0].x_range, background_fill_color=bgc,
        plot_width=1500, plot_height=25))
    r = figures[i].line(x="x", y="y", color="black", line_width = 1,
        source=sources[i])
    legend = Legend(items=[(channels[i], [r])], location="center")
    figures[i].add_layout(legend, 'left')
    figures[i].legend.background_fill_alpha = 0.0
    figures[i].xaxis.visible = False
    figures[i].yaxis.visible = False
    figures[i].ygrid.visible = False
    figures[i].min_border_left = 0
    figures[i].x_range.follow = "end"
    figures[i].x_range.follow_interval = 720000 # Should be same as rollover miliseconds
    if not i == 0 or i == len(channels):
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
grid = gridplot(figures,merge_tools=True, ncols=1,sizing_mode= "scale_both")
GridBox(spacing=0)
curdoc().add_root(grid)
curdoc().add_periodic_callback(update,2000)