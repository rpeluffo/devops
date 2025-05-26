import os
import subprocess
import pyperclip
import tkinter as tk
from tkinter import messagebox, filedialog
import time
import threading
from pathlib import Path

HOME = Path.home()
CONFIG_DIR = HOME / ".securid_token"
USER_CONFIG = CONFIG_DIR / "user"
ADMIN_CONFIG = CONFIG_DIR / "admin"

CONFIG_DIR.mkdir(exist_ok=True)

def read_token_path(role):
    path_file = USER_CONFIG if role == "user" else ADMIN_CONFIG
    if path_file.exists():
        return path_file.read_text().strip()
    return None

def save_token_path(role, path):
    path_file = USER_CONFIG if role == "user" else ADMIN_CONFIG
    path_file.write_text(path)

def configure_token(role):
    file_path = filedialog.askopenfilename(title=f"Select {role} token file")
    if file_path:
        save_token_path(role, file_path)
        messagebox.showinfo("Saved", f"{role.capitalize()} token path saved:\n{file_path}")

def generate_token(role):
    token_path = read_token_path(role)
    if not token_path or not os.path.isfile(token_path):
        messagebox.showerror("Error", f"No valid token file configured for {role}. Please configure it first.")
        return
    try:
        result = subprocess.run(
            ["securid", "-f", token_path],
            capture_output=True,
            text=True,
            check=True
        )
        token = result.stdout.strip()
        pyperclip.copy(token)
        show_token_popup(token)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Token generation failed:\n{e.stderr.strip()}")

def show_token_popup(token):
    popup = tk.Toplevel()
    popup.title("RSA Token")
    popup.geometry("300x120")

    tk.Label(popup, text="Token copied to clipboard:", font=("Arial", 10)).pack(pady=5)

    # Use Text widget to allow text selection
    text_widget = tk.Text(popup, height=1, font=("Courier", 12))
    text_widget.insert(tk.END, token)
    text_widget.config(state=tk.DISABLED)
    text_widget.pack(pady=5, padx=10)

    def copy_to_clipboard():
        pyperclip.copy(token)
        messagebox.showinfo("Copied", "Token copied to clipboard!")

    tk.Button(popup, text="Copy Token", command=copy_to_clipboard).pack(pady=5)

    def close_popup():
        time.sleep(15)
        popup.destroy()

    threading.Thread(target=close_popup, daemon=True).start()

# Main window
root = tk.Tk()
root.title("RSA Token Generator")
root.geometry("320x160")

tk.Label(root, text="Generate token for:", font=("Arial", 12)).grid(row=0, column=0, columnspan=3, pady=10)

# User row
tk.Button(root, text="User", width=12, command=lambda: generate_token("user")).grid(row=1, column=0, padx=10, pady=5)
tk.Button(root, text="⚙️", width=3, command=lambda: configure_token("user")).grid(row=1, column=1)

# Admin row
tk.Button(root, text="Admin", width=12, command=lambda: generate_token("admin")).grid(row=2, column=0, padx=10, pady=5)
tk.Button(root, text="⚙️", width=3, command=lambda: configure_token("admin")).grid(row=2, column=1)

root.mainloop()
