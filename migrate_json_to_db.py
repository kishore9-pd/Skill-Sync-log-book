"""
TECHWING Daily Training Logbook
Idempotent Database Migration Script: JSON file -> Relational SQL Database
"""

import os
import json
import shutil
from datetime import datetime
from werkzeug.security import generate_password_hash

from models import db, User, DailyLog, Suggestion, AuditLog

DATA_FILE = os.path.join(os.path.dirname(__file__), 'database.json')
BACKUP_FILE = os.path.join(os.path.dirname(__file__), 'database.json.bak')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'kishore@techwing.com').lower()

def run_migration(app):
    with app.app_context():
        # Ensure database tables exist
        db.create_all()

        if not os.path.exists(DATA_FILE):
            print(f"[MIGRATION] No {DATA_FILE} found. Database initialized empty.")
            return

        # 1. Create backup of database.json if not already backed up
        if not os.path.exists(BACKUP_FILE):
            shutil.copy2(DATA_FILE, BACKUP_FILE)
            print(f"[MIGRATION] Created safety backup: {BACKUP_FILE}")
        else:
            print(f"[MIGRATION] Backup file already exists at: {BACKUP_FILE}")

        # 2. Read existing JSON data
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        except Exception as e:
            print(f"[MIGRATION ERROR] Failed to read {DATA_FILE}: {e}")
            return

        users_data = json_data.get('users', [])
        logs_data = json_data.get('logs', [])
        suggestions_data = json_data.get('suggestions', [])

        migrated_users_count = 0
        migrated_logs_count = 0
        migrated_suggestions_count = 0

        # 3. Migrate Users
        user_email_map = {} # Maps user_email.lower() -> User instance
        for u in users_data:
            email = u.get('email', '').strip().lower()
            name = u.get('name', 'Student').strip()
            combo = u.get('combo', 'genai-aws').strip()
            raw_password = u.get('password', 'password123')

            if not email:
                continue

            existing_user = User.query.filter_by(email=email).first()
            if not existing_user:
                role = 'ADMIN' if email == ADMIN_EMAIL else 'USER'
                password_hash = generate_password_hash(raw_password)
                new_user = User(
                    name=name,
                    email=email,
                    combo=combo,
                    password_hash=password_hash,
                    role=role,
                    is_active=True
                )
                db.session.add(new_user)
                db.session.flush() # Populate new_user.id
                user_email_map[email] = new_user
                migrated_users_count += 1
            else:
                user_email_map[email] = existing_user

        db.session.commit()

        # Ensure admin fallback user exists if not present in JSON
        if ADMIN_EMAIL not in user_email_map:
            existing_admin = User.query.filter_by(email=ADMIN_EMAIL).first()
            if not existing_admin:
                admin_user = User(
                    name="Kishore Kumar (Admin)",
                    email=ADMIN_EMAIL,
                    combo="genai-aws",
                    password_hash=generate_password_hash("password123"),
                    role="ADMIN",
                    is_active=True
                )
                db.session.add(admin_user)
                db.session.flush()
                user_email_map[ADMIN_EMAIL] = admin_user
                db.session.commit()
            else:
                user_email_map[ADMIN_EMAIL] = existing_admin

        # Default fallback user for orphaned logs
        fallback_user = user_email_map.get(ADMIN_EMAIL) or User.query.first()

        # 4. Migrate Daily Logs
        for l in logs_data:
            log_id = l.get('id')
            if not log_id:
                continue

            user_email = l.get('user_email', '').strip().lower()
            owner_user = user_email_map.get(user_email) or User.query.filter_by(email=user_email).first() or fallback_user

            existing_log = DailyLog.query.filter_by(id=log_id).first()
            if not existing_log:
                new_log = DailyLog(
                    id=log_id,
                    user_id=owner_user.id,
                    user_email=user_email or owner_user.email,
                    combo=l.get('combo', owner_user.combo),
                    log_date=l.get('date', datetime.now().strftime('%Y-%m-%d')),
                    day=l.get('day', ''),
                    lab=l.get('lab', ''),
                    check_in=l.get('checkIn', ''),
                    check_out=l.get('checkOut', ''),
                    trainer=l.get('trainer', ''),
                    topics=l.get('topics', ''),
                    practical=l.get('practical', ''),
                    assignment=l.get('assignment', ''),
                    doubts=l.get('doubts', '')
                )
                db.session.add(new_log)
                migrated_logs_count += 1

        db.session.commit()

        # 5. Migrate Suggestions
        for s in suggestions_data:
            sug_id = s.get('id')
            if not sug_id:
                continue

            sug_email = s.get('email', '').strip().lower()
            owner_user = user_email_map.get(sug_email) or User.query.filter_by(email=sug_email).first()

            existing_sug = Suggestion.query.filter_by(id=sug_id).first()
            if not existing_sug:
                new_sug = Suggestion(
                    id=sug_id,
                    user_id=owner_user.id if owner_user else None,
                    date=s.get('date', datetime.now().strftime('%Y-%m-%d %H:%M')),
                    name=s.get('name', 'Anonymous Student'),
                    email=s.get('email', 'student@techwing.com'),
                    category=s.get('category', 'General Suggestion'),
                    subject=s.get('subject', 'No Subject'),
                    message=s.get('message', ''),
                    target_whatsapp=s.get('target_whatsapp', '918074404321'),
                    status=s.get('status', 'Received')
                )
                db.session.add(new_sug)
                migrated_suggestions_count += 1

        db.session.commit()

        # Record initial audit event
        audit_entry = AuditLog(
            user_id=fallback_user.id if fallback_user else None,
            user_email='system',
            action='DATABASE_MIGRATION_COMPLETE',
            target_type='SYSTEM',
            metadata_json=json.dumps({
                'migrated_users': migrated_users_count,
                'migrated_logs': migrated_logs_count,
                'migrated_suggestions': migrated_suggestions_count
            })
        )
        db.session.add(audit_entry)
        db.session.commit()

        print("==========================================================")
        print("DATABASE MIGRATION COMPLETED SUCCESSFULLY")
        print(f" Users Migrated:       {migrated_users_count}")
        print(f" Daily Logs Migrated:  {migrated_logs_count}")
        print(f" Suggestions Migrated: {migrated_suggestions_count}")
        print(f" Backup JSON Saved:    {BACKUP_FILE}")
        print("==========================================================")

if __name__ == '__main__':
    from flask import Flask
    from dotenv import load_dotenv
    load_dotenv()

    app = Flask(__name__)
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(app.instance_path, 'techwing_daily_log.db'))
    if db_url.startswith('sqlite:///'):
        db_path = db_url.replace('sqlite:///', '')
        if not os.path.isabs(db_path):
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    run_migration(app)
