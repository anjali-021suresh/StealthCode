from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk, ImageFont, ImageDraw
import subprocess
import shlex
import vpn_networking
import sys
import user_selection

def logo_with_custom_font(master, text, font_path, size, bg_color, fg_color):
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

def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    """Draw a rounded rectangle on a Tkinter Canvas."""
    points = [
        (x1 + radius, y1),
        (x1 + radius, y1),
        (x2 - radius, y1),
        (x2 - radius, y1),
        (x2, y1),
        (x2, y1 + radius),
        (x2, y1 + radius),
        (x2, y2 - radius),
        (x2, y2 - radius),
        (x2, y2),
        (x2 - radius, y2),
        (x2 - radius, y2),
        (x1 + radius, y2),
        (x1 + radius, y2),
        (x1, y2),
        (x1, y2 - radius),
        (x1, y2 - radius),
        (x1, y1 + radius),
        (x1, y1 + radius),
        (x1, y1),
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)

def login():
    """Handle login action."""
    username = username_entry.get().strip()
    password = password_entry.get().strip()

    if not username or not password:
        messagebox.showerror("Input Error", "Username and password cannot be empty.")
        return 

    print("Entering networking")
    users = vpn_networking.send_auth_details(username, password)
    print("Exiting networking")

    if users:
        messagebox.showinfo("Login Successful", f"Welcome, {username}!")
        root.destroy()

        users_arg = ",".join(users)

        # Improved subprocess handling
        try:
            inint = user_selection.StealthCodeApp(users, username)
            inint.run()


        except subprocess.CalledProcessError as e:
            messagebox.showerror("Subprocess Error", f"Failed to launch user_selection.py:\n{e.stderr}")
        except Exception as e:
            messagebox.showerror("Unexpected Error", str(e))

    
    else:
        messagebox.showerror("Login Failed", "Invalid username or password.")


def on_button_click(event):
    login()

def on_button_hover(event):
    login_button_canvas.itemconfig(button_id, fill="#365adf")

def on_button_leave(event):
    login_button_canvas.itemconfig(button_id, fill="#4a73ff")

def on_close():
    """Handle the closing of the root window."""
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        try:
            # Terminate any running subprocesses
            for process in list(subprocess._active):
                try:
                    process.terminate()
                except Exception as e:
                    print(f"Error terminating process: {e}")

            # Destroy the root window
            root.destroy()

            # Ensure clean exit
            sys.exit(0)
        except Exception as e:
            print(f"Error during shutdown: {e}")

# Main window setup
root = Tk()
root.title("Login Page")
root.geometry("1100x700")
root.configure(bg="#2b2b2b")

# Custom font path
font_path = r"assets/FasterOne-Regular.ttf"

# Render the logo
logo_with_custom_font(root, "STEALTHCODE", font_path, 72, "#2b2b2b", "#ffffff")

# Create the login box
login_frame = Frame(root, bg="#3c3f41", bd=0, relief=RAISED)
login_frame.place(relx=0.5, rely=0.55, anchor="center", width=450, height=450)

# Add a profile icon
icon_path = r"assets/profile_icon.png"  
try:
    profile_img = Image.open(icon_path).resize((90, 90), Image.LANCZOS)
    profile_photo = ImageTk.PhotoImage(profile_img)
    icon_label = Label(login_frame, image=profile_photo, bg="#3c3f41")
    icon_label.image = profile_photo
    icon_label.place(x=175, y=10)
except FileNotFoundError:
    messagebox.showwarning("Icon Error", "Profile icon not found.")

# "Login" text
Label(login_frame, text="Login", font=("Helvetica", 14, "bold"), bg="#3c3f41", fg="#ffffff").place(x=190, y=120)

# Username label and input with rounded corners
Label(login_frame, text="Username", font=("Helvetica", 12), bg="#3c3f41", fg="#ffffff").place(x=50, y=160)
username_canvas = Canvas(login_frame, bg="#3c3f41", highlightthickness=0, width=350, height=40)
username_canvas.place(x=50, y=190)
create_rounded_rectangle(username_canvas, 0, 0, 350, 40, radius=20, fill="#2b2b2b", outline="")
username_entry = Entry(login_frame, font=("Helvetica", 12), bd=0, highlightthickness=0, bg="#2b2b2b", fg="#ffffff", insertbackground="#ffffff")
username_entry.place(x=65, y=197, width=330, height=30)

# Password label and input with rounded corners
Label(login_frame, text="Password", font=("Helvetica", 12), bg="#3c3f41", fg="#ffffff").place(x=50, y=250)
password_canvas = Canvas(login_frame, bg="#3c3f41", highlightthickness=0, width=350, height=40)
password_canvas.place(x=50, y=280)
create_rounded_rectangle(password_canvas, 0, 0, 350, 40, radius=20, fill="#2b2b2b", outline="")
password_entry = Entry(login_frame, font=("Helvetica", 12), bd=0, highlightthickness=0 ,bg="#2b2b2b", fg="#ffffff", insertbackground="#ffffff", show="*")
password_entry.place(x=65, y=287, width=330, height=30)

# Custom Login Button with rounded corners
login_button_canvas = Canvas(login_frame, bg="#3c3f41", highlightthickness=0, width=200, height=50)
login_button_canvas.place(x=125, y=350)
button_id = create_rounded_rectangle(login_button_canvas, 0, 0, 200, 50, radius=25, fill="#4a73ff", outline="")
login_button_canvas.create_text(100, 25, text="Login", font=("Helvetica", 12, "bold"), fill="#ffffff")

# Bind hover and click events to the button
login_button_canvas.tag_bind(button_id, "<Button-1>", on_button_click)
login_button_canvas.tag_bind(button_id, "<Enter>", on_button_hover)

root.mainloop()
