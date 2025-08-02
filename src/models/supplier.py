import sqlite3
from datetime import datetime
from src.database_sqlite import get_db_connection

def format_datetime(dt):
    if isinstance(dt, str):
        return dt
    return dt.isoformat() if dt else None

class Supplier:
    def __init__(self, id, shop_id, name, contact_person, phone, email, address, gst_number, created_at, updated_at):
        self.id = id
        self.shop_id = shop_id
        self.name = name
        self.contact_person = contact_person
        self.phone = phone
        self.email = email
        self.address = address
        self.gst_number = gst_number
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def create(cls, shop_id, data):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO suppliers (shop_id, name, contact_person, phone, email, address, gst_number, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                shop_id,
                data['name'],
                data.get('contact_person', ''),
                data.get('phone', ''),
                data.get('email', ''),
                data.get('address', ''),
                data.get('gst_number', ''),
                datetime.now(),
                datetime.now()
            ))
            
            supplier_id = cursor.lastrowid
            conn.commit()
            
            return cls.get_by_id(supplier_id)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @classmethod
    def get_by_id(cls, supplier_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM suppliers WHERE id = ?', (supplier_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls(
                id=row[0], shop_id=row[1], name=row[2], contact_person=row[3],
                phone=row[4], email=row[5], address=row[6], gst_number=row[7],
                created_at=row[8], updated_at=row[9]
            )
        return None

    @classmethod
    def get_by_shop_id(cls, shop_id, search=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM suppliers WHERE shop_id = ?'
        params = [shop_id]
        
        if search:
            query += ' AND (name LIKE ? OR contact_person LIKE ? OR phone LIKE ? OR email LIKE ?)'
            search_term = f'%{search}%'
            params.extend([search_term, search_term, search_term, search_term])
        
        query += ' ORDER BY name ASC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        suppliers = []
        for row in rows:
            supplier = cls(
                id=row[0], shop_id=row[1], name=row[2], contact_person=row[3],
                phone=row[4], email=row[5], address=row[6], gst_number=row[7],
                created_at=row[8], updated_at=row[9]
            )
            suppliers.append(supplier)
        
        return suppliers

    def update(self, data):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE suppliers 
                SET name = ?, contact_person = ?, phone = ?, email = ?, 
                    address = ?, gst_number = ?, updated_at = ?
                WHERE id = ?
            ''', (
                data['name'],
                data.get('contact_person', ''),
                data.get('phone', ''),
                data.get('email', ''),
                data.get('address', ''),
                data.get('gst_number', ''),
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
            cursor.execute('DELETE FROM suppliers WHERE id = ?', (self.id,))
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
            'name': self.name,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'gst_number': self.gst_number,
            'created_at': format_datetime(self.created_at),
            'updated_at': format_datetime(self.updated_at)
        } 