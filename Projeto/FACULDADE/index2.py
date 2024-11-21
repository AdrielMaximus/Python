import dash
from dash import dcc, html
import plotly.graph_objs as go
import requests
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

# Inicializar o aplicativo Dash
app = dash.Dash(__name__)

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

# Função para calcular a projeção com base nos dados históricos
def project_future(data, years_ahead):
    # Preparar os dados para a regressão
    df = pd.DataFrame(data)
    df['date'] = pd.to_numeric(df['date'], errors='coerce')
    df['generation_twh'] = pd.to_numeric(df['generation_twh'], errors='coerce')

    # Ajustar a regressão linear
    model = LinearRegression()
    model.fit(df[['date']], df['generation_twh'])

    # Fazer a projeção para os próximos anos
    last_year = df['date'].max()
    future_years = np.array(range(last_year + 1, last_year + 1 + years_ahead)).reshape(-1, 1)
    future_predictions = model.predict(future_years)

    # Criar um novo DataFrame com as projeções
    projected_data = pd.DataFrame({
        'date': future_years.flatten(),
        'generation_twh': future_predictions
    })

    return projected_data

# Obter dados históricos da API
data = get_data_from_api()

# Layout do aplicativo Dash
app.layout = html.Div([
    html.H1("Projeção de Geração de Eletricidade no Brasil"),
    
    # Gráfico de geração histórica e projeção
    dcc.Graph(id="generation-graph"),
    
    # Seleção de anos à frente para projeção
    dcc.Slider(
        id="years-slider",
        min=1,
        max=10,
        step=1,
        value=5,
        marks={i: str(i) for i in range(1, 11)},
    ),
    
    html.Div(id="slider-output-container")
])

# Callback para atualizar o gráfico com base na seleção do usuário
@app.callback(
    dash.dependencies.Output("generation-graph", "figure"),
    dash.dependencies.Input("years-slider", "value")
)
def update_graph(years_ahead):
    # Fazer a projeção com base nos dados históricos
    projected_data = project_future(data, years_ahead)

    # Preparar os dados históricos e projetados para o gráfico
    df = pd.DataFrame(data)
    historical_data = df[['date', 'generation_twh']]

    # Gráfico empilhado com diferentes fontes de geração
    trace3 = go.Scatter(
        x=historical_data['date'],
        y=historical_data['generation_twh']*0.2,  # Exemplo de divisão das fontes
        mode='none',
        stackgroup='one',
        name='Wind',
        fillcolor='green'
    )
    
    trace4 = go.Scatter(
        x=historical_data['date'],
        y=historical_data['generation_twh']*0.2,  # Exemplo de divisão das fontes
        mode='none',
        stackgroup='one',
        name='Solar',
        fillcolor='lightgreen'
    )
    
    trace5 = go.Scatter(
        x=historical_data['date'],
        y=historical_data['generation_twh']*0.2,  # Exemplo de divisão das fontes
        mode='none',
        stackgroup='one',
        name='Bioenergy',
        fillcolor='orange'
    )
    
    trace6 = go.Scatter(
        x=historical_data['date'],
        y=historical_data['generation_twh']*0.2,  # Exemplo de divisão das fontes
        mode='none',
        stackgroup='one',
        name='Other Renewables',
        fillcolor='lightblue'
    )

    trace1 = go.Scatter(
        x=historical_data['date'],
        y=historical_data['generation_twh'],
        mode='lines+markers',
        name='Histórico',
        line={'color': 'blue'}
    )

    trace2 = go.Scatter(
        x=projected_data['date'],
        y=projected_data['generation_twh'],
        mode='lines+markers',
        name='Projeção Futura',
        line={'color': 'orange'}
    )

    figure = {
        'data': [trace1, trace2, trace3, trace4, trace5, trace6],
        'layout': go.Layout(
            title="Geração de Eletricidade no Brasil",
            xaxis={'title': 'Ano'},
            yaxis={'title': 'Geração (TWh)'},
            showlegend=True
        )
    }

    return figure

# Callback para atualizar o texto do slider
@app.callback(
    dash.dependencies.Output("slider-output-container", "children"),
    dash.dependencies.Input("years-slider", "value")
)
def update_slider_output(value):
    return f"Projeção para {value} anos à frente."

# Rodar o servidor do Dash
if __name__ == "__main__":
    app.run_server(debug=True)
