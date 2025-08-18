# DragonBall Power Stats+

### Sistema modular em Python para extração, análise e modelagem de dados do universo Dragon Ball, incorporando Web Scraping avançado, RPA com Playwright, banco SQLite, análise de dados e Machine Learning.

### 🚀 Visão Geral

Este projeto permite:

- Web Scraping Avançado de personagens do Dragon Ball, com fallback automatizado usando Playwright.
- Armazenamento em SQLite através de ORM (SQLAlchemy).
- Processamento e limpeza de dados com pandas e numpy.
- Visualização de insights estatísticos com matplotlib e seaborn.
- Machine Learning para clustering e predição de níveis de poder usando scikit-learn.
- Estrutura orientada a objetos, modular e testável, ideal para portfólio profissional.

### 📦 Tecnologias e Dependências

- Python 3.12+
- Web Scraping: aiohttp, requests, beautifulsoup4, lxml
- RPA: playwright (Chromium)
- Banco de Dados: sqlite3, SQLAlchemy
- Análise de Dados: pandas, numpy
- Visualização: matplotlib, seaborn
- Machine Learning: scikit-learn
- Testes: pytest
- Versionamento: Git (branches main, dev)

### 🛠️ Instalação

Clone este repositório:

- git clone https://github.com/seu-usuario/dragonball_power_stats_plus.git

- cd dragonball_power_stats_plus

- Crie e ative um ambiente virtual (recomendado):

 ```python
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\\Scripts\\activate  # Windows
 ```

- Instale as dependências:
  
 ```bash
pip install -r requirements.txt
playwright install
 ```

### ⚙️ Configuração

- Verifique o arquivo dragonball/config.py para ajustar parâmetros como:
- BASE_URL: URL da wiki
- DB_PATH: caminho do arquivo SQLite
- HEADLESS: modo headless do Playwright

### 📁 Estrutura do Projeto

dragonball_power_stats_plus/
```bash
├── data/                 # Arquivos de banco e dumps brutos
│   └── dragonball.db     # SQLite database
│
├── dragonball/           # Pacote principal
│   ├── __init__.py       # Inicialização do módulo
│   ├── config.py         # Configurações globais
│   ├── db.py             # ORM e modelos SQLAlchemy
│   ├── scraper.py        # Scraper assíncrono (aiohttp)
│   ├── rpa_bot.py        # RPA com Playwright
│   ├── parser.py         # Limpeza e normalização de dados
│   ├── features.py       # Extração de features para ML
│   └── ml_model.py       # Modelos de clustering e regressão
│
├── notebooks/            # Análises exploratórias e ML em Jupyter
│   └── dragonball_analysis.ipynb
│
├── scripts/              # Scripts utilitários
│   └── run_all.py        # Pipeline completo: scraping → DB → análise
│
├── tests/                # Testes unitários (pytest)
│   └── test_scraper.py
│
├── figures/              # Gráficos gerados pelo pipeline
│
├── requirements.txt      # Dependências do projeto
├── README.md             # Documentação principal
└── .gitignore            # Arquivos a serem ignorados pelo Git 
```
### 🚀 Uso Rápido

- Extrair e Popular Banco
- python scripts/run_all.py --stage=db
- Analisar e Gerar Gráficos
- python scripts/run_all.py --stage=analysis
- Executar Notebooks Interativos
- jupyter notebook notebooks/dragonball_analysis.ipynb

### 🧪 Testes

- Execute todos os testes com:
- pytest --maxfail=1 --disable-warnings -q

### Diagrama Entidade-Relacionamento (Banco de Dados)

<img width="1769" height="944" alt="Diagrama Banco de Dados" src="https://github.com/user-attachments/assets/0263b809-1bd3-4fcb-b30c-0b4d3fccc512" />



