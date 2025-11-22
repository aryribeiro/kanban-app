# 📋 Kanban App!

Web app de gerenciamento de projetos / Kanban desenvolvido em Python e Streamlit.

## 🚀 Recursos Principais

### ✨ Funcionalidades
- **Sistema de Autenticação** com códigos únicos de 8 dígitos
- **Quadro Kanban** com 5 colunas: Backlog, Análise, Desenvolvimento, Testes e Pronto
- **Post-its personalizáveis** com 5 cores diferentes
- **Drag-and-drop** entre colunas via selectbox
- **Controle de permissões** (Administrador vs Usuários Comuns)
- **Persistência local** com SQLite
- **Export/Import** em JSON
- **Exportação para PDF** do quadro completo
- **Upload de logo** personalizado

### 🎨 Design
- Interface clean e moderna
- Post-its com visual de nota adesiva
- Cores: Amarelo, Rosa, Verde, Azul e Laranja
- Layout responsivo e intuitivo

### 🔒 Segurança e Resiliência
- Banco de dados SQLite para persistência
- Retry com backoff exponencial
- Tratamento robusto de erros
- Operações idempotentes
- Cache em memória com `st.session_state`

## 📦 Instalação

### 1. Clone ou baixe os arquivos
```bash
# Estrutura de arquivos necessária:
kanban-app/
├── app.py
├── requirements.txt
└── README.md
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure a senha de administrador (opcional)
```bash
Edite ou crie o arquivo .env no seu VS Code e altere a senha
# ADMIN_PASSWORD=sua_senha_aqui
```

### 4. Execute a aplicação
```bash
streamlit run app.py
```

A aplicação será aberta automaticamente no navegador em `http://localhost:8501`

## 📖 Como Usar

### 👨‍💼 Para Administradores

#### 1. Criar um Novo Projeto
1. Na tela inicial, vá para a aba "🆕 Criar Novo Projeto"
2. Informe seu nome como administrador
3. Defina um título para o projeto
4. Clique em "✨ Criar Projeto"
5. **Anote o código de 8 dígitos gerado** - você precisará compartilhá-lo com a equipe

#### 2. Funcionalidades Exclusivas do Admin
- **Editar título do projeto** diretamente no cabeçalho
- **Upload de logo** (clique no botão "⚙️ Upload Logo")
- **Editar qualquer post-it** (não apenas os próprios)
- **Deletar qualquer post-it**
- **Limpar todo o projeto** (via sidebar > Zona de Perigo)
- **Acesso via senha**: Use "🔐 Administração" na sidebar

#### 3. Gerenciar Senha de Admin
- Senha padrão: `admin123`
- Para alterar: modifique o arquivo `.env` ou configure a variável de ambiente `ADMIN_PASSWORD`

### 👥 Para Usuários Comuns

#### 1. Acessar um Projeto
1. Na tela inicial, vá para a aba "🔑 Acessar Projeto Existente"
2. Insira o código de 8 dígitos fornecido pelo administrador
3. Informe seu nome
4. Clique em "🚀 Entrar no Projeto"

#### 2. Criar Tarefas
1. Em qualquer coluna, clique em "➕ Nova Tarefa"
2. Digite o conteúdo da tarefa
3. Escolha uma cor (Amarelo, Rosa, Verde, Azul ou Laranja)
4. Clique em "✅ Criar"

#### 3. Gerenciar Tarefas
- **Mover entre colunas**: Use o dropdown "Mover para" em cada post-it
- **Editar**: Clique no botão "✏️" (apenas suas próprias tarefas)
- **Deletar**: Clique no botão "🗑️" (apenas suas próprias tarefas)

### 💾 Persistência e Backup

#### Salvar Projeto em JSON
1. Na sidebar, clique em "📥 Salvar em JSON"
2. Clique em "⬇️ Download JSON"
3. O arquivo será salvo com timestamp: `kanban_project_[CÓDIGO]_[DATA].json`

#### Carregar Projeto de JSON
1. Na sidebar, use "📤 Carregar JSON"
2. Selecione o arquivo JSON previamente salvo
3. O projeto será restaurado com todas as tarefas

#### Exportar para PDF
1. Na sidebar, clique em "📄 Exportar PDF"
2. Clique em "⬇️ Download PDF"
3. Um PDF visual do quadro será gerado com todas as tarefas

## 🗂️ Estrutura de Dados

### Post-it (Tarefa)
Cada post-it contém:
- **ID único** (UUID)
- **Conteúdo** (texto da tarefa)
- **Cor** (hex color)
- **Proprietário** (nome de quem criou)
- **Coluna atual**
- **Data de criação**
- **Data da última edição**

### Banco de Dados SQLite
Arquivo: `kanban_app.db`

**Tabela `projects`:**
- code (PRIMARY KEY)
- title
- admin_name
- created_at
- logo_base64

**Tabela `tasks`:**
- id (PRIMARY KEY)
- project_code (FOREIGN KEY)
- content
- color
- owner
- column_name
- created_at
- updated_at

## 🎯 Dicas de Uso

### Para Equipes Distribuídas
1. **Admin cria o projeto** e compartilha o código via email/chat
2. **Todos acessam com o mesmo código** - cada um com seu nome
3. **Use JSON para backup regular** - salve semanalmente
4. **Export PDF para reuniões** - compartilhe snapshots do quadro

### Boas Práticas
- ✅ Use cores consistentes para tipos de tarefa
- ✅ Mantenha descrições claras e concisas nos post-its
- ✅ Faça backups regulares em JSON
- ✅ Mova tarefas conforme o progresso real
- ✅ Use a coluna "Backlog" para novas ideias

### Organização de Tarefas
- **Amarelo**: Tarefas normais
- **Rosa**: Urgente/Importante
- **Verde**: Concluído/Validado
- **Azul**: Pesquisa/Análise
- **Laranja**: Bloqueios/Impedimentos

## 🔧 Personalização

### Alterar Colunas
Edite o arquivo `app.py`, procure por:
```python
columns = ['Backlog', 'Análise', 'Desenvolvimento', 'Testes', 'Pronto']
```

### Adicionar Novas Cores
Em `app.py`, localize:
```python
color_map = {
    'Amarelo': '#FFF59D',
    'Rosa': '#F8BBD0',
    'Verde': '#C5E1A5',
    'Azul': '#BBDEFB',
    'Laranja': '#FFCC80'
}
```

### Alterar Layout
Modifique a seção CSS no início do `app.py`

## 🐛 Solução de Problemas

### Erro ao salvar no banco de dados
- Verifique permissões de escrita na pasta
- O arquivo `kanban_app.db` será criado automaticamente

### Projeto não carrega
- Verifique se o código está correto (8 dígitos)
- Confira se o banco de dados não foi corrompido
- Use o backup JSON para restaurar

### Post-its não aparecem
- Recarregue a página (F5)
- Verifique se as tarefas estão na coluna correta
- Use "Limpar Projeto" (admin) e recomece se necessário

## 📝 Requisitos do Sistema

- Python 3.8+
- Streamlit 1.28.0+
- Conexão com internet (para Streamlit)
- Navegador moderno (Chrome, Firefox, Safari, Edge)

## 🤝 Contribuindo

Este é um projeto de código aberto. Sinta-se livre para:
- Reportar bugs
- Sugerir melhorias
- Fazer fork e customizar
- Compartilhar com sua equipe

## 📄 Licença

Livre para uso pessoal e comercial.

## 🎉 Contato

por **Ary Ribeiro**: aryribeiro@gmail.com