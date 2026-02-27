from flask import Flask, request, jsonify, render_template_string
import pandas as pd
import sqlite3
import os
import config
import plotly.graph_objs as go
import dash
from dash import Dash, html, dcc
import numpy as np

app = Flask(__name__)
DB_PATH = config.DB_PATH

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pesquisas_nps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cnpj TEXT NOT NULL,
                nome_empresa TEXT NOT NULL,
                nome_completo TEXT NOT NULL,
                nps_nota INTEGER NOT NULL CHECK (nps_nota BETWEEN 0 AND 10),
                qualidade_produto INTEGER NOT NULL CHECK (qualidade_produto BETWEEN 1 AND 5),
                atendimento INTEGER NOT NULL CHECK (atendimento BETWEEN 1 AND 5),
                prazo_entrega INTEGER NOT NULL CHECK (prazo_entrega BETWEEN 1 AND 5),
                custo_beneficio INTEGER NOT NULL CHECK (custo_beneficio BETWEEN 1 AND 5),
                facilidade_negociacao INTEGER NOT NULL CHECK (facilidade_negociacao BETWEEN 1 AND 5),
                satisfacao_geral INTEGER NOT NULL CHECK (satisfacao_geral BETWEEN 1 AND 5),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    
@app.route('/')
def index():
    return render_template_string(open('form_nps.html').read())

@app.route('/receber')
def enviar():
    try:
        nome = request.form['nome']
        cnpj = request.form['cnpj']
        empresa = request.form['empresa']
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                            INSERT INTO pesquisas_nps (
                            nome_completo, cnpj, nome_empresa
                )           VALUES (?, ?, ?)
                            ''', (nome, cnpj, empresa))
            conn.commit()
        
        return '<h2>Obrigado! Seus dados foram salvos com sucesso.</h2>'

    except Exception as e:
        return f'<h2>Erro ao salvar os dados: {e}</h2>'
        
    
if __name__ == '__main__':
    init_db()
    app.run(debug=True)