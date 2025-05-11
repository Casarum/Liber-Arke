import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from add_transaction import AddTransactionTab
from view_balances import ViewBalancesTab
from generate_report import GenerateReportTab
from database import Database
from login import LoginWindow
from user_management import UserManagementWindow

class CashMovementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ARKA")
        self.root.geometry("1300x750")
        self.root.withdraw()
        
        self.db = Database()
        self.create_menu()
        self.current_user = None
        self.setup_theme()
        self.currencies = ['EUR', 'USD', 'LEK', 'GBP']
        
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.add_transaction_tab = AddTransactionTab(self)
        self.view_balances_tab = ViewBalancesTab(self)       
        self.generate_report_tab = GenerateReportTab(self)
        
        self.show_login()

    def check_db_connection(self):
        try:
            if not self.db.check_connection():
                if not self.db.reconnect():
                    retry = messagebox.askretrycancel(
                        "Database Connection Lost",
                        "Cannot connect to the database. Please check your connection and retry."
                    )
                    if retry:
                        return self.check_db_connection()
                    return False
            return True
        except Exception as e:
            messagebox.showerror("Database Error", f"Connection check failed: {str(e)}")
            return False

    def show_login(self):
        if self.check_db_connection():
            LoginWindow(self)

    def create_menu(self):
        menubar = tk.Menu(self.root)
    
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
    
        self.admin_menu = tk.Menu(menubar, tearoff=0)
        self.admin_menu.add_command(label="User Management", command=self.show_user_management)
        self.admin_menu.add_command(label="Reconnect Database", command=self.check_db_connection)
    
        self.dark_mode_var = tk.BooleanVar(value=False)
        self.admin_menu.add_checkbutton(label="Dark Mode", 
                                      variable=self.dark_mode_var,
                                      command=self.toggle_dark_mode)
    
        menubar.add_cascade(label="Admin", menu=self.admin_menu)
    
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Contact Support", command=self.show_contact_info)
        menubar.add_cascade(label="Help", menu=help_menu)
    
        self.root.config(menu=menubar)
        self.admin_menu_entry = 1

    def toggle_dark_mode(self):
        if self.dark_mode_var.get():
            bg_color = '#2d2d2d'
            fg_color = '#ffffff'
            entry_bg = '#3d3d3d'
            tree_bg = '#3d3d3d'
            tree_fg = '#ffffff'
            tree_selected = '#0078d7'
            tab_bg = '#3d3d3d'
            tab_fg = '#ffffff'
            tab_selected_bg = '#505050'
            button_bg = '#505050'
        else:
            bg_color = '#f0f0f0'
            fg_color = '#333333'
            entry_bg = '#ffffff'
            tree_bg = '#ffffff'
            tree_fg = '#333333'
            tree_selected = '#0078d7'
            tab_bg = bg_color
            tab_fg = fg_color
            tab_selected_bg = '#ffffff'
            button_bg = '#f0f0f0'

        style = ttk.Style()
        style.configure('.', 
                      background=bg_color, 
                      foreground=fg_color,
                      fieldbackground=entry_bg)
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('TEntry', fieldbackground=entry_bg, foreground=fg_color)
        style.configure('TCombobox', fieldbackground=entry_bg, foreground=fg_color)
        style.configure('TButton', background=button_bg, foreground=fg_color)
        style.configure('TNotebook', background=tab_bg)
        style.configure('TNotebook.Tab', 
                      background=tab_bg,
                      foreground=tab_fg,
                      padding=[10, 5],
                      font=('Segoe UI', 10, 'bold'))
        style.map('TNotebook.Tab',
                 background=[('selected', tab_selected_bg)],
                 foreground=[('selected', fg_color)])
        style.configure('Treeview', 
                      background=tree_bg,
                      foreground=tree_fg,
                      fieldbackground=tree_bg)
        style.map('Treeview', 
                 background=[('selected', tree_selected)],
                 foreground=[('selected', '#ffffff')])
        style.configure('Accent.TButton', 
                      font=('Segoe UI', 10, 'bold'), 
                      foreground='white', 
                      background='#4CAF50')
        style.map('Accent.TButton',
                 background=[('active', '#45a049'), 
                            ('pressed', '#45a049')])
        style.configure('TCombobox', 
              fieldbackground=entry_bg, 
              foreground=fg_color,
              selectbackground='#0078d7',
              selectforeground='white')
        style.map('TCombobox',
              fieldbackground=[('readonly', entry_bg)],
              selectbackground=[('readonly', '#0078d7')])
    
        self.update_widget_colors(bg_color, fg_color, entry_bg)

    def update_widget_colors(self, bg_color, fg_color, entry_bg):
        self.root.config(bg=bg_color)
    
        def update_children(parent):
            for child in parent.winfo_children():
                if isinstance(child, (ttk.Frame, ttk.LabelFrame, ttk.PanedWindow)):
                    update_children(child)
                elif isinstance(child, tk.Text):
                    child.config(
                        bg=entry_bg, 
                        fg=fg_color, 
                        insertbackground=fg_color,
                        selectbackground='#0078d7',
                        selectforeground='white'
                    )
                elif isinstance(child, ttk.Label):
                    child.config(foreground=fg_color)
                elif isinstance(child, (ttk.Entry, ttk.Combobox)):
                    child.config(foreground=fg_color)
                elif isinstance(child, ttk.Notebook):
                    style = ttk.Style()
                    style.configure('TNotebook', background=bg_color)
                    style.configure('TNotebook.Tab', 
                                   background=bg_color,
                                   foreground=fg_color)
    
        update_children(self.main_frame)
    
        for tab in [self.add_transaction_tab, self.view_balances_tab, self.generate_report_tab]:
            if hasattr(tab, 'tab'):
                tab.tab.config(style='TFrame')

    def show_contact_info(self):
        messagebox.showinfo(
            "Contact Support",
            "Per cdo pyetje, ju lutem kontaktoni:\n"
            "Emri: Blendi\n"
            "Tel: 0694020360\n"
            "Email: blendi.vangjeli@gmail.com"
        )

    def update_ui_for_role(self, role):
        if not self.check_db_connection():
            return
            
        if role != 'admin':
            self.generate_report_tab.delete_button.config(state=tk.DISABLED)
            self.root.config(menu=self.root.children['!menu'])
        else:
            self.generate_report_tab.delete_button.config(state=tk.NORMAL)
            self.create_menu()
            if hasattr(self, 'add_transaction_tab'):
                self.add_transaction_tab.update_ui_for_role()

    def show_user_management(self):
        if not self.check_db_connection():
            return
            
        if hasattr(self, 'current_user') and self.current_user['role'] == 'admin':
            UserManagementWindow(self)
        else:
            messagebox.showerror("Access Denied", "Only admin users can access this feature")

    def show_about(self):
        messagebox.showinfo("About", "ARKA\nVersion 1.0")

    def setup_theme(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('.', background='#f0f0f0', foreground='#333333')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10), padding=5)
        style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'), 
                       foreground='white', background='#4CAF50')
        style.map('Accent.TButton',
                 background=[('active', '#45a049'), ('pressed', '#45a049')])
        style.configure('Treeview', font=('Segoe UI', 9), rowheight=25,
                      fieldbackground='#ffffff', background='#ffffff')
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#0078d7')])
        style.configure('TNotebook', background='#f0f0f0')
        style.configure('TNotebook.Tab', padding=[10, 5], font=('Segoe UI', 10, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', '#ffffff')])

    def parse_date(self, date_str):
        try:
            return datetime.strptime(date_str, "%d-%m-%Y %H:%M")
        except ValueError:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return datetime.now()

    def format_date(self, date_str):
        dt = self.parse_date(date_str)
        return dt.strftime("%d-%m-%Y %H:%M")

if __name__ == "__main__":
    root = tk.Tk()
    app = CashMovementApp(root)
    root.mainloop()
    app.db.close()