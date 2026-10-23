CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL CHECK (length(full_name) BETWEEN 2 AND 100),
    email TEXT NOT NULL COLLATE NOCASE UNIQUE CHECK (length(email) <= 254),
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_name TEXT NOT NULL CHECK (length(student_name) BETWEEN 2 AND 100),
    registration_number TEXT NOT NULL CHECK (length(registration_number) BETWEEN 1 AND 40),
    department TEXT NOT NULL CHECK (length(department) BETWEEN 2 AND 100),
    semester INTEGER NOT NULL CHECK (semester BETWEEN 1 AND 12),
    examination_year INTEGER NOT NULL CHECK (examination_year BETWEEN 1950 AND 2100),
    college_name TEXT NOT NULL CHECK (length(college_name) BETWEEN 2 AND 150),
    reason TEXT NOT NULL CHECK (length(reason) BETWEEN 10 AND 1000),
    status TEXT NOT NULL DEFAULT 'Not Started'
        CHECK (status IN (
            'Not Started',
            'Documents Prepared',
            'Submitted',
            'Follow-up Required'
        )),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS applications_user_id_idx
    ON applications(user_id);
