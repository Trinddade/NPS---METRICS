from flask import Flask, request, render_template_string, redirect, url_for, render_template
import pandas as pd
import sqlite3
import config as config
import plotly.graph_objs as go
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
    return render_template('identificador_nps.html')

@app.route('/enviar', methods=['POST'])
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
    return render_template('pesquisa_nps.html')

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
    return render_template('obrigado.html')

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
    
    return df_identificacao, df_respostas_nps

def juncao(df_identificacao: pd.DataFrame, df_respostas_nps: pd.DataFrame) -> pd.DataFrame:
    
    df_completo = pd.merge(
        df_identificacao,
        df_respostas_nps,
        left_on="id",
        right_on="identificacao_id",
        how="inner"
    )
    return df_completo

def preparar_nps(df: pd.DataFrame) -> pd.DataFrame:
    
    df = df.copy()
    
    df["score_satisfacao"] = df[
        [
            "qualidade_produto",
            "atendimento",
            "prazo_entrega",
            "custo_beneficio",
            "facilidade_negociacao",
            "satisfacao_geral"
        ]
    ].mean(axis=1)
    
    return df

def classificar_nps(df: pd.DataFrame) -> pd.DataFrame:
    
    df["score_satisfacao"] = pd.to_numeric(df["score_satisfacao"], errors="coerce")
    
    df["categoria_nps"] = np.select(
        [
            df["score_satisfacao"] >= 4.5,
            df["score_satisfacao"].between(3.5, 4.49),
            df["score_satisfacao"] < 3.5
        ],
        [
            "Promotor",
            "Neutro",
            "Detrator"
        ],
        default="Indefinido"
    )
    
    return df

def calcular_nps(df: pd.DataFrame):

    promotores = (df["categoria_nps"] == "Promotor").sum()
    detratores = (df["categoria_nps"] == "Detrator").sum()

    total = len(df)

    if total == 0:
        return 0

    nps = ((promotores - detratores) / total) * 100

    return nps

@app.route('/dashboard')
def dashboard():

    df_identificacao, df_respostas_nps = carregar_dataframes()

    df_identificacao, df_respostas_nps = standardize(
        df_identificacao,
        df_respostas_nps
    )

    df_completo = juncao(
        df_identificacao,
        df_respostas_nps
    )

    df_completo = preparar_nps(df_completo)
    df_completo = classificar_nps(df_completo)

    nps_valor = calcular_nps(df_completo)

    fig_nps = go.Figure(go.Indicator(
        mode="gauge+number",
        value=nps_valor,
        title={'text': "NPS Geral"},
        number={'font':{'size':60,'color':'#ffffff'}},
        gauge={
            'axis': {'range': [-100, 100],'tickcolor':'#ffffff'},
            'bar': {'color': '#22c55e'},
            'bgcolor':'#0b0b0c',
            'borderwidth':0,
            'steps': [
                {'range': [-100, 0], 'color': "#ef4444"},
                {'range': [0, 50], 'color': "#f59e0b"},
                {'range': [50, 100], 'color': "#22c55e"}
            ]
        }
    ))

    fig_nps.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff")
    )

    categorias = df_completo["categoria_nps"].value_counts()

    fig_categorias = go.Figure(
        data=[go.Pie(
            labels=categorias.index,
            values=categorias.values,
            hole=0.65,
            marker=dict(colors=["#22c55e","#f59e0b","#ef4444"])
        )]
    )

    fig_categorias.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff"),
        showlegend=True
    )

    medias = df_completo[
        [
            "qualidade_produto",
            "atendimento",
            "prazo_entrega",
            "custo_beneficio",
            "facilidade_negociacao",
            "satisfacao_geral"
        ]
    ].mean()

    fig_medias = go.Figure(
        data=[go.Bar(
            x=medias.index,
            y=medias.values,
            marker_color=["#38bdf8","#22c55e","#a855f7","#f59e0b","#6366f1","#ef4444"]
        )]
    )

    fig_medias.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff"),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True,gridcolor="#1f1f22")
    )

    fig_hist = go.Figure(
        data=[go.Histogram(
            x=df_completo["nps_nota"],
            nbinsx=11,
            marker_color="#38bdf8"
        )]
    )

    fig_hist.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff"),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True,gridcolor="#1f1f22")
    )

    evolucao = df_completo.groupby("created_at")["score_satisfacao"].mean().reset_index()

    fig_evolucao = go.Figure(
        data=[go.Scatter(
            x=evolucao["created_at"],
            y=evolucao["score_satisfacao"],
            mode="lines+markers",
            line=dict(color="#22c55e", width=3),
            marker=dict(size=8,color="#22c55e")
        )]
    )

    fig_evolucao.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff"),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True,gridcolor="#1f1f22")
    )

    ranking = (
        df_completo.groupby("nome_empresa")["score_satisfacao"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
    )

    fig_empresas = go.Figure(
        data=[go.Bar(
            x=ranking.values,
            y=ranking.index,
            orientation="h",
            marker_color="#a855f7"
        )]
    )

    fig_empresas.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff"),
        xaxis=dict(showgrid=True,gridcolor="#1f1f22"),
        yaxis=dict(showgrid=False)
    )

    graph1 = fig_nps.to_html(full_html=False)
    graph2 = fig_categorias.to_html(full_html=False)
    graph3 = fig_medias.to_html(full_html=False)
    graph4 = fig_hist.to_html(full_html=False)
    graph5 = fig_evolucao.to_html(full_html=False)
    graph6 = fig_empresas.to_html(full_html=False)

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>

<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">

<style>

*{
margin:0;
padding:0;
box-sizing:border-box;
}

body{
font-family:'Inter',sans-serif;
background:#060606;
color:#ffffff;
}

.header{
padding:28px 40px;
font-size:26px;
font-weight:600;
background:#0b0b0c;
border-bottom:1px solid #1c1c1f;
letter-spacing:-0.5px;
}

.dashboard{
max-width:1500px;
margin:auto;
padding:40px;
}

.grid{
display:grid;
grid-template-columns:1fr 1fr;
gap:30px;
margin-top:30px;
}

.card{
background:#0f0f11;
border-radius:18px;
padding:26px;
border:1px solid #1c1c1f;
box-shadow:0 25px 60px rgba(0,0,0,0.7);
transition:all .25s ease;
}

.card:hover{
transform:translateY(-4px);
border-color:#2a2a2e;
}

.card-large{
grid-column:1 / -1;
}

.card-title{
font-size:14px;
color:#9ca3af;
margin-bottom:14px;
letter-spacing:0.4px;
}

@media (max-width:900px){

.grid{
grid-template-columns:1fr;
}

.dashboard{
padding:25px;
}

}

</style>

</head>

<body>

<div class="header">
NPS Analytics
</div>

<div class="dashboard">

<div class="card card-large">
<div class="card-title">NPS Score</div>
{{graph1|safe}}
</div>

<div class="grid">

<div class="card">
<div class="card-title">Clientes</div>
{{graph2|safe}}
</div>

<div class="card">
<div class="card-title">Avaliações</div>
{{graph3|safe}}
</div>

<div class="card">
<div class="card-title">Notas</div>
{{graph4|safe}}
</div>

<div class="card">
<div class="card-title">Evolução</div>
{{graph5|safe}}
</div>

</div>

<div class="card" style="margin-top:30px;">
<div class="card-title">Ranking</div>
{{graph6|safe}}
</div>

</div>

</body>
</html>
""",
graph1=graph1,
graph2=graph2,
graph3=graph3,
graph4=graph4,
graph5=graph5,
graph6=graph6)
    
if __name__ == '__main__':
    
    init_db()
    
    df_identificacao, df_respostas_nps = carregar_dataframes()
    
    df_identificacao, df_respostas_nps = standardize(
    df_identificacao,
    df_respostas_nps
)
    df_completo = juncao(
    df_identificacao,
    df_respostas_nps
)
    df_completo = preparar_nps(df_completo)

    df_completo = classificar_nps(df_completo)

    nps = calcular_nps(df_completo)
    
    print("\n📌 DataFrame Identificação:")
    print(df_identificacao.head())

    print("\n📌 DataFrame Respostas NPS:")
    print(df_respostas_nps.head())
    
    print(df_completo)
    
    app.run(debug=True)