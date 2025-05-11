import tkinter as tk
from tkinter import ttk

class ViewBalancesTab:
    def __init__(self, app):
        self.app = app
        self.tab = ttk.Frame(app.notebook)
        app.notebook.add(self.tab, text="Gjendje Arke")
        self.create_widgets()
        self.update_balances_view()

    def create_widgets(self):
        main_frame = ttk.Frame(self.tab, padding="15 15 15 15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, 
                 text="Current Balances", 
                 font=('Segoe UI', 12, 'bold')).pack(pady=(0, 10))
        
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.balances_tree = ttk.Treeview(tree_frame, 
                                        columns=('Valuta', 'Hyrjet Totale', 'Daljet Totale', 'Balanca'), 
                                        show='headings',
                                        selectmode='browse')
        
        columns = {
            'Valuta': {'width': 120, 'anchor': tk.CENTER},
            'Hyrjet Totale': {'width': 150, 'anchor': tk.E},
            'Daljet Totale': {'width': 150, 'anchor': tk.E},
            'Balanca': {'width': 150, 'anchor': tk.E}
        }
        
        for col, config in columns.items():
            self.balances_tree.heading(col, text=col, anchor=config['anchor'])
            self.balances_tree.column(col, width=config['width'], anchor=config['anchor'])
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.balances_tree.yview)
        self.balances_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.balances_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.balances_tree.tag_configure('positive', foreground='green')
        self.balances_tree.tag_configure('negative', foreground='red')
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(button_frame, 
                  text="Refresh Balances", 
                  command=self.update_balances_view,
                  style='Accent.TButton').pack(pady=5)

    def update_balances_view(self):
        if not self.app.check_db_connection():
            return
            
        for item in self.balances_tree.get_children():
            self.balances_tree.delete(item)
        
        try:
            balances = self.app.db.get_balances()
            
            if balances is None:
                messagebox.showerror("Error", "Failed to retrieve balances from database")
                return
            
            for currency, income, expense in balances:
                balance = income - expense
                tags = ('positive',) if balance >= 0 else ('negative',)
                
                self.balances_tree.insert('', tk.END, 
                                        values=(
                                            currency,
                                            f"{income:,.2f}",
                                            f"{expense:,.2f}",
                                            f"{balance:,.2f}"
                                        ),
                                        tags=tags)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update balances: {str(e)}")