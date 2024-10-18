#import requests
#import pandas as pd

# Função para coletar dados da API
def coletar_dados_api(url_api, headers=None):
    try:
        #resposta = requests.get(url_api, headers=headers)
        #resposta.raise_for_status()  # Verifica se a requisição foi bem-sucedida
        #dados = resposta.json()  # Converte a resposta em JSON

        # Adaptar a extração de dados conforme a estrutura do JSON retornado pela API
        # Supondo que os dados estejam em uma chave chamada 'data'
        #df = pd.DataFrame(dados['data'])  # Altere 'data' para a chave correta
        #return df
    #except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a API: {e}")
        return None
    except ValueError as e:
        print(f"Erro ao converter dados para JSON: {e}")
        return None

# Função para gerar o relatório CSV
def gerar_relatorio(dados, nome_arquivo='relatorio_enerlyze.csv'):
    dados.to_csv(nome_arquivo, index=False)
    print(f'Relatório gerado: {nome_arquivo}')

# Simulação do fluxo principal
if __name__ == "__main__":
    url_api = 'https://ember-climate.org/data/data-tools/data-explorer/'  # URL da API
    # Se a API requerer autenticação, você pode definir os headers aqui
    headers = {
         #'Authorization': Bearer '9f41a468-2b7c-4c18-bbc9-54bce231b024'  # Descomente e substitua pelo seu token, se necessário
    }

    dados_coletados = coletar_dados_api(url_api, headers)  # Coleta de dados da API

    if dados_coletados is not None:
        gerar_relatorio(dados_coletados)  # Gera o relatório em CSV
