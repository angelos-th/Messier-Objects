import json
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from PIL import Image, ImageTk


class MessierViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Messier Object Viewer")

        # Load data
        try:
            with open("messier.json", "r") as f:
                self.data = json.load(f)
            self.messier_objects = self.data["data"]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load messier.json: {e}")
            self.root.destroy()
            return

        # Get all unique constellations
        self.constellations = sorted(set(
            obj["constellation"] for obj in self.messier_objects.values()
        ))

        # Create UI
        self.create_widgets()
        self.image_url_map = {}  # Store URL for each tree row




    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left frame - constellation selection
        left_frame = ttk.LabelFrame(main_frame, text="Select Constellations", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Create scrollable canvas for constellations
        const_canvas = tk.Canvas(left_frame, width=150)  # Fixed width
        const_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=const_canvas.yview)
        const_canvas.configure(yscrollcommand=const_scrollbar.set)

        const_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        const_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Frame inside canvas to hold checkboxes
        const_frame = ttk.Frame(const_canvas)
        const_canvas.create_window((0, 0), window=const_frame, anchor="nw")

        # Checkboxes for constellations
        self.constellation_vars = {}
        for const in self.constellations:
            var = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(
                const_frame,
                text=const,
                variable=var,
                onvalue=True,
                offvalue=False,
                wraplength=120,  # Wrap long constellation names
                anchor=tk.W,
                justify=tk.LEFT,
            )
            cb.pack(anchor=tk.W, fill=tk.X)
            self.constellation_vars[const] = var

        # Update scrollregion when frame resizes
        const_frame.bind("<Configure>", lambda e: const_canvas.configure(scrollregion=const_canvas.bbox("all")))

        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            const_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        const_canvas.bind("<MouseWheel>", _on_mousewheel)
        const_frame.bind("<MouseWheel>", _on_mousewheel)

        # Select all / Deselect all buttons
        btn_frame = ttk.Frame(const_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Select All", command=self.select_all).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(btn_frame, text="Deselect All", command=self.deselect_all).pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Right frame - results
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Sorting controls
        sort_frame = ttk.Frame(right_frame)
        sort_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(sort_frame, text="Sort by:").pack(side=tk.LEFT)
        sort_options = ["Messier Number", "Magnitude", "Difficulty", "Name", "Type"]
        self.sort_menu = ttk.Combobox(sort_frame, values=sort_options, state="readonly", width=15)
        self.sort_menu.set("Messier Number")
        self.sort_menu.pack(side=tk.LEFT, padx=5)
        self.sort_menu.bind("<<ComboboxSelected>>", lambda e: self.filter_objects())

        ttk.Label(sort_frame, text="Order:").pack(side=tk.LEFT)
        order_options = ["Ascending", "Descending"]
        self.order_menu = ttk.Combobox(sort_frame, values=order_options, state="readonly", width=10)
        self.order_menu.set("Ascending")
        self.order_menu.pack(side=tk.LEFT, padx=5)
        self.order_menu.bind("<<ComboboxSelected>>", lambda e: self.filter_objects())

        # Filter button
        ttk.Button(right_frame, text="Show Objects", command=self.filter_objects).pack(fill=tk.X, pady=(0, 5))

        # Treeview for results
        self.tree = ttk.Treeview(right_frame, columns=("Number", "Name", "Type", "Mag", "Size", "Difficulty", "Constellation", "Image"), show="headings")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Configure columns
        columns = [
            ("Number", "Messier #", 80, tk.CENTER),
            ("Name", "Name", 150, tk.W),
            ("Type", "Type", 120, tk.W),
            ("Mag", "Magnitude", 80, tk.CENTER),
            ("Size", "Size", 100, tk.CENTER),
            ("Difficulty", "Difficulty", 100, tk.CENTER),
            ("Constellation", "Constellation", 120, tk.W),
            ("Image", "Image Link", 150, tk.W)
        ]

        for col_id, text, width, anchor in columns:
            self.tree.heading(col_id, text=text)
            self.tree.column(col_id, width=width, anchor=anchor)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Status bar
        self.status = ttk.Label(self.root, text="Select constellations and click 'Show Objects'", relief=tk.SUNKEN)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        # Make column headers clickable for sorting
        for col_id, text, _, _ in columns:
            self.tree.heading(col_id, command=lambda c=col_id: self.sort_column(c))
        self.tree.bind("<Double-1>", self.open_image)

    def select_all(self):
        for var in self.constellation_vars.values():
            var.set(True)

    def deselect_all(self):
        for var in self.constellation_vars.values():
            var.set(False)

    def sort_column(self, col):
        current_order = self.order_menu.get()
        new_order = "Descending" if current_order == "Ascending" else "Ascending"
        self.order_menu.set(new_order)

        col_names = {
            "Number": "Messier Number",
            "Name": "Name",
            "Type": "Type",
            "Mag": "Magnitude",
            "Size": "Size",
            "Difficulty": "Difficulty",
            "Constellation": "Constellation"
        }
        self.sort_menu.set(col_names.get(col, "Messier Number"))
        self.filter_objects()

    def filter_objects(self):
        # Get selected constellations
        selected = [const for const, var in self.constellation_vars.items() if var.get()]

        if not selected:
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.status.config(text="No constellations selected - show all objects")
            filtered = list(self.messier_objects.items())
        else:
            filtered = [
                (key, obj) for key, obj in self.messier_objects.items()
                if obj["constellation"] in selected
            ]
            self.status.config(text=f"Showing {len(filtered)} objects from {len(selected)} constellations")

        # Sort
        sort_by = self.sort_menu.get()
        order = self.order_menu.get()

        sort_keys = {
            "Messier Number": lambda x: int(x[0][1:]),
            "Name": lambda x: x[1]["name"].lower(),
            "Type": lambda x: x[1]["type"].lower(),
            "Magnitude": lambda x: float(x[1]["magnitude"]) if x[1]["magnitude"] is not None else 99,
            "Difficulty": lambda x: {
                "Easy": 0, "Moderate": 1, "Difficult": 2, "Very Difficult": 3, "": 4
            }.get(x[1]["viewingDifficulty"], 4),
            "Constellation": lambda x: x[1]["constellation"].lower()
        }

        key_func = sort_keys.get(sort_by, sort_keys["Messier Number"])
        filtered.sort(key=key_func)

        if order == "Descending":
            filtered.reverse()

        # Clear and populate tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Clear the URL map
        self.image_url_map.clear()

        for key, obj in filtered:
            url = obj.get("image", "")
            item_id = self.tree.insert("", tk.END, values=(
                key,
                obj["name"],
                obj["type"],
                obj.get("magnitude", ""),
                obj.get("size", ""),
                obj.get("viewingDifficulty", ""),
                obj["constellation"],
                url 
            ))
            self.image_url_map[item_id] = url  # Store URL
            
    def open_image(self, event):
        selected = self.tree.selection()
        if selected:
            item = selected[0]
            url = self.image_url_map.get(item)
            if url:
                webbrowser.open_new(url)

if __name__ == "__main__":
    root = tk.Tk()
    app = MessierViewer(root)
    root.geometry("1100x600")
    img = Image.open('icon.png')
    img = img.resize((16, 16), Image.LANCZOS)
    root.iconphoto(False, ImageTk.PhotoImage(img))
    root.mainloop()