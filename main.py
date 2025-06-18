import tkinter as tk
from tkinter import messagebox, filedialog
import os
import json
import uuid
from cryptography.fernet import Fernet
import base64
import hashlib
import random
import string
import shutil

def generate_key(master_password):
    return base64.urlsafe_b64encode(hashlib.sha256(master_password.encode()).digest())

def encrypt_data(data, key):
    f = Fernet(key)
    return f.encrypt(data.encode())

def decrypt_data(data, key):
    f = Fernet(key)
    return f.decrypt(data).decode()

def generate_password(length):
    chars = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choice(chars) for _ in range(length))

class PasswordManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Şifre Yöneticisi")
        self.root.geometry("500x500")
        self.master_password = None
        self.data = []
        self.login_attempts = 5
        self.folder_path = None
        self.meta_path = None
        self.data_path = None

        if not os.path.exists("config.json"):
            self.select_folder()
        else:
            with open("config.json", "r") as f:
                paths = json.load(f)
                self.folder_path = paths["folder"]
                self.meta_path = os.path.join(self.folder_path, "meta.json")
                self.data_path = os.path.join(self.folder_path, "data.dat")
            if not os.path.exists(self.meta_path):
                self.setup_screen()
            else:
                self.login_screen()

    def select_folder(self):
        messagebox.showinfo("Klasör Seç", "Lütfen şifre verilerinin saklanacağı klasörü seçin.")
        folder = filedialog.askdirectory(title="Klasör Seç")
        if not folder:
            messagebox.showerror("Hata", "Klasör seçilmedi. Uygulama kapanıyor.")
            self.root.destroy()
            return
        self.folder_path = folder
        self.meta_path = os.path.join(folder, "meta.json")
        self.data_path = os.path.join(folder, "data.dat")
        with open("config.json", "w") as f:
            json.dump({"folder": self.folder_path}, f)
        self.setup_screen()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def setup_screen(self):
        self.clear_screen()
        tk.Label(self.root, text="Kurulum", font=("Helvetica", 18)).pack(pady=10)
        tk.Label(self.root, text="Master Şifre:").pack()
        mp1_entry = tk.Entry(self.root, show="*")
        mp1_entry.pack()
        tk.Label(self.root, text="Master Şifre (Tekrar):").pack()
        mp2_entry = tk.Entry(self.root, show="*")
        mp2_entry.pack()
        tk.Label(self.root, text="Şifrenizi unutursanız tüm veriler silinir.", fg="red").pack(pady=10)

        def save_setup():
            mp1 = mp1_entry.get()
            mp2 = mp2_entry.get()
            if not mp1 or mp1 != mp2:
                messagebox.showerror("Hata", "Şifreler boş olamaz ve eşleşmeli.")
                return
            hashed = hashlib.sha256(mp1.encode()).hexdigest()
            with open(self.meta_path, "w") as f:
                json.dump({"master": hashed}, f)
            with open(self.data_path, "wb") as f:
                f.write(b"")
            messagebox.showinfo("Başarılı", "Kurulum tamamlandı.")
            self.login_screen()

        tk.Button(self.root, text="Kur", width=20, height=2, command=save_setup).pack(pady=10)

    def login_screen(self):
        self.clear_screen()
        tk.Label(self.root, text="Giriş", font=("Helvetica", 18)).pack(pady=10)
        tk.Label(self.root, text=f"Kalan Deneme: {self.login_attempts}").pack()
        tk.Label(self.root, text="Master Şifre:").pack()
        mp_entry = tk.Entry(self.root, show="*")
        mp_entry.pack()

        def login():
            with open(self.meta_path, "r") as f:
                meta = json.load(f)
            if hashlib.sha256(mp_entry.get().encode()).hexdigest() == meta.get("master"):
                self.master_password = mp_entry.get()
                self.load_data()
                self.main_menu()
            else:
                self.login_attempts -= 1
                if self.login_attempts <= 0:
                    confirm = messagebox.askyesno("Veriler Silinecek", "Tüm veriler silinsin mi?")
                    if confirm:
                        self.reset_app()
                else:
                    messagebox.showerror("Hata", f"Yanlış şifre! Kalan hakkınız: {self.login_attempts}")
                    self.login_screen()

        def forgot_password():
            confirm = messagebox.askyesno("Veriler Silinecek", "Şifrenizi unuttuysanız tüm veriler silinecek. Devam edilsin mi?")
            if confirm:
                self.reset_app()

        tk.Button(self.root, text="Giriş", command=login, width=20, height=2).pack(pady=5)
        tk.Button(self.root, text="Şifremi Unuttum", command=forgot_password, width=20, height=2).pack()

    def reset_app(self):
        try:
            if os.path.exists("config.json"):
                os.remove("config.json")
            if self.folder_path and os.path.exists(self.folder_path):
                for file in os.listdir(self.folder_path):
                    if file.endswith(".dat") or file.endswith(".json"):
                        os.remove(os.path.join(self.folder_path, file))
        except:
            pass
        self.login_attempts = 5
        messagebox.showinfo("Sıfırlandı", "Uygulama sıfırlandı.")
        self.select_folder()

    def load_data(self):
        if not os.path.exists(self.data_path):
            self.data = []
            return
        with open(self.data_path, "rb") as f:
            encrypted = f.read()
        if not encrypted:
            self.data = []
            return
        try:
            decrypted = decrypt_data(encrypted, generate_key(self.master_password))
            self.data = json.loads(decrypted)
        except:
            messagebox.showerror("Hata", "Veri okunamadı. Şifre yanlış olabilir.")
            self.data = []

    def save_data(self):
        key = generate_key(self.master_password)
        data_str = json.dumps(self.data)
        encrypted = encrypt_data(data_str, key)
        with open(self.data_path, "wb") as f:
            f.write(encrypted)

    def main_menu(self):
        self.clear_screen()
        tk.Label(self.root, text="Ana Menü", font=("Helvetica", 18)).pack(pady=10)
        tk.Button(self.root, text="Şifreleri Yönet", width=25, height=2, command=self.manage_passwords).pack(pady=5)
        tk.Button(self.root, text="Şifre Oluştur", width=25, height=2, command=self.password_generator).pack(pady=5)
        tk.Button(self.root, text="Çıkış", width=25, height=2, command=self.root.quit).pack(pady=5)

    def password_generator(self):
        self.clear_screen()
        tk.Label(self.root, text="Şifre Oluşturucu", font=("Helvetica", 18)).pack(pady=10)
        tk.Label(self.root, text="Uzunluk (4-32):").pack()
        length_entry = tk.Entry(self.root)
        length_entry.pack()
        result = tk.Entry(self.root, width=40)
        result.pack(pady=10)

        def generate():
            try:
                length = int(length_entry.get())
                if 4 <= length <= 32:
                    result.delete(0, tk.END)
                    result.insert(0, generate_password(length))
                else:
                    raise ValueError
            except:
                messagebox.showerror("Hata", "Geçerli uzunluk girin!")

        tk.Button(self.root, text="Oluştur", command=generate, width=20, height=2).pack(pady=5)
        tk.Button(self.root, text="Ana Menü", command=self.main_menu, width=20, height=2).pack()

    def manage_passwords(self):
        self.clear_screen()
        tk.Label(self.root, text="Şifreleri Yönet", font=("Helvetica", 18)).pack(pady=10)

        frame = tk.Frame(self.root)
        frame.pack()

        tk.Label(frame, text="Site:").grid(row=0, column=0)
        site_entry = tk.Entry(frame)
        site_entry.grid(row=0, column=1)

        tk.Label(frame, text="Kullanıcı:").grid(row=1, column=0)
        user_entry = tk.Entry(frame)
        user_entry.grid(row=1, column=1)

        tk.Label(frame, text="Parola:").grid(row=2, column=0)
        pass_entry = tk.Entry(frame)
        pass_entry.grid(row=2, column=1)

        listbox = tk.Listbox(self.root, width=60)
        listbox.pack(pady=10)

        def refresh():
            listbox.delete(0, tk.END)
            for item in self.data:
                listbox.insert(tk.END, f"{item['site']} | {item['user']} | {'*' * len(item['password'])}")

        def add_entry():
            site, user, pw = site_entry.get(), user_entry.get(), pass_entry.get()
            if not site or not user or not pw:
                messagebox.showerror("Hata", "Tüm alanları doldurun.")
                return
            self.data.append({
                "id": str(uuid.uuid4()),
                "site": site,
                "user": user,
                "password": pw
            })
            self.save_data()
            site_entry.delete(0, tk.END)
            user_entry.delete(0, tk.END)
            pass_entry.delete(0, tk.END)
            refresh()

        def delete_entry():
            index = listbox.curselection()
            if index:
                del self.data[index[0]]
                self.save_data()
                refresh()

        def show_password():
            index = listbox.curselection()
            if index:
                pw = self.data[index[0]]['password']
                messagebox.showinfo("Parola", pw)

        tk.Button(self.root, text="Ekle", command=add_entry, width=20, height=2).pack()
        tk.Button(self.root, text="Sil", command=delete_entry, width=20, height=2).pack()
        tk.Button(self.root, text="Parolayı Göster", command=show_password, width=20, height=2).pack()
        tk.Button(self.root, text="Ana Menü", command=self.main_menu, width=20, height=2).pack(pady=5)

        refresh()

if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordManager(root)
    root.mainloop()
