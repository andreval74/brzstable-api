# BRZStable API

API de automação e monitoramento para a stablecoin BRZStable, desenvolvida em Flask para implantação no Render.

## Visão Geral

Esta API fornece endpoints para monitoramento e automação da stablecoin BRZStable, incluindo:

- Monitoramento de status e colateralização
- Dados de preço e liquidez
- Sistema de arbitragem automatizado
- Integração com contratos inteligentes na BSC

## Tecnologias

- **Backend:** Python 3.11, Flask
- **Blockchain:** Web3.py, BSC (Binance Smart Chain)
- **Deploy:** Render.com
- **Versionamento:** GitHub

## Configuração Local

### Pré-requisitos

- Python 3.11+
- pip

### Instalação

```bash
# Clonar o repositório
git clone https://github.com/SEU_USUARIO/brzstable-api.git
cd brzstable-api

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações
```

### Execução Local

```bash
python app.py
```

A API estará disponível em `http://localhost:5000`

## Endpoints

### Health Check
- `GET /` - Status básico da API
- `GET /health` - Status detalhado com informações da blockchain

### Automação
- `GET /api/status` - Status da stablecoin (supply, reservas, colateralização)
- `GET /api/price` - Dados de preço e detecção de arbitragem
- `GET /api/liquidity` - Informações de liquidez
- `GET /api/monitor` - Monitoramento do sistema e alertas
- `POST /api/arbitrage` - Execução de operações de arbitragem

## Configuração no Render

### Variáveis de Ambiente

Configure as seguintes variáveis no painel do Render:

```
FLASK_ENV=production
SECRET_KEY=sua-chave-secreta-aqui
BSC_RPC_URL=https://bsc-dataseed.binance.org/
BRZSTABLE_ADDRESS=0xA991a6642ee368683A8308D79a3B6a46c535D851
MOCKUSDT_ADDRESS=0x5Fc088c2890fAB8c481cFB6D0d16f15A7f75c760
CORS_ORIGINS=https://webkeeper.com.br,https://seu-dominio.com
```

### Deploy

O deploy é automático via GitHub. Qualquer push para a branch `main` irá disparar um novo deploy.

## Estrutura do Projeto

```
brzstable-api/
├── app.py                 # Arquivo principal da aplicação
├── config.py             # Configurações da aplicação
├── requirements.txt      # Dependências Python
├── .env.example         # Exemplo de variáveis de ambiente
├── routes/
│   └── automation.py    # Rotas da API de automação
├── utils/
│   └── blockchain.py    # Utilitários para interação com blockchain
└── README.md           # Este arquivo
```

## Contratos Inteligentes

### BSC Testnet
- **BRZStable:** `0xA991a6642ee368683A8308D79a3B6a46c535D851`
- **MockUSDT:** `0x5Fc088c2890fAB8c481cFB6D0d16f15A7f75c760`

### BSC Mainnet
- **BRZStable:** (a ser implantado)
- **USDT:** `0x55d398326f99059fF775485246999027B3197955`

## Desenvolvimento

### Adicionando Novos Endpoints

1. Adicione a rota em `routes/automation.py`
2. Implemente a lógica necessária
3. Atualize a documentação
4. Faça commit e push para deploy automático

### Monitoramento

- Logs estão disponíveis no painel do Render
- Health check endpoint para monitoramento externo
- Alertas automáticos via sistema de monitoramento

## Segurança

- CORS configurado para domínios específicos
- Rate limiting implementado
- Validação de input em todos os endpoints
- Logs de segurança para auditoria

## Suporte

Para suporte e dúvidas, abra uma issue no repositório GitHub.

## Licença

MIT License

