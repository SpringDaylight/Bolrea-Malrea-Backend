import os
import json
import boto3
from typing import Optional
from dotenv import load_dotenv
from utils.secrets import load_kakao_secrets

# Load environment variables from .env file
load_dotenv()

ENV = os.getenv("ENV", "local")

DEFAULT_WEIGHTS = {
    "emotion": 0.4,
    "narrative": 0.4,
    "ending": 0.2
}

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")

# Kakao OAuth Configuration
KAKAO_SECRETS = load_kakao_secrets()
KAKAO_CLIENT_ID = KAKAO_SECRETS["KAKAO_CLIENT_ID"]
KAKAO_CLIENT_SECRET = KAKAO_SECRETS["KAKAO_CLIENT_SECRET"]
KAKAO_REDIRECT_URI = KAKAO_SECRETS["KAKAO_REDIRECT_URI"]

# AWS RDS Configuration
RDS_SECRET_ARN = os.getenv(
    "RDS_SECRET_ARN",
    "arn:aws:secretsmanager:ap-northeast-2:416963226971:secret:rds!db-f3aa3685-4bca-4982-bae8-c628e185fdf2-078IVh"
)
RDS_HOST = os.getenv("RDS_HOST", "movie-dev-db.cfyyuse8wwfa.ap-northeast-2.rds.amazonaws.com")
RDS_PORT = int(os.getenv("RDS_PORT", "5432"))
RDS_DATABASE = os.getenv("RDS_DATABASE", "movie")
RDS_USER = os.getenv("RDS_USER", "postgres")

# SSL Certificate path
SSL_CERT_PATH = os.getenv("SSL_CERT_PATH", "/certs/global-bundle.pem")


def get_rds_password() -> str:
    """
    Retrieve RDS password from AWS Secrets Manager using IRSA
    
    Returns:
        str: Database password
    """
    # First check for local password (for development)
    local_password = os.getenv("RDS_PASSWORD")
    if local_password:
        print("Using RDS_PASSWORD from environment variable")
        return local_password
    
    # Try Secrets Manager
    try:
        print(f"Attempting to retrieve password from Secrets Manager: {RDS_SECRET_ARN}")
        client = boto3.client('secretsmanager', region_name=AWS_REGION)
        response = client.get_secret_value(SecretId=RDS_SECRET_ARN)
        secret = json.loads(response['SecretString'])
        print("Successfully retrieved password from Secrets Manager")
        return secret['password']
    except Exception as e:
        print(f"ERROR: Failed to get password from Secrets Manager: {e}")
        print(f"Secret ARN: {RDS_SECRET_ARN}")
        print(f"AWS Region: {AWS_REGION}")
        raise RuntimeError(f"Could not retrieve RDS password. Check IRSA permissions and Secret ARN: {e}")


def get_database_url() -> str:
    """
    Construct database URL with password from environment or Secrets Manager
    
    Returns:
        str: SQLAlchemy database URL
    """
    from urllib.parse import quote_plus
    
    # Check if DATABASE_URL is explicitly set (for local override)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        print("Using DATABASE_URL from environment")
        return database_url

    # Local fallback without AWS dependencies
    if ENV.lower() == "local":
        return os.getenv(
            "LOCAL_DATABASE_URL",
            "postgresql+psycopg://movie_user:password@localhost:5432/movie_local",
        )
    
    # Try to get password from environment first (Kubernetes Secret)
    password = os.getenv("RDS_PASSWORD")
    if password:
        print("Using RDS_PASSWORD from environment (Kubernetes Secret)")
    else:
        # Fall back to Secrets Manager
        print("RDS_PASSWORD not found in environment, trying Secrets Manager")
        password = get_rds_password()
    
    # URL encode the password to handle special characters
    encoded_password = quote_plus(password)
    
    # Construct PostgreSQL URL
    db_url = f"postgresql://{RDS_USER}:{encoded_password}@{RDS_HOST}:{RDS_PORT}/{RDS_DATABASE}"
    print(f"Database URL constructed: postgresql://{RDS_USER}:***@{RDS_HOST}:{RDS_PORT}/{RDS_DATABASE}")
    return db_url
