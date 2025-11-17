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
            print("⚠️  SUPABASE_URL and SUPABASE_KEY environment variables are required for subscription service")
            self.supabase = None
        else:
            self.supabase = create_client(self.supabase_url, self.supabase_key)
    
    def _is_available(self) -> bool:
        """Check if subscription service is available (has valid supabase connection)"""
        return self.supabase is not None
    
    def get_subscription_plans(self) -> List[Dict[str, Any]]:
        """Get all available subscription plans"""
        if not self._is_available():
            return []
        try:
            result = self.supabase.table('subscription_plans').select('*').eq('is_active', True).order('price_cents').execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error fetching subscription plans: {e}")
            return []
    
    def get_user_subscription(self, user_id: str) -> Dict[str, Any]:
        """Get user's current subscription information"""
        if not self._is_available():
            return {"plan_name": "free", "status": "active", "usage_limit": 10}
        try:
            # Use the PostgreSQL function to get subscription with fallback to free
            result = self.supabase.rpc('get_user_subscription_with_fallback', {'user_id_param': user_id}).execute()
            
            if result.data and len(result.data) > 0:
                subscription = result.data[0]
                return {
                    "plan_name": subscription.get('plan_name', 'free'),
                    "status": subscription.get('status', 'active'),
                    "usage_limit": subscription.get('usage_limit', 10),
                    "price_cents": subscription.get('price_cents', 0),
                    "features": subscription.get('features', {}),
                    "created_at": subscription.get('created_at'),
                    "updated_at": subscription.get('updated_at')
                }
            else:
                # Return default free plan if no subscription found
                return {
                    "plan_name": "free",
                    "status": "active",
                    "usage_limit": 10,
                    "price_cents": 0,
                    "features": {},
                    "created_at": None,
                    "updated_at": None
                }
        except Exception as e:
            print(f"Error getting user subscription: {e}")
            # Return default free plan on error
            return {
                "plan_name": "free",
                "status": "active", 
                "usage_limit": 10,
                "price_cents": 0,
                "features": {},
                "created_at": None,
                "updated_at": None
            }
    
    def check_usage_limits(self, user_id: str) -> Dict[str, Any]:
        """Check if user has exceeded their usage limits"""
        if not self._is_available():
            return {"can_chat": True, "messages_left": 10, "limit_type": "free"}
        try:
            result = self.supabase.rpc('check_user_usage_limits', {'user_id_param': user_id}).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            else:
                return {"can_chat": True, "messages_left": 10, "limit_type": "free"}
        except Exception as e:
            print(f"Error checking usage limits: {e}")
            return {"can_chat": True, "messages_left": 10, "limit_type": "free"}
    
    def track_usage(self, user_id: str, messages_increment: int = 1, api_calls_increment: int = 1, tokens_increment: int = 0) -> bool:
        """Track user's API usage"""
        if not self._is_available():
            return True
        try:
            result = self.supabase.rpc('track_user_usage', {
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
        """Get user's current usage statistics"""
        if not self._is_available():
            return {"messages_used": 0, "api_calls_used": 0, "tokens_used": 0}
        try:
            result = self.supabase.table('user_usage').select('*').eq('user_id', user_id).execute()
            
            if result.data and len(result.data) > 0:
                usage = result.data[0]
                return {
                    "messages_used": usage.get('messages_used', 0),
                    "api_calls_used": usage.get('api_calls_used', 0),
                    "tokens_used": usage.get('tokens_used', 0),
                    "last_reset": usage.get('last_reset'),
                    "created_at": usage.get('created_at'),
                    "updated_at": usage.get('updated_at')
                }
            else:
                return {
                    "messages_used": 0,
                    "api_calls_used": 0,
                    "tokens_used": 0,
                    "last_reset": None,
                    "created_at": None,
                    "updated_at": None
                }
        except Exception as e:
            print(f"Error getting user usage: {e}")
            return {"messages_used": 0, "api_calls_used": 0, "tokens_used": 0}
    
    def subscribe_user(self, user_id: str, plan_name: str, stripe_subscription_id: Optional[str] = None) -> Dict[str, Any]:
        """Subscribe user to a plan"""
        if not self._is_available():
            return {"success": False, "message": "Subscription service not available"}
        try:
            subscription_data = {
                "user_id": user_id,
                "plan_name": plan_name,
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            if stripe_subscription_id:
                subscription_data["stripe_subscription_id"] = stripe_subscription_id
            
            result = self.supabase.table('user_subscriptions').insert(subscription_data).execute()
            
            if result.data:
                return {
                    "success": True,
                    "message": f"Successfully subscribed to {plan_name}",
                    "subscription": result.data[0]
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to create subscription"
                }
        except Exception as e:
            print(f"Error subscribing user: {e}")
            return {
                "success": False,
                "message": f"Error creating subscription: {str(e)}"
            }
    
    def cancel_subscription(self, user_id: str, plan_name: str) -> Dict[str, Any]:
        """Cancel user's subscription"""
        if not self._is_available():
            return {"success": False, "message": "Subscription service not available"}
        try:
            result = self.supabase.table('user_subscriptions').update({
                "status": "cancelled",
                "updated_at": datetime.now().isoformat()
            }).eq('user_id', user_id).eq('plan_name', plan_name).eq('status', 'active').execute()
            
            if result.data:
                return {
                    "success": True,
                    "message": f"Successfully cancelled {plan_name} subscription",
                    "subscription": result.data[0]
                }
            else:
                return {
                    "success": False,
                    "message": "No active subscription found to cancel"
                }
        except Exception as e:
            print(f"Error cancelling subscription: {e}")
            return {
                "success": False,
                "message": f"Error cancelling subscription: {str(e)}"
            }
    
    def get_ai_model_for_user(self, user_id: str) -> str:
        """Get the AI model that the user should use based on their subscription"""
        if not self._is_available():
            return "gpt-3.5-turbo"
        subscription = self.get_user_subscription(user_id)
        plan_name = subscription.get("plan_name", "free")
        
        if plan_name == "premium":
            return "gpt-4"
        elif plan_name == "pro":
            return "gpt-4"
        else:
            return "gpt-3.5-turbo"
    
    def can_user_chat(self, user_id: str) -> Dict[str, Any]:
        """Check if user can chat (hasn't exceeded limits)"""
        if not self._is_available():
            return {"can_chat": True, "message": "Free tier access"}
        usage_check = self.check_usage_limits(user_id)
        can_chat = usage_check.get("can_chat", True)
        messages_left = usage_check.get("messages_left", 0)
        limit_type = usage_check.get("limit_type", "free")
        
        if can_chat:
            return {
                "can_chat": True,
                "message": f"You have {messages_left} messages remaining",
                "messages_left": messages_left,
                "limit_type": limit_type
            }
        else:
            return {
                "can_chat": False,
                "message": "You've reached your usage limit. Please upgrade your plan.",
                "messages_left": 0,
                "limit_type": limit_type
            }
    
    def get_user_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for user"""
        if not self._is_available():
            return {
                "subscription": {"plan_name": "free", "status": "active"},
                "usage": {"messages_used": 0, "api_calls_used": 0},
                "limits": {"can_chat": True, "messages_left": 10}
            }
        subscription = self.get_user_subscription(user_id)
        usage = self.get_user_usage(user_id)
        limits = self.check_usage_limits(user_id)
        
        return {
            "subscription": subscription,
            "usage": usage,
            "limits": limits
        }

# Create global instance with lazy initialization
subscription_service = None

def get_subscription_service():
    """Get subscription service instance with lazy initialization"""
    global subscription_service
    if subscription_service is None:
        subscription_service = SubscriptionService()
    return subscription_service 