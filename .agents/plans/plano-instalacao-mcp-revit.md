# Plano de Integração e Instalação: Revit MCP Server para Google Antigravity

Este plano estabelece o roteiro técnico, didático e operacional para conectar o Autodesk Revit
ao assistente de inteligência artificial Google Antigravity utilizando o Model Context Protocol (MCP).

---

## 1. Visão Geral e Arquitetura da Solução

O **Model Context Protocol (MCP)** é um padrão aberto que permite a modelos de inteligência
artificial interagir diretamente com ferramentas, bancos de dados e softwares externos de forma
padronizada e segura.

Integrar o Revit ao Antigravity via MCP transforma o agente em um assistente de modelagem e
coordenação BIM capaz de inspecionar elementos, extrair quantitativos, criar geometrias paramétricas,
detectar interferências (_clash detection_) e exportar documentações diretamente no modelo ativo.

### Fluxo de Comunicação

```mermaid
flowchart LR
    direction LR
    AI["Google Antigravity - AI Assistant"]
    MCP["Revit MCP Server - FastMCP uv"]
    PyRevit["pyRevit Routes Server - HTTP localhost 48884"]
    Revit["Autodesk Revit API - Modelo RVT Ativo"]

    AI <-->|"stdio (JSON-RPC)"| MCP
    MCP <-->|"HTTP REST"| PyRevit
    PyRevit <-->|"IronPython / .NET"| Revit
```

1. **Antigravity (Cliente MCP)**: Inicia o processo do servidor via `stdio` com base na
   configuração declarada em `.agents/mcp_config.json`.
2. **Revit MCP Server (Servidor Python)**: Interpreta as requisições de ferramentas da IA e envia
   chamadas HTTP formatadas para a porta local `48884`.
3. **pyRevit Routes (Ponte Interna do Revit)**: Roda como processo em segundo plano dentro do próprio
   Revit, executando as instruções na thread principal da API do software.
4. **Autodesk Revit**: Aplica as alterações e consultas diretamente sobre o documento `.rvt` aberto.

---

## 2. Análise Comparativa dos Servidores MCP Disponíveis

| Critério                       | Opção 1: `demolinator/revit-mcp-server` (Recomendada)       | Opção 2: `ludattilo/revit-mcp-server`              |
| :----------------------------- | :---------------------------------------------------------- | :------------------------------------------------- |
| **Mecanismo de Ponte**         | pyRevit Routes (Servidor HTTP embutido)                     | Plugin C# .NET compilado (Socket TCP :8080)        |
| **Facilidade de Instalação**   | Alta: utiliza o pyRevit que a maioria dos arquitetos já usa | Média/Baixa: requer compilar ou carregar DLLs .NET |
| **Versões Suportadas**         | Revit 2024, 2025, 2026, 2027                                | Revit 2023, 2024, 2025, 2026, 2027                 |
| **Quantidade de Ferramentas**  | 48 ferramentas didáticas e funcionais                       | 124 a 138 ferramentas                              |
| **Unidades de Medida**         | Milímetros (`mm`) nativos com conversão automática          | Pés internos ou milímetros dependendo do comando   |
| **Integração com Antigravity** | Nativa via `uv run` em `.agents/mcp_config.json`            | Requer servidor Node.js/Python intermediário       |

**Decisão**: O servidor `demolinator/revit-mcp-server` é a solução mais recomendada e sustentável
para o ecossistema do Knowledge Lab, pois utiliza o pyRevit (ferramenta padrão na prática
arquitetônica) e o gerenciador de pacotes ultrarrápido `uv`.

---

## 3. Pré-requisitos de Sistema

- **Sistema Operacional**: Windows 10 ou Windows 11 (64-bit).
- **Software BIM**: Autodesk Revit 2024, 2025, 2026 ou 2027 instalado.
- **pyRevit**: Versão 4.8.16 ou superior instalada (Recomendado v7.0 para suporte pleno ao Revit 2026).
- **Git**: Git para Windows instalado para controle de versão e clonagem.
- **Python Package Manager**: `uv` instalado no ambiente do usuário.
- **Google Antigravity**: CLI `agy` operacional e espaço de trabalho inicializado.

### Resumo de Diagnóstico do Ambiente Atual

| Componente                 | Requisito       | Status Local           | Caminho / Versão                                               |
| :------------------------- | :-------------- | :--------------------- | :------------------------------------------------------------- |
| **Autodesk Revit**         | 2024-2027       | Instalado              | Revit 2026 (`C:\Program Files\Autodesk\Revit 2026\`)           |
| **Git**                    | 2.x+            | Instalado              | Git v2.55 (`C:\Program Files\Git\cmd\git.exe`)                 |
| **uv Package Manager**     | 0.10+           | Instalado              | uv v0.12.23 (`C:\Users\nicol\.local\bin\uv.exe`)               |
| **pyRevit**                | 4.8.16+         | Instalado              | pyRevit v7.0 (`C:\Users\nicol\AppData\Roaming\pyRevit-Master`) |
| **Servidor MCP Local**     | Demolinator     | Clonado e Sincronizado | `C:\tools\revit-mcp-server` (Ambiente virtual pronto)          |
| **Extensão pyRevit**       | Link simbólico  | Configurado            | `C:\pyRevitExtensions\revit-mcp.extension`                     |
| **Servidor Routes**        | Porta 48884     | Ativo no pyRevit       | Porta 48884 habilitada via CLI                                 |
| **Antigravity MCP Config** | Declaração JSON | Concluído              | `.agents/mcp_config.json` atualizado com `revit-mcp`           |

---

## 4. Roteiro Passo a Passo de Instalação e Configuração

### Passo 1: Instalação do Gerenciador `uv` (caso não esteja instalado)

Abra o terminal do PowerShell no Windows e execute o comando oficial de instalação:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Feche e reabra o terminal para confirmar a instalação:

```powershell
uv --version
```

---

### Passo 2: Clonagem do Repositório do Servidor MCP

Escolha uma pasta no seu computador para hospedar os utilitários de ferramentas (por exemplo,
`C:\tools\revit-mcp-server` ou dentro do seu diretório de ferramentas de desenvolvimento):

```powershell
New-Item -ItemType Directory -Force -Path "C:\tools"
cd C:\tools
git clone https://github.com/Demolinator/revit-mcp-server.git
cd revit-mcp-server
uv sync
```

O comando `uv sync` criará o ambiente virtual isolado e baixará automaticamente as dependências
necessárias (`fastmcp`, `httpx`, `pydantic`).

---

### Passo 3: Configuração da Extensão no pyRevit

O servidor necessita que a extensão `revit_mcp` seja carregada dentro do ambiente do Revit pelo
pyRevit.

1. Crie uma pasta para suas extensões personalizadas do pyRevit, caso ainda não tenha (ex:
   `C:\pyRevitExtensions`).
2. No PowerShell, crie um vínculo simbólico (_Junction_) apontando para a pasta clonada:

```powershell
New-Item -ItemType Junction -Path "C:\pyRevitExtensions\revit-mcp.extension" -Target "C:\tools\revit-mcp-server"
```

3. Configure o pyRevit para carregar a extensão e habilitar o servidor Routes. Isso pode ser feito via linha de comando (CLI) ou pela interface gráfica:

**Opção A — Via terminal pyRevit CLI (Rápido e automatizado)**:

```powershell
pyrevit extensions paths add "C:\pyRevitExtensions"
pyrevit configs routes enable
pyrevit configs routes port 48884
```

**Opção B — Pela interface gráfica do Revit**:

1. Abra o Autodesk Revit.
2. Na faixa de opções superior, clique na aba **pyRevit** e no ícone de engrenagem **Settings**.
3. Na seção **Custom Extension Directories**, adicione `C:\pyRevitExtensions`.
4. Na seção **Routes** (à esquerda), marque a opção **Enable Routes Server** (porta padrão `48884`).
5. Clique em **Save Settings and Reload**.

---

### Passo 4: Verificação da Comunicação Local com o Revit

1. Mantenha o Autodesk Revit aberto com qualquer projeto ou template iniciado.
2. Abra seu navegador de internet e acesse:
   [http://localhost:48884/revit_mcp/status/](http://localhost:48884/revit_mcp/status/)
3. A resposta exibida na página deve ser um JSON contendo:
   ```json
   {
     "status": "active",
     "project_title": "Projeto1 - Planta de piso"
   }
   ```
   Caso retorne código 404, verifique se a pasta foi nomeada com o sufixo `.extension`. Se a página
   não carregar, confirme se a opção **Routes Server** está ativada nas configurações do pyRevit.

---

### Passo 5: Configuração no Google Antigravity (`mcp_config.json`)

Para que o Antigravity reconheça e inicie o servidor MCP do Revit automaticamente, adicione a
definição do servidor no arquivo [`.agents/mcp_config.json`](./../mcp_config.json):

```json
{
  "mcpServers": {
    "revit-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "C:\\tools\\revit-mcp-server", "main.py"],
      "env": {
        "REVIT_HOST": "localhost",
        "REVIT_PORT": "48884"
      }
    }
  }
}
```

> [!NOTE]
> **Configuração Alternativa via HTTP**
> Caso prefira rodar o servidor em um terminal separado (para depuração visual em tempo real), execute
> `uv run main.py --http` no diretório do servidor e configure a URL `http://127.0.0.1:8000/mcp` no
> Antigravity.

---

## 5. Catálogo Didático de Ferramentas Disponíveis (48 Ferramentas)

Após a conexão, o agente Antigravity passa a ter acesso a 48 capacidades especializadas divididas em
seis disciplinas:

### A. Criação de Elementos (15 Ferramentas)

- `create_level`: Criação de novos níveis e cotas verticais de pavimentos.
- `create_grid`: Traçado de eixos estruturais e de referência.
- `create_line_based_element`: Modelagem de paredes básicas, vigas estruturais e elementos lineares.
- `create_surface_based_element`: Modelagem de lajes de piso, forros e coberturas.
- `place_family`: Inserção pontual de instâncias de famílias (portas, janelas, mobiliário, pilares).
- `create_room` & `create_room_separation`: Criação de ambientes e limites de separação de salas.
- `create_view`: Geração automática de plantas de piso, cortes, elevações e vistas 3D isométricas.
- `create_sheet`: Criação de pranchas de desenho com formatos e carimbos padronizados.
- `create_schedule`: Geração de tabelas de quantitativos com campos e filtros configurados.
- `create_duct`, `create_pipe`, `create_mep_system`: Lançamento de redes e sistemas MEP.

### B. Consulta e Inspeção do Modelo (12 Ferramentas)

- `get_revit_status`: Verifica se a conexão com o Revit está ativa e saudável.
- `get_revit_model_info`: Extrai metadados do projeto (nome do cliente, número, localização).
- `list_levels`: Lista todos os níveis existentes com suas respectivas cotas em milímetros.
- `list_families` & `list_family_categories`: Cataloga todas as famílias e tipos disponíveis.
- `get_current_view_elements`: Identifica todos os elementos visíveis na vista ativa no momento.
- `get_element_properties`: Lê todos os parâmetros de tipo e de instância de um elemento selecionado.
- `get_revit_view`: Captura e renderiza uma vista gráfica diretamente como imagem para o agente.

### C. Modificação e Parametrização (9 Ferramentas)

- `modify_element` & `set_parameter`: Ajusta valores de parâmetros em qualquer elemento do modelo.
- `color_splash`: Aplica sobreposição de cores nos elementos de acordo com valores de parâmetros.
- `clear_colors`: Restaura as cores e estilos gráficos originais da vista.
- `tag_walls` & `tag_elements`: Adiciona anotações e identificadores automáticos sobre elementos.
- `transform_elements`: Move, rotaciona, copia ou espelha elementos selecionados.
- `set_active_view`: Alterna a vista aberta na interface do Revit.

### D. Análise e Coordenação BIM (5 Ferramentas)

- `check_clashes`: Executa teste de interferência (_clash detection_) entre disciplinas (ex: estrutura versus tubulações).
- `get_material_quantities`: Extrai tabelas de levantamento volumétrico e áreas de materiais.
- `export_room_data`: Calcula áreas úteis, perímetros e volumes de todos os compartimentos.
- `ai_element_filter`: Filtra elementos combinando categorias e critérios lógicos.
- `analyze_model_statistics`: Gera diagnóstico estatístico de saúde e densidade de elementos no modelo.

### E. Documentação, Interoperabilidade e Persistência (7 Ferramentas)

- `create_dimensions`: Cria cotas lineares entre referências do projeto.
- `export_document`: Exporta vistas e pranchas selecionadas para arquivos PDF ou imagem.
- `export_ifc`: Gera exportação no padrão aberto IFC (IFC2x3 ou IFC4).
- `link_file`: Vincula ou importa arquivos DWG, DXF, DGN, SAT, SKP, 3DM ou RVT.
- `load_family`: Carrega arquivos `.rfa` externos localizados no disco rígido.
- `save_document`: Salva o modelo ativo ou executa _Save As_ para um novo caminho persistente.
- `execute_revit_code`: Executa scripts IronPython diretamente na sessão interna do Revit para casos de automação avançada.

---

## 6. Boas Práticas e Recomendações Operacionais (_Gotchas_)

1. **Unidades de Medida**:
   - Todas as ferramentas do `revit-mcp-server` foram projetadas para aceitar **milímetros (`mm`)**. O
     servidor realiza a conversão matemática automática para as unidades internas de pés (_feet_) do
     Revit.
2. **Requisito de Documento Ativo**:
   - A maioria das ferramentas exige que haja um projeto aberto no Revit. Se o Revit estiver na tela
     inicial sem nenhum arquivo aberto, as consultas retornarão erro de documento inativo.
3. **Persistência de Transações**:
   - O Revit trabalha com transações atômicas da API. Para evitar perda de dados em caso de falha de
     energia ou encerramento inesperado, sempre solicite ao agente a execução da ferramenta
     `save_document` após rodar alterações significativas de modelagem.
4. **Modelos com Compartilhamento de Trabalho (_Worksharing_)**:
   - Em modelos colaborativos centrais, certifique-se de que os _worksets_ necessários estão
     desbloqueados para edição antes de instruir o agente a criar elementos em lote.
