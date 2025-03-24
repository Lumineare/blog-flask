from flask import (
    Blueprint, render_template, request, g
)
from flaskr.db import get_db

bp = Blueprint('search', __name__)

@bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'posts')
    
    db = get_db()
    results = []
    
    if query:
        if search_type == 'posts':
            # Search posts by title and body
            results = db.execute(
                'SELECT p.id, title, body, created, author_id, username, image_filename, '
                'upvotes, downvotes '
                'FROM post p JOIN user u ON p.author_id = u.id '
                'WHERE title LIKE ? OR body LIKE ? '
                'ORDER BY created DESC',
                (f'%{query}%', f'%{query}%')
            ).fetchall()
            
            # Get post votes for current user
            if g.user:
                user_votes = {}
                user_post_votes = db.execute(
                    'SELECT post_id, vote_type FROM post_vote WHERE user_id = ?',
                    (g.user['id'],)
                ).fetchall()
                for vote in user_post_votes:
                    user_votes[vote['post_id']] = vote['vote_type']
                
                # Add user's vote info to results
                for i, post in enumerate(results):
                    post_dict = dict(post)
                    post_dict['user_vote'] = user_votes.get(post['id'])
                    results[i] = post_dict
                
        elif search_type == 'users':
            # Search users by username
            results = db.execute(
                'SELECT id, username FROM user WHERE username LIKE ? ORDER BY username',
                (f'%{query}%',)
            ).fetchall()
    
    return render_template('search/results.html', 
                          query=query, 
                          results=results, 
                          search_type=search_type)