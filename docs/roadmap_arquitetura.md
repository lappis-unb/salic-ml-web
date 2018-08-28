# Roadmap de Arquitetura
-- --
## Tópicos principais
### Curto/Médio prazo
- Realizar ajustes na aplicação web monolítica para iniciar-se a homologação
  - Links para o SALIC
  - Loading na página inicial
  - ...
- Análise dos dados de feedback
  - Automatização do processo de data capturing para ser disponibilizado numa planilha
- Modularizar a aplicação web monolítica em:
  - Backend Django REST
  - Frontend VueJS
- Ajustar fonte de dados para o Machine Learning
  - Transferir os CSVs do pacote Python para a aplicação web
  - Utilizar o banco de homologação do SALIC como fonte de dados.
  - Utilizar o SALIC-API como fonte de dados
  - Definir saídas do módulo de ML
- DevOPS
  - Finalizar ajustes do deploy na VM do MinC
  - Escrever testes
  - Configurar pipelines na infra do LAPPIS (backup plan)

### Longo prazo
- Arquitetura de Microservices
  - Um serviço para cada indicador
  - Cache de dados?
  - Paralelizar processamento interno
  - ...
- Exibição dos dados
  - Plugin?
  - Integração no SALIC?
  - Página externa?
  - ...
-- --
## Issues

### Curto/Médio prazo

1. BugFix
  1. __Adicionar, na aplicação web, links para o SALIC.__
  2. __Inserir loading na index page.__
2. Modularização da Arquitetura
  1. Backend Django REST
    1. __Replicar rotas da aplicação monolítica no formato de API__
    2. __Modularizar funcionalidades em mais arquivos__
    3. __Redefinir padrões de formato dos objetos enviados para o frontend__
    4. __Criar testes unitários__
  2. Frontend VueJS
    1. ...
    2. ...
    3. ...
3. Padronização de dados fornecidos pelo salic-ml-web
  1. __Defnir formatos de objetos para o salic-ml-web__
  2. __Definir formatos para as métricas já implementadas__
  3. __Reorganizar o data handling dentro do backend__
4. Data handling para o ML
  1. __Definir dados a serem passados como parâmetro para o módulo salic-ml-dev__
  2. __Definir modelos de objetos a serem utilizados pelo salic-ml-dev__
  3. __Modificar pasta de armazenamento do CSV para ser consumido pelo backend apenas__
  4. __Puxar dados de treinamento do banco de homologação__
  5. __Puxar dados de treinamento do SALIC-API__
5. DevOPS
  1. __Revisar processo de deploy na VM do MinC__
  2. __Corrigir problemas com o Pickle__
  3. __Subir instância na infra do LAPPIS__

### Longo prazo

1. Microservices
  1. __Remodelar arquitetura aplicando abordagem de microservices__
  2. __Pesquisar implementações já existentes no contexto de machine learning__
2. Exibição dos dados
  1. ...
