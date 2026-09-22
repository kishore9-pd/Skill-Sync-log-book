"""
Script to update COMBO_CONFIGS in app.py with the 7 official TechWing SkillSync combos.
"""
import re

NEW_COMBO_CONFIGS = '''# Official TechWing SkillSync Tech Combos (7 Combos)
# INFRA: AWS+DevOps, AWS+AI_JFS
# PROD:  AWS+Gen_AI, AWS+Agentic_AI, Gen_AI+Agentic_AI
# DEV:   AI_JFS+DevOps, AI_JFS+AWS_SA
COMBO_CONFIGS = {

    # ─── INFRA TRACK ───────────────────────────────────────────────────────
    \'AWS+DEVOPS\': {
        \'name\': \'AWS + DevOps\',
        \'subtitle\': \'AWS + DevOps | INFRA Track — Daily Class Record\',
        \'defaultTrainer\': \'Kishore Kumar\',
        \'defaultLab\': \'Lab 01 - AWS Cloud Operations Lab\',
        \'topics\': \'• Topic 1: AWS Core Infrastructure — EC2, VPC, IAM, S3\\n• Topic 2: Terraform Infrastructure as Code (IaC) & AWS CloudFormation\\n• Topic 3: CI/CD Pipelines with GitHub Actions, CodePipeline & ECS Fargate\',
        \'practical\': \'• Step 1: Provisioned multi-AZ VPC with public/private subnets using Terraform\\n• Step 2: Configured GitHub Actions workflow for automated ECR push & ECS deploy\\n• Step 3: Set up CloudWatch alarms and SNS alerts for production monitoring\',
        \'assignment\': \'• Write Terraform modules to deploy a full AWS production environment with auto-scaling & CI/CD.\',
        \'doubts\': \'• Clarified Terraform state lock management using S3 & DynamoDB backend.\\n• Note: Always run terraform plan before applying any infrastructure changes.\'
    },
    \'AWS+AI-JFS\': {
        \'name\': \'AWS + AI_JFS\',
        \'subtitle\': \'AWS + AI Java Full Stack | INFRA Track — Daily Class Record\',
        \'defaultTrainer\': \'Kishore Kumar\',
        \'defaultLab\': \'Lab 02 - Enterprise Java & AWS Cloud Hub\',
        \'topics\': \'• Topic 1: Spring Boot REST APIs & AWS Integration Patterns\\n• Topic 2: AWS RDS, DynamoDB & ElasticCache for Java Applications\\n• Topic 3: AWS Lambda, API Gateway & Serverless Java Architecture\',
        \'practical\': \'• Step 1: Built Spring Boot microservice connected to AWS RDS PostgreSQL\\n• Step 2: Deployed serverless Java function to AWS Lambda with SnapStart enabled\\n• Step 3: Configured API Gateway endpoints with IAM Auth & Lambda Proxy integration\',
        \'assignment\': \'• Deploy a full Spring Boot + React application on AWS using ECS Fargate with RDS backend.\',
        \'doubts\': \'• Discussed cold start mitigation strategies for AWS Lambda Java runtime.\\n• Note: Use AWS SDK v2 for asynchronous non-blocking requests in Java.\'
    },

    # ─── PROD TRACK ────────────────────────────────────────────────────────
    \'AWS+GENAI\': {
        \'name\': \'AWS + Gen_AI\',
        \'subtitle\': \'AWS + Generative AI | PROD Track — Daily Class Record\',
        \'defaultTrainer\': \'Kishore Kumar\',
        \'defaultLab\': \'Lab 03 - GenAI & AWS Bedrock Hub\',
        \'topics\': \'• Topic 1: Generative AI Foundations — LLMs, Prompting & Embeddings\\n• Topic 2: Amazon Bedrock — Titan, Claude, Llama2 Model Integration\\n• Topic 3: RAG Architecture with OpenSearch Serverless & LangChain\',
        \'practical\': \'• Step 1: Provisioned Amazon Bedrock Knowledge Base connected to S3 data source\\n• Step 2: Ingested PDF documents into OpenSearch Serverless vector index\\n• Step 3: Implemented LangChain ConversationalRetrievalChain with memory in Python\',
        \'assignment\': \'• Build a production-ready RAG Q&A chatbot using Amazon Bedrock, LangChain & OpenSearch.\',
        \'doubts\': \'• Discussed dense vector embeddings vs sparse BM25 keyword indexing trade-offs.\\n• Note: Pause OpenSearch Serverless collection when idle to prevent unnecessary costs.\'
    },
    \'AWS+AGENTIC AI-JFS\': {
        \'name\': \'AWS + Agentic_AI\',
        \'subtitle\': \'AWS + Agentic AI | PROD Track — Daily Class Record\',
        \'defaultTrainer\': \'Kishore Kumar\',
        \'defaultLab\': \'Lab 04 - Agentic AI & AWS Systems Hub\',
        \'topics\': \'• Topic 1: Agentic AI Frameworks — LangGraph, CrewAI & AutoGen\\n• Topic 2: AWS Bedrock Agents with Tool Use & Function Calling\\n• Topic 3: Multi-Agent Orchestration & Supervisor-Subagent Patterns on AWS\',
        \'practical\': \'• Step 1: Built custom Python AI agents with AWS Bedrock tool execution access\\n• Step 2: Implemented supervisor-subagent graph execution loop using LangGraph\\n• Step 3: Deployed multi-agent system to AWS Lambda with event-driven triggers\',
        \'assignment\': \'• Build an AWS-hosted multi-agent AI system that autonomously researches, codes, and deploys solutions.\',
        \'doubts\': \'• Discussed infinite loop prevention & max iteration token limits in agentic loops.\\n• Note: Always set max execution steps and fallback handlers on agent executors.\'
    },
    \'GENAI +AGENTIC AI\': {
        \'name\': \'Gen_AI + Agentic_AI\',
        \'subtitle\': \'Gen_AI + Agentic_AI | PROD Track — Daily Class Record\',
        \'defaultTrainer\': \'Kishore Kumar\',
        \'defaultLab\': \'Lab 05 - Autonomous AI Agents Hub\',
        \'topics\': \'• Topic 1: Generative AI — LLMs, RAG & Prompt Engineering Masterclass\\n• Topic 2: Agentic AI Workflows — ReAct, Tool Use & Dynamic Planning\\n• Topic 3: Multi-Agent Systems with LangGraph, CrewAI & Memory Management\',
        \'practical\': \'• Step 1: Built a RAG pipeline using ChromaDB + LangChain with streaming responses\\n• Step 2: Constructed multi-step AI agent with tools for search, code & data analysis\\n• Step 3: Implemented LangGraph agent graph with conditional routing & state management\',
        \'assignment\': \'• Build a fully autonomous AI research assistant using GenAI + Agentic workflows end-to-end.\',
        \'doubts\': \'• Analyzed trade-offs between single-agent vs multi-agent architectures for production.\\n• Note: Always define max_iterations and fallback responses in agent executor configs.\'
    },

    # ─── DEV TRACK ─────────────────────────────────────────────────────────
    \'AI-JFS-devops\': {
        \'name\': \'AI_JFS + DevOps\',
        \'subtitle\': \'AI Java Full Stack + DevOps | DEV Track — Daily Class Record\',
        \'defaultTrainer\': \'Kishore Kumar\',
        \'defaultLab\': \'Lab 06 - Java Full Stack & DevOps Hub\',
        \'topics\': \'• Topic 1: Spring Boot Microservices & REST API Design Patterns\\n• Topic 2: Docker Containerization & Kubernetes (K8s) Orchestration\\n• Topic 3: CI/CD Automation with Jenkins, GitHub Actions & AWS ECS\',
        \'practical\': \'• Step 1: Built Spring Boot REST API with Spring Data JPA & PostgreSQL backend\\n• Step 2: Created multi-stage Dockerfile and deployed container to K8s cluster\\n• Step 3: Configured automated build, test & deploy pipeline using Jenkins + GitHub Actions\',
        \'assignment\': \'• Deploy a full-stack containerized Spring Boot + React app to AWS EKS with complete CI/CD pipeline.\',
        \'doubts\': \'• Understood Pod Horizontal Pod Autoscaler (HPA) metrics & ingress controller routing.\\n• Note: Store all database credentials in Kubernetes Secrets, never in plain environment variables.\'
    },
    \'AI-JFS+AWS SA\': {
        \'name\': \'AI_JFS + AWS_SA\',
        \'subtitle\': \'AI Java Full Stack + AWS Solutions Architect | DEV Track — Daily Class Record\',
        \'defaultTrainer\': \'Kishore Kumar\',
        \'defaultLab\': \'Lab 07 - Cloud Architecture & Java Engineering Hub\',
        \'topics\': \'• Topic 1: AWS Solutions Architect — VPC, IAM, EC2, RDS & High Availability Design\\n• Topic 2: Spring Cloud Microservices & AWS API Gateway Integration\\n• Topic 3: AWS Auto Scaling, Elastic Load Balancing & Multi-AZ Fault Tolerance\',
        \'practical\': \'• Step 1: Designed multi-AZ VPC architecture with public/private subnets & NAT Gateways\\n• Step 2: Connected Spring Boot microservices via AWS API Gateway with IAM Authorization\\n• Step 3: Implemented Auto Scaling Group tied to Application Load Balancer with health checks\',
        \'assignment\': \'• Architect a highly available, fault-tolerant Java web application on AWS with RDS Multi-AZ & ALB.\',
        \'doubts\': \'• Reviewed VPC peering vs AWS Transit Gateway latency & cost trade-offs.\\n• Note: Always restrict Security Group ingress ports to minimum required ranges only.\'
    }
}
'''

# Read the app.py file
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the start and end of COMBO_CONFIGS using regex
start_marker = '# Default Training Combo Configuration Registry'
end_marker = '\n}\n\n# Auto-initialize'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx)

if start_idx == -1 or end_idx == -1:
    print(f"ERROR: Could not find markers. start_idx={start_idx}, end_idx={end_idx}")
    # Try alternate end
    end_idx2 = content.find('\n}\n\n# Auto-initialize', start_idx)
    print(f"Alternate end search: {end_idx2}")
else:
    # Replace from start marker to the closing } of COMBO_CONFIGS
    new_content = content[:start_idx] + NEW_COMBO_CONFIGS + content[end_idx + len(end_marker):]
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ COMBO_CONFIGS updated successfully in app.py!")
    print(f"   Replaced from line position {start_idx} to {end_idx}")
    
    # Verify the new combos are in place
    with open('app.py', 'r', encoding='utf-8') as f:
        verify = f.read()
    
    combos_to_check = ['AWS+DEVOPS', 'AWS+AI-JFS', 'AWS+GENAI', 'AWS+AGENTIC AI-JFS', 
                       'GENAI +AGENTIC AI', 'AI-JFS-devops', 'AI-JFS+AWS SA']
    removed_combos = ['genai-aws', 'fullstack-devops', 'datascience-azure', 'aiml-gcp', 
                      'cyber-cloud', 'python-analytics']
    
    print("\nVerification:")
    for c in combos_to_check:
        status = "✅" if f"'{c}'" in verify else "❌"
        print(f"  {status} Present: '{c}'")
    
    for c in removed_combos:
        status = "✅ Removed" if f"'{c}'" not in verify else "❌ Still present"
        print(f"  {status}: '{c}'")
