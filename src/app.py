import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from .analisar_alertas import analisar_arquivo_csv
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import pandas as pd
app = Flask(__name__, template_folder='../templates')

# Define caminhos absolutos e fixos para garantir consistência dentro do contêiner.
BASE_DIR = '/app'
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data', 'uploads')
REPORTS_FOLDER = os.path.join(BASE_DIR, 'data', 'reports')
DB_PATH = os.path.join(BASE_DIR, 'data', 'meu_dash.db')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['REPORTS_FOLDER'] = REPORTS_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db, directory='migrations')

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    original_filename = db.Column(db.String(255))
    report_path = db.Column(db.String(255))

    def __repr__(self):
        return f'<Report {self.original_filename}>'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        report_path = analisar_arquivo_csv(filepath, app.config['REPORTS_FOLDER'])
        
        # Save report metadata to the database
        new_report = Report(
            original_filename=filename,
            report_path=report_path
        )
        db.session.add(new_report)
        db.session.commit()

        report_filename = os.path.basename(report_path)
        run_folder = os.path.basename(os.path.dirname(report_path))

        return redirect(url_for('serve_report', run_folder=run_folder, filename=report_filename))

@app.route('/reports/<run_folder>/planos_de_acao/<filename>')
def serve_planos(run_folder, filename):
    return send_from_directory(os.path.join(app.config['REPORTS_FOLDER'], run_folder, 'planos_de_acao'), filename)

@app.route('/reports/<run_folder>/detalhes/<filename>')
def serve_detalhes(run_folder, filename):
    return send_from_directory(os.path.join(app.config['REPORTS_FOLDER'], run_folder, 'detalhes'), filename)

# Rota genérica para servir arquivos na raiz do diretório do run (ex: resumo_geral.html, editor_atuacao.html).
# Esta rota deve ser a ÚLTIMA para evitar conflitos com as rotas de subdiretórios mais específicas.
@app.route('/reports/<run_folder>/<path:filename>')
def serve_report(run_folder, filename):
    return send_from_directory(os.path.join(app.config['REPORTS_FOLDER'], run_folder), filename)

@app.route('/editor_atuacao/<run_folder>')
def editor_atuacao(run_folder):
    """
    Gera dinamicamente a página do editor de atuação lendo o CSV correspondente.
    """
    csv_filename = 'atuar.csv'
    csv_path = os.path.join(app.config['REPORTS_FOLDER'], run_folder, csv_filename)
    try:
        # Lê o conteúdo do CSV para injetar no template
        with open(csv_path, 'r', encoding='utf-8') as f:
            csv_content = f.read()
    except FileNotFoundError:
        return "Arquivo de atuação não encontrado para esta execução.", 404

    # Renderiza o template do editor com os dados do CSV
    return render_template(
        'editor_template.html',
        csv_data=csv_content,
        csv_filename=csv_filename
    )

@app.route('/relatorios')
def relatorios():
    reports = Report.query.order_by(Report.timestamp.desc()).all()
    return render_template('relatorios.html', reports=reports)
