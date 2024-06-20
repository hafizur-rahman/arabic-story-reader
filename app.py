import tkinter as tk
from tkinter import *
from tkinter.filedialog import askopenfile

from pdf2image import convert_from_path
from PIL import ImageTk, Image
from awesometkinter.bidirender import add_bidi_support

import IPython
import easyocr
import threading



import numpy as np

from ocr_reader import OcrReader
from translator import Translator


class App(tk.Tk):
    def __init__(self, title):
        super().__init__()

        self.translated_text = None
        self.extracted_text = None
        self.translate_text_label = None
        self.extracted_text_label = None
        self.load_pdf_btn = None
        self.image_on_canvas = None
        self.title(title)
        self.geometry("1400x700")

        self.bind("<Button-1>", self.__on_mouse_down)
        self.bind("<ButtonRelease-1>", self.__on_mouse_release)
        self.bind("<B1-Motion>", self.__on_mouse_move)
        self.bind("<Key>", self.__on_key_down)
        self.bind("<Up>", self.__on_keyUP)
        self.bind("<Down>", self.__on_keyDown)
        self.bind("<Left>", self.__on_keyLeft)
        self.bind("<Right>", self.__on_keyRight)

        self.box = [0, 0, 0, 0]
        self.ratio = 1.0
        self.rectangle = None
        self.crop_box = None

        self.pdf_file=None
        self.pages = []

        self.pdf_page_view = None
        self.current_page_no = 0

        self.page_image = tk.PhotoImage(file="./pexels-photo-3560168.png")

        self.ocr_reader = OcrReader(lang='ar')
        self.translator = Translator(model_name='facebook/nllb-200-distilled-600M')

    def build_ui(self):
        # Create Frame widget
        left_frame = Frame(self, width=600, height=800)
        left_frame.grid(row=0, column=0, padx=10, pady=5)

        right_frame = Frame(self, width=600, height=800)
        right_frame.grid(row=0, column=1, padx=10, pady=5)

        pdf_control_frame = Frame(left_frame, width=650, height=20)
        pdf_control_frame.grid(row=1, column=0, padx=10, pady=5)

        # Create label above the tool_bar
        self.load_pdf_btn = Button(pdf_control_frame, text="Load PDF...", command=self.show)
        self.load_pdf_btn.grid(row=1, column=0, padx=5, pady=5)

        self.pdf_page_view = tk.Canvas(left_frame, width=800, height=800)
        self.pdf_page_view.grid(row=0,column=0, padx=5, pady=5)
        self.image_on_canvas = self.pdf_page_view.create_image(0, 0, anchor="nw", image=self.page_image)

        Button(pdf_control_frame, text="<", command=self.show_prev_page).grid(
            row=1, column=1, padx=5, pady=5)
        Button(pdf_control_frame, text=">", command=self.show_next_page).grid(
            row=1, column=2, padx=5, pady=5)
        Button(pdf_control_frame, text="Extract", command=self.on_extract_text).grid(
            row=1, column=3, padx=5, pady=5)

        Label(right_frame,
              text="Extracted text (Please correct the text and format for better transtlation)",
              font=("Times New Roman", 14)
              ).grid(row=0,column=0, padx=5, pady=5)
        self.extracted_text_label = Text(right_frame, width=75, height=12, font=("Courier", 18))
        self.extracted_text_label.grid(row=1,column=0, padx=5, pady=5)

        Button(right_frame, text="Translate...", command=self.translate_text).grid(
            row=2, column=0, padx=5, pady=5)
        self.translate_text_label = Text(right_frame, width=80, height=12, font=("Courier", 16))
        self.translate_text_label.grid(row=3,column=0, padx=5, pady=5)
        #self.translate_text_label.bind('<Configure>', lambda e: label.config(wraplength=label.winfo_width()))

        add_bidi_support(self.extracted_text_label)
        add_bidi_support(self.translate_text_label)

    def __on_mouse_down(self, event):
        self.box[0], self.box[1] = event.x, event.y
        self.box[2], self.box[3] = event.x, event.y
        #print("top left coordinates: %s/%s" % (event.x, event.y))

    def __on_mouse_release(self, event):
        #print("bottom_right coordinates: %s/%s" % (self.box[2], self.box[3]))
        pass

    def __on_mouse_move(self, event):
        self.box[2], self.box[3] = event.x, event.y
        self.__refresh_rectangle()

    def __on_key_down(self, event):
        if event.char == 'q':
            self.destroy()

    def __on_keyUP(self, event):
        #print('UP')
        self.box[1] = self.box[1] - 1
        self.box[3] = self.box[3] - 1
        self.__refresh_rectangle()

    def __on_keyDown(self, event):
        self.box[1] = self.box[1] + 1
        self.box[3] = self.box[3] + 1
        self.__refresh_rectangle()
        #print ('Down')

    def __on_keyLeft(self, event):
        #print ('Left')
        self.box[0] = self.box[0] - 1
        self.box[2] = self.box[2] - 1
        self.__refresh_rectangle()

    def __on_keyRight(self, event):
        #print ('Right')
        self.box[0] = self.box[0] + 1
        self.box[2] = self.box[2] + 1
        self.__refresh_rectangle()

    def __refresh_rectangle(self):
        self.pdf_page_view.delete(self.rectangle)
        self.crop_box = [self.box[0], self.box[1], self.box[2], self.box[3]]
        self.rectangle = self.pdf_page_view.create_rectangle(self.box[0], self.box[1], self.box[2], self.box[3])

    def __fix_ratio_point(self, px, py):
        dx = px - self.box[0]
        dy = py - self.box[1]
        if min((dy / self.ratio), dx) == dx:
            dy = int(dx * self.ratio)
        else:
            dx = int(dy / self.ratio)
        return self.box[0] + dx, self.box[1] + dy

    def show(self):
        file_chosen = askopenfile()

        if file_chosen:
            self.pdf_file = file_chosen

            print(self.pdf_file.name)

            self.pages = convert_from_path(self.pdf_file.name)
            print(f"Pdf file loaded, page count: {len(self.pages)}")

            if len(self.pages):
                self.show_page(0)

    def show_page(self, page_no):
        if 0 <= page_no < len(self.pages):
            self.current_page_no = page_no

            image = self.pages[self.current_page_no]

            newImage = image.resize((800, 800))
            self.page_image = ImageTk.PhotoImage(newImage)

            self.pdf_page_view.itemconfig(self.image_on_canvas, image=self.page_image)

    def show_next_page(self):
        self.show_page(self.current_page_no + 1)

    def show_prev_page(self):
        self.show_page(self.current_page_no - 1)

    def on_extract_text(self):
        t1 = threading.Thread(target=self.extract_text)
        t1.start()

    def extract_text(self):
        cropped = ImageTk.getimage(self.page_image).crop(self.crop_box)

        self.extracted_text = self.ocr_reader.parse_text(np.array(cropped))

        self.extracted_text_label.delete("1.0", tk.END)
        self.extracted_text_label.insert(tk.INSERT, self.extracted_text)

    def translate_text(self):
        output = self.translator.translate(self.extracted_text_label.get("1.0", tk.END))
        self.translated_text = output[0]['translation_text']
        self.translate_text_label.delete("1.0", tk.END)
        self.translate_text_label.insert(tk.INSERT, self.translated_text)


window = App("Arabic Study")
window.build_ui()

window.mainloop()