import dash
from dash import dcc, html
import plotly.graph_objs as go
import requests
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
import io
import flask

# Inicializar o aplicativo Dash
app = dash.Dash(__name__)
server = app.server

# Função para obter os dados da API
def get_data_from_api():
    url = "https://api.ember-energy.org/v1/electricity-generation/yearly"
    params = {
        "entity_code": "BRA",
        "is_aggregate_series": "false",
        "start_date": "1990",
        "api_key": "9f41a468-2b7c-4c18-bbc9-54bce231b024"
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data['data']

# Obter dados históricos da API
data = get_data_from_api()

# Converter os dados em um DataFrame
df = pd.DataFrame(data)

# Corrigir os tipos de dados
df['date'] = pd.to_numeric(df['date'], errors='coerce')
df['generation_twh'] = pd.to_numeric(df['generation_twh'], errors='coerce')

# Separar os dados por tipo de energia
energy_types = df['series'].unique()
energy_data = {etype: df[df['series'] == etype] for etype in energy_types}

# Função para projetar os dados para anos futuros
def project_data(edata, years_ahead):
    model = LinearRegression()
    X = edata['date'].values.reshape(-1, 1)
    y = edata['generation_twh'].values
    model.fit(X, y)
    last_year = edata['date'].max()
    future_years = np.arange(last_year + 1, last_year + 1 + years_ahead).reshape(-1, 1)
    future_predictions = model.predict(future_years)
    future_df = pd.DataFrame({
        'date': future_years.flatten(),
        'generation_twh': future_predictions
    })
    return future_df

# Layout do aplicativo Dash
app.layout = html.Div([
    html.H1("Projeção de Geração de Eletricidade e Lixo no Brasil"),
    dcc.Graph(id="generation-by-type-graph"),
    dcc.Graph(id="waste-generation-graph"),
    dcc.Slider(
        id="years-slider",
        min=1,
        max=10,
        step=1,
        value=5,
        marks={i: str(i) for i in range(1, 11)},
    ),
    html.Div(id="slider-output-container"),
    html.Div([
        html.A("Baixar Dados dos Gráficos", id="download-link", download="dados_graficos.csv", href="", target="_blank", className="download-button")
    ])
])

# Callback para atualizar o gráfico de geração de eletricidade por tipo
@app.callback(
    dash.dependencies.Output("generation-by-type-graph", "figure"),
    dash.dependencies.Input("years-slider", "value")
)
def update_generation_by_type_graph(years_ahead):
    traces = []
    for etype, edata in energy_data.items():
        traces.append(go.Scatter(
            x=edata['date'],
            y=edata['generation_twh'],
            mode='lines+markers',
            name=f"{etype} (Histórico)",
            line={'width': 2}
        ))
        future_df = project_data(edata, years_ahead)
        traces.append(go.Scatter(
            x=future_df['date'],
            y=future_df['generation_twh'],
            mode='lines',
            name=f"{etype} (Projeção)",
            line={'dash': 'dash', 'width': 2}
        ))
    return {
        'data': traces,
        'layout': go.Layout(
            title="Geração de Eletricidade por Tipo no Brasil",
            xaxis={'title': 'Ano'},
            yaxis={'title': 'Geração (TWh)'},
            showlegend=True
        )
    }

# Callback para atualizar o gráfico de geração de lixo
@app.callback(
    dash.dependencies.Output("waste-generation-graph", "figure"),
    dash.dependencies.Input("years-slider", "value")
)
def update_waste_graph(years_ahead):
    df['solar_waste'] = df['generation_twh'] * 1000 * 20
    df['wind_waste'] = df['generation_twh'] * 1000 * 15
    df['hydro_waste'] = df['generation_twh'] * 1000 * 10
    df['bio_waste'] = df['generation_twh'] * 1000 * 30
    return {
        'data': [
            go.Bar(x=df['date'], y=df['solar_waste'], name='Solar', marker_color='yellow'),
            go.Bar(x=df['date'], y=df['wind_waste'], name='Eólica', marker_color='green'),
            go.Bar(x=df['date'], y=df['hydro_waste'], name='Hidrelétrica', marker_color='blue'),
            go.Bar(x=df['date'], y=df['bio_waste'], name='Bioenergia', marker_color='orange')
        ],
        'layout': go.Layout(
            title="Geração de Lixo por Tipo de Energia",
            xaxis={'title': 'Ano'},
            yaxis={'title': 'Geração de Lixo (kg)'},
            barmode='stack',
            showlegend=True
        )
    }

# Callback para atualizar o texto do slider
@app.callback(
    dash.dependencies.Output("slider-output-container", "children"),
    dash.dependencies.Input("years-slider", "value")
)
def update_slider_output(value):
    return f"Projeção para {value} anos à frente."

# Callback para gerar o link de download
@app.callback(
    dash.dependencies.Output("download-link", "href"),
    dash.dependencies.Input("years-slider", "value")
)
def update_download_link(years_ahead):
    all_data = []
    for etype, edata in energy_data.items():
        edata['type'] = etype
        edata['projection'] = 'Histórico'
        future_df = project_data(edata, years_ahead)
        future_df['type'] = etype
        future_df['projection'] = 'Projeção'
        all_data.append(pd.concat([edata, future_df]))
    combined_data = pd.concat(all_data)
    csv_string = combined_data.to_csv(index=False, encoding='utf-8')
    return f"data:text/csv;charset=utf-8,{csv_string}"

# Rodar o servidor do Dash
if __name__ == "__main__":
    app.run_server(debug=True)
