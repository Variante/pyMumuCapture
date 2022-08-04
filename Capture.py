# -*- coding:utf-8 -*-
import mss
from util import *
from tkinter import *
import tkinter.font as tkFont
from PIL import Image, ImageDraw, ImageFont, ImageTk
from itertools import combinations
import numpy as np
import cv2
from datetime import datetime
import threading
import random
import wexpect
import time


def main(cfg):
    # Windows
    root = Tk()
    # Create a frame
    app = Frame(root)
    app.pack()

    # Create a label in the frame
    lmain = Label(app)
    lmain.pack()
    
    ldtag1 = Label(app, font=tkFont.Font(size=15, weight=tkFont.BOLD))
    ldtag1.pack()
    lentry = Entry(app) 
    lentry.pack()
    ldtag = Label(app, font=tkFont.Font(size=15, weight=tkFont.BOLD))
    ldtag.pack()
    ldres = Message(app, width=800, font=tkFont.Font(size=15, weight=tkFont.NORMAL))
    ldres.pack()
    
    root.title('MumuCapture')
    # root.geometry('1300x760')
    target_name = cfg['name']
   
    scale = cfg['scale']

    save_img = False
    
    def onKeyPress(event):
        nonlocal save_img
        # print(event)
        if event.char in 'rR':
            cfg = load_cfg()
            gm.set_config(cfg)
        if event.char in 'sS':
            save_img = True

    def get_stick(des, win):
        words = des.split(',')
        value = 0
        for w in words:
            if w in ['top', 'left', 'width', 'height']:
                value += win[w]
            else:
                value += int(w)
        return value

    root.bind('<KeyPress>', onKeyPress)

    with mss.mss() as m:
        def capture_stream():
            nonlocal save_img

            win_info = get_window_roi(target_name, [0, 0, 1, 1], cfg['padding'])
            if win_info['left'] < 0 and win_info['top'] < 0:
                ldtag1.configure(text='未检测到窗口')
                ldtag.configure(text='')
                ldres.configure(text='')
                img_cache = None
            else:
                full_win = get_window_roi(target_name,[0, 0, 1, 1], [0, 0, 0, 0])
                if len(cfg['stick']) == 2:
                    root.geometry(f"+{get_stick(cfg['stick'][0], full_win)}+{get_stick(cfg['stick'][1], full_win)}")
                img = np.array(m.grab(win_info))
                pil_img = Image.fromarray(img[...,:3][...,::-1])
                        
                if save_img:
                    now = datetime.now()
                    date_time = now.strftime("./%H-%M-%S")
                    Image.fromarray(img[:, :, 2]).save(date_time + ".png")
                    save_img = False
                
                if scale > 0:
                    pil_img = pil_img.resize((int(pil_img.size[0] * scale), int(pil_img.size[1] * scale)))
                # update the display
                imgtk = ImageTk.PhotoImage(image=pil_img)
                lmain.imgtk = imgtk
                lmain.configure(image=imgtk)
            lmain.after(5, capture_stream) 

        capture_stream()
        root.mainloop()


def usage():
    print("AutoArk操作说明:\nS:保存当前截图\nR:重新加载配置" + '-'*8)


if __name__ == '__main__':
    usage()
    cfg = load_cfg()
    main(cfg)
