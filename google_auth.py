"""
Google OAuth Authentication Blueprint
Handles Google OAuth login flow using oauthlib
"""
import json
import os
import uuid
from urllib.parse import urlencode

import requests
from flask import Blueprint, redirect, request, url_for, flash, session
from flask_login import login_user, current_user
from oauthlib.oauth2 import WebApplicationClient
from werkzeug.security import generate_password_hash

from app import db
from models import User

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Create OAuth client
client = WebApplicationClient(GOOGLE_CLIENT_ID) if GOOGLE_CLIENT_ID else None

google_auth = Blueprint("google_auth", __name__)

def get_google_provider_cfg():
    """Get Google's OAuth configuration"""
    try:
        return requests.get(GOOGLE_DISCOVERY_URL).json()
    except Exception:
        return None

@google_auth.route("/google_login")
def login():
    """Initiate Google OAuth login"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        flash("Google OAuth is not configured", "error")
        return redirect(url_for("auth.login"))
    
    # Check if beta spots are available
    beta_count = User.query.filter(User.beta_user_number.isnot(None)).count()
    if beta_count >= 100:
        flash("Beta testing is full. We'll notify you when the app launches publicly!", "info")
        return redirect(url_for("landing"))
    
    google_provider_cfg = get_google_provider_cfg()
    if not google_provider_cfg:
        flash("Unable to connect to Google. Please try again later.", "error")
        return redirect(url_for("auth.login"))
    
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    
    # Generate redirect URI dynamically
    redirect_uri = url_for("google_auth.callback", _external=True, _scheme="https")
    
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=redirect_uri,
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@google_auth.route("/google_login/callback")
def callback():
    """Handle Google OAuth callback"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        flash("Google OAuth is not configured", "error")
        return redirect(url_for("auth.login"))
    
    code = request.args.get("code")
    if not code:
        flash("Google authentication failed", "error")
        return redirect(url_for("auth.login"))
    
    google_provider_cfg = get_google_provider_cfg()
    if not google_provider_cfg:
        flash("Unable to connect to Google. Please try again later.", "error")
        return redirect(url_for("auth.login"))
    
    token_endpoint = google_provider_cfg["token_endpoint"]
    redirect_uri = url_for("google_auth.callback", _external=True, _scheme="https")
    
    # Prepare token request
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url.replace("http://", "https://"),
        redirect_url=redirect_uri,
        code=code,
    )
    
    # Exchange code for token
    try:
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )
        
        # Parse token response
        client.parse_request_body_response(json.dumps(token_response.json()))
        
        # Get user info
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
        
        if userinfo_response.status_code != 200:
            flash("Failed to get user information from Google", "error")
            return redirect(url_for("auth.login"))
        
        userinfo = userinfo_response.json()
        
        # Verify email
        if not userinfo.get("email_verified"):
            flash("Google email not verified. Please verify your email with Google first.", "error")
            return redirect(url_for("auth.login"))
        
        users_email = userinfo["email"].lower()
        users_name = userinfo.get("given_name", "")
        users_family_name = userinfo.get("family_name", "")
        profile_picture = userinfo.get("picture", "")
        
        # Check if user exists
        user = User.query.filter_by(email=users_email).first()
        
        if not user:
            # Check beta spots
            beta_count = User.query.filter(User.beta_user_number.isnot(None)).count()
            if beta_count >= 100:
                flash("Beta testing is full. We'll notify you when the app launches publicly!", "info")
                return redirect(url_for("landing"))
            
            # Create new user
            user = User(
                id=str(uuid.uuid4()),
                email=users_email,
                first_name=users_name,
                last_name=users_family_name,
                profile_image_url=profile_picture,
                auth_method="google",
                is_verified=True,
                beta_user_number=beta_count + 1
            )
            db.session.add(user)
            db.session.commit()
            
            flash(f"Welcome to the beta! You're user #{user.beta_user_number} of 100.", "success")
        else:
            # Update existing user's Google info if needed
            if user.auth_method != "google":
                user.auth_method = "google"
            user.profile_image_url = profile_picture
            user.is_verified = True
            db.session.commit()
        
        # Log in user
        login_user(user, remember=True)
        
        # Redirect to intended page or dashboard
        next_page = session.pop('next_url', None)
        return redirect(next_page or url_for("dashboard"))
        
    except Exception as e:
        flash("Google authentication failed. Please try again.", "error")
        return redirect(url_for("auth.login"))

def is_google_configured():
    """Check if Google OAuth is properly configured"""
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)