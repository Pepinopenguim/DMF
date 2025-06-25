import tkinter as tk
from tkinter import ttk

class Model():
        def __init__(self):
                self.length = 10
                self.delta = 0 # spaces between calc
                self.nodes = []
        
        def set_length(self, new_length):
                self.length = new_length
        
        def add_node(self, position):
                self.nodes.append(position)


class View(tk.Tk):
        def __init__(self, controller):
                super().__init__("View")
                self.controller = controller
                self.geometry("900x600")

                self.pack_propagate = False
                self.start_gui()
                
        
        def start_gui(self):
                self.maincanvas = tk.Canvas(self, background="blue")
                self.maincanvas.pack(side="left", padx=20, pady=20, fill="both", expand=True)

                self.styler = ttk.Style()
                
                self.styler.configure("TFrame", background = "red")
                self.button_frame = ttk.Frame(self, style="TFrame")
                self.button_frame.pack(side="left", fill="both", padx=5, pady=20)

                ttk.Label(self.button_frame, text="Length:", width=40).pack(pady=2, side="top")

                self.len_entry = ttk.Entry(self.button_frame, width = 40)
                self.len_entry.insert(0,string="10")
                self.len_entry.pack(pady=2)

                

                

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