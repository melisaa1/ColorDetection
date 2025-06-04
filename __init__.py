import cv2
from tkinter import *
from tkinter import colorchooser
import numpy as np
import webcolors
from webcolors import CSS3_NAMES_TO_HEX
from difflib import get_close_matches
import sqlite3


def init_db():
    conn = sqlite3.connect('/Users/user/PyCharmMiscProject/OpenCvTest1/image_versions.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS image_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_data BLOB
        )
    ''')
    conn.commit()
    conn.close()


def load_last_image_from_db():
    conn = sqlite3.connect('/Users/user/PyCharmMiscProject/OpenCvTest1/image_versions.db')
    cursor = conn.cursor()
    cursor.execute("SELECT image_data FROM image_versions ORDER BY id DESC LIMIT 1 OFFSET 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        nparr = np.frombuffer(row[0], np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    else:
        return None

def closest_color_name(requested_rgb):
    min_colors = {}
    for name, hex_code in webcolors.CSS3_NAMES_TO_HEX.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(hex_code)
        rd = (int(r_c) - int(requested_rgb[0])) ** 2
        gd = (int(g_c) - int(requested_rgb[1])) ** 2
        bd = (int(b_c) - int(requested_rgb[2])) ** 2
        min_colors[rd + gd + bd] = name
    closest_name = min_colors[min(min_colors)]
    return closest_name

selectedColor = (0,0,0)
last_x ,last_y =None,None
isSelect=False
image_history=[]

def select():
    global selectedColor,last_x,last_y,image, isSelect ,image_history
    color = colorchooser.askcolor()
    if color[0] and last_y is not None and last_x is not None:
        #image_history.append(image.copy())
        isSelect = True
        rgb_color = color[0]
        selectedColor = (int(rgb_color[2]), int(rgb_color[1]), int(rgb_color[0]))
        cv2.circle(image,(last_x,last_y),5,selectedColor,-1)
        cv2.imshow("Image",image)
        save_image_to_db(image.copy())
    else:
        message_label4.config(text="🎨you didn't choose any pixel yet", fg="green")


def save():
    if isSelect :
     cv2.imwrite("savedImage.png", image)
     message_label.config(text="🎨saved successfully!", fg="green")
    else :
     message_label.config(text="🎨no change in image!", fg="green")

def save_image_to_db(image):
    conn = sqlite3.connect('/Users/user/PyCharmMiscProject/OpenCvTest1/image_versions.db')
    cursor = conn.cursor()
    is_success, buffer = cv2.imencode(".png", image)
    if is_success:
        cursor.execute("INSERT INTO image_versions (image_data) VALUES (?)", (buffer.tobytes(),))
        conn.commit()
    conn.close()

def get_pixel(event, x, y, flags, param):
    global image,last_x,last_y
    if event == cv2.EVENT_LBUTTONDOWN:
        pixel_value = image[y, x]
        print(f"Clicked at: {x}, {y}")
        print(f"Original Pixel Value (BGR): {pixel_value}")


        rgb_value = (pixel_value[2], pixel_value[1], pixel_value[0])
        background = f'#{rgb_value[0]:02x}{rgb_value[1]:02x}{rgb_value[2]:02x}'
        frame.config(bg=background)


        last_y,last_x=y,x
        temporary_image=image.copy()
        cv2.circle(temporary_image, (x, y), 10, (0,0,0), 1)
        cv2.imshow("Image", temporary_image)

        try:
            color_name = webcolors.rgb_to_name(rgb_value)
        except ValueError:
            color_name = closest_color_name(rgb_value)

        message_label1.config(text=f"Color: {color_name}", fg="black")


def calculate_dominant_color(image):
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    pixels = image_rgb.reshape(-1, 3)

    unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)

    dominant_color_idx = np.argmax(counts)

    dominant_color = unique_colors[dominant_color_idx]
    rgb_value = tuple(dominant_color)

    hex_color = f'#{dominant_color[0]:02x}{dominant_color[1]:02x}{dominant_color[2]:02x}'

    frame1.config(bg=hex_color)

    try:
        color_name = webcolors.rgb_to_name(rgb_value)
    except ValueError:
        color_name = closest_color_name(rgb_value)

    message_label2.config(text=f"Dominant color: {color_name}", fg="green")

def undo():
    global image
    conn = sqlite3.connect('/Users/user/PyCharmMiscProject/OpenCvTest1/image_versions.db')
    cursor = conn.cursor()

    # Count how many versions we have
    cursor.execute("SELECT COUNT(*) FROM image_versions")
    count = cursor.fetchone()[0]

    if count >= 2:
        # Delete the latest image
        cursor.execute("DELETE FROM image_versions WHERE id = (SELECT id FROM image_versions ORDER BY id DESC LIMIT 1)")
        conn.commit()

        # Load the new latest
        cursor.execute("SELECT image_data FROM image_versions ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        if row:
            nparr = np.frombuffer(row[0], np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            cv2.imshow("Image", image)
    else:
        conn.close()
        message_label3.config(text="🎨Nothing to undo!", fg="green")

init_db()
window = Tk()
window.geometry("350x350")
window.title("Detected Color")
frame = Frame(window, bd=50, relief="flat", width=100, height=100)
frame.place(x=0, y=0)
button = Button(window, text='Select Color', command=select)
button.place(x=150, y=0)
button = Button(window, text='save image', command=save)
button.place(x=150, y=280)
message_label = Label(window, text="", fg="green")
message_label.place(x=150, y=310)
message_label1 = Label(window, text="", fg="green")
message_label1.place(x=0, y=110)
message_label2 = Label(window, text="", fg="green")
message_label2.place(x=150, y=250)
message_label3 = Label(window, text="", fg="green")
message_label3.place(x=150, y=100)
message_label4 = Label(window, text="", fg="green")
message_label4.place(x=150, y=30)
button = Button(window, text='undo', command=undo)
button.place(x=150, y=70)


frame1 = Frame(window, bd=50, relief="flat", width=50, height=50)
frame1.place(x=190, y=190)

image = cv2.imread('secondimg.jpeg', 1)

#image = cv2.imread('new_image.jpeg', 1)
image = cv2.resize(image, (600, 700))
save_image_to_db(image.copy())
cv2.imshow("Image", image)
cv2.setMouseCallback("Image", get_pixel)
cv2.moveWindow("Image", 380, -100)


button = Button(window, text='dominant color', command=lambda : calculate_dominant_color(image))
button.place(x=150, y=150)
window.mainloop()
cv2.destroyAllWindows()
