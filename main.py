import tkinter as tk
from tkinter import ttk

class Model():
        def __init__(self):
                self.length = 10
                self.nodes = [] # (position, support)
                self.point_loads = [] # (magnitude, position, angle)
                self.loads = [] #
                self.supports = []
                self.materials = {
                        "E":2e11, # Pa
                        "I":10e-6, # m^4
                }
        
        def set_length(self, new_length):
                
                try:
                        self.length = new_length
                        return True
                except ValueError:
                        return False
        
        def add_support(self, position:float, support_type:str):

                # check if position inside beam
                if 0 <= position <= self.length:
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

                


class View(tk.Tk):
        def __init__(self, controller):
                super().__init__("View")
                self.controller = controller
                
                self.geometry("1000x700")

                self.pack_propagate = False
                self.start_gui()
                self.setup_styler()

        def setup_styler(self):
                self.styler = ttk.Style()
                self.styler.configure("TFrame", background="#f0f0f0")
                self.styler.configure("TLabel", padding=5, background="#f0f0f0")
                self.styler.configure("TButton", padding=5)   
        
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

                # Beam properties
                (ttk.Label(
                        self.control_frame,
                        text="Beam Properties",
                        font=("Arial", 10, "bold")
                        )
                .pack(pady=(0, 10))
                )
                

                

class Controller():
        def __init__(self):
                self.model = Model()
                self.view = View(self)
        
        def set_length(self, new_length):
                self.model.set_length()

        def run(self):
                self.view.mainloop()



if __name__ == "__main__":
        app = Controller()
        app.run()