from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('comments', __name__)

@bp.route('/post/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    db = get_db()
    
    # Check if post exists
    post = db.execute('SELECT * FROM post WHERE id = ?', (post_id,)).fetchone()
    if post is None:
        abort(404, f"Post id {post_id} doesn't exist.")
    
    # Get all comments for this post
    comments = db.execute(
        'SELECT c.id, c.body, c.created, c.author_id, c.parent_id, '
        'c.upvotes, c.downvotes, u.username '
        'FROM comment c JOIN user u ON c.author_id = u.id '
        'WHERE c.post_id = ? ORDER BY c.created ASC',
        (post_id,)
    ).fetchall()
    
    # Get votes for logged-in user
    user_votes = {}
    if g.user:
        user_comment_votes = db.execute(
            'SELECT comment_id, vote_type FROM comment_vote WHERE user_id = ?',
            (g.user['id'],)
        ).fetchall()
        for vote in user_comment_votes:
            user_votes[vote['comment_id']] = vote['vote_type']
    
    # Convert to list of dicts and add user's vote info
    comments_data = []
    for comment in comments:
        comment_dict = dict(comment)
        comment_dict['user_vote'] = user_votes.get(comment['id'])
        comments_data.append(comment_dict)
    
    return jsonify(comments_data)

@bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    body = request.form['body']
    parent_id = request.form.get('parent_id', None)
    
    if not body:
        flash('Comment body is required.')
        return redirect(url_for('blog.index'))
    
    db = get_db()
    
    # Check if post exists
    post = db.execute('SELECT * FROM post WHERE id = ?', (post_id,)).fetchone()
    if post is None:
        abort(404, f"Post id {post_id} doesn't exist.")
    
    # If parent_id is provided, check if it exists
    if parent_id:
        parent_comment = db.execute('SELECT * FROM comment WHERE id = ?', (parent_id,)).fetchone()
        if parent_comment is None:
            abort(404, f"Parent comment id {parent_id} doesn't exist.")
    
    db.execute(
        'INSERT INTO comment (post_id, author_id, parent_id, body)'
        ' VALUES (?, ?, ?, ?)',
        (post_id, g.user['id'], parent_id, body)
    )
    db.commit()
    
    return redirect(url_for('blog.view', id=post_id))

@bp.route('/comment/<int:id>/update', methods=['POST'])
@login_required
def update_comment(id):
    body = request.form['body']
    
    if not body:
        flash('Comment body is required.')
        return redirect(request.referrer)
    
    db = get_db()
    comment = db.execute('SELECT * FROM comment WHERE id = ?', (id,)).fetchone()
    
    if comment is None:
        abort(404, f"Comment id {id} doesn't exist.")
    if comment['author_id'] != g.user['id']:
        abort(403)
    
    db.execute(
        'UPDATE comment SET body = ? WHERE id = ?',
        (body, id)
    )
    db.commit()
    
    # Get the post_id to redirect back to the post
    post_id = comment['post_id']
    return redirect(url_for('blog.view', id=post_id))

@bp.route('/comment/<int:id>/delete', methods=['POST'])
@login_required
def delete_comment(id):
    db = get_db()
    comment = db.execute('SELECT * FROM comment WHERE id = ?', (id,)).fetchone()
    
    if comment is None:
        abort(404, f"Comment id {id} doesn't exist.")
    if comment['author_id'] != g.user['id']:
        abort(403)
    
    # Get the post_id to redirect back to the post
    post_id = comment['post_id']
    
    # Delete the comment
    db.execute('DELETE FROM comment WHERE id = ?', (id,))
    db.commit()
    
    return redirect(url_for('blog.view', id=post_id))