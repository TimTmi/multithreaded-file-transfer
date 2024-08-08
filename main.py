import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
from blinker import signal
from os import path
from CTkListbox import *
from time import sleep
import threading

import filetransferclient


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.protocol('WM_DELETE_WINDOW', self.close)

        self.iconbitmap(path.join("images", "wingfoot.ico"))
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
        self.help_frame = HelpFrame(*arguments)
        self.credits_frame = CreditsFrame(*arguments)

        self.current_frame = self.main_frame

        for i in (self.main_frame, self.upload_frame, self.uploaded_files_frame, self.help_frame, self.credits_frame):
            i.grid(row=0, column=0, sticky="nsew")

        self.show_frame(self.main_frame)

        self.server_active = False

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
    
    def show_notification(self, text: str):
        notification = SlideInNotification(self, text=text)
        self.after(5000, notification.destroy)

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
            text="Help",
            font=('Segoe UI',16, 'bold'),
            command=lambda: app.show_frame(app.help_frame)
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
    
    def open_file_dialog(self):
        self.file_path = filedialog.askopenfilename(
            title="Select a File",
            # initialdir="",
            filetypes=(("All files", "*.*"),)
        )
        if self.file_path:
            file_name = self.file_path.split("/")[-1]
            self.file_label.configure(text=f"Selected file: {self.truncate_text(text=file_name, max_length=30)}")
    
    def truncate_text(self, text, max_length):
            if len(text) > max_length:
                return text[:max_length-3] + "..."
            return text
    
    def upload_file(self):
        if not self.file_path:
           app.show_notification("Please select a file before uploading.")

        else:
            if self.file_exists(self.file_path):
                app.show_notification("The selected file has already existed on the server.")

            else:
                try:
                    ftc.upload_file(self.file_path)
                    app.show_notification("File uploaded successfully!")
                    
                except Exception as e:
                    app.show_notification(f"Failed to upload file: {e}")

    def file_exists(self, file_path):
        try:
            existing_files = ftc.list_files()
            file_name = path.basename(self.file_path)
            return any(file_name == name for name, _, _ in existing_files)
        except Exception as e:
            print(e)
    
    def refresh_file_label(self):
        self.file_label.configure(text="No file selected")

    def upload_and_refresh(self):
        self.upload_file()
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
            
            refresh_button = ctk.CTkButton(
                master=self,
                text="Refresh",
                font=('Segoe UI', 16, 'bold'),
                command=self.refresh
            )

            refresh_button.pack(
                fill = "both", expand = True,
            )

            refresh_button.place(x=350, y=35)

            bot_frame = ctk.CTkFrame(master=self,width=512,height=64)
            bot_frame.pack(
                padx=16,
                pady=16
            )

            bot_frame.grid_columnconfigure(0, weight=1)
            bot_frame.grid_columnconfigure(1, weight=1)
            bot_frame.grid_propagate(False)

            download_button = ctk.CTkButton(
                master=bot_frame, 
                text="Download", 
                font=('Segoe UI',16,'bold'), 
                command=self.download_file
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
            selection: int = self.file_list.curselection()

            if not selection:
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
                        ftc.download_file(selected_file, destination)
                        app.show_notification("File downloaded successfully!")
                    except Exception as e:
                        app.show_notification(f"Failed to download file: {str(e)}")
                else:
                    app.show_notification("Please select a folder to download the file to.")

    def delete_file(self):
        if len(self.files) == 0:
            app.show_notification("No files to delete.")

        else:
            selection: int = self.file_list.curselection()
            
            if not selection:
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

            for name, creation_time, size in self.files:
                self.file_list.insert('end', f"{name:<64}\n\t{creation_time:<64}\n\t{size:<64}")
        
        except Exception as e:
            self.files = []
            print(e)

    def delete_and_refresh(self):
        self.delete_file()
        self.refresh()


class HelpFrame(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, app: App):
        super().__init__(master=parent)

        return_button = app.create_return_button(self)

        return_button.pack(
            padx=16, pady=16,
            anchor="w"
        )



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

        credits = ctk.CTkLabel(
            master=frame,
            text = "Nguyễn Kiến Hào\nNguyễn Lê Quang\nTrần Anh Khoa\n\n@ Copyright 2024",
            font=('Segoe UI',16, 'bold')
        )
        credits.pack(pady=16)



class SlideInNotification(ctk.CTkFrame):
    def __init__(self, master, text, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(bg_color='transparent', fg_color='#0F2A46')

        self.text = text
        self.label = ctk.CTkLabel(self, text=self.text, font=('Segoe UI', 16, 'bold'))
        self.label.pack(pady=16, padx=16)
        
        self.window_width = 500
        self.window_height = 600
        self.width = 500 - 32
        self.height = 64
        
        self.position_x = 16
        self.position_y = self.window_height
        
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



if __name__ == "__main__":
    ftc = filetransferclient.FileTransferClient(1306)
    app = App()
    app.mainloop()
