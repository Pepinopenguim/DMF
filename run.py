import main
import plotly.graph_objects as go
import numpy as np

beam = main.Beam(100, 300, EI = 3141592.65359)

beam.add_bearing(0, "xy")
beam.add_bearing(100, "xy")

beam.add_load(-100)
strg = ""
solution = beam.solve_deformation()



x = np.linspace(0, 100, 304) 

fig = go.Figure([
        go.Scatter(
            x = x,
            y = solution
        )
    ])

fig.update_yaxes(scaleanchor="x")

fig.update_layout(template = "simple_white")

fig.show()