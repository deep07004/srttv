#!/usr/bin/env python3
from obspy import Stream, UTCDateTime
import obspy.clients.seedlink.easyseedlink as sl
import threading
import matplotlib.pylab as plt
from matplotlib.animation import FuncAnimation
import time
import functools

def handle_data(trace):
    print('Received the following trace:')
    print(trace)
    tr.append(trace)
def plot_it(i,tr,fig):
    tr.merge()
    tr.sort()
    now = UTCDateTime()
    start = now - 300
    tr.trim(starttime=start, endtime=now)
    plt.cla()
    tr.plot(fig=fig)

tr = Stream()
client = sl.create_client('rtserve.iris.washington.edu', on_data=handle_data)
client.select_stream('G','ATD','BH?')
thread = threading.Thread(target=client.run)
thread.setDaemon(True)
thread.start()
time.sleep(20)
fig = plt.figure()
anni = FuncAnimation(fig, plot_it, fargs=(tr,fig), interval=100)
plt.tight_layout()
plt.show()