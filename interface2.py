import os
from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageFont, ImageDraw
import subprocess
import sys
import json
import vpn_networking
from networking import Networking
from engine import Engine
from directory_mointor import DirectoryMonitor
import threading


file_path = None

class StealthCodeApp:
    def __init__(self, username, receiver_username, ip_address):
        self.username = username
        self.receiver_username = receiver_username
        self.ip_address = ip_address
        self.file_path = None


        # Initialize core components
        self.stealthCodeEngine = Engine()
        self.networking = Networking()
    

        # Start the networking server in a separate thread
        self.start_networking_thread()

        # Directory monitoring
        self.monitored_dir = "received_files"
        if not os.path.exists(self.monitored_dir):
            os.makedirs(self.monitored_dir, exist_ok=True)
        self.dir_monitor = DirectoryMonitor(self.monitored_dir, self.stealthCodeEngine.extract_data)
        self.dir_monitor.start()

        # Initialize Tkinter root window
        self.root = Tk()
        self.root.title("StealthCode")
        self.root.geometry("1100x700")
        self.root.configure(bg="#2b2b2b")

        # Set up the application UI
        self.setup_ui()


    def start_networking_thread(self):
        """Start the networking server in a separate thread."""
        networking_thread = threading.Thread(target=self.networking.start_server)
        networking_thread.daemon = True  # Daemonize the thread to ensure it closes when the program exits
        networking_thread.start()


    def setup_ui(self):


        self.message_box = RoundedTextBox(self.root, 50, 170, 500, 150, 20, "#2b2b2b", "#3c3f41", "#ffffff", ("Krona One", 12))
        self.received_box = RoundedTextBox(self.root, 50, 430, 500, 150, 20, "#2b2b2b", "#3c3f41", "#ffffff", ("Krona One", 12))

        ImagePlaceholder(self.root, 600, 140, 450, 450, "#3c3f41")

        # Set up the custom logo
        logo_with_custom_font(self.root, "STEALTHCODE", "assets/FasterOne-Regular.ttf", 48, "#2b2b2b")

        Label(self.root, text=f"Message to user: {self.receiver_username}", bg="#2b2b2b", fg="#ffffff", font=("Krona One", 14)).place(x=55, y=140)
        Label(self.root, text=f"Message from user: {self.receiver_username}", bg="#2b2b2b", fg="#ffffff", font=("Krona One", 14)).place(x=55, y=400)


        # Set up the send button
        button_canvas = Canvas(self.root, width=60, height=60, bg="#2b2b2b", highlightthickness=0)
        button_canvas.place(x=500, y=325)  # Adjust position as needed
        self.load_send_button_image(button_canvas, 30, 30, 50, self.send_message)  # Center in canvas



        # Bind the close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        Label(self.root, text=f"Send Message", bg="#2b2b2b", fg="#ffffff", font=("Krona One", 14)).place(x=366, y=340)



    def load_send_button_image(self, canvas, x, y, size, command=None):
        try:
            # Load and resize the button image
            img = Image.open("assets/arrow.png").resize((size, size), Image.Resampling.LANCZOS)
            self.send_button_image = ImageTk.PhotoImage(img)  # Store reference to prevent garbage collection

            # Place the image on the canvas
            image_id = canvas.create_image(x, y, image=self.send_button_image, anchor="center")

            # Bind the button click event
            if command:
                canvas.tag_bind(image_id, "<Button-1>", lambda e: command())

        except Exception as e:
            print(f"Error loading send button image: {e}")

    def send_message(self):
        message = self.message_box.get_message().strip()
        if not message:
            messagebox.showwarning("Empty Message", "Please enter a message before sending!")
            return
        
        receiver_public_key = vpn_networking.get_public_key(self.receiver_username)

        output_path, crypto_transmission_key, crypto_tag = self.stealthCodeEngine.hide_data(message, file_path, receiver_public_key)
        key_data = {
            "transmission_key": crypto_transmission_key,
            "tag": crypto_tag
        }

        file_path = "/tmp/key.json"
        with open(file_path, "w") as json_file:
            json.dump(key_data, json_file, indent=4)
        
        print(f"Data written to {file_path}")
        self.networking.send_file(file_path, self.ip_address)
        self.networking.send_file(output_path, self.ip_address)

        self.message_box.clear_message()
        custom_message_dialog(self.root, f"Message Sent:\n\n{message}")

    def on_close(self):
        """Handle the closing of the root window."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            # Terminate subprocesses if any are running
            for process in subprocess._active:
                try:
                    process.terminate()
                except Exception as e:
                    print(f"Error terminating process: {e}")

            # Destroy the root window
            self.root.destroy()
            vpn_networking.vpn_server_disconnection()
            print("[-] Stopping receiver listener")
            
            # to stop the listeing sever
            self.networking.stop_server()

            # Stop directory monitor
            self.dir_monitor.stop()

            # Exit the program
            sys.exit()

    def run(self):
        self.root.mainloop()


class RoundedTextBox:
    def __init__(self, master, x, y, width, height, corner_radius, bg_color, fg_color, text_color, font):
        self.canvas = Canvas(master, width=width, height=height, highlightthickness=0, bg=bg_color, bd=0)
        self.canvas.place(x=x, y=y)
        round_rectangle(self.canvas, 0, 0, width, height, corner_radius, fill=fg_color)

        self.text = Text(
            master,
            bd=0,  # No border around the text box
            bg=fg_color,
            fg=text_color,
            font=font,
            wrap=WORD,
            insertbackground=text_color,
            highlightthickness=0,
        )

        self.canvas.create_window(width // 2, height // 2, window=self.text, width=width - 20, height=height - 20)

    def get_message(self):
        return self.text.get("1.0", END)

    def clear_message(self):
        self.text.delete("1.0", END)


class ImagePlaceholder:
    def __init__(self, master, x, y, width, height, bg_color):
        self.canvas = Canvas(master, width=width, height=height, bg=bg_color, highlightthickness=0)
        self.canvas.place(x=x, y=y)
        self.width = width
        self.height = height
        self.placeholder_text = "Click to Add Image"
        self.text_id = self.canvas.create_text(width // 2, height // 2, text=self.placeholder_text, fill="gray")
        self.canvas.bind("<Button-1>", self.add_image)
        self.master = master

    def add_image(self, event):

        file_path = filedialog.askopenfilename(initialdir="~", title="Select image file")
        if file_path:
            try:
                
                file_path = file_path
                img = Image.open(file_path)
                img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
                self.canvas.create_image(self.width // 2, self.height // 2, image=img_tk, anchor="center")
                self.img_tk_reference = img_tk
            except Exception as e:
                custom_message_dialog(self.master, "Error", f"Failed to load image: {e}")


def custom_message_dialog(root, title, message):
    dialog = Toplevel(root)
    dialog.title(title)
    dialog.geometry("400x200")
    dialog.configure(bg="#2b2b2b")

    message_label = Label(dialog, text=message, bg="#2b2b2b", fg="#ffffff", font=("Krona One", 12), justify=LEFT)
    message_label.pack(pady=30, padx=20)

    close_button = Button(dialog, text="Close", command=dialog.destroy, bg="#3c3f41", fg="#ffffff", font=("Krona One", 12), width=10, height=2, bd=0)
    close_button.pack(pady=10)

    dialog.update()
    dialog.grab_set()
    dialog.transient(root)


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

    # Store a reference to prevent garbage collection
    master.logo_img = logo_img  # Attach to master window

    logo_label = Label(master, image=master.logo_img, bg=bg_color)
    logo_label.image = master.logo_img  # Keep a reference
    logo_label.place(relx=0.5, rely=0.1, anchor="center")







if __name__ == "__main__":
    username = "user"
    receiver_username = "receiver"
    ip_address = "127.0.0.1"  # Adjust as needed
    app = StealthCodeApp(username, receiver_username, ip_address)
    app.run()
