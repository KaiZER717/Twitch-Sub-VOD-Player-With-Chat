import datetime
import sys
import threading
import tkinter.font as tkFont
from time import sleep
from tkinter import *
from tkinter import scrolledtext, ttk

import vlc

import chat
import find_vod

if not sys.version_info.major == 3 and sys.version_info.minor >= 7:
    print("This script requires Python 3.7 or higher!")
    print(f"You are using Python {sys.version_info.major}.{sys.version_info.minor}")
    input()
    sys.exit(1)

vod = find_vod.vod_selector()


# Navigate events

def get_navscale_motion(event):
    global player
    if vlc.libvlc_media_player_is_playing(player):
        vlc.libvlc_media_player_pause(player)


def get_navscale_release(event):
    global scal, player
    vlc.libvlc_media_player_set_position(player, scal.get())
    if not vlc.libvlc_media_player_is_playing(player):
        vlc.libvlc_media_player_pause(player)


def get_volscale_release(event):
    global vol_scal, player
    vlc.libvlc_audio_set_volume(player, vol_scal.get())


def play_pause():
    global player
    vlc.libvlc_media_player_pause(player)


# Chat time sync

def print_mess(mess):
    global console
    console.configure(state='normal')  # enable insert
    try:
        console.insert(END, str(mess.timesign) + " ", 'timesign')
        console.tag_config('timesign', foreground='#C0C0C0')
        console.insert(END, str(mess.sender), str(mess.sender))
        console.tag_config(str(mess.sender), foreground=mess.colour)
        console.insert(END, ": ", 'mess')
        console.insert(END, str(mess.mess) + "\n", 'mess')
        console.tag_config('mess', foreground='#FFFFFF')
    except UnicodeError:
        print("error " + mess.mess)
    console.yview(END)  # autoscroll
    console.configure(state='disabled')  # disable editing


def player_sync():
    global scal, label, thread_status
    while thread_status:
        if vlc.libvlc_media_player_is_playing(player) == 1:
            time_sign = vlc.libvlc_media_player_get_time(player)
            lenght = vlc.libvlc_media_player_get_length(player) + (1 / 10 * 8)
            formated = str(datetime.timedelta(milliseconds=time_sign))[:7]
            label["text"] = formated
            scal.set(time_sign / lenght)
        sleep(.8)


def chat_sync(player, vod):
    global thread_status
    printed = []
    while thread_status:
        if vlc.libvlc_media_player_is_playing(player) == 1:
            messages = chat.message_dict(vod)
            if messages == "path error":
                on_closing()
            timecode = str(int(vlc.libvlc_media_player_get_time(player) // 1000) - 1)
            if timecode in messages:
                if len(messages[timecode]) != 1:
                    for mes1 in messages[timecode]:
                        if mes1.key not in printed:
                            print_mess(mes1)
                            printed.append(mes1.key)
                else:
                    if messages[timecode][0].key not in printed:
                        print_mess(messages[timecode][0])
                        printed.append(messages[timecode][0].key)
        sleep(.4)


# Create main widget

root = Tk()
root.title(vod.vod_name)
root.geometry("1280x720")
root.minsize(width=1000, height=650)
font_tp = tkFont.Font(family="roobert", size=11)

# VLC player creating

Instance = vlc.Instance()
player = Instance.media_player_new()
media = Instance.media_new(vod.vod_link)
player.set_media(media)
player_playing = True
vlc.libvlc_audio_set_volume(player, 100)

# Create widgets

console = scrolledtext.ScrolledText(root, width=50, height=50,
                                    state='disable', font=font_tp,
                                    wrap=WORD, borderwidth=0,
                                    highlightthickness=0)
button = ttk.Button(root, text="Pause", command=play_pause)
scal = Scale(root, orient=HORIZONTAL, length=373, from_=0,
             to=1, resolution=0.0001, sliderlength=10, fg="#f0f0f0",
             borderwidth=0, highlightthickness=0)
vol_scal = Scale(root, orient=HORIZONTAL, length=80,
                 from_=0, to=100, resolution=1, sliderlength=10,
                 borderwidth=0, highlightthickness=0)
player_frame = Label(root)
label = Label(root)

console['background'] = "#313335"
root['background'] = "#313335"
scal['background'] = "#313335"
scal['foreground'] = "#313335"
vol_scal['background'] = "#313335"
vol_scal['foreground'] = "#c8c8c8"
label['background'] = "#313335"
label['foreground'] = "#c8c8c8"

scal.bind("<B1-Motion>", get_navscale_motion)
scal.bind("<ButtonRelease-1>", get_navscale_release)

vol_scal.bind("<ButtonRelease-1>", get_volscale_release)
root.bind("<space>", lambda event: vlc.libvlc_media_player_pause(player))

vol_scal.set(100)

# Packing

player_frame.place(x=0, y=0, relwidth=.78, relheight=.94)
button.place(x=5, rely=0.95, relwidth=.05, relheight=.04)
vol_scal.place(relx=.08, rely=0.94, relwidth=.05, relheight=.1)
scal.place(relx=.15, rely=0.94, relwidth=.5, relheight=.1)
label.place(relx=.67, rely=0.953, relwidth=.05, relheight=0.05)
console.place(relx=.78, rely=0, relwidth=.22, relheight=1)

# Thread creating

thread_chat = threading.Thread(target=player_sync, daemon=True)
thread_chat_sync = threading.Thread(target=chat_sync, args=(player, vod), daemon=True)
thread_status = True
player.set_hwnd(player_frame.winfo_id())

player.play()
thread_chat_sync.start()
thread_chat.start()


def on_closing():
    global thread_status
    thread_status = False
    vlc.libvlc_media_player_stop(player)
    root.quit()
    sys.exit(7)


root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()