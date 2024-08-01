import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
from blinker import signal

import filetransferclient


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.iconbitmap("images\wingfoot.ico")
        self.geometry("500x600")
        self.resizable(False, False)
        self.title("Hermes Hub")

        container = ctk.CTkFrame(master=self)
        container.pack(fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for i in (MainFrame, UploadFrame, UploadedFilesFrame, HelpFrame, CreditsFrame):
            name = i.__name__
            frame = i(parent=container, controller=self)
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        
        current_frame: ctk.CTkFrame = None

        self.show_frame("MainFrame")
    
    def show_frame(self, name: str):
        frame: ctk.CTkFrame = self.frames[name]
        self.current_frame = frame
        frame.tkraise()



class MainFrame(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, controller: App):
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
                light_image=Image.open("images\wingfootTitle.png"),
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

        upload_button = ctk.CTkButton(
            master=frame2,
            text="UPLOAD",
            font=('Segoe UI',16, 'bold'),
            image=ctk.CTkImage(
                light_image=Image.open("images\cloud-upload.png"),
                size=(32,32)
            ),
            command=lambda: controller.show_frame("UploadFrame")
        )
        upload_button.grid(
            row=0,
            padx=16, pady=16,
            sticky="nsew"
        )

        download_button = ctk.CTkButton(
            master=frame2,
            text="UPLOADED FILES",
            font=('Segoe UI',16, 'bold'),
            image=ctk.CTkImage(
                light_image=Image.open("images\down.png"),
                size=(30,30)
            ),
            command=lambda: controller.show_frame("UploadedFilesFrame")
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
            command=lambda: controller.show_frame("HelpFrame")
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
            command=lambda: controller.show_frame("CreditsFrame")
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
            command=close_app
        )
        logout_button.grid(
            row=0, column=2,
            padx=16,
            pady=16
        )



class UploadFrame(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, controller: App):
        super().__init__(master=parent)

        return_button = ctk.CTkButton(
            master=self,
            text="",
            width=1,
            image=ctk.CTkImage(
                light_image=Image.open("images\\return.png"),
                size=(32,32)
            ),
            command=lambda: controller.show_frame("MainFrame")
        )
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
        # frame2.grid_rowconfigure(0, weight=1)
        # frame2.grid_rowconfigure(1, weight=1)
        # frame2.grid_columnconfigure(0, weight=1)

        # choose_file_frame = ctk.CTkFrame(master=frame2)
        # choose_file_frame.grid(sticky="ew")
        # choose_file_frame.grid_columnconfigure(0, weight=0)
        # choose_file_frame.grid_columnconfigure(1, weight=1)

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

        upload_button = ctk.CTkButton(master=frame2, text="Upload", font=('Segoe UI',16,'bold'), command=self.upload_file)
        upload_button.pack()
    
    def save_file_path(self, file_path):
        self.file_path = file_path
    
    def open_file_dialog(self):
        file_path = filedialog.askopenfilename(
            title="Select a File",
            filetypes=(("All files", "*.*"),)
        )
        if file_path:
            self.save_file_path(file_path)
            file_name = file_path.split("/")[-1]
            self.file_label.configure(text=f"Selected file: {self.truncate_text(text=file_name, max_length=30)}")
    
    def truncate_text(self, text, max_length):
            if len(text) > max_length:
                return text[:max_length-3] + "..."
            return text
    def upload_file(self):
        file_path1 = self.file_label.cget("text")
        if file_path1 == "No file selected":
            messagebox.showwarning("No File", "Please select a file before uploading.")
        else:
            file_path2 = self.file_path
            if self.file_exists(file_path2):
                messagebox.showwarning("File Exists", "The selected file already exists.")
            else:
                try:
                    ftc.upload_file(file_path2)
                    messagebox.showinfo("Success", "File uploaded successfully!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to upload file: {str(e)}")
    def file_exists(self, file_path):
        existing_files = ftc.list_files()
        file_name = file_path.split("/")[-1]
        return file_name in existing_files   



class UploadedFilesFrame(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, controller: App):
        super().__init__(master=parent)

        return_button = ctk.CTkButton(
            master=self,
            text="",
            width=1,
            image=ctk.CTkImage(
                light_image=Image.open("images\\return.png"),
                size=(32,32)
            ),
            command=lambda: controller.show_frame("MainFrame")
        )
        return_button.pack(
            padx=16, pady=16,
            anchor="w"
        )

        scrollable_frame = ctk.CTkScrollableFrame(master=self)
        scrollable_frame.pack(
            padx=16, pady=16,
            fill="both", expand=True
        )
        if(len(ftc.list_files())==0):
            check = "No files uploaded"
            label = ctk.CTkLabel(master=scrollable_frame, text=check, font=('Segoe UI',20,'bold'))
            label.pack(
                fill="both", expand=True
            )
        else:
            label = ctk.CTkLabel(master=scrollable_frame, text=ftc.list_files(), font=('Segoe UI',20,'bold'))
            label.pack(
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


        download_button = ctk.CTkButton(master=bot_frame, text="Download", font=('Segoe UI',20,'bold'))
        download_button.pack(
            fill="both", expand=True
        )
        download_button.grid(
            row=0, column=0,
            padx=16, pady=16,
            sticky="nsew"
        )
        delete_button = ctk.CTkButton(master=bot_frame, text="Delete", font=('Segoe UI',20,'bold'))
        delete_button.pack(
            fill="both", expand=True
        )
        delete_button.grid(
            row=0, column=1,
            padx=16, pady=16,
            sticky="nsew"
        )


class HelpFrame(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, controller: App):
        super().__init__(master=parent)

        return_button = ctk.CTkButton(
            master=self,
            text="",
            width=1,
            image=ctk.CTkImage(
                light_image=Image.open("images\\return.png"),
                size=(32,32)
            ),
            command=lambda: controller.show_frame("MainFrame")
        )
        return_button.pack(
            padx=16, pady=16,
            anchor="w"
        )



class CreditsFrame(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, controller: App):
        super().__init__(master=parent)

        return_button = ctk.CTkButton(
            master=self,
            text="",
            width=1,
            image=ctk.CTkImage(
                light_image=Image.open("images\\return.png"),
                size=(32,32)
            ),
            command=lambda: controller.show_frame("MainFrame")
        )
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
            text = "hào quang khoa",
            font=('Segoe UI',16, 'bold')
        )
        credits.pack(pady=16)

def close_app():
    app.destroy()

if __name__ == "__main__":
    
    ftc = filetransferclient.FileTransferClient(1306, "client_data")
    
    app = App()
    app.mainloop()
