import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from .analisar_alertas import analisar_arquivo_csv
from .analise_tendencia import gerar_relatorio_tendencia
from .get_date_range import get_date_range_from_file
from flask_sqlalchemy import SQLAlchemy
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
    date_range = db.Column(db.String(100), nullable=True) # Novo campo para o intervalo de datas

    def __repr__(self):
        return f'<Report {self.original_filename}>'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)

# --- ROTAS DE HEALTH CHECK PARA KUBERNETES ---

@app.route('/health')
def health_check():
    """Verifica a saúde da aplicação, incluindo banco de dados e permissões de arquivo."""
    try:
        # 1. Verifica a conexão com o banco de dados
        db.session.execute('SELECT 1')

        # 2. Verifica se os diretórios essenciais existem e têm permissão de escrita
        if not os.path.exists(app.config['UPLOAD_FOLDER']) or not os.access(app.config['UPLOAD_FOLDER'], os.W_OK):
            raise Exception(f"Diretório de upload não acessível: {app.config['UPLOAD_FOLDER']}")
        
        if not os.path.exists(app.config['REPORTS_FOLDER']) or not os.access(app.config['REPORTS_FOLDER'], os.W_OK):
            raise Exception(f"Diretório de relatórios não acessível: {app.config['REPORTS_FOLDER']}")

        return jsonify({'status': 'ok'}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'details': str(e)}), 503

# --- ROTAS PRINCIPAIS DA APLICAÇÃO ---

@app.route('/')
def index():
    """Renderiza a página inicial de upload e passa a última análise de tendência, se existir."""
    last_trend_analysis = None
    # Busca o último relatório registrado no banco de dados
    last_report = Report.query.order_by(Report.timestamp.desc()).first()

    if last_report:
        run_folder_path = os.path.dirname(last_report.report_path)
        # O relatório de tendência sempre tem o mesmo nome
        trend_report_path = os.path.join(run_folder_path, 'resumo_tendencia.html')

        # Verifica se o arquivo de tendência realmente existe no disco
        if os.path.exists(trend_report_path):
            run_folder_name = os.path.basename(run_folder_path)
            last_trend_analysis = {
                'url': url_for('serve_report', run_folder=run_folder_name, filename='resumo_tendencia.html'),
                'date': last_report.timestamp.strftime('%d/%m/%Y às %H:%M')
            }
            
    return render_template('upload.html', last_trend_analysis=last_trend_analysis)

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
        date_range_atual = get_date_range_from_file(filepath_atual)

        run_folder_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir = os.path.join(app.config['REPORTS_FOLDER'], run_folder_name)
        os.makedirs(output_dir, exist_ok=True)

        # --- ETAPA 2: Busca o relatório anterior no histórico ---
        last_report = Report.query.order_by(Report.timestamp.desc()).first()
        trend_report_path_relative = None

        # --- ETAPA 3: Gera o relatório de tendência (se houver um anterior) ---
        if last_report and last_report.json_summary_path and os.path.exists(last_report.json_summary_path):
            print(f"📈 Relatório anterior encontrado. Iniciando análise de tendência.")
            
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
            print("⚠️ Nenhum relatório anterior encontrado.")

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
            date_range=date_range_atual
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
