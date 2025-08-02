import sqlite3
from datetime import datetime
from src.database_sqlite import get_db_connection

class Shop:
    def __init__(self, id=None, user_id=None, shop_name=None, owner_name=None, 
                 phone=None, address=None, city=None, state=None, pincode=None,
                 gst_number=None, license_number=None, is_active=False, 
                 subscription_status='inactive', created_at=None, updated_at=None):
        self.id = id
        self.user_id = user_id
        self.shop_name = shop_name
        self.owner_name = owner_name
        self.phone = phone
        self.address = address
        self.city = city
        self.state = state
        self.pincode = pincode
        self.gst_number = gst_number
        self.license_number = license_number
        self.is_active = is_active
        self.subscription_status = subscription_status
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def create(cls, user_id, shop_data):
        """Create a new shop"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO shops (
                    user_id, shop_name, owner_name, phone, address, city, state, 
                    pincode, gst_number, license_number, is_active, subscription_status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, shop_data.get('shop_name'), shop_data.get('owner_name'),
                shop_data.get('phone'), shop_data.get('address'), shop_data.get('city'),
                shop_data.get('state'), shop_data.get('pincode'), shop_data.get('gst_number'),
                shop_data.get('license_number'), False, 'inactive',
                datetime.now(), datetime.now()
            ))
            
            shop_id = cursor.lastrowid
            conn.commit()
            
            return cls.get_by_id(shop_id)
            
        except sqlite3.Error as e:
            conn.rollback()
            raise Exception(f"Database error: {e}")
        finally:
            conn.close()

    @classmethod
    def get_by_id(cls, shop_id):
        """Get shop by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM shops WHERE id = ?', (shop_id,))
            row = cursor.fetchone()
            
            if row:
                return cls(*row)
            return None
            
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
        finally:
            conn.close()

    @classmethod
    def get_by_user_id(cls, user_id):
        """Get shop by user ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM shops WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if row:
                return cls(*row)
            return None
            
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
        finally:
            conn.close()

    @classmethod
    def get_all_paginated(cls, page=1, limit=10, search=''):
        """Get all shops with pagination and search"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            offset = (page - 1) * limit
            
            if search:
                cursor.execute('''
                    SELECT s.*, u.email FROM shops s
                    LEFT JOIN users u ON s.user_id = u.id
                    WHERE s.shop_name LIKE ? OR s.owner_name LIKE ? OR u.email LIKE ?
                    ORDER BY s.created_at DESC
                    LIMIT ? OFFSET ?
                ''', (f'%{search}%', f'%{search}%', f'%{search}%', limit, offset))
            else:
                cursor.execute('''
                    SELECT s.*, u.email FROM shops s
                    LEFT JOIN users u ON s.user_id = u.id
                    ORDER BY s.created_at DESC
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
            
            rows = cursor.fetchall()
            shops = []
            
            for row in rows:
                shop = cls(*row[:-1])  # Exclude email from shop object
                shop.email = row[-1]   # Add email as separate attribute
                shops.append(shop)
            
            return shops
            
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
        finally:
            conn.close()

    @classmethod
    def count_all(cls):
        """Count all shops"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT COUNT(*) FROM shops')
            return cursor.fetchone()[0]
            
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
        finally:
            conn.close()

    @classmethod
    def count_active(cls):
        """Count active shops"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT COUNT(*) FROM shops WHERE is_active = 1')
            return cursor.fetchone()[0]
            
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
        finally:
            conn.close()

    def activate(self):
        """Activate the shop"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE shops 
                SET is_active = 1, subscription_status = 'active', updated_at = ?
                WHERE id = ?
            ''', (datetime.now(), self.id))
            
            conn.commit()
            self.is_active = True
            self.subscription_status = 'active'
            
        except sqlite3.Error as e:
            conn.rollback()
            raise Exception(f"Database error: {e}")
        finally:
            conn.close()

    def deactivate(self):
        """Deactivate the shop"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE shops 
                SET is_active = 0, subscription_status = 'inactive', updated_at = ?
                WHERE id = ?
            ''', (datetime.now(), self.id))
            
            conn.commit()
            self.is_active = False
            self.subscription_status = 'inactive'
            
        except sqlite3.Error as e:
            conn.rollback()
            raise Exception(f"Database error: {e}")
        finally:
            conn.close()

    def get_dashboard_stats(self):
        """Get dashboard statistics for the shop"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Get total customers
            cursor.execute('SELECT COUNT(*) FROM customers WHERE shop_id = ?', (self.id,))
            total_customers = cursor.fetchone()[0]
            
            # Get total products
            cursor.execute('SELECT COUNT(*) FROM products WHERE shop_id = ?', (self.id,))
            total_products = cursor.fetchone()[0]
            
            # Get total invoices
            cursor.execute('SELECT COUNT(*) FROM invoices WHERE shop_id = ?', (self.id,))
            total_invoices = cursor.fetchone()[0]
            
            # Get total revenue (sum of all invoice totals)
            cursor.execute('''
                SELECT COALESCE(SUM(total_amount), 0) 
                FROM invoices 
                WHERE shop_id = ?
            ''', (self.id,))
            total_revenue = cursor.fetchone()[0] or 0
            
            # Get today's sales
            cursor.execute('''
                SELECT COALESCE(SUM(total_amount), 0) 
                FROM invoices 
                WHERE shop_id = ? 
                AND DATE(created_at) = DATE('now')
            ''', (self.id,))
            today_sales = cursor.fetchone()[0] or 0
            
            # Get today's invoices count
            cursor.execute('''
                SELECT COUNT(*) 
                FROM invoices 
                WHERE shop_id = ? 
                AND DATE(created_at) = DATE('now')
            ''', (self.id,))
            today_invoices = cursor.fetchone()[0]
            
            # Get this month's revenue
            cursor.execute('''
                SELECT COALESCE(SUM(total_amount), 0) 
                FROM invoices 
                WHERE shop_id = ? 
                AND created_at >= date('now', 'start of month')
            ''', (self.id,))
            monthly_revenue = cursor.fetchone()[0] or 0
            
            # Get this month's invoices count
            cursor.execute('''
                SELECT COUNT(*) 
                FROM invoices 
                WHERE shop_id = ? 
                AND created_at >= date('now', 'start of month')
            ''', (self.id,))
            monthly_invoices = cursor.fetchone()[0]
            
            # Get pending payments (sum of balance amounts)
            cursor.execute('''
                SELECT COALESCE(SUM(balance_amount), 0) 
                FROM invoices 
                WHERE shop_id = ? 
                AND balance_amount > 0
            ''', (self.id,))
            pending_payments = cursor.fetchone()[0] or 0
            
            # Get low stock products count
            cursor.execute('''
                SELECT COUNT(*) 
                FROM products 
                WHERE shop_id = ? 
                AND stock_quantity <= min_stock_level 
                AND is_active = 1
            ''', (self.id,))
            low_stock_count = cursor.fetchone()[0]
            
            # Get low stock products details
            cursor.execute('''
                SELECT id, name, category, stock_quantity, min_stock_level, unit
                FROM products 
                WHERE shop_id = ? 
                AND stock_quantity <= min_stock_level 
                AND is_active = 1
                ORDER BY stock_quantity ASC
                LIMIT 10
            ''', (self.id,))
            low_stock_products = []
            for row in cursor.fetchall():
                low_stock_products.append({
                    'id': row[0],
                    'name': row[1],
                    'category': row[2],
                    'stock_quantity': row[3],
                    'min_stock_level': row[4],
                    'unit': row[5]
                })
            
            # Get recent invoices
            cursor.execute('''
                SELECT i.id, i.invoice_number, i.total_amount, i.status, i.created_at,
                       c.name as customer_name
                FROM invoices i
                LEFT JOIN customers c ON i.customer_id = c.id
                WHERE i.shop_id = ?
                ORDER BY i.created_at DESC
                LIMIT 10
            ''', (self.id,))
            recent_invoices = []
            for row in cursor.fetchall():
                recent_invoices.append({
                    'id': row[0],
                    'invoice_number': row[1],
                    'total_amount': row[2],
                    'status': row[3],
                    'created_at': row[4],
                    'customer': {'name': row[5]} if row[5] else None
                })
            
            return {
                'total_customers': total_customers,
                'total_products': total_products,
                'total_invoices': total_invoices,
                'total_revenue': total_revenue,
                'today_sales': today_sales,
                'today_invoices': today_invoices,
                'monthly_revenue': monthly_revenue,
                'monthly_invoices': monthly_invoices,
                'pending_payments': pending_payments,
                'low_stock_count': low_stock_count,
                'low_stock_products': low_stock_products,
                'recent_invoices': recent_invoices
            }
            
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
        finally:
            conn.close()

    def update(self, shop_data):
        """Update shop information"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE shops 
                SET shop_name = ?, owner_name = ?, phone = ?, address = ?, 
                    city = ?, state = ?, pincode = ?, gst_number = ?, 
                    license_number = ?, updated_at = ?
                WHERE id = ?
            ''', (
                shop_data.get('shop_name', self.shop_name),
                shop_data.get('owner_name', self.owner_name),
                shop_data.get('phone', self.phone),
                shop_data.get('address', self.address),
                shop_data.get('city', self.city),
                shop_data.get('state', self.state),
                shop_data.get('pincode', self.pincode),
                shop_data.get('gst_number', self.gst_number),
                shop_data.get('license_number', self.license_number),
                datetime.now(),
                self.id
            ))
            
            conn.commit()
            
            # Update instance attributes
            for key, value in shop_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
        except sqlite3.Error as e:
            conn.rollback()
            raise Exception(f"Database error: {e}")
        finally:
            conn.close()

    def to_dict(self):
        """Convert shop to dictionary"""
        def format_datetime(dt):
            """Helper function to format datetime or string"""
            if dt is None:
                return None
            if isinstance(dt, str):
                return dt
            if hasattr(dt, 'isoformat'):
                return dt.isoformat()
            return str(dt)
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'shop_name': self.shop_name,
            'owner_name': self.owner_name,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'pincode': self.pincode,
            'gst_number': self.gst_number,
            'license_number': self.license_number,
            'is_active': self.is_active,
            'subscription_status': self.subscription_status,
            'created_at': format_datetime(self.created_at),
            'updated_at': format_datetime(self.updated_at),
            'email': getattr(self, 'email', None)  # Include email if available
        }

