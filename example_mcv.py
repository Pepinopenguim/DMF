import tkinter as tk
from tkinter import ttk

class Model:
    def __init__(self):
        self.length = 10.0  # meters
        self.nodes = []
        self.supports = []  # List of (position, type)
        self.loads = []     # List of (position, magnitude)
        self.materials = {
            'YoungModulus': 2.1e11,  # Pa (steel)
            'Inertia': 8.33e-6       # m^4 (rectangular beam)
        }
    
    def set_length(self, new_length):
        try:
            self.length = float(new_length)
            return True
        except ValueError:
            return False
    
    def add_support(self, position, support_type):
        """Adds support at normalized position (0-1)"""
        if 0 <= position <= 1:
            self.supports.append((position, support_type))
            return True
        return False
    
    def add_point_load(self, position, magnitude):
        """Adds point load at normalized position (0-1)"""
        if 0 <= position <= 1:
            self.loads.append((position, magnitude))
            return True
        return False
    
    def calculate_nodes(self, divisions):
        """Generates node positions based on divisions"""
        self.nodes = [i * self.length / divisions for i in range(divisions + 1)]
        return self.nodes

class View(tk.Tk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.title("Finite Difference Beam Solver")
        self.geometry("1000x700")
        
        self.create_widgets()
        self.setup_style()
    
    def setup_style(self):
        self.styler = ttk.Style()
        self.styler.configure("TFrame", background="#f0f0f0")
        self.styler.configure("TButton", padding=5)
        self.styler.configure("TLabel", padding=5, background="#f0f0f0")
    
    def create_widgets(self):
        # Main layout containers
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Canvas for beam visualization
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.pack(side="left", fill="both", expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", bd=2, relief="groove")
        self.canvas.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Control panel
        self.control_frame = ttk.Frame(self.main_frame, width=250)
        self.control_frame.pack(side="right", fill="y", padx=5, pady=5)
        
        # Beam properties
        ttk.Label(self.control_frame, text="Beam Properties", font=('Arial', 10, 'bold')).pack(pady=(0, 10))
        
        self.length_var = tk.StringVar(value="10.0")
        length_entry = ttk.Entry(self.control_frame, textvariable=self.length_var)
        length_entry.pack(fill="x", padx=5, pady=2)
        ttk.Button(self.control_frame, text="Set Length", 
                  command=lambda: self.controller.update_length(self.length_var.get())).pack(pady=5)
        
        # Support controls
        ttk.Separator(self.control_frame).pack(fill="x", pady=10)
        ttk.Label(self.control_frame, text="Supports", font=('Arial', 10, 'bold')).pack()
        
        self.support_pos_var = tk.StringVar(value="0.5")
        ttk.Entry(self.control_frame, textvariable=self.support_pos_var).pack(fill="x", padx=5, pady=2)
        
        support_types = ["Fixed", "Pinned", "Roller"]
        self.support_type_var = tk.StringVar(value="Pinned")
        ttk.Combobox(self.control_frame, textvariable=self.support_type_var, values=support_types).pack(fill="x", padx=5, pady=2)
        
        ttk.Button(self.control_frame, text="Add Support", 
                  command=lambda: self.controller.add_support(
                      float(self.support_pos_var.get()),
                      self.support_type_var.get())).pack(pady=5)
        
        # Load controls
        ttk.Separator(self.control_frame).pack(fill="x", pady=10)
        ttk.Label(self.control_frame, text="Point Loads", font=('Arial', 10, 'bold')).pack()
        
        self.load_pos_var = tk.StringVar(value="0.5")
        ttk.Entry(self.control_frame, textvariable=self.load_pos_var).pack(fill="x", padx=5, pady=2)
        
        self.load_mag_var = tk.StringVar(value="1000")
        ttk.Entry(self.control_frame, textvariable=self.load_mag_var).pack(fill="x", padx=5, pady=2)
        
        ttk.Button(self.control_frame, text="Add Point Load", 
                  command=lambda: self.controller.add_point_load(
                      float(self.load_pos_var.get()),
                      float(self.load_mag_var.get()))).pack(pady=5)
        
        # Solve button
        ttk.Separator(self.control_frame).pack(fill="x", pady=10)
        ttk.Button(self.control_frame, text="Solve", command=self.controller.solve).pack(pady=10)
    
    def draw_beam(self):
        self.canvas.delete("all")
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        # Draw beam
        beam_y = height // 2
        self.canvas.create_line(50, beam_y, width - 50, beam_y, width=3, fill="black")
        
        # Draw supports
        for pos, sup_type in self.controller.model.supports:
            x = 50 + (width - 100) * pos
            if sup_type == "Fixed":
                self.draw_fixed_support(x, beam_y)
            elif sup_type == "Pinned":
                self.draw_pinned_support(x, beam_y)
            else:  # Roller
                self.draw_roller_support(x, beam_y)
        
        # Draw loads
        for pos, magnitude in self.controller.model.loads:
            x = 50 + (width - 100) * pos
            self.draw_point_load(x, beam_y, magnitude)
    
    def draw_fixed_support(self, x, beam_y):
        size = 20
        self.canvas.create_rectangle(x - size, beam_y, x + size, beam_y + size, fill="gray")
        self.canvas.create_line(x - size, beam_y, x + size, beam_y, width=3)
    
    def draw_pinned_support(self, x, beam_y):
        size = 15
        self.canvas.create_polygon(
            x - size, beam_y,
            x + size, beam_y,
            x, beam_y + size,
            fill="gray")
        self.canvas.create_line(x - size, beam_y, x + size, beam_y, width=3)
    
    def draw_roller_support(self, x, beam_y):
        size = 15
        radius = 5
        self.canvas.create_rectangle(
            x - size, beam_y,
            x + size, beam_y + radius * 2,
            fill="gray")
        self.canvas.create_line(x - size, beam_y, x + size, beam_y, width=3)
        for i in range(-1, 2):
            self.canvas.create_oval(
                x + i * radius * 2 - radius,
                beam_y + radius * 2,
                x + i * radius * 2 + radius,
                beam_y + radius * 4,
                fill="gray")
    
    def draw_point_load(self, x, beam_y, magnitude):
        size = min(50, abs(magnitude) / 50)
        direction = -1 if magnitude > 0 else 1
        self.canvas.create_line(x, beam_y, x, beam_y + direction * size, width=2, arrow=tk.LAST)
        self.canvas.create_text(x, beam_y + direction * (size + 15), text=f"{magnitude} N")

class Controller:
    def __init__(self):
        self.model = Model()
        self.view = View(self)
        self.view.bind("<Configure>", self.on_resize)
        self.update_display()
    
    def update_length(self, new_length):
        if self.model.set_length(new_length):
            self.update_display()
            return True
        return False
    
    def add_support(self, position, support_type):
        if self.model.add_support(position, support_type):
            self.update_display()
            return True
        return False
    
    def add_point_load(self, position, magnitude):
        if self.model.add_point_load(position, magnitude):
            self.update_display()
            return True
        return False
    
    def solve(self):
        # Placeholder for finite difference solution
        print("Solving...")
        nodes = self.model.calculate_nodes(10)
        print(f"Nodes: {nodes}")
        print(f"Supports: {self.model.supports}")
        print(f"Loads: {self.model.loads}")
        # Here you would implement the actual finite difference solver
    
    def update_display(self):
        self.view.draw_beam()
    
    def on_resize(self, event):
        self.update_display()
    
    def run(self):
        self.view.mainloop()

if __name__ == "__main__":
    app = Controller()
    app.run()