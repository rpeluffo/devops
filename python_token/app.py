import os
from securid import Token
from datetime import datetime
import xml.etree.ElementTree as ET
import base64
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
    token_file = (USER_CONFIG if role == "user" else ADMIN_CONFIG) / "rsa_token.id"
    if token_file.exists():
        return str(token_file)
    return None

def save_token_path(role, original_file_path):
    dest_dir = USER_CONFIG if role == "user" else ADMIN_CONFIG
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_file = dest_dir / "rsa_token.id"
    token_content = Path(original_file_path).read_bytes()
    dest_file.write_bytes(token_content)

def configure_token(role):
    file_path = filedialog.askopenfilename(title=f"Select {role} token file")
    if file_path:
        save_token_path(role, file_path)

        # Show the actual saved path
        saved_path = (USER_CONFIG if role == "user" else ADMIN_CONFIG) / "rsa_token.id"
        messagebox.showinfo("Saved", f"{role.capitalize()} token saved to:\n{saved_path}")

        # Update the checkmark label after saving new token
        update_checkmark(role)

def generate_token(role):
    token_path = read_token_path(role)
    if not token_path or not os.path.isfile(token_path):
        print(f"[ERROR] No valid token file configured for {role}. Please configure it first.")
        return
    try:
        tree = ET.parse(token_path)
        root = tree.getroot()
        
        tkn = root.find('TKN')
        header = root.find('TKNHeader')

        serial = tkn.find('SN').text.strip()

        seed_b64 = tkn.find('Seed').text.strip()
        seed = base64.b64decode(seed_b64)

        interval = int(header.find('DefInterval').text.strip())
        digits = int(header.find('DefDigits').text.strip())

        exp_date_str = header.find('DefDeath').text.strip()
        exp_date = datetime.strptime(exp_date_str, "%Y/%m/%d").date()
        token = Token(
            serial=serial,
            seed=seed,
            interval=interval,
            digits=digits,
            exp_date=exp_date
        )
        code = token.generate_otp(datetime.now())
        pyperclip.copy(code)
        show_token_popup(role,serial,code)
    except Exception as e:
        print(f"[ERROR] Token generation failed: {str(e)}")


def show_token_popup(role,serial,token):
    popup = tk.Toplevel()
    popup.title("RSA Token")
    popup.geometry("300x200")

    tk.Label(popup, text=f"Role: {role.capitalize()}", font=("Arial", 10)).pack(pady=5)
    tk.Label(popup, text=f"Serial: {serial}", font=("Arial", 10)).pack(pady=5)
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

def update_checkmark(role):
    token_path = read_token_path(role)
    label = check_labels[role]
    if token_path and os.path.isfile(token_path):
        label.config(text="✅", fg="green")
    else:
        label.config(text="")

# Main window
root = tk.Tk()
root.title("RSA Token Generator")
root.geometry("250x160")  # Reduced width

tk.Label(root, text="Generate token for:", font=("Arial", 12)).grid(row=0, column=0, columnspan=3, pady=10)

check_labels = {}

# User row
tk.Button(root, text="User", width=10, command=lambda: generate_token("user")).grid(row=1, column=0, padx=(5,3), pady=5, sticky='w')
tk.Button(root, text="⚙️", width=2, command=lambda: configure_token("user")).grid(row=1, column=1, padx=(0,3), pady=5, sticky='w')
check_labels["user"] = tk.Label(root, text="", font=("Arial", 14))
check_labels["user"].grid(row=1, column=2, padx=(0,5), pady=5, sticky='w')

# Admin row
tk.Button(root, text="Admin", width=10, command=lambda: generate_token("admin")).grid(row=2, column=0, padx=(5,3), pady=5, sticky='w')
tk.Button(root, text="⚙️", width=2, command=lambda: configure_token("admin")).grid(row=2, column=1, padx=(0,3), pady=5, sticky='w')
check_labels["admin"] = tk.Label(root, text="", font=("Arial", 14))
check_labels["admin"].grid(row=2, column=2, padx=(0,5), pady=5, sticky='w')

# Initialize checkmarks on startup
update_checkmark("user")
update_checkmark("admin")

root.mainloop()
