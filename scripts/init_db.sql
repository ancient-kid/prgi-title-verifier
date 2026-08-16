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

-- Seed Guideline Rules (All 18 Statutory Guidelines w.e.f. 01.07.2025)
INSERT INTO prgi_guidelines (guideline_ref, category, title, description, severity) VALUES
('Guideline 1', 'Distinctiveness & Root Words', 'Generic or Root Word Titles Prohibited', 'Proposed titles should contain more than one word formed by combining distinct terms. Generic or root words (Manthan, Darpan, Inspire, Success, Khulasa, Rahasya, Katha, Herald, Malar, Mukhi, Nukkad) shall not be registered.', 'HARD_REJECT'),
('Guideline 2', 'Phonetic & Visual Uniqueness', 'Phonetic and Visual Deceptive Similarity', 'Proposed titles must be unique and shall not be phonetically or visually similar to any existing registered title in same language across India or any language in same State.', 'HARD_REJECT'),
('Guideline 3', 'Public Decency & Morality', 'Negative Connotations, Obscene & Crime Terms', 'Titles with negative connotations with religious sentiments, obscene, absurd or offensive to public sentiments or words like crime, corruption etc. will not be registered.', 'HARD_REJECT'),
('Guideline 4', 'Acronyms & Numerals', 'Abbreviations, Acronyms and Numerals Requirement', 'Abbreviations, acronyms or numerals will be considered only if meaningfully and appropriately attached with other words.', 'HARD_REJECT'),
('Guideline 5', 'Combination Titles', 'Combination or Rearrangement of Registered Titles', 'Titles combining existing registered titles in full, in part or by rearranging words or inserting non-distinctive terms will not be registered.', 'HARD_REJECT'),
('Guideline 6', 'Personal Names', 'Individual Names of Owner or Publisher Prohibited', 'Titles denoting the name of an individual should not be the names of the owner or publisher of the proposed periodical.', 'HARD_REJECT'),
('Guideline 7', 'Special Characters', 'Signs, Symbols, Emojis and Non-Text Characters', 'Titles containing non-text characters, mathematical signs (+, *), pictographs, photos, hallmarks, logos, emojis etc. will not be registered.', 'HARD_REJECT'),
('Guideline 8', 'Generic Modifiers', 'Insignificant Prefixes, Suffixes & Generic Modifiers', 'Titles formed by insignificantly prefixing or suffixing generic or repetitive terms (cities/states, periodicities, articles A/An/The, adjectives) will not be approved.', 'HARD_REJECT'),
('Guideline 9', 'Legal & Judicial', 'Judicial Pronouncements, Copyright, Trademark & Defamation', 'Proposed title shall not be registered if found in violation of any judicial pronouncement including copyright, trademark, contempt of court and defamation.', 'HARD_REJECT'),
('Guideline 10', 'National Security', 'Sovereignty, Integrity of India & Public Order', 'Titles containing words affecting sovereignty and integrity of India, security of the State, international relations, public order or inciting unrest will not be registered.', 'HARD_REJECT'),
('Guideline 11', 'Emblems Act Compliance', 'National Symbols, Emblems & Emblems Act 1950', 'Titles similar to national symbols, mottos, suggesting misleading government association or violative of Emblems and Names Act 1950 will not be registered.', 'HARD_REJECT'),
('Guideline 12', 'Official Authority Blacklist', 'Government Organs, Regulatory Agencies & Public Schemes', 'Titles containing names of Government Organs/Depts, Regulatory/Enforcement Agencies (Police, CBI, CID, Army, Vigilance, Sarkar, Parliament, public schemes) will not be registered.', 'HARD_REJECT'),
('Guideline 13', 'Foreign Association', 'Misleading Foreign Country or City Association', 'Titles suggesting association with a foreign country, city, or place not corresponding to state/place of publication shall not be registered.', 'HARD_REJECT'),
('Guideline 14', 'National Dignitaries', 'Names of Prominent National Leaders & Heads of Govt', 'Titles with names of national leaders, Heads of Government, and functionaries of Central/State governments will not be registered.', 'HARD_REJECT'),
('Guideline 15', 'Broadcast Media', 'Satellite TV Channels, FM Radio & Broadcast Names (MIB)', 'Titles registered as Satellite TV/FM Radio/Community Radio with MIB shall not be registered unless applied by authorized owner/representative.', 'HARD_REJECT'),
('Guideline 16', 'Well-Known Periodicals', 'Protection of Well-Known Periodicals', 'Titles resembling well-known periodicals applied by non-owners shall not be registered to prevent false/misleading association.', 'HARD_REJECT'),
('Guideline 17', 'Commercial & Non-Periodical', 'Advertisements, Classifieds, Tenders & Directories', 'Titles using words like Ad, Advertisement, Classifieds, Tender, Calendar, Panchang, Matrimonial, Yellow pages, directory etc. shall not be registered.', 'HARD_REJECT'),
('Guideline 18', 'Ownership & Editions', 'Transfer of Ownership & New Edition Restrictions', 'Registration of new editions and transfer of ownership of titles falling under categories 3 and 9 to 13 will not be considered.', 'HARD_REJECT')
ON CONFLICT DO NOTHING;
