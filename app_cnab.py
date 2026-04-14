import streamlit as st
import pandas as pd
import io
from datetime import datetime

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(page_title="Hub Operacional FIDC - VIZ Gestora", layout="wide", initial_sidebar_state="expanded")

st.sidebar.title("🛠️ Ferramentas FIDC")
opcao_menu = st.sidebar.radio(
    "Escolha a operação desejada:",
    ["📊 1. Validador CNAB", "🔍 2. Leitor CNAB", "⚙️ 3. Gerador CNAB"]
)
st.sidebar.markdown("---")
st.sidebar.info("Sistema de processamento posicional padrão CNAB 444.")

# ==============================================================================
# DICIONÁRIO DE LAYOUT 444 (Com Coluna do Cedente Dividida)
# ==============================================================================
# Ordem: (Nome da Coluna, Tamanho, Tipo, Alinhamento, Highlight_Amarelo?)
LAYOUT_444 = [
    ("01_ID_Registro", 1, 'str', 'ljust', True),
    ("02_Debito_Automatico", 19, 'str', 'rjust', False),
    ("03_Coobrigacao", 2, 'str', 'zeros', True),
    ("04_Caract_Especial", 2, 'str', 'zeros', False),
    ("05_Modalidade", 4, 'str', 'zeros', True),
    ("06_Natureza", 2, 'str', 'zeros', False),
    ("07_Origem_Recurso", 4, 'str', 'zeros', False),
    ("08_Classe_Risco", 2, 'str', 'rjust', False),
    ("09_Zeros", 1, 'str', 'zeros', False),
    ("10_Num_Controle", 25, 'str', 'ljust', True),
    ("11_Num_Banco", 3, 'str', 'zeros', False),
    ("12_Zeros", 5, 'str', 'zeros', False),
    ("13_ID_Titulo_Banco", 11, 'str', 'rjust', False),
    ("14_Digito_Nosso_Num", 1, 'str', 'rjust', False),
    ("15_Valor_Pago", 10, 'float', 'zeros', True),
    ("16_Condicao_Papeleta", 1, 'str', 'rjust', False),
    ("17_Emite_Papeleta", 1, 'str', 'rjust', False),
    ("18_Data_Liquidacao", 6, 'str', 'zeros', True),
    ("19_ID_Operacao_Banco", 4, 'str', 'rjust', False),
    ("20_Ind_Rateio", 1, 'str', 'rjust', False),
    ("21_End_Aviso_Debito", 1, 'str', 'zeros', False),
    ("22_Branco", 2, 'str', 'rjust', False),
    ("23_Ocorrencia", 2, 'str', 'zeros', True),
    ("24_Num_Documento", 10, 'str', 'rjust', True),
    ("25_Data_Vencimento", 6, 'str', 'zeros', True),
    ("26_Valor_Titulo", 13, 'float', 'zeros', True),
    ("27_Banco_Cobranca", 3, 'str', 'zeros', False),
    ("28_Agencia_Deposit", 5, 'str', 'zeros', False),
    ("29_Especie_Titulo", 2, 'str', 'zeros', True),
    ("30_Identificacao", 1, 'str', 'rjust', False),
    ("31_Data_Emissao", 6, 'str', 'zeros', True),
    ("32_Instrucao_1", 2, 'str', 'zeros', True),
    ("33_Instrucao_2", 1, 'str', 'zeros', True),
    ("34_Tipo_Pessoa_Ced", 2, 'str', 'zeros', True),
    ("35_Zeros", 12, 'str', 'zeros', False),
    ("36_Num_Termo_Cessao", 19, 'str', 'ljust', True),
    ("37_Valor_Aquisicao", 13, 'float', 'zeros', True),
    ("38_Valor_Abatimento", 13, 'float', 'zeros', False),
    ("39_Tipo_Insc_Sacado", 2, 'str', 'zeros', True),
    ("40_Insc_Sacado", 14, 'str', 'zeros', True),
    ("41_Nome_Sacado", 40, 'str', 'ljust', True),
    ("42_Endereco_Sacado", 40, 'str', 'ljust', False),
    ("43_Num_NF_Duplicata", 9, 'str', 'rjust', False),
    ("44_Serie_NF", 3, 'str', 'rjust', False),
    ("45_CEP_Sacado", 8, 'str', 'zeros', False),
    ("46_Nome_Cedente", 46, 'str', 'ljust', True),
    ("47_CNPJ_Cedente", 14, 'str', 'zeros', True),
    ("48_Chave_NF", 44, 'str', 'rjust', False),
    ("49_Seq_Registro", 6, 'seq', 'zeros', False)
]

# ==============================================================================
# FUNÇÕES DE FORMATAÇÃO E EXCEL
# ==============================================================================
def str_para_valor(texto):
    texto = texto.strip()
    if not texto.isdigit(): return 0.0
    return float(texto) / 100

def processar_string_cnab(valor, tamanho, alinhamento):
    val = str(valor).strip()
    if val in ('nan', 'None'): val = ''
    if val.endswith('.0'): val = val[:-2]
    
    if alinhamento == 'zeros':
        return val.zfill(tamanho)[:tamanho]
    elif alinhamento == 'ljust':
        return val.ljust(tamanho)[:tamanho]
    else: # rjust
        return val.rjust(tamanho)[:tamanho]

def processar_float_cnab(valor, tamanho):
    val = str(valor).strip()
    if val in ('nan', 'None', ''):
        v_float = 0.0
    else:
        try:
            if ',' in val:
                val = val.replace('.', '').replace(',', '.')
            v_float = float(val)
        except ValueError:
            v_float = 0.0
    return f"{v_float:.2f}".replace(".", "").zfill(tamanho)[:tamanho]

def salvar_excel_formatado(df, sheet_name='Titulos'):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        
        fmt_texto = workbook.add_format({'num_format': '@'})
        fmt_header_prior = workbook.add_format({'bold': True, 'bg_color': '#FFFF99', 'border': 1, 'num_format': '@'})
        fmt_header_std = workbook.add_format({'bold': True, 'border': 1, 'num_format': '@'})

        for col_num, (col_nome, _, _, _, highlight) in enumerate(LAYOUT_444):
            worksheet.set_column(col_num, col_num, 20, fmt_texto)
            worksheet.write(0, col_num, col_nome, fmt_header_prior if highlight else fmt_header_std)
            
    return buffer.getvalue()

# ==============================================================================
# MÓDULOS DO HUB
# ==============================================================================
if opcao_menu == "📊 1. Validador CNAB":
    st.title("📊 Validador de Arquivos CNAB 444")
    st.markdown("Cruza os valores de **Aquisição vs Nominal** e aponta as divergências do lote.")
    arquivo_upado = st.file_uploader("Upload do ficheiro (.REM ou .TXT)", type=["rem", "txt", "REM", "TXT"])

    if arquivo_upado is not None:
        titulos = []
        linhas = arquivo_upado.getvalue().decode("utf-8", errors="ignore").splitlines()
        barra_progresso = st.progress(0)
        
        for num_linha, linha in enumerate(linhas, start=1):
            if len(linha.strip()) == 0: continue
            linha = linha.ljust(444)
            
            if linha[0] == '1': 
                valor_titulo = str_para_valor(linha[126:139])
                valor_aquisicao = str_para_valor(linha[192:205])
                status_validacao = 'NOK' if valor_aquisicao > valor_titulo else 'OK'
                
                titulos.append({
                    "Linha": num_linha,
                    "Num_Controle": linha[37:62].strip(),
                    "Valor_Titulo": valor_titulo,
                    "Valor_Aquisicao": valor_aquisicao,
                    "Diferenca (Spread)": valor_titulo - valor_aquisicao,
                    "Validacao (Titulo >= Aquisicao)": status_validacao
                })
            barra_progresso.progress(num_linha / len(linhas))
                
        df_detalhe = pd.DataFrame(titulos)
        
        if not df_detalhe.empty:
            total_titulo = df_detalhe['Valor_Titulo'].sum()
            total_aquisicao = df_detalhe['Valor_Aquisicao'].sum()
            df_resumo = pd.DataFrame({
                'Métricas': ['Valor_Titulo Total', 'Valor_Aquisicao Total', 'Spread', 'OK', 'NOK'],
                'Valores': [total_titulo, total_aquisicao, total_titulo - total_aquisicao, 
                           (df_detalhe['Validacao (Titulo >= Aquisicao)'] == 'OK').sum(), 
                           (df_detalhe['Validacao (Titulo >= Aquisicao)'] == 'NOK').sum()]
            })

            st.success("✅ Ficheiro validado com sucesso!")
            col1, col2 = st.columns([1, 2])
            with col1: st.dataframe(df_resumo, use_container_width=True)
            with col2: st.dataframe(df_detalhe, use_container_width=True)
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_detalhe.to_excel(writer, sheet_name='Relatorio', index=False)
            
            st.download_button("📥 Baixar Relatório de Validação", data=buffer.getvalue(), 
                               file_name=f"Validacao_{arquivo_upado.name}.xlsx", type="primary")

elif opcao_menu == "🔍 2. Leitor CNAB":
    st.title("🔍 Leitor e Extrator de CNAB 444")
    st.markdown("Transforma qualquer arquivo texto de remessa ou retorno numa folha de Excel com 49 colunas.")
    arquivo_upado = st.file_uploader("Upload do CNAB (.REM / .TXT)", type=["rem", "txt", "REM", "TXT"])
    
    if arquivo_upado is not None:
        linhas = arquivo_upado.getvalue().decode("utf-8", errors="ignore").splitlines()
        titulos_extraidos = []
        barra_progresso = st.progress(0)
        
        for num_linha, linha in enumerate(linhas):
            if not linha.strip() or linha[0] != '1': continue
            linha = linha.ljust(444)
            titulo_dict = {}
            pos_atual = 0
            for col_nome, tamanho, tipo, alinhamento, _ in LAYOUT_444:
                valor_bruto = linha[pos_atual : pos_atual + tamanho]
                if tipo == 'float':
                    try:
                        valor_num = float(valor_bruto) / 100
                    except ValueError:
                        valor_num = 0.0
                    titulo_dict[col_nome] = valor_num
                else:
                    valor_limpo = valor_bruto.strip()
                    if "Data" in col_nome and len(valor_limpo) == 6 and valor_limpo.isdigit() and valor_limpo != "000000":
                        valor_limpo = f"{valor_limpo[0:2]}/{valor_limpo[2:4]}/{valor_limpo[4:6]}"
                    titulo_dict[col_nome] = valor_limpo
                pos_atual += tamanho
            titulos_extraidos.append(titulo_dict)
            barra_progresso.progress((num_linha + 1) / len(linhas))
            
        if titulos_extraidos:
            df_leitor = pd.DataFrame(titulos_extraidos)
            st.success(f"✅ Ficheiro lido com sucesso! {len(df_leitor)} títulos extraídos.")
            st.dataframe(df_leitor.head())
            
            excel_data = salvar_excel_formatado(df_leitor, "Titulos")
            st.download_button(
                label="📥 Baixar Folha Completa (49 Colunas)",
                data=excel_data,
                file_name=f"Extraido_{arquivo_upado.name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        else:
            st.warning("⚠️ Nenhum registo de título (linha 1) encontrado neste ficheiro.")

elif opcao_menu == "⚙️ 3. Gerador CNAB":
    st.title("⚙️ Gerador de Remessa CNAB 444")
    
    with st.expander("🛠️ 1. Configurações do Cabeçalho (Header - Linha 0)", expanded=True):
        st.markdown("Preencha ou altere os parâmetros para a montagem do cabeçalho.")
        col_h1, col_h2, col_h3 = st.columns(3)
        with col_h1:
            cod_originador = st.text_input("Código do Originador (CNPJ)*", placeholder="Ex: 00000000000100", max_chars=20)
            literal_remessa = st.text_input("Literal Remessa", value="REMESSA", max_chars=7)
            cod_banco = st.text_input("Código do Banco", placeholder="439", max_chars=3)
        with col_h2:
            nome_originador = st.text_input("Nome do Originador*", max_chars=30)
            cod_servico = st.text_input("Código do Serviço", value="01", max_chars=2)
            nome_banco = st.text_input("Nome do Banco", placeholder="ID CTVM SA", max_chars=15)
        with col_h3:
            data_geracao = st.text_input("Data de Geração (DDMMAA)", value=datetime.now().strftime("%d%m%y"), max_chars=6)
            id_sistema = st.text_input("ID do Sistema", value="MX0000001", max_chars=9)
            literal_servico = st.text_input("Literal Serviço", value="COBRANCA", max_chars=15)
            seq_arquivo = st.text_input("Sequencial do Arquivo (NSA)", value="1", max_chars=6)
    
    st.markdown("---")
    
    df_template = pd.DataFrame(columns=[col[0] for col in LAYOUT_444])
    excel_template = salvar_excel_formatado(df_template, "Template")
    
    st.subheader("2. Títulos (Detalhe)")
    st.download_button(
        label="📥 Baixar Template Padrão",
        data=excel_template,
        file_name="Template_49_Colunas_CNAB.xlsx",
        help="Baixe este template. As colunas a amarelo são obrigatórias/recomendadas."
    )
    
    arquivo_planilha = st.file_uploader("Upload da Folha Preenchida (.xlsx ou .csv)", type=["xlsx", "xls", "csv"])
    if arquivo_planilha is not None:
        try:
            if arquivo_planilha.name.endswith('.csv'):
                df_entrada = pd.read_csv(arquivo_planilha, sep=None, engine='python', dtype=str, encoding='utf-8-sig')
            else:
                df_entrada = pd.read_excel(arquivo_planilha, dtype=str)
                
            df_entrada = df_entrada.fillna("")
            st.success(f"Folha carregada! {len(df_entrada)} títulos encontrados.")
            st.dataframe(df_entrada.head())
            
            if not cod_originador or not nome_originador:
                st.warning("⚠️ Preencha obrigatoriamente o Código e o Nome do Originador no quadro acima.")
            else:
                if st.button("🚀 Gerar Ficheiro CNAB (.REM)", type="primary"):
                    linhas_cnab = []
                    
                    # 1. HEADER (Linha 0)
                    header = "01" 
                    header += processar_string_cnab(literal_remessa.upper(), 7, 'ljust')
                    header += processar_string_cnab(cod_servico, 2, 'zeros')
                    header += processar_string_cnab(literal_servico.upper(), 15, 'ljust')
                    header += processar_string_cnab(cod_originador, 20, 'zeros')
                    header += processar_string_cnab(nome_originador.upper(), 30, 'ljust')
                    header += processar_string_cnab(cod_banco, 3, 'zeros')
                    header += processar_string_cnab(nome_banco.upper(), 15, 'ljust')
                    header += processar_string_cnab(data_geracao, 6, 'zeros')
                    header += " " * 8  
                    header += processar_string_cnab(id_sistema, 9, 'ljust')
                    header = header.ljust(438, " ") 
                    header += processar_string_cnab(seq_arquivo, 6, 'zeros')
                    linhas_cnab.append(header)
                    
                    # 2. DETALHES (Linhas 1 a N)
                    seq_linha = 2
                    for index, row in df_entrada.iterrows():
                        linha_detalhe = ""
                        for col_nome, tamanho, tipo, alinhamento, _ in LAYOUT_444:
                            valor_celula = str(row.get(col_nome, ''))
                            if "Data" in col_nome:
                                valor_celula = valor_celula.replace("/", "").replace("-", "")
                            
                            if tipo == 'seq':
                                linha_detalhe += str(seq_linha).zfill(tamanho)
                            elif tipo == 'float':
                                linha_detalhe += processar_float_cnab(valor_celula, tamanho)
                            else:
                                linha_detalhe += processar_string_cnab(valor_celula, tamanho, alinhamento)
                        linhas_cnab.append(linha_detalhe)
                        seq_linha += 1
                    
                    # 3. TRAILLER (Linha 9)
                    trailler = "9".ljust(438, " ") + str(seq_linha).zfill(6)
                    linhas_cnab.append(trailler)
                    
                    conteudo_final = "\n".join(linhas_cnab)
                    
                    st.download_button(
                        label="📥 Baixar Ficheiro CNAB (.REM)",
                        data=conteudo_final,
                        file_name=f"CB{data_geracao}.REM",
                        mime="text/plain",
                        type="primary"
                    )
        except Exception as e:
            st.error(f"Erro ao processar a folha de cálculo: {e}")
