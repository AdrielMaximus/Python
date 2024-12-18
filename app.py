import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import requests
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
import os
from flask import send_file

app = dash.Dash(
    __name__,
    external_scripts=[{"src": "https://cdn.tailwindcss.com"}],
)
app.scripts.config.serve_locally = True
app.title = "Enerlyze"

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

data = get_data_from_api()
df = pd.DataFrame(data)
df['date'] = pd.to_numeric(df['date'], errors='coerce')
df['generation_twh'] = pd.to_numeric(df['generation_twh'], errors='coerce')
energy_types = df['series'].unique()
energy_data = {etype: df[df['series'] == etype] for etype in energy_types}

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

app.layout = html.Div(
    className="bg-indigo-950",
    children=[
        html.Div(
            className="h-screen w-full flex justify-center items-center",
            id="initial-screen",
            children=[
                html.Div(
                    className="p-4 md:p-8 lg:p-16 xl:p-20 flex flex-col items-center",
                    children=[
                        html.H1(
                            "Bem-vindo ao Enerlyze, clique em iniciar para começar",
                            className="text-2xl font-bold mb-4 text-cyan-100 uppercase text-center",
                        ),
                        html.Button(
                            "Iniciar", 
                            id="start-button", 
                            n_clicks=0,
                            className="bg-blue-800 uppercase font-bold text-cyan-100 px-6 py-2 rounded-lg shadow-md hover:bg-blue-600 transition-all"
                        )
                    ]
                )
            ], style={'display': 'block'}
        ),
        html.Div(
            id="content-screen",
            className="p-4 md:p-8 lg:p-16 xl:p-20",
            children=[
                html.Div(
                    className="flex mx-auto justify-between",
                    children=[
                        html.Div(
                            className="text-left",
                            children=[
                                html.H1(
                                    children="Projeção de Geração de Eletricidade e Lixo no Brasil",
                                    className="text-2xl font-bold mb-4 text-cyan-100 uppercase",
                                ),
                                html.H2(
                                    children="Enerlyze",
                                    className="text-l font-bold text-cyan-100 uppercase",
                                ),
                            ]    
                        ),
                        html.Div(
                            className="my-auto",
                            children=[
                                html.A(
                                    "Baixar Projeções", 
                                    id="download-link", 
                                    download="projecao_energia.csv", 
                                    href="/static/projecao_energia.csv", 
                                    target="_blank", 
                                    className="bg-blue-800 text-cyan-100 px-6 py-2 rounded-lg shadow-md hover:bg-blue-600 transition-all mr-4"
                                ),
                                html.Button(
                                    "Voltar", 
                                    id="back-button", 
                                    n_clicks=0,
                                    className="bg-blue-800 text-cyan-100 px-6 py-2 rounded-lg shadow-md hover:bg-blue-600 transition-all"
                                ),
                            ]
                        ),
                    ]
                ),
                html.Div(
                    className="flex",
                    children=[
                        html.Div(
                            className="flex-1 bg-blue-800 p-2 rounded-lg min-w-[300px] my-8 lg:my-16 mr-4",
                            children=dcc.Graph(id="generation-by-type-graph"),
                        ),
                        html.Div(
                            className="flex-1 bg-blue-800 p-2 rounded-lg min-w-[300px] my-8 lg:my-16",
                            children=dcc.Graph(id="waste-generation-graph"),
                        ),
                    ],
                ),
            ],
            style={'display': 'none'}
        )
    ]
)

@app.callback(
    [Output("initial-screen", "style"),
     Output("content-screen", "style"),
     Output("generation-by-type-graph", "figure"),
     Output("waste-generation-graph", "figure")],
    [Input("start-button", "n_clicks"),
     Input("back-button", "n_clicks")],
    [State("initial-screen", "style"),
     State("content-screen", "style")]
)
def toggle_screens(start_clicks, back_clicks, initial_style, content_style):
    ctx = dash.callback_context
    if not ctx.triggered:
        return initial_style, content_style, {}, {}

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "start-button":
        return {'display': 'none'}, {'display': 'block'}, update_generation_by_type_graph(), update_waste_graph()
    elif button_id == "back-button":
        return {'display': 'block'}, {'display': 'none'}, {}, {}

    return initial_style, content_style, {}, {}

def update_generation_by_type_graph():
    traces = []
    for etype, edata in energy_data.items():
        traces.append(go.Scatter(
            x=edata['date'],
            y=edata['generation_twh'],
            mode='lines+markers',
            name=f"{etype} (Histórico)",
            line={'width': 2}
        ))
        future_df = project_data(edata, years_ahead=5)
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
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            font=dict(color="cyan"),
            xaxis={'title': 'Ano'},
            yaxis={'title': 'Geração (TWh)'},
            legend=dict(
                orientation="h",
                x=0.5,
                xanchor="center",
                y=-0.5,
                bgcolor="rgba(0, 0, 0, 0)"
            ),
            showlegend=True
        )
    }

def update_waste_graph():
    df['solar_waste'] = df['generation_twh'] * 1000 * 20
    df['wind_waste'] = df['generation_twh'] * 1000 * 15
    df['hydro_waste'] = df['generation_twh'] * 1000 * 10
    df['bio_waste'] = df['generation_twh'] * 1000 * 30

    df_grouped = df.groupby('date').agg({
        'solar_waste': 'sum',
        'wind_waste': 'sum',
        'hydro_waste': 'sum',
        'bio_waste': 'sum'
    }).reset_index()

    return {
        'data': [
            go.Bar(
                x=df_grouped['date'],
                y=df_grouped['solar_waste'],
                name='Solar',
                marker_color='yellow',
                hoverinfo='x+y',
                width=0.8,
            ),
            go.Bar(
                x=df_grouped['date'],
                y=df_grouped['wind_waste'],
                name='Eólica',
                marker_color='green',
                hoverinfo='x+y',
                width=0.8,
            ),
            go.Bar(
                x=df_grouped['date'],
                y=df_grouped['hydro_waste'],
                name='Hidrelétrica',
                marker_color='gray',  # Mudança para cinza
                hoverinfo='x+y',
                width=0.8,
            ),
            go.Bar(
                x=df_grouped['date'],
                y=df_grouped['bio_waste'],
                name='Biomassa',
                marker_color='brown',
                hoverinfo='x+y',
                width=0.8,
            ),
        ],
        'layout': go.Layout(
            barmode='stack',
            title='Projeção de Resíduos',
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            font=dict(color="cyan"),
            xaxis={'title': 'Ano'},
            yaxis={'title': 'Resíduos (kg)'}
        )
    }

if __name__ == "__main__":
    app.run(debug=True)
