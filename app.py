import os
import logging
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from routes.automation import automation_bp

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)
logger = logging.getLogger(__name__)

def create_app():
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)
    
    # Carregar configurações
    app.config.from_object(Config)
    
    # Validar configurações obrigatórias
    try:
        Config.validate_config()
    except ValueError as e:
        logger.error(f"Erro de configuração: {str(e)}")
        # Em ambiente de desenvolvimento, continuar mesmo com configurações faltando
        if os.environ.get('FLASK_ENV') == 'production':
            raise e
        else:
            logger.warning("Executando em modo de desenvolvimento com configurações incompletas")
    
    # Configurar CORS
    if app.config['CORS_ORIGINS']:
        CORS(app, origins=app.config['CORS_ORIGINS'])
        logger.info(f"CORS configurado para: {app.config['CORS_ORIGINS']}")
    else:
        CORS(app)  # Permitir todas as origens para desenvolvimento
        logger.info("CORS configurado para todas as origens (desenvolvimento)")
    
    # Registrar blueprints
    app.register_blueprint(automation_bp, url_prefix='/api')
    
    # Rotas principais
    @app.route('/')
    def health_check():
        """Health check básico"""
        return jsonify({
            "status": "healthy", 
            "message": "BRZStable API is running",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": os.environ.get('FLASK_ENV', 'development')
        })
    
    @app.route('/health')
    def detailed_health_check():
        """Health check detalhado"""
        try:
            from web3 import Web3
            
            # Verificar conectividade com BSC
            rpc_url = app.config['BSC_RPC_URL']
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            is_connected = False
            latest_block = None
            
            try:
                is_connected = w3.is_connected()
                if is_connected:
                    latest_block = w3.eth.block_number
            except Exception as e:
                logger.error(f"Erro ao verificar conexão BSC: {str(e)}")
            
            return jsonify({
                "status": "healthy" if is_connected else "degraded",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0",
                "environment": os.environ.get('FLASK_ENV', 'development'),
                "bsc_connection": {
                    "connected": is_connected,
                    "rpc_url": rpc_url,
                    "latest_block": latest_block
                },
                "contracts": {
                    "brzstable_address": app.config['BRZSTABLE_ADDRESS'],
                    "mockusdt_address": app.config['MOCKUSDT_ADDRESS']
                },
                "cors_origins": app.config['CORS_ORIGINS']
            })
        except Exception as e:
            logger.error(f"Erro no health check detalhado: {str(e)}")
            return jsonify({
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }), 500
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "status": "error",
            "message": "Endpoint não encontrado",
            "timestamp": datetime.utcnow().isoformat()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Erro interno do servidor: {str(error)}")
        return jsonify({
            "status": "error",
            "message": "Erro interno do servidor",
            "timestamp": datetime.utcnow().isoformat()
        }), 500
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "status": "error",
            "message": "Método não permitido",
            "timestamp": datetime.utcnow().isoformat()
        }), 405
    
    return app

# Criar aplicação
app = create_app()

if __name__ == '__main__':
    # Configuração para execução local
    port = app.config['PORT']
    host = app.config['HOST']
    debug = app.config['DEBUG']
    
    logger.info(f"Iniciando BRZStable API...")
    logger.info(f"Ambiente: {os.environ.get('FLASK_ENV', 'development')}")
    logger.info(f"Host: {host}")
    logger.info(f"Porta: {port}")
    logger.info(f"Debug: {debug}")
    logger.info(f"BSC RPC: {app.config['BSC_RPC_URL']}")
    logger.info(f"BRZStable: {app.config['BRZSTABLE_ADDRESS']}")
    logger.info(f"MockUSDT: {app.config['MOCKUSDT_ADDRESS']}")
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug
        )
    except Exception as e:
        logger.error(f"Erro ao iniciar a aplicação: {str(e)}")
        exit(1)

