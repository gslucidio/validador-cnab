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
    [
        "📊 Validador CNAB", 
        "🔍 Leitor CNAB", 
        "⚙️ Gerador CNAB"
    ]
)
st.sidebar.markdown("---")
st.sidebar.info("Sistema de processamento posicional padrão CNAB 444.")

# ==============================================================================
# DICIONÁRIO DE LAYOUT 444 
# ==============================================================================
LAYOUT_444 = [
    ("01_ID_Registro", 1, 'str', 'spaces'),
    ("02_Debito_Automatico", 19, 'str', 'spaces'),
    ("03_Coobrigacao", 2, 'str', 'zeros'),
    ("04_Caract_Especial", 2, 'str', 'zeros'),
    ("05_Modalidade", 4, 'str', 'zeros'),
    ("06_Natureza", 2, 'str', 'zeros'),
    ("07_Origem_Recurso", 4, 'str', 'zeros'),
    ("08_Classe_Risco", 2, 'str', 'spaces'),
    ("09_Zeros", 1, 'str', 'zeros'),
    ("10_Num_Controle", 25, 'str', 'spaces'),
    ("11_Num_Banco", 3, 'str', 'zeros'),
    ("12_Zeros", 5, 'str', 'zeros'),
    ("13_ID_Titulo_Banco", 11, 'str', 'spaces'), 
    ("14_Digito_Nosso_Num", 1, 'str', 'spaces'),
    ("15_Valor_Pago", 10, 'float', 'zeros'),
    ("16_Condicao_Papeleta", 1, 'str', 'spaces'),
    ("17_Emite_Papeleta", 1, 'str', 'spaces'),
    ("18_Data_Liquidacao", 6, 'str', 'zeros'),
    ("19_ID_Operacao_Banco", 4, 'str', 'spaces'),
    ("20_Ind_Rateio", 1, 'str', 'spaces'),
    ("21_End_Aviso_Debito", 1, 'str', 'zeros'),
    ("22_Branco", 2, 'str', 'spaces'),
    ("23_Ocorrencia", 2, 'str', 'zeros'),
    ("24_Num_Documento", 10, 'str', 'spaces'),
    ("25_Data_Vencimento", 6, 'str', 'zeros'),
    ("26_Valor_Titulo", 13, 'float', 'zeros'),
    ("27_Banco_Cobranca", 3, 'str', 'zeros'),
    ("28_Agencia_Deposit", 5, 'str', 'zeros'),
    ("29_Especie_Titulo", 2, 'str', 'zeros'),
    ("30_Identificacao", 1, 'str', 'spaces'),
    ("31_Data_Emissao", 6, 'str', 'zeros'),
    ("32_Instrucao_1", 2, 'str', 'zeros'),
    ("33_Instrucao_2", 1, 'str', 'zeros'),
    ("34_Tipo_Pessoa_Ced", 2, 'str', 'zeros'),
    ("35_Zeros", 12, 'str', 'spaces'),           
    ("36_Num_Termo_Cessao", 19, 'str', 'spaces'),
    ("37_Valor_Aquisicao", 13, 'float', 'zeros'),
    ("38_Valor_Abatimento", 13, 'float', 'zeros'),
    ("39_Tipo_Insc_Sacado", 2, 'str', 'zeros'),
    ("40_Insc_Sacado", 14, 'str', 'zeros'),
    ("41_Nome_Sacado", 40, 'str', 'spaces'),
    ("42_Endereco_Sacado", 40, 'str', 'spaces'),
    ("43_Num_NF_Duplicata", 9, 'str', 'spaces'), 
    ("44_Serie_NF", 3, 'str', 'spaces'),
    ("45_CEP_Sacado", 8, 'str', 'zeros'),
    ("46_Cedente", 60, 'str', 'spaces'),
    ("47_Chave_NF", 44, 'str', 'spaces'),
    ("48_Seq_Registro", 6, 'seq', 'zeros')
]

# ==============================================================================
# FUNÇÕES AUXILIARES DE FORMATAÇÃO 
# ==============================================================================
def str_para_valor(texto):
    texto = texto.strip()
    if not texto.isdigit(): return 0.0
    return float(texto) / 100

def processar_string_cnab(valor, tamanho, alinhamento):
    val = str(valor).strip()
    if val in ('nan', 'None'):
        val = ''
    if val.endswith('.0'): 
        val = val[:-2]
        
    if alinhamento == 'zeros':
        return val.zfill(tamanho)[:tamanho]
    else:
        return val.ljust(tamanho)[:tamanho]

def processar_float_cnab(valor, tamanho):
    val = str(valor).strip()
    if val in ('nan', 'None', ''):
        v_float = 0.0
    else:
        try:
            v_float = float(val)
        except:
            v_float = 0.0
    val_limpo = f"{v_float:.2f}".replace(".", "").replace(",", "")
    return val_limpo.zfill(tamanho)[:tamanho]

# ==============================================================================
# MÓDULO 1: VALIDADOR CNAB 
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

# ==============================================================================
# MÓDULO 2: LEITOR CNAB (NOVO)
# ==============================================================================
elif opcao_menu == "🔍 2. Leitor CNAB":
    st.title("🔍 Leitor e Extrator de CNAB 444")
    st.markdown("Transforma qualquer arquivo texto de remessa ou retorno em uma planilha de Excel com 48 colunas.")
    
    arquivo_upado = st.file_uploader("Faça o upload do arquivo CNAB (.REM / .TXT)", type=["rem", "txt", "REM", "TXT"])
    
    if arquivo_upado is not None:
        linhas = arquivo_upado.getvalue().decode("utf-8", errors="ignore").splitlines()
        titulos_extraidos = []
        barra_progresso = st.progress(0)
        
        for num_linha, linha in enumerate(linhas):
            if not linha.strip(): continue
            linha = linha.ljust(444)
            
            if linha[0] == '1': # Somente linhas de detalhe
                titulo_dict = {}
                pos_atual = 0
                
                for col_nome, tamanho, tipo, alinhamento in LAYOUT_444:
                    valor_bruto = linha[pos_atual : pos_atual + tamanho]
                    
                    if tipo == 'float':
                        try:
                            # Converte de volta de string sem vírgula para moeda real (ex: 000000015050 -> 150.50)
                            valor_num = float(valor_bruto) / 100
                        except:
                            valor_num = 0.0
                        titulo_dict[col_nome] = valor_num
                    else:
                        # Limpa espaços em branco nas pontas para a planilha ficar limpa
                        titulo_dict[col_nome] = valor_bruto.strip()
                        
                    pos_atual += tamanho
                    
                titulos_extraidos.append(titulo_dict)
            barra_progresso.progress((num_linha + 1) / len(linhas))
            
        if titulos_extraidos:
            df_leitor = pd.DataFrame(titulos_extraidos)
            st.success(f"✅ Arquivo lido perfeitamente! {len(df_leitor)} títulos foram extraídos para a planilha.")
            st.dataframe(df_leitor.head(), use_container_width=True)
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_leitor.to_excel(writer, sheet_name='Titulos', index=False)
                
            st.download_button(
                label="📥 Baixar Planilha Completa (48 Colunas)",
                data=buffer.getvalue(),
                file_name=f"Extraido_{arquivo_upado.name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        else:
            st.warning("⚠️ Nenhum registro de título (linha iniciada com '1') encontrado neste arquivo.")

# ==============================================================================
# MÓDULO 3: GERADOR CNAB 
# ==============================================================================
elif opcao_menu == "⚙️ 3. Gerador CNAB":
    st.title("⚙️ Gerador de Remessa CNAB 444")
    
    with st.expander("🛠️ 1. Configurações do Cabeçalho (Header - Linha 0)", expanded=True):
        st.markdown("Preencha ou altere os parâmetros para a montagem do cabeçalho da remessa.")
        
        col_h1, col_h2, col_h3 = st.columns(3)
        with col_h1:
            cod_originador = st.text_input("Código do Originador (CNPJ)*", placeholder="Ex: 00000000000100", max_chars=20)
            literal_remessa = st.text_input("Literal Remessa", value="REMESSA", max_chars=7)
            cod_banco = st.text_input("Código do Banco", placeholder="Ex: 000", max_chars=3)
            
        with col_h2:
            nome_originador = st.text_input("Nome do Originador*", max_chars=30)
            cod_servico = st.text_input("Código do Serviço", value="01", max_chars=2)
            nome_banco = st.text_input("Nome do Banco", max_chars=15)
            
        with col_h3:
            data_geracao = st.text_input("Data de Geração (DDMMAA)", value=datetime.now().strftime("%d%m%y"), max_chars=6)
            id_sistema = st.text_input("ID do Sistema", value="MX0000001", max_chars=9)
            literal_servico = st.text_input("Literal Serviço", value="COBRANCA", max_chars=15)
            seq_arquivo = st.text_input("Sequencial do Arquivo (NSA)", value="1", max_chars=6)
    
    st.markdown("---")
    
    df_template = pd.DataFrame(columns=[col[0] for col in LAYOUT_444])
    buffer_tpl = io.BytesIO()
    with pd.ExcelWriter(buffer_tpl, engine='xlsxwriter') as writer:
        df_template.to_excel(writer, index=False)
    
    st.subheader("2. Títulos (Detalhe)")
    st.download_button(
        label="📥 Baixar Template Padrão (48 Colunas)",
        data=buffer_tpl.getvalue(),
        file_name="Template_48_Colunas_CNAB.xlsx"
    )
    
    arquivo_planilha = st.file_uploader("Faça o upload da Planilha Preenchida (.xlsx ou .csv)", type=["xlsx", "xls", "csv"])
    
    if arquivo_planilha is not None:
        try:
            if arquivo_planilha.name.endswith('.csv'):
                df_entrada = pd.read_csv(arquivo_planilha, sep=None, engine='python', dtype=str, encoding='utf-8-sig')
            else:
                df_entrada = pd.read_excel(arquivo_planilha, dtype=str)
                
            df_entrada = df_entrada.fillna("")
                
            st.success(f"Planilha carregada! {len(df_entrada)} títulos encontrados.")
            st.dataframe(df_entrada.head())
            
            if not cod_originador or not nome_originador:
                st.warning("⚠️ Preencha obrigatoriamente o Código e o Nome do Originador no quadro acima.")
            else:
                if st.button("🚀 Gerar Ficheiro CNAB (.REM)", type="primary"):
                    linhas_cnab = []
                    
                    # 1. HEADER (Linha 0)
                    header = "0" 
                    header += "1" 
                    header += processar_string_cnab(literal_remessa.upper(), 7, 'spaces')
                    header += processar_string_cnab(cod_servico, 2, 'zeros')
                    header += processar_string_cnab(literal_servico.upper(), 15, 'spaces')
                    header += processar_string_cnab(cod_originador, 20, 'zeros')
                    header += processar_string_cnab(nome_originador.upper(), 30, 'spaces')
                    header += processar_string_cnab(cod_banco, 3, 'zeros')
                    header += processar_string_cnab(nome_banco.upper(), 15, 'spaces')
                    header += processar_string_cnab(data_geracao, 6, 'zeros')
                    
                    header += " " * 8  
                    header += processar_string_cnab(id_sistema, 9, 'spaces')
                    
                    header = header.ljust(438, " ") 
                    header += processar_string_cnab(seq_arquivo, 6, 'zeros')
                    linhas_cnab.append(header)
                    
                    # 2. DETALHES (Linhas 1 a N)
                    seq_linha = 2
                    for index, row in df_entrada.iterrows():
                        linha_detalhe = ""
                        for col_nome, tamanho, tipo, alinhamento in LAYOUT_444:
                            valor_celula = row.get(col_nome, '')
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
                        label="📥 Baixar Arquivo CNAB (.REM)",
                        data=conteudo_final,
                        file_name=f"CB{data_geracao}.REM",
                        mime="text/plain",
                        type="primary"
                    )
                    
        except Exception as e:
            st.error(f"Erro ao processar a folha de cálculo: {e}")

