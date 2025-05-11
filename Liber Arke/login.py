import tkinter as tk
from tkinter import ttk, messagebox

class LoginWindow:
    def __init__(self, app):
        self.app = app
        self.window = tk.Toplevel(app.root)
        self.window.title("Login")
        self.window.geometry("300x200")
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Center the window
        window_width = 300
        window_height = 200
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.window.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        self.create_widgets()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.window, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(main_frame)
        self.username_entry.grid(row=0, column=1, sticky=tk.EW, pady=5)
        
        ttk.Label(main_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(main_frame, show="*")
        self.password_entry.grid(row=1, column=1, sticky=tk.EW, pady=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, 
                 text="Login", 
                 command=self.login,
                 style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, 
                 text="Cancel", 
                 command=self.on_close).pack(side=tk.LEFT, padx=5)
        
        self.username_entry.focus()
        self.password_entry.bind("<Return>", lambda e: self.login())
        main_frame.columnconfigure(1, weight=1)
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        user = self.app.db.authenticate_user(username, password)
        if user:
            self.app.current_user = {
                'id': user[0],
                'username': user[1],
                'role': user[2]
            }
            self.app.update_ui_for_role(user[2])
            self.window.destroy()
            self.app.root.deiconify()
        else:
            messagebox.showerror("Error", "Invalid username or password")
            self.password_entry.delete(0, tk.END)
    
    def on_close(self):
        self.app.root.destroy()
