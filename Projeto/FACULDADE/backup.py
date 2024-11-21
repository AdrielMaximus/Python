import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
import requests

# Classe para acessar as APIs e coletar dados
class APIClient:
    def __init__(self, url, headers=None):
        self.url = url
        self.headers = headers

    def coletar_dados(self):
        try:
            resposta = requests.get(self.url, headers=self.headers)
            resposta.raise_for_status()
            dados = resposta.json()
            print(dados)  # Verifica os dados retornados pela API
            return pd.DataFrame(dados['data'])
        except requests.exceptions.RequestException as e:
            print(f"Erro ao acessar a API: {e}")
            return None
        except ValueError as e:
            print(f"Erro ao converter dados para JSON: {e}")
            return None

# URLs das APIs
urls_apis = {
    'Carbon Intensity': 'https://api.ember-energy.org/v1/carbon-intensity/yearly?entity_code=BRA&start_date=1990&api_key=9f41a468-2b7c-4c18-bbc9-54bce231b024',
    'Electricity Generation': 'https://api.ember-energy.org/v1/electricity-generation/yearly?entity_code=BRA&is_aggregate_series=false&start_date=1990&api_key=9f41a468-2b7c-4c18-bbc9-54bce231b024',
    'Power Sector Emissions': 'https://api.ember-energy.org/v1/power-sector-emissions/yearly?entity_code=BRA&series=Coal,Gas&start_date=2000&api_key=9f41a468-2b7c-4c18-bbc9-54bce231b024',
    'Electricity Demand': 'https://api.ember-energy.org/v1/electricity-demand/yearly?entity=Brazil&entity_code=BRA&start_date=2000&include_all_dates_value_range=false&api_key=9f41a468-2b7c-4c18-bbc9-54bce231b024'
}

# Inicializando o app Dash
app = dash.Dash(__name__)

# Layout com filtros e gráficos
app.layout = html.Div([
    html.H1("Energy Generation by Source"),
    dcc.Dropdown(
        id='dataset-dropdown',
        options=[
            {'label': 'Generation - Yearly', 'value': 'Electricity Generation'},
            {'label': 'Emissions - Yearly', 'value': 'Power Sector Emissions'},
            {'label': 'Carbon Intensity', 'value': 'Carbon Intensity'},
            {'label': 'Electricity Demand', 'value': 'Electricity Demand'},
        ],
        value='Electricity Generation', 
    ),
    dcc.Dropdown(
        id='fuel-dropdown',
        options=[
            {'label': 'Solar', 'value': 'Solar'},
            {'label': 'Wind', 'value': 'Wind'},
            {'label': 'Coal', 'value': 'Coal'},
            {'label': 'Hydro', 'value': 'Hydro'},
            {'label': 'Other Renewables', 'value': 'Other Renewables'}
        ],
        value='Solar', 
    ),
    dcc.Dropdown(
        id='chart-type-dropdown',
        options=[
            {'label': 'Area', 'value': 'area'},
            {'label': 'Line', 'value': 'line'},
            {'label': 'Map', 'value': 'map'}
        ],
        value='area',  
    ),
    dcc.Graph(id='generation-chart')
])

# Callback para atualizar o gráfico com base nos filtros
@app.callback(
    dash.dependencies.Output('generation-chart', 'figure'),
    [dash.dependencies.Input('dataset-dropdown', 'value'),
     dash.dependencies.Input('fuel-dropdown', 'value'),
     dash.dependencies.Input('chart-type-dropdown', 'value')]
)
def update_graph(dataset, fuel, chart_type):
    # Acesse a URL da API para coletar os dados
    api_url = urls_apis.get(dataset)
    api_client = APIClient(api_url)
    df = api_client.coletar_dados()

    if df is not None:
        # Converte a coluna 'date' para o formato datetime
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])  # Remove linhas com datas inválidas

        # Verifica se a coluna de combustível existe
        if fuel in df.columns:
            if chart_type == 'area':
                fig = px.area(df, x='date', y=fuel, title=f'{fuel} Generation over the Years')
            elif chart_type == 'line':
                fig = px.line(df, x='date', y=fuel, title=f'{fuel} Generation over the Years')
            else:
                fig = px.scatter_geo(df, locations="date", color=fuel, title=f'{fuel} Generation over the Years')
            
            return fig
        else:
            return {}  # Se o combustível não existir, retorna gráfico vazio
    else:
        return {}  # Se não for possível coletar os dados

# Execução do Dash App
if __name__ == '__main__':
    app.run_server(debug=True)
