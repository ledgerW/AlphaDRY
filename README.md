# 🚀 AlphaDRY 💎

[![FastAPI](https://img.shields.io/badge/FastAPI-0.95.0-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-Enabled-00873C.svg?style=flat)](https://langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Powered-FF6B6B.svg?style=flat)](https://github.com/langchain-ai/langgraph)

🔍 An AI-powered platform for identifying, analyzing, and tracking cryptocurrency token opportunities from social media signals.

## 🌟 Overview

AlphaDRY is a sophisticated system that monitors social media for cryptocurrency token mentions, analyzes them for investment potential, and provides detailed reports with safety scores and recommendations. The platform focuses primarily on Base and Solana blockchain tokens, using multi-agent AI systems to process social signals and generate actionable insights.

## 🏗️ Architecture

```mermaid
graph TD
    A[Social Media Posts] -->|Ingestion| B[Token Finder Agent]
    B -->|Token Identification| C[Database]
    C -->|Token Data| D[Alpha Scout Agent]
    D -->|Research & Analysis| E[Alpha Reports]
    
    F[Web Interface] -->|API Requests| G[FastAPI Backend]
    G -->|Query Data| C
    G -->|Generate Analysis| D
    C -->|Token Data| F
    E -->|Investment Insights| F
    
    H[External APIs] -->|Market Data| D
    H -->|Token Info| C
```

### 🔄 Data Flow

```mermaid
sequenceDiagram
    participant SM as Social Media
    participant TF as Token Finder
    participant AS as Alpha Scout
    participant DB as Database
    participant UI as Web Interface
    
    SM->>TF: Social post with token mention
    TF->>TF: Analyze text for token mentions
    TF->>DB: Store social post & token report
    DB->>AS: Retrieve token data
    AS->>AS: Research token opportunity
    AS->>DB: Store alpha report
    UI->>DB: Request token data
    DB->>UI: Return token & alpha data
    UI->>UI: Display token insights
```

## ✨ Features

- 🔍 **Token Identification**: Automatically identifies purchasable tokens mentioned in social media posts
- 📊 **Market Analysis**: Gathers and analyzes token market data, including price movements and trading volume
- 🛡️ **Safety Scoring**: Evaluates tokens for safety risks and community reputation
- 💰 **Investment Recommendations**: Provides "Buy", "Hold", or "Sell" recommendations with detailed justifications
- 🔄 **Real-time Monitoring**: Tracks social media platforms for new token mentions
- 📱 **Web Interface**: Clean, intuitive UI for exploring tokens and alpha reports
- 🔗 **Multi-chain Support**: Primary focus on Base and Solana blockchains

## 🚀 Getting Started

### 📋 Prerequisites

- Python 3.9+
- PostgreSQL database
- API keys for external services

### 🔧 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/AlphaDRY.git
cd AlphaDRY
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Create a .env file with the following variables
DATABASE_URL=postgresql://user:password@localhost/alphadry
API_KEY=your_api_key_here
OPENAI_API_KEY=your_openai_api_key
```

4. Initialize the database:
```bash
python -c "from database import create_db_and_tables; create_db_and_tables()"
```

5. Run the application:
```bash
uvicorn main:app --reload
```

## 📖 Usage

### 🌐 Web Interface

The platform provides three main pages:

1. **Home Page** (`/`): Displays the Alpha Feed with recent token opportunities
2. **Token Details** (`/token?address={token_address}`): Shows comprehensive information about a specific token
3. **Token List** (`/tokens`): Lists all tracked tokens with filtering and sorting options

### 🔌 API Endpoints

| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/api/alpha_reports` | GET | Get all alpha reports | `/api/alpha_reports?date=2025-05-17` |
| `/api/token/{address}` | GET | Get detailed token information | `/api/token/0x1234...` |
| `/api/tokens` | GET | Get filtered and sorted tokens | `/api/tokens?chains=base,solana&sort_by=market_cap` |
| `/api/analyze_social_post` | POST | Analyze a social media post for token mentions | See API docs |
| `/api/analyze_and_scout` | POST | Analyze post and generate alpha report | See API docs |
| `/api/token/social_summary/{token_address}` | GET | Get summary of social posts about a token | `/api/token/social_summary/0x1234...` |

## 🧪 Testing

Run the test suite with:

```bash
pytest
```

## 📊 Database Schema

```mermaid
erDiagram
    Token ||--o{ TokenReport : has
    Token ||--o{ TokenOpportunity : has
    SocialMediaPost ||--o| TokenReport : generates
    TokenReport ||--o{ TokenOpportunity : identifies
    AlphaReport ||--o{ TokenOpportunity : contains
    
    Token {
        int id PK
        string symbol
        string name
        string chain
        string address
        string image_url
        string website_url
        datetime created_at
    }
    
    SocialMediaPost {
        int id PK
        string source
        string post_id
        string author_id
        string text
        datetime timestamp
        int reactions_count
        int replies_count
    }
    
    TokenReport {
        int id PK
        bool mentions_purchasable_token
        string token_symbol
        string token_chain
        string token_address
        bool is_listed_on_dex
        array trading_pairs
        int confidence_score
        string reasoning
    }
    
    TokenOpportunity {
        int id PK
        string name
        string chain
        string contract_address
        float market_cap
        int community_score
        int safety_score
        string justification
        array sources
        string recommendation
    }
    
    AlphaReport {
        int id PK
        bool is_relevant
        string analysis
        string message
        datetime created_at
    }
```

## 📦 Deployment

For production deployment, refer to the [DEPLOYMENT.md](DEPLOYMENT.md) file for detailed instructions on:

- Database migration and safety procedures
- Environment configuration
- Backup management
- Troubleshooting

<details>
<summary>🔍 Advanced Deployment Options</summary>

## Advanced Options

For high-availability deployments:

1. Set up database replication
2. Configure load balancing
3. Implement caching for API responses
4. Set up monitoring and alerting

</details>

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔍 Project Structure

```
AlphaDRY/
├── agents/                  # AI agent implementations
│   ├── multi_agent_alpha_scout.py    # Token analysis agent
│   ├── multi_agent_token_finder.py   # Token identification agent
│   ├── models.py            # Data models for agents
│   └── tools.py             # Agent tools
├── chains/                  # LangChain components
├── db/                      # Database models and operations
│   ├── models/              # SQLModel definitions
│   ├── operations/          # Database CRUD operations
│   └── scripts/             # Database maintenance scripts
├── evaluation/              # Evaluation metrics and utilities
├── migrations/              # Alembic database migrations
├── routers/                 # FastAPI route definitions
├── static/                  # Static assets (CSS, JS, images)
├── main.py                  # Application entry point
├── database.py              # Database connection
└── requirements.txt         # Python dependencies
