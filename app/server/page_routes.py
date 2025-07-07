"""
Page Routes - Multi-Team Gaming System
=====================================

Flask page routes that serve HTML templates using TemplateBuilder.
This file only handles page routes, not API or SocketIO routes.

Author: Multi-Team Gaming System Development Team
Version: 1.0.0 MVP
"""

from flask import Flask, send_from_directory
from EEGame.app.server.TemplateBuilder import TemplateBuilder
import os


def init_page_routes(app: Flask):
    """
    Initialize all page routes for the Flask application.
    
    Args:
        app: Flask application instance
    """
    # Initialize the template builder
    builder = TemplateBuilder("components")
    
    # Get the path to the assets directory
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_dir = os.path.join(app_dir, 'assets')
    
    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        """Serve static assets (images, etc.)."""
        return send_from_directory(assets_dir, filename)
    
    @app.route('/')
    @app.route('/home')
    def home():
        """Serve the HomePage template."""
        try:
            html = builder.build_template("HomePage")
            return html
        except Exception as e:
            return f"Error loading HomePage: {str(e)}", 500
    
    @app.route('/reaction')
    @app.route('/reaction-game')
    def reaction_game():
        """Serve the ReactionGame template."""
        try:
            html = builder.build_template("ReactionGame")
            return html
        except Exception as e:
            return f"Error loading ReactionGame: {str(e)}", 500
    
    @app.route('/teams')
    @app.route('/team-management')
    def team_management():
        """Serve the TeamManagement template."""
        try:
            html = builder.build_template("TeamManagement")
            return html
        except Exception as e:
            return f"Error loading TeamManagement: {str(e)}", 500
        
    @app.route("/create-team")
    def create_team():
        """Serve the CreateTeam template."""
        try:
            html = builder.build_template("CreateTeams")
            return html
        except Exception as e:
            return f"Error loading CreateTeam: {str(e)}", 500
        
    @app.route('/reaction-timer')
    @app.route('/reaction-timer-game')
    def reaction_timer_game():
        """Serve the ReactionTimer template."""
        try:
            html = builder.build_template("ReactionTimer")
            return html
        except Exception as e:
            return f"Error loading ReactionTimer: {str(e)}", 500
        
    @app.route('/quiz-game')
    @app.route('/quiz')
    def quiz_game():
        """Serve the QuizGame template."""
        try:
            html = builder.build_template("QuizGame")
            return html
        except Exception as e:
            return f"Error loading QuizGame: {str(e)}", 500
    
    print("✓ Page routes initialized successfully")
