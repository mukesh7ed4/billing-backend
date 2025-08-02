from flask import Blueprint, request, jsonify
from src.routes.auth import require_shop_user, get_current_shop_id
from src.models.shop import Shop
from src.models.customer import Customer
from src.models.product import Product
from src.models.invoice import Invoice
from src.models.payment import InvoicePayment
from src.database_sqlite import get_db_connection

shop_bp = Blueprint('shop', __name__)

@shop_bp.route('/dashboard', methods=['GET'])
@require_shop_user
def get_shop_dashboard():
    """Get shop dashboard statistics"""
    try:
        shop_id = get_current_shop_id()
        if not shop_id:
            return jsonify({'error': 'Shop not found'}), 404
        
        shop = Shop.get_by_id(shop_id)
        if not shop:
            return jsonify({'error': 'Shop not found'}), 404
        
        stats = shop.get_dashboard_stats()
        
        # Get recent invoices
        recent_invoices = Invoice.get_by_shop_id(shop_id, limit=5)
        
        # Get low stock products
        low_stock_products = Product.get_low_stock_products(shop_id)
        
        return jsonify({
            'shop': shop.to_dict(),
            'stats': stats,
            'recent_invoices': [invoice.to_dict(include_customer=True) for invoice in recent_invoices],
            'low_stock_products': [product.to_dict() for product in low_stock_products[:5]]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@shop_bp.route('/profile', methods=['GET'])
@require_shop_user
def get_shop_profile():
    """Get shop profile"""
    try:
        shop_id = get_current_shop_id()
        if not shop_id:
            return jsonify({'error': 'Shop not found'}), 404
        
        shop = Shop.get_by_id(shop_id)
        if not shop:
            return jsonify({'error': 'Shop not found'}), 404
        
        return jsonify({'shop': shop.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@shop_bp.route('/profile', methods=['PUT'])
@require_shop_user
def update_shop_profile():
    """Update shop profile"""
    try:
        shop_id = get_current_shop_id()
        if not shop_id:
            return jsonify({'error': 'Shop not found'}), 404
        
        shop = Shop.get_by_id(shop_id)
        if not shop:
            return jsonify({'error': 'Shop not found'}), 404
        
        data = request.get_json()
        
        # Update shop
        shop.update(data)
        return jsonify({
            'message': 'Shop profile updated successfully',
            'shop': shop.to_dict()
        }), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Customer routes
@shop_bp.route('/customers', methods=['GET'])
@require_shop_user
def get_customers():
    """Get shop customers"""
    try:
        shop_id = get_current_shop_id()
        if not shop_id:
            return jsonify({'error': 'Shop not found'}), 404
        
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        search = request.args.get('search')
        
        offset = (page - 1) * limit
        
        customers = Customer.get_by_shop_id(shop_id, limit=limit, offset=offset, search=search)
        
        # Get total count for pagination
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if search:
                cursor.execute('''
                    SELECT COUNT(*) FROM customers 
                    WHERE shop_id = ? AND (name LIKE ? OR phone LIKE ? OR email LIKE ?)
                ''', (shop_id, f'%{search}%', f'%{search}%', f'%{search}%'))
            else:
                cursor.execute('SELECT COUNT(*) FROM customers WHERE shop_id = ?', (shop_id,))
            total_count = cursor.fetchone()[0]
        
        return jsonify({
            'customers': [customer.to_dict() for customer in customers],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@shop_bp.route('/customers', methods=['POST'])
@require_shop_user
def create_customer():
    """Create new customer"""
    try:
        shop_id = get_current_shop_id()
        if not shop_id:
            return jsonify({'error': 'Shop not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Customer name is required'}), 400
        
        customer = Customer.create(shop_id, data)
        
        return jsonify({
            'message': 'Customer created successfully',
            'customer': customer.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@shop_bp.route('/customers/<int:customer_id>', methods=['PUT'])
@require_shop_user
def update_customer(customer_id):
    """Update customer"""
    try:
        shop_id = get_current_shop_id()
        if not shop_id:
            return jsonify({'error': 'Shop not found'}), 404
        
        customer = Customer.get_by_id(customer_id)
        if not customer or customer.shop_id != shop_id:
            return jsonify({'error': 'Customer not found'}), 404
        
        data = request.get_json()
        
        customer.update(data)
        return jsonify({
            'message': 'Customer updated successfully',
            'customer': customer.to_dict()
        }), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@shop_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
@require_shop_user
def delete_customer(customer_id):
    """Delete customer"""
    try:
        shop_id = get_current_shop_id()
        if not shop_id:
            return jsonify({'error': 'Shop not found'}), 404
        
        customer = Customer.get_by_id(customer_id)
        if not customer or customer.shop_id != shop_id:
            return jsonify({'error': 'Customer not found'}), 404
        
        if customer.delete():
            return jsonify({'message': 'Customer deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete customer'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@shop_bp.route('/customers/<int:customer_id>/invoices', methods=['GET'])
@require_shop_user
def get_customer_invoices(customer_id):
    """Get all invoices for a specific customer"""
    try:
        shop_id = get_current_shop_id()
        if not shop_id:
            return jsonify({'error': 'Shop not found'}), 404
        
        # Verify customer belongs to this shop
        customer = Customer.get_by_id(customer_id)
        if not customer or customer.shop_id != shop_id:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Get invoices for this customer
        invoices = Invoice.get_by_customer_id(customer_id, shop_id)
        
        return jsonify({
            'invoices': [invoice.to_dict(include_customer=False) for invoice in invoices]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@shop_bp.route('/customers/<int:customer_id>/payments', methods=['GET'])
@require_shop_user
def get_customer_payments(customer_id):
    """Get all payments for a specific customer"""
    try:
        shop_id = get_current_shop_id()
        if not shop_id:
            return jsonify({'error': 'Shop not found'}), 404
        
        # Verify customer belongs to this shop
        customer = Customer.get_by_id(customer_id)
        if not customer or customer.shop_id != shop_id:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Get payments for this customer
        payments = InvoicePayment.get_by_customer_id(customer_id, shop_id)
        
        return jsonify({
            'payments': [payment.to_dict() for payment in payments]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Product routes
@shop_bp.route('/products', methods=['GET'])
@require_shop_user
def get_products():
    """Get shop products"""
    try:
        shop_id = get_current_shop_id()
        if not shop_id:
            return jsonify({'error': 'Shop not found'}), 404
        
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        search = request.args.get('search')
        category = request.args.get('category')
        
        offset = (page - 1) * limit
        
        products = Product.get_by_shop_id(
            shop_id, limit=limit, offset=offset, 
            search=search, category=category
        )
        
        # Get total count for pagination
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = 'SELECT COUNT(*) FROM products WHERE shop_id = ? AND is_active = 1'
            params = [shop_id]
            
            if search:
                query += ' AND (name LIKE ? OR brand LIKE ? OR barcode LIKE ?)'
                params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
            
            if category:
                query += ' AND category = ?'
                params.append(category)
            
            cursor.execute(query, params)
            total_count = cursor.fetchone()[0]
        
        return jsonify({
            'products': [product.to_dict() for product in products],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@shop_bp.route('/products', methods=['POST'])
@require_shop_user
def create_product():
    """Create new product"""
    try:
        shop_id = get_current_shop_id()
        if not shop_id:
            return jsonify({'error': 'Shop not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'category', 'unit', 'price']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        product = Product.create(shop_id, data)
        
        return jsonify({
            'message': 'Product created successfully',
            'product': product.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@shop_bp.route('/products/<int:product_id>', methods=['PUT'])
@require_shop_user
def update_product(product_id):
    """Update product"""
    try:
        shop_id = get_current_shop_id()
        if not shop_id:
            return jsonify({'error': 'Shop not found'}), 404
        
        product = Product.get_by_id(product_id)
        if not product or product.shop_id != shop_id:
            return jsonify({'error': 'Product not found'}), 404
        
        data = request.get_json()
        
        product.update(**data)
        return jsonify({
            'message': 'Product updated successfully',
            'product': product.to_dict()
        }), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@shop_bp.route('/products/categories', methods=['GET'])
@require_shop_user
def get_product_categories():
    """Get product categories"""
    try:
        shop_id = get_current_shop_id()
        if not shop_id:
            return jsonify({'error': 'Shop not found'}), 404
        
        categories = Product.get_categories(shop_id)
        
        return jsonify({'categories': categories}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Invoice routes
@shop_bp.route('/invoices', methods=['GET'])
@require_shop_user
def get_invoices():
    """Get shop invoices"""
    try:
        shop_id = get_current_shop_id()
        if not shop_id:
            return jsonify({'error': 'Shop not found'}), 404
        
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        status = request.args.get('status')
        search = request.args.get('search')
        
        offset = (page - 1) * limit
        
        invoices = Invoice.get_by_shop_id(
            shop_id, limit=limit, offset=offset, 
            status=status, search=search
        )
        
        # Get total count for pagination
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = '''
                SELECT COUNT(*) FROM invoices i
                LEFT JOIN customers c ON i.customer_id = c.id
                WHERE i.shop_id = ?
            '''
            params = [shop_id]
            
            if status:
                query += ' AND i.status = ?'
                params.append(status)
            
            if search:
                query += ' AND (i.invoice_number LIKE ? OR c.name LIKE ?)'
                params.extend([f'%{search}%', f'%{search}%'])
            
            cursor.execute(query, params)
            total_count = cursor.fetchone()[0]
        
        return jsonify({
            'invoices': [invoice.to_dict(include_customer=True) for invoice in invoices],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@shop_bp.route('/invoices', methods=['POST'])
@require_shop_user
def create_invoice():
    """Create new invoice"""
    try:
        shop_id = get_current_shop_id()
        if not shop_id:
            return jsonify({'error': 'Shop not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('invoice_date'):
            return jsonify({'error': 'Invoice date is required'}), 400
        
        if not data.get('items') or len(data['items']) == 0:
            return jsonify({'error': 'Invoice items are required'}), 400
        
        # Validate items
        for item in data['items']:
            if not all(key in item for key in ['product_id', 'quantity', 'unit_price']):
                return jsonify({'error': 'Invalid item data'}), 400
            
            # Validate numeric values
            try:
                quantity = float(item['quantity'] or 0)
                unit_price = float(item['unit_price'] or 0)
                if quantity <= 0 or unit_price <= 0:
                    return jsonify({'error': 'Quantity and unit price must be greater than 0'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid numeric values in items'}), 400
        
        invoice = Invoice.create(shop_id, data, data['items'])
        
        return jsonify({
            'message': 'Invoice created successfully',
            'invoice': invoice.to_dict(include_items=True, include_customer=True)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@shop_bp.route('/invoices/<int:invoice_id>', methods=['GET'])
@require_shop_user
def get_invoice(invoice_id):
    """Get invoice details"""
    try:
        shop_id = get_current_shop_id()
        if not shop_id:
            return jsonify({'error': 'Shop not found'}), 404
        
        invoice = Invoice.get_by_id(invoice_id)
        if not invoice or invoice.shop_id != shop_id:
            return jsonify({'error': 'Invoice not found'}), 404
        
        return jsonify({
            'invoice': invoice.to_dict(include_items=True, include_customer=True)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@shop_bp.route('/invoices/<int:invoice_id>/payments', methods=['POST'])
@require_shop_user
def add_payment_to_invoice(invoice_id):
    """Add payment to invoice"""
    try:
        shop_id = get_current_shop_id()
        if not shop_id:
            return jsonify({'error': 'Shop not found'}), 404
        
        invoice = Invoice.get_by_id(invoice_id)
        if not invoice or invoice.shop_id != shop_id:
            return jsonify({'error': 'Invoice not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('amount') or not data.get('payment_method'):
            return jsonify({'error': 'Amount and payment method are required'}), 400
        
        if data['amount'] <= 0:
            return jsonify({'error': 'Payment amount must be positive'}), 400
        
        if data['amount'] > invoice.balance_amount:
            return jsonify({'error': 'Payment amount cannot exceed balance amount'}), 400
        
        # Add payment
        if invoice.add_payment(
            amount=data['amount'],
            payment_method=data['payment_method'],
            payment_date=data.get('payment_date'),
            reference_number=data.get('reference_number'),
            notes=data.get('notes')
        ):
            return jsonify({
                'message': 'Payment added successfully',
                'invoice': invoice.to_dict(include_items=True, include_customer=True)
            }), 200
        else:
            return jsonify({'error': 'Failed to add payment'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@shop_bp.route('/invoices/<int:invoice_id>/returns', methods=['POST'])
@require_shop_user
def create_return_invoice(invoice_id):
    """Create a return invoice for returned items"""
    try:
        shop_id = get_current_shop_id()
        if not shop_id:
            return jsonify({'error': 'Shop not found'}), 404
        
        # Get original invoice
        original_invoice = Invoice.get_by_id(invoice_id)
        if not original_invoice or original_invoice.shop_id != shop_id:
            return jsonify({'error': 'Invoice not found'}), 404
        
        # Check if invoice is already paid or has returns
        if original_invoice.status == 'paid':
            return jsonify({'error': 'Cannot return items from fully paid invoice'}), 400
        
        data = request.get_json()
        return_data = data.get('return_data', {})
        items_data = data.get('items', [])
        
        if not items_data:
            return jsonify({'error': 'No items specified for return'}), 400
        
        # Validate return items
        original_items = original_invoice.get_items()
        original_items_dict = {item['product_id']: item for item in original_items}
        
        for return_item in items_data:
            product_id = return_item.get('product_id')
            return_quantity = float(return_item.get('quantity', 0))
            
            if product_id not in original_items_dict:
                return jsonify({'error': f'Product {product_id} not found in original invoice'}), 400
            
            original_quantity = float(original_items_dict[product_id]['quantity'])
            if return_quantity > original_quantity:
                return jsonify({'error': f'Return quantity cannot exceed original quantity for product {product_id}'}), 400
        
        # Create return invoice
        return_invoice = Invoice.create_return_invoice(invoice_id, return_data, items_data)
        
        return jsonify({
            'message': 'Return invoice created successfully',
            'return_invoice': return_invoice.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@shop_bp.route('/invoices/<int:invoice_id>', methods=['DELETE'])
@require_shop_user
def delete_invoice(invoice_id):
    """Delete an invoice"""
    try:
        shop_id = get_current_shop_id()
        if not shop_id:
            return jsonify({'error': 'Shop not found'}), 404
        
        invoice = Invoice.get_by_id(invoice_id)
        if not invoice or invoice.shop_id != shop_id:
            return jsonify({'error': 'Invoice not found'}), 404
        
        # Check if invoice has payments
        payments = invoice.get_payments()
        if payments:
            return jsonify({'error': 'Cannot delete invoice with payments. Please delete payments first.'}), 400
        
        # Delete invoice items first
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM invoice_items WHERE invoice_id = ?', (invoice_id,))
            cursor.execute('DELETE FROM invoices WHERE id = ?', (invoice_id,))
            conn.commit()
        
        return jsonify({'message': 'Invoice deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

