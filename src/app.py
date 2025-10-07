import os
import shutil # Para deletar diretórios recursivamente
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, flash # NOVO: flash adicionado
from werkzeug.utils import secure_filename
from . import services
from .get_date_range import get_date_range_from_file
from .utils import sort_files_by_date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text 
from flask_migrate import Migrate

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
app.config['SECRET_KEY'] = 'uma-chave-secreta-forte-para-flash' # NOVO: Chave secreta necessária para usar flash
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    original_filename = db.Column(db.String(255))
    report_path = db.Column(db.String(255))
    json_summary_path = db.Column(db.String(255))
    date_range = db.Column(db.String(100), nullable=True)

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
    
    # Lógica para o plano de ação continua a mesma: sempre o mais recente.
    last_report = Report.query.order_by(Report.timestamp.desc()).first()
    if last_report:
        run_folder_path = os.path.dirname(last_report.report_path)
        run_folder_name = os.path.basename(run_folder_path)
        action_plan_path = os.path.join(run_folder_path, 'editor_atuacao.html')
        if os.path.exists(action_plan_path):
            last_action_plan = {
                'url': url_for('serve_report', run_folder=run_folder_name, filename='editor_atuacao.html'),
                'date': last_report.timestamp.strftime('%d/%m/%Y às %H:%M')
            }

    # NOVA LÓGICA: Encontra o relatório de tendência mais recente, independentemente da última análise.
    all_reports_desc = Report.query.order_by(Report.timestamp.desc()).all()
    for report in all_reports_desc:
        # Adicionado um bloco try/except para o caso de o report.report_path ser inválido
        try:
            run_folder_path = os.path.dirname(report.report_path)
            trend_report_path = os.path.join(run_folder_path, 'resumo_tendencia.html')
            if os.path.exists(trend_report_path):
                run_folder_name = os.path.basename(run_folder_path)
                last_trend_analysis = {
                    'url': url_for('serve_report', run_folder=run_folder_name, filename='resumo_tendencia.html'),
                    'date': report.timestamp.strftime('%d/%m/%Y às %H:%M')
                }
                break # Encontrou o mais recente, pode parar
        except Exception:
            # Ignora relatórios com caminhos inválidos que poderiam quebrar a página inicial
            continue
            
    return render_template(
        'upload.html', 
        last_trend_analysis=last_trend_analysis,
        last_action_plan=last_action_plan
    )

@app.route('/upload', methods=['POST'])
def upload_file():
    """Orquestra o processo de upload, análise e geração de relatórios."""
    if 'file_atual' not in request.files:
        flash("Nenhum arquivo enviado.", "error")
        return redirect(url_for('index'))
        
    file_atual = request.files['file_atual']

    if file_atual.filename == '':
        flash("Nenhum arquivo selecionado.", "error")
        return redirect(url_for('index'))

    try:
        # Delega toda a lógica de negócio para a nova camada de serviço
        result = services.process_upload_and_generate_reports(
            file_atual=file_atual,
            upload_folder=app.config['UPLOAD_FOLDER'],
            reports_folder=app.config['REPORTS_FOLDER'],
            db=db,
            Report=Report,
            base_dir=BASE_DIR
        )

        if result:
            return redirect(url_for('serve_report', run_folder=result['run_folder'], filename=result['report_filename']))
        else:
            raise Exception("O serviço de processamento falhou sem retornar um erro específico.")

    except Exception as e:
        print(f"❌ Erro fatal no processo de upload: {e}")
        import traceback
        traceback.print_exc()
        flash("Ocorreu um erro ao processar o arquivo. Verifique se o formato do CSV está correto e tente novamente.", "error")
        return redirect(url_for('index'))

@app.route('/compare', methods=['POST'])
def compare_files():
    """
    Orquestra a comparação direta entre dois arquivos enviados pelo usuário.
    """
    if 'files' not in request.files:
        flash("Nenhum arquivo enviado.", "error")
        return redirect(url_for('index'))

    files = request.files.getlist('files')
    
    if len(files) != 2:
        flash("Por favor, selecione exatamente dois arquivos para comparação.", "error")
        return redirect(url_for('index'))

    saved_filepaths = []
    for f in files:
        if f.filename == '':
            # A validação de 'required' no HTML deve pegar isso, mas é uma segurança extra.
            flash("Ambos os campos de arquivo devem ser preenchidos.", "error")
            return redirect(url_for('index'))
        
        filename = secure_filename(f.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}")
        f.save(filepath)
        saved_filepaths.append(filepath)

    try:
        # Usa a lógica importada para determinar qual arquivo é o atual e qual é o anterior
        sorted_paths = sort_files_by_date(saved_filepaths)
        if not sorted_paths:
            flash("Não foi possível determinar a ordem cronológica dos arquivos. Verifique se ambos contêm a coluna 'sys_created_on' com datas válidas.", "error")
            return redirect(url_for('index'))

        filepath_atual, filepath_anterior = sorted_paths
        filename_atual = os.path.basename(filepath_atual).replace(f"temp_{os.path.basename(filepath_atual).split('_')[1]}_", "")
        filename_anterior = os.path.basename(filepath_anterior).replace(f"temp_{os.path.basename(filepath_anterior).split('_')[1]}_", "")
        
        run_folder_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_compare"
        output_dir = os.path.join(app.config['REPORTS_FOLDER'], run_folder_name)
        
        # Cria subdiretórios para cada análise para evitar conflitos de arquivos
        output_dir_anterior = os.path.join(output_dir, 'anterior')
        output_dir_atual = os.path.join(output_dir, 'atual')
        os.makedirs(output_dir_anterior, exist_ok=True)
        os.makedirs(output_dir_atual, exist_ok=True)

        # ALTERAÇÃO: Executa a análise completa (False) para garantir consistência total
        # com o fluxo de upload padrão. Isso gera todos os relatórios para ambos os
        # períodos, garantindo que os JSONs de resumo sejam 100% precisos.
        print("⚙️  Executando análise completa para o arquivo ATUAL...")
        results_atual = analisar_arquivo_csv(filepath_atual, output_dir_atual, light_analysis=False)
        print("⚙️  Executando análise completa para o arquivo ANTERIOR...")
        results_anterior = analisar_arquivo_csv(filepath_anterior, output_dir_anterior, light_analysis=False)

        # Gera o relatório de tendência
        output_trend_path = os.path.join(output_dir, 'resumo_tendencia.html')
        gerar_relatorio_tendencia(
            json_anterior=results_anterior['json_path'],
            json_atual=results_atual['json_path'],
            csv_anterior_name=filename_anterior,
            csv_atual_name=filename_atual,
            output_path=output_trend_path,
            date_range_anterior=get_date_range_from_file(filepath_anterior),
            date_range_atual=get_date_range_from_file(filepath_atual),
            is_direct_comparison=True # Informa que é uma comparação direta
        )
        
        return redirect(url_for('serve_report', run_folder=run_folder_name, filename='resumo_tendencia.html'))

    except Exception as e:
        print(f"❌ Erro fatal no processo de comparação: {e}")
        flash("Ocorreu um erro inesperado durante a comparação. Verifique os logs.", "error")
        return redirect(url_for('index'))
    finally:
        # Garante que os arquivos temporários sejam sempre limpos, mesmo em caso de erro.
        for p in saved_filepaths:
            if os.path.exists(p):
                os.remove(p)

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

@app.route('/docs/<path:filename>')
def serve_docs(filename):
    docs_dir = os.path.abspath(os.path.join(app.root_path, '..', 'docs'))
    return send_from_directory(docs_dir, filename)

@app.route('/relatorios')
def relatorios():
    """Exibe a página de histórico de relatórios."""
    reports = Report.query.order_by(Report.timestamp.desc()).all()
    report_data = []
    for report in reports:
        report_data.append({
            'id': report.id, # NOVO: Passando o ID para a exclusão
            'timestamp': report.timestamp,
            'original_filename': report.original_filename,
            'url': url_for('serve_report', 
                        run_folder=os.path.basename(os.path.dirname(report.report_path)), 
                        filename=os.path.basename(report.report_path))
        })
    return render_template('relatorios.html', reports=report_data)

# --- NOVA ROTA PARA EXCLUSÃO ---
@app.route('/report/delete/<int:report_id>', methods=['POST'])
def delete_report(report_id):
    """Encontra e exclui um relatório do banco e do sistema de arquivos."""
    report = Report.query.get_or_404(report_id)
    
    try:
        # Pega o diretório do relatório (ex: '.../data/reports/run_20251005_103000')
        report_dir = os.path.dirname(report.report_path)
        
        # Deleta a pasta inteira do 'run', garantindo que todos os arquivos associados sejam removidos
        if os.path.isdir(report_dir):
            shutil.rmtree(report_dir)
            print(f"🗑️ Diretório '{report_dir}' excluído com sucesso.")
        
        # Deleta o registro do banco de dados
        db.session.delete(report)
        db.session.commit()
        
        print(f"✅ Relatório '{report.original_filename}' excluído do banco de dados.")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao excluir o relatório {report_id}: {e}")
        
    return redirect(url_for('relatorios'))


# --- INICIALIZAÇÃO DA APLICAÇÃO ---

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)