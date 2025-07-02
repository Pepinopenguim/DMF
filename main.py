import tkinter as tk
import numpy as np
from tkinter import ttk

class Model():
        def __init__(self):
                self.length = 10
                self.total_node_num = 30
                self.nodes = [] # (position, support)
                self.point_loads = [] # (magnitude, position, angle)
                self.loads = [] #
                self.supports = []
                self.materials = {
                        "E":2e11, # Pa
                        "I":10e-6, # m^4
                }
        
        def set_length(self, new_length:float):
                
                try:
                        self.length = int(new_length)
                        return True
                except ValueError:
                        return False

        def set_total_node_num(self, new_node_num:int):
                try:
                        self.total_node_num = int(new_node_num)
                        return True
                except ValueError:
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
                        return True
                return False
        
        def add_loads(self, position_vector:tuple, magnitude:float):
                
                for pos in position_vector:
                        if not 0 <= pos <= self.length:
                                return False
                
                if not isinstance(magnitude, (int, float)):
                        return False

                pos0, pos1 = position_vector
                
                # invert values if order is wrong
                if pos0 > pos1:
                        pos0, pos1 = pos1, pos0

                self.loads.append(((pos0, pos1), magnitude))

                return True

class Pencil():
        def __init__(self, view, width = 3, fill = "blue", line_color = "black"):
                self.view = view
                self.line_width = width
                self.line_color = line_color
                self.fill = fill
        
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
                
                side = 2 * height / int(np.tan(np.pi / 3))

                p1 = (x0 + side / 2, y0 + height)
                p2 = (x0 - side / 2, y0 + height)

                self.view.maincanvas.create_line(p0, p1, p2, p0, width = self.line_width, fill=self.line_color)
                self.view.maincanvas.create_polygon(p0, p1, p2, p0, width = self.line_width, fill=self.fill)

                # draw little lines :)
                for i in np.linspace(p2[0], p1[0], 7)[1:-1]: # get 3 nums
                        i = int(i)
                        self.draw_angled_line(15, (i, y0 + height), 225)
        
        def draw_y(self, beam_position:float, height:float, canvas:tk.Canvas):
                beam_length = self.view.controller.model.length
                        
                x0 = self.view.canvas_padx + (self.view.canvas_w - 2*self.view.canvas_padx)*(beam_position / beam_length)
                y0 = self.view.beam_y

                p0 = (x0, y0)
                
                side = 2 * height // int(np.tan(np.pi / 3))

                p1 = (x0 + side // 2, y0 + height)
                p2 = (x0 - side // 2, y0 + height)

                self.view.maincanvas.create_line(p0, p1, p2, p0, width = self.line_width, fill=self.line_color)
                self.view.maincanvas.create_polygon(p0, p1, p2, p0, width = self.line_width, fill=self.fill)

                # draw little circles :)
                #self.draw_angled_line(abs(int(p2[0] - p1[0])), (p2[0], y0 + 1.2 * height))
                self.draw_circles_along_line(
                        start_pos=(p2[0], y0 + 1.2 * height),
                        end_pos=(p1[0], y0 + 1.2 * height),
                        num_circles=6,
                        width=self.line_width//1.5,
                        fill=self.fill
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
                self.view.maincanvas.create_line(*polygon_points, width = self.line_width, fill=self.line_color)
                self.view.maincanvas.create_polygon(*polygon_points, width = self.line_width, fill=self.fill)

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
                
                        self.view.maincanvas.create_line(*polygon_points, width = self.line_width, fill=self.line_color)
                        self.view.maincanvas.create_polygon(*polygon_points, width = self.line_width, fill=self.fill)

                        self.draw_circles_along_line(
                                start_pos=(x0 - 2 * height/ratio, y0 + height),
                                end_pos=(x0 - 2 * height/ratio, y0 - height),
                                num_circles=6,
                                width=self.line_width//1.5,
                                fill=self.fill 
                        )
                elif abs(beam_position - beam_length) < episilon: # draw to the right
                        polygon_points = [p0, (x0, y0 - height), (x0 + height/ratio, y0 - height), (x0 + height/ratio, y0 + height), (x0, y0 + height), p0]
                        
                        self.view.maincanvas.create_line(*polygon_points, width = self.line_width, fill=self.line_color)
                        self.view.maincanvas.create_polygon(*polygon_points, width = self.line_width, fill=self.fill)

                        self.draw_circles_along_line(
                                start_pos=(x0 + 2 * height/ratio, y0 + height),
                                end_pos=(x0 + 2 * height/ratio, y0 - height),
                                num_circles=6,
                                width=self.line_width//1.5,
                                fill=self.fill 
                        )

                else:
                        polygon_points = [(x0 - height/(2*ratio), y0 - height), (x0 - height/(2*ratio), y0 + height), (x0 + height/(2*ratio), y0 + height), (x0 + height/(2*ratio), y0 - height)]
                        draw_lines = False 
                








                


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
                        command=None # temp
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

                ttk.Button(
                        self.control_frame,
                        text="Add Support",
                        command=lambda :self.controller.add_support(
                                position=self.support_pos_strgvar.get(),
                                support_type=self.Var1.get()*"x" + self.Var2.get()*"y" + self.Var3.get()*"z"
                        )
                ).pack(pady=5)

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
                self.from_strgvar = tk.StringVar(value="")
                from_entry = ttk.Entry(line1, textvariable=self.from_strgvar, width = 6)
                from_entry.pack(side="left")
                self.to_strgvar = tk.StringVar(value="")
                to_entry = ttk.Entry(line1, textvariable=self.to_strgvar, width = 6)
                to_entry.pack(side="left")
                
                line2.pack(pady=lines_pady)
                ttk.Label(line2, text="Magnitude", font=("Arial", 10, "bold"), width=10).pack(side="left", padx=2)
                self.f2_strgvar = tk.StringVar(value="")
                f2_entry = ttk.Entry(line2, textvariable=self.f2_strgvar, width = 12)
                f2_entry.pack()

                line3.pack(pady=lines_pady)
                ttk.Label(line3, text="Angle", font=("Arial", 10, "bold"), width=10).pack(side="left", padx=2)
                self.f3_strgvar = tk.StringVar(value="")
                f3_entry = ttk.Entry(line3, textvariable=self.f3_strgvar, width = 12)
                f3_entry.pack()
        
        def solve_gui(self):
                self.create_separator(frame = self.control_frame, text="")

                solve_button = ttk.Button(self.control_frame, text="Solve", command=None)
                solve_button.pack(pady=2)

        


        def draw_beam(self):
                self.maincanvas.delete("all")
                self.canvas_w, self.canvas_h = self.maincanvas.winfo_width(), self.maincanvas.winfo_height()
                

                self.beam_y = self.canvas_h // 2

                self.canvas_padx = 50

                self.maincanvas.create_line(self.canvas_padx, self.beam_y, self.canvas_w - self.canvas_padx, self.beam_y, width = 3, fill="black")

                # draw supports
                for support_pos, support_type in self.controller.model.supports:
                        match support_type:
                                case "xy":
                                        self.pencil.draw_xy(support_pos, self.canvas_h//22, canvas=self.maincanvas)
                                case "y":
                                        self.pencil.draw_y(support_pos, self.canvas_h//22, canvas=self.maincanvas)
                                case "xyz":
                                        self.pencil.draw_xyz(support_pos, self.canvas_h//22, canvas=self.maincanvas)
                                case "xz":
                                        self.pencil.draw_xz(support_pos, self.canvas_h//22, canvas=self.maincanvas)

                


class Controller():
        def __init__(self):
                self.model = Model()
                self.view = View(self)

                self.view.bind("<Configure>", self.on_resize)
        
        def update_display(self):
                self.view.draw_beam()

        def add_support(self, position, support_type):
                # checks if position argument is valid
                try:
                        position = float(position)
                except ValueError:
                        return False
                # checks if support_type is not empty
                if support_type == "":
                        return False
                
                print(position, support_type)
                if self.model.add_support(position, support_type):
                        self.update_display()
                        return True
                return False

        def set_length(self, new_length):
                self.model.set_length()

        def run(self):
                self.view.mainloop()
        
        def on_resize(self, event):
                self.update_display()



if __name__ == "__main__":
        app = Controller()
        app.run()