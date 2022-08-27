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

Há três conjuntos de testes que podem ser encontrados na pasta `tests`. São eles:

- unitários: testam pequenas unidades de código, isolando-as de dependências externas, como o banco de dados, e de módulos externos;
- de integração: testam a camada de abstração do banco de dados (única dependência externa até o momento), verificando se os métodos do repositório refletem corretamente no banco de dados e vive-versa;
- end-to-end: testam a API, verificando se as chamadas aos endpoints têm o retorno esperado, unidos dentro de um contexto de uso (do cadastro de usuário, passando pelo agendamento, baixa da vacina aplicada e disponibilização no cartão de vacina digital).

Os testes podem ser executados com:

```
make test
```

A cobertura do código fica disponível em `htmlcov/index.html`.

É possível ver a saída verbosa. Atente-se para a necessidade de definir a variável de ambiente com o nome do banco de teste no escopo dos testes. Por exemplo:

```
MONGO_DB=test pytest -v
```

A suíte de testes assíncronos foi construída com:

- pytest
- pytest-mock: que oferece uma fixture com recursos de mock do módulo unittest do Python
- httpx: para um cliente de testes com suporte a requisições assíncronas
- asgi-lifespan: para conseguir testar a api sem precisar subir o servidor
- pytest-asyncio: para testar código assíncrono com pytest

### Documentação

- Com Swagger: http://127.0.0.1:8000/docs
- Com ReDoc: http://127.0.0.1:8000/redoc

### To do

- [ ] Frontend
- [ ] Rota para retornar locais de vacinação por proximidade geográfica
- [ ] Mais cenários de teste
- [ ] Implementar cache
