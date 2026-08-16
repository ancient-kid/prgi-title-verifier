-- ==========================================================
-- PRGI Automated Title Verification System - Database Schema
-- Compatible with PostgreSQL 14+ and SQLite 3
-- ==========================================================

-- Table 1: Registered Titles (160,000+ Master Database)
CREATE TABLE IF NOT EXISTS registered_titles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    cleaned_title VARCHAR(500) NOT NULL,
    anchor_words VARCHAR(255),
    registration_no VARCHAR(100) UNIQUE,
    language VARCHAR(100) DEFAULT 'English',
    state VARCHAR(100) DEFAULT 'National',
    periodicity VARCHAR(100) DEFAULT 'Daily',
    publisher VARCHAR(255),
    phonetic_metaphone VARCHAR(255),
    indic_soundex VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_titles_cleaned ON registered_titles(cleaned_title);
CREATE INDEX IF NOT EXISTS idx_titles_anchor ON registered_titles(anchor_words);
CREATE INDEX IF NOT EXISTS idx_titles_regno ON registered_titles(registration_no);
CREATE INDEX IF NOT EXISTS idx_titles_lang ON registered_titles(language);

-- Table 2: Title Applications & Audit Logs
CREATE TABLE IF NOT EXISTS title_applications (
    id SERIAL PRIMARY KEY,
    application_no VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    applicant_id VARCHAR(100) NOT NULL,
    applicant_name VARCHAR(255),
    applicant_email VARCHAR(255),
    language VARCHAR(100),
    state VARCHAR(100),
    periodicity VARCHAR(100),
    verification_probability FLOAT NOT NULL,
    status VARCHAR(50) NOT NULL, -- Approved, Rejected, Review Needed, Pending
    decision_code VARCHAR(100),
    diagnostics_json TEXT,
    execution_time_ms FLOAT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_app_title ON title_applications(title);
CREATE INDEX IF NOT EXISTS idx_app_applicant ON title_applications(applicant_id);
CREATE INDEX IF NOT EXISTS idx_app_status ON title_applications(status);

-- Table 3: PRGI Guidelines & Disallowed Categories
CREATE TABLE IF NOT EXISTS prgi_guidelines (
    id SERIAL PRIMARY KEY,
    guideline_ref VARCHAR(50) NOT NULL,
    category VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    act_reference VARCHAR(255) DEFAULT 'Press and Registration of Periodicals Act, 2023',
    severity VARCHAR(50) DEFAULT 'HARD_REJECT' -- HARD_REJECT, REVIEW, WARNING
);

-- Seed Guideline Rules
INSERT INTO prgi_guidelines (guideline_ref, category, title, description, severity) VALUES
('Guideline 12', 'Disallowed Words', 'Prohibited Law Enforcement and Security Terms', 'Prohibits use of words like Police, Crime, CBI, CID, Army, Vigilance, Sarkar.', 'HARD_REJECT'),
('Guideline 4', 'Emblems Act', 'Emblems and Names (Improper Use) Act 1950', 'Prohibits names of National Emblems, Ashoka Chakra, Bharat Ratna, President, United Nations.', 'HARD_REJECT'),
('Guideline 8', 'Generics', 'Purely Generic Titles with No Anchor Word', 'Rejects titles consisting entirely of generic periodicities and modifiers without distinctiveness.', 'HARD_REJECT'),
('Guideline 6', 'Combination', 'Frankentitle & Combination Titles', 'Rejects titles formed by combining two or more existing registered brand titles.', 'HARD_REJECT'),
('Guideline 5', 'Similarity', 'Phonetic and Deceptive Orthographic Similarity', 'Bars titles phonetically or orthographically deceptively similar to existing registered titles.', 'HARD_REJECT'),
('Guideline 11', 'Cross-Lingual', 'Cross-Lingual Semantic Translation Equivalence', 'Restricts direct linguistic translation copies of existing titles across Indian languages.', 'HARD_REJECT'),
('Guideline 14', 'Defamatory', 'Obscene, Defamatory or Sensational Titles', 'Bars titles containing offensive, criminal, obscene, or communal conflict words.', 'HARD_REJECT')
ON CONFLICT DO NOTHING;
