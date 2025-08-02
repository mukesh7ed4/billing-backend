from flask import Blueprint, request, jsonify
from src.models.expense import Expense
from src.models.supplier import Supplier
from src.models.purchase_order import PurchaseOrder

expense_bp = Blueprint('expense', __name__)

@expense_bp.route('/expenses', methods=['GET'])
def get_expenses():
    try:
        shop_id = request.args.get('shop_id', type=int)
        search = request.args.get('search', '')
        
        if not shop_id:
            return jsonify({'error': 'Shop ID is required'}), 400
        
        expenses = Expense.get_by_shop_id(shop_id, search)
        return jsonify({
            'expenses': [expense.to_dict() for expense in expenses]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@expense_bp.route('/expenses', methods=['POST'])
def create_expense():
    try:
        data = request.get_json()
        shop_id = data.get('shop_id')
        
        if not shop_id:
            return jsonify({'error': 'Shop ID is required'}), 400
        
        required_fields = ['title', 'amount', 'category', 'date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        expense = Expense.create(shop_id, data)
        return jsonify(expense.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@expense_bp.route('/expenses/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    try:
        data = request.get_json()
        expense = Expense.get_by_id(expense_id)
        
        if not expense:
            return jsonify({'error': 'Expense not found'}), 404
        
        updated_expense = expense.update(data)
        return jsonify(updated_expense.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@expense_bp.route('/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    try:
        expense = Expense.get_by_id(expense_id)
        
        if not expense:
            return jsonify({'error': 'Expense not found'}), 404
        
        expense.delete()
        return jsonify({'message': 'Expense deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@expense_bp.route('/suppliers', methods=['GET'])
def get_suppliers():
    try:
        shop_id = request.args.get('shop_id', type=int)
        search = request.args.get('search', '')
        
        if not shop_id:
            return jsonify({'error': 'Shop ID is required'}), 400
        
        suppliers = Supplier.get_by_shop_id(shop_id, search)
        return jsonify({
            'suppliers': [supplier.to_dict() for supplier in suppliers]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@expense_bp.route('/suppliers', methods=['POST'])
def create_supplier():
    try:
        data = request.get_json()
        shop_id = data.get('shop_id')
        
        if not shop_id:
            return jsonify({'error': 'Shop ID is required'}), 400
        
        if not data.get('name'):
            return jsonify({'error': 'Supplier name is required'}), 400
        
        supplier = Supplier.create(shop_id, data)
        return jsonify(supplier.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@expense_bp.route('/suppliers/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    try:
        data = request.get_json()
        supplier = Supplier.get_by_id(supplier_id)
        
        if not supplier:
            return jsonify({'error': 'Supplier not found'}), 404
        
        updated_supplier = supplier.update(data)
        return jsonify(updated_supplier.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@expense_bp.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
def delete_supplier(supplier_id):
    try:
        supplier = Supplier.get_by_id(supplier_id)
        
        if not supplier:
            return jsonify({'error': 'Supplier not found'}), 404
        
        supplier.delete()
        return jsonify({'message': 'Supplier deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Purchase Order routes
@expense_bp.route('/purchase-orders', methods=['GET'])
def get_purchase_orders():
    try:
        shop_id = request.args.get('shop_id', type=int)
        search = request.args.get('search', '')
        
        if not shop_id:
            return jsonify({'error': 'Shop ID is required'}), 400
        
        purchase_orders = PurchaseOrder.get_by_shop_id(shop_id, search)
        return jsonify({
            'purchase_orders': [po.to_dict() for po in purchase_orders]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@expense_bp.route('/purchase-orders', methods=['POST'])
def create_purchase_order():
    try:
        data = request.get_json()
        shop_id = data.get('shop_id')
        
        if not shop_id:
            return jsonify({'error': 'Shop ID is required'}), 400
        
        required_fields = ['supplier_id', 'order_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        purchase_order = PurchaseOrder.create(shop_id, data)
        return jsonify(purchase_order.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@expense_bp.route('/purchase-orders/<int:po_id>', methods=['PUT'])
def update_purchase_order(po_id):
    try:
        data = request.get_json()
        purchase_order = PurchaseOrder.get_by_id(po_id)
        
        if not purchase_order:
            return jsonify({'error': 'Purchase order not found'}), 404
        
        updated_po = purchase_order.update(data)
        return jsonify(updated_po.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@expense_bp.route('/purchase-orders/<int:po_id>', methods=['DELETE'])
def delete_purchase_order(po_id):
    try:
        purchase_order = PurchaseOrder.get_by_id(po_id)
        
        if not purchase_order:
            return jsonify({'error': 'Purchase order not found'}), 404
        
        purchase_order.delete()
        return jsonify({'message': 'Purchase order deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

 