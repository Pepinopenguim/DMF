# Import necessary libraries
import tkinter as tk
import numpy as np
from tkinter import ttk

# This class holds the data for the beam simulation
class Model():
        # Initialize the model with default values
        def __init__(self):
                # Length of the beam
                self.length = 10
                # Number of nodes for calculation
                self.total_node_num = 30
                # List to store node data (position, support)
                # supports are defined as strings: e.g. "xyz", "xz", "xy"
                # Where z is rotation 
                self.nodes = []

                # List to store point loads (magnitude, position, angle)
                # note that angle is in degrees
                self.point_loads = []
                # List to store distributed loads (position tuple, magnitude)
                self.loads = []
                # List to keep track of the order efforts were added
                self.order_of_efforts = []

                self.deflections = np.nan

                # List to store supports (position, support_type)
                self.supports = []
                # Dictionary for material properties
                self.materials = {
                        "E":2e11, # Young's Modulus in Pascals
                        "I":10e-6, # Moment of inertia in m^4
                }

                self.solved = False

        # Method to find the maximum force applied to the beam
        def get_max_force(self):
                max_force = 0
                # Check point loads
                for magnitude, _, _ in self.point_loads:
                        if abs(magnitude) > max_force:
                                max_force = abs(magnitude)
                # Check distributed loads
                for _, magnitude in self.loads:
                        if abs(magnitude) > max_force:
                                max_force = abs(magnitude)
                return max_force
        
        # Method to set a new length for the beam
        def set_properties(self, new_length:float, new_E:float, new_I:float):
                self.length = new_length
                self.materials["E"] = new_E
                self.materials["I"] = new_I
                # Check if existing supports are still valid with the new length
                self._check_valid_elements()
                self.solved = False
                return True
        
        # Method to remove the most recently added support
        def remove_last_support(self):
                if self.supports: # Check if the list is not empty
                        self.supports.pop()
                        self.solved = False
                        return True
                return False
        
        def _restart_order_of_efforts(self):
                self.order_of_efforts = []
                self.solved = False

                for _ in self.loads:
                        self.order_of_efforts.append("load")
                
                for _ in self.point_loads:
                        self.order_of_efforts.append("point")

        # Method to remove the most recently added effort (load or point force)
        def remove_last_effort(self):
                if self.order_of_efforts:
                        # Get the type of the last effort
                        last_effort = self.order_of_efforts.pop()
                        self.solved = False
                else:
                        return False

                # Remove the effort from the corresponding list based on its type
                match last_effort:
                        case "point":
                                self.point_loads.pop()
                        case "load":
                                self.loads.pop()
                return True

        # Method to validate supports, removing any outside the beam's length
        def _check_valid_elements(self):
                for i, (pos, _) in enumerate(self.supports):
                        if not 0 <= pos <= self.length:
                                # Removes supports when length (L) is changed
                                self.supports.pop(i)
                
                for i, ((pos1, pos2), _) in enumerate(self.loads):
                        if not 0 <= pos1 <= self.length or not 0 <= pos2 <= self.length:
                                self.loads.pop(i)
                
                for i, (_, pos, _) in enumerate(self.point_loads):
                        if not 0 <= pos <= self.length:
                                self.point_loads.pop(i)
                
                self._restart_order_of_efforts()
                                
        # Method to set the total number of nodes for calculations
        def set_total_node_num(self, new_node_num:int):
                self.total_node_num = new_node_num
                self.solved = False
                return True

        # Method to add a new support to the beam
        def add_support(self, position:float, support_type:str):
                self.supports.append((position, support_type))
                self.solved = False
                return True

        # Method to add a concentrated (point) load
        def add_point_load(self, magnitude:float, position:float, angle:float = 90):
                # Check if magnitude and angle values are valid
                if not isinstance(magnitude, (float, int)) or not 0 <= angle <= 180:
                        return False
                
                # Check if position is within the beam's length
                if 0 <= position <= self.length:
                        self.point_loads.append((magnitude, position, angle))
                        self.order_of_efforts.append("point")
                        self.solved = False
                        return True
                return False
        
        # Method to add a distributed load
        def add_loads(self, pos_limits:tuple, magnitude:float):

                pos0, pos1 = pos_limits

                self.loads.append(((pos0, pos1), magnitude))
                self.order_of_efforts.append("load")
                self.solved = False
                return True

        def solve_FDM(self):
                if not self.solved:
                        try:
                                # 1. Initialization
                                N = self.total_node_num
                                h = self.length / (N - 1)  # Step size
                                E = self.materials["E"]
                                I = self.materials["I"]

                                # 2. Assemble the stiffness matrix and force vector
                                K = self._build_stiffness_matrix(N)
                                F = self._build_load_vector(N, h)

                                # 3. Add boundaries
                                K, F = self._apply_boundary_conditions(K, F, N, h)
                                F_scaled = F * (h**4 / (E * I))
                                v = np.linalg.solve(K, F_scaled) # v is the deflection vector

                                # 4. Calculate and store results
                                self.node_positions = np.linspace(0, self.length, N)
                                self.deflections = v
                                self.slopes = np.gradient(v, h)

                                # Moment M = E*I*v''
                                self.moments = E * I * np.gradient(self.slopes[2:-3], h)

                                # Shear V = E*I*v'''
                                self.shears = np.gradient(self.moments, h)
                                self.shears[0] = self.shears[1]
                                self.shears[-1] = self.shears[-2]

                                # Normal force (simplified calculation)
                                # self.normals = self._calculate_normal_force(N, h)
                                # to do

                                self.solved = True
                                return True
                        except np.linalg.LinAlgError as e:
                                print(f"Beam may be unstable: {e}")
                                return False
                        except Exception as e:
                                print(e)
                                return False

        def _get_node_by_pos(self, pos, h) -> int:
                N = self.total_node_num
                j = int(np.round(pos / h)) # Node index of the support
                j = min(N - 1, max(0, j))  # Clamp index to be safe

                return j

        def _build_load_vector(self, N, h):
                
                F = np.zeros(N) # define N sized vector

                for magnitude, pos, angle in self.point_loads:
                        # get node closest to position
                        j = self._get_node_by_pos(pos, h)

                        # convert force P to equivalent distribution q
                        Fy = magnitude * np.sin(angle * np.pi / 180) / h

                        F[j] += Fy # converting deg to rad
                
                for (pos_start, pos_end), magnitude in self.loads:
                        j_start = self._get_node_by_pos(pos_start, h)
                        j_end = self._get_node_by_pos(pos_end, h)

                        for j in range(j_start, j_end + 1):
                                F[j] += magnitude
                
                return F

        def _build_stiffness_matrix(self, N):

                K = np.zeros((N, N))
                
                # Standard 4th-order derivative stencil
                for i in range(2, N-2):
                        K[i, i-2:i+3] = [1, -4, 6, -4, 1]

                # Special stencils for free end nodes
                # they should be replaced by supports if so
                K[0, 0:3] = [2, -4, 2]
                K[1, 0:4] = [-2, 5, -4, 1]

                K[N-2, N-4:N] = [1, -4, 5, -2]
                K[N-1, N-3:N] = [2, -4, 2]

                return K
        
        def _apply_boundary_conditions(self, K, F, N, h):
                
                for pos, support_type in self.supports:
                        j = self._get_node_by_pos(pos, h)

                        # x is handled by another method
                        match support_type.replace("x", ""):
                                case "y": # 1° or 2° degree support
                                        K[j, :] = 0
                                        K[j, j] = 1
                                        F[j] = 0
                                case "z":
                                        # Stencil is defined by:
                                        #       Angle = 0 -> w_-1 = w_1
                                        #       Shear = 0 -> w_-2 = w_2
                                        K[j, :] = 0
                                        if j <= N // 2:
                                                K[j, j:j+3] = [6, -8, 2]
                                        else:
                                                K[j, j-2:j+1] = [2, -8, 6]

                                case "yz":
                                        # Stencil is defined by:
                                        #       Deflection = 0 -> w_0 = 0
                                        #       Angle = 0 -> w_-1 = w_1
                                        # ensure deflection is null at 0
                                        K[j, :] = 0
                                        K[j,j] = 1
                                        F[j] = 0
                                        # extreme boundaries need to erase ghost nodes
                                        # So i'm defining it like this to guarantee
                                        # no ghost node is created, by defining in relation
                                        # to the node right next to it 
                                        if j <= N // 2:
                                                # boundaries corrected for node positions
                                                K[j+1, :] = 0
                                                K[j+1, j+1:j+5] = [0, 7, -4, 1]
                                        else:
                                                
                                                # boundaries corrected for node positions
                                                K[j-1, :] = 0
                                                K[j-1, j-3:j+1] = [1, -4, 7, 0]
                
                return K, F

# This class handles drawing on the canvas
class Pencil():
        # Initialize the pencil with drawing properties
        def __init__(self, view, width = 2, sup_fill = "blue", eff_fill = "red", line_color = "black"):
                self.view = view
                self.line_width = width
                self.line_color = line_color
                self.sup_fill = sup_fill # Fill color for supports
                self.eff_fill = eff_fill # Fill color for efforts (forces)
                self.max_force = 0

                # Mapper to call the correct drawing function based on support type
                self.mapper = {
                        "xy":self.draw_xy,
                        "y":self.draw_y,
                        "xyz":self.draw_xyz,
                        "xz":self.draw_xz,
                }
        
        # Draws a line at a specific angle and length
        def draw_angled_line(self, length, start_pos,  canvas: tk.Canvas, angle_degrees = 0):
                # Calculate the end point of the line
                p1 = (int(start_pos[0] + length * np.cos(angle_degrees * np.pi / 180)), int(start_pos[1] - length * np.sin(angle_degrees * np.pi / 180)))
                # Create the line on the canvas
                canvas.create_line(start_pos, p1, width = self.line_width, fill=self.line_color)
        
        # Helper function to create a circle given a center and radius
        def create_circle(self, canvas, center, radius, **options):
                cx, cy = center
                # Calculate bounding box coordinates
                x0 = cx - radius
                y0 = cy - radius
                x1 = cx + radius
                y1 = cy + radius

                # Create the oval (circle) on the canvas
                return canvas.create_oval(x0, y0, x1, y1, **options)


        # Draws a series of small circles along a line (used for some support types)
        def _draw_circles_along_line(self, start_pos:tuple, end_pos:tuple, num_circles:int, canvas: tk.Canvas, **kwargs):
                start_x, start_y = start_pos
                length_x = end_pos[0] - start_pos[0]
                length_y = end_pos[1] - start_pos[1]
                
                # Calculate the total length of the line
                length = int(np.linalg.norm([length_x, length_y]))
                # Calculate the radius of each circle
                cir_radius = length / (2 * num_circles)

                
                # Loop to draw each circle
                for i in range(1, num_circles+1):
                        # Calculate the center of the current circle
                        xi = start_x + length_x * cir_radius * (2*i - 1) / length
                        yi = start_y + length_y * cir_radius * (2*i - 1) / length

                        # Draw the circle
                        self.create_circle(canvas=canvas, center=(xi, yi), radius=cir_radius, **kwargs)

        # Draws a fixed support (restricts x and y movement)
        def draw_xy(self, beam_position:float, height:float, canvas:tk.Canvas):
                beam_length = self.view.controller.model.length
                                        
                # Map beam position to canvas coordinates
                x0 = int(self.view.canvas_padx + (canvas.winfo_width() - 2*self.view.canvas_padx)*(beam_position / beam_length))
                y0 = self.view.beam_y

                p0 = (x0, y0)
                
                # Calculate the dimensions of the triangular support symbol
                side = 2 * height / float(np.tan(np.pi / 3))

                # Define the points of the triangle
                p1 = (x0 + side / 2, y0 + height)
                p2 = (x0 - side / 2, y0 + height)

                # Draw the triangle
                canvas.create_polygon(p0, p1, p2, p0, width = self.line_width, fill=self.sup_fill)
                canvas.create_line(p0, p1, p2, p0, width = self.line_width, fill=self.line_color)

                # Draw little hatching lines to indicate a fixed connection
                for i in np.linspace(p2[0], p1[0], 5):
                        
                        self.draw_angled_line(15, (i, y0 + height), angle_degrees = 225, canvas= canvas)
        
        # Draws a roller support (restricts y movement)
        def draw_y(self, beam_position:float, height:float, canvas:tk.Canvas):
                beam_length = self.view.controller.model.length
                                        
                # Map beam position to canvas coordinates
                x0 = self.view.canvas_padx + (canvas.winfo_width() - 2*self.view.canvas_padx)*(beam_position / beam_length)
                y0 = self.view.beam_y

                p0 = (x0, y0)
                
                # Calculate dimensions for the triangle
                side = 2 * height / float(np.tan(np.pi / 3))

                p1 = (x0 + side / 2, y0 + height)
                p2 = (x0 - side / 2, y0 + height)

                # Draw the triangle
                canvas.create_polygon(p0, p1, p2, p0, width = self.line_width, fill=self.sup_fill)
                canvas.create_line(p0, p1, p2, p0, width = self.line_width, fill=self.line_color)

                # Draw little circles to indicate a roller
                
                self._draw_circles_along_line(
                        start_pos=(p2[0], y0 + 1.2 * height),
                        end_pos=(p1[0], y0 + 1.2 * height),
                        num_circles=4,
                        width=self.line_width//1.5,
                        fill=self.sup_fill,
                        canvas=canvas
                )
        
        # Draws a clamped or fixed-end support (restricts x, y, and z rotation)
        def draw_xyz(self, beam_position:float, height:float, canvas:tk.Canvas):
                beam_length = self.view.controller.model.length

                # Map beam position to canvas coordinates
                x0 = self.view.canvas_padx + (canvas.winfo_width() - 2*self.view.canvas_padx)*(beam_position / beam_length)
                y0 = self.view.beam_y
                p0 = (x0, y0)

                ratio = 6
                episilon = .1
                
                # Determine drawing logic based on position (start, end, or middle of beam)
                if abs(beam_position) < episilon: # Draw on the left
                        polygon_points = [p0, (x0, y0 - height), (x0 - height/ratio, y0 - height), (x0 - height/ratio, y0 + height), (x0, y0 + height), p0]
                        draw_lines = "left"
                elif abs(beam_position - beam_length) < episilon: # Draw on the right
                        polygon_points = [p0, (x0, y0 - height), (x0 + height/ratio, y0 - height), (x0 + height/ratio, y0 + height), (x0, y0 + height), p0]
                        draw_lines = "right"
                else: # Draw in the middle
                        polygon_points = [(x0 - height/(ratio), y0 - height), (x0 - height/(ratio), y0 + height), (x0 + height/(ratio), y0 + height), (x0 + height/(ratio), y0 - height)]
                        draw_lines = False 
                # Draw the main rectangle of the support
                canvas.create_polygon(*polygon_points, width = self.line_width, fill=self.sup_fill)
                canvas.create_line(*polygon_points, width = self.line_width, fill=self.line_color)

                # Draw hatching lines
                match draw_lines:
                        case "left":
                                for i in np.linspace(y0 - height, y0 + height, 7)[1:-1]: 
                                        self.draw_angled_line(15, (x0-height/ratio, i), angle_degrees = 135, canvas = canvas)
                        case "right":
                                for i in np.linspace(y0 - height, y0 + height, 7)[1:-1]: 
                                        self.draw_angled_line(15, (x0+height/ratio, i), angle_degrees = 45, canvas = canvas)
                
        # Draws a support that restricts x and z movement
        def draw_xz(self, beam_position:float, height:float, canvas:tk.Canvas):
                beam_length = self.view.controller.model.length

                # Map beam position to canvas coordinates
                x0 = self.view.canvas_padx + (canvas.winfo_width() - 2*self.view.canvas_padx)*(beam_position / beam_length)
                y0 = self.view.beam_y
                p0 = (x0, y0)

                ratio = 6
                episilon = .1
                
                # Determine drawing logic based on position
                if abs(beam_position) < episilon: # Draw on the left
                        polygon_points = [p0, (x0, y0 - height), (x0 - height/ratio, y0 - height), (x0 - height/ratio, y0 + height), (x0, y0 + height), p0]
                
                        canvas.create_polygon(*polygon_points, width = self.line_width, fill=self.sup_fill)
                        canvas.create_line(*polygon_points, width = self.line_width, fill=self.line_color)

                        # Draw circles to indicate roller-like behavior in one plane
                        self._draw_circles_along_line(
                                start_pos=(x0 - 2 * height/ratio, y0 + height),
                                end_pos=(x0 - 2 * height/ratio, y0 - height),
                                num_circles=6,
                                width=self.line_width//1.5,
                                fill=self.sup_fill,
                                canvas=canvas
                        )
                elif abs(beam_position - beam_length) < episilon: # Draw on the right
                        polygon_points = [p0, (x0, y0 - height), (x0 + height/ratio, y0 - height), (x0 + height/ratio, y0 + height), (x0, y0 + height), p0]
                        
                        canvas.create_polygon(*polygon_points, width = self.line_width, fill=self.sup_fill)
                        canvas.create_line(*polygon_points, width = self.line_width, fill=self.line_color)

                        self._draw_circles_along_line(
                                start_pos=(x0 + 2 * height/ratio, y0 + height),
                                end_pos=(x0 + 2 * height/ratio, y0 - height),
                                num_circles=6,
                                width=self.line_width//1.5,
                                fill="white",
                                canvas=canvas
                        )

                else: # Draw in the middle
                        
                        polygon1_points = [(x0  - height/(ratio), y0 - height), (x0  - height/(ratio), y0 + height), (x0  - 1.5 * height/(ratio), y0 + height), (x0  - 1.5 * height/(ratio), y0 - height)]
                        polygon2_points = [(x0  + height/(ratio), y0 - height), (x0  + height/(ratio), y0 + height), (x0  + 1.5 * height/(ratio), y0 + height), (x0  + 1.5 * height/(ratio), y0 - height)]
                        
                        canvas.create_polygon(*polygon1_points, width = self.line_width, fill=self.sup_fill)
                        canvas.create_polygon(*polygon2_points, width = self.line_width, fill=self.sup_fill)

                        self._draw_circles_along_line(
                                start_pos=(x0, y0 + height),
                                end_pos=(x0, y0 - height),
                                num_circles=6,
                                width=self.line_width//1.5,
                                fill=self.sup_fill,
                                canvas=canvas
                        )
                        
        
        # Draws a point load (arrow) on the beam
        def draw_point_load(self, beam_position:float, height:float, magnitude:float, canvas:tk.Canvas, angle:float = 90, literal_coords = False, write = True):
                
                
                # Get the maximum force to scale the arrow size
                self.max_force = self.view.controller.model.get_max_force()

                
                # Calculate the height of the arrow based on its magnitude relative to the max force
                draw_height = height / 3 * (2 * abs(magnitude) / self.max_force + 1)


                beam_length = self.view.controller.model.length
                # Map beam position to canvas x-coordinate
                x0 = self.view.canvas_padx + (canvas.winfo_width() - 2*self.view.canvas_padx)*(beam_position / beam_length)

                # If literal_coords is true, use the given position directly
                if literal_coords:
                        x0 = beam_position

                y0 = self.view.beam_y
                end_pos = (x0, y0)

                

                # Calculate the start position of the arrow based on angle and height
                start_x = end_pos[0] + draw_height * np.cos(angle * np.pi / 180)
                start_y = end_pos[1] - draw_height * np.sin(angle * np.pi / 180)
                start_pos = (start_x, start_y)

                # Draw the force vector as a line with an arrowhead at the end
                canvas.create_line(
                        start_pos, 
                        end_pos, 
                        width=self.line_width, 
                        fill=self.eff_fill, 
                        arrow=tk.LAST if magnitude < 0 else tk.FIRST,  # Add an arrowhead to the end of the line
                        arrowshape=(height/6, height/5, height/10) # Customize arrowhead shape (length, fullwidth, halfwidth at base)
                )
                # If specified, write the magnitude of the force
                if write:
                        is_up = end_pos[1] < start_y

                        k = 1 if is_up else -1

                        # Write force magnitude text on the canvas
                        canvas.create_text(
                                (start_x, start_y + k * draw_height / 5),
                                text = f"{abs(magnitude):.2f}",
                                fill = self.eff_fill, 
                                font = f"TkDefaultFont {int(height / 3)}"
                )
        
        # Draws a distributed load on the beam
        def draw_load(self, pos_limits:tuple, height:float, magnitude:float, canvas:tk.Canvas):

                beam_length = self.view.controller.model.length

                # Get max force to scale the drawing
                self.max_force = self.view.controller.model.get_max_force()
                
                # Calculate drawing height based on magnitude
                draw_height = height / 3 * (2 * abs(magnitude) / self.max_force + 1)

                x0, x1 = pos_limits
                # Map beam positions to canvas coordinates
                x0 = self.view.canvas_padx + (canvas.winfo_width() - 2*self.view.canvas_padx)*(x0 / beam_length)
                x1 = self.view.canvas_padx + (canvas.winfo_width() - 2*self.view.canvas_padx)*(x1 / beam_length)

                # Calculate the number of small arrows to draw for the distributed load
                N = int(abs(x0 - x1) / (height / 3))

                # Draw a series of small point loads to represent the distributed load
                for i in np.linspace(x0, x1, N):
                        
                        self.draw_point_load(
                                beam_position=i,
                                height=height,
                                canvas=canvas,
                                magnitude=magnitude,
                                literal_coords=True, # Use canvas coordinates directly
                                write=False # Don't write magnitude for each small arrow
                        )
                
                # Draw a line connecting the tops of the arrows
                canvas.create_line((x0, self.view.beam_y - draw_height), (x1, self.view.beam_y - draw_height), width=self.line_width, fill=self.eff_fill)

                # Write the magnitude of the distributed load
                canvas.create_text(
                        (x0 + abs(x0 - x1) / 2, self.view.beam_y - draw_height * (1.5)),
                        text = f"{abs(magnitude):.2f}",
                        fill = self.eff_fill, 
                        font = f"TkDefaultFont {int(height / 3)}"
                )

# main application window (GUI)
class View(tk.Tk):
        # Initialize the view
        def __init__(self, controller):
                super().__init__("View")
                self.controller = controller
                self.font = ("Helvetica", 10, "bold")
                # Set window size
                self.geometry("1000x700")
                # Create a pencil for drawing
                self.pencil = Pencil(self)
                self.pack_propagate = False
                # if true, adds gui elements for viewing graphs
                self.view_solution:bool = False
                self.solution_mode = "deflection"
                
                # Define padding on the sides of the canvas
                self.canvas_padx = 50
                
                # Set terminal variables
                self.terminal_messages = []
                self.terminal_color = "#eeeeee"

                self.start_gui()
                self.setup_styler()

        # Configures the style for themed Tkinter widgets
        def setup_styler(self):
                self.styler = ttk.Style()
                self.styler.configure("TFrame", background="#f0f0f0")
                self.styler.configure("TLabel", padding=5, background="#f0f0f0")
                self.styler.configure("TButton", padding=5) 

        # Helper function to create a separator with a title
        def create_separator(self, frame, text, side = "top", pady=12):
                ttk.Separator(frame).pack(fill="x", pady=3, side="top")
                if text is not None:
                        ttk.Label(
                                frame,
                                text=text,
                                font=self.font
                        ).pack(side=side)  
        
        # Method to create and arrange all the main GUI components
        def start_gui(self):
                # Main layout containers
                self.main_frame = ttk.Frame(self)
                self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

                # define frame for left widgets
                self.left_frame = ttk.Frame(self.main_frame)
                self.left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

                # Configure grid rows for proportional sizing
                self.left_frame.rowconfigure(0, weight=1)  
                self.left_frame.rowconfigure(1, weight=1)  
                self.left_frame.columnconfigure(0, weight=1)

                # Canvas Frame 
                self.canvas_frame = ttk.Frame(self.left_frame)
                self.canvas_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)

                self.maincanvas = tk.Canvas(self.canvas_frame, bg="white", bd=2, relief="groove")
                self.maincanvas.pack(fill="both", expand=True, padx=5, pady=5)

                # Terminal Frame
                self.terminal_frame = ttk.Frame(self.left_frame)
                self.terminal_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

                # Control Panel for user inputs
                self.control_frame = tk.Frame(self.main_frame, width = 250)
                self.control_frame.pack(side="right", fill="y", padx=5, pady=5)


                
                # Initial drawing of the beam and setup of control panel sections
                self.terminal_gui()
                self.draw_beam()
                self.length_gui()
                self.supports_gui()
                self.loads_gui()
                self.solve_gui()

        def terminal_gui(self):
                self.terminal_canvas = tk.Canvas(self.terminal_frame, bg=self.terminal_color, bd=2, relief="groove")
                self.terminal_canvas.pack(fill="both", expand=True, padx=5)
                self.terminal_canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)
                self.terminal_canvas.bind("<Button-1>", self._on_terminal_click)

        # Creates the GUI elements for setting the beam length
        def length_gui(self):
                # length section
                self.create_separator(self.control_frame, text="Beam Properties", pady=3)

                # frames for sideways packing
                len_frame = ttk.Frame(self.control_frame)
                E_frame = ttk.Frame(self.control_frame)
                I_frame = ttk.Frame(self.control_frame)

                
                len_frame.pack(pady=1)
                E_frame.pack(pady=1)
                I_frame.pack(pady=1)

                self.len_var = tk.StringVar(value="10.0")
                self.E_var = tk.StringVar(value='2e11')
                self.I_var = tk.StringVar(value=self.controller.model.materials["I"])

                # Length input
                ttk.Label(
                        len_frame,
                        text="Length (m)",
                        font=self.font,
                        width=10
                ).pack(side="left")

                ttk.Entry(
                        len_frame,
                        textvariable=self.len_var
                ).pack(fill="x", side="left")

                # E input
                ttk.Label(
                        E_frame,
                        text="Set E (Pa)",
                        font=self.font,
                        width=10
                ).pack(side="left")
                
                ttk.Entry(
                        E_frame,
                        textvariable=self.E_var
                ).pack(fill="x", side="left")

                # I input
                ttk.Label(
                        I_frame,
                        text="Set I (m^4)",
                        font=self.font,
                        width=10
                ).pack(side="left")
                
                ttk.Entry(
                        I_frame,
                        textvariable=self.I_var
                ).pack(fill="x", side="left")
                
                # Button for update beam
                ttk.Button(
                        self.control_frame,
                        text="Update Beam",
                        command=lambda: self.controller.update_beam_properties(
                                self.len_var.get(),
                                self.E_var.get(),
                                self.I_var.get()
                        )
                ).pack(pady=2)

        # Creates the GUI elements for adding/removing supports
        def supports_gui(self):
                # Support controls section
                self.create_separator(self.control_frame, "Supports")
                
                # Frame for the position input
                line1 = ttk.Frame(self.control_frame)
                line1.pack(pady=5)
                ttk.Label(line1, text="Position", font=self.font, width=10).pack(side="left", padx=2)
                self.support_pos_strgvar = tk.StringVar(value="")
                support_pos_entry = ttk.Entry(line1, textvariable=self.support_pos_strgvar, width = 12)
                support_pos_entry.pack(side="left")

                # Frame for the support type checkboxes
                chkbtn_frame = ttk.Frame(self.control_frame)
                chkbtn_frame.pack(padx=5, pady=5)

                # Variables for the checkboxes
                self.Var1 = tk.IntVar(value=0)
                self.Var2 = tk.IntVar(value=0)
                self.Var3 = tk.IntVar(value=0)


                # Checkboxes for x, y, z constraints
                ChkBtn1 = ttk.Checkbutton(
                        chkbtn_frame,
                        variable = self.Var1,
                        text = "x",
                )
                ChkBtn2 = ttk.Checkbutton(
                        chkbtn_frame,
                        variable = self.Var2,
                        text = "y",
                )
                ChkBtn3 = ttk.Checkbutton(
                        chkbtn_frame,
                        variable = self.Var3,
                        text = "z",
                )


                ChkBtn1.pack(padx=5, pady=2, side="left")
                ChkBtn2.pack(padx=5, pady=2, side="left")
                ChkBtn3.pack(padx=5, pady=2, side="left")

                # Frame for the add/remove support buttons
                sup_button_frame = ttk.Frame(self.control_frame)
                sup_button_frame.pack(pady=5)

                # Button to add a support
                ttk.Button(
                        sup_button_frame,
                        text="Add Support",
                        command=lambda :self.controller.add_support(
                                position=self.support_pos_strgvar.get(),
                                # Combine checkbox values to form the support type string (e.g., "xy")
                                support_type=self.Var1.get()*"x" + self.Var2.get()*"y" + self.Var3.get()*"z"
                        )
                ).pack(side="left", padx = 2)
                # Button to remove the last support
                ttk.Button(
                        sup_button_frame,
                        text="Remove Support",
                        command=self.controller.remove_last_support      
                ).pack(side="left", padx = 2)

        # Creates the GUI elements for adding/removing forces and loads
        def loads_gui(self):
                # Title for the loads section
                title_load_frame = ttk.Frame(self.control_frame, width=250)
                title_load_frame.pack()
                self.create_separator(title_load_frame, "Forces & Loads")


                # Frames for input fields
                line1 = tk.Frame(self.control_frame)
                line2 = tk.Frame(self.control_frame)
                line3 = tk.Frame(self.control_frame)
                lines_pady = 1

                # Position input
                line1.pack(pady=lines_pady)
                ttk.Label(line1, text="Position", font=self.font, width=10).pack(side="left", padx=2)
                self.load_pos_strgvar = tk.StringVar(value="")
                ttk.Entry(line1, textvariable=self.load_pos_strgvar, width = 12).pack()
                
                # Magnitude input
                line2.pack(pady=lines_pady)
                ttk.Label(line2, text="Magnitude", font=self.font, width=10).pack(side="left", padx=2)
                self.mag_strgvar = tk.StringVar(value="")
                ttk.Entry(line2, textvariable=self.mag_strgvar, width = 12).pack()

                # Angle input
                line3.pack(pady=lines_pady)
                ttk.Label(line3, text="Angle", font=self.font, width=10).pack(side="left", padx=2)
                self.angle_strgvar = tk.StringVar(value="90")
                ttk.Entry(line3, textvariable=self.angle_strgvar, width = 12).pack()

                # Frame for the add/remove force buttons
                load_button_frame = ttk.Frame(self.control_frame)
                load_button_frame.pack(pady = 5)

                # Button to add a force or load
                ttk.Button(
                        load_button_frame,
                        text="Add Force",
                        command=lambda: self.controller.add_effort(
                                magnitude=self.mag_strgvar.get(),
                                position=self.load_pos_strgvar.get(),
                                angle = self.angle_strgvar.get()
                        )
                ).pack(side="left", padx=2)

                # Button to remove the last force or load
                ttk.Button(
                        load_button_frame,
                        text="Remove Force",
                        command=self.controller.remove_last_effort
                ).pack(side="left", padx=2)
        
        # Creates the GUI element for solving the beam problem
        def solve_gui(self):
                self.create_separator(frame = self.control_frame, text=None, pady=4)

                # entry for num of nodes
                line1 = tk.Frame(self.control_frame)
                line1.pack(pady=3)
                ttk.Label(line1, text="N° Nodes", font=self.font, width=10).pack(side="left", padx=2)
                self.nodes_strgvar = tk.StringVar(value="30")
                ttk.Entry(line1, textvariable=self.nodes_strgvar, width = 12).pack(side="left")

                self.after_solve_frame = ttk.Frame(self.control_frame)
                self.after_solve_frame.pack(pady=3)

                # See Shear 
                ttk.Button(
                        self.after_solve_frame,
                        text="Shear",
                        command=lambda: self.controller.view_graph_button_clicked("shear")
                ).grid(row=0, column=0, padx=2, pady=2)

                # See Moment 
                ttk.Button(
                        self.after_solve_frame,
                        text="Moment",
                        command=lambda: self.controller.view_graph_button_clicked("moment")
                ).grid(row=0, column=1, padx=2, pady=2)

                # See Slopes 
                ttk.Button(
                        self.after_solve_frame,
                        text="Slopes",
                        command=lambda: self.controller.view_graph_button_clicked("slope")
                ).grid(row=1, column=0, padx=2, pady=2)


                # See Deflection
                ttk.Button(
                        self.after_solve_frame,
                        text="Deflection",
                        command=lambda: self.controller.view_graph_button_clicked("deflection")
                ).grid(row=1, column=1, padx=2, pady=2)


        def _on_mouse_wheel(self, event):
                if not self.view_solution: # only valid for terminal
                        self.terminal_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def add_terminal_message(self, message):
                self.terminal_messages.append(message)
        
        def _get_fdm_values(self):
                
                match self.solution_mode:
                        case "deflection":
                                return self.controller.model.deflections
                        case "moment":
                                return np.array([-1*i for i in self.controller.model.moments]) 
                                # multiply by -1 for drawing 
                        case "shear":                                
                                return self.controller.model.shears
                        
                        case "slope":
                                return self.controller.model.slopes
                        
        def _on_terminal_click(self, event):
                if self.view_solution:
                        self.terminal_canvas.delete("coord_text")
                        # Get mouse click coordinates
                        click_x, click_y = event.x, event.y

                        # Find closest x in the plotted data
                        model = self.controller.model
                        y_values = self._get_fdm_values()
                        x_values = np.linspace(0, model.length, len(y_values))

                        term_w = self.terminal_canvas.winfo_width()
                        x_canvas = [
                                self.canvas_padx + x / model.length * (term_w - 2 * self.canvas_padx)
                                for x in x_values
                        ]

                        # Find the nearest x index
                        distances = [abs(click_x - px) for px in x_canvas]
                        closest_index = distances.index(min(distances))

                        # Retrieve corresponding physical values
                        beam_x = x_values[closest_index]
                        beam_y = y_values[closest_index]

                        # Display value on canvas
                        self.terminal_canvas.create_text(
                                click_x, click_y - 10,  # slight offset above cursor
                                text=f"x = {beam_x:.2f}\ny = {beam_y:.5e}",
                                fill="blue", font=("Arial", 10),
                                tags="coord_text",
                                anchor="w" if beam_x != model.length else "e"
                        )

        def draw_terminal_messages(self):
                self.terminal_canvas.yview_moveto(0.0)
                self.terminal_canvas.config(bg=self.terminal_color)
                self.view_solution = False
                

                # clear canvas
                self.terminal_canvas.delete("all")

                # get canvas dimenions
                w = self.terminal_canvas.winfo_width()
                h = self.terminal_canvas.winfo_height()

                terminal_font = ("Consolas", 14, "italic")

                # get font_size
                temp_text = self.terminal_canvas.create_text((0,0), text="D", font=terminal_font)
                _, y1, _, y2 =  self.terminal_canvas.bbox(temp_text)
                font_size = y2 - y1
                self.terminal_canvas.delete(temp_text)

                # define start y coord to write
                num_messages = len(self.terminal_messages)
                if num_messages * font_size > h:
                        write_y = - (num_messages - h / font_size) * font_size + h / 50
                else:
                        write_y = font_size                                          
                write_x = w / 100


                for message in self.terminal_messages:
                        self.terminal_canvas.create_text(
                                (write_x, write_y),
                                fill= "black",
                                text= f"> {message}",
                                font= terminal_font,
                                anchor="w"
                        )

                        write_y += font_size

                return
        
        def draw_solved_beam(self):
                mode = self.solution_mode
                self.view_solution = True
                # remove all elements in terminal canvas
                self.terminal_canvas.delete("all")

                # get canvas width and height
                term_w, term_h = self.terminal_canvas.winfo_width(), self.terminal_canvas.winfo_height()

                # define model
                model = self.controller.model

                self.terminal_canvas.config(bg = "white")
                
                y_values = self._get_fdm_values()
                
                max_abs_point = abs(max(y_values.min(), y_values.max(), key=abs))
                std_height = term_h / 5

                sol_beam_y = term_h / 2

                # draw line that represents beam
                self.terminal_canvas.create_line(
                        (self.canvas_padx, sol_beam_y),
                        (term_w - self.canvas_padx, sol_beam_y),
                        width = 3, fill="black"
                )

                # get x values
                x_values = np.linspace(0, model.length, len(y_values))

                # define points in canvas coords
                points = [(
                                self.canvas_padx + x / model.length * (term_w - 2 * self.canvas_padx), # x
                                sol_beam_y - (y / max_abs_point) * std_height # y
                        )
                        for x, y
                        in zip(x_values, y_values)
                ]
                
                # draw graph
                self.terminal_canvas.create_line(
                        *points,
                        width = 2, fill = "red"
                )
                          
        # Redraws the entire canvas
        def draw_beam(self, canvas: tk.Canvas = None):
                if canvas is None:
                        canvas = self.maincanvas
                # Clear the canvas
                canvas.delete("all")
                # Get current canvas dimensions
                canvas_w, canvas_h = canvas.winfo_width(), canvas.winfo_height()
                

                # Define the y-position of the beam on the canvas
                self.beam_y = canvas_h / 2

                std_height = canvas_h / 8

                # Draw the main beam line
                canvas.create_line(
                (self.canvas_padx, self.beam_y),
                (canvas_w - self.canvas_padx, self.beam_y),
                width = 3, fill="black"
                )

                # Draw all saved supports
                for support_pos, support_type in self.controller.model.supports:
                        # Call the appropriate drawing function from the pencil's mapper
                        self.pencil.mapper[support_type](support_pos, std_height, canvas=canvas)
                        
                # Draw all saved point forces
                for magnitude, force_pos, angle in self.controller.model.point_loads:
                        self.pencil.draw_point_load(beam_position=force_pos, height=std_height, canvas=canvas, angle=angle, magnitude=magnitude)

                # Draw all saved distributed loads
                for pos_limits, magnitude in self.controller.model.loads:
                        self.pencil.draw_load(pos_limits=pos_limits, height=std_height, canvas=canvas, magnitude=magnitude)
        
        def update_display(self):
                self.draw_beam()
                self.draw_terminal_messages()

# This class acts as the controller (in the MVC pattern), handling user input and updating the model and view
class Controller():
        # Initialize the controller
        def __init__(self):
                # Create instances of the model and view
                self.model = Model()
                self.view = View(self)
        
                # When the canvas is resized, call the update_display method
                self.view.maincanvas.bind("<Configure>", self.update_display)
        
        # Starts the main event loop of the application
        def run(self):
                self.view.mainloop()
        
                # Handles the "Set Length" button click
        def update_beam_properties(self, new_length, new_E, new_I):
                # Validate the inputs
                test1, new_length = self.test_float(new_length, "Length")
                test2, new_E = self.test_float(new_E, "E")
                test3, new_I = self.test_float(new_I, "I")
            
                if not (test1 and test2 and test3):
                        return False
            
                elif new_length <= 0:
                        self.add_terminal_message(f"Error: Length must be greater than '0'!")
                        return False
                
                elif new_E <= 0 or new_I <= 0:
                        self.add_terminal_message(f"Error: E and I must be greater than '0'!")
                        return False

                if not new_length == self.model.length:
                        self.add_terminal_message(f"New Length set to:{new_length}")

                if not new_E == self.model.materials["E"]:
                        self.add_terminal_message(f"New E set to:{new_E}")

                if not new_I == self.model.materials["I"]:
                        self.add_terminal_message(f"New I set to:{new_I}")

                # If the model successfully sets the length, update the view
                if self.model.set_properties(new_length, new_E, new_I):
                        self.update_display()
                        return True
                
                return False

        # Sets the total number of nodes for the simulation
        def set_total_node_num(self, new_node_num):
                test, new_node_num = self.test_float(new_node_num, "N° Nodes", test_int = True)
    
                if not test:
                        return False

                if new_node_num == self.model.total_node_num:
                        return True

                if new_node_num < 10:
                        self.add_terminal_message("N° Nodes must be higher than 9.")
                        return False
            
                if self.model.set_total_node_num(new_node_num):
                        self.add_terminal_message(f"N° Nodes set to {new_node_num}")
                        return True
                return False

        # Handles the "Add Support" button click
        def add_support(self, position, support_type):
                # Validate the position input is floatable
                positions = []
                for position in position.split(";"):
                        test, position = self.test_float(position, "Position")
                        if not test:
                                return False
                        
                        positions.append(position)

                for position in positions:
                        # check if position is within the beam's length
                        if not 0 <= position <= self.model.length:
                                self.add_terminal_message(f"Error: Support position must be inside beam!")
                                return False

                        # check if new support is too close to an existing one
                        for already_saved_position, _ in self.model.supports:
                                if abs(position - already_saved_position) <= self.model.length / self.model.total_node_num:
                                        self.add_terminal_message(f"Error: Cannot add support too close to another one!")
                                        return False
                
                        # Check if the support type is valid/implemented
                        if support_type not in self.view.pencil.mapper:
                                self.add_terminal_message(f"Error: Support kind '{support_type}' not yet implemented!")
                                return False
                
                        # If the model successfully adds the support, update the view
                        if self.model.add_support(position, support_type):
                                self.add_terminal_message(f"New support {support_type} added to:{position}")
                                continue
            
                return False

        # Handles the "Remove Support" button click
        def remove_last_support(self):
                # If the model successfully removes a support, update the view
                if self.model.remove_last_support():
                        self.add_terminal_message("Support Removed.")
                        return True
                return False

        # Handles the "Add Force" button click
        def add_effort(self, magnitude:float, position, angle:float = 90):
                # test magnitude and angle
                test1, magnitude = self.test_float(magnitude, "Magnitude")
                test2, angle = self.test_float(angle, "Angle")
            
                if not (test1 and test2):
                        return False
            
                if magnitude == 0:
                        self.add_terminal_message("Error: Magnitude cannot be '0'")
                        return False

                # Check if the position input is for a distributed load (e.g., "2;5")
                if ";" in position:
                        pos0, pos1 = position.split(";")[:2]

                        test0, pos0 = self.test_float(pos0, "Position 1")
                        test1, pos1 = self.test_float(pos1, "Position 2")
                    
                        if not (test0 and test1):
                                return False

                        if pos1 < pos0:
                                pos0, pos1 = pos1, pos0
                    
                        if (not 0 <= pos0 <= self.model.length) or (not 0 <= pos1 <= self.model.length):
                                self.add_terminal_message("Error: Position must be inside beam!")
                                return False
            
                # Otherwise, it's a point load
                else:
                        test, pos0 = self.test_float(position, "Position")
                        pos1 = None
                    
                        if not test:
                                return False

                        if not 0 <= pos0 <= self.model.length:
                                self.add_terminal_message("Error: Position must be inside beam!")
                                return False
            

                # If pos1 is None, it's a point load
                if pos1 is None:
                        # If the model adds the point load, update the display
                        if self.model.add_point_load(magnitude=magnitude, position=pos0, angle=angle):
                                if angle == 90:
                                        self.add_terminal_message(f"New force {magnitude} added to: {position}")
                                        return True
                                self.add_terminal_message(f"New force ({magnitude}>{angle}°) added to: {position}")
                                return True
                        return False

                # If pos1 is valid, it's a distributed load
                if self.model.add_loads(pos_limits=(pos0, pos1), magnitude=magnitude):
                        self.add_terminal_message(f"New load {magnitude} added from {pos0} to {pos1}")
                        return True
                return False

        # Handles the "Remove Force" button click
        def remove_last_effort(self):
                # If the model successfully removes an effort, update the view
                if self.model.remove_last_effort():
                        self.view.add_terminal_message("Effort Removed.")
                        self.update_display()
                        return True
                return False

        # Handles the "Solve" button click
        def solve_button_clicked(self):
                
                if not self.model.supports:
                        self.add_terminal_message(f"Error: You cannot solve a beam without supports")
                        return False

                if len(self.model.loads) + len(self.model.point_loads) == 0:
                        self.add_terminal_message(f"Error: You cannot solve a beam without loads")
                        return False

                if not self.set_total_node_num(self.view.nodes_strgvar.get()):

                        return False
                self.add_terminal_message(f"SOLVING FOR {self.model.total_node_num} NODES...")
                

                self.model.solve_FDM()

                self.update_display()
                self.view.draw_solved_beam()

                return True
        
        def view_graph_button_clicked(self, mode:str):
                self.view.solution_mode = mode

                self.solve_button_clicked()

        # This method is called to refresh the drawing on the canvas
        def update_display(self, event=None):
                self.view.update_display()
    
        # Adds a message to the view's terminal display
        def add_terminal_message(self, message:str):
                self.view.add_terminal_message(message)
                self.update_display()

        # Tests if a variable can be converted to a float or integer
        def test_float(self, var, var_name="input", test_int = False): # worked, var
                try:
                        if not test_int:
                                var = float(var)
                                return True, var
                        var = int(var)
                        return True, var
                except (ValueError, TypeError):
                        self.add_terminal_message(f"Error: Invalid value for {var_name}: '{var}'")
                        return False, None




# This block runs if the script is executed directly
if __name__ == "__main__":
        # Create an instance of the controller
        app = Controller()
        # Start the application
        app.run()
