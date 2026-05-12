import os
import sys
import json
import socket
import time
import io
import re
import random
import tempfile
import zipfile
import multiprocessing
from multiprocessing import Queue, Manager, freeze_support
from tkinter import filedialog, messagebox
import tkinterdnd2
import customtkinter
from customtkinter import CTkLabel as Label, CTkFrame as Frame, CTkButton as button, CTkImage, CTkFont
from PIL import Image
import segno
import threading
from flask import Flask, redirect, url_for, render_template, request, send_file, jsonify, Response,abort
from werkzeug.utils import secure_filename
import math

#PATH CONFIGURATIONS
user_home = os.path.expanduser("~")
app_folder = ".transfer_wizard"
config_folder = os.path.join(user_home, app_folder)

config_file = os.path.join(config_folder, "config.json")
qr_temp_path = os.path.join(config_folder, "QR.png")
default_path = os.path.join(user_home, "Downloads")

default_config = {
    "path": default_path,
    "mode": "dark"
}

if not os.path.exists(config_folder):
    os.makedirs(config_folder)

def load_config():
    if not os.path.exists(config_file):
        with open(config_file, "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config
    with open(config_file, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default_config

def save_config(config_dict):
    with open(config_file, "w") as f:
        json.dump(config_dict, f, indent=4)

app_config = load_config()
actual_path = app_config["path"]
default_mode = app_config["mode"]

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
# finding the ip
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
except:
    ip = "127.0.0.1"

def qr():
    qr_img = segno.make_qr(f"http://{ip}:5000")
    qr_img.save(qr_temp_path, scale=10)

def format_bytes(bytes_size):
    if bytes_size <= 0: return '0 Bytes'
    k = 1024
    sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    i = int(math.floor(math.log(bytes_size, k)))
    return f"{round(bytes_size / (k ** i), 2)} {sizes[i]}"

def format_time(seconds):
    if seconds < 0 or not math.isfinite(seconds): return "Calculating..."
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remaining_seconds = int(seconds % 60)
    
    parts = []
    if hours > 0: parts.append(f"{hours} hr")
    if minutes > 0: parts.append(f"{minutes} min")
    parts.append(f"{remaining_seconds} sec")
    return " ".join(parts)


def create_zip(filepaths_to_send):
    """Writes a zip file to the OS Temp folder without using compression to save RAM/Time"""
    temp_dir = tempfile.gettempdir()
    temp_zip_path = os.path.join(temp_dir, f"transfer_wizard_{os.urandom(4).hex()}.zip")
    
    with zipfile.ZipFile(temp_zip_path, 'w', compression=zipfile.ZIP_STORED) as zip_file:
        for filepath in filepaths_to_send:
            try:
                filename = os.path.basename(filepath)
                zip_file.write(filepath, filename)
            except FileNotFoundError:
                print(f"Skipping missing file: {filepath}")
    return temp_zip_path

def track_and_stream(filepath, total_size, server_state, is_temp=False):
    """Streams files to the phone and calculates progress, speed, and ETA."""
    bytes_sent = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    
    server_state["download_progress"] = 1 
    server_state["download_stats"] = "Speed: Calculating... | Time Left: Calculating..."
    
    start_time = time.time()
    last_update_time = start_time
    last_bytes_sent = 0
    
    try:
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
                
                bytes_sent += len(chunk)
                current_time = time.time()
                
                percent = int((bytes_sent / total_size) * 100)
                server_state["download_progress"] = max(1, min(99, percent))
                
                # --- SPEED & ETA CALCULATION ---
                # We update the stats every 0.5 seconds to keep the UI smooth
                time_elapsed = current_time - last_update_time
                if time_elapsed > 0.5:
                    bytes_this_interval = bytes_sent - last_bytes_sent
                    speed_bps = bytes_this_interval / time_elapsed
                    
                    if speed_bps > 0:
                        eta_seconds = (total_size - bytes_sent) / speed_bps
                        eta_str = format_time(eta_seconds)
                    else:
                        eta_str = "Calculating..."
                        
                    speed_str = f"{format_bytes(speed_bps)}/s"
                    server_state["download_stats"] = f"Speed: {speed_str}  |  Time Left: {eta_str}"
                    
                    last_update_time = current_time
                    last_bytes_sent = bytes_sent
                    
        # Stream finished!
        server_state["download_progress"] = 100
        
    finally:
        if server_state.get("download_progress") != 100:
            server_state["download_progress"] = 0
        server_state["download_stats"] = "" # Clean up stats
        
        if is_temp:
            try:
                os.remove(filepath)
            except Exception:
                pass



def stream_and_delete(filepath):
    """Streams the zip to the downloader and cleans up the temp file afterwards"""
    try:
        with open(filepath, 'rb') as f:
            yield from f
    finally:
        try:
            os.remove(filepath)
            print(f"Cleaned up temporary file: {filepath}")
        except Exception as e:
            print(f"Could not delete temp file: {e}")

def ms_con():
    messagebox.showinfo("Connected", "You are Connected")

def msg():
    messagebox.showinfo("Received", "Files Received Successfully. Saved In Your Folder")

def clear_frame(frame):
    """Destroys all widgets in a frame to prevent stacking/overlapping UI bugs"""
    for widget in frame.winfo_children():
        widget.destroy()

def open_folder():
    if os.name == 'nt':
        os.startfile(actual_path)
    elif sys.platform == 'darwin':
        os.system(f'open "{actual_path}"')
    else:
        os.system(f'xdg-open "{actual_path}"')

def folder():
    global actual_path
    folder_path = filedialog.askdirectory(title="Folder to save your files?")
    if folder_path:
        actual_path = folder_path
        app_config["path"] = actual_path
        save_config(app_config)
        try:
            label3.configure(text=f"Your File will be saved in {actual_path}")
        except NameError:
            pass

def mode():
    v = value.get()
    customtkinter.set_appearance_mode(v)
    app_config["mode"] = v
    save_config(app_config)

def open_file_dialog():
    files = filedialog.askopenfiles(mode='r')
    if files:
        paths = [os.path.abspath(f.name) for f in files]
        path_queue.put(paths)

def draganddrop(files):
    if files:
        path_queue.put(files)

def server(q1, path_queue,server_state):
    template_dir = resource_path('templates')
    static_dir = resource_path('static')
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    @app.route("/")
    def router():
        return redirect(url_for("home"))
    
    @app.route('/home')
    def home():
        if server_state['locked_ip'] is None:
            server_state['locked_ip']=request.remote_addr
            q1.put("Connected")
            return render_template("Home.html")
        else:
            if server_state['locked_ip']==request.remote_addr:
                return render_template("Home.html")
            else:
                return abort(403)
            
    @app.route('/Send')
    def Send():
        if server_state['locked_ip'] is not None:
            if server_state['locked_ip']==request.remote_addr:
                return render_template("Upload.html")
            else:
                return abort(403)
        else:
            return abort(403)

    @app.route('/upload', methods=["POST"])
    def upload():
        client_ip = request.remote_addr
        if server_state['locked_ip'] is not None:
            if server_state['locked_ip']==request.remote_addr:
                current_config = load_config()
                save_dir = current_config["path"]    
                if save_dir and os.path.exists(save_dir):
                    try:
                        files = request.files.getlist("file")
                        if files:
                            filenames = []
                            for f in files:
                                safe_filename = secure_filename(f.filename) or "unnamed_file"
                                final_path = os.path.join(save_dir, safe_filename)
                                f.save(final_path)
                                filenames.append(safe_filename)
                            return jsonify({"message": "Files uploaded successfully", "filenames": filenames}), 200
                        else:
                            return jsonify({"error": "No files were selected"}), 400
                    except Exception as e:
                        return jsonify({"error": str(e)}), 500
                else:
                    return jsonify({"error": "Upload path not configured"}), 400 
            else:
                return abort(403)
        else:
            return abort(403)    

    @app.route('/snd')
    def snd():
        if server_state['locked_ip'] is not None:
            if server_state['locked_ip']==request.remote_addr:
                try:
                    data = path_queue.get(timeout=0.5)
                    if data:
                        filepaths_to_send = data
                        if filepaths_to_send:
                            unique_id=random.randint(1000,9999)
                            if len(filepaths_to_send) > 1:
                                temp_zip_path = create_zip(filepaths_to_send)
                                total_size = os.path.getsize(temp_zip_path)
                                unique_filename=f"file_{unique_id}.zip"
                                return Response(
                                    track_and_stream(temp_zip_path, total_size, server_state, is_temp=True),
                                    mimetype='application/zip',
                                    headers={
                                        'Content-Disposition': f'attachment; filename="{unique_filename}"',
                                        'Content-Length': str(total_size)
                                    }
                                )
                            else:
                                single_file = filepaths_to_send[0]
                                total_size = os.path.getsize(single_file)
                                original_name = os.path.basename(single_file)
                                name,ext=os.path.splitext(original_name)
                                unique_filename=f"{name}_{unique_id}{ext}"
                                return Response(
                                    track_and_stream(single_file, total_size, server_state, is_temp=False),
                                    mimetype='application/octet-stream',
                                    headers={
                                        'Content-Disposition': f'attachment; filename="{unique_filename}"',
                                        'Content-Length': str(total_size)
                                    }
                                )
                    return render_template("not.html")
                except multiprocessing.queues.Empty:
                    return render_template("not.html")
            else:
                return abort(403)
        else:
            return abort(403)
        
    @app.route('/disconnect')
    def disconnect():
        client_ip = request.remote_addr
        if server_state['locked_ip']==client_ip:
            q1.put("Disconnected")
            return render_template("dis.html")
        
    @app.route('/progress', methods=["POST"])
    def update_progress():
        data = request.get_json(silent=True)
        if data:
            if data and "percent" in data:
                server_state["upload_progress"] = data["percent"]
            if "speed" in data and "time" in data:
                server_state["upload_stats"] = f"{data['speed']}  |  {data['time']}"
        return "OK", 200
    app.run(host='0.0.0.0', debug=False, port=5000)

#GUI Screens
def mscreen():
    global label3
    frame2.pack_forget()
    frame1.pack(fill="both", expand=True)
    clear_frame(frame1)
    Label(master=frame1,text="Welcome to File Transfer Wizard",font=myfont).pack(padx=20)
    Label(frame1, text="Scan the QR To connect with your Device: ",font=myfont1).pack(padx=20)
    Label(frame1, text=f"http://{ip}:5000 (To connect to other Computers)",font=myfont).pack(pady=10)
    label3=Label(frame1, text=f"Your File will be saved in {actual_path}",font=myfont1)
    label3.pack(pady=10)
    button(frame1, text="Change Folder", command=folder).pack(pady=10)
    customtkinter.CTkSwitch(frame1,text="Dark/Light" ,onvalue="dark",offvalue="light",variable=value,command=mode).pack(anchor="ne",padx=30)  
    qr()
    img = Image.open(qr_temp_path)
    myqr = CTkImage(light_image=img, dark_image=img, size=(250, 250))
    Label(frame1, text="", image=myqr).pack(pady=20)
    os.remove(qr_temp_path)

def Screen():
    global label4,progress_bar,progress_label,stats_label
    clear_frame(frame2)
    frame1.pack_forget()
    frame2.pack(fill="both", expand=True)
    win.after(0, ms_con)
    label4 = Label(master=frame2, text="You are Connected",font=myfont)
    label4.pack(pady=10)
    Label(frame2, text="Now You can Transfer Your Files",font=myfont1).pack(pady=10)
    Label(frame2, text="Thanks for Using",font=myfont1).pack(pady=10)
    button(frame2, text="Send (Browse)",command=open_file_dialog).pack(pady=20)
    button(frame2,text="Set Your Folder",command=folder).place(rely=0.27,relx=0.13)
    button(frame2,text="Disconnect",command=lambda:q1.put("Disconnected"),fg_color="red",text_color="white").place(rely=0.20,relx=0.13)
    button(frame2,text="Open Folder",command=open_folder).grid(row=1,column=1,padx=475,pady=165)
    progress_label = Label(frame2, text="Receiving...")
    stats_label = Label(frame2, text="")
    progress_bar = customtkinter.CTkProgressBar(frame2, width=300)
    progress_bar.set(0)
    def on_drop(event):
        files = win.tk.splitlist(event.data)
        if not files: return
        drop_zone.configure(state="normal")
        drop_zone.delete("1.0", customtkinter.END) 
        npath = []
        display_names = []
        
        for file_path in files:
            clean_path = os.path.normpath(file_path)
            npath.append(clean_path)
            filename = os.path.basename(clean_path)
            display_names.append(filename)
            drop_zone.insert(customtkinter.END,"\n\n")
            drop_zone.insert(customtkinter.END, f"📄 {filename}\n")
            
        drop_zone.configure(state="disabled")
        msg_text = f"Do you want to send '{display_names[0]}'?" if len(display_names) == 1 else f"Do you want to send these {len(display_names)} files?"
        if messagebox.askyesno("Confirm Transfer", msg_text):
            win.after(0, draganddrop, npath)
            drop_zone.configure(state="normal")
            threading.Timer(3,lambda:drop_zone.delete("1.0", customtkinter.END)).run()
            drop_zone.configure(state="disabled")
        else:
            drop_zone.configure(state="normal")
            drop_zone.delete("1.0", customtkinter.END)
            drop_zone.configure(state="disabled")
    drop_zone = customtkinter.CTkTextbox(frame2,state="disabled") #make it read-only
    drop_zone.place(rely=0.42,relx=0.66)
    label7=Label(frame2,text="Drag and Drop Here!",font=myfont1)
    label7.place(rely=0.42,relx=0.71)
    drop_zone.drop_target_register(tkinterdnd2.DND_FILES)
    drop_zone.dnd_bind('<<Drop>>', on_drop)
    qr()
    img = Image.open(qr_temp_path)
    myqr = CTkImage(light_image=img, dark_image=img, size=(250,250))
    Label(frame2,text="",image=myqr).pack(anchor="sw",padx=30,pady=30)
    os.remove(qr_temp_path)

def check_connection(q1, server_state):
    try:
        data = q1.get(timeout=0.1)
        if data == "Connected":
            win.after(0, Screen)

        elif data == "upload_success":
            pass
        elif data=="Disconnected":
            server_state['locked_ip']=None
            server_state['upload_progress']=0
            win.after(0,mscreen)
            win.after(1000,lambda:messagebox.showinfo(title="Info",message="You are Disconnected"))
    except multiprocessing.queues.Empty:
        pass
    # --- PROGRESS BAR SYNC LOGIC ---
    try:
        up_progress = server_state.get("upload_progress", 0)
        down_progress = server_state.get("download_progress", 0)
        
        if 0 < up_progress < 100:
            progress_label.place(rely=0.80, relx=0.54)
            progress_bar.place(rely=0.78, relx=0.54)
            stats_label.place(rely=0.84, relx=0.54)
            progress_bar.set(up_progress / 100.0)
            progress_label.configure(text=f"Receiving File: {up_progress}%")
            stats_label.configure(text=server_state.get("upload_stats", ""))
            
        elif up_progress == 100:
            progress_bar.set(1.0)
            progress_label.configure(text="✅ Processing File on Disk...")
            stats_label.place_forget() 
            
        elif 0 < down_progress < 100:
            progress_label.place(rely=0.80, relx=0.54)
            progress_bar.place(rely=0.78, relx=0.54)
            stats_label.place(rely=0.84, relx=0.54)
            progress_bar.set(down_progress / 100.0)
            progress_label.configure(text=f"Sending File: {down_progress}%")
            stats_label.configure(text=server_state.get("download_stats", ""))
            
        elif down_progress == 100:
            if "down_finish_time" not in server_state:
                server_state["down_finish_time"] = time.time()
            
            progress_bar.set(1.0)
            progress_label.configure(text="✅ Sent Successfully!")
            stats_label.place_forget()
            
            if time.time() - server_state["down_finish_time"] > 2.0:
                server_state["download_progress"] = 0
                del server_state["down_finish_time"]
                
        elif up_progress == 0 and down_progress == 0:
            progress_label.place_forget()
            progress_bar.place_forget()
            try:
                stats_label.place_forget()
            except NameError:
                pass
            
    except NameError:
        pass
    win.after(100, check_connection, q1, server_state)

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        server_process.terminate()
        server_process.join()
        win.destroy()

if __name__ == "__main__":
    freeze_support()
    customtkinter.set_appearance_mode(default_mode)
    manager = Manager()
    server_state = manager.dict()
    server_state["locked_ip"] = None
    q1 = Queue()
    path_queue = Queue()
    server_process = multiprocessing.Process(target=server, args=(q1, path_queue,server_state))
    server_process.start()
    win = customtkinter.CTk()
    win.title("Transfer Wizard")
    win.geometry("700x600")

    win.resizable(False, False)
    try:
        win.iconbitmap(resource_path(os.path.join("data", "icon.ico")))
    except:
        pass
    value = customtkinter.StringVar(value=default_mode)
    myfont = CTkFont(family="Arial", size=15, weight="bold")
    myfont1 = CTkFont(family="Candara", size=15)
    frame1 = Frame(win, width=700, height=600)
    frame2 = Frame(win, width=700, height=600)
    frame1.pack_propagate(False)
    frame2.pack_propagate(False)
    mscreen()
    win.after(100, check_connection, q1, server_state)
    win.protocol("WM_DELETE_WINDOW", on_closing)
    win.mainloop()