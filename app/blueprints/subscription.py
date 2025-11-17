#!/usr/bin/env python3
"""
Subscription API Blueprint
Handles subscription plans, user subscriptions, and usage tracking.
"""

from flask import Blueprint, request, jsonify
from functools import wraps

subscription_bp = Blueprint('subscription', __name__)

# These will be initialized lazily
auth_system = None
subscription_service = None


def _get_services():
    """Lazy initialization of services"""
    global auth_system, subscription_service
    if auth_system is None:
        from app.core.auth_system import get_auth_system
        auth_system, _ = get_auth_system()
    if subscription_service is None:
        from app.services.subscription_service import get_subscription_service
        subscription_service = get_subscription_service()
    return auth_system, subscription_service


def require_auth_if_available(f):
    """Decorator that requires auth if auth_system is available"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth, _ = _get_services()
        if auth is None:
            request.current_user = {'id': 'anonymous', 'email': 'anonymous@example.com'}
            return f(*args, **kwargs)
        else:
            return auth.require_auth(f)(*args, **kwargs)
    return decorated_function


@subscription_bp.route('/plans', methods=['GET'])
def get_subscription_plans():
    """Get all available subscription plans"""
    try:
        _, sub_service = _get_services()
        plans = sub_service.get_subscription_plans()
        return jsonify({
            'success': True,
            'plans': plans
        }), 200
    except Exception as e:
        print(f"Error getting subscription plans: {e}")
        return jsonify({'error': 'Failed to get subscription plans'}), 500


@subscription_bp.route('/dashboard', methods=['GET'])
@require_auth_if_available
def get_user_dashboard():
    """Get user dashboard data"""
    try:
        user_id = request.current_user['id']
        _, sub_service = _get_services()
        dashboard_data = sub_service.get_user_dashboard_data(user_id)
        
        return jsonify({
            'success': True,
            'data': dashboard_data
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@subscription_bp.route('/subscribe', methods=['POST'])
@require_auth_if_available
def subscribe_to_plan():
    """Subscribe user to a plan"""
    try:
        data = request.get_json()
        if not data or 'plan_name' not in data:
            return jsonify({'error': 'Plan name is required'}), 400
        
        plan_name = data['plan_name']
        stripe_subscription_id = data.get('stripe_subscription_id')
        
        user_id = request.current_user['id']
        _, sub_service = _get_services()
        result = sub_service.subscribe_user(user_id, plan_name, stripe_subscription_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Subscription created successfully',
                'subscription': result['subscription']
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@subscription_bp.route('/cancel', methods=['POST'])
@require_auth_if_available
def cancel_subscription():
    """Cancel user's subscription"""
    try:
        data = request.get_json()
        if not data or 'plan_name' not in data:
            return jsonify({'error': 'Plan name is required'}), 400
        
        plan_name = data['plan_name']
        user_id = request.current_user['id']
        _, sub_service = _get_services()
        result = sub_service.cancel_subscription(user_id, plan_name)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Subscription cancelled successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@subscription_bp.route('/usage', methods=['GET'])
@require_auth_if_available
def get_usage_info():
    """Get user's usage information"""
    try:
        user_id = request.current_user['id']
        _, sub_service = _get_services()
        usage = sub_service.get_user_usage(user_id)
        limits = sub_service.check_usage_limits(user_id)
        
        return jsonify({
            'success': True,
            'usage': usage,
            'limits': limits
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@subscription_bp.route('/check-limits', methods=['GET'])
@require_auth_if_available
def check_usage_limits():
    """Check if user can use the service"""
    try:
        user_id = request.current_user['id']
        _, sub_service = _get_services()
        limits = sub_service.check_usage_limits(user_id)
        
        return jsonify({
            'success': True,
            'limits': limits
        }), 200
    except Exception as e:
        print(f"Error checking usage limits: {e}")
        return jsonify({'error': 'Failed to check limits'}), 500


@subscription_bp.route('/can-chat', methods=['GET'])
@require_auth_if_available
def can_user_chat():
    """Check if user can chat"""
    try:
        user_id = request.current_user['id']
        _, sub_service = _get_services()
        limits = sub_service.check_usage_limits(user_id)
        
        return jsonify({
            'success': True,
            'can_chat': limits.get('can_chat', True),
            'limits': limits
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500




