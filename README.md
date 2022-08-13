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

### Testes

Há um conjunto de testes de integração que podem ser executados com

```
make test
```

Ou

```
pytest -v
```

A suíte de testes assíncronos foi construída com:

- pytest
- httpx: para um cliente de testes com suporte a requisições assíncronas
- asgi-lifespan: para conseguir testar a api sem precisar subir o servidor
- pytest-asyncio: para testar código assíncrono com pytest

### Documentação

- Com Swagger: http://127.0.0.1:8000/docs
- Com ReDoc: http://127.0.0.1:8000/redoc

### To do

- [ ] Rota para retornar locais de vacinação por proximidade geográfica
- [ ] Desenho de permissões
- [ ] Login e autenticação
- [ ] Mais cenários de teste
- [ ] Mockar banco com mongomock_motor
- [ ] Implementar cache em rotas mais perenes
