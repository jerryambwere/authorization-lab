#!/usr/bin/env python3

from flask import Flask, jsonify, request, session, make_response
from flask_migrate import Migrate
from flask_restful import Api, Resource
from models import db, Article, User

# Initialize app
app = Flask(__name__)
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

# Initialize extensions
migrate = Migrate(app, db)
db.init_app(app)
api = Api(app)

# Helper function
def is_logged_in():
    """Check if a user is logged in by verifying the session user_id."""
    return bool(session.get('user_id'))

# Resources
class ClearSession(Resource):
    def delete(self):
        """Clear the session data."""
        session.clear()
        return {}, 204


class IndexArticle(Resource):
    def get(self):
        """Retrieve all articles."""
        articles = [article.to_dict() for article in Article.query.all()]
        return make_response(jsonify(articles), 200)


class ShowArticle(Resource):
    def get(self, id):
        """Retrieve an article by ID with page view restrictions for unauthenticated users."""
        article = Article.query.filter(Article.id == id).first()
        if not article:
            return {'error': 'Article not found'}, 404

        if not is_logged_in():
            # Implement page view logic for unauthenticated users
            session['page_views'] = session.get('page_views', 0) + 1
            if session['page_views'] > 3:
                return {'message': 'Maximum pageview limit reached'}, 401

        return article.to_dict(), 200


class Login(Resource):
    def post(self):
        """Authenticate a user and start a session."""
        username = request.get_json().get('username')
        user = User.query.filter_by(username=username).first()

        if user:
            session['user_id'] = user.id
            return user.to_dict(), 200

        return {'error': 'Invalid credentials'}, 401


class Logout(Resource):
    def delete(self):
        """Log the user out by clearing the user_id from the session."""
        session['user_id'] = None
        return {}, 204


class CheckSession(Resource):
    def get(self):
        """Check if the user is logged in."""
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                return user.to_dict(), 200

        return {'error': 'Unauthorized'}, 401


class MemberOnlyIndex(Resource):
    def get(self):
        """Retrieve articles marked as members-only."""
        if not is_logged_in():
            return {'error': 'Unauthorized'}, 401

        articles = [article.to_dict() for article in Article.query.filter_by(is_member_only=True).all()]
        return make_response(jsonify(articles), 200)


class MemberOnlyArticle(Resource):
    def get(self, id):
        """Retrieve a specific members-only article by ID."""
        if not is_logged_in():
            return {'error': 'Unauthorized'}, 401

        article = Article.query.filter_by(id=id, is_member_only=True).first()
        if not article:
            return {'error': 'Article not found or not restricted'}, 404

        return article.to_dict(), 200


# API Endpoints
api.add_resource(ClearSession, '/clear', endpoint='clear')
api.add_resource(IndexArticle, '/articles', endpoint='article_list')
api.add_resource(ShowArticle, '/articles/<int:id>', endpoint='show_article')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(MemberOnlyIndex, '/members_only_articles', endpoint='member_index')
api.add_resource(MemberOnlyArticle, '/members_only_articles/<int:id>', endpoint='member_article')

# Main block
if __name__ == '__main__':
    app.run(port=5555, debug=True)
