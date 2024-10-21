import requests
import pandas as pd

# Função para coletar dados da API e retornar um DataFrame
def coletar_dados_api(url_api, headers=None):
    try:
        resposta = requests.get(url_api, headers=headers)
        resposta.raise_for_status()  # Verifica se a requisição foi bem-sucedida
        dados = resposta.json()  # Converte a resposta em JSON

        # Verifique como os dados estão estruturados. Supondo que os dados relevantes estejam na chave 'data'.
        # Ajuste 'data' se necessário para se adaptar à estrutura da sua API.
        df = pd.DataFrame(dados['data'])  # Substitua 'data' pela chave correta
        return df
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a API: {e}")
        return None
    except ValueError as e:
        print(f"Erro ao converter dados para JSON: {e}")
        return None

# Função para gerar o dashboard em Excel
def gerar_dashboard_excel(dataframes, nome_arquivo='dashboard_enerlyze.xlsx'):
    with pd.ExcelWriter(nome_arquivo, engine='xlsxwriter') as writer:
        for nome, df in dataframes.items():
            df.to_excel(writer, sheet_name=nome, index=False)
    print(f'Dashboard gerado: {nome_arquivo}')

# Simulação do fluxo principal
if __name__ == "__main__":
    # URLs das APIs
    urls_apis = {
        'Carbon Intensity': 'https://api.ember-energy.org/v1/carbon-intensity/yearly?entity_code=BRA&start_date=1990&api_key=9f41a468-2b7c-4c18-bbc9-54bce231b024',
        'Electricity Generation': 'https://api.ember-energy.org/v1/electricity-generation/yearly?entity_code=BRA&is_aggregate_series=false&start_date=1990&api_key=9f41a468-2b7c-4c18-bbc9-54bce231b024',
        'Power Sector Emissions': 'https://api.ember-energy.org/v1/power-sector-emissions/yearly?entity_code=BRA&series=Coal,Gas&start_date=2000&api_key=9f41a468-2b7c-4c18-bbc9-54bce231b024',
        'Electricity Demand': 'https://api.ember-energy.org/v1/electricity-demand/yearly?entity=Brazil&entity_code=BRA&start_date=2000&include_all_dates_value_range=false&api_key=9f41a468-2b7c-4c18-bbc9-54bce231b024'
    }

    # Dicionário para armazenar os DataFrames
    dataframes = {}

    # Coleta de dados de cada API e armazenamento no dicionário
    for nome_api, url_api in urls_apis.items():
        dados_coletados = coletar_dados_api(url_api)
        if dados_coletados is not None:
            dataframes[nome_api] = dados_coletados

    # Gera o arquivo Excel com várias abas
    if dataframes:
        gerar_dashboard_excel(dataframes)
