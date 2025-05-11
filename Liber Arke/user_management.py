import tkinter as tk
from tkinter import ttk, messagebox

class UserManagementWindow:
    def __init__(self, app):
        self.app = app
        self.window = tk.Toplevel(app.root)
        self.window.title("User Management")
        self.window.geometry("600x450")
        
        self.center_window()
        
        self.create_widgets()
        self.load_users()
        
    def center_window(self):
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'600x450+{x}+{y}')
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.window, padding="10 10 10 10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Users:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)
        
        # Treeview with additional column for upload permissions
        self.user_tree = ttk.Treeview(main_frame, columns=('username', 'role', 'upload'), show='headings')
        self.user_tree.heading('username', text='Username')
        self.user_tree.heading('role', text='Role')
        self.user_tree.heading('upload', text='Can Upload')
        self.user_tree.column('username', width=200)
        self.user_tree.column('role', width=100)
        self.user_tree.column('upload', width=100)
        self.user_tree.pack(fill=tk.BOTH, expand=True)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, 
                 text="Krijo Perdorues", 
                 command=self.show_create_user,
                 style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, 
                 text="Ndrysho fjalekalim", 
                 command=self.show_change_password).pack(side=tk.LEFT, padx=5)
                 
        ttk.Button(button_frame,
                 text="Toggle Upload",
                 command=self.toggle_upload_permission).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, 
                 text="Mbyll", 
                 command=self.window.destroy).pack(side=tk.RIGHT)
    
    def load_users(self):
        if not self.app.check_db_connection():
            return
            
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
            
        try:
            users = self.app.db.get_all_users()
            if users is None:
                messagebox.showerror("Error", "Failed to load users from database")
                return
                
            for user in users:
                self.user_tree.insert('', tk.END, 
                                    values=(user[1], user[2], 'Yes' if user[3] else 'No'), 
                                    iid=user[0])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load users: {str(e)}")
    
    def show_create_user(self):
        if self.app.check_db_connection():
            CreateUserDialog(self.app, self)
    
    def show_change_password(self):
        if not self.app.check_db_connection():
            return
            
        selected = self.user_tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user first")
            return
        
        ChangePasswordDialog(self.app, selected, self)
        
    def toggle_upload_permission(self):
        if not self.app.check_db_connection():
            return
            
        selected = self.user_tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user first")
            return
            
        current_value = self.user_tree.item(selected, 'values')[2]
        new_value = not (current_value == 'Yes')
        
        if self.app.db.change_upload_permission(selected, new_value):
            self.load_users()
            messagebox.showinfo("Success", "Upload permission updated")
        else:
            messagebox.showerror("Error", "Failed to update upload permission")

class CreateUserDialog:
    def __init__(self, app, parent_window):
        self.app = app
        self.parent = parent_window
        self.dialog = tk.Toplevel(parent_window.window)
        self.dialog.title("Create New User")
        self.dialog.resizable(False, False)
        
        self.dialog.geometry("350x250")
        self.dialog.grab_set()
        
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="15 15 15 15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(main_frame)
        self.username_entry.grid(row=0, column=1, sticky=tk.EW, pady=5)
        
        ttk.Label(main_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(main_frame, show="*")
        self.password_entry.grid(row=1, column=1, sticky=tk.EW, pady=5)
        
        ttk.Label(main_frame, text="Role:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.role_var = tk.StringVar(value="user")
        ttk.Combobox(main_frame, 
                    textvariable=self.role_var,
                    values=['user', 'admin'],
                    state='readonly').grid(row=2, column=1, sticky=tk.EW, pady=5)
        
        self.upload_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame,
                       text="Allow document uploads",
                       variable=self.upload_var).grid(row=3, column=0, columnspan=2, pady=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, 
                 text="Create", 
                 command=self.create_user,
                 style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, 
                 text="Cancel", 
                 command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        main_frame.columnconfigure(1, weight=1)
        self.username_entry.focus()
    
    def create_user(self):
        if not self.app.check_db_connection():
            return
            
        username = self.username_entry.get()
        password = self.password_entry.get()
        role = self.role_var.get()
        can_upload = self.upload_var.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters")
            return
        
        try:
            if self.app.db.create_user(username, password, role, can_upload):
                messagebox.showinfo("Success", "User created successfully")
                self.parent.load_users()
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", "Username already exists")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create user: {str(e)}")

class ChangePasswordDialog:
    def __init__(self, app, user_id, parent_window):
        self.app = app
        self.user_id = user_id
        self.parent = parent_window
        self.dialog = tk.Toplevel(parent_window.window)
        self.dialog.title("Change Password")
        self.dialog.resizable(False, False)
        
        self.dialog.geometry("350x250")
        self.dialog.grab_set()
        
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        username = self.parent.user_tree.item(self.user_id, 'values')[0]
        
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(header_frame, 
                text=f"Change Password for: {username}",
                font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)
        
        fields_frame = ttk.Frame(main_frame)
        fields_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(fields_frame, text="Fjalekalimi i ri:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.new_password_entry = ttk.Entry(fields_frame, show="*")
        self.new_password_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(fields_frame, text="Konfirmo fjalekalim:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.confirm_password_entry = ttk.Entry(fields_frame, show="*")
        self.confirm_password_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(main_frame, 
                text="Fjalekalimi duhet te permbaje minimumi 6 karaktere",
                font=('Segoe UI', 8)).pack(anchor=tk.W, pady=(0, 15))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, 
                 text="Ruaj", 
                 command=self.change_password,
                 style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, 
                 text="Anulo", 
                 command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        fields_frame.columnconfigure(1, weight=1)
        
        self.new_password_entry.focus()
        self.confirm_password_entry.bind("<Return>", lambda e: self.change_password())
    
    def change_password(self):
        if not self.app.check_db_connection():
            return
            
        new_password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        if not new_password or not confirm_password:
            messagebox.showerror("Error", "Please enter both password fields")
            return
        
        if new_password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        if len(new_password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters")
            return
        
        try:
            if self.app.db.change_password(self.user_id, new_password):
                messagebox.showinfo("Success", "Password changed successfully")
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to change password")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to change password: {str(e)}")