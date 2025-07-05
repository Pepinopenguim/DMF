# Import necessary libraries
import tkinter as tk
import numpy as np
from tkinter import ttk
from bird_coords import bird_coords

# This class holds the data for the beam simulation
class Model():
        # Initialize the model with default values
        def __init__(self):
                # Length of the beam
                self.length = 10
                # Number of nodes for calculation
                self.total_node_num = 30
                # List to store node data (position, support)
                self.nodes = [] 

                # List to store point loads (magnitude, position, angle)
                self.point_loads = []
                # List to store distributed loads (position tuple, magnitude)
                self.loads = []
                # List to keep track of the order efforts were added
                self.order_of_efforts = []

                # List to store supports (position, support_type)
                self.supports = []
                # Dictionary for material properties
                self.materials = {
                        "E":2e11, # Young's Modulus in Pascals
                        "I":10e-6, # Moment of inertia in m^4
                }

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
        def set_length(self, new_length:float):
                if new_length == self.length:
                        return False
                self.length = new_length
                # Check if existing supports are still valid with the new length
                self.check_valid_supports()
                return True
        
        # Method to remove the most recently added support
        def remove_last_support(self):
                if self.supports: # Check if the list is not empty
                        self.supports.pop()
                        return True
                return False

        # Method to remove the most recently added effort (load or point force)
        def remove_last_effort(self):
                if self.order_of_efforts:
                        # Get the type of the last effort
                        last_effort = self.order_of_efforts.pop()
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
        def check_valid_supports(self):
                for i, (pos, _) in enumerate(self.supports):
                        if not 0 <= pos <= self.length:
                                # Removes supports when length (L) is changed
                                self.supports.pop(i)
                                


        # Method to set the total number of nodes for calculations
        def set_total_node_num(self, new_node_num:int):
                try:
                        self.total_node_num = int(new_node_num)
                        return True
                except (ValueError, TypeError):
                        return False

        # Method to add a new support to the beam
        def add_support(self, position:float, support_type:str):

                # Check if the position is within the beam's length
                if 0 <= position <= self.length:
                        for already_saved_position, _ in self.supports:
                                # The program will not accept 2 supports too close together
                                if abs(position - already_saved_position) < self.length / self.total_node_num:
                                        return False 
                        self.supports.append((position, support_type))
                        
                        return True
                return False # Return false if position is not valid

        # Method to add a concentrated (point) load
        def add_point_load(self, magnitude:float, position:float, angle:float = 90):
                # Check if magnitude and angle values are valid
                if not isinstance(magnitude, (float, int)) or not 0 <= angle <= 180:
                        return False
                
                # Check if position is within the beam's length
                if 0 <= position <= self.length:
                        self.point_loads.append((magnitude, position, angle))
                        self.order_of_efforts.append("point")
                        return True
                return False
        
        # Method to add a distributed load
        def add_loads(self, pos_limits:tuple, magnitude:float):
                
                # Check if the load positions are within the beam's length
                for pos in pos_limits:
                        if not 0 <= pos <= self.length:
                                print("k1")
                                return False
                print(type(magnitude))
                # Check if the magnitude is a valid number
                if not isinstance(magnitude, (int, float)):
                        print("k2")
                        return False

                pos0, pos1 = pos_limits
                
                # Invert values if the start position is after the end position
                if pos0 > pos1:
                        pos0, pos1 = pos1, pos0

                self.loads.append(((pos0, pos1), magnitude))
                self.order_of_efforts.append("load")
                return True

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
        def draw_angled_line(self, length, start_pos, angle_degrees = 0):
                # Calculate the end point of the line
                p1 = (int(start_pos[0] + length * np.cos(angle_degrees * np.pi / 180)), int(start_pos[1] - length * np.sin(angle_degrees * np.pi / 180)))
                # Create the line on the canvas
                self.view.maincanvas.create_line(start_pos, p1, width = self.line_width, fill=self.line_color)
        
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
        def draw_circles_along_line(self, start_pos:tuple, end_pos:tuple, num_circles:int, **kwargs):
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
                        self.create_circle(canvas=self.view.maincanvas, center=(xi, yi), radius=cir_radius, **kwargs)

        # Draws a fixed support (restricts x and y movement)
        def draw_xy(self, beam_position:float, height:float, canvas:tk.Canvas):
                beam_length = self.view.controller.model.length
                                        
                # Map beam position to canvas coordinates
                x0 = int(self.view.canvas_padx + (self.view.canvas_w - 2*self.view.canvas_padx)*(beam_position / beam_length))
                y0 = self.view.beam_y

                p0 = (x0, y0)
                
                # Calculate the dimensions of the triangular support symbol
                side = 2 * height / float(np.tan(np.pi / 3))

                # Define the points of the triangle
                p1 = (x0 + side / 2, y0 + height)
                p2 = (x0 - side / 2, y0 + height)

                # Draw the triangle
                self.view.maincanvas.create_polygon(p0, p1, p2, p0, width = self.line_width, fill=self.sup_fill)
                self.view.maincanvas.create_line(p0, p1, p2, p0, width = self.line_width, fill=self.line_color)

                # Draw little hatching lines to indicate a fixed connection
                for i in np.linspace(p2[0], p1[0], 5):
                        
                        self.draw_angled_line(15, (i, y0 + height), 225)
        
        # Draws a roller support (restricts y movement)
        def draw_y(self, beam_position:float, height:float, canvas:tk.Canvas):
                beam_length = self.view.controller.model.length
                                        
                # Map beam position to canvas coordinates
                x0 = self.view.canvas_padx + (self.view.canvas_w - 2*self.view.canvas_padx)*(beam_position / beam_length)
                y0 = self.view.beam_y

                p0 = (x0, y0)
                
                # Calculate dimensions for the triangle
                side = 2 * height / float(np.tan(np.pi / 3))

                p1 = (x0 + side / 2, y0 + height)
                p2 = (x0 - side / 2, y0 + height)

                # Draw the triangle
                self.view.maincanvas.create_polygon(p0, p1, p2, p0, width = self.line_width, fill=self.sup_fill)
                self.view.maincanvas.create_line(p0, p1, p2, p0, width = self.line_width, fill=self.line_color)

                # Draw little circles to indicate a roller
                
                self.draw_circles_along_line(
                        start_pos=(p2[0], y0 + 1.2 * height),
                        end_pos=(p1[0], y0 + 1.2 * height),
                        num_circles=4,
                        width=self.line_width//1.5,
                        fill=self.sup_fill
                )
        
        # Draws a clamped or fixed-end support (restricts x, y, and z rotation)
        def draw_xyz(self, beam_position:float, height:float, canvas:tk.Canvas):
                beam_length = self.view.controller.model.length

                # Map beam position to canvas coordinates
                x0 = self.view.canvas_padx + (self.view.canvas_w - 2*self.view.canvas_padx)*(beam_position / beam_length)
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
                        polygon_points = [(x0 - height/(2*ratio), y0 - height), (x0 - height/(2*ratio), y0 + height), (x0 + height/(2*ratio), y0 + height), (x0 + height/(2*ratio), y0 - height)]
                        draw_lines = False 
                # Draw the main rectangle of the support
                self.view.maincanvas.create_polygon(*polygon_points, width = self.line_width, fill=self.sup_fill)
                self.view.maincanvas.create_line(*polygon_points, width = self.line_width, fill=self.line_color)

                # Draw hatching lines
                match draw_lines:
                        case "left":
                                for i in np.linspace(y0 - height, y0 + height, 7)[1:-1]: 
                                        self.draw_angled_line(15, (x0-height/ratio, i), 135)
                        case "right":
                                for i in np.linspace(y0 - height, y0 + height, 7)[1:-1]: 
                                        self.draw_angled_line(15, (x0+height/ratio, i), 45)
                
        # Draws a support that restricts x and z movement
        def draw_xz(self, beam_position:float, height:float, canvas:tk.Canvas):
                beam_length = self.view.controller.model.length

                # Map beam position to canvas coordinates
                x0 = self.view.canvas_padx + (self.view.canvas_w - 2*self.view.canvas_padx)*(beam_position / beam_length)
                y0 = self.view.beam_y
                p0 = (x0, y0)

                ratio = 6
                episilon = .1
                
                # Determine drawing logic based on position
                if abs(beam_position) < episilon: # Draw on the left
                        polygon_points = [p0, (x0, y0 - height), (x0 - height/ratio, y0 - height), (x0 - height/ratio, y0 + height), (x0, y0 + height), p0]
                
                        self.view.maincanvas.create_polygon(*polygon_points, width = self.line_width, fill=self.sup_fill)
                        self.view.maincanvas.create_line(*polygon_points, width = self.line_width, fill=self.line_color)

                        # Draw circles to indicate roller-like behavior in one plane
                        self.draw_circles_along_line(
                                start_pos=(x0 - 2 * height/ratio, y0 + height),
                                end_pos=(x0 - 2 * height/ratio, y0 - height),
                                num_circles=6,
                                width=self.line_width//1.5,
                                fill=self.sup_fill 
                        )
                elif abs(beam_position - beam_length) < episilon: # Draw on the right
                        polygon_points = [p0, (x0, y0 - height), (x0 + height/ratio, y0 - height), (x0 + height/ratio, y0 + height), (x0, y0 + height), p0]
                        
                        self.view.maincanvas.create_polygon(*polygon_points, width = self.line_width, fill=self.sup_fill)
                        self.view.maincanvas.create_line(*polygon_points, width = self.line_width, fill=self.line_color)

                        self.draw_circles_along_line(
                                start_pos=(x0 + 2 * height/ratio, y0 + height),
                                end_pos=(x0 + 2 * height/ratio, y0 - height),
                                num_circles=6,
                                width=self.line_width//1.5,
                                fill=self.sup_fill 
                        )

                else: # Draw in the middle
                        polygon_points = [(x0 - height/(2*ratio), y0 - height), (x0 - height/(2*ratio), y0 + height), (x0 + height/(2*ratio), y0 + height), (x0 + height/(2*ratio), y0 - height)]
                        draw_lines = False 
        
        # Draws a point load (arrow) on the beam
        def draw_point_load(self, beam_position:float, height:float, canvas:tk.Canvas, magnitude:float, angle:float = 90, literal_coords = False, write = True):
                
                
                # Get the maximum force to scale the arrow size
                self.max_force = self.view.controller.model.get_max_force()

                
                # Calculate the height of the arrow based on its magnitude relative to the max force
                draw_height = height / 3 * (2 * abs(magnitude) / self.max_force + 1)


                beam_length = self.view.controller.model.length
                # Map beam position to canvas x-coordinate
                x0 = self.view.canvas_padx + (self.view.canvas_w - 2*self.view.canvas_padx)*(beam_position / beam_length)

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
                self.view.maincanvas.create_line(
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
                        self.view.maincanvas.create_text(
                                (start_x, start_y + k * draw_height / 5),
                                text = f"{abs(magnitude):.2f}",
                                fill = self.eff_fill, 
                                font = f"TkDefaultFont {int(height / 3)}"
                )
        
        # Draws a distributed load on the beam
        def draw_load(self, pos_limits:tuple, height:float, canvas:tk.Canvas, magnitude:float):

                beam_length = self.view.controller.model.length

                # Get max force to scale the drawing
                self.max_force = self.view.controller.model.get_max_force()
                
                # Calculate drawing height based on magnitude
                draw_height = height / 3 * (2 * abs(magnitude) / self.max_force + 1)

                x0, x1 = pos_limits
                # Map beam positions to canvas coordinates
                x0 = self.view.canvas_padx + (self.view.canvas_w - 2*self.view.canvas_padx)*(x0 / beam_length)
                x1 = self.view.canvas_padx + (self.view.canvas_w - 2*self.view.canvas_padx)*(x1 / beam_length)

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
                self.view.maincanvas.create_line((x0, self.view.beam_y - draw_height), (x1, self.view.beam_y - draw_height), width=self.line_width, fill=self.eff_fill)

                # Write the magnitude of the distributed load
                self.view.maincanvas.create_text(
                        (x0 + abs(x0 - x1) / 2, self.view.beam_y - draw_height * (7/6)),
                        text = f"{abs(magnitude):.2f}",
                        fill = self.eff_fill, 
                        font = f"TkDefaultFont {int(height / 3)}"
                )
        
        def draw_bird(self, topleft, size, canvas:tk.Canvas, color):
                
                bird_coords, eye_coords = bird_coords[:-4], bird_coords[-4:]

                


                

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

                # Set terminal variables
                self.terminal_scroller_offset = 0
                self.terminal_messages = []

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
                ttk.Separator(frame).pack(fill="x", pady=12, side="top")
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

                self.terminal_canvas = tk.Canvas(self.terminal_frame, bg="#eeeeee", bd=2, relief="groove")
                self.terminal_canvas.pack(fill="both", expand=True, padx=5)
                self.terminal_canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)

                # Control Panel for user inputs
                self.control_frame = tk.Frame(self.main_frame, width = 250)
                self.control_frame.pack(side="right", fill="y", padx=5, pady=5)
                
                # Initial drawing of the beam and setup of control panel sections
                self.draw_beam()
                self.length_gui()
                self.supports_gui()
                self.loads_gui()
                self.solve_gui()


        # Creates the GUI elements for setting the beam length
        def length_gui(self):
                # length section
                self.create_separator(self.control_frame, text=None, pady=3)

                # frame for sideways packing
                len_frame = ttk.Frame(self.control_frame)
                len_frame.pack(pady=3)

                # Length input
                ttk.Label(
                        len_frame,
                        text="Length",
                        font=self.font
                ).pack(side="left")
                self.len_var = tk.StringVar(value="10.0")
                ttk.Entry(
                        len_frame,
                        textvariable=self.len_var
                ).pack(fill="x", side="left")

                ttk.Button(
                        self.control_frame,
                        text="Set Length (m)",
                        command=lambda: self.controller.set_length(self.len_var.get())
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
                self.create_separator(title_load_frame, "Forces & Loads", side="left")

                # A placeholder help button
                ttk.Button(title_load_frame, text="?", command=None, width=1).pack(side="left")

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

                # Solve button (command not yet implemented)
                solve_button = ttk.Button(self.control_frame, text="Solve", command=self.controller.save_button_clicked)
                solve_button.pack(pady=2)

                self.after_solve_frame = ttk.Frame(self.control_frame)
                self.after_solve_frame.pack(pady=3)

        def destroy_after_solve_gui(self):
                for widget in self.after_solve_frame.winfo_children():
                        widget.destroy()

        def after_solve_gui(self):
                self.destroy_after_solve_gui()

                # See Normal 
                ttk.Button(
                        self.after_solve_frame,
                        text="Normal",
                        command=None
                ).grid(row=0, column=0, padx=2, pady=2)

                # See Slice 
                ttk.Button(
                        self.after_solve_frame,
                        text="Cortante",
                        command=None
                ).grid(row=0, column=1, padx=2, pady=2)

                # See Moment 
                ttk.Button(
                        self.after_solve_frame,
                        text="Moment",
                        command=None
                ).grid(row=1, column=0, padx=2, pady=2)

        def on_mouse_wheel(self, event):
                self.terminal_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def add_terminal_message(self, message):
                self.terminal_messages.append(message)

        def draw_terminal(self):
                if not self.view_solution:
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

        # Redraws the entire canvas
        def draw_beam(self):
                # Clear the canvas
                self.maincanvas.delete("all")
                # Get current canvas dimensions
                self.canvas_w, self.canvas_h = self.maincanvas.winfo_width(), self.maincanvas.winfo_height()
                

                # Define the y-position of the beam on the canvas
                self.beam_y = self.canvas_h // 2

                # Define padding on the sides of the canvas
                self.canvas_padx = 50

                std_height = self.canvas_h / 10

                # Draw the main beam line
                self.maincanvas.create_line(self.canvas_padx, self.beam_y, self.canvas_w - self.canvas_padx, self.beam_y, width = 3, fill="black")

                # Draw all saved supports
                for support_pos, support_type in self.controller.model.supports:
                        # Call the appropriate drawing function from the pencil's mapper
                        self.pencil.mapper[support_type](support_pos, std_height, canvas=self.maincanvas)
                        
                # Draw all saved point forces
                for magnitude, force_pos, angle in self.controller.model.point_loads:
                        self.pencil.draw_point_load(beam_position=force_pos, height=std_height, canvas=self.maincanvas, angle=angle, magnitude=magnitude)

                # Draw all saved distributed loads
                for pos_limits, magnitude in self.controller.model.loads:
                        self.pencil.draw_load(pos_limits=pos_limits, height=std_height, canvas=self.maincanvas, magnitude=magnitude)
        
        def update_display(self):
                self.draw_beam()
                self.draw_terminal()

# This class acts as the controller (in the MVC pattern), handling user input and updating the model and view
class Controller():
        # Initialize the controller
        def __init__(self):
                # Create instances of the model and view
                self.model = Model()
                self.view = View(self)

                # When the canvas is resized, call the update_display method
                self.view.maincanvas.bind("<Configure>", self.update_display)
        
        # This method is called to refresh the drawing on the canvas
        def update_display(self, event=None):
                self.view.update_display()
        
        # Handles the "Remove Support" button click
        def remove_last_support(self):
                # If the model successfully removes a support, update the view
                if self.model.remove_last_support():
                        self.view.add_terminal_message("Support Removed.")
                        self.update_display()
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
        
        # Handles the "Set Length" button click
        def set_length(self, new_length):
                # Validate the input
                try:
                        new_length = float(new_length)
                except (ValueError, TypeError):
                        return False
                
                # If the model successfully sets the length, update the view
                if self.model.set_length(new_length):
                        self.view.add_terminal_message(f"New Length set to:{new_length}")
                        self.update_display()
                        return True
                return False

        # Handles the "Add Support" button click
        def add_support(self, position, support_type):

                # Validate the position input
                try:
                        position = float(position)
                except (ValueError, TypeError):
                        return False
                # Check if the support type is valid/implemented
                if support_type not in self.view.pencil.mapper:
                        print("not yet supported")
                        return False
                
                # If the model successfully adds the support, update the view
                if self.model.add_support(position, support_type):
                        self.view.add_terminal_message(f"New support {support_type} added to:{position}")
                        self.update_display()
                        return True
                
                return False

        # Handles the "Add Force" button click
        def add_effort(self, magnitude:float, position, angle:float = 90):
                # Check if the position input is for a distributed load (e.g., "2;5")
                if ";" in position:
                        try:
                                # Parse positions, magnitude, and angle
                                pos0, pos1 = [float(i) for i in position.split(";")[:2]]
                                magnitude = float(magnitude)
                                angle = float(angle)

                        except (ValueError, TypeError):
                                return False
                # Otherwise, it's a point load
                else:
                        try:
                                # Parse magnitude, angle, and position
                                magnitude = float(magnitude)
                                angle = float(angle)
                                pos0 = float(position)
                                pos1 = None
                        except (ValueError, TypeError):
                                return False
        
                # If pos1 is None, it's a point load
                if pos1 is None:
                        # If the model adds the point load, update the display
                        if self.model.add_point_load(magnitude=magnitude, position=pos0, angle=angle):
                                self.view.add_terminal_message(f"New force ({magnitude}>{angle}°) added to:{position}")
                                self.update_display()
                                return True
                        return False

                # If pos1 is valid, it's a distributed load
                if self.model.add_loads(pos_limits=(pos0, pos1), magnitude=magnitude):
                        self.view.add_terminal_message(f"New load ({magnitude}) added from {pos0} to {pos1}")
                        self.update_display()
                        return True
                return False

        def save_button_clicked(self):
                self.view.after_solve_gui()
                self.update_display()

        # Starts the main event loop of the application
        def run(self):
                self.view.mainloop()
        



# This block runs if the script is executed directly
if __name__ == "__main__":
        # Create an instance of the controller
        app = Controller()
        # Start the application
        app.run()
