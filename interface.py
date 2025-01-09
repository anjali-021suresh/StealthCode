from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageFont, ImageDraw

username = "User123"  # Predefined username
stored_message = ""  # Variable to store the input message

def round_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    #Draw a rounded rectangle on the canvas
    points = [
        (x1 + radius, y1), (x1 + radius, y1),
        (x2 - radius, y1), (x2 - radius, y1),
        (x2, y1), (x2, y1 + radius),
        (x2, y1 + radius), (x2, y2 - radius),
        (x2, y2 - radius), (x2, y2),
        (x2 - radius, y2), (x2 - radius, y2),
        (x1 + radius, y2), (x1 + radius, y2),
        (x1, y2), (x1, y2 - radius),
        (x1, y2 - radius), (x1, y1 + radius),
        (x1, y1 + radius), (x1, y1),
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)

class RoundedTextBox:
    def __init__(self, master, x, y, width, height, corner_radius, bg_color, fg_color, text_color, font):
        self.canvas = Canvas(master, width=width, height=height, highlightthickness=0, bg=bg_color)
        self.canvas.place(x=x, y=y)
        round_rectangle(self.canvas, 0, 0, width, height, corner_radius, fill=fg_color)
        self.text = Text(
            master,
            bd=0,
            bg=fg_color,
            fg=text_color,
            font=font,
            wrap=WORD,
            insertbackground=text_color,
        )
        self.canvas.create_window(width // 2, height // 2, window=self.text, width=width - 20, height=height - 20)

class ImagePlaceholder:
    def __init__(self, master, x, y, width, height, bg_color):
        self.canvas = Canvas(master, width=width, height=height, bg=bg_color, highlightthickness=0)
        self.canvas.place(x=x, y=y)
        self.width = width
        self.height = height
        self.placeholder_text = "Click to Add Image"
        self.text_id = self.canvas.create_text(width // 2, height // 2, text=self.placeholder_text, fill="gray")
        self.canvas.bind("<Button-1>", self.add_image)

    def add_image(self, event):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if file_path:
            img = Image.open(file_path)
            img.thumbnail((self.width, self.height))  # Maintain aspect ratio
            self.img_tk = ImageTk.PhotoImage(img)
            self.canvas.create_image(self.width // 2, self.height // 2, image=self.img_tk, anchor="center")
            self.canvas.delete(self.text_id)  # Remove placeholder text

def create_paper_plane_button(canvas, x, y, size, command):
    """Create a circular button with a paper plane icon facing right."""
    # Draw the circular button
    button = canvas.create_oval(x, y, x + size, y + size, fill="#3c3f41", outline="")

    # Draw the paper plane icon
    # Main body (triangle facing right)
    plane_body = [
        (x + size * 0.3, y + size * 0.3),  # Top left
        (x + size * 0.3, y + size * 0.7),  # Bottom left
        (x + size * 0.7, y + size * 0.5),  # Tip (right point)
    ]
    canvas.create_polygon(plane_body, fill="#ffffff", outline="#ffffff")

    # Tail fin (smaller triangle on the left side)
    tail_fin = [
        (x + size * 0.3, y + size * 0.5),  # Middle of the base
        (x + size * 0.4, y + size * 0.4),  # Top inner point
        (x + size * 0.4, y + size * 0.6),  # Bottom inner point
    ]
    canvas.create_polygon(tail_fin, fill="#ffffff", outline="#ffffff")

    # Bind click event to the button
    canvas.tag_bind(button, "<Button-1>", lambda e: command())
    canvas.tag_bind("all", "<Button-1>", lambda e: command())  # Include all shapes

def logo_with_custom_font(master, text, font_path, size, bg_color="#2b2b2b", text_color="#ffffff"):
    """Render logo text with a custom font using Pillow and display it in Tkinter."""
    try:
        # Create an image to render the text
        image_width, image_height = 600, 100
        image = Image.new("RGBA", (image_width, image_height), bg_color)
        draw = ImageDraw.Draw(image)

        # Load the custom font
        font = ImageFont.truetype(font_path, size)
    except OSError:
        # Fallback if the custom font cannot be loaded
        messagebox.showwarning("Font Error", "Custom font not found, using default font.")
        font = ImageFont.load_default()

    # Center the text within the image
    text_bbox = draw.textbbox((0, 0), text, font=font)  # Get the bounding box of the text
    text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
    text_x = (image_width - text_width) // 2
    text_y = (image_height - text_height) // 2

    # Draw the text onto the image
    draw.text((text_x, text_y), text, font=font, fill=text_color)

    # Convert the image to a format usable by Tkinter
    logo_img = ImageTk.PhotoImage(image)
    logo_label = Label(master, image=logo_img, bg=bg_color)
    logo_label.image = logo_img  # Keep a reference to avoid garbage collection
    logo_label.place(relx=0.5, rely=0.1, anchor="center")

def send_message():
    global stored_message
    message = message_box.text.get("1.0", END).strip()  # Get the message from the textbox
    if message:
        stored_message = message  # Store the message in the variable
        message_box.text.delete("1.0", END)  # Clear the textbox
        messagebox.showinfo("Stored Message", f"Message Sent:\n\n{stored_message}")  # Show the stored message


# Main window
root = Tk()
root.title("StealthCode")
root.geometry("1100x700")
root.configure(bg="#2b2b2b")

# Labels for textboxes
Label(root, text=f"Message to: {username}", bg="#2b2b2b", fg="#ffffff", font=("Helvetica", 12)).place(x=50, y=140)
Label(root, text=f"Received from: {username}", bg="#2b2b2b", fg="#ffffff", font=("Helvetica", 12)).place(x=50, y=400)

# Rounded text boxes
message_box = RoundedTextBox(root, 50, 170, 500, 150, 20, "#2b2b2b", "#3c3f41", "#ffffff", ("Helvetica", 12))
received_box = RoundedTextBox(root, 50, 430, 500, 150, 20, "#2b2b2b", "#3c3f41", "#ffffff", ("Helvetica", 12))

# Image placeholder
ImagePlaceholder(root, 600, 140, 450, 450, "#3c3f41")

# logo with Faster One font
logo_with_custom_font(root, "STEALTHCODE", r"assets/FasterOne-Regular.ttf", 48, "#2b2b2b")

# Canvas for the button
Label(root, text=f"Send Message", bg="#2b2b2b", fg="#ffffff", font=("Helvetica", 14)).place(x=360, y=333)
button_canvas = Canvas(root,width=50, height=55, bg="#2b2b2b", highlightthickness=0)
button_canvas.place(x=500, y=325) 

# Create the paper plane button
create_paper_plane_button(button_canvas, x=0, y=0, size=50, command=send_message)

root.mainloop()
