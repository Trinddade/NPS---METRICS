from flask import Flask, request, jsonify, render_template_string, redirect, url_for
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
            CREATE TABLE IF NOT EXISTS identificacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_completo TEXT NOT NULL,
            cnpj TEXT NOT NULL,
            nome_empresa TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
    ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS respostas_nps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identificacao_id INTEGER NOT NULL,
            nps_nota INTEGER NOT NULL CHECK (nps_nota BETWEEN 0 AND 10),
            qualidade_produto INTEGER NOT NULL CHECK (qualidade_produto BETWEEN 1 AND 5),
            atendimento INTEGER NOT NULL CHECK (atendimento BETWEEN 1 AND 5),
            prazo_entrega INTEGER NOT NULL CHECK (prazo_entrega BETWEEN 1 AND 5),
            custo_beneficio INTEGER NOT NULL CHECK (custo_beneficio BETWEEN 1 AND 5),
            facilidade_negociacao INTEGER NOT NULL CHECK (facilidade_negociacao BETWEEN 1 AND 5),
            satisfacao_geral INTEGER NOT NULL CHECK (satisfacao_geral BETWEEN 1 AND 5),

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (identificacao_id) REFERENCES identificacao(id)                 
                )             
    ''')
        
        conn.commit()
    
@app.route('/')
def index():
    return render_template_string(open('identificador_nps.html').read())

@app.route('/enviar', methods=['GET', 'POST'])
def enviar():
    if request.method == 'POST':
        try:
            nome_completo = request.form['nome']
            cnpj = request.form['cnpj']
            nome_empresa = request.form['empresa']
        
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                                INSERT INTO identificacao (
                                nome_completo, cnpj, nome_empresa
                    )               VALUES (?, ?, ?)
                                ''', (nome_completo, cnpj, nome_empresa))
                conn.commit()
        
            return redirect (url_for('pesquisa_nps'))

        except Exception as e:
            return f'<h2>Erro ao salvar os dados: {e}</h2>'
    return redirect(url_for('index'))
    
@app.route('/nps')
def pesquisa_nps():
    return render_template_string(open('pesquisa_nps.html').read())

@app.route('/salvar_nps', methods=['POST'])
def salvar_nps():
    try:
        nps_nota = request.form['nps_nota']
        qualidade_produto = request.form['qualidade_produto']
        atendimento = request.form['atendimento']
        prazo_entrega = request.form['prazo_entrega']
        custo_beneficio = request.form['custo_beneficio']
        facilidade_negociacao = request.form['facilidade_negociacao']
        satisfacao_geral = request.form['satisfacao_geral']
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM identificacao ORDER BY id DESC LIMIT 1")
            identificacao_id = cursor.fetchone()[0]
            cursor.execute('''
                    INSERT INTO respostas_nps (
                        identificacao_id,
                        nps_nota,
                        qualidade_produto,
                        atendimento,
                        prazo_entrega,
                        custo_beneficio,
                        facilidade_negociacao,
                        satisfacao_geral
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    identificacao_id,
                    nps_nota,
                    qualidade_produto,
                    atendimento,
                    prazo_entrega,
                    custo_beneficio,
                    facilidade_negociacao,
                    satisfacao_geral
                ))
            conn.commit()

        return redirect(url_for('obrigado'))

    except Exception as e:
        return f"<h2>Erro: {e}</h2>"
    
@app.route('/obrigado')
def obrigado():
    return render_template_string(open('obrigado.html').read())

def carregar_dataframes():
    with sqlite3.connect(DB_PATH) as conn:
        df_identificacao = pd.read_sql_query(
            "SELECT * FROM identificacao", conn
        )
        df_respostas_nps = pd.read_sql_query(
            "SELECT * FROM respostas_nps", conn
        )
    return df_identificacao, df_respostas_nps

def standardize(df_identificacao: pd.DataFrame, df_respostas_nps: pd.DataFrame) -> tuple:
    
    df_identificacao = df_identificacao.copy()
    df_respostas_nps = df_respostas_nps.copy()
    
    df_identificacao['created_at'] = pd.to_datetime(df_identificacao['created_at'])
    df_identificacao['created_at'] = df_identificacao['created_at'].dt.date
    df_identificacao['nome_completo'] = df_identificacao['nome_completo'].str.strip().str.title()
    df_identificacao['nome_empresa'] = df_identificacao['nome_empresa'].str.strip().str.title()
    df_identificacao['cnpj'] = df_identificacao['cnpj'].astype(str).str.strip().str.zfill(14)
    
    df_respostas_nps = df_respostas_nps.drop(columns=['created_at'])
    
    return ## falta concluir
#  fase final da transformação, falta a logica para gerar o número de NPS
# importante é transformar os valores das colunas que vão receber as respostas da pesquisa para int
    
if __name__ == '__main__':
    
    init_db()
    
    df_identificacao, df_respostas_nps = carregar_dataframes()
    
    print("\n📌 DataFrame Identificação:")
    print(df_identificacao.head())

    print("\n📌 DataFrame Respostas NPS:")
    print(df_respostas_nps.head())
    
    app.run(debug=True)