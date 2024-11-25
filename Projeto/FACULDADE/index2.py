import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import requests
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

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
    html.Div(
        id="initial-screen",
        children=[
            html.H1("Bem vindo ao enerlyze, clique em iniciar para começar"),
            html.Button("Iniciar", id="start-button", n_clicks=0)
        ],
        style={'display': 'block'}  # Inicialmente exibe a tela de boas-vindas
    ),
    
    html.Div(
        id="content-screen",
        children=[
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
            ]),
            html.Button("Voltar", id="back-button", n_clicks=0)
        ],
        style={'display': 'none'}  # Inicialmente oculta a tela de conteúdo
    )
])

# Callback para alternar entre a tela inicial e a tela de conteúdo
@app.callback(
    [Output("initial-screen", "style"),
     Output("content-screen", "style"),
     Output("generation-by-type-graph", "figure"),
     Output("waste-generation-graph", "figure")],
    [Input("start-button", "n_clicks"),
     Input("back-button", "n_clicks"),
     Input("years-slider", "value")],
    [State("initial-screen", "style"),
     State("content-screen", "style")]
)
def toggle_screens(start_clicks, back_clicks, years_ahead, initial_style, content_style):
    ctx = dash.callback_context
    if not ctx.triggered:
        return initial_style, content_style, {}, {}

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "start-button":
        # Quando o botão Iniciar for pressionado, exibe a tela de conteúdo e oculta a tela inicial
        return {'display': 'none'}, {'display': 'block'}, update_generation_by_type_graph(years_ahead), update_waste_graph(years_ahead)
    elif button_id == "back-button":
        # Quando o botão Voltar for pressionado, exibe a tela inicial e oculta a tela de conteúdo
        return {'display': 'block'}, {'display': 'none'}, {}, {}
    
    return initial_style, content_style, {}, {}

# Função para atualizar o gráfico de geração de eletricidade por tipo
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

# Função para atualizar o gráfico de geração de lixo
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

# Rodar o servidor do Dash
if __name__ == "__main__":
    app.run_server(debug=True)
