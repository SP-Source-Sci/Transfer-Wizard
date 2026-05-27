# Transfer Wizard 🧙‍♂️

Transfer Wizard is a Python-based desktop application that makes transferring files between your computer and mobile device (or another computer) across a local Wi-Fi network incredibly simple. It spins up a local Flask web server and generates a QR code—just scan it with your phone to start sending and receiving files instantly, no cables required!

## ✨ Features

* 📱 **QR Code Pairing:** Instantly connect your mobile device by scanning the automatically generated QR code. No need to manually type IP addresses.
* 🔒 **Secure IP Locking:** Once a device connects, the local server locks to that specific IP address. Any other device attempting to connect will receive a 403 Forbidden error, keeping your transfer session private.
* 📁 **Drag & Drop Support:** Easily queue files for transfer by dragging them directly into the designated drop zone.
* ⚡ **On-the-Fly Zipping:** Sending multiple files? The app automatically bundles them into an uncompressed ZIP file in your system's temp folder to save RAM and minimize processing time before streaming.
* 📊 **Real-Time Stats:** View live progress bars, transfer speeds, and estimated time remaining (ETA) directly in the desktop UI for both uploads and downloads.
* 🎨 **Modern GUI:** Built with `customtkinter`, featuring a clean interface with a built-in Dark/Light mode toggle.
* ⚙️ **Persistent Configurations:** Remembers your preferred save directory and theme preferences across sessions (stored in `~/.transfer_wizard/config.json`).

---

## 🛠️ Prerequisites

Ensure you have **Python 3.8 or higher** installed. You will also need to install the required external libraries.

You can install the dependencies using `pip`:

```bash
pip install Flask Werkzeug customtkinter tkinterdnd2 Pillow segno

```

*Note: Standard library modules like `os`, `sys`, `socket`, `multiprocessing`, `json`, and `zipfile` are used extensively but do not require separate installation.*

---

## 🚀 Installation & Setup

1. **Clone or Download the Repository:**
Ensure you download the main Python script (`Transfer Wizard.py`) along with its required web assets.
2. **Directory Structure:**
Because the script uses Flask to serve web pages to the connecting device, ensure your project folder looks like this:
```text
├── Transfer Wizard.py
├── data/
│   └── icon.ico             # Desktop app icon
├── static/                  # CSS/JS for the Flask server (Required)
└── templates/               # HTML files (Home.html, Upload.html, etc.) (Required)

```


*(Note: The script expects `templates` and `static` folders to exist in the exact directory from which it is run to serve the web interface properly.)*

---

## 💻 How to Use

1. **Run the Application:**
Launch the application via your terminal or command prompt:
```bash
python "Transfer Wizard.py"

```


2. **Connect Your Device:**
* Upon launching, the app will display a QR code and a local URL (e.g., `http://192.168.X.X:5000`).
* **Mobile:** Scan the QR code using your phone's camera.
* **PC:** Type the displayed URL into another computer's web browser on the same network.


3. **Transfer Files:**
* **Sending to Phone:** Click "Send (Browse)" to open a file dialog, or drag and drop files into the app. Accept the confirmation prompt, and the file will immediately begin downloading on the connected device.
* **Receiving from Phone:** Use the web interface on your connected device to select and upload files to your PC.


4. **Manage Files:**
* Click "Open Folder" in the desktop app to instantly view your received files.
* Click "Change Folder" to set a custom download destination.


5. **Disconnect:**
* Click "Disconnect" to kick the current device, free up the IP lock, and return to the QR code screen to connect a new device.



---

## ⚙️ How it Works (Under the Hood)

* **Multiprocessing:** The app runs the `customtkinter` UI on the main process and spins up the `Flask` server on a separate daemonized background process. They communicate using a `multiprocessing.Queue` and a `Manager().dict()` for real-time state sharing (like progress bar updates).
* **Streaming:** Instead of loading large files into memory, the Flask server uses generator functions (`yield`) to stream file chunks directly over the network, ensuring low memory usage even for multi-gigabyte files.
* **Networking:** The app uses Python's `socket` library to ping `8.8.8.8` to dynamically determine your machine's local IPv4 address for hosting the Flask server.