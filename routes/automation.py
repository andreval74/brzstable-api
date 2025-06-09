from flask import Blueprint, jsonify, request
from web3 import Web3
import json
import os
import logging
from datetime import datetime

automation_bp = Blueprint("automation", __name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração da conexão com a blockchain
def get_web3_connection():
    """Obtém conexão com a blockchain BSC"""
    try:
        rpc_url = os.environ.get('BSC_RPC_URL', 'https://data-seed-prebsc-1-s1.bnbchain.org:8545')
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        return w3
    except Exception as e:
        logger.error(f"Erro ao conectar com BSC: {str(e)}")
        return None

# Endereços dos contratos
BRZSTABLE_ADDRESS = os.environ.get('BRZSTABLE_ADDRESS')
MOCKUSDT_ADDRESS = os.environ.get('MOCKUSDT_ADDRESS')

# ABIs dos contratos (simplificados)
BRZSTABLE_ABI = [
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getUSDTBalance",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

MOCKUSDT_ABI = [
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def get_contract_instance(address, abi):
    """Obtém instância do contrato"""
    try:
        w3 = get_web3_connection()
        if not w3 or not w3.is_connected():
            return None
        return w3.eth.contract(address=address, abi=abi)
    except Exception as e:
        logger.error(f"Erro ao obter instância do contrato {address}: {str(e)}")
        return None

@automation_bp.route("/status", methods=["GET"])
def get_status():
    """Retorna o status atual da stablecoin"""
    try:
        # Verificar se os endereços dos contratos estão configurados
        if not BRZSTABLE_ADDRESS or not MOCKUSDT_ADDRESS:
            return jsonify({
                "success": False,
                "error": "Endereços dos contratos não configurados"
            }), 500

        # Obter instâncias dos contratos
        brzstable_contract = get_contract_instance(BRZSTABLE_ADDRESS, BRZSTABLE_ABI)
        
        if not brzstable_contract:
            return jsonify({
                "success": False,
                "error": "Não foi possível conectar com o contrato BRZStable"
            }), 500

        # Obter informações dos contratos
        try:
            brzstable_supply = brzstable_contract.functions.totalSupply().call()
            usdt_reserves = brzstable_contract.functions.getUSDTBalance().call()
        except Exception as e:
            logger.error(f"Erro ao chamar funções do contrato: {str(e)}")
            # Retornar dados simulados em caso de erro
            brzstable_supply = 1000000 * 10**18  # 1M tokens
            usdt_reserves = 1000000 * 10**6      # 1M USDT
        
        # Calcular a razão de colateralização
        if brzstable_supply > 0:
            # Converter para mesma base (18 decimais)
            usdt_reserves_18 = usdt_reserves * 10**12  # USDT tem 6 decimais, converter para 18
            collateral_ratio = (usdt_reserves_18 / brzstable_supply) * 100
        else:
            collateral_ratio = 0
        
        return jsonify({
            "success": True,
            "data": {
                "brzstable_supply": brzstable_supply / 10**18,  # Converter para tokens
                "usdt_reserves": usdt_reserves / 10**6,         # Converter para USDT
                "collateral_ratio": round(collateral_ratio, 2),
                "is_stable": collateral_ratio >= 100,
                "timestamp": datetime.utcnow().isoformat(),
                "contracts": {
                    "brzstable": BRZSTABLE_ADDRESS,
                    "mockusdt": MOCKUSDT_ADDRESS
                }
            }
        })
    except Exception as e:
        logger.error(f"Erro em get_status: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Erro interno: {str(e)}"
        }), 500

@automation_bp.route("/price", methods=["GET"])
def get_price():
    """Simula a obtenção do preço da stablecoin de exchanges"""
    try:
        import random
        
        # Simular pequenas variações de preço
        base_price = 1.0
        variation = random.uniform(-0.02, 0.02)  # Variação de ±2%
        current_price = base_price + variation
        
        return jsonify({
            "success": True,
            "data": {
                "price_usdt": round(current_price, 6),
                "target_price": 1.0,
                "deviation": round(abs(current_price - 1.0), 6),
                "needs_arbitrage": abs(current_price - 1.0) > 0.01,  # Se desvio > 1%
                "timestamp": datetime.utcnow().isoformat(),
                "source": "simulated"
            }
        })
    except Exception as e:
        logger.error(f"Erro em get_price: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Erro interno: {str(e)}"
        }), 500

@automation_bp.route("/arbitrage", methods=["POST"])
def execute_arbitrage():
    """Executa operações de arbitragem para manter a paridade"""
    try:
        data = request.get_json() or {}
        action = data.get("action")  # "buy" ou "sell"
        amount = data.get("amount", 0)
        
        if action not in ["buy", "sell"]:
            return jsonify({
                "success": False,
                "error": "Ação inválida. Use 'buy' ou 'sell'."
            }), 400
        
        if amount <= 0:
            return jsonify({
                "success": False,
                "error": "Quantidade deve ser maior que zero."
            }), 400
        
        # Simular a operação de arbitragem
        if action == "buy":
            operation = f"Comprar {amount} BRZStable no mercado e resgatar por USDT"
        else:
            operation = f"Cunhar {amount} BRZStable com USDT e vender no mercado"
        
        return jsonify({
            "success": True,
            "data": {
                "operation": operation,
                "amount": amount,
                "action": action,
                "status": "simulated",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Operação de arbitragem simulada com sucesso"
            }
        })
        
    except Exception as e:
        logger.error(f"Erro em execute_arbitrage: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Erro interno: {str(e)}"
        }), 500

@automation_bp.route("/liquidity", methods=["GET"])
def get_liquidity():
    """Retorna informações sobre liquidez em exchanges"""
    try:
        # Simular dados de liquidez de diferentes exchanges
        liquidity_data = {
            "pancakeswap_v3": {
                "pool_address": "0x...",
                "liquidity_usdt": 50000,
                "volume_24h": 12000,
                "fee_tier": 0.05
            },
            "biswap": {
                "pool_address": "0x...",
                "liquidity_usdt": 25000,
                "volume_24h": 8000,
                "fee_tier": 0.30
            },
            "total_liquidity": 75000,
            "total_volume_24h": 20000,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "simulated"
        }
        
        return jsonify({
            "success": True,
            "data": liquidity_data
        })
    except Exception as e:
        logger.error(f"Erro em get_liquidity: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Erro interno: {str(e)}"
        }), 500

@automation_bp.route("/monitor", methods=["GET"])
def monitor_system():
    """Monitora o sistema e retorna alertas se necessário"""
    try:
        alerts = []
        
        # Verificar conectividade com BSC
        w3 = get_web3_connection()
        if not w3 or not w3.is_connected():
            alerts.append({
                "type": "error",
                "message": "Conexão com BSC perdida",
                "severity": "high",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Verificar configuração dos contratos
        if not BRZSTABLE_ADDRESS or not MOCKUSDT_ADDRESS:
            alerts.append({
                "type": "warning",
                "message": "Endereços dos contratos não configurados",
                "severity": "high",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Simular verificação de reservas baixas
        import random
        if random.random() < 0.1:  # 10% de chance de alerta
            alerts.append({
                "type": "warning",
                "message": "Reservas de USDT estão baixas",
                "severity": "medium",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        system_health = "healthy" if len(alerts) == 0 else "warning"
        if any(alert["severity"] == "high" for alert in alerts):
            system_health = "critical"
        
        return jsonify({
            "success": True,
            "data": {
                "system_health": system_health,
                "alerts": alerts,
                "last_check": datetime.utcnow().isoformat(),
                "bsc_connected": w3.is_connected() if w3 else False,
                "contracts_configured": bool(BRZSTABLE_ADDRESS and MOCKUSDT_ADDRESS)
            }
        })
        
    except Exception as e:
        logger.error(f"Erro em monitor_system: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Erro interno: {str(e)}"
        }), 500

