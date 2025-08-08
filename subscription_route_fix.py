
# Add this to app.py to fix subscription route
@app.route('/subscription-plans-safe')
def subscription_plans_safe():
    """Safe subscription plans route with error handling"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            # Redirect to login for non-authenticated users
            return redirect(url_for('login_form', next=request.url))
        
        # Get plans safely
        plans = subscription_manager.get_all_plans()
        
        # Get current subscription safely
        try:
            current_subscription = subscription_manager.get_user_subscription(user_id)
        except:
            current_subscription = None
        
        # Get daily usage safely
        try:
            daily_usage = subscription_manager.get_daily_usage(user_id)
        except:
            daily_usage = {'calls': 0, 'limit': 100}
        
        return render_template('subscription_plans.html', 
                             plans=plans or [], 
                             current_subscription=current_subscription,
                             daily_usage=daily_usage)
                             
    except Exception as e:
        flash('Unable to load subscription plans. Please try again later.', 'error')
        return redirect(url_for('dashboard'))
