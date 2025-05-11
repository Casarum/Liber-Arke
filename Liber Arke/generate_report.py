import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import csv
from tkcalendar import Calendar
import tempfile
import os
import platform
import subprocess
import logging
from PIL import Image, ImageTk
import shutil

class GenerateReportTab:
    def __init__(self, app):
        self.app = app
        self.tab = ttk.Frame(app.notebook)
        app.notebook.add(self.tab, text="Raporti")
        
        self.logger = logging.getLogger('ARKA.GenerateReportTab')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler('arka_reports.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        self.max_image_dimension = 5000
        self.max_bytes_per_pixel = 3
        
        self.temp_files = []
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.tab, padding="10 10 10 10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        filter_frame = ttk.LabelFrame(main_frame, text="Report Filters", padding="10 5 10 5")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        date_frame = ttk.Frame(filter_frame)
        date_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(date_frame, text="Date Range:").pack(side=tk.LEFT, padx=5)
        
        from_frame = ttk.Frame(date_frame)
        from_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(from_frame, text="From:").pack(side=tk.LEFT)
        self.report_from_date = ttk.Entry(from_frame, width=15)
        self.report_from_date.pack(side=tk.LEFT)
        self.report_from_date.insert(0, datetime.now().strftime("%d-%m-%Y 00:00"))
        
        from_cal_button = ttk.Button(
            from_frame,
            text="📅",
            width=3,
            command=lambda: self.show_calendar(self.report_from_date)
        )
        from_cal_button.pack(side=tk.LEFT, padx=2)
        
        to_frame = ttk.Frame(date_frame)
        to_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(to_frame, text="To:").pack(side=tk.LEFT)
        self.report_to_date = ttk.Entry(to_frame, width=15)
        self.report_to_date.pack(side=tk.LEFT)
        self.report_to_date.insert(0, datetime.now().strftime("%d-%m-%Y 23:59"))
        
        to_cal_button = ttk.Button(
            to_frame,
            text="📅",
            width=3,
            command=lambda: self.show_calendar(self.report_to_date)
        )
        to_cal_button.pack(side=tk.LEFT, padx=2)
        
        filter_row = ttk.Frame(filter_frame)
        filter_row.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_row, text="Pershkrimi:").pack(side=tk.LEFT, padx=5)
        self.report_desc_filter = ttk.Entry(filter_row, width=25)
        self.report_desc_filter.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(filter_row, text="Valuta:").pack(side=tk.LEFT, padx=5)
        self.report_currency_var = tk.StringVar()
        ttk.Combobox(filter_row, 
                    textvariable=self.report_currency_var, 
                    values=['All'] + self.app.currencies, 
                    width=8,
                    state='readonly').pack(side=tk.LEFT, padx=5)
        self.report_currency_var.set('All')
        
        ttk.Label(filter_row, text="Lloji:").pack(side=tk.LEFT, padx=5)
        self.report_type_var = tk.StringVar(value="All")
        ttk.Combobox(filter_row, 
                    textvariable=self.report_type_var, 
                    values=['All', 'Income', 'Expense'], 
                    width=8,
                    state='readonly').pack(side=tk.LEFT, padx=5)
        
        button_frame = ttk.Frame(filter_frame)
        button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, 
                  text="Gjenero Raport", 
                  command=self.generate_report,
                  style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        income_frame = ttk.LabelFrame(tree_frame, text="HYRJET", padding="5 5 5 5")
        income_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=5, pady=5)
        self.report_income_tree = ttk.Treeview(income_frame, 
                                             columns=('Data', 'Pershkrimi', 'Valuta', 'Shuma', 'Dokumenti'), 
                                             show='headings')
        for col in ('Data', 'Pershkrimi', 'Valuta', 'Shuma', 'Dokumenti'):
            self.report_income_tree.heading(col, text=col)
            self.report_income_tree.column(col, width=120, anchor=tk.CENTER)
        self.report_income_tree.column('Pershkrimi', width=200)
        self.report_income_tree.column('Dokumenti', width=150)
        self.report_income_tree.pack(fill=tk.BOTH, expand=True)
        
        expense_frame = ttk.LabelFrame(tree_frame, text="DALJET", padding="5 5 5 5")
        expense_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=5, pady=5)
        self.report_expense_tree = ttk.Treeview(expense_frame, 
                                              columns=('Data', 'Pershkrimi', 'Valuta', 'Shuma', 'Dokumenti'), 
                                              show='headings')
        for col in ('Data', 'Pershkrimi', 'Valuta', 'Shuma', 'Dokumenti'):
            self.report_expense_tree.heading(col, text=col)
            self.report_expense_tree.column(col, width=120, anchor=tk.CENTER)
        self.report_expense_tree.column('Pershkrimi', width=200)
        self.report_expense_tree.column('Dokumenti', width=150)
        self.report_expense_tree.pack(fill=tk.BOTH, expand=True)
        
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(bottom_frame, text="Export to CSV", command=self.export_report_to_csv).pack(side=tk.LEFT, padx=5)
        self.delete_button = ttk.Button(bottom_frame, text="FSHIJ TRANSAKSION", command=self.delete_selected_transactions)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        totals_frame = ttk.LabelFrame(main_frame, text="Currency Totals", padding="10 5 10 5")
        totals_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.report_totals_notebook = ttk.Notebook(totals_frame)
        self.report_totals_notebook.pack(fill=tk.X, expand=True)
        
        self.report_currency_total_vars = {}
        for currency in self.app.currencies:
            frame = ttk.Frame(self.report_totals_notebook)
            self.report_totals_notebook.add(frame, text=currency)
            
            income_var = tk.StringVar()
            ttk.Label(frame, textvariable=income_var, font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=10)
            
            expense_var = tk.StringVar()
            ttk.Label(frame, textvariable=expense_var, font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=10)
            
            balance_var = tk.StringVar()
            ttk.Label(frame, textvariable=balance_var, font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=10)
            
            self.report_currency_total_vars[currency] = {
                'income': income_var,
                'expense': expense_var,
                'balance': balance_var
            }
            income_var.set(f"Income: 0.00 {currency}")
            expense_var.set(f"Expense: 0.00 {currency}")
            balance_var.set(f"Balance: 0.00 {currency}")
        
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.columnconfigure(1, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        self.report_income_tree.bind("<Double-1>", self.view_document)
        self.report_expense_tree.bind("<Double-1>", self.view_document)

    def show_calendar(self, target_entry):
        def set_date():
            selected_date = cal.selection_get()
            current_value = target_entry.get()
            try:
                _, time_part = current_value.split()
            except ValueError:
                time_part = "00:00"
            
            new_value = selected_date.strftime("%d-%m-%Y") + " " + time_part
            target_entry.delete(0, tk.END)
            target_entry.insert(0, new_value)
            top.destroy()
        
        top = tk.Toplevel(self.tab)
        top.title("Select Date")
        top.grab_set()
        
        cal = Calendar(top, selectmode='day', date_pattern='dd-mm-yyyy')
        cal.pack(pady=10, padx=10)
        
        ttk.Button(top, text="OK", command=set_date).pack(pady=5)

    def generate_report(self):
        if not self.app.check_db_connection():
            return
            
        from_date_str = self.report_from_date.get()
        to_date_str = self.report_to_date.get()
        desc_filter = self.report_desc_filter.get()
        currency_filter = self.report_currency_var.get()
        type_filter = self.report_type_var.get()
        
        self.logger.info(
            f"Generating report from {from_date_str} to {to_date_str}. "
            f"Filters: desc='{desc_filter}', currency='{currency_filter}', type='{type_filter}'"
        )
        
        try:
            from_dt = datetime.strptime(from_date_str, "%d-%m-%Y %H:%M")
            to_dt = datetime.strptime(to_date_str, "%d-%m-%Y %H:%M")
            from_date = from_dt.strftime("%Y-%m-%d %H:%M:%S")
            to_date = to_dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Please use DD-MM-YYYY HH:MM")
            return
        
        for item in self.report_income_tree.get_children():
            self.report_income_tree.delete(item)
        for item in self.report_expense_tree.get_children():
            self.report_expense_tree.delete(item)
        
        currency_totals = {curr: {'income': 0.0, 'expense': 0.0} for curr in self.app.currencies}
        
        try:
            transactions = self.app.db.get_filtered_transactions(
                from_date, to_date, desc_filter, currency_filter, type_filter
            )
            
            if transactions is None:
                messagebox.showerror("Error", "Failed to retrieve transactions from database")
                return
            
            for transaction in transactions:
                currency = transaction[2]
                amount = float(transaction[4])
                document_name = transaction[8] if len(transaction) > 8 else None
                document_size = transaction[9] if len(transaction) > 9 else 0
                
                doc_info = ""
                if document_name and document_size:
                    size_mb = document_size / 1024 / 1024
                    doc_info = f"{document_name} ({size_mb:.2f}MB)"
                
                if transaction[5] == 'income':
                    currency_totals[currency]['income'] += amount
                    self.report_income_tree.insert('', tk.END, values=(
                        transaction[1].strftime("%d-%m-%Y %H:%M"),
                        transaction[3],
                        transaction[2],
                        f"{amount:,.2f}",
                        doc_info
                    ), tags=('has_doc',) if doc_info else ())
                else:
                    currency_totals[currency]['expense'] += amount
                    self.report_expense_tree.insert('', tk.END, values=(
                        transaction[1].strftime("%d-%m-%Y %H:%M"),
                        transaction[3],
                        transaction[2],
                        f"{amount:,.2f}",
                        doc_info
                    ), tags=('has_doc',) if doc_info else ())
            
            for currency in self.app.currencies:
                income = currency_totals[currency]['income']
                expense = currency_totals[currency]['expense']
                balance = income - expense
                
                self.report_currency_total_vars[currency]['income'].set(f"Income: {income:,.2f} {currency}")
                self.report_currency_total_vars[currency]['expense'].set(f"Expense: {expense:,.2f} {currency}")
                self.report_currency_total_vars[currency]['balance'].set(f"Balance: {balance:,.2f} {currency}")
                
            self.report_income_tree.tag_configure('has_doc', foreground='blue')
            self.report_expense_tree.tag_configure('has_doc', foreground='blue')
            
            self.logger.info(f"Report generated successfully with {len(transactions)} transactions")
                
        except Exception as e:
            error_msg = f"Failed to generate report: {str(e)}"
            self.logger.error(error_msg)
            messagebox.showerror("Error", error_msg)

    def validate_temp_document(self, file_path):
        try:
            if os.path.getsize(file_path) > self.app.add_transaction_tab.max_document_size:
                self.logger.warning("Temp document exceeds size limit")
                return False
                
            with Image.open(file_path) as img:
                img.verify()
                img = Image.open(file_path)
                img.load()
                
                if img.size[0] > self.max_image_dimension or img.size[1] > self.max_image_dimension:
                    self.logger.warning(f"Temp document dimensions too large: {img.size}")
                    return False
                    
                file_size = os.path.getsize(file_path)
                bytes_per_pixel = file_size / (img.size[0] * img.size[1])
                if bytes_per_pixel > self.max_bytes_per_pixel:
                    self.logger.warning(f"Temp document suspicious bytes per pixel: {bytes_per_pixel}")
                    return False
                    
                img.close()
            return True
        except Exception as e:
            self.logger.warning(f"Temp document validation failed: {str(e)}")
            return False

    def view_document(self, event):
        try:
            tree = event.widget
            item = tree.identify_row(event.y)
            if not item:
                return
                
            values = tree.item(item, 'values')
            if len(values) < 5 or not values[4]:
                return
                
            try:
                transaction_id = None
                cursor = self.app.db.conn.cursor()
                cursor.execute("""
                SELECT id FROM transactions 
                WHERE registration_date = ? 
                AND description = ?
                AND currency = ?
                AND amount = ?
                AND transaction_type = ?
                AND document_name LIKE ?
                AND deleted = 0
                """, (
                    datetime.strptime(values[0], "%d-%m-%Y %H:%M").strftime("%Y-%m-%d %H:%M:%S"),
                    values[1],
                    values[2],
                    float(values[3].replace(',', '')),
                    'income' if tree == self.report_income_tree else 'expense',
                    f"{values[4].split()[0]}%"
                ))
                result = cursor.fetchone()
                
                if not result:
                    raise ValueError("Transaction not found")
                    
                document_data, document_name = self.app.db.get_document(result[0])
                if not document_data:
                    raise ValueError("Document not found in database")
                    
                temp_dir = tempfile.mkdtemp()
                temp_path = os.path.join(temp_dir, document_name)
                self.temp_files.append(temp_path)
                
                with open(temp_path, 'wb') as f:
                    f.write(document_data)
                    
                if not self.validate_temp_document(temp_path):
                    raise ValueError("Document failed validation")
                    
                self.logger.info(f"Opening document: {document_name} from transaction {result[0]}")
                
                try:
                    img = Image.open(temp_path)
                    img.show()
                except Exception as open_error:
                    raise ValueError(f"Could not open document: {str(open_error)}")
                    
                self.tab.after(5000, self.secure_cleanup)
                
            except Exception as e:
                error_msg = f"Could not open document: {str(e)}"
                self.logger.error(error_msg)
                messagebox.showerror("Error", error_msg)
                self.secure_cleanup()
                
        except Exception as outer_error:
            self.logger.error(f"Unexpected error in view_document: {str(outer_error)}")
            messagebox.showerror("Error", "An unexpected error occurred while processing the document")

    def secure_cleanup(self):
        for temp_path in self.temp_files:
            try:
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
                    dir_path = os.path.dirname(temp_path)
                    if os.path.exists(dir_path):
                        shutil.rmtree(dir_path, ignore_errors=True)
            except Exception as e:
                self.logger.warning(f"Could not delete temp file {temp_path}: {str(e)}")
        self.temp_files = []

    def delete_selected_transactions(self):
        if not self.app.check_db_connection():
            return
            
        if not hasattr(self.app, 'current_user') or self.app.current_user['role'] != 'admin':
            messagebox.showerror("Permission Denied", "Only admin users can delete transactions")
            return
            
        income_selected = self.report_income_tree.selection()
        expense_selected = self.report_expense_tree.selection()
        
        if not income_selected and not expense_selected:
            messagebox.showwarning("Warning", "No transactions selected for deletion")
            return
        
        if not messagebox.askyesno("Confirm", "Delete selected transactions?"):
            return
        
        to_delete = []
        
        for item in income_selected:
            values = self.report_income_tree.item(item, 'values')
            cursor = self.app.db.conn.cursor()
            cursor.execute("""
            SELECT id FROM transactions 
            WHERE registration_date = ? 
            AND description = ?
            AND currency = ?
            AND amount = ?
            AND transaction_type = 'income'
            AND deleted = 0
            """, (
                datetime.strptime(values[0], "%d-%m-%Y %H:%M").strftime("%Y-%m-%d %H:%M:%S"),
                values[1],
                values[2],
                float(values[3].replace(',', ''))
            ))
            result = cursor.fetchone()
            if result:
                to_delete.append(result[0])
        
        for item in expense_selected:
            values = self.report_expense_tree.item(item, 'values')
            cursor = self.app.db.conn.cursor()
            cursor.execute("""
            SELECT id FROM transactions 
            WHERE registration_date = ? 
            AND description = ?
            AND currency = ?
            AND amount = ?
            AND transaction_type = 'expense'
            AND deleted = 0
            """, (
                datetime.strptime(values[0], "%d-%m-%Y %H:%M").strftime("%Y-%m-%d %H:%M:%S"),
                values[1],
                values[2],
                float(values[3].replace(',', ''))
            ))
            result = cursor.fetchone()
            if result:
                to_delete.append(result[0])
        
        success_count = 0
        for transaction_id in to_delete:
            if self.app.db.soft_delete_transaction(transaction_id, self.app.current_user['id']):
                success_count += 1
        
        self.logger.info(
            f"User {self.app.current_user['username']} deleted {success_count} of {len(to_delete)} transactions"
        )
        
        messagebox.showinfo("Success", f"Deleted {success_count} of {len(to_delete)} transactions")
        self.generate_report()
        self.app.view_balances_tab.update_balances_view()

    def export_report_to_csv(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv", 
            filetypes=[("CSV files", "*.csv")],
            title="Save Report As"
        )
        if not file_path:
            return

        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    "Date", "Description", "Currency", "Amount", 
                    "Type", "Document Name", "Document Size (MB)"
                ])

                for row in self.report_income_tree.get_children():
                    values = self.report_income_tree.item(row)['values']
                    doc_info = values[4] if len(values) > 4 else ''
                    doc_name = doc_info.split()[0] if doc_info else ''
                    doc_size = doc_info.split('(')[1].split('MB')[0] if doc_info and '(' in doc_info else ''
                    writer.writerow([
                        values[0], values[1], values[2], values[3],
                        'Income', doc_name, doc_size
                    ])

                for row in self.report_expense_tree.get_children():
                    values = self.report_expense_tree.item(row)['values']
                    doc_info = values[4] if len(values) > 4 else ''
                    doc_name = doc_info.split()[0] if doc_info else ''
                    doc_size = doc_info.split('(')[1].split('MB')[0] if doc_info and '(' in doc_info else ''
                    writer.writerow([
                        values[0], values[1], values[2], values[3],
                        'Expense', doc_name, doc_size
                    ])

            self.logger.info(f"Report exported to {file_path}")
            messagebox.showinfo("Success", "Report exported successfully!")
        except Exception as e:
            error_msg = f"Failed to export report: {str(e)}"
            self.logger.error(error_msg)
            messagebox.showerror("Error", error_msg)