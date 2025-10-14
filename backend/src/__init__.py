from flask_sqlalchemy import SQLAlchemy

# Cria a instância do SQLAlchemy aqui para evitar importações circulares.
# Esta instância será importada por 'app.py' e 'models.py'.
db = SQLAlchemy()
