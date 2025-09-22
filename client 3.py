import base64
import io
import os
from customtkinter import *
import threading
from socket import socket, AF_INET, SOCK_STREAM
from PIL import Image


class MainWindow(CTk):
    def __init__(self):
        super().__init__()
        self.geometry("500x400")
        self.title("LogiTalk")
        self.label = None
        self.entry = None
        self.save_btn = None
        self.username = "Bonsen"
        self.configure(fg_color="#1E1A2E")

        self.menu_frame = CTkFrame(self, width=30, height=self.winfo_height(), fg_color="#2E2447")
        self.menu_frame.pack_propagate(False)
        self.menu_frame.place(x=0, y=0)

        self.is_show_menu = False
        self.speed_animate_menu = -5

        self.btn = CTkButton(self, text='▶️', width=30, fg_color="#6A0DAD", hover_color="#944DDB", command=self.toggle_show_menu)
        self.btn.place(x=0, y=0)

        self.message_entry = CTkEntry(self, placeholder_text="Надіслати повідомлення", height=40, fg_color="#2E2447", border_color="#6A0DAD", text_color="white")
        self.message_entry.place(x=0, y=0)

        self.send_button = CTkButton(self, text=">", width=50, height=40, fg_color="#6A0DAD", hover_color="#944DDB", command=self.send_message)
        self.send_button.place(x=0, y=0)

        self.open_img_button = CTkButton(self, text='📂', width=50, height=40, fg_color="#6A0DAD", hover_color="#944DDB", command=self.open_image)
        self.open_img_button.place(x=0, y=0)

        self.chat_field = CTkScrollableFrame(self, fg_color="#1E1A2E")
        self.chat_field.place(x=0, y=0)

        self.addaptive_ui()

        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(("0.tcp.ngrok.io", 15105))
            hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався(лась) до чату!\n"
            self.sock.send(hello.encode('utf-8'))
            threading.Thread(target=self.recv_message, daemon=True).start()
        except Exception as e:
            self.add_message(f"Не вдалося підключитися до сервера: {e}")

    def addaptive_ui(self):
        self.menu_frame.configure(height=self.winfo_height())
        self.chat_field.place(x=self.menu_frame.winfo_width(), y=0)
        self.chat_field.configure(
            width=self.winfo_width() - self.menu_frame.winfo_width() - 20,
            height=self.winfo_height() - 40
        )

        self.send_button.place(x=self.winfo_width() - 50, y=self.winfo_height() - 40)
        self.message_entry.place(x=self.menu_frame.winfo_width(), y=self.send_button.winfo_y())
        self.message_entry.configure(
            width=self.winfo_width() - self.menu_frame.winfo_width() - self.send_button.winfo_width() - 55
        )
        self.open_img_button.place(x=self.winfo_width() - 105, y=self.send_button.winfo_y())
        self.after(50, self.addaptive_ui)

    def toggle_show_menu(self):
        if self.is_show_menu:
            self.is_show_menu = False
            self.speed_animate_menu *= -1
            self.btn.configure(text='▶️')
            self.show_menu()
        else:
            self.is_show_menu = True
            self.speed_animate_menu *= -1
            self.btn.configure(text='◀️')
            self.show_menu()

            self.label = CTkLabel(self.menu_frame, text='Імʼя', text_color="white")
            self.label.pack(pady=30)

            self.entry = CTkEntry(self.menu_frame, fg_color="#2E2447", border_color="#6A0DAD", text_color="white")
            self.entry.pack()

            self.save_btn = CTkButton(self.menu_frame, text="Зберегти", fg_color="#6A0DAD", hover_color="#944DDB", command=self.save_name)
            self.save_btn.pack(pady=10)

    def show_menu(self):
        self.menu_frame.configure(width=self.menu_frame.winfo_width() + self.speed_animate_menu)
        if self.menu_frame.winfo_width() <= 200 and self.is_show_menu:
            self.after(10, self.show_menu)
        elif self.menu_frame.winfo_width() >= 40 and not self.is_show_menu:
            self.after(10, self.show_menu)
            if self.label and self.entry and self.save_btn:
                self.label.destroy()
                self.entry.destroy()
                self.save_btn.destroy()

    def save_name(self):
        new_name = self.entry.get().strip()
        if new_name:
            self.username = new_name
            self.add_message(f"Ваш новий нік: {self.username}", is_self=True)

    def add_message(self, text, img=None, is_self=False):
        bg_color = "#944DDB" if is_self else "#2E2447"

        message_frame = CTkFrame(self.chat_field, fg_color=bg_color, corner_radius=15)
        message_frame.pack(pady=5, anchor='e' if is_self else 'w')

        wraplength_size = self.winfo_width() - self.menu_frame.winfo_width() - 60

        if not img:
            CTkLabel(
                message_frame,
                text=text,
                wraplength=wraplength_size,
                text_color="white",
                justify="left"
            ).pack(padx=10, pady=5)
        else:
            CTkLabel(
                message_frame,
                text=text,
                wraplength=wraplength_size,
                text_color="white",
                image=img,
                compound="top",
                justify="left"
            ).pack(padx=10, pady=5)

    def send_message(self):
        text = self.message_entry.get()
        if text:
            self.add_message(self.username + ":" + text, is_self=True)
            data = f"TEXT@{self.username}@{text}\n"
            try:
                self.sock.send(data.encode('utf-8'))
            except:
                pass
            self.message_entry.delete(0, END)

    def recv_message(self):
        buffer = ""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode('utf-8', errors='ignore')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    self.handle_line(line.strip())
            except:
                break

    def handle_line(self, line):
        if not line:
            return

        parts = line.split("@", 3)
        msg_type = parts[0]
        if msg_type == "TEXT":
            if len(parts) >= 3:
                autor = parts[1]
                message = parts[2]
                self.add_message(f"{autor}: {message}")
        elif msg_type == "IMAGE":
            if len(parts) >= 4:
                autor = parts[1]
                filename = parts[2]
                img = parts[3]
                try:
                    img_data = base64.b64decode(img)
                    pil_img = Image.open(io.BytesIO(img_data))
                    ctk_tk = CTkImage(pil_img, size=(300, 300))
                    self.add_message(f"{autor}: Надіслав зображення {filename}", img=ctk_tk)
                except Exception:
                    self.add_message("Помилка відобрадення зображення")

    def open_image(self):
        file_name = filedialog.askopenfilename()
        if not file_name:
            return
        try:
            with open(file_name, 'rb') as f:
                raw = f.read()

            b64 = base64.b64encode(raw).decode()
            short_name = os.path.basename(file_name)
            data = f"IMAGE@{self.username}@{short_name}@{b64}\n"
            self.sock.send(data.encode())
            self.add_message(" ", CTkImage(light_image=Image.open(file_name), size=(300, 300)), is_self=True)
        except Exception:
            self.add_message("Не вдалося надіслати зображення")


if __name__ == "__main__":
    win = MainWindow()
    win.mainloop()
