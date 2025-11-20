import psycopg2
from psycopg2 import sql
from config import DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT

def get_conn():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
    )

def init_db():
    schema = """
    CREATE TABLE IF NOT EXISTS University (
        university_id SERIAL PRIMARY KEY,
        name VARCHAR(150) NOT NULL,
        country VARCHAR(100) NOT NULL,
        ranking INT,
        contact_email VARCHAR(120) UNIQUE
    );

    CREATE TABLE IF NOT EXISTS Student (
        student_id SERIAL PRIMARY KEY,
        name VARCHAR(120) NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        password VARCHAR(225) NOT NULL,
        dob DATE,
        department VARCHAR(100),
        cgpa NUMERIC(3,2),
        university_id INT,
        FOREIGN KEY (university_id)
            REFERENCES University(university_id)
            ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS Mentor (
        mentor_id SERIAL PRIMARY KEY,
        name VARCHAR(120) NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        password VARCHAR(225) NOT NULL,
        department VARCHAR(100),
        university_id INT,
        FOREIGN KEY (university_id)
            REFERENCES University(university_id)
            ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS Program (
        program_id SERIAL PRIMARY KEY,
        title VARCHAR(200) NOT NULL,
        description TEXT,
        program_type VARCHAR(50),
        duration INT,
        eligibility TEXT,
        start_date DATE,
        end_date DATE,
        university_id INT,
        mentor_id INT,
        FOREIGN KEY (university_id)
            REFERENCES University(university_id)
            ON DELETE CASCADE,
        FOREIGN KEY (mentor_id)
            REFERENCES Mentor(mentor_id)
            ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS Application (
        application_id SERIAL PRIMARY KEY,
        student_id INT NOT NULL,
        program_id INT NOT NULL,
        status VARCHAR(30) DEFAULT 'Pending',
        applied_date TIMESTAMP DEFAULT NOW(),
        scholarship_awarded BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (student_id)
            REFERENCES Student(student_id)
            ON DELETE CASCADE,
        FOREIGN KEY (program_id)
            REFERENCES Program(program_id)
            ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS Scholarship (
        scholarship_id SERIAL PRIMARY KEY,
        program_id INT NOT NULL,
        name VARCHAR(150) NOT NULL,
        amount NUMERIC(10,2),
        eligibility_criteria TEXT,
        FOREIGN KEY (program_id)
            REFERENCES Program(program_id)
            ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS VisaPermit (
        visa_id SERIAL PRIMARY KEY,
        student_id INT NOT NULL,
        country VARCHAR(100),
        application_status VARCHAR(50) DEFAULT 'Pending',
        issued_date DATE,
        expiry_date DATE,
        FOREIGN KEY (student_id)
            REFERENCES Student(student_id)
            ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS Housing (
        housing_id SERIAL PRIMARY KEY,
        university_id INT NOT NULL,
        location VARCHAR(150),
        room_type VARCHAR(50),
        rent NUMERIC(10,2),
        availability BOOLEAN DEFAULT TRUE,
        FOREIGN KEY (university_id)
            REFERENCES University(university_id)
            ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS HousingAssignment (
        assign_id SERIAL PRIMARY KEY,
        student_id INT NOT NULL,
        housing_id INT NOT NULL,
        allotment_date DATE DEFAULT CURRENT_DATE,
        checkout_date DATE,
        FOREIGN KEY (student_id)
            REFERENCES Student(student_id)
            ON DELETE CASCADE,
        FOREIGN KEY (housing_id)
            REFERENCES Housing(housing_id)
            ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS HousingRequest (
        request_id SERIAL PRIMARY KEY,
        student_id INT NOT NULL,
        request_type VARCHAR(20) NOT NULL, -- 'apply' OR 'vacate'
        status VARCHAR(20) DEFAULT 'Pending',
        request_date TIMESTAMP DEFAULT NOW(),
        FOREIGN KEY (student_id)
            REFERENCES Student(student_id)
            ON DELETE CASCADE
    );


    CREATE TABLE IF NOT EXISTS Admin (
        admin_id SERIAL PRIMARY KEY,
        name VARCHAR(80) NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        password VARCHAR(225) NOT NULL
    );

    -- Scholarship Applications (per program)
    CREATE TABLE IF NOT EXISTS ScholarshipApplication (
        sch_app_id SERIAL PRIMARY KEY,
        application_id INT NOT NULL,
        scholarship_id INT NOT NULL,
        status VARCHAR(30) DEFAULT 'Pending',
        UNIQUE (application_id, scholarship_id),
        FOREIGN KEY (application_id)
            REFERENCES Application(application_id)
            ON DELETE CASCADE,
        FOREIGN KEY (scholarship_id)
            REFERENCES Scholarship(scholarship_id)
            ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS RequiredDocuments (
        req_id SERIAL PRIMARY KEY,
        program_id INT NOT NULL,
        document_name VARCHAR(255) NOT NULL,
        FOREIGN KEY (program_id)
            REFERENCES Program(program_id)
            ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS ApplicationDocument (
        app_doc_id SERIAL PRIMARY KEY,
        application_id INT NOT NULL,
        req_id INT NOT NULL,
        file_name VARCHAR(255),
        status VARCHAR(20) DEFAULT 'Pending',

        CONSTRAINT unique_app_req UNIQUE (application_id, req_id),

        FOREIGN KEY (application_id)
            REFERENCES Application(application_id)
            ON DELETE CASCADE,

        FOREIGN KEY (req_id)
            REFERENCES RequiredDocuments(req_id)
            ON DELETE CASCADE
    );

    -- Seed data
    INSERT INTO University (name, country, ranking, contact_email)
    VALUES ('Amrita Vishwa Vidyapeetham', 'India', 5, 'info@amrita.edu')
    ON CONFLICT DO NOTHING;

    INSERT INTO Admin (name, email, password)
    VALUES (
        'System Admin',
        'admin@portal.com',
        'scrypt:32768:8:1$1kmyWq0yU0CHjzv0$d5750057ce306b78563c9374b181b4326e63c9cbb5eec657b7491ceda9dc79fbb1c848e9d48984d3cecf8c12d43e5463c5bd5d0ad8c886029fcf0b67b8ced1b0'
    )
    ON CONFLICT DO NOTHING;

    INSERT INTO Mentor (name, email, password, department, university_id)
    VALUES (
        'Dr. Arvind Reddy',
        'arvindr@university.com',
        'scrypt:32768:8:1$ZJ7qb1Iyz8SU9uds$76f8db6c58ce7ba801ea260de6894d026daa59b8582311aeb9dcc5fc12d52a1c020980e21ea8c903d82b61bac6b0d0c06dce41a226e3ee7f83a209c100d38aff',
        'Computer Science',
        1
    )
    ON CONFLICT DO NOTHING;
    """

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(schema)
    conn.commit()
    cur.close()
    conn.close()
    print("Database schema initialized successfully.")

