#!/usr/bin/env python3
"""
Subscription API Routes for Moneta
Handles subscription plans, user subscriptions, and usage tracking.
"""

from flask import Blueprint, request, jsonify
from auth_system import auth_system, get_auth_system
from services.subscription_service import subscription_service

# Create subscription blueprint
subscription_bp = Blueprint('subscription', __name__)

@subscription_bp.route('/api/subscription/plans', methods=['GET'])
def get_subscription_plans():
    """Get all available subscription plans"""
    try:
        plans = subscription_service.get_subscription_plans()
        return jsonify({
            'success': True,
            'plans': plans
        }), 200
    except Exception as e:
        print(f"Error getting subscription plans: {e}")
        return jsonify({'error': 'Failed to get subscription plans'}), 500

@subscription_bp.route('/api/subscription/user-status', methods=['GET'])
@auth_system.require_auth
def get_user_subscription_status():
    """Get current user's subscription status and usage"""
    try:
        user_id = request.current_user['id']
        dashboard_data = subscription_service.get_user_dashboard_data(user_id)
        
        return jsonify({
            'success': True,
            'data': dashboard_data
        }), 200
    except Exception as e:
        print(f"Error getting user subscription status: {e}")
        return jsonify({'error': 'Failed to get subscription status'}), 500

@subscription_bp.route('/api/subscription/subscribe', methods=['POST'])
@auth_system.require_auth
def subscribe_to_plan():
    """Subscribe user to a plan"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        plan_name = data.get('plan_name')
        stripe_subscription_id = data.get('stripe_subscription_id')
        
        if not plan_name:
            return jsonify({'error': 'Plan name is required'}), 400
        
        user_id = request.current_user['id']
        result = subscription_service.subscribe_user(user_id, plan_name, stripe_subscription_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Successfully subscribed to plan',
                'subscription': result['subscription']
            }), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        print(f"Error subscribing to plan: {e}")
        return jsonify({'error': 'Subscription failed'}), 500

@subscription_bp.route('/api/subscription/cancel', methods=['POST'])
@auth_system.require_auth
def cancel_subscription():
    """Cancel user's subscription"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        plan_name = data.get('plan_name')
        
        if not plan_name:
            return jsonify({'error': 'Plan name is required'}), 400
        
        user_id = request.current_user['id']
        result = subscription_service.cancel_subscription(user_id, plan_name)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message']
            }), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        print(f"Error cancelling subscription: {e}")
        return jsonify({'error': 'Cancellation failed'}), 500

@subscription_bp.route('/api/subscription/usage', methods=['GET'])
@auth_system.require_auth
def get_user_usage():
    """Get user's current usage statistics"""
    try:
        user_id = request.current_user['id']
        usage = subscription_service.get_user_usage(user_id)
        limits = subscription_service.check_usage_limits(user_id)
        
        return jsonify({
            'success': True,
            'usage': usage,
            'limits': limits
        }), 200
    except Exception as e:
        print(f"Error getting user usage: {e}")
        return jsonify({'error': 'Failed to get usage data'}), 500

@subscription_bp.route('/api/subscription/check-limits', methods=['GET'])
@auth_system.require_auth
def check_usage_limits():
    """Check if user can use the service"""
    try:
        user_id = request.current_user['id']
        limits = subscription_service.check_usage_limits(user_id)
        
        return jsonify({
            'success': True,
            'limits': limits
        }), 200
    except Exception as e:
        print(f"Error checking usage limits: {e}")
        return jsonify({'error': 'Failed to check limits'}), 500

def register_subscription_routes(app):
    """Register subscription routes with the Flask app"""
    # Ensure auth system is initialized
    global auth_system
    if auth_system is None:
        auth_system, _ = get_auth_system()
    
    app.register_blueprint(subscription_bp) 