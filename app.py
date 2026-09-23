"""
TECHWING Daily Training Logbook & Conversational AI System
Python Flask Backend & Application Server (SQLAlchemy SQL Database Edition)
Location: D:\\login app
"""

import os
import json
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_migrate import Migrate
from sqlalchemy import inspect, text
from dotenv import load_dotenv
import requests

# Load environment variables from .env
load_dotenv()

from models import db, User, DailyLog, Suggestion, LoginActivity, AuditLog
from migrate_json_to_db import run_migration

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'techwing_secret_key_genai_aws')

# Instance folder setup
os.makedirs(app.instance_path, exist_ok=True)

# Database Configuration
db_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(app.instance_path, 'techwing_daily_log.db'))
# Some hosted PostgreSQL services still provide the older postgres:// prefix.
if db_url.startswith('postgres://'):
    db_url = 'postgresql://' + db_url[len('postgres://'):]

# Handle sqlite path normalization for windows
if db_url.startswith('sqlite:///'):
    raw_path = db_url.replace('sqlite:///', '')
    if not os.path.isabs(raw_path):
        raw_path = os.path.join(app.instance_path, raw_path)
    db_url = 'sqlite:///' + raw_path.replace('\\', '/')

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 1800
}

if db_url.startswith(('postgresql://', 'postgresql+')):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'].update({
        'pool_size': int(os.environ.get('DB_POOL_SIZE', '20')),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', '40')),
        'pool_timeout': 30
    })
elif db_url.startswith('sqlite:///'):
    app.config['SQLALCHEMY_ENGINE_OPTIONS']['connect_args'] = {'timeout': 30}

db.init_app(app)
migrate = Migrate(app, db)

ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'kishore@techwing.com').lower()

# Official TechWing SkillSync Tech Combos (7 Combos)
# INFRA: AWS+DevOps, AWS+AI_JFS
# PROD:  AWS+Gen_AI, AWS+Agentic_AI, Gen_AI+Agentic_AI
# DEV:   AI_JFS+DevOps, AI_JFS+AWS_SA
COMBO_CONFIGS = {

    # ─── INFRA TRACK ───────────────────────────────────────────────────────
    'AWS+DEVOPS': {
        'name': 'AWS + DevOps',
        'subtitle': 'AWS + DevOps | INFRA Track — Daily Class Record',
        'defaultTrainer': 'Kishore Kumar',
        'defaultLab': 'Lab 01 - AWS Cloud Operations Lab',
        'topics': '• Topic 1: AWS Core Infrastructure — EC2, VPC, IAM, S3\n• Topic 2: Terraform Infrastructure as Code (IaC) & AWS CloudFormation\n• Topic 3: CI/CD Pipelines with GitHub Actions, CodePipeline & ECS Fargate',
        'practical': '• Step 1: Provisioned multi-AZ VPC with public/private subnets using Terraform\n• Step 2: Configured GitHub Actions workflow for automated ECR push & ECS deploy\n• Step 3: Set up CloudWatch alarms and SNS alerts for production monitoring',
        'assignment': '• Write Terraform modules to deploy a full AWS production environment with auto-scaling & CI/CD.',
        'doubts': '• Clarified Terraform state lock management using S3 & DynamoDB backend.\n• Note: Always run terraform plan before applying any infrastructure changes.'
    },
    'AWS+AI-JFS': {
        'name': 'AWS + AI_JFS',
        'subtitle': 'AWS + AI Java Full Stack | INFRA Track — Daily Class Record',
        'defaultTrainer': 'Kishore Kumar',
        'defaultLab': 'Lab 02 - Enterprise Java & AWS Cloud Hub',
        'topics': '• Topic 1: Spring Boot REST APIs & AWS Integration Patterns\n• Topic 2: AWS RDS, DynamoDB & ElasticCache for Java Applications\n• Topic 3: AWS Lambda, API Gateway & Serverless Java Architecture',
        'practical': '• Step 1: Built Spring Boot microservice connected to AWS RDS PostgreSQL\n• Step 2: Deployed serverless Java function to AWS Lambda with SnapStart enabled\n• Step 3: Configured API Gateway endpoints with IAM Auth & Lambda Proxy integration',
        'assignment': '• Deploy a full Spring Boot + React application on AWS using ECS Fargate with RDS backend.',
        'doubts': '• Discussed cold start mitigation strategies for AWS Lambda Java runtime.\n• Note: Use AWS SDK v2 for asynchronous non-blocking requests in Java.'
    },

    # ─── PROD TRACK ────────────────────────────────────────────────────────
    'AWS+GENAI': {
        'name': 'AWS + Gen_AI',
        'subtitle': 'AWS + Generative AI | PROD Track — Daily Class Record',
        'defaultTrainer': 'Kishore Kumar',
        'defaultLab': 'Lab 03 - GenAI & AWS Bedrock Hub',
        'topics': '• Topic 1: Generative AI Foundations — LLMs, Prompting & Embeddings\n• Topic 2: Amazon Bedrock — Titan, Claude, Llama2 Model Integration\n• Topic 3: RAG Architecture with OpenSearch Serverless & LangChain',
        'practical': '• Step 1: Provisioned Amazon Bedrock Knowledge Base connected to S3 data source\n• Step 2: Ingested PDF documents into OpenSearch Serverless vector index\n• Step 3: Implemented LangChain ConversationalRetrievalChain with memory in Python',
        'assignment': '• Build a production-ready RAG Q&A chatbot using Amazon Bedrock, LangChain & OpenSearch.',
        'doubts': '• Discussed dense vector embeddings vs sparse BM25 keyword indexing trade-offs.\n• Note: Pause OpenSearch Serverless collection when idle to prevent unnecessary costs.'
    },
    'AWS+AGENTIC AI-JFS': {
        'name': 'AWS + Agentic_AI',
        'subtitle': 'AWS + Agentic AI | PROD Track — Daily Class Record',
        'defaultTrainer': 'Kishore Kumar',
        'defaultLab': 'Lab 04 - Agentic AI & AWS Systems Hub',
        'topics': '• Topic 1: Agentic AI Frameworks — LangGraph, CrewAI & AutoGen\n• Topic 2: AWS Bedrock Agents with Tool Use & Function Calling\n• Topic 3: Multi-Agent Orchestration & Supervisor-Subagent Patterns on AWS',
        'practical': '• Step 1: Built custom Python AI agents with AWS Bedrock tool execution access\n• Step 2: Implemented supervisor-subagent graph execution loop using LangGraph\n• Step 3: Deployed multi-agent system to AWS Lambda with event-driven triggers',
        'assignment': '• Build an AWS-hosted multi-agent AI system that autonomously researches, codes, and deploys solutions.',
        'doubts': '• Discussed infinite loop prevention & max iteration token limits in agentic loops.\n• Note: Always set max execution steps and fallback handlers on agent executors.'
    },
    'GENAI +AGENTIC AI': {
        'name': 'Gen_AI + Agentic_AI',
        'subtitle': 'Gen_AI + Agentic_AI | PROD Track — Daily Class Record',
        'defaultTrainer': 'Kishore Kumar',
        'defaultLab': 'Lab 05 - Autonomous AI Agents Hub',
        'topics': '• Topic 1: Generative AI — LLMs, RAG & Prompt Engineering Masterclass\n• Topic 2: Agentic AI Workflows — ReAct, Tool Use & Dynamic Planning\n• Topic 3: Multi-Agent Systems with LangGraph, CrewAI & Memory Management',
        'practical': '• Step 1: Built a RAG pipeline using ChromaDB + LangChain with streaming responses\n• Step 2: Constructed multi-step AI agent with tools for search, code & data analysis\n• Step 3: Implemented LangGraph agent graph with conditional routing & state management',
        'assignment': '• Build a fully autonomous AI research assistant using GenAI + Agentic workflows end-to-end.',
        'doubts': '• Analyzed trade-offs between single-agent vs multi-agent architectures for production.\n• Note: Always define max_iterations and fallback responses in agent executor configs.'
    },

    # ─── DEV TRACK ─────────────────────────────────────────────────────────
    'AI-JFS-devops': {
        'name': 'AI_JFS + DevOps',
        'subtitle': 'AI Java Full Stack + DevOps | DEV Track — Daily Class Record',
        'defaultTrainer': 'Kishore Kumar',
        'defaultLab': 'Lab 06 - Java Full Stack & DevOps Hub',
        'topics': '• Topic 1: Spring Boot Microservices & REST API Design Patterns\n• Topic 2: Docker Containerization & Kubernetes (K8s) Orchestration\n• Topic 3: CI/CD Automation with Jenkins, GitHub Actions & AWS ECS',
        'practical': '• Step 1: Built Spring Boot REST API with Spring Data JPA & PostgreSQL backend\n• Step 2: Created multi-stage Dockerfile and deployed container to K8s cluster\n• Step 3: Configured automated build, test & deploy pipeline using Jenkins + GitHub Actions',
        'assignment': '• Deploy a full-stack containerized Spring Boot + React app to AWS EKS with complete CI/CD pipeline.',
        'doubts': '• Understood Pod Horizontal Pod Autoscaler (HPA) metrics & ingress controller routing.\n• Note: Store all database credentials in Kubernetes Secrets, never in plain environment variables.'
    },
    'AI-JFS+AWS SA': {
        'name': 'AI_JFS + AWS_SA',
        'subtitle': 'AI Java Full Stack + AWS Solutions Architect | DEV Track — Daily Class Record',
        'defaultTrainer': 'Kishore Kumar',
        'defaultLab': 'Lab 07 - Cloud Architecture & Java Engineering Hub',
        'topics': '• Topic 1: AWS Solutions Architect — VPC, IAM, EC2, RDS & High Availability Design\n• Topic 2: Spring Cloud Microservices & AWS API Gateway Integration\n• Topic 3: AWS Auto Scaling, Elastic Load Balancing & Multi-AZ Fault Tolerance',
        'practical': '• Step 1: Designed multi-AZ VPC architecture with public/private subnets & NAT Gateways\n• Step 2: Connected Spring Boot microservices via AWS API Gateway with IAM Authorization\n• Step 3: Implemented Auto Scaling Group tied to Application Load Balancer with health checks',
        'assignment': '• Architect a highly available, fault-tolerant Java web application on AWS with RDS Multi-AZ & ALB.',
        'doubts': '• Reviewed VPC peering vs AWS Transit Gateway latency & cost trade-offs.\n• Note: Always restrict Security Group ingress ports to minimum required ranges only.'
    }
}

# Auto-initialize & Migrate JSON to SQL on Startup
with app.app_context():
    db.create_all()
    if 'pin_number' not in {column['name'] for column in inspect(db.engine).get_columns('users')}:
        with db.engine.begin() as connection:
            connection.execute(text('ALTER TABLE users ADD COLUMN pin_number VARCHAR(255)'))
    daily_log_columns = {column['name'] for column in inspect(db.engine).get_columns('daily_logs')}
    if 'important_notes' not in daily_log_columns:
        with db.engine.begin() as connection:
            connection.execute(text('ALTER TABLE daily_logs ADD COLUMN important_notes TEXT'))
    for existing_user in User.query.filter(User.pin_number.isnot(None)).all():
        if len(existing_user.pin_number.strip()) == 10 and existing_user.pin_number.strip().isalnum():
            existing_user.set_college_pin(existing_user.pin_number.strip())
    db.session.commit()
    run_migration(app)


# Routes & Page URL Redirections
@app.route('/')
@app.route('/register')
@app.route('/login')
@app.route('/dashboard')
@app.route('/editor')
@app.route('/voice-ai')
@app.route('/history')
@app.route('/print-sheet')
@app.route('/suggestions')
@app.route('/tracks/<combo_key>')
def index(combo_key=None):
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify(COMBO_CONFIGS)

@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    name = data.get('name', '').strip()
    combo = data.get('combo', 'AWS+DEVOPS').strip()
    password = data.get('password', 'password123').strip()
    pin = str(data.get('pin', '')).strip()

    if not email or not name or not password or not pin:
        return jsonify({'error': 'Name, Email, Password, and College PIN are required'}), 400

    pin = pin.strip()
    if len(pin) != 10 or not pin.isalnum():
        return jsonify({'error': 'College PIN must contain exactly 10 alphanumeric characters'}), 400

    existing_user = User.query.filter(User.email.ilike(email)).first()
    if existing_user:
        return jsonify({'error': 'Email already registered. Please log in.'}), 400

    role = 'ADMIN' if email == ADMIN_EMAIL else 'USER'
    new_user = User(
        name=name,
        email=email,
        combo=combo,
        role=role,
        is_active=True
    )
    new_user.set_college_pin(pin)
    new_user.set_password(password)

    try:
        db.session.add(new_user)
        db.session.flush()

        audit = AuditLog(
            user_id=new_user.id,
            user_email=email,
            action='REGISTER',
            target_type='USER',
            target_id=str(new_user.id),
            metadata_json=json.dumps({'name': name, 'combo': combo, 'role': role}),
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception('Student registration transaction failed for %s', email)
        return jsonify({'error': 'Registration could not be saved. Please try again.'}), 500

    return jsonify({'message': 'Registration successful', 'user': new_user.to_dict()})

@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({'error': 'Email and Password are required'}), 400

    user = User.query.filter(User.email.ilike(email)).first()

    if not user:
        return jsonify({'error': 'Account not found. Please register your student account first.'}), 400

    if not user.check_password(password):
        return jsonify({'error': 'Incorrect password. Please try again.'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account is deactivated. Please contact administration.'}), 403

    # Update last login & create activity record
    user.last_login_at = datetime.utcnow()

    activity = LoginActivity(
        user_id=user.id,
        login_time=datetime.utcnow(),
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')[:500]
    )
    db.session.add(activity)

    audit = AuditLog(
        user_id=user.id,
        user_email=user.email,
        action='LOGIN',
        target_type='USER',
        target_id=str(user.id),
        ip_address=request.remote_addr
    )
    db.session.add(audit)

    db.session.commit()

    return jsonify({'message': 'Login successful', 'user': user.to_dict()})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    email = request.args.get('email', '').strip().lower()
    combo = request.args.get('combo', 'all').strip()

    query = DailyLog.query

    if email:
        query = query.filter(DailyLog.user_email.ilike(email))
    if combo != 'all':
        query = query.filter(DailyLog.combo == combo)

    logs = query.order_by(DailyLog.created_at.desc()).all()
    return jsonify([l.to_dict() for l in logs])

@app.route('/api/logs', methods=['POST'])
def save_log():
    data = request.json or {}

    req_id = data.get('id')
    is_update = data.get('is_update', False)
    user_email = data.get('user_email', 'kishore@techwing.com').strip().lower()
    topics = data.get('topics', '').strip()
    assignment = data.get('assignment', '').strip()

    required_fields = {
        'date': data.get('date', '').strip(),
        'day': data.get('day', '').strip(),
        'lab': data.get('lab', '').strip(),
        'check-in time': data.get('checkIn', '').strip(),
        'check-out time': data.get('checkOut', '').strip(),
        'trainer': data.get('trainer', '').strip(),
        'topics covered': topics,
        'task / assignment': assignment,
    }
    missing_fields = [label for label, value in required_fields.items() if not value]
    if missing_fields:
        return jsonify({'error': f"Please complete the required fields: {', '.join(missing_fields)}."}), 400

    owner_user = User.query.filter(User.email.ilike(user_email)).first()
    if not owner_user:
        owner_user = User.query.filter_by(email=ADMIN_EMAIL).first() or User.query.first()

    existing_log = None
    if is_update and req_id:
        existing_log = DailyLog.query.filter_by(id=req_id).first()

    log_id = existing_log.id if existing_log else (req_id if (req_id and not is_update) else f"log_{int(time.time()*1000)}")

    log_date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    combo_name = data.get('combo', owner_user.combo if owner_user else 'genai-aws')

    if existing_log:
        existing_log.user_id = owner_user.id if owner_user else existing_log.user_id
        existing_log.user_email = user_email
        existing_log.combo = combo_name
        existing_log.log_date = log_date
        existing_log.day = data.get('day', datetime.now().strftime('%A'))
        existing_log.lab = data.get('lab', 'Lab 04')
        existing_log.check_in = data.get('checkIn', '09:30')
        existing_log.check_out = data.get('checkOut', '16:30')
        existing_log.trainer = data.get('trainer', 'Trainer Name')
        existing_log.topics = data.get('topics', '')
        existing_log.practical = data.get('practical', '')
        existing_log.assignment = data.get('assignment', '')
        existing_log.doubts = data.get('doubts', '')
        existing_log.important_notes = data.get('important_notes', data.get('importantNotes', ''))
        existing_log.updated_at = datetime.utcnow()
        target_log = existing_log
        msg = 'Existing log updated successfully'
        action_type = 'LOG_UPDATED'
    else:
        new_log = DailyLog(
            id=log_id,
            user_id=owner_user.id if owner_user else 1,
            user_email=user_email,
            combo=combo_name,
            log_date=log_date,
            day=data.get('day', datetime.now().strftime('%A')),
            lab=data.get('lab', 'Lab 04'),
            check_in=data.get('checkIn', '09:30'),
            check_out=data.get('checkOut', '16:30'),
            trainer=data.get('trainer', 'Trainer Name'),
            topics=data.get('topics', ''),
            practical=data.get('practical', ''),
            assignment=data.get('assignment', ''),
            doubts=data.get('doubts', ''),
            important_notes=data.get('important_notes', data.get('importantNotes', ''))
        )
        db.session.add(new_log)
        target_log = new_log
        msg = 'New log entry saved successfully (duplicate copy supported for date)'
        action_type = 'LOG_CREATED'

    db.session.flush()

    audit = AuditLog(
        user_id=owner_user.id if owner_user else None,
        user_email=user_email,
        action=action_type,
        target_type='DAILY_LOG',
        target_id=log_id,
        metadata_json=json.dumps({'date': log_date, 'combo': combo_name}),
        ip_address=request.remote_addr
    )
    db.session.add(audit)

    db.session.commit()
    return jsonify({'message': msg, 'log': target_log.to_dict()})

def struct_to_bullets(text, prefix="• Topic"):
    """Helper to convert raw spoken phrase into clean structured bullet sentences"""
    clean_text = text.replace('\n', ' ').strip()
    for kw in ['topics covered', 'topic covered', 'topics', 'topic', 'practical work', 'practical', 'hands-on', 'assignment', 'task', 'doubts', 'doubt', 'notes']:
        if clean_text.lower().startswith(kw):
            clean_text = clean_text[len(kw):].strip(': ').strip()

    if not clean_text:
        return ""

    parts = [p.strip() for p in clean_text.split('.') if p.strip()]
    if len(parts) == 1 and ',' in parts[0] and len(parts[0]) > 30:
        parts = [p.strip() for p in parts[0].split(',') if p.strip()]

    formatted_bullets = []
    for i, p in enumerate(parts):
        p_cap = p[0].upper() + p[1:] if len(p) > 1 else p.upper()
        if prefix.lower().startswith('• step'):
            formatted_bullets.append(f"• Step {i+1}: {p_cap}")
        elif prefix.lower().startswith('• topic'):
            formatted_bullets.append(f"• Topic {i+1}: {p_cap}")
        elif prefix.lower().startswith('• task'):
            formatted_bullets.append(f"• Task Assignment: {p_cap}")
        else:
            formatted_bullets.append(f"• Note {i+1}: {p_cap}")

    return "\n".join(formatted_bullets)

@app.route('/api/ai/parse-voice', methods=['POST'])
def ai_parse_voice():
    """Python GenAI Voice Parser: Converts speech into professional structured sentence sequences"""
    data = request.json or {}
    text = data.get('text', '').strip()
    combo = data.get('combo', 'genai-aws')
    requested_target = data.get('target_section', 'auto')

    lower_text = text.lower()

    parsed_topics = ""
    parsed_assignment = ""
    parsed_doubts = ""
    parsed_important_notes = ""

    target_section = 'auto'
    target_name = "Dynamic AI Structurer"

    section_patterns = {
        'topics': r'(?:topics?|covered|learned)\s*(?:covered|today|with|are|:)?\s*',
        'assignment': r'(?:task|assignment|homework)\s*(?:is|with|:)?\s*',
        'doubts': r'(?:doubts?|questions?)\s*(?:are|with|:)?\s*',
        'important_notes': r'(?:important\s+notes?|notes?)\s*(?:are|with|:)?\s*'
    }

    import re
    labels = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in section_patterns.items())
    matches = list(re.finditer(labels, text, flags=re.IGNORECASE))
    if requested_target == 'auto' and len(matches) > 1:
        parsed_values = {name: '' for name in section_patterns}
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            value = text[match.end():end].strip(' ,.;:-')
            parsed_values[match.lastgroup] = struct_to_bullets(value, {
                'topics': '• Topic', 'assignment': '• Task',
                'doubts': '• Doubt', 'important_notes': '• Note'
            }[match.lastgroup])
        parsed_topics = parsed_values['topics']
        parsed_assignment = parsed_values['assignment']
        parsed_doubts = parsed_values['doubts']
        parsed_important_notes = parsed_values['important_notes']
        target_section = 'multiple'
        target_name = 'MULTIPLE FORM SECTIONS'
    elif requested_target == 'topics':
        target_section = 'topics'
        target_name = "TOPICS COVERED TODAY"
        parsed_topics = struct_to_bullets(text, "• Topic")
    elif requested_target == 'assignment':
        target_section = 'assignment'
        target_name = "TASK / ASSIGNMENT"
        parsed_assignment = struct_to_bullets(text, "• Task")
    elif requested_target == 'doubts':
        target_section = 'doubts'
        target_name = "DOUBTS"
        parsed_doubts = struct_to_bullets(text, "• Doubt")
    elif requested_target in ['important', 'important_notes', 'notes']:
        target_section = 'important_notes'
        target_name = "IMPORTANT NOTES"
        parsed_important_notes = struct_to_bullets(text, "• Note")
    else:
        has_topics = any(k in lower_text for k in ['topic', 'covered', 'learned', 'studied', 'theory', 'concept', 'lecture', 'session'])
        has_assignment = any(k in lower_text for k in ['assignment', 'task', 'homework', 'exercise', 'assigned', 'challenge'])
        has_doubts = any(k in lower_text for k in ['doubt', 'doubts', 'question', 'clarification', 'issue'])
        has_important_notes = any(k in lower_text for k in ['important', 'note', 'notes'])

        if has_assignment and not has_topics:
            target_section = 'assignment'
            target_name = "TASK / ASSIGNMENT"
            parsed_assignment = struct_to_bullets(text, "• Task")
        elif has_important_notes and not has_topics:
            target_section = 'important_notes'
            target_name = "IMPORTANT NOTES"
            parsed_important_notes = struct_to_bullets(text, "• Note")
        elif has_doubts and not has_topics:
            target_section = 'doubts'
            target_name = "DOUBTS"
            parsed_doubts = struct_to_bullets(text, "• Doubt")
        else:
            target_section = 'topics'
            target_name = "TOPICS COVERED TODAY"
            parsed_topics = struct_to_bullets(text, "• Topic")

    reply_text = f"🤖 SkillSync Voice AI Structured Your Speech!\n\n" \
                 f"🎯 Target Section(s): **[{target_name}]**\n" \
                 f"📝 Original Voice Prompt: \"{text}\"\n\n" \
                 f"The AI has structured your input into sequential bullet sentences. Click 'Apply to Live Form & Sheet' to populate!"

    return jsonify({
        'reply': reply_text,
        'target_section': target_section,
        'target_name': target_name,
        'prompt_text': text,
        'topics': parsed_topics,
        'assignment': parsed_assignment,
        'doubts': parsed_doubts,
        'important_notes': parsed_important_notes
    })

@app.route('/api/ai/transcribe-voice', methods=['POST'])
def transcribe_voice():
    """Transcribe recorded browser audio for browsers without Web Speech API."""
    api_key = os.environ.get('OPENAI_API_KEY', '').strip()
    audio = request.files.get('audio')
    if not api_key:
        return jsonify({'error': 'Voice transcription is not configured on the server.'}), 503
    if not audio:
        return jsonify({'error': 'No audio recording was received.'}), 400

    try:
        response = requests.post(
            'https://api.openai.com/v1/audio/transcriptions',
            headers={'Authorization': f'Bearer {api_key}'},
            files={'file': (audio.filename or 'voice.webm', audio.stream, audio.mimetype or 'audio/webm')},
            data={'model': os.environ.get('OPENAI_TRANSCRIPTION_MODEL', 'whisper-1'), 'response_format': 'json'},
            timeout=90
        )
        if not response.ok:
            app.logger.error('Voice transcription provider failed: %s', response.text[:500])
            return jsonify({'error': 'Voice transcription service failed. Please try again.'}), 502
        transcript = response.json().get('text', '').strip()
        if not transcript:
            return jsonify({'error': 'No speech was detected in the recording.'}), 422
        return jsonify({'text': transcript})
    except requests.RequestException:
        app.logger.exception('Voice transcription request failed')
        return jsonify({'error': 'Voice transcription service is unavailable.'}), 502

@app.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    suggestions = Suggestion.query.order_by(Suggestion.created_at.desc()).all()
    return jsonify([s.to_dict() for s in suggestions])

@app.route('/api/suggestions', methods=['POST'])
def save_suggestion():
    data = request.json or {}
    name = data.get('name', 'Anonymous Student').strip()
    email = data.get('email', 'student@techwing.com').strip().lower()
    category = data.get('category', 'General Suggestion').strip()
    subject = data.get('subject', 'No Subject').strip()
    message = data.get('message', '').strip()

    if not message or not subject:
        return jsonify({'error': 'Subject and suggestion message cannot be empty'}), 400

    owner_user = User.query.filter(User.email.ilike(email)).first()

    sug_entry = Suggestion(
        id=f'sug_{int(time.time()*1000)}',
        user_id=owner_user.id if owner_user else None,
        date=datetime.now().strftime('%Y-%m-%d %H:%M'),
        name=name,
        email=email,
        category=category,
        subject=subject,
        message=message,
        target_whatsapp='918074404321',
        status='Received'
    )
    db.session.add(sug_entry)

    audit = AuditLog(
        user_id=owner_user.id if owner_user else None,
        user_email=email,
        action='SUGGESTION_CREATED',
        target_type='SUGGESTION',
        target_id=sug_entry.id,
        metadata_json=json.dumps({'subject': subject, 'category': category}),
        ip_address=request.remote_addr
    )
    db.session.add(audit)

    db.session.commit()

    print(f"[SERVER WHATSAPP DISPATCH -> 918074404321]: New suggestion from {name} ({email}) | Category: {category} | Subject: {subject}")

    return jsonify({
        'message': 'Suggestion has been successfully submitted!',
        'status': 'success',
        'suggestion': sug_entry.to_dict()
    })

def get_owner_master():
    passcode = request.args.get('passcode', '')
    email = request.args.get('email', '').lower()

    # Passcode or Admin Role Verification
    is_valid_passcode = passcode in ['admin123', 'techwing123', '8074404321', 'password123']
    user = User.query.filter(User.email.ilike(email)).first() if email else None
    is_admin_user = (user and user.role == 'ADMIN') or (email == ADMIN_EMAIL)

    if not is_valid_passcode and not is_admin_user:
        return jsonify({'error': 'Unauthorized owner access. Admin privileges required.'}), 403

    users = User.query.all()
    logs = DailyLog.query.order_by(DailyLog.created_at.desc()).all()
    suggestions = Suggestion.query.order_by(Suggestion.created_at.desc()).all()
    login_activity = LoginActivity.query.order_by(LoginActivity.login_time.desc()).limit(100).all()
    audit_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(100).all()

    users_list = []
    for u in users:
        log_cnt = DailyLog.query.filter_by(user_id=u.id).count()
        u_dict = u.to_dict()
        u_dict['log_count'] = log_cnt
        users_list.append(u_dict)

    if user:
        audit = AuditLog(
            user_id=user.id,
            user_email=user.email,
            action='ADMIN_VIEW',
            target_type='MASTER_DASHBOARD',
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()

    return jsonify({
        'users': users_list,
        'logs': [l.to_dict() for l in logs],
        'suggestions': [s.to_dict() for s in suggestions],
        'login_activity': [a.to_dict() for a in login_activity],
        'audit_logs': [a.to_dict() for a in audit_logs],
        'combos': COMBO_CONFIGS
    })

def inspect_database():
    passcode = request.args.get('passcode', '')
    email = request.args.get('email', '').lower()

    is_valid_passcode = passcode in ['admin123', 'techwing123', '8074404321', 'password123']
    user = User.query.filter(User.email.ilike(email)).first() if email else None
    is_admin_user = (user and user.role == 'ADMIN') or (email == ADMIN_EMAIL)

    if not is_valid_passcode and not is_admin_user:
        return jsonify({'error': 'Unauthorized owner access.'}), 403

    db_path = app.config['SQLALCHEMY_DATABASE_URI']
    db_size = 0
    raw_path = ""
    if db_path.startswith('sqlite:///'):
        raw_path = db_path.replace('sqlite:///', '')
        if os.path.exists(raw_path):
            db_size = os.path.getsize(raw_path)

    tables_info = {
        'users': {
            'count': User.query.count(),
            'columns': ['id', 'name', 'email', 'combo', 'role', 'is_active', 'created_at', 'last_login_at']
        },
        'daily_logs': {
            'count': DailyLog.query.count(),
            'columns': ['id', 'user_id', 'user_email', 'combo', 'log_date', 'day', 'lab', 'check_in', 'check_out', 'trainer', 'topics', 'practical', 'assignment', 'doubts', 'created_at', 'updated_at']
        },
        'suggestions': {
            'count': Suggestion.query.count(),
            'columns': ['id', 'user_id', 'date', 'name', 'email', 'category', 'subject', 'message', 'target_whatsapp', 'status', 'created_at']
        },
        'login_activity': {
            'count': LoginActivity.query.count(),
            'columns': ['id', 'user_id', 'login_time', 'logout_time', 'ip_address', 'user_agent']
        },
        'audit_logs': {
            'count': AuditLog.query.count(),
            'columns': ['id', 'user_id', 'user_email', 'action', 'target_type', 'target_id', 'metadata_json', 'ip_address', 'created_at']
        }
    }

    return jsonify({
        'status': 'HEALTHY',
        'database_uri': db_path,
        'database_file_path': os.path.abspath(raw_path) if raw_path else db_path,
        'database_size_bytes': db_size,
        'database_size_human': f"{round(db_size / 1024, 2)} KB" if db_size else "N/A",
        'tables': tables_info,
        'recent_audits': [a.to_dict() for a in AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()]
    })

def download_database():
    passcode = request.args.get('passcode', '')
    email = request.args.get('email', '').lower()

    is_valid_passcode = passcode in ['admin123', 'techwing123', '8074404321', 'password123']
    user = User.query.filter(User.email.ilike(email)).first() if email else None
    is_admin_user = (user and user.role == 'ADMIN') or (email == ADMIN_EMAIL)

    if not is_valid_passcode and not is_admin_user:
        return jsonify({'error': 'Unauthorized owner access.'}), 403

    db_path = app.config['SQLALCHEMY_DATABASE_URI']
    if db_path.startswith('sqlite:///'):
        raw_path = db_path.replace('sqlite:///', '')
        if os.path.exists(raw_path):
            directory = os.path.dirname(os.path.abspath(raw_path))
            filename = os.path.basename(raw_path)
            return send_from_directory(directory, filename, as_attachment=True)

    return jsonify({'error': 'Database file download only supported for SQLite.'}), 400


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    print("==========================================================")
    print("TECHWING Daily Training Logbook SQL Database Server Starting...")
    print(f"Open in Browser: http://127.0.0.1:{port}")
    print("Database URI: " + app.config['SQLALCHEMY_DATABASE_URI'])
    print("==========================================================")
    if os.environ.get('FLASK_DEBUG', '').lower() == 'true':
        app.run(host='0.0.0.0', port=port, debug=True)
    else:
        from waitress import serve
        serve(app, host='0.0.0.0', port=port, threads=8)
