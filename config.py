import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configurações básicas
    SECRET_KEY = os.environ.get('SECRET_KEY', 'brzstable-secret-key-development')
    DEBUG = os.environ.get('FLASK_ENV') != 'production'
    
    # Configurações da Blockchain
    BSC_RPC_URL = os.environ.get('BSC_RPC_URL', 'https://data-seed-prebsc-1-s1.bnbchain.org:8545')
    BRZSTABLE_ADDRESS = os.environ.get('BRZSTABLE_ADDRESS')
    MOCKUSDT_ADDRESS = os.environ.get('MOCKUSDT_ADDRESS')
    
    # Configurações CORS
    cors_origins_str = os.environ.get('CORS_ORIGINS', '')
    CORS_ORIGINS = [origin.strip() for origin in cors_origins_str.split(',') if origin.strip()]
    
    # Configurações do servidor
    PORT = int(os.environ.get('PORT', 5000))
    HOST = os.environ.get('HOST', '0.0.0.0')
    
    # Configurações de rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    
    @staticmethod
    def validate_config():
        """Valida se as configurações obrigatórias estão presentes"""
        required_vars = ['BRZSTABLE_ADDRESS', 'MOCKUSDT_ADDRESS']
        missing_vars = []
        
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Variáveis de ambiente obrigatórias não encontradas: {', '.join(missing_vars)}")
        
        return True

