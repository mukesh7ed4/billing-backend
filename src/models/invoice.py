import sqlite3
from datetime import datetime, date
from src.database_sqlite import get_db_connection

class Invoice:
    def __init__(self, id=None, shop_id=None, customer_id=None, invoice_number=None,
                 invoice_date=None, due_date=None, subtotal=None, tax_amount=0,
                 discount_amount=0, total_amount=None, paid_amount=0, balance_amount=None,
                 status='pending', notes=None, original_invoice_id=None, created_at=None, updated_at=None):
        self.id = id
        self.shop_id = shop_id
        self.customer_id = customer_id
        self.invoice_number = invoice_number
        self.invoice_date = invoice_date
        self.due_date = due_date
        self.subtotal = subtotal
        self.tax_amount = tax_amount
        self.discount_amount = discount_amount
        self.total_amount = total_amount
        self.paid_amount = paid_amount
        self.balance_amount = balance_amount
        self.status = status
        self.notes = notes
        self.original_invoice_id = original_invoice_id
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def generate_invoice_number(cls, shop_id):
        """Generate unique invoice number"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM invoices WHERE shop_id = ?
            ''', (shop_id,))
            count = cursor.fetchone()[0]
            
            today = date.today()
            return f"INV-{shop_id}-{today.strftime('%Y%m%d')}-{count + 1:04d}"

    @classmethod
    def create(cls, shop_id, invoice_data, items_data):
        """Create a new invoice with items"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Generate invoice number if not provided
            invoice_number = invoice_data.get('invoice_number') or cls.generate_invoice_number(shop_id)
            
            # Calculate totals
            subtotal = sum(float(item['quantity'] or 0) * float(item['unit_price'] or 0) for item in items_data)
            tax_amount = float(invoice_data.get('tax_amount', 0) or 0)
            discount_amount = float(invoice_data.get('discount_amount', 0) or 0)
            total_amount = subtotal + tax_amount - discount_amount
            
            # Handle immediate payment if provided
            initial_payment = float(invoice_data.get('initial_payment', 0) or 0)
            paid_amount = initial_payment
            balance_amount = total_amount - paid_amount
            
            # Determine initial status
            if balance_amount <= 0:
                status = 'paid'
            elif paid_amount > 0:
                status = 'partial'
            else:
                status = 'pending'
            
            # Create invoice
            cursor.execute('''
                INSERT INTO invoices (
                    shop_id, customer_id, invoice_number, invoice_date, due_date,
                    subtotal, tax_amount, discount_amount, total_amount,
                    paid_amount, balance_amount, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                shop_id, invoice_data.get('customer_id') if invoice_data.get('customer_id') != 'walk-in' else None,
                invoice_number, invoice_data['invoice_date'],
                invoice_data.get('due_date'), subtotal, tax_amount,
                discount_amount, total_amount, paid_amount,
                balance_amount, status, invoice_data.get('notes')
            ))
            
            invoice_id = cursor.lastrowid
            
            # Create invoice items
            for item in items_data:
                quantity = float(item['quantity'] or 0)
                unit_price = float(item['unit_price'] or 0)
                total_price = quantity * unit_price
                
                # Get product details
                cursor.execute('SELECT name, unit FROM products WHERE id = ?', (item['product_id'],))
                product_result = cursor.fetchone()
                if not product_result:
                    raise Exception(f"Product with ID {item['product_id']} not found")
                
                product_name, product_unit = product_result
                
                cursor.execute('''
                    INSERT INTO invoice_items (
                        invoice_id, product_id, product_name, unit, quantity, unit_price, total_price
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    invoice_id, item['product_id'], product_name, product_unit, quantity,
                    unit_price, total_price
                ))
                
                # Update product stock
                cursor.execute('''
                    UPDATE products 
                    SET stock_quantity = stock_quantity - ?
                    WHERE id = ?
                ''', (int(quantity), item['product_id']))
            
            # Record initial payment if provided
            if initial_payment > 0:
                payment_method = invoice_data.get('payment_method', 'cash')
                payment_date = invoice_data.get('payment_date') or date.today()
                reference_number = invoice_data.get('reference_number')
                notes = invoice_data.get('payment_notes', 'Initial payment')
                
                cursor.execute('''
                    INSERT INTO invoice_payments (
                        invoice_id, amount, payment_method, payment_date,
                        reference_number, notes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    invoice_id, initial_payment, payment_method, payment_date,
                    reference_number, notes, datetime.now(), datetime.now()
                ))
            
            conn.commit()
            return cls.get_by_id(invoice_id)

    @classmethod
    def create_return_invoice(cls, original_invoice_id, return_data, items_data):
        """Create a return invoice (negative invoice) for returned items"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get original invoice
            original_invoice = cls.get_by_id(original_invoice_id)
            if not original_invoice:
                raise Exception("Original invoice not found")
            
            # Generate return invoice number
            return_invoice_number = f"RET-{original_invoice.invoice_number}"
            
            # Calculate totals (negative values for return)
            subtotal = -sum(float(item['quantity'] or 0) * float(item['unit_price'] or 0) for item in items_data)
            tax_amount = -float(return_data.get('tax_amount', 0) or 0)
            discount_amount = -float(return_data.get('discount_amount', 0) or 0)
            total_amount = subtotal + tax_amount - discount_amount
            
            # Create return invoice
            cursor.execute('''
                INSERT INTO invoices (
                    shop_id, customer_id, invoice_number, invoice_date, due_date,
                    subtotal, tax_amount, discount_amount, total_amount,
                    paid_amount, balance_amount, status, notes, original_invoice_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                original_invoice.shop_id, original_invoice.customer_id,
                return_invoice_number, return_data['return_date'],
                return_data.get('due_date'), subtotal, tax_amount,
                discount_amount, total_amount, 0, total_amount,
                'pending', f"Return for invoice {original_invoice.invoice_number}. {return_data.get('notes', '')}",
                original_invoice_id
            ))
            
            return_invoice_id = cursor.lastrowid
            
            # Create return invoice items
            for item in items_data:
                quantity = -float(item['quantity'] or 0)  # Negative quantity for return
                unit_price = float(item['unit_price'] or 0)
                total_price = quantity * unit_price
                
                # Get product details
                cursor.execute('SELECT name, unit FROM products WHERE id = ?', (item['product_id'],))
                product_result = cursor.fetchone()
                if not product_result:
                    raise Exception(f"Product with ID {item['product_id']} not found")
                
                product_name, product_unit = product_result
                
                cursor.execute('''
                    INSERT INTO invoice_items (
                        invoice_id, product_id, product_name, unit, quantity, unit_price, total_price
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    return_invoice_id, item['product_id'], product_name, product_unit, quantity,
                    unit_price, total_price
                ))
                
                # Update product stock (add back returned items)
                cursor.execute('''
                    UPDATE products 
                    SET stock_quantity = stock_quantity + ?
                    WHERE id = ?
                ''', (int(abs(quantity)), item['product_id']))
            
            conn.commit()
            return cls.get_by_id(return_invoice_id)

    @classmethod
    def get_by_id(cls, invoice_id):
        """Get invoice by ID"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM invoices WHERE id = ?', (invoice_id,))
            row = cursor.fetchone()
            
            if row:
                return cls(*row)
            return None

    @classmethod
    def get_by_shop_id(cls, shop_id, limit=None, offset=None, status=None, search=None):
        """Get invoices by shop ID with optional filtering"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT i.*, c.name as customer_name 
                FROM invoices i 
                LEFT JOIN customers c ON i.customer_id = c.id 
                WHERE i.shop_id = ?
            '''
            params = [shop_id]
            
            if status:
                query += ' AND i.status = ?'
                params.append(status)
            
            if search:
                query += ' AND (i.invoice_number LIKE ? OR c.name LIKE ?)'
                search_term = f'%{search}%'
                params.extend([search_term, search_term])
            
            query += ' ORDER BY i.created_at DESC'
            
            if limit:
                query += ' LIMIT ?'
                params.append(limit)
                if offset:
                    query += ' OFFSET ?'
                    params.append(offset)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            invoices = []
            for row in rows:
                invoice = cls(*row[:-1])  # Exclude customer_name from constructor
                invoice.customer_name = row[-1]  # Add customer_name as attribute
                invoices.append(invoice)
            
            return invoices

    @classmethod
    def get_by_customer_id(cls, customer_id, shop_id):
        """Get invoices by customer ID for a specific shop"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT i.*, c.name as customer_name 
                FROM invoices i 
                LEFT JOIN customers c ON i.customer_id = c.id 
                WHERE i.customer_id = ? AND i.shop_id = ?
                ORDER BY i.created_at DESC
            '''
            
            cursor.execute(query, (customer_id, shop_id))
            rows = cursor.fetchall()
            
            invoices = []
            for row in rows:
                invoice = cls(*row[:-1])  # Exclude customer_name from constructor
                invoice.customer_name = row[-1]  # Add customer_name as attribute
                invoices.append(invoice)
            
            return invoices

    def get_items(self):
        """Get invoice items"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, invoice_id, product_id, product_name, unit, quantity, unit_price, total_price, created_at
                FROM invoice_items
                WHERE invoice_id = ?
            ''', (self.id,))
            rows = cursor.fetchall()
            
            return [{
                'id': row[0],
                'invoice_id': row[1],
                'product_id': row[2],
                'product_name': row[3],
                'unit': row[4],
                'quantity': float(row[5]),
                'unit_price': float(row[6]),
                'total_price': float(row[7]),
                'created_at': row[8]
            } for row in rows]

    def get_payments(self):
        """Get invoice payments"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM invoice_payments 
                WHERE invoice_id = ? 
                ORDER BY payment_date DESC
            ''', (self.id,))
            rows = cursor.fetchall()
            
            from src.models.payment import InvoicePayment
            return [InvoicePayment(*row) for row in rows]

    def add_payment(self, amount, payment_method, payment_date=None, reference_number=None, notes=None):
        """Add payment to invoice"""
        if payment_date is None:
            payment_date = date.today()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Validate payment amount
            if amount <= 0:
                raise Exception("Payment amount must be positive")
            
            if amount > self.balance_amount:
                raise Exception("Payment amount cannot exceed balance amount")
            
            # Create payment record in invoice_payments table
            cursor.execute('''
                INSERT INTO invoice_payments (
                    invoice_id, amount, payment_method, payment_date,
                    reference_number, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.id, amount, payment_method, payment_date,
                reference_number, notes, datetime.now(), datetime.now()
            ))
            
            # Update invoice paid amount and balance
            new_paid_amount = self.paid_amount + amount
            new_balance_amount = self.total_amount - new_paid_amount
            
            # Update status based on balance
            if new_balance_amount <= 0:
                new_status = 'paid'
            elif new_paid_amount > 0:
                new_status = 'partial'
            else:
                new_status = 'pending'
            
            cursor.execute('''
                UPDATE invoices 
                SET paid_amount = ?, balance_amount = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_paid_amount, new_balance_amount, new_status, self.id))
            
            conn.commit()
            
            # Update instance attributes
            self.paid_amount = new_paid_amount
            self.balance_amount = new_balance_amount
            self.status = new_status
            
            return True

    def get_payment_history(self):
        """Get detailed payment history for this invoice"""
        payments = self.get_payments()
        return {
            'invoice_id': self.id,
            'invoice_number': self.invoice_number,
            'total_amount': float(self.total_amount),
            'paid_amount': float(self.paid_amount),
            'balance_amount': float(self.balance_amount),
            'status': self.status,
            'payments': [payment.to_dict() for payment in payments],
            'payment_count': len(payments),
            'last_payment_date': payments[0].payment_date if payments else None
        }

    def is_overdue(self):
        """Check if invoice is overdue"""
        if not self.due_date or self.status == 'paid':
            return False
        
        from datetime import date
        today = date.today()
        due_date = date.fromisoformat(self.due_date) if isinstance(self.due_date, str) else self.due_date
        return today > due_date

    def get_days_overdue(self):
        """Get number of days overdue"""
        if not self.is_overdue():
            return 0
        
        from datetime import date
        today = date.today()
        due_date = date.fromisoformat(self.due_date) if isinstance(self.due_date, str) else self.due_date
        return (today - due_date).days

    def get_payment_summary(self):
        """Get payment summary with statistics"""
        payments = self.get_payments()
        
        # Group payments by method
        payment_methods = {}
        for payment in payments:
            method = payment.payment_method
            if method not in payment_methods:
                payment_methods[method] = 0
            payment_methods[method] += float(payment.amount)
        
        return {
            'total_paid': float(self.paid_amount),
            'total_balance': float(self.balance_amount),
            'payment_count': len(payments),
            'payment_methods': payment_methods,
            'is_overdue': self.is_overdue(),
            'days_overdue': self.get_days_overdue(),
            'status': self.status
        }

    def can_add_payment(self, amount):
        """Check if a payment can be added"""
        if amount <= 0:
            return False, "Payment amount must be positive"
        
        if amount > self.balance_amount:
            return False, f"Payment amount ({amount}) cannot exceed balance ({self.balance_amount})"
        
        return True, "Payment can be added"

    def update_status(self, status):
        """Update invoice status"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE invoices 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, self.id))
            conn.commit()
            self.status = status
            return cursor.rowcount > 0

    def get_customer(self):
        """Get customer details"""
        if not self.customer_id:
            return None
        
        from src.models.customer import Customer
        return Customer.get_by_id(self.customer_id)

    def to_dict(self, include_items=False, include_customer=False):
        """Convert invoice to dictionary"""
        result = {
            'id': self.id,
            'shop_id': self.shop_id,
            'customer_id': self.customer_id,
            'invoice_number': self.invoice_number,
            'invoice_date': self.invoice_date,
            'due_date': self.due_date,
            'subtotal': float(self.subtotal),
            'tax_amount': float(self.tax_amount),
            'discount_amount': float(self.discount_amount),
            'total_amount': float(self.total_amount),
            'paid_amount': float(self.paid_amount),
            'balance_amount': float(self.balance_amount),
            'status': self.status,
            'notes': self.notes,
            'original_invoice_id': self.original_invoice_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        if include_items:
            result['items'] = self.get_items()
        
        if include_customer:
            customer = self.get_customer()
            result['customer'] = customer.to_dict() if customer else None
        
        return result

    def get_return_invoices(self):
        """Get all return invoices for this invoice"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM invoices 
                WHERE original_invoice_id = ? 
                ORDER BY created_at DESC
            ''', (self.id,))
            rows = cursor.fetchall()
            return [cls(*row) for row in rows]

    def get_total_returns(self):
        """Get total amount returned for this invoice"""
        return_invoices = self.get_return_invoices()
        return sum(abs(invoice.total_amount) for invoice in return_invoices)

    def get_net_amount(self):
        """Get net amount after returns"""
        return self.total_amount - self.get_total_returns()

class InvoiceItem:
    def __init__(self, id=None, invoice_id=None, product_id=None, product_name=None, unit=None,
                 quantity=None, unit_price=None, total_price=None, created_at=None):
        self.id = id
        self.invoice_id = invoice_id
        self.product_id = product_id
        self.product_name = product_name
        self.unit = unit
        self.quantity = quantity
        self.unit_price = unit_price
        self.total_price = total_price
        self.created_at = created_at

    def to_dict(self):
        """Convert invoice item to dictionary"""
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'unit': self.unit,
            'quantity': float(self.quantity),
            'unit_price': float(self.unit_price),
            'total_price': float(self.total_price),
            'created_at': self.created_at
        }

