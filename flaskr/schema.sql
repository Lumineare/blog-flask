-- Tambahkan kolom upvotes dan downvotes ke tabel post jika belum ada
ALTER TABLE post ADD COLUMN upvotes INTEGER DEFAULT 0;
ALTER TABLE post ADD COLUMN downvotes INTEGER DEFAULT 0;

-- Buat tabel baru untuk menyimpan vote
CREATE TABLE IF NOT EXISTS vote (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  post_id INTEGER NOT NULL,
  vote_type INTEGER NOT NULL, -- 1 untuk upvote, -1 untuk downvote
  FOREIGN KEY (user_id) REFERENCES user (id),
  FOREIGN KEY (post_id) REFERENCES post (id),
  UNIQUE(user_id, post_id)
);

-- Buat tabel untuk komentar
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
);

-- Buat tabel untuk reaksi komentar
CREATE TABLE IF NOT EXISTS comment_vote (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  comment_id INTEGER NOT NULL,
  vote_type INTEGER NOT NULL, -- 1 untuk upvote, -1 untuk downvote
  FOREIGN KEY (user_id) REFERENCES user (id),
  FOREIGN KEY (comment_id) REFERENCES comment (id),
  UNIQUE(user_id, comment_id)
);