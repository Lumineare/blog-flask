from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('votes', __name__)

@bp.route('/post/<int:post_id>/vote', methods=['POST'])
@login_required
def vote_post(post_id):
    vote_type = request.json.get('vote_type')  # 1 for upvote, -1 for downvote, 0 for remove vote
    
    if vote_type not in [1, -1, 0]:
        return jsonify({'error': 'Invalid vote type'}), 400
    
    db = get_db()
    
    # Check if post exists
    post = db.execute('SELECT * FROM post WHERE id = ?', (post_id,)).fetchone()
    if post is None:
        return jsonify({'error': 'Post not found'}), 404
    
    # Check if user has already voted
    existing_vote = db.execute(
        'SELECT * FROM post_vote WHERE post_id = ? AND user_id = ?',
        (post_id, g.user['id'])
    ).fetchone()
    
    if existing_vote:
        if vote_type == 0:
            # Remove vote
            db.execute(
                'DELETE FROM post_vote WHERE id = ?',
                (existing_vote['id'],)
            )
            
            # Update post vote counts
            if existing_vote['vote_type'] == 1:
                db.execute('UPDATE post SET upvotes = upvotes - 1 WHERE id = ?', (post_id,))
            else:
                db.execute('UPDATE post SET downvotes = downvotes - 1 WHERE id = ?', (post_id,))
                
        elif vote_type != existing_vote['vote_type']:
            # Change vote
            db.execute(
                'UPDATE post_vote SET vote_type = ? WHERE id = ?',
                (vote_type, existing_vote['id'])
            )
            
            # Update post vote counts
            if vote_type == 1:
                db.execute('UPDATE post SET upvotes = upvotes + 1, downvotes = downvotes - 1 WHERE id = ?', (post_id,))
            else:
                db.execute('UPDATE post SET upvotes = upvotes - 1, downvotes = downvotes + 1 WHERE id = ?', (post_id,))
    else:
        if vote_type != 0:
            # Add new vote
            db.execute(
                'INSERT INTO post_vote (post_id, user_id, vote_type) VALUES (?, ?, ?)',
                (post_id, g.user['id'], vote_type)
            )
            
            # Update post vote counts
            if vote_type == 1:
                db.execute('UPDATE post SET upvotes = upvotes + 1 WHERE id = ?', (post_id,))
            else:
                db.execute('UPDATE post SET downvotes = downvotes + 1 WHERE id = ?', (post_id,))
    
    db.commit()
    
    # Get updated vote counts
    updated_post = db.execute('SELECT upvotes, downvotes FROM post WHERE id = ?', (post_id,)).fetchone()
    
    return jsonify({
        'upvotes': updated_post['upvotes'],
        'downvotes': updated_post['downvotes'],
        'user_vote': vote_type if vote_type != 0 else None
    })

@bp.route('/comment/<int:comment_id>/vote', methods=['POST'])
@login_required
def vote_comment(comment_id):
    vote_type = request.json.get('vote_type')  # 1 for upvote, -1 for downvote, 0 for remove vote
    
    if vote_type not in [1, -1, 0]:
        return jsonify({'error': 'Invalid vote type'}), 400
    
    db = get_db()
    
    # Check if comment exists
    comment = db.execute('SELECT * FROM comment WHERE id = ?', (comment_id,)).fetchone()
    if comment is None:
        return jsonify({'error': 'Comment not found'}), 404
    
    # Check if user has already voted
    existing_vote = db.execute(
        'SELECT * FROM comment_vote WHERE comment_id = ? AND user_id = ?',
        (comment_id, g.user['id'])
    ).fetchone()
    
    if existing_vote:
        if vote_type == 0:
            # Remove vote
            db.execute(
                'DELETE FROM comment_vote WHERE id = ?',
                (existing_vote['id'],)
            )
            
            # Update comment vote counts
            if existing_vote['vote_type'] == 1:
                db.execute('UPDATE comment SET upvotes = upvotes - 1 WHERE id = ?', (comment_id,))
            else:
                db.execute('UPDATE comment SET downvotes = downvotes - 1 WHERE id = ?', (comment_id,))
                
        elif vote_type != existing_vote['vote_type']:
            # Change vote
            db.execute(
                'UPDATE comment_vote SET vote_type = ? WHERE id = ?',
                (vote_type, existing_vote['id'])
            )
            
            # Update comment vote counts
            if vote_type == 1:
                db.execute('UPDATE comment SET upvotes = upvotes + 1, downvotes = downvotes - 1 WHERE id = ?', (comment_id,))
            else:
                db.execute('UPDATE comment SET upvotes = upvotes - 1, downvotes = downvotes + 1 WHERE id = ?', (comment_id,))
    else:
        if vote_type != 0:
            # Add new vote
            db.execute(
                'INSERT INTO comment_vote (comment_id, user_id, vote_type) VALUES (?, ?, ?)',
                (comment_id, g.user['id'], vote_type)
            )
            
            # Update comment vote counts
            if vote_type == 1:
                db.execute('UPDATE comment SET upvotes = upvotes + 1 WHERE id = ?', (comment_id,))
            else:
                db.execute('UPDATE comment SET downvotes = downvotes + 1 WHERE id = ?', (comment_id,))
    
    db.commit()
    
    # Get updated vote counts
    updated_comment = db.execute('SELECT upvotes, downvotes FROM comment WHERE id = ?', (comment_id,)).fetchone()
    
    return jsonify({
        'upvotes': updated_comment['upvotes'],
        'downvotes': updated_comment['downvotes'],
        'user_vote': vote_type if vote_type != 0 else None
    })