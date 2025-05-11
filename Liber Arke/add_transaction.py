import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import time
from threading import Thread
from tkcalendar import Calendar
import imghdr
from PIL import Image, ImageTk
import os
import hashlib
import logging
import re

class AddTransactionTab:
    def __init__(self, app):
        self.app = app
        self.tab = ttk.Frame(app.notebook)
        app.notebook.add(self.tab, text="Shto Transaksion")
        
        self.logger = logging.getLogger('ARKA.AddTransactionTab')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler('arka_transactions.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        self.max_document_size = 5 * 1024 * 1024
        self.max_image_dimension = 5000
        self.max_bytes_per_pixel = 3
        self.allowed_extensions = ['.jpg', '.jpeg']
        self.allowed_mime_types = ['jpeg', 'jpg']
        
        self.date_entry_width = 20
        self.desc_entry_width = 20
        self.desc_entry_height = 2
        self.currency_width = 10
        self.amount_width = 15
        
        self.create_widgets()
        self.start_time_updater()

    def create_widgets(self):
        main_frame = ttk.Frame(self.tab, padding="15 15 15 15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        label_font = ('Segoe UI', 10, 'bold')
        entry_font = ('Segoe UI', 10)
        
        date_frame = ttk.Frame(main_frame)
        date_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(main_frame, text="Data:", font=label_font).grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.date_var = tk.StringVar()
        self.date_var.set(datetime.now().strftime("%d-%m-%Y %H:%M"))
        
        self.date_entry = ttk.Entry(
            date_frame,
            textvariable=self.date_var,
            font=entry_font,
            width=self.date_entry_width
        )
        self.date_entry.pack(side=tk.LEFT)
        
        self.cal_button = ttk.Button(
            date_frame,
            text="📅",
            width=3,
            command=self.show_calendar
        )
        self.cal_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(main_frame, text="Pershkrimi:", font=label_font).grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.NW)
        
        self.desc_entry = tk.Text(
            main_frame,
            font=entry_font,
            width=self.desc_entry_width,
            height=self.desc_entry_height,
            wrap=tk.WORD,
            padx=5,
            pady=5
        )
        self.desc_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        
        scrollbar = ttk.Scrollbar(
            main_frame, 
            orient=tk.VERTICAL, 
            command=self.desc_entry.yview
        )
        scrollbar.grid(row=1, column=2, sticky=tk.NS)
        self.desc_entry['yscrollcommand'] = scrollbar.set
        
        ttk.Label(main_frame, text="Valuta:", font=label_font).grid(
            row=2, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.currency_var = tk.StringVar()
        self.currency_combobox = ttk.Combobox(
            main_frame, 
            textvariable=self.currency_var, 
            values=self.app.currencies,
            font=entry_font,
            width=self.currency_width,
            state='readonly'
        )
        self.currency_combobox.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        self.currency_combobox.current(0)
        
        ttk.Label(main_frame, text="Shuma:", font=label_font).grid(
            row=3, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.amount_entry = ttk.Entry(
            main_frame, 
            font=entry_font,
            width=self.amount_width
        )
        self.amount_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        
        type_frame = ttk.Frame(main_frame)
        type_frame.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(main_frame, text="Lloji:", font=label_font).grid(
            row=4, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.type_var = tk.StringVar(value="income")
        self.income_radio = ttk.Radiobutton(
            type_frame, 
            text="Hyrje", 
            variable=self.type_var, 
            value="income"
        )
        self.income_radio.pack(side=tk.LEFT, padx=5)
        self.expense_radio = ttk.Radiobutton(
            type_frame, 
            text="Dalje", 
            variable=self.type_var, 
            value="expense"
        )
        self.expense_radio.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(main_frame, text="Dokumenti:", font=label_font).grid(
            row=5, column=0, padx=5, pady=5, sticky=tk.W)
        
        doc_frame = ttk.Frame(main_frame)
        doc_frame.grid(row=5, column=1, padx=5, pady=5, sticky=tk.EW)
        
        self.doc_name_var = tk.StringVar()
        self.doc_name_label = ttk.Label(doc_frame, textvariable=self.doc_name_var)
        self.doc_name_label.pack(side=tk.LEFT, padx=5)
        
        self.attach_button = ttk.Button(
            doc_frame, 
            text="Bashkangjit Dokument",
            command=self.attach_document
        )
        self.attach_button.pack(side=tk.LEFT)
        
        self.remove_button = ttk.Button(
            doc_frame, 
            text="Hiq",
            command=self.remove_document,
            state=tk.DISABLED
        )
        self.remove_button.pack(side=tk.LEFT, padx=5)
        
        self.document_data = None
        self.document_filename = None
        self.document_size = 0
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=15)
        self.add_button = ttk.Button(
            button_frame, 
            text="Shto Transaksion", 
            command=self.add_transaction,
            style='Accent.TButton'
        )
        self.add_button.pack(pady=5, ipadx=10, ipady=5)
        
        main_frame.columnconfigure(1, weight=1)
        
        self.date_entry.focus()
        widgets_in_order = [
            self.date_entry,
            self.cal_button,
            self.desc_entry,
            self.currency_combobox,
            self.amount_entry,
            self.income_radio,
            self.expense_radio,
            self.attach_button,
            self.remove_button,
            self.add_button
        ]
        
        for widget in widgets_in_order:
            widget.bind("<Tab>", lambda e, w=widgets_in_order: self.focus_next_widget(e, w))
        
        self.amount_entry.bind("<Return>", lambda e: self.add_transaction())
        self.add_button.bind("<Return>", lambda e: self.add_transaction())

    def sanitize_filename(self, filename):
        if not filename:
            return ""
        filename = os.path.basename(filename)
        return re.sub(r'[^\w\-_.]', '', filename)

    def is_valid_image(self, file_path):
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in self.allowed_extensions:
                self.logger.warning(f"Invalid file extension: {ext}")
                return False
                
            mime_type = imghdr.what(file_path)
            if mime_type not in self.allowed_mime_types:
                self.logger.warning(f"Invalid MIME type: {mime_type}")
                return False
                
            file_size = os.path.getsize(file_path)
            if file_size > self.max_document_size:
                self.logger.warning(f"File too large: {file_size} bytes")
                return False
                
            try:
                with Image.open(file_path) as img:
                    img.verify()
                
                with Image.open(file_path) as img:
                    img.load()
                    
                    if img.size[0] > self.max_image_dimension or img.size[1] > self.max_image_dimension:
                        self.logger.warning(f"Image dimensions too large: {img.size}")
                        return False
                        
                    bytes_per_pixel = file_size / (img.size[0] * img.size[1])
                    if bytes_per_pixel > self.max_bytes_per_pixel:
                        self.logger.warning(f"Suspicious bytes per pixel ratio: {bytes_per_pixel}")
                        return False
                        
            except Exception as img_error:
                self.logger.warning(f"Image validation failed: {str(img_error)}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Image validation error: {str(e)}")
            return False

    def attach_document(self):
        filetypes = [("JPEG files", "*.jpg *.jpeg")]
        filename = filedialog.askopenfilename(
            title="Select a document",
            filetypes=filetypes
        )
        
        if not filename:
            return
            
        try:
            file_size = os.path.getsize(filename)
            if file_size > self.max_document_size:
                raise ValueError(f"File too large (max {self.max_document_size/1024/1024:.2f}MB)")
                
            if not self.is_valid_image(filename):
                raise ValueError("File is not a valid JPEG image or contains suspicious content")
                
            with open(filename, 'rb') as f:
                document_data = f.read()
                
            file_hash = hashlib.sha256(document_data).hexdigest()
            self.logger.info(f"Document attached: {filename}, Size: {file_size}, Hash: {file_hash}")
                
            self.document_data = document_data
            self.document_filename = self.sanitize_filename(os.path.basename(filename))
            self.document_size = file_size
            self.doc_name_var.set(self.document_filename)
            self.remove_button.config(state=tk.NORMAL)
            
        except Exception as e:
            error_msg = f"Document rejected: {str(e)}"
            self.logger.warning(f"Rejected document: {filename} - {error_msg}")
            messagebox.showerror("Security Error", error_msg)
            self.remove_document()

    def remove_document(self):
        self.document_data = None
        self.document_filename = None
        self.document_size = 0
        self.doc_name_var.set("")
        self.remove_button.config(state=tk.DISABLED)

    def add_transaction(self):
        if not self.app.check_db_connection():
            return
    
        try:
            if hasattr(self.app, 'current_user') and self.app.current_user['role'] != 'admin':
                date_str = datetime.now().strftime("%d-%m-%Y %H:%M")
            else:
                date_str = self.date_var.get()
            
            try:
                datetime.strptime(date_str, "%d-%m-%Y %H:%M")
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Please use DD-MM-YYYY HH:MM")
                return
    
            description = self.desc_entry.get("1.0", tk.END).strip()
            if not description:
                messagebox.showerror("Error", "Description cannot be empty")
                return
        
            try:
                amount = float(self.amount_entry.get())
                if amount <= 0:
                    messagebox.showerror("Error", "Amount must be positive")
                    return
            except ValueError:
                messagebox.showerror("Error", "Invalid amount. Please enter a valid number")
                return
    
            currency = self.currency_var.get()
            transaction_type = self.type_var.get()
            user_id = self.app.current_user['id'] if hasattr(self.app, 'current_user') else None

            self.logger.info(
                f"Attempting to add transaction: {date_str}, {currency}, {amount}, "
                f"{transaction_type}, User: {user_id}, Doc: {bool(self.document_data)}"
            )

            success = self.app.db.add_transaction(
                date_str, 
                currency, 
                description, 
                amount, 
                transaction_type,
                user_id,
                self.document_data,
                self.document_filename
            )

            if success:
                self.logger.info("Transaction added successfully")
                messagebox.showinfo("Success", "Transaction added successfully!")
        
                self.desc_entry.delete("1.0", tk.END)
                self.amount_entry.delete(0, tk.END)
                self.remove_document()
        
                self.app.view_balances_tab.update_balances_view()
                self.app.generate_report_tab.generate_report()
            else:
                self.logger.error("Failed to add transaction to database")
                messagebox.showerror("Error", "Failed to add transaction to database")
            
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            self.logger.error(error_msg)
            messagebox.showerror("Error", error_msg)

    def show_calendar(self):
        def set_date():
            selected_date = cal.selection_get()
            current_time = datetime.now().strftime("%H:%M")
            self.date_var.set(selected_date.strftime("%d-%m-%Y") + " " + current_time)
            top.destroy()
        
        top = tk.Toplevel(self.tab)
        top.title("Select Date")
        top.grab_set()
        
        cal = Calendar(top, selectmode='day', date_pattern='dd-mm-yyyy')
        cal.pack(pady=10, padx=10)
        
        ttk.Button(top, text="OK", command=set_date).pack(pady=5)

    def focus_next_widget(self, event, widget_list):
        current_widget = event.widget
        try:
            index = widget_list.index(current_widget)
            next_index = (index + 1) % len(widget_list)
            next_widget = widget_list[next_index]
            next_widget.focus()
            
            if isinstance(next_widget, ttk.Combobox):
                next_widget.event_generate('<Down>')
        except ValueError:
            pass
        return "break"

    def start_time_updater(self):
        def update_time():
            while True:
                try:
                    current_time = datetime.now().strftime("%d-%m-%Y %H:%M")
                    if hasattr(self, 'date_var'):
                        self.date_var.set(current_time)
                    time.sleep(60)
                except:
                    break
        
        time_thread = Thread(target=update_time, daemon=True)
        time_thread.start()

    def update_ui_for_role(self):
        if hasattr(self.app, 'current_user'):
            if self.app.current_user['role'] == 'admin':
                self.date_entry.config(state='normal')
                self.cal_button.config(state='normal')
                self.attach_button.config(state='normal')
            else:
                self.date_entry.config(state='disabled')
                self.cal_button.config(state='disabled')
                self.date_var.set(datetime.now().strftime("%d-%m-%Y %H:%M"))
                
                if hasattr(self.app.current_user, 'can_upload_documents'):
                    can_upload = self.app.current_user.can_upload_documents
                else:
                    can_upload = self.app.db.can_user_upload_documents(self.app.current_user['id'])
                
                self.attach_button.config(state='normal' if can_upload else 'disabled')