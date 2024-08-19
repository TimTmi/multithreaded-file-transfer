import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
from blinker import signal
from os import path
from CTkListbox import *
from time import sleep
import threading
import ipaddress
import time
import os
from humanize import naturalsize

import filetransferclient


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.protocol('WM_DELETE_WINDOW', self.close)

        self.iconbitmap(default=path.join("images", "wingfoot.ico"))
        self.geometry("500x600")
        self.resizable(False, False)
        self.title("Hermes Hub")

        container = ctk.CTkFrame(master=self)
        container.pack(fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        arguments = (container, self)
        self.main_frame = MainFrame(*arguments)
        self.upload_frame = UploadFrame(*arguments)
        self.uploaded_files_frame = UploadedFilesFrame(*arguments)
        self.settings_frame = SettingsFrame(*arguments)
        self.credits_frame = CreditsFrame(*arguments)

        self.current_frame = self.main_frame

        for i in (self.main_frame, self.upload_frame, self.uploaded_files_frame, self.settings_frame, self.credits_frame):
            i.grid(row=0, column=0, sticky="nsew")

        self.show_frame(self.main_frame)

        self.server_active: bool = False
        self.server_ip: str = ftc.get_local_host()
        self.chunks: int = 4

        self.status_label = ctk.CTkLabel(
            master=self,
            text="Server Status: ",
            font=('Segoe UI', 14, 'bold'),
            padx=3,
            pady=3
        )
        self.status_label.place(relx=1.0, rely=0.0, anchor='ne', x=-50, y=0)

        self.status_online_label = ctk.CTkLabel(
            master=self,
            text="Online",
            font=('Segoe UI', 14, 'bold'),
            text_color='green',
            padx=4,
            pady=4
        )
        self.status_online_label.place(relx=1.0, rely=0.0, anchor='ne', x=-1, y=0)

        self.status_offline_label = ctk.CTkLabel(
           master=self,
           text="Offline",
           font=('Segoe UI', 14, 'bold'),
           text_color='red',
           padx=3,
           pady=3
        )
        self.status_offline_label.place(relx=1.0, rely=0.0, anchor='ne', x=-1, y=0)

        self.pinging: bool = True
        self.ping_thread = threading.Thread(target=self.ping)
        self.ping_thread.start()

    def ping(self):
        while self.pinging:
            if not self.server_active and ftc.ping():
                self.server_active = True
                self.status_online_label.tkraise()
                self.show_notification("Connected to server")
            elif self.server_active and not ftc.ping():
                self.server_active = False
                self.uploaded_files_frame.refresh()
                self.status_offline_label.tkraise()
                self.show_notification("Lost connection to server")
                if self.current_frame is self.upload_frame or self.current_frame is self.uploaded_files_frame:
                    self.show_frame(self.main_frame)
            sleep(1)

    def show_frame(self, frame: ctk.CTkFrame):
        self.current_frame = frame
        if hasattr(frame, 'refresh'):
            frame.refresh()
        frame.tkraise()
    
    def create_return_button(self, master, command=None):
        if command is None:
            command = lambda: app.show_frame(app.main_frame)
        return_button = ctk.CTkButton(
            master=master,
            text="",
            width=1,
            image=ctk.CTkImage(
                light_image=Image.open(path.join("images", "return.png")),
                size=(32,32)
            ),
            command=command
        )

        return return_button

    # def center_widget(self, widget: ctk.CTkBaseClass):
    #     widget.update_idletasks()
    #     window_width = widget.winfo_width()
    #     window_height = widget.winfo_height()
    #     screen_width = widget.winfo_screenwidth()
    #     screen_height = widget.winfo_screenheight()

    #     x = (screen_width - window_width) // 2
    #     y = (screen_height - window_height) // 2

    #     widget.place(x=x, y=y)
    
    def show_notification(self, text: str):
        notification = SlideInNotification(self, text=text)
        self.after(5000, notification.destroy)

    def truncate_text(self, text, max_length):
            if len(text) > max_length:
                return text[:max_length-3] + "..."
            return text

    def close(self):
        self.pinging = False
        self.ping_thread.join()
        self.destroy()



class MainFrame(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, app: App):
        super().__init__(master=parent)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        frame1 = ctk.CTkFrame(
            master=self,
            fg_color="transparent"
        )
        frame1.grid(
            row=0
        )

        title = ctk.CTkLabel(
            master=frame1,
            text = '',
            image=ctk.CTkImage(
                light_image=Image.open(path.join("images", "wingfootTitle.png")),
                size=(250,250)
            ),
        )
        title.pack(
            padx=16, pady=16,
            expand = True
        )

        frame2 = ctk.CTkFrame(master=self,width=512,height=128+16)
        frame2.grid(
            row=1,
            padx=16
        )
        frame2.grid_columnconfigure(0, weight=1)
        frame2.grid_propagate(False)

        def _upload_button_pressed():
            if not app.server_active:
                app.show_notification("Cannot connect to server")
                return
            app.show_frame(app.upload_frame)

        upload_button = ctk.CTkButton(
            master=frame2,
            text="UPLOAD",
            font=('Segoe UI',16, 'bold'),
            image=ctk.CTkImage(
                light_image=Image.open(path.join("images", "cloud-upload.png")),
                size=(32,32)
            ),
            command=_upload_button_pressed
        )
        upload_button.grid(
            row=0,
            padx=16, pady=16,
            sticky="nsew"
        )

        def _uploaded_files_button_pressed():
            if not app.server_active:
                app.show_notification("Cannot connect to server")
                return
            app.show_frame(app.uploaded_files_frame)

        download_button = ctk.CTkButton(
            master=frame2,
            text="UPLOADED FILES",
            font=('Segoe UI',16, 'bold'),
            image=ctk.CTkImage(
                light_image=Image.open(path.join("images", "folder.png")),
                size=(30,30)
            ),
            command=_uploaded_files_button_pressed
        )
        download_button.grid(
            row=1,
            padx=16, pady=16,
            sticky="nsew"
        )

        frame3 = ctk.CTkFrame(master=self,width=512,height=64)
        frame3.grid(
            row=2,
            padx=16, 
            pady=16
        )
        frame3.grid_columnconfigure(0, weight=1)
        frame3.grid_columnconfigure(1, weight=1)
        frame3.grid_propagate(False)

        credits_button = ctk.CTkButton(
            master=frame3,
            text="Settings",
            font=('Segoe UI',16, 'bold'),
            command=lambda: app.show_frame(app.settings_frame)
        )
        credits_button.grid(
            row=0, column=0,
            padx=16,
            pady=16
        )

        credits_button = ctk.CTkButton(
            master=frame3,
            text="Credits",
            font=('Segoe UI',16, 'bold'),
            command=lambda: app.show_frame(app.credits_frame)
        )
        credits_button.grid(
            row=0, column=1,
            padx=16,
            pady=16
        )

        logout_button = ctk.CTkButton(
            master=frame3,
            text="Quit",
            font=('Segoe UI',16, 'bold'),
            command=app.close
        )
        logout_button.grid(
            row=0, column=2,
            padx=16,
            pady=16
        )



class UploadFrame(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, app: App):
        super().__init__(master=parent)

        self.app = app

        return_button = app.create_return_button(self)

        return_button.pack(
            padx=16, pady=16,
            anchor="w"
        )

        frame = ctk.CTkFrame(master=self)
        frame.pack(
            padx=16, pady=16,
            fill="both",
            expand=True
        )

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        frame2 = ctk.CTkFrame(
            master=frame,
            fg_color="transparent"
        )
        frame2.grid(sticky="ew")

        self.file_label = ctk.CTkLabel(
            master=frame2,
            text="No file selected",
            font=('Segoe UI', 16, 'bold'),
            width=20
        )
        self.file_label.pack()

        choose_file_button = ctk.CTkButton(
            master=frame2,
            text="Choose a File",
            font=('Segoe UI',16, 'bold'),
            command=self.open_file_dialog
        )
        choose_file_button.pack(pady=16)

        upload_button = ctk.CTkButton(master=frame2, text="Upload", font=('Segoe UI',16,'bold'), command=self.upload_and_refresh)
        upload_button.pack()

        self.file_path = ""
    
    def refresh(self):
        self.file_label.configure(text="No file selected")
        self.file_path = ""
    
    def open_file_dialog(self):
        self.file_path = filedialog.askopenfilename(
            title="Select a File",
            # initialdir="",
            filetypes=(("All files", "*.*"),)
        )
        if self.file_path:
            file_name = path.basename(self.file_path)
            self.file_label.configure(text=f"Selected file: {app.truncate_text(text=file_name, max_length=30)}")
    
    def upload_file(self):
        if not self.file_path:
           app.show_notification("Please select a file before uploading.")

        else:
            if self.file_exists():
                app.show_notification("The selected file has already existed on the server.")

            else:
                try:
                    progress_window = ProgressWindow(master=self, title="Uploading...", main_label_text=app.truncate_text(text=self.file_path, max_length=30), bar_count=app.chunks, goal=path.getsize(self.file_path))
                    ftc.upload_file(self.file_path, app.chunks, progress_window.track_progress)
                    # ftc.upload_file(self.file_path, app.chunks)
                    # app.show_notification("File uploaded successfully!")
                    self.file_path = ""
                    
                except Exception as e:
                    app.show_notification(f"Failed to upload file: {e}")

    def file_exists(self):
        try:
            existing_files = ftc.list_files()
            if existing_files is None:
                return False
            file_name = path.basename(self.file_path)
            return any(file_name == name for name, _, _ in existing_files)
        except Exception as e:
            print(e)
    
    def refresh_file_label(self):
        self.file_label.configure(text="No file selected")

    def upload_and_refresh(self):
        upload_thread = threading.Thread(target=self.upload_file)
        upload_thread.daemon = True
        upload_thread.start()
        # self.upload_file()
        self.refresh_file_label()



class UploadedFilesFrame(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, app: App):
        super().__init__(master=parent)

        try:
            return_button = app.create_return_button(self)

            return_button.pack(
                padx=16, pady=16,
                anchor="w"
            )

            self.scrollable_frame = ctk.CTkFrame(master=self)
            self.scrollable_frame.pack(
                padx=16, pady=16,
                fill="both", expand=True
            )

            self.label = ctk.CTkLabel(master=self.scrollable_frame, text="No files uploaded", font=('Segoe UI',20,'bold'))
            self.label.pack(
                    fill="both", expand=True
            )

            self.file_list = CTkListbox(
                    master=self.scrollable_frame,
                    font=('Segoe UI'),
                    width=512, height=10
            )

            self.file_list.pack(
                    fill="both", expand=True
            )
            
            bot_frame = ctk.CTkFrame(master=self,width=512,height=64)
            bot_frame.pack(
                padx=16,
                pady=16
            )

            bot_frame.grid_columnconfigure(0, weight=1)
            bot_frame.grid_columnconfigure(1, weight=1)
            bot_frame.grid_propagate(False)

            def start_download_thread():
                download_thread = threading.Thread(target=self.download_file)
                download_thread.daemon = True
                download_thread.start()

            download_button = ctk.CTkButton(
                master=bot_frame,
                text="Download",
                font=('Segoe UI',16,'bold'),
                command=start_download_thread
                # command=self.download_file
            )

            download_button.grid(
                row=0, column=0,
                padx=16, pady=16,
                sticky="nsew"
            )

            delete_button = ctk.CTkButton(
                master=bot_frame, 
                text="Delete", 
                font=('Segoe UI',16,'bold'),
                command=self.delete_and_refresh
            )

            delete_button.grid(
                row=0, column=1,
                padx=16, pady=16,
                sticky="nsew"
            )

            self.files = []
            self.refresh()

            if len(self.files) == 0:
                self.file_list.pack_forget()
                self.label.pack(fill="both", expand=True)
                
            else:
                self.label.pack_forget()
                self.file_list.pack(fill="both", expand=True)

        except Exception as e:
            print(e)

    def download_file(self):
        if len(self.files) == 0:
            app.show_notification("No files to download.")

        else:
            selection = self.file_list.curselection()

            if selection is None:
                app.show_notification("Please select a file to download.")
            
            else:
                selected_file: str = self.files[selection][0]
                selected_file = selected_file.splitlines()[0]
                destination = filedialog.asksaveasfilename(
                    title="Save as", 
                    confirmoverwrite=True,
                    initialfile=selected_file,
                    defaultextension=f".{selected_file.split('.')[1]}",
                    filetypes=[('All Files', '*.*')]
                )

                if destination:
                    try:
                        progress_window = ProgressWindow(master=self, title="Downloading...", main_label_text=app.truncate_text(text=selected_file, max_length=30), bar_count=app.chunks, goal=int(self.files[selection][2]))
                        ftc.download_file(selected_file, destination, app.chunks, progress_window.track_progress)
                        app.show_notification("File downloaded successfully!")
                    except Exception as e:
                        app.show_notification(f"Failed to download file: {str(e)}")
                else:
                    app.show_notification("Please select a folder to download the file to.")

    def delete_file(self):
        if len(self.files) == 0:
            app.show_notification("No files to delete.")

        else:
            selection = self.file_list.curselection()
            
            if selection is None:
                app.show_notification("Please select a file to delete.")

            else:
                try:
                    selected_file: str = self.files[selection][0]
                    selected_file = selected_file.splitlines()[0]
                    ftc.delete_file(selected_file)
                    app.show_notification("File deleted successfully!")

                except Exception as e:
                    app.show_notification(f"Failed to delete file: {str(e)}")

    def refresh(self):
        try:
            self.files = ftc.list_files()
            self.label.pack_forget()
            self.file_list.pack(fill="both", expand=True)
            self.file_list.delete(0, "end")

            if self.files is None:
                self.files = []

            for name, creation_time, size in self.files:
                size = naturalsize(size)
                self.file_list.insert('end', f"{name:<64}\n\t{creation_time:<64}\n\t{size:<64}")
        
        except Exception as e:
            self.files = []
            print(e)

    def delete_and_refresh(self):
        self.delete_file()
        self.refresh()


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, app: App):
        super().__init__(master=parent)

        return_button = app.create_return_button(self)

        return_button.pack(
            padx=16, pady=16,
            anchor="w"
        )

        frame = ctk.CTkFrame(master=self)
        frame.pack(
            padx=16, pady=16,
            fill="both",
            expand=True
        )

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        frame1 = ctk.CTkFrame(master=frame)
        frame1.grid(row=0, column=0, sticky="sw", padx=16, pady=16)

        server_ip_label = ctk.CTkLabel(
            master=frame1,
            text="Server IP",
            font=('Segoe UI',16, 'bold')
        )

        server_ip_label.pack(side="left", padx=16, pady=16)

        self.server_ip_entry = ctk.CTkEntry(
            master=frame1,
            placeholder_text="0.0.0.0",
            font=('Segoe UI',16, 'bold')
        )

        self.server_ip_entry.pack(side="left", padx=16, pady=16)
        self.server_ip_entry.bind("<Return>", lambda event, app=app, entry=self.server_ip_entry: _on_server_ip_submitted(app=app, server_ip=entry.get()))

        def _on_server_ip_submitted(app: App, server_ip: str):
            app.focus_set()

            try:
                ipaddress.ip_address(server_ip)
                app.server_ip = server_ip
                # ftc = filetransferclient.FileTransferClient(server_ip=server_ip, port=61306)
                ftc.address = (server_ip, 61306)
            
            except ValueError:
                print(f"\"{server_ip}\" is not a valid IP address")

        frame2 = ctk.CTkFrame(master=frame)
        frame2.grid(row=1, column=0, sticky="nw", padx=16, pady=16)

        chunks_label = ctk.CTkLabel(
            master=frame2,
            text="Chunk(s) per transfer",
            font=('Segoe UI',16, 'bold')
        )

        chunks_label.pack(side="left", padx=16, pady=16)

        self.spinbox = CustomSpinbox(frame2, min_value=1, max_value=10)
        self.spinbox.pack(side="right")
        self.spinbox.add_command(lambda event=None, app=app, spinbox=self.spinbox, min=self.spinbox.min_value, max=self.spinbox.max_value: _on_chunks_submitted(app, spinbox, min, max))

        def _on_chunks_submitted(app: App, spinbox: CustomSpinbox, min: int, max: int):
            app.focus_set()
            input = spinbox.entry.get()

            try:
                chunks = int(input)
                if chunks < min:
                    chunks = min
                elif chunks > max:
                    chunks = max
                
                spinbox.entry.delete(0, ctk.END)
                spinbox.entry.insert(0, str(chunks))
                app.chunks = chunks
            
            except ValueError:
                print(f"\"{input}\" is not a valid int")
                spinbox.entry.delete(0, ctk.END)
                spinbox.entry.insert(0, str(app.chunks))
    
    def refresh(self):
        self.server_ip_entry.delete(0, ctk.END)
        self.server_ip_entry.insert(0, str(app.server_ip))
        self.spinbox.entry.delete(0, ctk.END)
        self.spinbox.entry.insert(0, str(app.chunks))



class CreditsFrame(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, app: App):
        super().__init__(master=parent)

        return_button = app.create_return_button(self)

        return_button.place(x=16, y=16)

        title = ctk.CTkLabel(
            master=self,
            text="Credits",
            font=('Segoe UI',32, 'bold')
        )
        title.pack(pady=16)

        frame = ctk.CTkFrame(master=self)
        frame.pack(
            padx=16, pady=16,
            fill="both", expand=True
        )

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        credits = ctk.CTkLabel(
            master=frame,
            text = "Nguyễn Kiến Hào\nNguyễn Lê Quang\nTrần Anh Khoa\n\nCopyright © 2024",
            font=('Segoe UI',16, 'bold')
        )
        credits.grid(row=0, column=0)



class CustomSpinbox(ctk.CTkFrame):
    def __init__(self, master=None, min_value=0, max_value=100, step_size=1, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.step_size = step_size

        self.value_change_handler: any

        self.entry = ctk.CTkEntry(self, width=60, justify="center", font=('Segoe UI', 16, 'bold'))
        self.entry.insert(0, str(self.min_value))
        self.entry.grid(row=0, column=0, padx=(5, 0), pady=(0, 0), sticky="nsew")

        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=0, column=1, padx=(5, 5), pady=(5, 5), sticky="nsew")

        button_frame.grid_rowconfigure(0, weight=1)
        button_frame.grid_rowconfigure(2, weight=1)

        self.increment_button = ctk.CTkButton(button_frame, text="+", width=30, font=('Segoe UI', 16, 'bold'), command=self.increment)
        self.increment_button.grid(row=0, column=0, pady=(0, 2), sticky="nsew")

        self.decrement_button = ctk.CTkButton(button_frame, text="-", width=30, font=('Segoe UI', 16, 'bold'), command=self.decrement)
        self.decrement_button.grid(row=2, column=0, pady=(2, 0), sticky="nsew")

    def add_command(self, command):
        if not command is None:
            self.entry.bind("<Return>", command)
            self.value_change_handler = command
    
    def increment(self):
        value = int(self.entry.get())
        if value < self.max_value:
            value += self.step_size
            self.entry.delete(0, ctk.END)
            self.entry.insert(0, str(value))
        
        self._value_changed()

    def decrement(self):
        value = int(self.entry.get())
        if value > self.min_value:
            value -= self.step_size
            self.entry.delete(0, ctk.END)
            self.entry.insert(0, str(value))
        
        self._value_changed()
    
    def _value_changed(self):
        self.value_change_handler()



class SlideInNotification(ctk.CTkFrame):
    def __init__(self, master, text, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg_color='transparent', fg_color='#0F2A46')
        self.text = text
        self.label = ctk.CTkLabel(self, text=self.text, font=('Segoe UI', 16, 'bold'))
        self.label.pack(pady=16, padx=16)
        
        self.update_idletasks()
        self.width = self.label.winfo_reqwidth() + 32
        self.height = self.label.winfo_reqheight() + 32

        self.window_width = app.winfo_width()
        self.window_height = app.winfo_height()

        self.position_x = self.window_width - self.width - 16
        self.position_y = self.window_height
        
        self.configure(width=self.width, height=self.height)
        self.place(x=self.position_x, y=self.position_y)
        
        self.slide_in()
    
    def slide_in(self):
        if self.position_y > self.window_height - self.height - 16:
            self.position_y -= 8
            self.place(x=self.position_x, y=self.position_y)
            self.after(10, self.slide_in)
        else:
            self.after(1300, self.slide_out)
    
    def slide_out(self):
        if self.position_y < self.window_height:
            self.position_y += 8
            self.place(x=self.position_x, y=self.position_y)
            self.after(10, self.slide_out)
        else:
            self.destroy()



class ProgressWindow(ctk.CTkToplevel):
    def __init__(self, master, title: str, main_label_text: str, bar_count: int, goal: int, **kwargs):
        try:
            super().__init__(master, **kwargs)

            self.geometry("500x200")
            self.resizable(False, False)
            self.title(title)
            self.after(130, self.lift)
            # icon_path = os.path.join("images", "wingfoot.ico")
            # if os.path.exists(icon_path):
            #     self.iconbitmap(icon_path)
            # else:
            #     print(f"Icon file not found: {icon_path}")

            self.goal = goal
            self.humanized_goal = naturalsize(goal)

            main_label = ctk.CTkLabel(
                master=self,
                text=main_label_text,
                font=('Segoe UI', 16, 'bold')
            )
            main_label.pack(pady=16)

            self.progress_in_size = ctk.CTkLabel(
                master=self,
                text="0/0",
                font=('Segoe UI', 16, 'bold')
            )
            self.progress_in_size.pack(padx=16, anchor='w')

            self.progress_in_percentage = ctk.CTkLabel(
                master=self,
                text="0%",
                font=('Segoe UI', 16, 'bold')
            )
            self.progress_in_percentage.pack(padx=16, pady=(0, 16), anchor='w')

            progress_bars = ctk.CTkFrame(master=self)
            progress_bars.pack(padx=16, pady=16)

            self.progress_bar_list: list[ctk.CTkProgressBar] = []
            self.current_progress: int = 0

            for i in range(bar_count):
                progress_bars.columnconfigure(i, weight=1)

                progress_bar = ctk.CTkProgressBar(master=progress_bars)
                self.progress_bar_list.append(progress_bar)
                progress_bar.set(0)

                progress_bar.grid(row=0, column=i)

        except Exception as e:
            print(e)

    def track_progress(self, chunk_number, transferred, percentage):
        self.progress_bar_list[chunk_number].set(percentage)
        self.current_progress += transferred
        self.progress_in_size.configure(text=f"{naturalsize(self.current_progress)} / {self.humanized_goal}")
        self.progress_in_percentage.configure(text=f"{self.current_progress / self.goal * 100:.2f}%")

        if self.current_progress == self.goal:
            # print(f"{self.current_progress} {self.goal}")
            self.after(2000, self.destroy)

    # def close_window(self):
    #     self.destroy()



ftc: filetransferclient.FileTransferClient

if __name__ == "__main__":
    ftc = filetransferclient.FileTransferClient(61306)
    app = App()
    app.mainloop()
