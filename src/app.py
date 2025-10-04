import os
import json
import shutil
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from .analisar_alertas import analisar_arquivo_csv
from .analise_tendencia import gerar_relatorio_tendencia
from .get_date_range import get_date_range_from_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_migrate import Migrate
from celery import Celery

# =============================================================================
# CONFIGURAÇÃO FLASK
# =============================================================================
app = Flask(__name__, template_folder='../templates')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, '..', 'data', 'uploads')
REPORTS_FOLDER = os.path.join(BASE_DIR, '..', 'data', 'reports')
DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'meu_dash.db')

app.config.from_mapping(
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    REPORTS_FOLDER=REPORTS_FOLDER,
    SQLALCHEMY_DATABASE_URI=f'sqlite:///{DB_PATH}',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    CELERY_BROKER_URL=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    CELERY_RESULT_BACKEND=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# =============================================================================
# CONFIGURAÇÃO CELERY
# =============================================================================
celery_app = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery_app.conf.update(app.config)

# Envolve as tarefas do Celery com o contexto da aplicação Flask
TaskBase = celery_app.Task
class ContextTask(TaskBase):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return TaskBase.__call__(self, *args, **kwargs)
celery_app.Task = ContextTask

# =============================================================================
# MODELO DE DADOS (DB)
# =============================================================================
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    original_filename = db.Column(db.String(255))
    report_path = db.Column(db.String(255))
    json_summary_path = db.Column(db.String(255))
    date_range = db.Column(db.String(100), nullable=True)
    max_date = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Report {self.original_filename}>'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)

# Limite de relatórios para o sistema de rotação
MAX_REPORTS = 20

# =============================================================================
# TAREFA ASSÍNCRONA (CELERY)
# =============================================================================
@celery_app.task(bind=True)
def processar_analise(self, filepath_atual, filename_atual, reports_folder):
    """
    Task Celery para executar o pipeline de análise completo de forma assíncrona.
    """
    try:
        # --- ETAPA 1: Extrai o intervalo de datas e valida ---
        date_info = get_date_range_from_file(filepath_atual)
        date_range_atual, max_date_atual = (date_info[0], date_info[1]) if date_info else (None, None)

        if not max_date_atual:
            error_msg = f"Não foi possível extrair um período de datas válido do arquivo '{filename_atual}'. Verifique se a coluna 'sys_created_on' está presente e formatada corretamente."
            print(f"❌ Erro de Validação: {error_msg}")
            os.remove(filepath_atual)
            # O estado de falha é definido via exceção para o Celery capturar
            raise ValueError(error_msg)

        # --- ETAPA 2: Validação Cronológica Estrita ---
        last_report = Report.query.order_by(Report.max_date.desc()).first()
        
        if last_report and max_date_atual <= last_report.max_date:
            error_msg = (f"Erro de Cronologia: O período do arquivo enviado ({date_range_atual}) não é posterior ao "
                         f"último relatório processado ({last_report.date_range}). Por favor, envie um arquivo mais recente.")
            print(f"❌ {error_msg}")
            os.remove(filepath_atual)
            raise ValueError(error_msg)

        run_folder_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir = os.path.join(reports_folder, run_folder_name)
        os.makedirs(output_dir, exist_ok=True)

        trend_report_path_relative = None

        # --- ETAPA 3: Gera o relatório de tendência (se houver um anterior válido) ---
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

        # --- ETAPA 5: Salva o novo relatório no banco ---
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
        
        report_url = url_for('serve_report', 
                               run_folder=os.path.basename(os.path.dirname(report_path_final)), 
                               filename=os.path.basename(report_path_final), 
                               _external=True)

        # --- ETAPA 6: Rotação de Relatórios Antigos ---
        try:
            # Ordena do mais novo para o mais antigo
            reports_to_check = Report.query.order_by(Report.timestamp.desc()).all()
            
            if len(reports_to_check) > MAX_REPORTS:
                # Seleciona os relatórios que excedem o limite
                reports_to_delete = reports_to_check[MAX_REPORTS:]
                print(f"ℹ️  Rotação de relatórios: {len(reports_to_delete)} relatório(s) antigo(s) para remover.")
                
                for report in reports_to_delete:
                    try:
                        # O caminho do relatório aponta para um arquivo dentro da pasta 'run_...'
                        # Queremos remover a pasta 'run_...' inteira.
                        report_dir = os.path.dirname(report.report_path)
                        if report_dir and os.path.exists(report_dir):
                            shutil.rmtree(report_dir)
                            print(f"🗑️  Diretório de relatório antigo removido: {report_dir}")
                        
                        db.session.delete(report)
                    except Exception as e_inner:
                        print(f"⚠️  Erro ao remover o relatório antigo {report.id}: {e_inner}")
                
                db.session.commit()
                print("✅ Rotação de relatórios concluída.")
        except Exception as e_rotation:
            print(f"⚠️  Ocorreu um erro durante a rotação de relatórios: {e_rotation}")

        return {"status": "success", "report_url": report_url}

    except Exception as e:
        print(f"❌ Erro fatal na tarefa de análise: {e}")
        # A exceção será propagada e o Celery marcará a tarefa como FALHA
        # O traceback é automaticamente registrado pelo Celery
        raise

# =============================================================================
# ROTAS FLASK
# =============================================================================
@app.route('/health')
def health_check():
    return jsonify({'status': 'ok'}), 200

@app.route('/')
def index():
    last_report = Report.query.order_by(Report.timestamp.desc()).first()
    
    summary_data = None
    last_trend_analysis = None

    if last_report:
        # Link para o relatório de tendência, se existir
        run_folder_path = os.path.dirname(last_report.report_path)
        run_folder_name = os.path.basename(run_folder_path)
        trend_report_path = os.path.join(run_folder_path, 'resumo_tendencia.html')
        if os.path.exists(trend_report_path):
            last_trend_analysis = {
                'url': url_for('serve_report', run_folder=run_folder_name, filename='resumo_tendencia.html'),
                'date': last_report.timestamp.strftime('%d/%m/%Y às %H:%M')
            }

        # Carregar dados do resumo JSON para o dashboard
        if last_report.json_summary_path and os.path.exists(last_report.json_summary_path):
            try:
                with open(last_report.json_summary_path, 'r', encoding='utf-8') as f:
                    summary_data = json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                print(f"⚠️  Não foi possível carregar o arquivo de resumo JSON: {e}")
                summary_data = None

    return render_template(
        'upload.html', 
        last_trend_analysis=last_trend_analysis,
        summary_data=summary_data,
        last_report_date=last_report.timestamp.strftime('%d/%m/%Y às %H:%M') if last_report else None
    )

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Recebe o arquivo, salva, e dispara a tarefa assíncrona de análise.
    """
    if 'file_atual' not in request.files:
        return render_template('upload.html', error="Nenhum arquivo enviado.")
    
    file_atual = request.files['file_atual']

    if file_atual.filename == '':
        return render_template('upload.html', error="Nenhum arquivo selecionado.")

    try:
        filename_atual = secure_filename(file_atual.filename)
        filepath_atual = os.path.join(app.config['UPLOAD_FOLDER'], f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename_atual}")
        file_atual.save(filepath_atual)
        
        # Dispara a tarefa em segundo plano
        task = processar_analise.delay(
            filepath_atual=filepath_atual,
            filename_atual=filename_atual,
            reports_folder=app.config['REPORTS_FOLDER']
        )
        
        return redirect(url_for('task_page', task_id=task.id))

    except Exception as e:
        print(f"❌ Erro fatal no processo de upload: {e}")
        import traceback
        traceback.print_exc()
        return render_template('upload.html', error="Ocorreu um erro ao processar o arquivo. Verifique se o formato do CSV está correto e tente novamente.")

@app.route('/task/<task_id>')
def task_page(task_id):
    """Página que mostra o status de uma tarefa em andamento."""
    return render_template('status.html', task_id=task_id)

@app.route('/status/<task_id>')
def task_status(task_id):
    """Retorna o status de uma tarefa Celery."""
    task = processar_analise.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'result': {'status': 'Pendente...'}
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'result': task.info, # task.info contém o dicionário de retorno da tarefa
        }
    else:
        # Em caso de falha, o resultado é a própria exceção
        response = {
            'state': task.state,
            'result': {'error': str(task.info)}, # str(task.info) converte a exceção em string
        }
    return jsonify(response)

# (O restante das rotas para servir arquivos permanece o mesmo)
@app.route('/reports/<run_folder>/planos_de_acao/<filename>')
def serve_planos(run_folder, filename):
    return send_from_directory(os.path.join(app.config['REPORTS_FOLDER'], run_folder, 'planos_de_acao'), filename)

@app.route('/reports/<run_folder>/detalhes/<filename>')
def serve_detalhes(run_folder, filename):
    return send_from_directory(os.path.join(app.config['REPORTS_FOLDER'], run_folder, 'detalhes'), filename)

@app.route('/reports/<run_folder>/<path:filename>')
def serve_report(run_folder, filename):
    return send_from_directory(os.path.join(app.config['REPORTS_FOLDER'], run_folder), filename)

@app.route('/docs/<path:filename>')
def serve_docs(filename):
    docs_dir = os.path.abspath(os.path.join(app.root_path, '..', 'docs'))
    return send_from_directory(docs_dir, filename)

@app.route('/relatorios')
def relatorios():
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

# =============================================================================
# INICIALIZAÇÃO
# =============================================================================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)