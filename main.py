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
                        arrowshape=(10, 12, 5) # Customize arrowhead shape (length, fullwidth, halfwidth at base)
                )
                # If specified, write the magnitude of the force
                if write:
                        is_up = end_pos[1] < start_y

                        k = 1 if is_up else -1

                        # Write force magnitude text on the canvas
                        self.view.maincanvas.create_text(
                                (start_x, start_y + k * draw_height / 8),
                                text = f"{abs(magnitude):.2f}",
                                fill = self.eff_fill, 
                                font = f"TkDefaultFont {int(height / 4)}"
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
                N = int(abs(x0 - x1) / (height / 5))

                # Draw a series of small point loads to represent the distributed load
                for i in np.linspace(x0, x1, N):
                        print(i)
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
                        font = f"TkDefaultFont {int(height / 4)}"
                )
                



                


# This class represents the main application window (GUI)
class View(tk.Tk):
        # Initialize the view
        def __init__(self, controller):
                super().__init__("View")
                self.controller = controller
                
                # Set window size
                self.geometry("1000x700")
                # Create a pencil for drawing
                self.pencil = Pencil(self)
                self.pack_propagate = False
                # Set up the GUI elements
                self.start_gui()
                # Set up styling for ttk widgets
                self.setup_styler()

        # Configures the style for themed Tkinter widgets
        def setup_styler(self):
                self.styler = ttk.Style()
                self.styler.configure("TFrame", background="#f0f0f0")
                self.styler.configure("TLabel", padding=5, background="#f0f0f0")
                self.styler.configure("TButton", padding=5) 

        # Helper function to create a separator with a title
        def create_separator(self, frame, text, side = "top"):
                ttk.Separator(frame).pack(fill="x", pady=12, side="top")
                (ttk.Label(
                        frame,
                        text=text,
                        font=("Arial", 10, "bold")
                        )
                ).pack(side=side)  
        
        # Method to create and arrange all the main GUI components
        def start_gui(self):
                # Main layout containers
                self.main_frame = ttk.Frame(self)
                self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

                # Canvas for drawing the beam
                self.canvas_frame = ttk.Frame(self.main_frame)
                self.canvas_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

                self.maincanvas = tk.Canvas(self.canvas_frame, bg="white", bd=2, relief="groove")
                self.maincanvas.pack(fill="both", expand=True, padx=5, pady=5)


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
                # Length entry field
                self.len_var = tk.StringVar(value="10.0")
                len_entry = ttk.Entry(self.control_frame, textvariable=self.len_var)
                len_entry.pack(fill="x", padx=5, pady=2)
                ttk.Button(
                        self.control_frame, text="Set Length (m)",
                        command=lambda: self.controller.set_length(self.len_var.get())
                ).pack(pady=2)

        # Creates the GUI elements for adding/removing supports
        def supports_gui(self):
                # Support controls section
                self.create_separator(self.control_frame, "Supports")
                
                # Frame for the position input
                line1 = ttk.Frame(self.control_frame)
                line1.pack(pady=5)
                ttk.Label(line1, text="Position", font=("Arial", 10, "bold"), width=10).pack(side="left", padx=2)
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
                ttk.Label(line1, text="Position", font=("Arial", 10, "bold"), width=10).pack(side="left", padx=2)
                self.load_pos_strgvar = tk.StringVar(value="")
                ttk.Entry(line1, textvariable=self.load_pos_strgvar, width = 12).pack()
                
                # Magnitude input
                line2.pack(pady=lines_pady)
                ttk.Label(line2, text="Magnitude", font=("Arial", 10, "bold"), width=10).pack(side="left", padx=2)
                self.mag_strgvar = tk.StringVar(value="")
                ttk.Entry(line2, textvariable=self.mag_strgvar, width = 12).pack()

                # Angle input
                line3.pack(pady=lines_pady)
                ttk.Label(line3, text="Angle", font=("Arial", 10, "bold"), width=10).pack(side="left", padx=2)
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
                self.create_separator(frame = self.control_frame, text="")

                # Solve button (command not yet implemented)
                solve_button = ttk.Button(self.control_frame, text="Solve", command=None)
                solve_button.pack(pady=2)

        


        # Redraws the entire canvas
        def draw_beam(self):
                # Clear the canvas
                self.maincanvas.delete("all")
                # Get current canvas dimensions
                self.canvas_w, self.canvas_h = self.maincanvas.winfo_width(), self.maincanvas.winfo_height()
                

                # Define the y-position of the beam on the canvas
                self.beam_y = self.canvas_h // 3

                # Define padding on the sides of the canvas
                self.canvas_padx = 50

                # Draw the main beam line
                self.maincanvas.create_line(self.canvas_padx, self.beam_y, self.canvas_w - self.canvas_padx, self.beam_y, width = 3, fill="black")

                # Draw all saved supports
                for support_pos, support_type in self.controller.model.supports:
                        # Call the appropriate drawing function from the pencil's mapper
                        self.pencil.mapper[support_type](support_pos, self.canvas_h//22, canvas=self.maincanvas)
                        
                # Draw all saved point forces
                for magnitude, force_pos, angle in self.controller.model.point_loads:
                        self.pencil.draw_point_load(beam_position=force_pos, height=self.canvas_h//11, canvas=self.maincanvas, angle=angle, magnitude=magnitude)

                # Draw all saved distributed loads
                for pos_limits, magnitude in self.controller.model.loads:
                        self.pencil.draw_load(pos_limits=pos_limits, height=self.canvas_h//11, canvas=self.maincanvas, magnitude=magnitude)

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

                self.view.draw_beam()
        
        # Handles the "Remove Support" button click
        def remove_last_support(self):
                # If the model successfully removes a support, update the view
                if self.model.remove_last_support():
                        self.update_display()
                        return True
                return False

        # Handles the "Remove Force" button click
        def remove_last_effort(self):
                # If the model successfully removes an effort, update the view
                if self.model.remove_last_effort():
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

                        # starttemp (Temporary print for debugging)
                        print("-"*10)
                        for i in self.model.supports:
                                print(i)
                        print("-"*10)
                        # endtemp

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
                                self.update_display()
                                print(1)
                                return True
                        print(2)
                        return False

                # If pos1 is valid, it's a distributed load
                if self.model.add_loads(pos_limits=(pos0, pos1), magnitude=magnitude):
                        self.update_display()
                        print(3)
                        return True
                print(4)
                return False
                

        # Starts the main event loop of the application
        def run(self):
                self.view.mainloop()
        



# This block runs if the script is executed directly
if __name__ == "__main__":
        # Create an instance of the controller
        app = Controller()
        # Start the application
        app.run()
