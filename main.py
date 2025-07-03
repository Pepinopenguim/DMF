import tkinter as tk
import numpy as np
from tkinter import ttk

class Model():
        def __init__(self):
                self.length = 10
                self.total_node_num = 30
                self.nodes = [] # (position, support)

                self.point_loads = [] # (magnitude, position, angle)
                self.loads = [] # pos_tuple, magnitude
                self.order_of_efforts = []

                self.supports = [] # position, support_type
                self.materials = {
                        "E":2e11, # Pa
                        "I":10e-6, # m^4
                }

        def get_max_force(self):
                max_force = 0
                for magnitude, _, _ in self.point_loads:
                        if abs(magnitude) > max_force:
                                max_force = abs(magnitude)
                for _, magnitude in self.loads:
                        if abs(magnitude) > max_force:
                                max_force = abs(magnitude)
                return max_force
        
        def set_length(self, new_length:float):
                self.length = new_length
                self.check_valid_supports()
                return True
        
        def remove_last_support(self):
                if self.supports: # check if not null
                        self.supports.pop()
                        return True
                return False

        def remove_last_effort(self):
                if self.order_of_efforts:
                        last_effort = self.order_of_efforts.pop()
                else:
                        return False

                match last_effort:
                        case "point":
                                self.point_loads.pop()
                        case "load":
                                self.loads.pop()
                return True


        def check_valid_supports(self):
                for i, (pos, _) in enumerate(self.supports):
                        if not 0 <= pos <= self.length:
                                self.supports.pop(i)
                                # removes supports when L is changed 


        def set_total_node_num(self, new_node_num:int):
                try:
                        self.total_node_num = int(new_node_num)
                        return True
                except (ValueError, TypeError):
                        return False

        def add_support(self, position:float, support_type:str):

                # check if position inside beam
                if 0 <= position <= self.length:
                        for already_saved_position, _ in self.supports:
                                # the program will not accept 2 supports too close together
                                if abs(position - already_saved_position) < self.length / self.total_node_num:
                                        return False 
                        self.supports.append((position, support_type))
                        
                        return True
                return False # position not valid
        
        def add_point_load(self, magnitude:float, position:float, angle:float = 90):
                # check if magnitude and angles are valid
                if not isinstance(magnitude, (float, int)) or not 0 <= angle <= 180:
                        return False
                
                # check if position inside beam
                if 0 <= position <= self.length:
                        self.point_loads.append((magnitude, position, angle))
                        self.order_of_efforts.append("point")
                        return True
                return False
        
        def add_loads(self, pos_limits:tuple, magnitude:float):
                
                for pos in pos_limits:
                        if not 0 <= pos <= self.length:
                                print("k1")
                                return False
                print(type(magnitude))
                if not isinstance(magnitude, (int, float)):
                        print("k2")
                        return False

                pos0, pos1 = pos_limits
                
                # invert values if order is wrong
                if pos0 > pos1:
                        pos0, pos1 = pos1, pos0

                self.loads.append(((pos0, pos1), magnitude))
                self.order_of_efforts.append("load")
                return True

class Pencil():
        def __init__(self, view, width = 2, sup_fill = "blue", eff_fill = "red", line_color = "black"):
                self.view = view
                self.line_width = width
                self.line_color = line_color
                self.sup_fill = sup_fill
                self.eff_fill = eff_fill
                self.max_force = 0

                self.mapper = {
                        "xy":self.draw_xy,
                        "y":self.draw_y,
                        "xyz":self.draw_xyz,
                        "xz":self.draw_xz,
                }
        
        def draw_angled_line(self, length, start_pos, angle_degrees = 0):
                p1 = (int(start_pos[0] + length * np.cos(angle_degrees * np.pi / 180)), int(start_pos[1] - length * np.sin(angle_degrees * np.pi / 180)))
                self.view.maincanvas.create_line(start_pos, p1, width = self.line_width, fill=self.line_color)
        
        def create_circle(self, canvas, center, radius, **options):
                cx, cy = center
                x0 = cx - radius
                y0 = cy - radius
                x1 = cx + radius
                y1 = cy + radius

                return canvas.create_oval(x0, y0, x1, y1, **options)


        def draw_circles_along_line(self, start_pos:tuple, end_pos:tuple, num_circles:int, **kwargs):
                start_x, start_y = start_pos
                length_x = end_pos[0] - start_pos[0]
                length_y = end_pos[1] - start_pos[1]
                
                length = int(np.linalg.norm([length_x, length_y]))
                cir_radius = length / (2 * num_circles)

                
                for i in range(1, num_circles+1):
                        xi = start_x + length_x * cir_radius * (2*i - 1) / length
                        yi = start_y + length_y * cir_radius * (2*i - 1) / length

                        self.create_circle(canvas=self.view.maincanvas, center=(xi, yi), radius=cir_radius, **kwargs)

        def draw_xy(self, beam_position:float, height:float, canvas:tk.Canvas):
                beam_length = self.view.controller.model.length
                        
                x0 = int(self.view.canvas_padx + (self.view.canvas_w - 2*self.view.canvas_padx)*(beam_position / beam_length))
                y0 = self.view.beam_y

                p0 = (x0, y0)
                
                side = 2 * height / float(np.tan(np.pi / 3))

                p1 = (x0 + side / 2, y0 + height)
                p2 = (x0 - side / 2, y0 + height)

                self.view.maincanvas.create_polygon(p0, p1, p2, p0, width = self.line_width, fill=self.sup_fill)
                self.view.maincanvas.create_line(p0, p1, p2, p0, width = self.line_width, fill=self.line_color)

                # draw little lines :)
                for i in np.linspace(p2[0], p1[0], 5):
                        
                        self.draw_angled_line(15, (i, y0 + height), 225)
        
        def draw_y(self, beam_position:float, height:float, canvas:tk.Canvas):
                beam_length = self.view.controller.model.length
                        
                x0 = self.view.canvas_padx + (self.view.canvas_w - 2*self.view.canvas_padx)*(beam_position / beam_length)
                y0 = self.view.beam_y

                p0 = (x0, y0)
                
                side = 2 * height / float(np.tan(np.pi / 3))

                p1 = (x0 + side / 2, y0 + height)
                p2 = (x0 - side / 2, y0 + height)

                self.view.maincanvas.create_polygon(p0, p1, p2, p0, width = self.line_width, fill=self.sup_fill)
                self.view.maincanvas.create_line(p0, p1, p2, p0, width = self.line_width, fill=self.line_color)

                # draw little circles :)
                
                self.draw_circles_along_line(
                        start_pos=(p2[0], y0 + 1.2 * height),
                        end_pos=(p1[0], y0 + 1.2 * height),
                        num_circles=4,
                        width=self.line_width//1.5,
                        fill=self.sup_fill
                )
        
        def draw_xyz(self, beam_position:float, height:float, canvas:tk.Canvas):
                beam_length = self.view.controller.model.length

                x0 = self.view.canvas_padx + (self.view.canvas_w - 2*self.view.canvas_padx)*(beam_position / beam_length)
                y0 = self.view.beam_y
                p0 = (x0, y0)

                ratio = 6
                episilon = .1
                
                if abs(beam_position) < episilon: # draw to the left
                        polygon_points = [p0, (x0, y0 - height), (x0 - height/ratio, y0 - height), (x0 - height/ratio, y0 + height), (x0, y0 + height), p0]
                        draw_lines = "left"
                elif abs(beam_position - beam_length) < episilon: # draw to the right
                        polygon_points = [p0, (x0, y0 - height), (x0 + height/ratio, y0 - height), (x0 + height/ratio, y0 + height), (x0, y0 + height), p0]
                        draw_lines = "right"
                else:
                        polygon_points = [(x0 - height/(2*ratio), y0 - height), (x0 - height/(2*ratio), y0 + height), (x0 + height/(2*ratio), y0 + height), (x0 + height/(2*ratio), y0 - height)]
                        draw_lines = False 
                self.view.maincanvas.create_polygon(*polygon_points, width = self.line_width, fill=self.sup_fill)
                self.view.maincanvas.create_line(*polygon_points, width = self.line_width, fill=self.line_color)

                match draw_lines:
                        case "left":
                                for i in np.linspace(y0 - height, y0 + height, 7)[1:-1]: 
                                        self.draw_angled_line(15, (x0-height/ratio, i), 135)
                        case "right":
                                for i in np.linspace(y0 - height, y0 + height, 7)[1:-1]: 
                                        self.draw_angled_line(15, (x0+height/ratio, i), 45)
                
        def draw_xz(self, beam_position:float, height:float, canvas:tk.Canvas):
                beam_length = self.view.controller.model.length

                x0 = self.view.canvas_padx + (self.view.canvas_w - 2*self.view.canvas_padx)*(beam_position / beam_length)
                y0 = self.view.beam_y
                p0 = (x0, y0)

                ratio = 6
                episilon = .1
                
                if abs(beam_position) < episilon: # draw to the left
                        polygon_points = [p0, (x0, y0 - height), (x0 - height/ratio, y0 - height), (x0 - height/ratio, y0 + height), (x0, y0 + height), p0]
                
                        self.view.maincanvas.create_polygon(*polygon_points, width = self.line_width, fill=self.sup_fill)
                        self.view.maincanvas.create_line(*polygon_points, width = self.line_width, fill=self.line_color)

                        self.draw_circles_along_line(
                                start_pos=(x0 - 2 * height/ratio, y0 + height),
                                end_pos=(x0 - 2 * height/ratio, y0 - height),
                                num_circles=6,
                                width=self.line_width//1.5,
                                fill=self.sup_fill 
                        )
                elif abs(beam_position - beam_length) < episilon: # draw to the right
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

                else:
                        polygon_points = [(x0 - height/(2*ratio), y0 - height), (x0 - height/(2*ratio), y0 + height), (x0 + height/(2*ratio), y0 + height), (x0 + height/(2*ratio), y0 - height)]
                        draw_lines = False 
        def draw_point_load(self, beam_position:float, height:float, canvas:tk.Canvas, magnitude:float, angle:float = 90, literal_coords = False, write = True):
                
                
                self.max_force = self.view.controller.model.get_max_force()

                
                draw_height = height / 3 * (2 * abs(magnitude) / self.max_force + 1)


                beam_length = self.view.controller.model.length
                x0 = self.view.canvas_padx + (self.view.canvas_w - 2*self.view.canvas_padx)*(beam_position / beam_length)

                if literal_coords:
                        x0 = beam_position

                y0 = self.view.beam_y
                end_pos = (x0, y0)

                

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
                if write:
                        is_up = end_pos[1] < start_y

                        k = 1 if is_up else -1

                        # write force magnitude
                        self.view.maincanvas.create_text(
                                (start_x, start_y + k * draw_height / 8),
                                text = f"{abs(magnitude):.2f}",
                                fill = self.eff_fill, 
                                font = f"TkDefaultFont {int(height / 4)}"
        )
        def draw_load(self, pos_limits:tuple, height:float, canvas:tk.Canvas, magnitude:float):

                beam_length = self.view.controller.model.length

                self.max_force = self.view.controller.model.get_max_force()
                
                draw_height = height / 3 * (2 * abs(magnitude) / self.max_force + 1)

                x0, x1 = pos_limits
                x0 = self.view.canvas_padx + (self.view.canvas_w - 2*self.view.canvas_padx)*(x0 / beam_length)
                x1 = self.view.canvas_padx + (self.view.canvas_w - 2*self.view.canvas_padx)*(x1 / beam_length)

                N = int(abs(x0 - x1) / (height / 5))

                for i in np.linspace(x0, x1, N):
                        print(i)
                        self.draw_point_load(
                                beam_position=i,
                                height=height,
                                canvas=canvas,
                                magnitude=magnitude,
                                literal_coords=True,
                                write=False
                        )
                
                # line
                self.view.maincanvas.create_line((x0, self.view.beam_y - draw_height), (x1, self.view.beam_y - draw_height), width=self.line_width, fill=self.eff_fill)

                # text

                # write force magnitude
                self.view.maincanvas.create_text(
                        (x0 + abs(x0 - x1) / 2, self.view.beam_y - draw_height * (7/6)),
                        text = f"{abs(magnitude):.2f}",
                        fill = self.eff_fill, 
                        font = f"TkDefaultFont {int(height / 4)}"
                )
                



                


class View(tk.Tk):
        def __init__(self, controller):
                super().__init__("View")
                self.controller = controller
                
                self.geometry("1000x700")
                self.pencil = Pencil(self)
                self.pack_propagate = False
                self.start_gui()
                self.setup_styler()

        def setup_styler(self):
                self.styler = ttk.Style()
                self.styler.configure("TFrame", background="#f0f0f0")
                self.styler.configure("TLabel", padding=5, background="#f0f0f0")
                self.styler.configure("TButton", padding=5) 

        def create_separator(self, frame, text, side = "top"):
                ttk.Separator(frame).pack(fill="x", pady=12, side="top")
                (ttk.Label(
                        frame,
                        text=text,
                        font=("Arial", 10, "bold")
                        )
                ).pack(side=side)  
        
        def start_gui(self):
                # Main layout containers
                self.main_frame = ttk.Frame(self)
                self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

                # Canvas
                self.canvas_frame = ttk.Frame(self.main_frame)
                self.canvas_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

                self.maincanvas = tk.Canvas(self.canvas_frame, bg="white", bd=2, relief="groove")
                self.maincanvas.pack(fill="both", expand=True, padx=5, pady=5)


                # Control Panel
                self.control_frame = tk.Frame(self.main_frame, width = 250)
                self.control_frame.pack(side="right", fill="y", padx=5, pady=5)
                
                self.draw_beam()
                self.length_gui()
                self.supports_gui()
                self.loads_gui()
                self.solve_gui()


        def length_gui(self):
                # Length entry
                self.len_var = tk.StringVar(value="10.0")
                len_entry = ttk.Entry(self.control_frame, textvariable=self.len_var)
                len_entry.pack(fill="x", padx=5, pady=2)
                ttk.Button(
                        self.control_frame, text="Set Length (m)",
                        command=lambda: self.controller.set_length(self.len_var.get())
                ).pack(pady=2)

        def supports_gui(self):
                # support controls
                self.create_separator(self.control_frame, "Supports")
                
                line1 = ttk.Frame(self.control_frame)
                line1.pack(pady=5)
                ttk.Label(line1, text="Position", font=("Arial", 10, "bold"), width=10).pack(side="left", padx=2)
                self.support_pos_strgvar = tk.StringVar(value="")
                support_pos_entry = ttk.Entry(line1, textvariable=self.support_pos_strgvar, width = 12)
                support_pos_entry.pack(side="left")

                chkbtn_frame = ttk.Frame(self.control_frame)
                chkbtn_frame.pack(padx=5, pady=5)

                self.Var1 = tk.IntVar(value=0)
                self.Var2 = tk.IntVar(value=0)
                self.Var3 = tk.IntVar(value=0)


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

                sup_button_frame = ttk.Frame(self.control_frame)
                sup_button_frame.pack(pady=5)

                ttk.Button(
                        sup_button_frame,
                        text="Add Support",
                        command=lambda :self.controller.add_support(
                                position=self.support_pos_strgvar.get(),
                                support_type=self.Var1.get()*"x" + self.Var2.get()*"y" + self.Var3.get()*"z"
                        )
                ).pack(side="left", padx = 2)
                ttk.Button(
                        sup_button_frame,
                        text="Remove Support",
                        command=self.controller.remove_last_support        
                ).pack(side="left", padx = 2)

        def loads_gui(self):
                title_load_frame = ttk.Frame(self.control_frame, width=250)
                title_load_frame.pack()
                self.create_separator(title_load_frame, "Forces & Loads", side="left")

                ttk.Button(title_load_frame, text="?", command=None, width=1).pack(side="left")

                line1 = tk.Frame(self.control_frame)
                line2 = tk.Frame(self.control_frame)
                line3 = tk.Frame(self.control_frame)
                lines_pady = 1

                line1.pack(pady=lines_pady)
                ttk.Label(line1, text="Position", font=("Arial", 10, "bold"), width=10).pack(side="left", padx=2)
                self.load_pos_strgvar = tk.StringVar(value="")
                ttk.Entry(line1, textvariable=self.load_pos_strgvar, width = 12).pack()
                
                line2.pack(pady=lines_pady)
                ttk.Label(line2, text="Magnitude", font=("Arial", 10, "bold"), width=10).pack(side="left", padx=2)
                self.mag_strgvar = tk.StringVar(value="")
                ttk.Entry(line2, textvariable=self.mag_strgvar, width = 12).pack()

                line3.pack(pady=lines_pady)
                ttk.Label(line3, text="Angle", font=("Arial", 10, "bold"), width=10).pack(side="left", padx=2)
                self.angle_strgvar = tk.StringVar(value="90")
                ttk.Entry(line3, textvariable=self.angle_strgvar, width = 12).pack()

                load_button_frame = ttk.Frame(self.control_frame)
                load_button_frame.pack(pady = 5)

                ttk.Button(
                        load_button_frame,
                        text="Add Force",
                        command=lambda: self.controller.add_effort(
                                magnitude=self.mag_strgvar.get(),
                                position=self.load_pos_strgvar.get(),
                                angle = self.angle_strgvar.get()
                        )
                ).pack(side="left", padx=2)

                ttk.Button(
                        load_button_frame,
                        text="Remove Force",
                        command=self.controller.remove_last_effort
                ).pack(side="left", padx=2)
        
        def solve_gui(self):
                self.create_separator(frame = self.control_frame, text="")

                solve_button = ttk.Button(self.control_frame, text="Solve", command=None)
                solve_button.pack(pady=2)

        


        def draw_beam(self):
                self.maincanvas.delete("all")
                self.canvas_w, self.canvas_h = self.maincanvas.winfo_width(), self.maincanvas.winfo_height()
                

                self.beam_y = self.canvas_h // 3

                self.canvas_padx = 50

                self.maincanvas.create_line(self.canvas_padx, self.beam_y, self.canvas_w - self.canvas_padx, self.beam_y, width = 3, fill="black")

                # draw supports
                for support_pos, support_type in self.controller.model.supports:
                        self.pencil.mapper[support_type](support_pos, self.canvas_h//22, canvas=self.maincanvas)
                        
                # draw forces
                for magnitude, force_pos, angle in self.controller.model.point_loads:
                        self.pencil.draw_point_load(beam_position=force_pos, height=self.canvas_h//11, canvas=self.maincanvas, angle=angle, magnitude=magnitude)

                # draw loads
                for pos_limits, magnitude in self.controller.model.loads:
                        self.pencil.draw_load(pos_limits=pos_limits, height=self.canvas_h//11, canvas=self.maincanvas, magnitude=magnitude)

class Controller():
        def __init__(self):
                self.model = Model()
                self.view = View(self)

                # When canvas is resized, update display
                self.view.maincanvas.bind("<Configure>", self.update_display)
        
        def update_display(self, event=None):

                self.view.draw_beam()
        
        def remove_last_support(self):
                if self.model.remove_last_support():
                        self.update_display()
                        return True
                return False

        def remove_last_effort(self):
                if self.model.remove_last_effort():
                        self.update_display()
                        return True
                return False
        
        def set_length(self, new_length):
                # check if its valid
                try:
                        new_length = float(new_length)
                except (ValueError, TypeError):
                        return False
                
                if self.model.set_length(new_length):
                        self.update_display()
                        return True
                return False

        def add_support(self, position, support_type):

                # checks if position argument is valid
                try:
                        position = float(position)
                except (ValueError, TypeError):
                        return False
                # checks if support_type valid
                if support_type not in self.view.pencil.mapper:
                        print("not yet supported")
                        return False
                
                if self.model.add_support(position, support_type):

                        # starttemp
                        print("-"*10)
                        for i in self.model.supports:
                                print(i)
                        print("-"*10)
                        # endtemp

                        self.update_display()
                        return True
                
                
                
                return False

        def add_effort(self, magnitude:float, position, angle:float = 90):
                if ";" in position:
                        try:
                                pos0, pos1 = [float(i) for i in position.split(";")[:2]]
                                magnitude = float(magnitude)
                                angle = float(angle)

                        except (ValueError, TypeError):
                                return False
                else:
                        try:
                                magnitude = float(magnitude)
                                angle = float(angle)
                                pos0 = float(position)
                                pos1 = None
                        except (ValueError, TypeError):
                                return False
        
                if pos1 is None:
                        # then a pontualforce will be added
                        if self.model.add_point_load(magnitude=magnitude, position=pos0, angle=angle):
                                self.update_display()
                                print(1)
                                return True
                        print(2)
                        return False

                # here pos1 is valid, then a load will be added

                if self.model.add_loads(pos_limits=(pos0, pos1), magnitude=magnitude):
                        self.update_display()
                        print(3)
                        return True
                print(4)
                return False
                

        def run(self):
                self.view.mainloop()
        



if __name__ == "__main__":
        app = Controller()
        app.run()