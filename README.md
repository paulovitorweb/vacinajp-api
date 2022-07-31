# Vacina JP

Uma aplicação de estudo que fornece uma API mínima escrita em Python e com banco de dados MongoDB para o que seria um sistema de agendamento de vacinas.

## Tecnologias

- FastAPI
- MongoDB
- Beanie
- Docker
- docker-compose

## Build

### Requisitos

- Python >= 3.8
- MongoDB >= 4.4

### Crie um ambiente virtual e ative

```
python3 -m venv venv
source venv/bin/activate
```

### Instale as dependências

```
pip install -r dev-requirements.txt
pip install -r requirements.txt
```

### Suba o container do MongoDB

```
docker-compose up -d
```

### Suba a API

```
make dev
```

### Documentação

- Com Swagger: http://127.0.0.1:8000/docs
- Com ReDoc: http://127.0.0.1:8000/redoc
