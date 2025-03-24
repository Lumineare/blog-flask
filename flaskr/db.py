import sqlite3
from datetime import datetime

import click
from flask import current_app, g

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def update_schema():
    """Update database schema without losing data."""
    db = get_db()
    try:
        # Menambahkan kolom ke tabel post jika belum ada
        try:
            db.execute('SELECT upvotes FROM post LIMIT 1')
        except sqlite3.OperationalError:
            db.execute('ALTER TABLE post ADD COLUMN upvotes INTEGER DEFAULT 0')
        
        try:
            db.execute('SELECT downvotes FROM post LIMIT 1')
        except sqlite3.OperationalError:
            db.execute('ALTER TABLE post ADD COLUMN downvotes INTEGER DEFAULT 0')
        
        # Membuat tabel vote jika belum ada
        db.execute('''
        CREATE TABLE IF NOT EXISTS vote (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            vote_type INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (post_id) REFERENCES post (id),
            UNIQUE(user_id, post_id)
        )
        ''')
        
        # Membuat tabel comment jika belum ada
        db.execute('''
        CREATE TABLE IF NOT EXISTS comment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            author_id INTEGER NOT NULL,
            parent_id INTEGER,
            body TEXT NOT NULL,
            created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            upvotes INTEGER DEFAULT 0,
            downvotes INTEGER DEFAULT 0,
            FOREIGN KEY (post_id) REFERENCES post (id),
            FOREIGN KEY (author_id) REFERENCES user (id),
            FOREIGN KEY (parent_id) REFERENCES comment (id)
        )
        ''')
        
        # Membuat tabel comment_vote jika belum ada
        db.execute('''
        CREATE TABLE IF NOT EXISTS comment_vote (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            comment_id INTEGER NOT NULL,
            vote_type INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (comment_id) REFERENCES comment (id),
            UNIQUE(user_id, comment_id)
        )
        ''')
        
        db.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        db.rollback()
        return False

@click.command('update-schema')
def update_schema_command():
    """Update the database schema without losing data."""
    if update_schema():
        click.echo('Skema database telah diperbarui.')
    else:
        click.echo('Gagal memperbarui skema database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(update_schema_command)

sqlite3.register_adapter(datetime, lambda v: v.isoformat())
sqlite3.register_converter("timestamp", lambda v: datetime.fromisoformat(v.decode()))