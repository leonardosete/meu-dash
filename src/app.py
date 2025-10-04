import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from .analisar_alertas import analisar_arquivo_csv
from .analise_tendencia import gerar_relatorio_tendencia
from .get_date_range import get_date_range_from_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text # Adicionado para compatibilidade com SQLAlchemy 2.0
from flask_migrate import Migrate # type: ignore

app = Flask(__name__, template_folder='../templates')

# --- CONFIGURAÇÃO DE CAMINHOS E BANCO DE DADOS ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, '..', 'data', 'uploads')
REPORTS_FOLDER = os.path.join(BASE_DIR, '..', 'data', 'reports')
DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'meu_dash.db')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['REPORTS_FOLDER'] = REPORTS_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    original_filename = db.Column(db.String(255))
    report_path = db.Column(db.String(255))
    json_summary_path = db.Column(db.String(255))
    date_range = db.Column(db.String(100), nullable=True)
    max_date = db.Column(db.DateTime, nullable=True) # Novo campo para a data máxima do conteúdo

    def __repr__(self):
        return f'<Report {self.original_filename}>'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)

# --- ROTAS DE HEALTH CHECK PARA KUBERNETES ---

@app.route('/health')
def health_check():
    """Verifica se a aplicação está online e respondendo a requisições."""
    return jsonify({'status': 'ok'}), 200

# --- ROTAS PRINCIPAIS DA APLICAÇÃO ---

@app.route('/')
def index():
    """Renderiza a página inicial e passa links para as últimas análises, se existirem."""
    last_trend_analysis = None
    last_action_plan = None
    
    # Busca o último relatório registrado no banco de dados
    last_report = Report.query.order_by(Report.timestamp.desc()).first()

    if last_report:
        run_folder_path = os.path.dirname(last_report.report_path)
        run_folder_name = os.path.basename(run_folder_path)

        # 1. Verifica se existe o relatório de TENDÊNCIA
        trend_report_path = os.path.join(run_folder_path, 'resumo_tendencia.html')
        if os.path.exists(trend_report_path):
            last_trend_analysis = {
                'url': url_for('serve_report', run_folder=run_folder_name, filename='resumo_tendencia.html'),
                'date': last_report.timestamp.strftime('%d/%m/%Y às %H:%M')
            }

        # 2. Verifica se existe o PLANO DE AÇÃO (editor_atuacao.html)
        action_plan_path = os.path.join(run_folder_path, 'editor_atuacao.html')
        if os.path.exists(action_plan_path):
            last_action_plan = {
                'url': url_for('serve_report', run_folder=run_folder_name, filename='editor_atuacao.html'),
                'date': last_report.timestamp.strftime('%d/%m/%Y às %H:%M')
            }
            
    return render_template(
        'upload.html', 
        last_trend_analysis=last_trend_analysis,
        last_action_plan=last_action_plan
    )

@app.route('/upload', methods=['POST'])
def upload_file():
    """Orquestra o processo de upload, análise e comparação automática de tendências."""
    if 'file_atual' not in request.files:
        return render_template('upload.html', error="Nenhum arquivo enviado.")
        
    file_atual = request.files['file_atual']

    if file_atual.filename == '':
        return render_template('upload.html', error="Nenhum arquivo selecionado.")

    try:
        # --- ETAPA 1: Salva o arquivo e extrai o intervalo de datas ---
        filename_atual = secure_filename(file_atual.filename)
        filepath_atual = os.path.join(app.config['UPLOAD_FOLDER'], f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename_atual}")
        file_atual.save(filepath_atual)
        
        date_info = get_date_range_from_file(filepath_atual)
        date_range_atual, max_date_atual = (date_info[0], date_info[1]) if date_info else (None, None)

        run_folder_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir = os.path.join(app.config['REPORTS_FOLDER'], run_folder_name)
        os.makedirs(output_dir, exist_ok=True)

        # --- ETAPA 2: Busca o relatório anterior no histórico (LÓGICA ATUALIZADA) ---
        last_report = None
        if max_date_atual:
            # Busca o relatório cuja data máxima é a maior, mas ainda anterior à data máxima do arquivo atual
            last_report = Report.query.filter(Report.max_date < max_date_atual).order_by(Report.max_date.desc()).first()
        
        if not last_report:
            # Fallback para a lógica antiga se não encontrar um relatório por data ou se o arquivo atual não tiver data
            last_report = Report.query.order_by(Report.timestamp.desc()).first()

        trend_report_path_relative = None

        # --- ETAPA 3: Gera o relatório de tendência (se houver um anterior) ---
        if last_report and last_report.json_summary_path and os.path.exists(last_report.json_summary_path):
            print(f"📈 Relatório anterior encontrado ({last_report.original_filename}). Iniciando análise de tendência.")
            
            temp_analysis_results = analisar_arquivo_csv(filepath_atual, output_dir, light_analysis=True)
            json_path_atual = temp_analysis_results['json_path']
            
            output_trend_path = os.path.join(output_dir, 'resumo_tendencia.html')
            
            gerar_relatorio_tendencia(
                json_anterior=last_report.json_summary_path,
                json_atual=json_path_atual,
                csv_anterior_name=last_report.original_filename,
                csv_atual_name=filename_atual,
                output_path=output_trend_path,
                date_range_anterior=last_report.date_range,
                date_range_atual=date_range_atual
            )
            trend_report_path_relative = os.path.basename(output_trend_path)
            print(f"✅ Relatório de tendência gerado.")
        else:
            print("⚠️ Nenhum relatório anterior compatível encontrado para análise de tendência.")

        # --- ETAPA 4: Executa a análise completa no arquivo atual ---
        final_analysis_results = analisar_arquivo_csv(
            input_file=filepath_atual, 
            output_dir=output_dir, 
            light_analysis=False,
            trend_report_path=trend_report_path_relative
        )
        report_path_final = final_analysis_results['html_path']
        json_path_final = final_analysis_results['json_path']

        # --- ETAPA 5: Salva o novo relatório no banco e redireciona ---
        new_report = Report(
            original_filename=filename_atual,
            report_path=report_path_final,
            json_summary_path=json_path_final,
            date_range=date_range_atual,
            max_date=max_date_atual
        )
        db.session.add(new_report)
        db.session.commit()
        print(f"💾 Novo relatório '{filename_atual}' salvo no banco de dados.")

        run_folder = os.path.basename(os.path.dirname(report_path_final))
        report_filename = os.path.basename(report_path_final)
        return redirect(url_for('serve_report', run_folder=run_folder, filename=report_filename))

    except Exception as e:
        print(f"❌ Erro fatal no processo de upload: {e}")
        import traceback
        traceback.print_exc()
        return render_template('upload.html', error="Ocorreu um erro ao processar o arquivo. Verifique se o formato do CSV está correto e tente novamente.")

# --- ROTAS PARA SERVIR ARQUIVOS ESTÁTICOS ---

@app.route('/reports/<run_folder>/planos_de_acao/<filename>')
def serve_planos(run_folder, filename):
    return send_from_directory(os.path.join(app.config['REPORTS_FOLDER'], run_folder, 'planos_de_acao'), filename)

@app.route('/reports/<run_folder>/detalhes/<filename>')
def serve_detalhes(run_folder, filename):
    return send_from_directory(os.path.join(app.config['REPORTS_FOLDER'], run_folder, 'detalhes'), filename)

@app.route('/reports/<run_folder>/<path:filename>')
def serve_report(run_folder, filename):
    return send_from_directory(os.path.join(app.config['REPORTS_FOLDER'], run_folder), filename)

# --- ROTA ADICIONADA PARA DOCUMENTAÇÃO ---
@app.route('/docs/<path:filename>')
def serve_docs(filename):
    """Serve os arquivos de documentação estática."""
    # app.root_path aponta para /app/src, então usamos '..' para subir um nível
    docs_dir = os.path.abspath(os.path.join(app.root_path, '..', 'docs'))
    return send_from_directory(docs_dir, filename)

@app.route('/relatorios')
def relatorios():
    """Exibe a página de histórico de relatórios."""
    reports = Report.query.order_by(Report.timestamp.desc()).all()
    report_data = []
    for report in reports:
        report_data.append({
            'timestamp': report.timestamp,
            'original_filename': report.original_filename,
            'url': url_for('serve_report', 
                        run_folder=os.path.basename(os.path.dirname(report.report_path)), 
                        filename=os.path.basename(report.report_path))
        })
    return render_template('relatorios.html', reports=report_data)

# --- INICIALIZAÇÃO DA APLICAÇÃO ---

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
