#!/usr/bin/env python3
"""
Subscription Service for Moneta
Handles subscription management, usage tracking, and tier validation.
"""

import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from supabase import create_client, Client

# Load environment variables
load_dotenv()

class SubscriptionService:
    """Service for managing user subscriptions and usage tracking"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    def get_subscription_plans(self) -> List[Dict[str, Any]]:
        """Get all available subscription plans"""
        try:
            result = self.supabase.table('subscription_plans').select('*').eq('is_active', True).order('price_cents').execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error fetching subscription plans: {e}")
            return []
    
    def get_user_subscription(self, user_id: str) -> Dict[str, Any]:
        """Get user's current subscription information"""
        try:
            # Use the PostgreSQL function to get subscription with fallback to free
            result = self.supabase.rpc('get_user_subscription', {'user_id_param': user_id}).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            else:
                # Fallback to free plan if function fails
                return {
                    'plan_name': 'free',
                    'price_cents': 0,
                    'monthly_message_limit': 50,
                    'features': {"memory_limit": 100, "features": ["basic_chat", "memory_storage"]},
                    'ai_model': 'gpt-4o-mini',
                    'status': 'free',
                    'expires_at': None
                }
        except Exception as e:
            print(f"Error fetching user subscription: {e}")
            # Return free plan as fallback
            return {
                'plan_name': 'free',
                'price_cents': 0,
                'monthly_message_limit': 50,
                'features': {"memory_limit": 100, "features": ["basic_chat", "memory_storage"]},
                'ai_model': 'gpt-4o-mini',
                'status': 'free',
                'expires_at': None
            }
    
    def check_usage_limits(self, user_id: str) -> Dict[str, Any]:
        """Check if user has exceeded their usage limits"""
        try:
            result = self.supabase.rpc('check_user_limits', {'user_id_param': user_id}).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            else:
                # Fallback response
                return {
                    'can_use_service': True,
                    'messages_used': 0,
                    'messages_limit': 50,
                    'plan_name': 'free'
                }
        except Exception as e:
            print(f"Error checking usage limits: {e}")
            return {
                'can_use_service': True,
                'messages_used': 0,
                'messages_limit': 50,
                'plan_name': 'free'
            }
    
    def track_usage(self, user_id: str, messages_increment: int = 1, api_calls_increment: int = 1, tokens_increment: int = 0) -> bool:
        """Track user usage"""
        try:
            self.supabase.rpc('track_user_usage', {
                'user_id_param': user_id,
                'messages_increment': messages_increment,
                'api_calls_increment': api_calls_increment,
                'tokens_increment': tokens_increment
            }).execute()
            return True
        except Exception as e:
            print(f"Error tracking usage: {e}")
            return False
    
    def get_user_usage(self, user_id: str) -> Dict[str, Any]:
        """Get user's current month usage"""
        try:
            current_month = datetime.now().strftime('%Y-%m')
            result = self.supabase.table('user_usage').select('*').eq('user_id', user_id).eq('month_year', current_month).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            else:
                return {
                    'messages_used': 0,
                    'api_calls_used': 0,
                    'tokens_used': 0
                }
        except Exception as e:
            print(f"Error fetching user usage: {e}")
            return {
                'messages_used': 0,
                'api_calls_used': 0,
                'tokens_used': 0
            }
    
    def subscribe_user(self, user_id: str, plan_name: str, stripe_subscription_id: Optional[str] = None) -> Dict[str, Any]:
        """Subscribe user to a plan"""
        try:
            # Get the plan
            plan_result = self.supabase.table('subscription_plans').select('*').eq('name', plan_name).execute()
            
            if not plan_result.data:
                return {
                    'success': False,
                    'error': 'Invalid subscription plan'
                }
            
            plan = plan_result.data[0]
            
            # Check if user already has this subscription
            existing_sub = self.supabase.table('user_subscriptions').select('*').eq('user_id', user_id).eq('plan_id', plan['id']).eq('status', 'active').execute()
            
            if existing_sub.data:
                return {
                    'success': False,
                    'error': 'User already has this subscription'
                }
            
            # Create subscription
            subscription_data = {
                'user_id': user_id,
                'plan_id': plan['id'],
                'status': 'active',
                'started_at': datetime.utcnow().isoformat(),
                'expires_at': None if plan_name == 'premium' else (datetime.utcnow() + timedelta(days=30)).isoformat(),
                'stripe_subscription_id': stripe_subscription_id
            }
            
            result = self.supabase.table('user_subscriptions').insert(subscription_data).execute()
            
            if result.data:
                return {
                    'success': True,
                    'subscription': result.data[0]
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create subscription'
                }
            
        except Exception as e:
            print(f"Error subscribing user: {e}")
            return {
                'success': False,
                'error': 'Subscription failed'
            }
    
    def cancel_subscription(self, user_id: str, plan_name: str) -> Dict[str, Any]:
        """Cancel user's subscription"""
        try:
            # Get the plan
            plan_result = self.supabase.table('subscription_plans').select('*').eq('name', plan_name).execute()
            
            if not plan_result.data:
                return {
                    'success': False,
                    'error': 'Invalid subscription plan'
                }
            
            plan = plan_result.data[0]
            
            # Update subscription status
            result = self.supabase.table('user_subscriptions').update({
                'status': 'cancelled',
                'updated_at': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).eq('plan_id', plan['id']).execute()
            
            if result.data:
                return {
                    'success': True,
                    'message': 'Subscription cancelled successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to cancel subscription'
                }
            
        except Exception as e:
            print(f"Error cancelling subscription: {e}")
            return {
                'success': False,
                'error': 'Cancellation failed'
            }
    
    def get_ai_model_for_user(self, user_id: str) -> str:
        """Get the AI model that should be used for this user based on their subscription"""
        subscription = self.get_user_subscription(user_id)
        return subscription.get('ai_model', 'gpt-4o-mini')
    
    def can_user_chat(self, user_id: str) -> Dict[str, Any]:
        """Check if user can send a chat message"""
        limits = self.check_usage_limits(user_id)
        
        if not limits['can_use_service']:
            return {
                'can_chat': False,
                'reason': 'Monthly message limit exceeded',
                'messages_used': limits['messages_used'],
                'messages_limit': limits['messages_limit'],
                'plan_name': limits['plan_name']
            }
        
        return {
            'can_chat': True,
            'messages_used': limits['messages_used'],
            'messages_limit': limits['messages_limit'],
            'plan_name': limits['plan_name']
        }
    
    def get_user_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user subscription and usage data for dashboard"""
        try:
            subscription = self.get_user_subscription(user_id)
            usage = self.get_user_usage(user_id)
            limits = self.check_usage_limits(user_id)
            
            return {
                'subscription': subscription,
                'usage': usage,
                'limits': limits,
                'can_chat': limits['can_use_service']
            }
        except Exception as e:
            print(f"Error getting dashboard data: {e}")
            return {
                'subscription': {'plan_name': 'free', 'ai_model': 'gpt-4o-mini'},
                'usage': {'messages_used': 0, 'api_calls_used': 0, 'tokens_used': 0},
                'limits': {'can_use_service': True, 'messages_used': 0, 'messages_limit': 50, 'plan_name': 'free'},
                'can_chat': True
            }

# Create global instance
subscription_service = SubscriptionService() 