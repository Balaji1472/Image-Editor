import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk, ImageOps

class ImageEditor:
    def __init__(self, root):
        self.root = root
        self.original_image = None  # Original image for reference
        self.display_image = None   # Image to display
        self.photo = None
        self.zoom_factor = 1.0
        self.crop_start = None
        self.crop_rect = None
        self.backup_image = None  # Backup of the original image
        self.image_id = None
        self.canvas_x = 0
        self.canvas_y = 0
        self.is_cropping = False  # To track if crop mode is active

        # Create frames for layout
        self.image_frame = tk.Frame(root, width=500, height=500, bg='gray')
        self.image_frame.pack(side="left", fill="both", expand=False)

        self.button_frame = tk.Frame(root)
        self.button_frame.pack(side="right", fill="y")

        # Canvas for image display
        self.canvas = tk.Canvas(self.image_frame, width=500, height=500, bg='white')
        self.canvas.pack(fill="both", expand=True)

        # Buttons
        self.upload_button = tk.Button(self.button_frame, text="Upload File", command=self.upload_file)
        self.upload_button.pack(pady=5)

        self.zoom_in_button = tk.Button(self.button_frame, text="Zoom In", command=self.zoom_in)
        self.zoom_in_button.pack(pady=5)

        self.zoom_out_button = tk.Button(self.button_frame, text="Zoom Out", command=self.zoom_out)
        self.zoom_out_button.pack(pady=5)

        self.crop_button = tk.Button(self.button_frame, text="Crop", command=self.start_crop)
        self.crop_button.pack(pady=5)

        self.rotate_button = tk.Button(self.button_frame, text="Rotate", command=self.rotate)
        self.rotate_button.pack(pady=5)

        self.grayscale_button = tk.Button(self.button_frame, text="Grayscale", command=self.grayscale)
        self.grayscale_button.pack(pady=5)

        self.flip_h_button = tk.Button(self.button_frame, text="Flip Horizontal", command=self.flip_horizontal)
        self.flip_h_button.pack(pady=5)

        self.flip_v_button = tk.Button(self.button_frame, text="Flip Vertical", command=self.flip_vertical)
        self.flip_v_button.pack(pady=5)

        self.save_button = tk.Button(self.button_frame, text="Save Image", command=self.save_image)
        self.save_button.pack(pady=5)

        self.cancel_button = tk.Button(self.button_frame, text="Cancel", command=self.cancel_changes)
        self.cancel_button.pack(pady=5)

        # Bind mouse events for moving the image
        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag_motion)

    def upload_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.gif;*.jpg;*.jpeg")])
        if file_path:
            try:
                self.original_image = Image.open(file_path)
                self.backup_image = self.original_image.copy()  # Backup the image
                self.zoom_factor = 1.0
                self.update_image()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")
        else:
            messagebox.showwarning("No File Selected", "No file was selected.")

    def update_image(self):
        if self.original_image:
            # Resize image based on the zoom factor
            width, height = int(self.original_image.width * self.zoom_factor), int(self.original_image.height * self.zoom_factor)
            self.display_image = self.original_image.resize((width, height), Image.LANCZOS)

            # Convert to PhotoImage to display in Tkinter
            self.photo = ImageTk.PhotoImage(self.display_image)
            self.draw_image()

    def draw_image(self):
        self.canvas.delete("all")
        if self.image_id:
            self.canvas.delete(self.image_id)
        # Center image in canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        image_width, image_height = self.photo.width(), self.photo.height()
        x = max(0, (canvas_width - image_width) / 2 + self.canvas_x)
        y = max(0, (canvas_height - image_height) / 2 + self.canvas_y)
        self.image_id = self.canvas.create_image(x, y, anchor="nw", image=self.photo)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def zoom_in(self):
        if self.original_image:
            self.zoom_factor *= 1.2
            self.update_image()

    def zoom_out(self):
        if self.original_image:
            self.zoom_factor /= 1.2
            self.update_image()

    def start_crop(self):
        """Enter cropping mode by allowing the user to select a region."""
        if self.original_image:
            self.is_cropping = True
            # Bind events for cropping
            self.canvas.bind("<ButtonPress-1>", self.on_crop_start)
            self.canvas.bind("<B1-Motion>", self.on_crop_drag)
            self.canvas.bind("<ButtonRelease-1>", self.on_crop_end)

    def on_crop_start(self, event):
        if self.is_cropping:
            # Start point of the cropping area
            self.crop_start = (event.x, event.y)
            # Create a rectangle for visual feedback of the crop area
            self.crop_rect = self.canvas.create_rectangle(self.crop_start[0], self.crop_start[1], self.crop_start[0], self.crop_start[1], outline="red")

    def on_crop_drag(self, event):
        if self.is_cropping and self.crop_rect:
            # Update the rectangle's size as the user drags the cursor
            self.canvas.coords(self.crop_rect, self.crop_start[0], self.crop_start[1], event.x, event.y)

    def on_crop_end(self, event):
        if self.is_cropping and self.crop_rect:
            # Get the final coordinates of the crop box
            x1, y1, x2, y2 = self.canvas.coords(self.crop_rect)

            # Convert canvas coordinates to image coordinates
            canvas_bbox = self.canvas.bbox(self.image_id)
            crop_x1 = max(0, (x1 - canvas_bbox[0]) / self.zoom_factor)
            crop_y1 = max(0, (y1 - canvas_bbox[1]) / self.zoom_factor)
            crop_x2 = max(0, (x2 - canvas_bbox[0]) / self.zoom_factor)
            crop_y2 = max(0, (y2 - canvas_bbox[1]) / self.zoom_factor)

            if abs(crop_x1 - crop_x2) > 0 and abs(crop_y1 - crop_y2) > 0:
                # Crop the image using the calculated crop box
                crop_box = (crop_x1, crop_y1, crop_x2, crop_y2)
                self.original_image = self.original_image.crop(crop_box)
                self.zoom_factor = 1.0  # Reset zoom after cropping
                self.update_image()

            # Clear the crop rectangle and exit crop mode
            self.canvas.delete(self.crop_rect)
            self.is_cropping = False

    def rotate(self):
        if self.original_image:
            angle = simpledialog.askfloat("Rotate", "Enter the rotation angle (degrees):", minvalue=0, maxvalue=360)
            if angle is not None:
                self.original_image = self.original_image.rotate(angle, expand=True)
                self.update_image()

    def grayscale(self):
        if self.original_image:
            self.original_image = ImageOps.grayscale(self.original_image)
            self.update_image()

    def flip_horizontal(self):
        if self.original_image:
            self.original_image = self.original_image.transpose(Image.FLIP_LEFT_RIGHT)
            self.update_image()

    def flip_vertical(self):
        if self.original_image:
            self.original_image = self.original_image.transpose(Image.FLIP_TOP_BOTTOM)
            self.update_image()

    def save_image(self):
        if self.original_image:
            save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")])
            if save_path:
                try:
                    self.original_image.save(save_path)
                    messagebox.showinfo("Image Saved", "Image has been saved successfully!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save image: {e}")
            else:
                messagebox.showwarning("Save Cancelled", "Image save was cancelled.")

    def cancel_changes(self):
        if self.backup_image:
            self.original_image = self.backup_image.copy()
            self.zoom_factor = 1.0
            self.update_image()

    def on_drag_start(self, event):
        self.drag_data = {"x": event.x, "y": event.y}

    def on_drag_motion(self, event):
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        self.canvas_x += dx
        self.canvas_y += dy
        self.draw_image()
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

# Create the main window
root = tk.Tk()
root.title("Aeroponics Images")

editor = ImageEditor(root)

# Start the Tkinter event loop
root.mainloop()
