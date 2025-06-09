from flask import Blueprint, jsonify, request
from web3 import Web3
import json
import requests
import time
import logging
from datetime import datetime

# Blueprint para rotas de automação multi-rede
automation_bp = Blueprint('automation', __name__)

# Configuração Web3 para BSC Testnet
BSC_TESTNET_RPC = "https://data-seed-prebsc-1-s1.bnbchain.org:8545"
w3 = Web3(Web3.HTTPProvider(BSC_TESTNET_RPC))

# Endereços dos contratos (serão atualizados quando você implantar)
CONTRACTS = {
    "MOCKUSDT": "0x5Fc088c2890fAB8c481cFB6D0d16f15A7f75c760",
    "BRZSTABLE": "0xA991a6642ee368683A8308D79a3B6a46c535D851",
    "MULTI_LIQUIDITY_MANAGER": "0x0000000000000000000000000000000000000000",  # Será atualizado
    "STABLECOIN_FACTORY": "0x0000000000000000000000000000000000000000"      # Será atualizado
}

# ABIs simplificadas
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]

LIQUIDITY_MANAGER_ABI = [
    {
        "inputs": [
            {"name": "tokenA", "type": "address"},
            {"name": "tokenB", "type": "address"},
            {"name": "amountA", "type": "uint256"},
            {"name": "amountB", "type": "uint256"}
        ],
        "name": "createPool",
        "outputs": [{"name": "poolId", "type": "bytes32"}],
        "type": "function"
    },
    {
        "inputs": [{"name": "poolId", "type": "bytes32"}],
        "name": "getPoolInfo",
        "outputs": [
            {
                "components": [
                    {"name": "tokenA", "type": "address"},
                    {"name": "tokenB", "type": "address"},
                    {"name": "pairAddress", "type": "address"},
                    {"name": "liquidityAmount", "type": "uint256"},
                    {"name": "isActive", "type": "bool"},
                    {"name": "createdAt", "type": "uint256"},
                    {"name": "networkId", "type": "uint256"}
                ],
                "name": "",
                "type": "tuple"
            }
        ],
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getAllPoolIds",
        "outputs": [{"name": "", "type": "bytes32[]"}],
        "type": "function"
    },
    {
        "inputs": [
            {"name": "poolId", "type": "bytes32"},
            {"name": "priceOfTokenA", "type": "bool"}
        ],
        "name": "getTokenPrice",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

STABLECOIN_FACTORY_ABI = [
    {
        "inputs": [
            {"name": "name", "type": "string"},
            {"name": "symbol", "type": "string"},
            {"name": "collateralToken", "type": "address"},
            {"name": "initialSupply", "type": "uint256"},
            {"name": "collateralRatio", "type": "uint256"},
            {"name": "initialLiquidityA", "type": "uint256"},
            {"name": "initialLiquidityB", "type": "uint256"}
        ],
        "name": "createStablecoin",
        "outputs": [{"name": "stablecoinId", "type": "bytes32"}],
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getAllStablecoinIds",
        "outputs": [{"name": "", "type": "bytes32[]"}],
        "type": "function"
    },
    {
        "inputs": [{"name": "stablecoinId", "type": "bytes32"}],
        "name": "getStablecoinInfo",
        "outputs": [
            {
                "components": [
                    {"name": "stablecoinAddress", "type": "address"},
                    {"name": "liquidityManagerAddress", "type": "address"},
                    {"name": "poolId", "type": "bytes32"},
                    {
                        "components": [
                            {"name": "name", "type": "string"},
                            {"name": "symbol", "type": "string"},
                            {"name": "collateralToken", "type": "address"},
                            {"name": "initialSupply", "type": "uint256"},
                            {"name": "collateralRatio", "type": "uint256"},
                            {"name": "isActive", "type": "bool"},
                            {"name": "createdAt", "type": "uint256"}
                        ],
                        "name": "config",
                        "type": "tuple"
                    }
                ],
                "name": "",
                "type": "tuple"
            }
        ],
        "type": "function"
    }
]

def get_contract_instance(address, abi):
    """Cria instância de contrato Web3"""
    try:
        if address == "0x0000000000000000000000000000000000000000":
            return None
        return w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)
    except Exception as e:
        logging.error(f"Erro ao criar instância do contrato {address}: {e}")
        return None

def get_token_info(token_address):
    """Obtém informações básicas de um token ERC20"""
    try:
        contract = get_contract_instance(token_address, ERC20_ABI)
        if not contract:
            return None
            
        return {
            "address": token_address,
            "name": contract.functions.name().call(),
            "symbol": contract.functions.symbol().call(),
            "decimals": contract.functions.decimals().call(),
            "totalSupply": contract.functions.totalSupply().call()
        }
    except Exception as e:
        logging.error(f"Erro ao obter informações do token {token_address}: {e}")
        return None

@automation_bp.route('/status', methods=['GET'])
def get_status():
    """Status geral do sistema multi-rede"""
    try:
        # Informações básicas da rede
        latest_block = w3.eth.block_number
        
        # Informações dos tokens principais
        mockusdt_info = get_token_info(CONTRACTS["MOCKUSDT"])
        brzstable_info = get_token_info(CONTRACTS["BRZSTABLE"])
        
        # Status dos contratos de gerenciamento
        liquidity_manager = get_contract_instance(CONTRACTS["MULTI_LIQUIDITY_MANAGER"], LIQUIDITY_MANAGER_ABI)
        factory = get_contract_instance(CONTRACTS["STABLECOIN_FACTORY"], STABLECOIN_FACTORY_ABI)
        
        return jsonify({
            "status": "success",
            "network": {
                "name": "BSC Testnet",
                "chainId": 97,
                "latestBlock": latest_block,
                "rpcUrl": BSC_TESTNET_RPC
            },
            "contracts": {
                "mockUSDT": mockusdt_info,
                "brzStable": brzstable_info,
                "liquidityManager": {
                    "address": CONTRACTS["MULTI_LIQUIDITY_MANAGER"],
                    "isDeployed": liquidity_manager is not None
                },
                "stablecoinFactory": {
                    "address": CONTRACTS["STABLECOIN_FACTORY"],
                    "isDeployed": factory is not None
                }
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Erro ao obter status: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@automation_bp.route('/pools', methods=['GET'])
def get_all_pools():
    """Lista todos os pools de liquidez"""
    try:
        liquidity_manager = get_contract_instance(CONTRACTS["MULTI_LIQUIDITY_MANAGER"], LIQUIDITY_MANAGER_ABI)
        
        if not liquidity_manager:
            return jsonify({
                "status": "error",
                "message": "Liquidity Manager não implantado"
            }), 400
        
        # Obter todos os IDs de pools
        pool_ids = liquidity_manager.functions.getAllPoolIds().call()
        
        pools = []
        for pool_id in pool_ids:
            try:
                pool_info = liquidity_manager.functions.getPoolInfo(pool_id).call()
                
                # Obter informações dos tokens
                token_a_info = get_token_info(pool_info[0])
                token_b_info = get_token_info(pool_info[1])
                
                # Obter preço atual
                try:
                    price = liquidity_manager.functions.getTokenPrice(pool_id, True).call()
                    price_formatted = price / 1e18
                except:
                    price_formatted = 0
                
                pools.append({
                    "poolId": pool_id.hex(),
                    "tokenA": token_a_info,
                    "tokenB": token_b_info,
                    "pairAddress": pool_info[2],
                    "liquidityAmount": pool_info[3],
                    "isActive": pool_info[4],
                    "createdAt": pool_info[5],
                    "networkId": pool_info[6],
                    "currentPrice": price_formatted
                })
                
            except Exception as e:
                logging.error(f"Erro ao processar pool {pool_id.hex()}: {e}")
                continue
        
        return jsonify({
            "status": "success",
            "pools": pools,
            "totalPools": len(pools)
        })
        
    except Exception as e:
        logging.error(f"Erro ao obter pools: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@automation_bp.route('/stablecoins', methods=['GET'])
def get_all_stablecoins():
    """Lista todas as stablecoins criadas"""
    try:
        factory = get_contract_instance(CONTRACTS["STABLECOIN_FACTORY"], STABLECOIN_FACTORY_ABI)
        
        if not factory:
            return jsonify({
                "status": "error",
                "message": "Stablecoin Factory não implantado"
            }), 400
        
        # Obter todos os IDs de stablecoins
        stablecoin_ids = factory.functions.getAllStablecoinIds().call()
        
        stablecoins = []
        for stablecoin_id in stablecoin_ids:
            try:
                stablecoin_info = factory.functions.getStablecoinInfo(stablecoin_id).call()
                
                # Obter informações do token
                token_info = get_token_info(stablecoin_info[0])
                
                stablecoins.append({
                    "stablecoinId": stablecoin_id.hex(),
                    "address": stablecoin_info[0],
                    "liquidityManagerAddress": stablecoin_info[1],
                    "poolId": stablecoin_info[2].hex(),
                    "tokenInfo": token_info,
                    "config": {
                        "name": stablecoin_info[3][0],
                        "symbol": stablecoin_info[3][1],
                        "collateralToken": stablecoin_info[3][2],
                        "initialSupply": stablecoin_info[3][3],
                        "collateralRatio": stablecoin_info[3][4],
                        "isActive": stablecoin_info[3][5],
                        "createdAt": stablecoin_info[3][6]
                    }
                })
                
            except Exception as e:
                logging.error(f"Erro ao processar stablecoin {stablecoin_id.hex()}: {e}")
                continue
        
        return jsonify({
            "status": "success",
            "stablecoins": stablecoins,
            "totalStablecoins": len(stablecoins)
        })
        
    except Exception as e:
        logging.error(f"Erro ao obter stablecoins: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@automation_bp.route('/price/<token_address>', methods=['GET'])
def get_token_price(token_address):
    """Obtém preço de um token específico"""
    try:
        # Simular preço baseado em USDT com pequena variação
        base_price = 1.0
        variation = (time.time() % 100) / 10000  # Variação de ±0.01
        current_price = base_price + (variation - 0.005)
        
        # Calcular desvio percentual
        deviation = ((current_price - base_price) / base_price) * 100
        
        return jsonify({
            "status": "success",
            "tokenAddress": token_address,
            "price": {
                "current": round(current_price, 6),
                "target": base_price,
                "deviation": round(deviation, 3),
                "currency": "USDT"
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Erro ao obter preço: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@automation_bp.route('/arbitrage/opportunities', methods=['GET'])
def get_arbitrage_opportunities():
    """Detecta oportunidades de arbitragem"""
    try:
        opportunities = []
        
        # Simular oportunidades de arbitragem
        if time.time() % 30 < 10:  # 1/3 do tempo há oportunidades
            opportunities.append({
                "poolId": "0x1234567890abcdef",
                "tokenPair": "BRZ/USDT",
                "priceDeviation": 0.15,
                "potentialProfit": 0.08,
                "recommendedAction": "buy_brz",
                "urgency": "medium"
            })
        
        return jsonify({
            "status": "success",
            "opportunities": opportunities,
            "totalOpportunities": len(opportunities),
            "lastCheck": datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Erro ao detectar arbitragem: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@automation_bp.route('/monitor/system', methods=['GET'])
def monitor_system():
    """Monitoramento geral do sistema"""
    try:
        # Status da conexão blockchain
        latest_block = w3.eth.block_number
        
        # Simular métricas do sistema
        system_metrics = {
            "uptime": "99.8%",
            "totalTransactions": 1247,
            "totalVolume": 125430.50,
            "activeArbitrages": 3,
            "systemHealth": "excellent"
        }
        
        return jsonify({
            "status": "success",
            "blockchain": {
                "connected": True,
                "latestBlock": latest_block,
                "network": "BSC Testnet"
            },
            "metrics": system_metrics,
            "alerts": [],
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Erro no monitoramento: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@automation_bp.route('/contracts/update', methods=['POST'])
def update_contract_addresses():
    """Atualiza endereços dos contratos"""
    try:
        data = request.get_json()
        
        if 'liquidityManager' in data:
            CONTRACTS["MULTI_LIQUIDITY_MANAGER"] = data['liquidityManager']
        
        if 'stablecoinFactory' in data:
            CONTRACTS["STABLECOIN_FACTORY"] = data['stablecoinFactory']
        
        return jsonify({
            "status": "success",
            "message": "Endereços atualizados com sucesso",
            "contracts": CONTRACTS
        })
        
    except Exception as e:
        logging.error(f"Erro ao atualizar contratos: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@automation_bp.route('/networks/supported', methods=['GET'])
def get_supported_networks():
    """Lista redes suportadas"""
    try:
        networks = [
            {
                "chainId": 97,
                "name": "BSC Testnet",
                "rpcUrl": "https://data-seed-prebsc-1-s1.bnbchain.org:8545",
                "explorer": "https://testnet.bscscan.com",
                "nativeCurrency": "tBNB",
                "isActive": True,
                "dex": {
                    "name": "PancakeSwap",
                    "factory": "0x6725F303b657a9451d8BA641348b6761A6CC7a17",
                    "router": "0xD99D1c33F9fC3444f8101754aBC46c52416550D1"
                }
            }
        ]
        
        return jsonify({
            "status": "success",
            "networks": networks,
            "totalNetworks": len(networks)
        })
        
    except Exception as e:
        logging.error(f"Erro ao obter redes: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

