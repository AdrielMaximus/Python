import requests
import pandas as pd
import xlsxwriter

class APIClient:
    def __init__(self, url, headers=None):
        self.url = url
        self.headers = headers

    def coletar_dados(self):
        try:
            resposta = requests.get(self.url, headers=self.headers)
            resposta.raise_for_status()
            dados = resposta.json()
            return pd.DataFrame(dados['data'])
        except requests.exceptions.RequestException as e:
            print(f"Erro ao acessar a API: {e}")
            return None
        except ValueError as e:
            print(f"Erro ao converter dados para JSON: {e}")
            return None

class DashboardGenerator:
    def __init__(self, dataframes, nome_arquivo='dashboard_enerlyze.xlsx'):
        self.dataframes = dataframes
        self.nome_arquivo = nome_arquivo

    def gerar_excel_com_graficos(self):
        with pd.ExcelWriter(self.nome_arquivo, engine='xlsxwriter') as writer:
            for nome, df in self.dataframes.items():
                df.to_excel(writer, sheet_name=nome, index=False, startrow=15, startcol=0)
                workbook = writer.book
                worksheet = writer.sheets[nome]

                chart = workbook.add_chart({'type': 'line'})

                if nome == 'Carbon Intensity' and 'date' in df.columns and 'emissions_intensity_gco2_per_kwh' in df.columns:
                    chart.add_series({
                        'name': 'Carbon Intensity (gCO2/kWh)',
                        'categories': [nome, 16, df.columns.get_loc('date'), 15 + len(df), df.columns.get_loc('date')],
                        'values': [nome, 16, df.columns.get_loc('emissions_intensity_gco2_per_kwh'), 15 + len(df), df.columns.get_loc('emissions_intensity_gco2_per_kwh')],
                    })
                    chart.set_title({'name': 'Carbon Intensity ao longo dos anos'})
                    chart.set_x_axis({'name': 'Ano'})
                    chart.set_y_axis({'name': 'gCO2/kWh'})

                elif nome == 'Electricity Generation' and 'date' in df.columns and 'series' in df.columns:
                    for serie in df['series'].unique():
                        df_serie = df[df['series'] == serie]
                        chart.add_series({
                            'name': f'Geração {serie} (TWh)',
                            'categories': [nome, 16, df.columns.get_loc('date'), 15 + len(df_serie), df.columns.get_loc('date')],
                            'values': [nome, 16, df.columns.get_loc('generation_twh'), 15 + len(df_serie), df.columns.get_loc('generation_twh')],
                        })
                    chart.set_title({'name': 'Geração de Eletricidade por Origem'})
                    chart.set_x_axis({'name': 'Ano'})
                    chart.set_y_axis({'name': 'TWh'})

                elif nome == 'Power Sector Emissions' and 'date' in df.columns and 'series' in df.columns:
                    for serie in df['series'].unique():
                        df_serie = df[df['series'] == serie]
                        chart.add_series({
                            'name': f'Emissões {serie} (MtCO2)',
                            'categories': [nome, 16, df.columns.get_loc('date'), 15 + len(df_serie), df.columns.get_loc('date')],
                            'values': [nome, 16, df.columns.get_loc('emissions_mtco2'), 15 + len(df_serie), df.columns.get_loc('emissions_mtco2')],
                        })
                    chart.set_title({'name': 'Emissões do Setor Energético'})
                    chart.set_x_axis({'name': 'Ano'})
                    chart.set_y_axis({'name': 'MtCO2'})

                elif nome == 'Electricity Demand' and 'date' in df.columns:
                    chart.add_series({
                        'name': 'Demanda (TWh)',
                        'categories': [nome, 16, df.columns.get_loc('date'), 15 + len(df), df.columns.get_loc('date')],
                        'values': [nome, 16, df.columns.get_loc('demand_twh'), 15 + len(df), df.columns.get_loc('demand_twh')],
                    })
                    chart.add_series({
                        'name': 'Demanda per capita (MWh)',
                        'categories': [nome, 16, df.columns.get_loc('date'), 15 + len(df), df.columns.get_loc('date')],
                        'values': [nome, 16, df.columns.get_loc('demand_mwh_per_capita'), 15 + len(df), df.columns.get_loc('demand_mwh_per_capita')],
                    })
                    chart.set_title({'name': 'Demanda de Eletricidade'})
                    chart.set_x_axis({'name': 'Ano'})
                    chart.set_y_axis({'name': 'TWh e MWh per capita'})

                chart.set_legend({'position': 'bottom'})
                worksheet.insert_chart('A1', chart, {'x_scale': 2, 'y_scale': 1.5})

        print(f'Dashboard com gráficos gerado: {self.nome_arquivo}')

class Application:
    def __init__(self, urls_apis):
        self.urls_apis = urls_apis
        self.dataframes = {}

    def executar(self):
        for nome_api, url_api in self.urls_apis.items():
            cliente_api = APIClient(url_api)
            dados_coletados = cliente_api.coletar_dados()
            if dados_coletados is not None:
                self.dataframes[nome_api] = dados_coletados

        if self.dataframes:
            gerador_dashboard = DashboardGenerator(self.dataframes)
            gerador_dashboard.gerar_excel_com_graficos()

if __name__ == "__main__":
    urls_apis = {
        'Carbon Intensity': 'https://api.ember-energy.org/v1/carbon-intensity/yearly?entity_code=BRA&start_date=1990&api_key=9f41a468-2b7c-4c18-bbc9-54bce231b024',
        'Electricity Generation': 'https://api.ember-energy.org/v1/electricity-generation/yearly?entity_code=BRA&is_aggregate_series=false&start_date=1990&api_key=9f41a468-2b7c-4c18-bbc9-54bce231b024',
        'Power Sector Emissions': 'https://api.ember-energy.org/v1/power-sector-emissions/yearly?entity_code=BRA&series=Coal,Gas&start_date=2000&api_key=9f41a468-2b7c-4c18-bbc9-54bce231b024',
        'Electricity Demand': 'https://api.ember-energy.org/v1/electricity-demand/yearly?entity=Brazil&entity_code=BRA&start_date=2000&include_all_dates_value_range=false&api_key=9f41a468-2b7c-4c18-bbc9-54bce231b024'
    }

    app = Application(urls_apis)
    app.executar()
