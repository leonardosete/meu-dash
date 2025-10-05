import os
import shutil # NOVO: Para deletar diretórios recursivamente
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, flash # NOVO: flash adicionado
from werkzeug.utils import secure_filename
from .analisar_alertas import analisar_arquivo_csv
from .analise_tendencia import gerar_relatorio_tendencia
from .get_date_range import get_date_range_from_file
from .utils import sort_files_by_date # NOVO: Importando a função de ordenação
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
    
    last_report = Report.query.order_by(Report.timestamp.desc()).first()

    if last_report:
        run_folder_path = os.path.dirname(last_report.report_path)
        run_folder_name = os.path.basename(run_folder_path)

        trend_report_path = os.path.join(run_folder_path, 'resumo_tendencia.html')
        if os.path.exists(trend_report_path):
            last_trend_analysis = {
                'url': url_for('serve_report', run_folder=run_folder_name, filename='resumo_tendencia.html'),
                'date': last_report.timestamp.strftime('%d/%m/%Y às %H:%M')
            }

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
        filename_atual = secure_filename(file_atual.filename)
        filepath_atual = os.path.join(app.config['UPLOAD_FOLDER'], f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename_atual}")
        file_atual.save(filepath_atual)
        date_range_atual = get_date_range_from_file(filepath_atual)

        run_folder_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir = os.path.join(app.config['REPORTS_FOLDER'], run_folder_name)
        os.makedirs(output_dir, exist_ok=True)

        last_report = Report.query.order_by(Report.timestamp.desc()).first()
        trend_report_path_relative = None

        if last_report and last_report.json_summary_path and os.path.exists(last_report.json_summary_path):
            print(f"📈 Relatório anterior encontrado. Iniciando análise de tendência.")

            # Salva o arquivo CSV anterior temporariamente para usar a função de ordenação
            # Esta é uma simplificação. O ideal seria ter o arquivo original ou extrair a data do JSON.
            # Por agora, vamos assumir que o date_range é suficiente.
            date_range_anterior_obj = datetime.strptime(last_report.date_range.split(' a ')[0], '%d/%m/%Y') if last_report.date_range else None
            date_range_atual_obj = datetime.strptime(date_range_atual.split(' a ')[0], '%d/%m/%Y') if date_range_atual else None

            if date_range_anterior_obj and date_range_atual_obj and date_range_atual_obj > date_range_anterior_obj:
                print("✅ Período do upload é mais recente que o último relatório. Gerando tendência...")
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
                print("⚠️  Aviso: O arquivo enviado não é cronologicamente mais recente que o último relatório. A análise de tendência será pulada.")
        else:
            print("⚠️ Nenhum relatório anterior encontrado para comparação.")

        final_analysis_results = analisar_arquivo_csv(
            input_file=filepath_atual, 
            output_dir=output_dir, 
            light_analysis=False,
            trend_report_path=trend_report_path_relative
        )
        report_path_final = final_analysis_results['html_path']
        json_path_final = final_analysis_results['json_path']

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
        os.makedirs(output_dir, exist_ok=True)

        # Gera os resumos JSON para ambos os arquivos
        results_atual = analisar_arquivo_csv(filepath_atual, output_dir, light_analysis=True)
        results_anterior = analisar_arquivo_csv(filepath_anterior, output_dir, light_analysis=True)

        # Gera o relatório de tendência
        output_trend_path = os.path.join(output_dir, 'resumo_tendencia.html')
        gerar_relatorio_tendencia(
            json_anterior=results_anterior['json_path'],
            json_atual=results_atual['json_path'],
            csv_anterior_name=filename_anterior,
            csv_atual_name=filename_atual,
            output_path=output_trend_path,
            date_range_anterior=get_date_range_from_file(filepath_anterior),
            date_range_atual=get_date_range_from_file(filepath_atual)
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