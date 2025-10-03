import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from .analisar_alertas import analisar_arquivo_csv
from .analise_tendencia import gerar_relatorio_tendencia as run_trend_analysis_script
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__, template_folder='../templates')

# Define caminhos absolutos e fixos para garantir consistência.
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
    json_summary_path = db.Column(db.String(255)) # Novo campo para o JSON

    def __repr__(self):
        return f'<Report {self.original_filename}>'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file_atual = request.files.get('file_atual')
    file_anterior = request.files.get('file_anterior')

    if not file_atual or file_atual.filename == '':
        return render_template('upload.html', error="O arquivo do período atual é obrigatório.")

    try:
        # --- ETAPA 1: Salvar e analisar o arquivo ATUAL (light analysis) ---
        filename_atual = secure_filename(file_atual.filename)
        filepath_atual = os.path.join(app.config['UPLOAD_FOLDER'], f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename_atual}")
        file_atual.save(filepath_atual)

        # Roda uma análise leve apenas para gerar o JSON necessário para a comparação.
        run_folder_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir = os.path.join(app.config['REPORTS_FOLDER'], run_folder_name)
        os.makedirs(output_dir, exist_ok=True)

        json_path_atual = analisar_arquivo_csv(filepath_atual, output_dir, light_analysis=True)['json_path']

        # --- ETAPA 2: Obter o JSON do arquivo ANTERIOR ---
        json_path_anterior = None
        filename_anterior = None

        if file_anterior and file_anterior.filename != '':
            # Caso 1: Usuário forneceu um arquivo anterior específico.
            filename_anterior = secure_filename(file_anterior.filename)
            filepath_anterior = os.path.join(app.config['UPLOAD_FOLDER'], f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename_anterior}")
            file_anterior.save(filepath_anterior)
            # Roda análise leve no arquivo anterior.
            json_path_anterior = analisar_arquivo_csv(filepath_anterior, output_dir, light_analysis=True)['json_path']
        else:
            # Caso 2: Buscar o relatório mais recente no banco de dados.
            last_report = Report.query.order_by(Report.timestamp.desc()).first()
            if last_report:
                json_path_anterior = last_report.json_summary_path
                filename_anterior = last_report.original_filename

        # --- ETAPA 3: Gerar o relatório de tendência, se possível ---
        trend_report_path = None
        if json_path_anterior and os.path.exists(json_path_anterior):
            print(f"📈 Iniciando análise de tendência entre '{filename_atual}' e '{filename_anterior}'...")
            output_trend_path = os.path.join(output_dir, 'resumo_tendencia.html')
            run_trend_analysis_script(
                json_anterior=json_path_anterior,
                json_atual=json_path_atual,
                csv_anterior_name=filename_anterior or "Histórico",
                csv_atual_name=filename_atual,
                output_path=output_trend_path
            )
            trend_report_path = output_trend_path
        else:
            print("⚠️ Não foi encontrado um relatório anterior para comparação. O relatório de tendência não será gerado.")

        # --- ETAPA 4: Gerar o relatório completo para o arquivo ATUAL ---
        # Agora, com o caminho do relatório de tendência em mãos, geramos o dashboard completo.
        analysis_results_final = analisar_arquivo_csv(
            filepath_atual,
            output_dir,
            light_analysis=False,
            trend_report_path=trend_report_path
        )
        report_path_final = analysis_results_final['html_path']

        # --- ETAPA 5: Salvar no banco e redirecionar ---
        new_report = Report(
            original_filename=filename_atual,
            report_path=report_path_final,
            json_summary_path=json_path_atual
        )
        db.session.add(new_report)
        db.session.commit()

        run_folder = os.path.basename(os.path.dirname(report_path_final))
        report_filename = os.path.basename(report_path_final)
        return redirect(url_for('serve_report', run_folder=run_folder, filename=report_filename))

    except Exception as e:
        print(f"❌ Erro fatal no processo de upload: {e}")
        import traceback
        traceback.print_exc()
        return render_template('upload.html', error="Ocorreu um erro ao processar o arquivo. Verifique se o formato do CSV está correto e tente novamente.")


@app.route('/reports/<run_folder>/planos_de_acao/<filename>')
def serve_planos(run_folder, filename):
    return send_from_directory(os.path.join(app.config['REPORTS_FOLDER'], run_folder, 'planos_de_acao'), filename)

@app.route('/reports/<run_folder>/detalhes/<filename>')
def serve_detalhes(run_folder, filename):
    return send_from_directory(os.path.join(app.config['REPORTS_FOLDER'], run_folder, 'detalhes'), filename)

@app.route('/reports/<run_folder>/<path:filename>')
def serve_report(run_folder, filename):
    return send_from_directory(os.path.join(app.config['REPORTS_FOLDER'], run_folder), filename)

@app.route('/relatorios')
def relatorios():
    reports = Report.query.order_by(Report.timestamp.desc()).all()
    # Adiciona a lógica para extrair o run_folder do report_path
    report_data = []
    for report in reports:
        run_folder = os.path.basename(os.path.dirname(report.report_path))
        filename = os.path.basename(report.report_path)
        report_data.append({
            'timestamp': report.timestamp,
            'original_filename': report.original_filename,
            'url': url_for('serve_report', run_folder=run_folder, filename=filename)
        })
    return render_template('relatorios.html', reports=report_data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
