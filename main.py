#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
import streamlit as st
import mysql.connector
import sqlalchemy 
from sqlalchemy import create_engine
import pymssql 
import pyodbc   

# Código dos botões Carga e Reset

def _carga():
    con = pyodbc.connect("driver={ODBC Driver 17 for SQL Server};"
                         "Server=academiacnp.mssql.somee.com;"
                         "Uid=marcosinada;"
                         "Pwd=livro8403;")
    cursor = con.cursor()
    df = pd.read_sql("SELECT TOP 100* FROM dw\
    WHERE NOT EXISTS(SELECT * FROM dw2 WHERE dw.[Código de cliente] = dw2.[Código de cliente])", con);
    cursor.close()
    con.close()
    sqlEngine = sqlalchemy.create_engine('mssql+pymssql://marcosinada:livro8403@academiacnp.mssql.somee.com/academiacnp')
    dbConnection    = sqlEngine.connect()
    df.to_sql('dw2', dbConnection, index=False,if_exists='append');
    dbConnection.close() 

def _reset():
    con = pyodbc.connect("driver={ODBC Driver 17 for SQL Server};"
                         "Server=academiacnp.mssql.somee.com;"
                         "Database=academiacnp;"
                         "Uid=marcosinada;"
                         "Pwd=livro8403;")
    cursor = con.cursor()
    
    df = pd.read_sql("SELECT TOP 100 * FROM dw", con);
    cursor.close()
    con.close()
    sqlEngine = sqlalchemy.create_engine('mssql+pymssql://marcosinada:livro8403@academiacnp.mssql.somee.com/academiacnp')
    dbConnection = sqlEngine.connect()
    df.to_sql('dw2', dbConnection, index=False, if_exists='replace');
    dbConnection.close()

# Aqui começa o comando inicial para o programa funcionar.

con = pyodbc.connect("driver={ODBC Driver 17 for SQL Server};"
                     "Server=academiacnp.mssql.somee.com;"
                     "Uid=marcosinada;"
                     "Pwd=livro8403;") 
cursor = con.cursor()
df = pd.read_sql("SELECT * FROM dw2", con);
cursor.close()
con.close()

datas = df['data última presença']
periodo = []
temp = []
for d in datas:
    temp = str(d)
    periodo.append(temp)
datas = pd.Series(periodo)
periodo = datas.unique()

hoje = datetime.now()

Calc_idades = df[['Nascimento']]
for idade in Calc_idades:    
    Calc_idades['data_atual'] = hoje
 

df['idade'] = (Calc_idades.data_atual[0:len(Calc_idades)] - Calc_idades.Nascimento[0:len(Calc_idades)]) // timedelta(days=365.2425)  

# Conteúdo que aparece na tela.

st.title("Academia Pompeia")

st.sidebar.button('Carregar mais dados', help='Clique para realizar a simulação de entrada de dados', on_click=_carga)

sidebar_selection = st.sidebar.radio(
    "Selecione uma opção:",
    ['Qual é o cliente que não vai a mais tempo?',
     'O consultor que tem mais clientes?',
     'Professor que tem mais alunos?',
     'Qual é a modalidade, mais consumida?', 
     'Encontrar inconsistencias no cadastro das modalidades?'] )

if sidebar_selection == 'Qual é o cliente que não vai a mais tempo?':
  st.markdown('## Qual é o cliente que não vai a mais tempo?')
  data_inicial = st.select_slider('Selecione a data inicial:',options=periodo)
  clientes = df[['Código de cliente']]
  clientes['data última presença'] = datas
  cliente_sedentario = clientes[(clientes['data última presença'] >= data_inicial)]
  cliente_sedentario = cliente_sedentario.head(1)
  cliente_sedentario

if sidebar_selection == 'O consultor que tem mais clientes?':
  st.markdown('## O consultor que tem mais clientes?')
  st.write('Não foi possivel informar o consultor que tem mais clientes, pois não temos a data de inclusão. Dessa forma não consigo responder essa pergunta no momento.')  
  data_inicial, data_final = st.select_slider('Selecione o período:', options=periodo, value=(periodo.min(), periodo.max()))
  consultores = df[['Consultor']]
  consultores['data última presença'] = datas
  consultores = consultores[(consultores['data última presença'] >= data_inicial) & (consultores['data última presença'] <= data_final)]
  consultores = consultores.groupby('Consultor').agg(Total=('Consultor','count')).sort_values(by='Total', ascending=False)
  consultor = consultores.head(1)
  consultor
  st.bar_chart(consultores,width=0, height=400)  
  
if sidebar_selection == 'Professor que tem mais alunos?':
  st.markdown('## Professor que tem mais alunos?')
  professores = df[['Professor']].groupby('Professor').agg(Total=('Professor','count')).sort_values(by='Total', ascending=False)
  professores.head(8)
  professor = professores[1:2]
  professor
  st.bar_chart(professores,width=0, height=400)
  
if sidebar_selection == 'Qual é a modalidade, mais consumida?':
  st.markdown('## Qual é a modalidade, mais consumida?')
  st.write('Modalidades dentro do período')  
  data_inicial, data_final = st.select_slider('Selecione o período:', options=periodo, value=(periodo.min(), periodo.max()))
  temp = pd.DataFrame({'datas':datas})
  temp[['modalidade1','modalidade2','modalidade3']] = df['Modalidade'].str.split('+', expand = True)
  correcao = {'MUSCULAÇÃO ': 'MUSCULAÇÃO',' MUSCULAÇÃO':'MUSCULAÇÃO',' MUSCULAÇÃO ':'MUSCULAÇÃO','FUNCIONAL ':'FUNCIONAL',' FUNCIONAL':'FUNCIONAL','NATAÇÃO ':'NATAÇÃO',' NATAÇÃO':'NATAÇÃO','-':'PLANO COMPLETO'}
  temp.replace(correcao, inplace= True)
  temp = temp[(temp['datas'] >= data_inicial) & (temp['datas'] <= data_final)]
  modalidades = pd.DataFrame()
  modalidades['Total'] = pd.concat([temp['modalidade1'],temp['modalidade2'],temp['modalidade3']], ignore_index=True)
  modalidades = pd.DataFrame(modalidades['Total'].value_counts())
  modalidades[0:2]
  st.bar_chart(modalidades,width=0, height=400)

if sidebar_selection == 'Como conheceu a academia':
  df['Como Conheceu'].replace({'-':'NÃO INFORMADO'}, inplace = True)
  como_conheceu = df['Como Conheceu'].value_counts()
  st.bar_chart(como_conheceu,width=0, height=400)

if sidebar_selection == 'Encontrar inconsistencias no cadastro das modalidades?':
  st.write("Clientes cadastrados como Natação Infantil que estão acima da idade")
  select_1 = df[df['Modalidade'].str.contains('NATAÇÃO INFANTIL', na=False)]
  select_1 = select_1[['Código de cliente','idade','Modalidade']]
  select_1 = select_1.query('idade > 13').sort_values(by=['idade'])
  select_1
  
  st.write("Clientes cadastrados como Natação que estão abaixo da idade")
  select_2 = df[df['Modalidade'].str.contains('NATAÇÃO', na=False)]
  select_2 = select_2[~select_2['Modalidade'].str.contains('INFANTIL', na=False)]
  select_2 = select_2[['Código de cliente','idade','Modalidade']]
  select_2 = select_2.query('idade < 13').sort_values(by=['idade'])
  select_2

  st.write("Clientes cadastrados como Musculação que estão abaixo da idade")
  select_3 = df[df['Modalidade'].str.contains('MUSCULAÇÃO', na=False)]
  select_3 = select_3[['Código de cliente','idade','Modalidade']]
  select_3 = select_3.query('idade < 16').sort_values(by=['idade'])
  select_3
    
  


st.sidebar.button('RESET', help='Clique para voltar ao estado inicial', on_click=_reset)  











