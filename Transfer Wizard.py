import multiprocessing.process
import multiprocessing.queues
from tkinter import filedialog
from tkinter.filedialog import askopenfile
from tkinter import ttk
import os
from PIL import ImageTk, Image
from tkinter import PhotoImage
import socket
from tkinter import messagebox
import segno
import customtkinter
from flask import Flask, redirect, url_for, render_template, request, send_file, session, send_from_directory,jsonify
import multiprocessing
from multiprocessing import Queue,Manager,freeze_support
from customtkinter import CTkLabel as Label ,CTkFrame as Frame,CTkButton as button ,CTkImage,filedialog,CTkProgressBar,CTkFont
import requests
import sys
from zipfile import ZipFile
import io 


app_path=os.getenv("APPDATA")
app_folder="Transfer Wizard"
config_folder=os.path.join(app_path,app_folder)

if not os.path.exists(config_folder):
    os.makedirs(f"{config_folder}/data")
    open(f"{config_folder}/data/path.txt","w")
    open(f"{config_folder}/data/mode.txt","w")
    
user=os.path.expanduser("~")
default_path=os.path.join(user,"Downloads")
try:
    with open(f"{config_folder}/data/path.txt","r") as h:
        pt=h.read()
        if pt:
            actual_path=pt
        else:
            with open(f"{config_folder}/data/path.txt","w") as h:
                h.write(default_path)
                actual_path=default_path+"(default folder)"
except FileNotFoundError:
    with open(f"{config_folder}/data/path.txt","w") as h:
        h.write(default_path)
        actual_path=default_path+"(default folder)"

default_mode="dark"
try:
    with open(f"{config_folder}/data/mode.txt","r") as h:
        md=h.read()
        if md:
            default_mode=md
        else:
            with open(f"{config_folder}/data/mode.txt","w") as h:
                h.write(default_mode)
                default_mode=default_mode
except FileNotFoundError:
    with open(f"{config_folder}/data/mode.txt","w") as h:
        h.write(default_mode)







try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
except:
    print("from socket")
    host = socket.gethostname()
    ip = socket.gethostbyname(host)

def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS2
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def open_folder():
    with open(f"{config_folder}/data/path.txt","r") as h:
        path=h.read()
        print(os.startfile(path))

def qr():
    qr = segno.make_qr(f"http://{ip}:5000")
    qr.save(resource_path(f"{config_folder}\\data\\QR.png"), scale=10)





def zip(filepath_to_send):
    zip_buffer = io.BytesIO() #create a buffer to store the zip file.
    with ZipFile(zip_buffer, 'w') as zip_file: #create a zip file in the buffer.
        for filepath in filepath_to_send: #loop through all the file paths.
            try:
                filename = os.path.basename(filepath)
                zip_file.write(filepath, filename) #add the file to the zip file.
            except FileNotFoundError:
                return f"File not found: {filepath}", 404
    zip_buffer.seek(0) #reset the buffer to the beginning.
    return zip_buffer 

l = []
def clear(frame):
    for widget in Frame.winfo_children(frame):
        widget.destroy()
        l.append(widget)
    print(l)

lfiles = list(os.listdir())


def mode():
    v=value.get()
    if v=="dark":
        customtkinter.set_appearance_mode("dark")
        with open(f"{config_folder}/data/mode.txt","w") as h:
                h.write("dark")
    else:
        customtkinter.set_appearance_mode("light")
        with open(f"{config_folder}/data/mode.txt","w") as h:
                h.write("light")

def folder():
    folder_path=filedialog.askdirectory(title="Folder to save your files?")
    if folder_path:
        with open(resource_path(f"{app_path}\\Transfer Wizard\\data\\path.txt"),"w") as t:
            t.write(folder_path)
            actual_path=folder_path
            label3.configure(text=f"Your File will be saved in {actual_path}")
            
    
def open_file_dialog():
    files = filedialog.askopenfiles(mode='r')
    if files:
        paths=[]
        for f in files:
            fl = os.path.abspath(f.name)
            paths.append(fl)
        try:
                headers = {'Content-Type': 'application/json'}
                response = requests.post(f"http://{ip}:5000/set_filepath",headers=headers, json={"filepath": paths}) #send the file path as json
                if response.status_code == 200:
                    print("File path sent successfully")
                else:
                    print(f"Error sending file path: {response.status_code}")
                    messagebox.showerror("Error", "Error sending file path.")

        except requests.exceptions.RequestException as e:
                print(f"Error sending file path: {e}")
                messagebox.showerror("Error", "Error sending file path, check console.")

    else:
        messagebox.showinfo("No file selected", "Please select a file to send")


def mscreen():
    global label3
    frame2.pack_forget()
    frame1.pack(fill="both",expand=True)
    frame1.tkraise()
    frame1.pack_propagate(False)
    label1=Label(master=frame1,text="Welcome to File Transfer Wizard",font=myfont)
    label1.pack(padx=20)
    label2 = Label(frame1, text="Scan the QR To connect with your Device: ",font=myfont1)
    label2.pack(pady=20)
    label4 = Label(frame1, text=f"http://{ip}:5000 (To connect to other Computers)",font=myfont)
    label4.pack(pady=10)
    label3 = Label(frame1, text=f"Your File will be saved in {actual_path}",font=myfont1)
    label3.pack(pady=10)
    bt1=button(frame1,text="Set a Folder",command=folder).pack(pady=20)
    qr()
    customtkinter.CTkSwitch(frame1,text="Dark/Light" ,onvalue="dark",offvalue="light",variable=value,command=mode).pack(anchor="ne",padx=30)
    img = Image.open(resource_path(f"{config_folder}\\data\\QR.png"))
    myqr = CTkImage(light_image=img,dark_image=img,size=(250,250))
    label2=Label(frame1,text="",image=myqr).pack(pady=20)
    os.remove(resource_path(f"{config_folder}\\data\\QR.png"))

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        server_process.terminate()
        server_process.join()
        win.destroy()


def Screen():
    print("here in screen")
    frame1.pack_forget()
    frame2.pack(fill="both",expand=True)
    frame2.pack_propagate(False)
    label4 = Label(master=frame2, text="You are Connected",font=myfont).pack(pady=10)
    label5 = Label(frame2, text="Now You can Transfer Your Files",font=myfont1).pack(pady=10)
    label6 = Label(frame2, text="Thanks for Using",font=myfont1).pack(pady=10)
    customtkinter.CTkSwitch(frame1,text="Dark/Light" ,onvalue="dark",offvalue="light",variable=value,command=mode).pack(anchor="ne",padx=30)
    bt4=button(frame2, text="Send",command=open_file_dialog).pack(pady=20)
    bt5=button(frame2,text="Set Your Folder",command=folder).place(rely=0.27,relx=0.13)
    bt5=button(frame2,text="Open Folder",command=open_folder).grid(row=1,column=1,padx=475,pady=165)
    qr()
    img = Image.open(resource_path(f"{config_folder}\\data\\QR.png"))
    myqr = CTkImage(light_image=img,dark_image=img,size=(250,250))
    label2=Label(frame2,text="",image=myqr).pack(anchor="sw",padx=30,pady=30)
    os.remove(resource_path(f"{config_folder}\\data\\QR.png"))

def f2():
    ttk.Button(command=Screen())

def msg():
    messagebox.showinfo("Received","Received Successfuly.Saved In Your Folder")

def server(q1):
    app = Flask(__name__)
    @app.route("/")
    def router():
        return redirect(url_for("home"))
    @app.route('/home')
    def home():
        q1.put("Connected")
        return render_template("Home.html")
    @app.route("/qer")
    def qer():
        print("qer called")
        q1.put("send file")
        return "hello"
    
    @app.route('/set_filepath', methods=['POST','GET'])
    def set_filepath():
        global filepath_to_send
        data = request.get_json()
        if data and "filepath" in data:
            filepath_to_send = data["filepath"]
            print(type(filepath_to_send))   
            print("file path received",filepath_to_send)
            url=f"http://{ip}:5000/snd"
            return "File path received successfully", 200 # Modified to return simple success string

        else:
            return jsonify({"error": "Invalid request"}), 400

    @app.route('/snd')
    def snd():
        global filepath_to_send
        try:
            if filepath_to_send:
                if len(filepath_to_send)>1:
                    zip_buffer=zip(filepath_to_send)
                    return send_file(zip_buffer, as_attachment=True, download_name='files.zip')
                else:
                    return send_file(filepath_to_send[0],as_attachment=True)
            else:
                return "No files selected", 400
        except:
            return render_template("not.html")

    @app.route('/Receive')
    def Receive():
        return render_template("receive.html")


    @app.route('/Send')
    def Send():
        return render_template("Upload.html")



    @app.route('/upload', methods=["POST"])
    def upload():
        if request.method == "POST":
            with open(resource_path(f"{app_path}\\Transfer Wizard\\data\\path.txt"),"r") as t: 
                path=t.readline()
                if path:
                    try:
                        files = request.files.getlist("file")
                        if files:
                            for f in files:
                                f.save(f"{path}/{f.filename}")
                            a=multiprocessing.Process(target=msg)
                            a.start()
                            return jsonify({"message": "Files uploaded successfully", "filenames": f.filename}), 200
                        else:
                            return jsonify({"error": "No files were selected"}), 400
                    except Exception as e:
                        return jsonify({"error": str(e)}), 500
                else:
                    return jsonify({"error": "Upload path not configured"}), 400 
    app.run(host='0.0.0.0', debug=False, port=5000)


def check_connection(q1):
    l = os.listdir()
    try:
        data=q1.get(timeout=0.1)
        if data=="Connected":
            print("Connected")
            win.after(0, Screen)  
            return  
    except multiprocessing.queues.Empty:
        pass
    win.after(100, check_connection,q1)

if (__name__) == "__main__":
        freeze_support()
        q1=Queue()
        server_process = multiprocessing.Process(target=server,args=(q1,))
        server_process.start()
        win = customtkinter.CTk()
        win.title("Transfer Wizard")
        win.geometry("700x600")
        win.maxsize(width=700,height=600)
        win.minsize(width=700,height=600)
        customtkinter.set_appearance_mode(default_mode)
        value=customtkinter.StringVar(value=default_mode)
        frame1 = Frame(win, width=700, height=600)
        frame2 = Frame(win, width=700, height=600)
        myfont=CTkFont(family="Arial",size=15,weight="bold",slant="roman")
        myfont1=CTkFont(family="Candara",size=15,slant="roman")
        win.iconbitmap(resource_path("data\\icon.ico"))
        mscreen()
        win.after(100,check_connection,q1)
        win.protocol("WM_DELETE_WINDOW", on_closing)
        win.mainloop()
