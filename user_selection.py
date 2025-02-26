from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
import subprocess
from tkinter import ttk
import vpn_networking
from PIL import Image, ImageTk, ImageFont, ImageDraw
import argparse
import os
import sys
import interface2
import shutil


class StealthCodeApp:
    def __init__(self, users, current_user):
        self.users = users
        self.current_user = current_user
        self.SELECTED_WG0_CONF = None
        self.root = Tk()
        
        # Setup GUI components
        self.setup_gui()

    def setup_gui(self):
        """Set up the GUI components."""
        self.root.title("StealthCode: User Selection")
        self.root.geometry("1100x700")
        self.root.configure(bg="#2b2b2b")

        # Custom font path
        font_path = r"assets/FasterOne-Regular.ttf"
        # Render the logo
        self.logo_with_custom_font(self.root, "STEALTHCODE", font_path, 72, "#2b2b2b", "#ffffff")

        # Create canvas
        canvas = Canvas(self.root, bg="#2b2b2b", highlightthickness=0, width=756, height=364)
        canvas.place(x=172, y=218)

        # Rounded rectangle dimensions
        W, H, RADIUS = 756, 364, 25
        x1, y1 = 0, 0
        x2, y2 = x1 + W, y1 + H

        # Draw the rounded rectangle
        self.create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=RADIUS, fill="#3c3f41", outline="")

        # Add "Select receiver" label
        label = Label(self.root, text="Select receiver", font=("Krona One", 16), fg="#ffffff", bg="#3c3f41")
        label.place(x=320, y=374)

        # Dropdown menu for receiver selection
        self.selected_receiver = StringVar()
        dropdown_menu = ttk.Combobox(
            self.root,
            textvariable=self.selected_receiver,
            values=self.users,
            state="readonly",
            font=("Krona One", 14),
            justify="left",
        )
        dropdown_menu.place(x=500, y=378, width=221.59, height=25)
        dropdown_menu.set("Select Receiver")  # Default placeholder

        # Add "OK" button
        ok_button = ttk.Button(self.root, text="OK", style="Custom.TButton", command=self.on_click)
        ok_button.place(x=662, y=420, width=60, height=32)

        # Customize "OK" button style
        style = ttk.Style()
        style.configure("Custom.TButton", font=("Krona One", 12), background="#5B5BE0", foreground="white")
        style.map("Custom.TButton", background=[("active", "#4D4DB8")])

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def logo_with_custom_font(self, master, text, font_path, size, bg_color, fg_color):
        """Render the logo text with a custom font using Pillow."""
        image_width, image_height = 600, 150
        image = Image.new("RGBA", (image_width, image_height), bg_color)
        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.truetype(font_path, size)
        except OSError:
            messagebox.showwarning("Font Error", "Custom font not found, using default font.")
            font = ImageFont.load_default()

        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_x = (image_width - (text_bbox[2] - text_bbox[0])) // 2
        text_y = (image_height - (text_bbox[3] - text_bbox[1])) // 2
        draw.text((text_x, text_y), text, font=font, fill=fg_color)

        logo_img = ImageTk.PhotoImage(image)
        logo_label = Label(master, image=logo_img, bg=bg_color)
        logo_label.image = logo_img
        logo_label.place(relx=0.5, rely=0.15, anchor="center")

    def create_rounded_rectangle(self, canvas, x1, y1, x2, y2, radius=21, **kwargs):
        """Draw a proportionally correct rounded rectangle."""
        if radius > (x2 - x1) / 2 or radius > (y2 - y1) / 2:
            radius = min((x2 - x1) / 2, (y2 - y1) / 2)

        points = [
            x1 + radius, y1,  # Start point (top-left corner arc start)
            x2 - radius, y1,  # Top-right corner arc start
            x2, y1,           # Top-right corner
            x2, y1 + radius,  # Right-top arc
            x2, y2 - radius,  # Right-bottom arc
            x2, y2,           # Bottom-right corner
            x2 - radius, y2,  # Bottom-right corner arc start
            x1 + radius, y2,  # Bottom-left arc start
            x1, y2,           # Bottom-left corner
            x1, y2 - radius,  # Left-bottom arc
            x1, y1 + radius,  # Left-top arc
            x1, y1            # Back to top-left corner
        ]

        return canvas.create_polygon(points, smooth=True, **kwargs)

    def on_click(self):
        receiver_name = self.selected_receiver.get()
        print("Receiver is:", receiver_name)

        receiver_ip = vpn_networking.user_ip_retrieval(receiver_name)
        print("Receiver IP:", receiver_ip)

        if receiver_ip:
            print("[+] Connecting to the VPN server...")
            if vpn_networking.vpn_server_connection():
                print("[+] VPN connection established.")
                self.root.destroy()

                # Start StealthCodeApp from interface2
                init = interface2.StealthCodeApp(self.current_user, receiver_name, receiver_ip)
                init.run()  # Run the second app's GUI in the same thread (blocking)
            else:
                print("[-] VPN connection failed. Asking user to select a config file...")
                self.show_custom_dialog()

                if self.SELECTED_WG0_CONF:
                    try:
                        self.root.destroy()
                        init = interface2.StealthCodeApp(self.current_user, receiver_name, receiver_ip)
                        init.run()  # Start the second app
                    except subprocess.CalledProcessError as e:
                        print(f"[ERROR] Failed to move config or start interface: {e}")
                else:
                    print("[-] No config file selected. VPN connection cannot proceed.")
        else:
            print("Receiver IP retrieval failed.")

    def show_custom_dialog(self):
        """Display a custom dialog box that forces the user to select a file."""
        def select_file():
            """Allow the user to select a file."""
            file_path = filedialog.askopenfilename(
                title="Select a File",
                filetypes=[("All Files", "*.*"), ("Text Files", "*.txt"), ("Images", "*.png;*.jpg")]
            )
            if file_path and os.path.exists(file_path):
                self.SELECTED_WG0_CONF = file_path
                selected_file_label.config(
                    text=f"Selected File:\n{file_path}",
                    wraplength=250,
                    justify="center",
                    fg="green"
                )
                
                confirm_button.config(state="normal")  # Enable the confirm button
            else:
                selected_file_label.config(text="No valid file selected. Please try again.", fg="red")

        def confirm_selection():
            """Confirm the file selection and close the dialog."""
            if self.SELECTED_WG0_CONF:
                dialog.destroy()
                shutil.move(self.SELECTED_WG0_CONF, "/etc/wireguard/wg0.conf")
                print(f"File moved to {"/etc/wireguard/wg0.conf"}")
                vpn_networking.vpn_server_connection()
            else:
                messagebox.showwarning("File Required", "You must select a valid file to proceed!")

        # Create a new Toplevel window (dialog box)
        dialog = Toplevel(self.root)
        dialog.title("Custom Dialog")
        dialog.geometry("400x250")
        dialog.transient(self.root)  # Make it a modal dialog (blocks interaction with the main window)
        dialog.grab_set()  # Disable interaction with other windows

        # Add a label to the dialog
        Label(dialog, text="Please select a file to proceed.", font=("Arial", 12)).pack(pady=20)

        # Label to display the selected file
        selected_file_label = Label(dialog, text="", font=("Arial", 10), fg="red")
        selected_file_label.pack(pady=10)

        # Add a "Select File" button
        select_button = Button(dialog, text="Select File", command=select_file, font=("Arial", 10))
        select_button.pack(pady=10)

        # Add a "Confirm" button to confirm selection
        confirm_button = Button(
            dialog, text="Confirm", command=confirm_selection, font=("Arial", 10), state="disabled"
        )
        confirm_button.pack(pady=10)

        # Prevent closing the window without a valid selection
        dialog.protocol("WM_DELETE_WINDOW", confirm_selection)

        # Wait for the dialog to close before proceeding
        self.root.wait_window(dialog)

    def on_close(self):
        """Handle the closing of the root window."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            # Destroy the root window
            self.root.destroy()
            sys.exit()  # Exit after closing the window

    def run(self):
        """Run the Tkinter main loop."""
        self.root.mainloop()


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--users", type=str, required=True, help="List of available users")
    parser.add_argument("--current-user", type=str, required=True, help="Current user logged in")
    args = parser.parse_args()

    # Convert the received string back into a list
    users = args.users.split(",")
    current_user = args.current_user

    # Start the application
    app = StealthCodeApp(users, current_user)
    app.run()
