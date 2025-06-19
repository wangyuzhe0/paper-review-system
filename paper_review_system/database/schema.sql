-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'reviewer', 'author'))
);

-- 论文表
CREATE TABLE IF NOT EXISTS papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    abstract TEXT,
    file_path TEXT,
    author_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'submitted',
    FOREIGN KEY(author_id) REFERENCES users(id)
);

-- 评审分配表
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER NOT NULL,
    reviewer_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'assigned',
    FOREIGN KEY(paper_id) REFERENCES papers(id),
    FOREIGN KEY(reviewer_id) REFERENCES users(id)
);


-- 评审表
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER NOT NULL,
    reviewer_id INTEGER NOT NULL,
    score INTEGER NOT NULL CHECK(score >= 0 AND score <= 100),
    comments TEXT,
    FOREIGN KEY(paper_id) REFERENCES papers(id),
    FOREIGN KEY(reviewer_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_assignments_paper ON assignments(paper_id);
CREATE INDEX IF NOT EXISTS idx_assignments_reviewer ON assignments(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_reviews_paper ON reviews(paper_id);
CREATE INDEX IF NOT EXISTS idx_reviews_reviewer ON reviews(reviewer_id);