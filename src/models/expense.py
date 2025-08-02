import sqlite3
from datetime import datetime
from src.database_sqlite import get_db_connection

def format_datetime(dt):
    if isinstance(dt, str):
        return dt
    return dt.isoformat() if dt else None

class Expense:
    def __init__(self, id, shop_id, title, amount, category, supplier_id, date, description, payment_method, created_at, updated_at):
        self.id = id
        self.shop_id = shop_id
        self.title = title
        self.amount = amount
        self.category = category
        self.supplier_id = supplier_id
        self.date = date
        self.description = description
        self.payment_method = payment_method
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def create(cls, shop_id, data):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO expenses (shop_id, title, amount, category, supplier_id, date, description, payment_method, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                shop_id,
                data['title'],
                float(data['amount']),
                data['category'],
                data.get('supplier_id'),
                data['date'],
                data.get('description', ''),
                data.get('payment_method', 'cash'),
                datetime.now(),
                datetime.now()
            ))
            
            expense_id = cursor.lastrowid
            conn.commit()
            
            return cls.get_by_id(expense_id)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @classmethod
    def get_by_id(cls, expense_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.*, s.name as supplier_name
            FROM expenses e
            LEFT JOIN suppliers s ON e.supplier_id = s.id
            WHERE e.id = ?
        ''', (expense_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            expense = cls(
                id=row[0], shop_id=row[1], title=row[2], amount=row[3],
                category=row[4], supplier_id=row[5], date=row[6],
                description=row[7], payment_method=row[8],
                created_at=row[9], updated_at=row[10]
            )
            expense.supplier = {'id': row[5], 'name': row[11]} if row[5] else None
            return expense
        return None

    @classmethod
    def get_by_shop_id(cls, shop_id, search=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT e.*, s.name as supplier_name
            FROM expenses e
            LEFT JOIN suppliers s ON e.supplier_id = s.id
            WHERE e.shop_id = ?
        '''
        params = [shop_id]
        
        if search:
            query += ' AND (e.title LIKE ? OR e.category LIKE ? OR s.name LIKE ?)'
            search_term = f'%{search}%'
            params.extend([search_term, search_term, search_term])
        
        query += ' ORDER BY e.date DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        expenses = []
        for row in rows:
            expense = cls(
                id=row[0], shop_id=row[1], title=row[2], amount=row[3],
                category=row[4], supplier_id=row[5], date=row[6],
                description=row[7], payment_method=row[8],
                created_at=row[9], updated_at=row[10]
            )
            expense.supplier = {'id': row[5], 'name': row[11]} if row[5] else None
            expenses.append(expense)
        
        return expenses

    def update(self, data):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE expenses 
                SET title = ?, amount = ?, category = ?, supplier_id = ?, 
                    date = ?, description = ?, payment_method = ?, updated_at = ?
                WHERE id = ?
            ''', (
                data['title'],
                float(data['amount']),
                data['category'],
                data.get('supplier_id'),
                data['date'],
                data.get('description', ''),
                data.get('payment_method', 'cash'),
                datetime.now(),
                self.id
            ))
            
            conn.commit()
            return self.get_by_id(self.id)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def delete(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM expenses WHERE id = ?', (self.id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def to_dict(self):
        return {
            'id': self.id,
            'shop_id': self.shop_id,
            'title': self.title,
            'amount': self.amount,
            'category': self.category,
            'supplier_id': self.supplier_id,
            'supplier': self.supplier,
            'date': self.date,
            'description': self.description,
            'payment_method': self.payment_method,
            'created_at': format_datetime(self.created_at),
            'updated_at': format_datetime(self.updated_at)
        } 