import sqlite3
from datetime import datetime
from src.database_sqlite import get_db_connection

def format_datetime(dt):
    if isinstance(dt, str):
        return dt
    return dt.isoformat() if dt else None

class PurchaseOrder:
    def __init__(self, id, shop_id, supplier_id, po_number, order_date, expected_delivery, total_amount, status, notes, created_at, updated_at, supplier=None):
        self.id = id
        self.shop_id = shop_id
        self.supplier_id = supplier_id
        self.po_number = po_number
        self.order_date = order_date
        self.expected_delivery = expected_delivery
        self.total_amount = total_amount
        self.status = status
        self.notes = notes
        self.created_at = created_at
        self.updated_at = updated_at
        self.supplier = supplier

    @classmethod
    def create(cls, shop_id, data):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Generate PO number
            po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{shop_id:03d}"
            
            cursor.execute('''
                INSERT INTO purchase_orders (shop_id, supplier_id, po_number, order_date, expected_delivery, total_amount, status, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                shop_id,
                data['supplier_id'],
                po_number,
                data['order_date'],
                data.get('expected_delivery'),
                float(data.get('total_amount', 0)),
                data.get('status', 'pending'),
                data.get('notes', ''),
                datetime.now(),
                datetime.now()
            ))
            
            po_id = cursor.lastrowid
            conn.commit()
            
            return cls.get_by_id(po_id)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @classmethod
    def get_by_id(cls, po_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT po.*, s.name as supplier_name, s.contact_person, s.phone, s.email
            FROM purchase_orders po
            LEFT JOIN suppliers s ON po.supplier_id = s.id
            WHERE po.id = ?
        ''', (po_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            po = cls(
                id=row[0], shop_id=row[1], supplier_id=row[2], po_number=row[3],
                order_date=row[4], expected_delivery=row[5], total_amount=row[6],
                status=row[7], notes=row[8], created_at=row[9], updated_at=row[10]
            )
            if row[2]:  # supplier_id
                po.supplier = {
                    'id': row[2],
                    'name': row[11],
                    'contact_person': row[12],
                    'phone': row[13],
                    'email': row[14]
                }
            return po
        return None

    @classmethod
    def get_by_shop_id(cls, shop_id, search=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT po.*, s.name as supplier_name, s.contact_person, s.phone, s.email
            FROM purchase_orders po
            LEFT JOIN suppliers s ON po.supplier_id = s.id
            WHERE po.shop_id = ?
        '''
        params = [shop_id]
        
        if search:
            query += ' AND (po.po_number LIKE ? OR s.name LIKE ? OR po.status LIKE ?)'
            search_term = f'%{search}%'
            params.extend([search_term, search_term, search_term])
        
        query += ' ORDER BY po.order_date DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        purchase_orders = []
        for row in rows:
            po = cls(
                id=row[0], shop_id=row[1], supplier_id=row[2], po_number=row[3],
                order_date=row[4], expected_delivery=row[5], total_amount=row[6],
                status=row[7], notes=row[8], created_at=row[9], updated_at=row[10]
            )
            if row[2]:  # supplier_id
                po.supplier = {
                    'id': row[2],
                    'name': row[11],
                    'contact_person': row[12],
                    'phone': row[13],
                    'email': row[14]
                }
            purchase_orders.append(po)
        
        return purchase_orders

    def update(self, data):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE purchase_orders 
                SET supplier_id = ?, order_date = ?, expected_delivery = ?, 
                    total_amount = ?, status = ?, notes = ?, updated_at = ?
                WHERE id = ?
            ''', (
                data.get('supplier_id', self.supplier_id),
                data.get('order_date', self.order_date),
                data.get('expected_delivery', self.expected_delivery),
                float(data.get('total_amount', self.total_amount)),
                data.get('status', self.status),
                data.get('notes', self.notes),
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
            cursor.execute('DELETE FROM purchase_orders WHERE id = ?', (self.id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def to_dict(self):
        return {
            'id': self.id,
            'shop_id': self.shop_id,
            'supplier_id': self.supplier_id,
            'po_number': self.po_number,
            'order_date': self.order_date,
            'expected_delivery': self.expected_delivery,
            'total_amount': self.total_amount,
            'status': self.status,
            'notes': self.notes,
            'created_at': format_datetime(self.created_at),
            'updated_at': format_datetime(self.updated_at),
            'supplier': self.supplier
        } 