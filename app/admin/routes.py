from flask import Blueprint, render_template, jsonify, request
from app.auth.middleware import admin_required
from app.models.user import User
from app.models.contract import Contract
from app.models.upload import Upload
from app.utils.response_utils import success_response, error_response
from datetime import datetime, timedelta
import psutil
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required()
def dashboard():
    """Admin dashboard with system overview"""
    # Get statistics
    stats = {
        'total_users': User.query.count(),
        'active_contracts': Contract.query.filter_by(status='active').count(),
        'total_files': Upload.query.count()
    }
    
    # Get system status
    system_status = {
        'healthy': True,
        'last_check': datetime.utcnow()
    }
    
    # Get services status
    services_status = [
        {
            'name': 'Database',
            'status': 'healthy'
        },
        {
            'name': 'Blockchain',
            'status': 'healthy'
        },
        {
            'name': 'Storage',
            'status': 'healthy'
        }
    ]
    
    # Get system resources
    system_resources = {
        'cpu_usage': psutil.cpu_percent(),
        'memory_usage': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent
    }
    
    # Get recent activity
    recent_activity = get_recent_activity()
    
    return render_template(
        'admin/dashboard.html',
        stats=stats,
        system_status=system_status,
        services_status=services_status,
        system_resources=system_resources,
        recent_activity=recent_activity
    )

@admin_bp.route('/users')
@admin_required()
def users():
    """Users management page"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Get users with pagination
    pagination = User.query.paginate(page=page, per_page=per_page)
    
    return render_template(
        'admin/users.html',
        users=pagination.items,
        pagination={
            'current': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': range(1, pagination.pages + 1),
            'start': (page - 1) * per_page + 1,
            'end': min(page * per_page, pagination.total)
        }
    )

@admin_bp.route('/contracts')
@admin_required()
def contracts():
    """Contracts management page"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Get contracts with pagination
    pagination = Contract.query.paginate(page=page, per_page=per_page)
    
    return render_template(
        'admin/contracts.html',
        contracts=pagination.items,
        pagination={
            'current': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': range(1, pagination.pages + 1),
            'start': (page - 1) * per_page + 1,
            'end': min(page * per_page, pagination.total)
        }
    )

@admin_bp.route('/files')
@admin_required()
def files():
    """Files management page"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Get files with pagination
    pagination = Upload.query.paginate(page=page, per_page=per_page)
    
    return render_template(
        'admin/files.html',
        files=pagination.items,
        pagination={
            'current': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': range(1, pagination.pages + 1),
            'start': (page - 1) * per_page + 1,
            'end': min(page * per_page, pagination.total)
        }
    )

# API endpoints for admin actions
@admin_bp.route('/api/users/<int:user_id>', methods=['GET'])
@admin_required()
def get_user(user_id):
    """Get user details"""
    user = User.query.get_or_404(user_id)
    return success_response(user.to_dict())

@admin_bp.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required()
def toggle_user_status(user_id):
    """Toggle user active status"""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        return error_response('Cannot modify admin status', 403)
    
    user.is_active = not user.is_active
    db.session.commit()
    
    return success_response({'status': user.is_active})

@admin_bp.route('/api/users/filter')
@admin_required()
def filter_users():
    """Filter users based on search criteria"""
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    status = request.args.get('status', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.name.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )
    
    if role:
        query = query.filter_by(is_admin=(role == 'admin'))
    
    if status:
        query = query.filter_by(is_active=(status == 'active'))
    
    users = query.all()
    return success_response([user.to_dict() for user in users])

@admin_bp.route('/api/contracts/<string:cid>')
@admin_required()
def get_contract(cid):
    """Get contract details"""
    contract = Contract.query.filter_by(initial_cid=cid).first_or_404()
    return success_response(contract.to_dict())

@admin_bp.route('/api/contracts/<string:cid>/cancel', methods=['POST'])
@admin_required()
def cancel_contract(cid):
    """Cancel a contract"""
    contract = Contract.query.filter_by(initial_cid=cid).first_or_404()
    
    if contract.status != 'draft':
        return error_response('Can only cancel draft contracts', 400)
    
    contract.status = 'cancelled'
    db.session.commit()
    
    return success_response({'status': 'cancelled'})

@admin_bp.route('/api/contracts/filter')
@admin_required()
def filter_contracts():
    """Filter contracts based on search criteria"""
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    date_filter = request.args.get('date', '')
    
    query = Contract.query
    
    if search:
        query = query.filter(
            (Contract.title.ilike(f'%{search}%')) |
            (Contract.contractor_name.ilike(f'%{search}%')) |
            (Contract.provider_name.ilike(f'%{search}%'))
        )
    
    if status:
        query = query.filter_by(status=status)
    
    if date_filter:
        today = datetime.utcnow().date()
        if date_filter == 'today':
            query = query.filter(Contract.created_at >= today)
        elif date_filter == 'week':
            query = query.filter(Contract.created_at >= today - timedelta(days=7))
        elif date_filter == 'month':
            query = query.filter(Contract.created_at >= today - timedelta(days=30))
    
    contracts = query.all()
    return success_response([contract.to_dict() for contract in contracts])

def get_recent_activity(limit=10):
    """Get recent system activity"""
    activity = []
    
    # Get recent contracts
    contracts = Contract.query.order_by(Contract.created_at.desc()).limit(limit).all()
    for contract in contracts:
        activity.append({
            'type': 'contract',
            'description': f'New contract created: {contract.title}',
            'user': contract.creator.name,
            'timestamp': contract.created_at,
            'icon': 'file-contract',
            'color': 'blue'
        })
    
    # Get recent uploads
    uploads = Upload.query.order_by(Upload.created_at.desc()).limit(limit).all()
    for upload in uploads:
        activity.append({
            'type': 'upload',
            'description': f'File uploaded: {upload.filename}',
            'user': upload.user.name,
            'timestamp': upload.created_at,
            'icon': 'upload',
            'color': 'green'
        })
    
    # Sort by timestamp
    activity.sort(key=lambda x: x['timestamp'], reverse=True)
    return activity[:limit]
