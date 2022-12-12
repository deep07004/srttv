import numpy as np
import panel as pn

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource

pn.extension()

p = figure(sizing_mode='stretch_width', title='Bokeh streaming example')

xs = np.arange(1000)
ys = np.random.randn(1000).cumsum()
x, y = xs[-1], ys[-1]

cds = ColumnDataSource(data={'x': xs, 'y': ys})

p.line('x', 'y', source=cds)

bk_pane = pn.pane.Bokeh(p)
bk_pane.servable()
def stream():
    global x, y
    x += 1
    y += np.random.randn()
    cds.stream({'x': [x], 'y': [y]})
    pn.io.push_notebook(bk_pane) # Only needed when running in notebook context
    
pn.state.add_periodic_callback(stream, 100)
#PeriodicCallback(callback=<function stream at 0x7f77a917fdc0>, count=None, log=True, name='PeriodicCallback01380', period=100, running=True, timeout=None)
