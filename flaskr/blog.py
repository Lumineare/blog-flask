import os
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username, image_filename, '
        'upvotes, downvotes '
        'FROM post p JOIN user u ON p.author_id = u.id '
        'ORDER BY created DESC'
    ).fetchall()
    
    # Get post votes for current user
    user_votes = {}
    if g.user:
        user_post_votes = db.execute(
            'SELECT post_id, vote_type FROM post_vote WHERE user_id = ?',
            (g.user['id'],)
        ).fetchall()
        for vote in user_post_votes:
            user_votes[vote['post_id']] = vote['vote_type']
    
    return render_template('blog/index.html', posts=posts, user_votes=user_votes)

@bp.route('/<int:id>/view')
def view(id):
    post = get_post(id, check_author=False)
    
    db = get_db()
    
    # Get votes for this post
    user_vote = None
    if g.user:
        user_vote = db.execute(
            'SELECT vote_type FROM post_vote WHERE post_id = ? AND user_id = ?',
            (id, g.user['id'])
        ).fetchone()
        user_vote = user_vote['vote_type'] if user_vote else None
    
    # Get comment count for this post
    comment_count = db.execute(
        'SELECT COUNT(*) FROM comment WHERE post_id = ?',
        (id,)
    ).fetchone()[0]
    
    return render_template('blog/view.html', 
                          post=post, 
                          user_vote=user_vote,
                          comment_count=comment_count)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        # Handle image upload
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Create uploads directory if it doesn't exist
                uploads_dir = os.path.join(current_app.static_folder, 'uploads')
                if not os.path.exists(uploads_dir):
                    os.makedirs(uploads_dir)
                file.save(os.path.join(uploads_dir, filename))
                image_filename = filename

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id, image_filename)'
                ' VALUES (?, ?, ?, ?)',
                (title, body, g.user['id'], image_filename)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username, image_filename, '
        'upvotes, downvotes '
        'FROM post p JOIN user u ON p.author_id = u.id '
        'WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        # Handle image update
        image_filename = post['image_filename']
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                uploads_dir = os.path.join(current_app.static_folder, 'uploads')
                if not os.path.exists(uploads_dir):
                    os.makedirs(uploads_dir)
                file.save(os.path.join(uploads_dir, filename))
                image_filename = filename

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?, image_filename = ?'
                ' WHERE id = ?',
                (title, body, image_filename, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))