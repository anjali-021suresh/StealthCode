import os
from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk, ImageFont, ImageDraw
import argparse
import sys
import subprocess
from tkinter import messagebox
import vpn_networking
from networking import Networking
from engine import Engine
import json
from directory_mointor import DirectoryMonitor


stored_message = ""  # Variable to store the input message
file_path = NONE
stealthCodeEngine = Engine()
networking = Networking()
networking.start_server()

# Directory to monitor
monitored_dir = "received_files"

# Ensure the directory exists
if not os.path.exists(monitored_dir):
    os.makedirs(monitored_dir, exist_ok=True) 

dir_monitor = DirectoryMonitor(monitored_dir, stealthCodeEngine.extract_data)
dir_monitor.start()

# for decrpting a file look for file addtions and if file is found get the file path and send it to decrpytion function must be in the seperate thread.


def get_arguments():
    parser = argparse.ArgumentParser(description="Get username and IP address from the command line.")
    
    # Add arguments for username and IP address
    parser.add_argument('-u', '--username', type=str, required=True, help="The name of the current user.")
    parser.add_argument('-ur', '--username-receiver', type=str, required=True, help="The username of the receiver.")
    parser.add_argument('-ip', '--ip_address', type=str, required=True, help="The IP address to connect to.")
    
    # Parse the arguments
    args = parser.parse_args()
    
    return args

args = get_arguments()
username = args.username # name of current use
receiver_username = args.username_receiver # receiver username
ip_address = args.ip_address # to get ip address of the receiver
public_key_receiver = vpn_networking.get_public_key(receiver_username)

def round_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
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



def custom_message_dialog(root, message):
    # Create a top-level window for the message box
    dialog = Toplevel(root)
    dialog.title("Message")
    dialog.geometry("400x200")
    dialog.configure(bg="#2b2b2b")
    
    # Create message label in the center
    message_label = Label(dialog, text=message, bg="#2b2b2b", fg="#ffffff", font=("Krona One", 12), justify=LEFT)
    message_label.pack(pady=30, padx=20)

    # Create the close button (square shape)
    def close_dialog():
        dialog.destroy()  # Close the message box when button is clicked

    # Square "Close" button
    close_button = Button(dialog, text="Close", command=close_dialog, bg="#3c3f41", fg="#ffffff", font=("Krona One", 12), width=10, height=2, bd=0)
    close_button.pack(pady=10)

    dialog.update()  # Ensure the window is fully rendered before grabbing the focus
    dialog.grab_set()  # Ensure that the dialog is modal
    dialog.transient(root)  # Make the dialog appear on top of the root window




class RoundedTextBox:
    def __init__(self, master, x, y, width, height, corner_radius, bg_color, fg_color, text_color, font):
        # Canvas for the background of the rounded text box
        self.canvas = Canvas(master, width=width, height=height, highlightthickness=0, bg=bg_color, bd=0)
        self.canvas.place(x=x, y=y)

        # Draw the rounded rectangle
        round_rectangle(self.canvas, 0, 0, width, height, corner_radius, fill=fg_color)

        # Text widget (no border, no highlight thickness)
        self.text = Text(
            master,
            bd=0,  # No border around the text box
            bg=fg_color,  # Background color of the text box
            fg=text_color,  # Text color
            font=font,  # Font of the text
            wrap=WORD,  # Wrap text to fit inside the box
            insertbackground=text_color,  # Cursor color
            highlightthickness=0,  # Remove highlight border
        )

        # Create a window inside the canvas to place the text widget
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
    # File selector with an appropriate initial directory and file type filter
        global file_path
        file_path = filedialog.askopenfilename(initialdir="~", title="Select image file")

        if file_path:
            try:
                # Open the image
                img = Image.open(file_path)
                
                # Resize the image to match the rectangle's dimensions
                img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
                
                # Convert the resized image into a format compatible with Tkinter
                self.img_tk = ImageTk.PhotoImage(img)
                
                # Display the image on the canvas
                self.canvas.create_image(self.width // 2, self.height // 2, image=self.img_tk, anchor="center")
                
                # Remove placeholder text
                self.canvas.delete(self.text_id)
                
                # Keep a reference to prevent garbage collection
                self.img_tk_reference = self.img_tk
            except Exception as e:
                # Show an error dialog if the image fails to load
                custom_message_dialog(root, "Error", f"Failed to load image: {e}")


# Load the image for the send button (e.g., an arrow image)
def load_send_button_image(canvas, x, y, size, command):
    try:
        # Load the image for the send button
        send_image = Image.open("assets/arrow.png")
        send_image = send_image.resize((size, size), Image.Resampling.LANCZOS)  # Resize image
        send_img_tk = ImageTk.PhotoImage(send_image)

        # Create an image object on the canvas and keep a reference
        image_id = canvas.create_image(x, y, image=send_img_tk)

        # Keep a reference to the image to prevent garbage collection
        canvas.image = send_img_tk

        # Bind the image to the click event, making it behave like a button
        canvas.tag_bind(image_id, "<Button-1>", lambda event: command())  # Trigger the command on click

    except Exception as e:
        custom_message_dialog(root, "Error", f"Failed to load image: {e}")

def logo_with_custom_font(master, text, font_path, size, bg_color="#2b2b2b", text_color="#ffffff"):
    try:
        # Create an image to render the text
        image_width, image_height = 600, 100
        image = Image.new("RGBA", (image_width, image_height), bg_color)
        draw = ImageDraw.Draw(image)

        # Load the custom font
        font = ImageFont.truetype(font_path, size)
    except OSError:
        # Fallback if the custom font cannot be loaded
        custom_message_dialog(master, "Font Error", "Custom font not found, using default font.")
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
    message = message_box.get("1.0", END).strip()  # Get the message from the textbox
    if not message:  # Check if the message is empty
        messagebox.showwarning("Empty Message", "Please enter a message before sending!")
        return

    global file_path
    #1. Encrpt and hide messages
    #2. Key Extange to json files and send it
    #3. Send file to the receiver
    output_path, crypto_transmission_key, crypto_tag = stealthCodeEngine.hide_data()
    key_data = {

        "transmission_key": crypto_transmission_key,
        "tag": crypto_tag
    }
    # File path where the JSON file will be saved
    file_path = "/tmp/key.json"

    # Write data to a JSON file
    with open(file_path, "w") as json_file:
        json.dump(key_data, json_file, indent=4)  # `indent=4` adds formatting for readability

    print(f"Data written to {file_path}")
    # sending key file
    networking.send_file(file_path, ip_address)

    # sending stego image
    networking.send_file(file_path, ip_address)

    stored_message = message  # Store the message in the variable
    message_box.delete("1.0", END)  # Clear the textbox
    custom_message_dialog(root, f"Message Sent:\n\n{stored_message}")  # Show the stored message



# Main window
root = Tk()
root.title("StealthCode")
root.geometry("1100x700")
root.configure(bg="#2b2b2b")



# Labels for textboxes
Label(root, text=f"Message to: {receiver_username}", bg="#2b2b2b", fg="#ffffff", font=("Krona One", 12)).place(x=50, y=140)
Label(root, text=f"Received from: {receiver_username}", bg="#2b2b2b", fg="#ffffff", font=("Krona One", 12)).place(x=50, y=400)

# Rounded text boxes
message_box = RoundedTextBox(root, 50, 170, 500, 150, 20, "#2b2b2b", "#3c3f41", "#ffffff", ("Krona One", 12))
received_box = RoundedTextBox(root, 50, 430, 500, 150, 20, "#2b2b2b", "#3c3f41", "#ffffff", ("Krona One", 12))

# Image placeholder
ImagePlaceholder(root, 600, 140, 450, 450, "#3c3f41")

# logo with Faster One font
logo_with_custom_font(root, "STEALTHCODE", r"assets/FasterOne-Regular.ttf", 48, "#2b2b2b")

# Canvas for the button
Label(root, text=f"Send Message", bg="#2b2b2b", fg="#ffffff", font=("Krona One", 14)).place(x=360, y=328)
button_canvas = Canvas(root, width=50, height=55, bg="#2b2b2b", highlightthickness=0)
button_canvas.place(x=500, y=325)

# Create the paper plane button
load_send_button_image(button_canvas, 24, 20, 39, send_message)  # Use button_canvas instead of canvas

if stealthCodeEngine.crypto.plaintext:
    received_box.text.insert(END, stealthCodeEngine.crypto.plaintext)

def on_close():
    """Handle the closing of the root window."""
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        # Terminate subprocesses if any are running
        for process in subprocess._active:
            try:
                process.terminate()
            except Exception as e:
                print(f"Error terminating process: {e}")

        # Destroy the root window
        root.destroy()
        vpn_networking.vpn_server_disconnection()
        print("[-] Stoping receiver listner")
        vpn_networking.stop_receiver()

        # stop dir monitor
        dir_monitor.stop()

        # Exit the program
        sys.exit()
    # also close the wireguard connection important





root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()
