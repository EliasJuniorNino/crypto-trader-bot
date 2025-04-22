import pandas as pd

# Criando um DataFrame simples
df = pd.DataFrame(
    {'date':   [1,  2,  3,  4,  5],
     'fear':   [10, 20, 30, 40, 50],
     'price':  [10, 20, 30, 40, 50]})

# Deslocando a coluna 'A' por 2 posições
df['price'] = df['price'].shift(-1)

df = df.iloc[:-1]

# O DataFrame após a operação de deslocamento
print(df)
