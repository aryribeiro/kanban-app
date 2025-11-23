import streamlit as st
import json
import uuid
import random
import string
from datetime import datetime
import sqlite3
import base64
from io import BytesIO
import time
from PIL import Image
import os
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Kanban App!",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Customizado
st.markdown("""
<style>
    .stApp {
        background-color: #F5F5F5;
    }
    .kanban-column {
        background: white;
        border-radius: 8px;
        padding: 15px;
        margin: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        min-height: 500px;
    }
    .post-it {
        border-radius: 4px;
        padding: 12px;
        margin: 8px 0;
        box-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        word-wrap: break-word;
    }
    .column-title {
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 15px;
        text-align: center;
        color: #1f77b4;
    }
    .header-gradient {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    .task-meta {
        font-size: 11px;
        color: #666;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def generate_project_code():
    """Gera código alfanumérico único de 8 dígitos"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def format_datetime(dt_string):
    """Formata datetime para DD/MM HH:MM"""
    try:
        dt = datetime.fromisoformat(dt_string)
        return dt.strftime("%d/%m %H:%M")
    except:
        return dt_string

def get_admin_password():
    """Obtém senha de administrador do ambiente ou usa padrão"""
    return os.getenv('ADMIN_PASSWORD', 'admin123')

def image_to_base64(image):
    """Converte imagem PIL para base64"""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def base64_to_image(base64_string):
    """Converte base64 para imagem PIL"""
    try:
        image_data = base64.b64decode(base64_string.split(',')[1] if ',' in base64_string else base64_string)
        return Image.open(BytesIO(image_data))
    except:
        return None

# =============================================================================
# CLASSE DATABASE
# =============================================================================

class Database:
    """Gerenciamento de persistência com SQLite"""
    
    def __init__(self, db_path="kanban_app.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa tabelas do banco"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Tabela de projetos
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS projects (
                        code TEXT PRIMARY KEY,
                        title TEXT,
                        admin_name TEXT,
                        created_at TEXT,
                        logo_base64 TEXT
                    )
                """)
                
                # Tabela de tarefas
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id TEXT PRIMARY KEY,
                        project_code TEXT,
                        content TEXT,
                        color TEXT,
                        owner TEXT,
                        column_name TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (project_code) REFERENCES projects(code)
                    )
                """)
                
                conn.commit()
                conn.close()
                return True
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt) + random.uniform(0, 1))
                else:
                    st.error(f"Erro ao inicializar banco de dados: {e}")
                    return False
    
    def save_project(self, project_code, project_metadata):
        """Salva metadados do projeto"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO projects 
                (code, title, admin_name, created_at, logo_base64)
                VALUES (?, ?, ?, ?, ?)
            """, (
                project_code,
                project_metadata.get('title', ''),
                project_metadata.get('admin_name', ''),
                project_metadata.get('created_at', ''),
                project_metadata.get('logo_base64', '')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Erro ao salvar projeto: {e}")
            return False
    
    def load_project(self, project_code):
        """Carrega metadados do projeto"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM projects WHERE code = ?", (project_code,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'code': row[0],
                    'title': row[1],
                    'admin_name': row[2],
                    'created_at': row[3],
                    'logo_base64': row[4]
                }
            return None
        except Exception as e:
            st.error(f"Erro ao carregar projeto: {e}")
            return None
    
    def save_tasks(self, project_code, tasks):
        """Salva todas as tarefas do projeto"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Remove tarefas antigas do projeto
            cursor.execute("DELETE FROM tasks WHERE project_code = ?", (project_code,))
            
            # Insere tarefas atualizadas
            for task in tasks:
                cursor.execute("""
                    INSERT INTO tasks 
                    (id, project_code, content, color, owner, column_name, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task['id'],
                    project_code,
                    task['content'],
                    task['color'],
                    task['owner'],
                    task['column'],
                    task['created_at'],
                    task['updated_at']
                ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Erro ao salvar tarefas: {e}")
            return False
    
    def load_tasks(self, project_code):
        """Carrega todas as tarefas do projeto"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM tasks WHERE project_code = ?", (project_code,))
            rows = cursor.fetchall()
            conn.close()
            
            tasks = []
            for row in rows:
                tasks.append({
                    'id': row[0],
                    'content': row[2],
                    'color': row[3],
                    'owner': row[4],
                    'column': row[5],
                    'created_at': row[6],
                    'updated_at': row[7]
                })
            
            return tasks
        except Exception as e:
            st.error(f"Erro ao carregar tarefas: {e}")
            return []

# Instância global do banco
db = Database()

# =============================================================================
# INICIALIZAÇÃO DO SESSION STATE
# =============================================================================

def init_session_state():
    """Inicializa variáveis do session state"""
    if 'project_code' not in st.session_state:
        st.session_state.project_code = None
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'tasks' not in st.session_state:
        st.session_state.tasks = []
    if 'project_metadata' not in st.session_state:
        st.session_state.project_metadata = {}
    if 'show_admin_panel' not in st.session_state:
        st.session_state.show_admin_panel = False
    if 'editing_task_id' not in st.session_state:
        st.session_state.editing_task_id = None

init_session_state()

# =============================================================================
# FUNÇÕES DE PERSISTÊNCIA
# =============================================================================

def export_to_json():
    """Exporta projeto para JSON"""
    data = {
        'project_metadata': st.session_state.project_metadata,
        'columns': {
            'Backlog': [],
            'Análise': [],
            'Desenvolvimento': [],
            'Testes': [],
            'Pronto': []
        },
        'tasks': st.session_state.tasks
    }
    
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"kanban_project_{st.session_state.project_code}_{timestamp}.json"
    
    return json_str, filename

def import_from_json(uploaded_file):
    """Importa projeto de JSON"""
    try:
        data = json.load(uploaded_file)
        
        if 'project_metadata' in data and 'tasks' in data:
            st.session_state.project_metadata = data['project_metadata']
            st.session_state.tasks = data['tasks']
            st.session_state.project_code = data['project_metadata'].get('code')
            
            # Salva no banco
            db.save_project(st.session_state.project_code, st.session_state.project_metadata)
            db.save_tasks(st.session_state.project_code, st.session_state.tasks)
            
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao importar JSON: {e}")
        return False

def export_to_pdf():
    """Exporta quadro Kanban para PDF"""
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        from reportlab.lib import colors
        
        buffer = BytesIO()
        page_width, page_height = landscape(A4)
        c = canvas.Canvas(buffer, pagesize=landscape(A4))
        
        # Cabeçalho - Logo (se existir)
        y_position = page_height - 40
        
        if st.session_state.project_metadata.get('logo_base64'):
            try:
                logo = base64_to_image(st.session_state.project_metadata['logo_base64'])
                if logo:
                    logo_img = ImageReader(logo)
                    c.drawImage(logo_img, 30, page_height - 90, width=60, height=60, preserveAspectRatio=True, mask='auto')
            except:
                pass
        
        # Título do Projeto
        c.setFont("Helvetica-Bold", 18)
        c.drawString(110, page_height - 50, st.session_state.project_metadata.get('title', 'Kanban Board'))
        
        # Informações do projeto (código, data, admin)
        c.setFont("Helvetica", 10)
        c.drawString(110, page_height - 70, f"Código: {st.session_state.project_code}")
        c.drawString(250, page_height - 70, f"Criado: {format_datetime(st.session_state.project_metadata.get('created_at', ''))}")
        c.drawString(420, page_height - 70, f"Admin: {st.session_state.project_metadata.get('admin_name', '')}")
        
        # Linha separadora
        c.line(30, page_height - 100, page_width - 30, page_height - 100)
        
        # Colunas do Kanban
        columns = ['Backlog', 'Análise', 'Desenvolvimento', 'Testes', 'Pronto']
        num_columns = len(columns)
        col_width = (page_width - 60) / num_columns
        x_start = 30
        y_start = page_height - 130
        
        # Mapeamento de cores hex para RGB
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        
        for i, col in enumerate(columns):
            x = x_start + (i * col_width)
            
            # Título da coluna
            c.setFont("Helvetica-Bold", 14)
            c.setFillColorRGB(0.12, 0.47, 0.71)  # Azul #1f77b4
            c.drawString(x + 10, y_start, col)
            
            # Tarefas da coluna
            col_tasks = [t for t in st.session_state.tasks if t['column'] == col]
            y_task = y_start - 30
            
            for task in col_tasks:
                if y_task < 80:  # Evita sair da página
                    break
                
                # Converte cor hex para RGB
                try:
                    r, g, b = hex_to_rgb(task['color'])
                    c.setFillColorRGB(r, g, b)
                except:
                    c.setFillColorRGB(1, 1, 0.8)  # Amarelo claro como fallback
                
                # Desenha retângulo do post-it com a cor correta
                post_it_height = 80
                c.roundRect(x + 5, y_task - post_it_height, col_width - 15, post_it_height, 4, fill=1, stroke=1)
                
                # Sombra do post-it
                c.setFillColorRGB(0.5, 0.5, 0.5)
                c.setStrokeColorRGB(0.5, 0.5, 0.5)
                
                # Metadados da tarefa (owner, datas)
                c.setFillColorRGB(0.4, 0.4, 0.4)
                c.setFont("Helvetica", 7)
                
                meta_y = y_task - 15
                owner_text = f"👤 {task['owner']}"
                c.drawString(x + 10, meta_y, owner_text)
                
                created_text = f"📅 Criado: {format_datetime(task['created_at'])}"
                c.drawString(x + 10, meta_y - 10, created_text)
                
                edited_text = f"✏️ Editado: {format_datetime(task['updated_at'])}"
                c.drawString(x + 10, meta_y - 20, edited_text)
                
                # Conteúdo da tarefa (em negrito)
                c.setFillColorRGB(0.2, 0.2, 0.2)  # Cinza escuro #333
                c.setFont("Helvetica-Bold", 9)
                
                content = task['content']
                content_y = meta_y - 35
                
                # Quebra o texto em múltiplas linhas se necessário
                max_width = col_width - 25
                words = content.split()
                lines = []
                current_line = []
                
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    if c.stringWidth(test_line, "Helvetica-Bold", 9) < max_width:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                        current_line = [word]
                
                if current_line:
                    lines.append(' '.join(current_line))
                
                # Limita a 3 linhas
                lines = lines[:3]
                
                for line_idx, line in enumerate(lines):
                    if line_idx >= 3:
                        break
                    line_text = line if line_idx < 2 or len(lines) <= 3 else line[:30] + "..."
                    c.drawString(x + 10, content_y - (line_idx * 10), line_text)
                
                # Próximo post-it
                y_task -= (post_it_height + 15)
        
        # Footer
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawString(30, 30, "📋 Kanban App! | por Ary Ribeiro: aryribeiro@gmail.com")
        c.drawRightString(page_width - 30, 30, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        c.save()
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {e}")
        return None

# =============================================================================
# COMPONENTES UI
# =============================================================================

def render_header():
    """Renderiza cabeçalho do projeto"""
    if st.session_state.project_code:
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            # Logo
            if st.session_state.project_metadata.get('logo_base64'):
                try:
                    logo = base64_to_image(st.session_state.project_metadata['logo_base64'])
                    if logo:
                        st.image(logo, width=100)
                except:
                    pass
        
        with col2:
            # Título editável (apenas admin)
            if st.session_state.is_admin:
                new_title = st.text_input(
                    "Título do Projeto",
                    value=st.session_state.project_metadata.get('title', 'Meu Projeto Kanban'),
                    key="project_title"
                )
                if new_title != st.session_state.project_metadata.get('title'):
                    st.session_state.project_metadata['title'] = new_title
                    db.save_project(st.session_state.project_code, st.session_state.project_metadata)
            else:
                st.markdown(f"### {st.session_state.project_metadata.get('title', 'Meu Projeto Kanban')}")
            
            # Informações
            created = format_datetime(st.session_state.project_metadata.get('created_at', ''))
            st.caption(f"📅 Criado em: {created} | 🔑 Código: **{st.session_state.project_code}** | 👤 {st.session_state.current_user}")
        
        with col3:
            pass

def render_post_it(task, column):
    """Renderiza um post-it"""
    
    bg_color = task['color']
    content = task['content'].replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
    owner = task['owner'].replace('<', '&lt;').replace('>', '&gt;')
    
    # Container do post-it com todo o conteúdo dentro
    post_it_html = f"""
    <div class="post-it" style="background-color: {bg_color};">
        <div class="task-meta">
            👤 {owner}<br>
            📅 Criado: {format_datetime(task['created_at'])}<br>
            ✏️ Editado: {format_datetime(task['updated_at'])}
        </div>
        <div style="margin-top: 10px; font-weight: bold; font-size: 14px; color: #333; word-wrap: break-word;">
            {content}
        </div>
    </div>
    """
    
    st.markdown(post_it_html, unsafe_allow_html=True)
    
    # Botões abaixo do post-it
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Mover para outra coluna
        columns = ['Backlog', 'Análise', 'Desenvolvimento', 'Testes', 'Pronto']
        other_columns = [c for c in columns if c != column]
        move_to = st.selectbox(
            "Mover para",
            ['Mover ←→'] + other_columns,
            key=f"move_{task['id']}",
            label_visibility="collapsed"
        )
        
        if move_to != 'Mover ←→':
            task['column'] = move_to
            task['updated_at'] = datetime.now().isoformat()
            db.save_tasks(st.session_state.project_code, st.session_state.tasks)
            st.rerun()
    
    with col2:
        # Editar (apenas dono ou admin)
        can_edit = st.session_state.is_admin or task['owner'] == st.session_state.current_user
        if can_edit and st.button("✏️", key=f"edit_{task['id']}"):
            st.session_state.editing_task_id = task['id']
            st.rerun()
    
    with col3:
        # Deletar (apenas dono ou admin)
        can_delete = st.session_state.is_admin or task['owner'] == st.session_state.current_user
        if can_delete and st.button("🗑️", key=f"del_{task['id']}"):
            st.session_state.tasks = [t for t in st.session_state.tasks if t['id'] != task['id']]
            db.save_tasks(st.session_state.project_code, st.session_state.tasks)
            st.rerun()
    
    st.markdown("---")

def render_kanban_board():
    """Renderiza o quadro Kanban completo"""
    columns = ['Backlog', 'Análise', 'Desenvolvimento', 'Testes', 'Pronto']
    cols = st.columns(5)
    
    for idx, column in enumerate(columns):
        with cols[idx]:
            st.markdown(f'<div class="column-title">{column}</div>', unsafe_allow_html=True)
            
            # Botão Nova Tarefa
            if st.button(f"➕ Nova Tarefa", key=f"new_{column}"):
                st.session_state[f'creating_in_{column}'] = True
            
            # Formulário de criação
            if st.session_state.get(f'creating_in_{column}', False):
                with st.form(key=f"form_{column}"):
                    content = st.text_area("Conteúdo da tarefa", height=100)
                    color = st.selectbox("Cor", ['Amarelo', 'Rosa', 'Verde', 'Azul', 'Laranja'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("✅ Criar"):
                            color_map = {
                                'Amarelo': '#FFF59D',
                                'Rosa': '#F8BBD0',
                                'Verde': '#C5E1A5',
                                'Azul': '#BBDEFB',
                                'Laranja': '#FFCC80'
                            }
                            
                            new_task = {
                                'id': str(uuid.uuid4()),
                                'content': content,
                                'color': color_map[color],
                                'owner': st.session_state.current_user,
                                'column': column,
                                'created_at': datetime.now().isoformat(),
                                'updated_at': datetime.now().isoformat()
                            }
                            
                            st.session_state.tasks.append(new_task)
                            db.save_tasks(st.session_state.project_code, st.session_state.tasks)
                            # Recarrega do banco para garantir sincronização
                            st.session_state.tasks = db.load_tasks(st.session_state.project_code)
                            st.session_state[f'creating_in_{column}'] = False
                            st.rerun()
                    
                    with col2:
                        if st.form_submit_button("❌ Cancelar"):
                            st.session_state[f'creating_in_{column}'] = False
                            st.rerun()
            
            # Tarefas da coluna
            column_tasks = [t for t in st.session_state.tasks if t['column'] == column]
            
            for task in column_tasks:
                if st.session_state.editing_task_id == task['id']:
                    # Modo de edição
                    with st.form(key=f"edit_form_{task['id']}"):
                        new_content = st.text_area("Editar conteúdo", value=task['content'], height=100)
                        color_options = ['Amarelo', 'Rosa', 'Verde', 'Azul', 'Laranja']
                        color_map = {
                            '#FFF59D': 'Amarelo',
                            '#F8BBD0': 'Rosa',
                            '#C5E1A5': 'Verde',
                            '#BBDEFB': 'Azul',
                            '#FFCC80': 'Laranja'
                        }
                        current_color = color_map.get(task['color'], 'Amarelo')
                        new_color = st.selectbox("Cor", color_options, index=color_options.index(current_color))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Salvar"):
                                color_map_reverse = {
                                    'Amarelo': '#FFF59D',
                                    'Rosa': '#F8BBD0',
                                    'Verde': '#C5E1A5',
                                    'Azul': '#BBDEFB',
                                    'Laranja': '#FFCC80'
                                }
                                task['content'] = new_content
                                task['color'] = color_map_reverse[new_color]
                                task['updated_at'] = datetime.now().isoformat()
                                db.save_tasks(st.session_state.project_code, st.session_state.tasks)
                                st.session_state.editing_task_id = None
                                st.rerun()
                        
                        with col2:
                            if st.form_submit_button("❌ Cancelar"):
                                st.session_state.editing_task_id = None
                                st.rerun()
                else:
                    render_post_it(task, column)

# =============================================================================
# SIDEBAR
# =============================================================================

def render_sidebar():
    """Renderiza sidebar com opções"""
    with st.sidebar:
        st.markdown("## 📋 Kanban App!")
        
        if st.session_state.project_code:
            st.markdown("---")
            
            # Botões Administração e Atualizar lado a lado
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if st.button("🔐 Administração", key="admin_btn"):
                    st.session_state.show_admin_panel = not st.session_state.show_admin_panel
            
            with col2:
                if st.button("🔄", help="Atualizar tarefas", key="refresh_btn"):
                    st.session_state.tasks = db.load_tasks(st.session_state.project_code)
                    st.toast("✅ Atualizado!", icon="✅")
                    st.rerun()
            
            if st.session_state.show_admin_panel:
                password = st.text_input("Senha de Admin", type="password", key="admin_pwd")
                if st.button("Entrar como Admin"):
                    if password == get_admin_password():
                        st.session_state.is_admin = True
                        st.success("✅ Acesso de administrador concedido!")
                        st.session_state.show_admin_panel = False
                        st.rerun()
                    else:
                        st.error("❌ Senha incorreta!")
            
            st.markdown("---")
            st.markdown(f"**Usuário atual:** {st.session_state.current_user}")
            st.markdown(f"**Projeto:** {st.session_state.project_code}")
            
            if st.session_state.is_admin:
                st.success("🔓 Modo Administrador")
            
            st.markdown("---")
            
            # Opções de persistência
            st.markdown("### 💾 Persistência")
            
            # Salvar JSON
            if st.button("📥 Salvar em JSON"):
                json_str, filename = export_to_json()
                st.download_button(
                    label="⬇️ Download JSON",
                    data=json_str,
                    file_name=filename,
                    mime="application/json"
                )
            
            # Carregar JSON
            st.markdown("#### 📤 Carregar JSON")
            uploaded_json = st.file_uploader("Selecione o arquivo JSON", type=['json'], key="json_uploader")
            if uploaded_json is not None:
                # Verifica se é um novo arquivo diferente do último processado
                file_id = f"{uploaded_json.name}_{uploaded_json.size}_{uploaded_json.file_id if hasattr(uploaded_json, 'file_id') else ''}"
                
                # Se não existe last_json_id ou é um arquivo diferente, processa
                if 'last_json_id' not in st.session_state or st.session_state.get('last_json_id') != file_id:
                    if import_from_json(uploaded_json):
                        st.session_state.last_json_id = file_id
                        st.session_state.json_loaded = True
                        st.success("✅ Projeto carregado com sucesso!")
                    else:
                        st.error("❌ Erro ao carregar o arquivo JSON")
            
            # Botão para aplicar o JSON carregado
            if st.session_state.get('json_loaded', False):
                if st.button("🔄 Aplicar Mudanças", type="primary", key="apply_json_btn"):
                    st.session_state.json_loaded = False
                    st.rerun()
            
            # Exportar PDF
            if st.button("📄 Exportar PDF"):
                pdf_buffer = export_to_pdf()
                if pdf_buffer:
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=pdf_buffer,
                        file_name=f"kanban_{st.session_state.project_code}.pdf",
                        mime="application/pdf"
                    )
            
            # Limpar projeto (apenas admin)
            if st.session_state.is_admin:
                st.markdown("---")
                st.markdown("### ⚠️ Zona de Perigo")
                
                # Checkbox de confirmação
                confirmar = st.checkbox("⚠️ Confirmar que desejo limpar TODAS as tarefas", key="confirm_clear")
                
                # Botão só funciona se checkbox estiver marcado
                if st.button("🗑️ Limpar Projeto", type="secondary", disabled=not confirmar):
                    st.session_state.tasks = []
                    db.save_tasks(st.session_state.project_code, st.session_state.tasks)
                    # Reseta variáveis de controle do JSON para permitir novo upload
                    if 'last_json_id' in st.session_state:
                        del st.session_state.last_json_id
                    if 'json_loaded' in st.session_state:
                        del st.session_state.json_loaded
                    st.success("✅ Projeto limpo com sucesso!")
                    time.sleep(1)
                    st.rerun()
            
            # Upload de logo (admin)
            if st.session_state.is_admin:
                st.markdown("---")
                st.markdown("### 🖼️ Logo do Projeto")
                logo_file = st.file_uploader("Upload Logo", type=['png', 'jpg', 'jpeg'], key="logo_uploader")
                if logo_file:
                    # Verifica se é um novo arquivo
                    file_id = f"{logo_file.name}_{logo_file.size}"
                    if st.session_state.get('last_logo_id') != file_id:
                        image = Image.open(logo_file)
                        # Redimensiona para 200x200
                        image.thumbnail((200, 200))
                        st.session_state.project_metadata['logo_base64'] = f"data:image/png;base64,{image_to_base64(image)}"
                        db.save_project(st.session_state.project_code, st.session_state.project_metadata)
                        st.session_state.last_logo_id = file_id
                        st.success("✅ Logo atualizado com sucesso!")
                        time.sleep(0.5)

# =============================================================================
# FLUXO PRINCIPAL
# =============================================================================

def main():
    """Fluxo principal da aplicação"""
    
    # Se não há projeto ativo, mostra tela de autenticação
    if not st.session_state.project_code:
        st.markdown('<div class="header-gradient"><h1>📋 Kanban App!</h1><p>Gerencie seus projetos com eficiência</p></div>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🆕 Criar Novo Projeto", "🔑 Acessar Projeto Existente"])
        
        with tab1:
            st.markdown("### Criar um novo projeto")
            admin_name = st.text_input("Seu nome (Administrador)")
            project_title = st.text_input("Título do projeto", value="Meu Projeto Kanban")
            
            if st.button("✨ Criar Projeto", type="primary"):
                if admin_name:
                    # Gera código único
                    project_code = generate_project_code()
                    
                    # Configura metadados
                    st.session_state.project_code = project_code
                    st.session_state.is_admin = True
                    st.session_state.current_user = admin_name
                    st.session_state.project_metadata = {
                        'code': project_code,
                        'title': project_title,
                        'admin_name': admin_name,
                        'created_at': datetime.now().isoformat(),
                        'logo_base64': ''
                    }
                    st.session_state.tasks = []
                    
                    # Salva no banco
                    db.save_project(project_code, st.session_state.project_metadata)
                    
                    st.success(f"🎉 Projeto criado! Código: **{project_code}**")
                    st.info("💡 Compartilhe este código com sua equipe!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Por favor, informe seu nome.")
        
        with tab2:
            st.markdown("### Acessar projeto existente")
            access_code = st.text_input("Código do projeto (8 dígitos)")
            user_name = st.text_input("Seu nome")
            
            if st.button("🚀 Entrar no Projeto", type="primary"):
                if access_code and user_name:
                    # Tenta carregar projeto
                    project_data = db.load_project(access_code)
                    
                    if project_data:
                        st.session_state.project_code = access_code
                        st.session_state.current_user = user_name
                        st.session_state.is_admin = False
                        st.session_state.project_metadata = project_data
                        st.session_state.tasks = db.load_tasks(access_code)
                        
                        st.success(f"✅ Bem-vindo ao projeto: {project_data['title']}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Código de projeto inválido!")
                else:
                    st.error("Por favor, preencha todos os campos.")
    
    else:
        # Projeto ativo - mostra interface principal
        render_sidebar()
        render_header()
        
        st.markdown("---")
        
        # Renderiza o quadro Kanban
        render_kanban_board()
        
        # Footer
        st.markdown("---")
        st.caption("📋 Kanban App! | por Ary Ribeiro: aryribeiro@gmail.com")

if __name__ == "__main__":
    main()

st.markdown("""
<style>
    .main {
        background-color: #ffffff;
        color: #333333;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    /* Esconde completamente todos os elementos da barra padrão do Streamlit */
    header {display: none !important;}
    footer {display: none !important;}
    #MainMenu {display: none !important;}
    /* Remove qualquer espaço em branco adicional */
    div[data-testid="stAppViewBlockContainer"] {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    /* Remove quaisquer margens extras */
    .element-container {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
</style>
""", unsafe_allow_html=True)