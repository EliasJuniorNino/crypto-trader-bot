import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import os
import logging
from datetime import datetime
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.layers import LSTM, TimeDistributed

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crypto_prediction.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("crypto_predictor")

# Configurações globais
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
tf.random.set_seed(RANDOM_SEED)
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)


class CryptoPredictor:
    """Classe para previsão de valores de criptomoedas com base em indicadores de medo e ganância."""
    
    def __init__(self, dataset_path):
        """
        Inicializa o preditor de criptomoedas.
        
        Args:
            dataset_path: Caminho para o arquivo CSV dos dados
        """
        self.dataset_path = dataset_path
        self.model = None
        self.scaler = StandardScaler()
        self.target_columns = []
        self.features = []
        
    def load_data(self):
        """Carrega e valida os dados do dataset."""
        try:
            initial_df = pd.read_csv(self.dataset_path)
            if initial_df.empty:
                raise ValueError("Dataset está vazio.")
            logger.info(f"Dados carregados com sucesso. Shape: {initial_df.shape}")
            return initial_df
        except FileNotFoundError:
            logger.error(f"Arquivo não encontrado: {self.dataset_path}")
            raise
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {str(e)}")
            raise
            
    def preprocess_data(self, df):
        """
        Realiza o pré-processamento dos dados.
        
        Args:
            df: DataFrame com os dados brutos
            
        Returns:
            DataFrame limpo e processado
        """
        # Backup dos dados originais
        original_shape = df.shape
        
        # Análise e tratamento de valores nulos
        null_counts = df.isnull().sum()
        if null_counts.any():
            logger.info(f"Valores nulos encontrados: \n{null_counts[null_counts > 0]}")
            df.dropna(inplace=True)
         
        # Remoção de colunas que têm apenas zeros
        ignore_zero_cols = ['hour', 'day']
        zero_cols = [col for col in df.columns if col not in ignore_zero_cols and (df[col] == 0).all()]
        if zero_cols:
            logger.info(f"Removendo colunas com todos os valores zero exceto: {ignore_zero_cols}")
            df = df.drop(columns=zero_cols)
            
        # Remoção de duplicatas
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            logger.info(f"Removendo {duplicates} linhas duplicadas")
            df.drop_duplicates(inplace=True)
        
        logger.info(f"Pré-processamento concluído. Shape original: {original_shape}, novo shape: {df.shape}")
        
        # Salvar dados processados
        clean_path = os.path.join(DATA_DIR, "dataset_clean.csv")
        df.to_csv(clean_path, index=False)
        logger.info(f"Dados limpos salvos em {clean_path}")
        
        return df
    
    def engineer_features(self, df):
        """
        Engenharia de features para o modelo.
        
        Args:
            df: DataFrame limpo
            
        Returns:
            X: Features
            y: Targets
            df_full: DataFrame completo com features adicionadas
        """
        # Separar a última linha para predição futura
        df_full = df.copy()
        df = df.iloc[:-1].copy()
        
        # Converter para datetime e criar features temporais
        try:
            df['data'] = pd.to_datetime(df[['year', 'month', 'day', 'hour']])
            
            # Features temporais básicas
            df['dia_do_ano'] = df['data'].dt.dayofyear
            df['dia_da_semana'] = df['data'].dt.weekday
            df['semana'] = df['data'].dt.isocalendar().week.astype(int)
            df['fim_de_semana'] = df['dia_da_semana'].isin([5, 6]).astype(int)
            
            #  Features temporais adicionais
            df['mes'] = df['data'].dt.month
            df['trimestre'] = df['data'].dt.quarter
            
            # Features cíclicas para variáveis temporais
            df['dia_do_ano_sin'] = np.sin(2 * np.pi * df['dia_do_ano']/365)
            df['dia_do_ano_cos'] = np.cos(2 * np.pi * df['dia_do_ano']/365)
            df['dia_da_semana_sin'] = np.sin(2 * np.pi * df['dia_da_semana']/7)
            df['dia_da_semana_cos'] = np.cos(2 * np.pi * df['dia_da_semana']/7)
            
            # Feature da hora e suas transformações cíclicas
            df['hour_sin'] = np.sin(2 * np.pi * (df['hour']/24))
            df['hour_cos'] = np.cos(2 * np.pi * (df['hour']/24))
            
        except KeyError as e:
            logger.error(f"Colunas de data não encontradas: {str(e)}")
            raise
        
        # Verificar a presença das colunas necessárias
        required_cols = ['fear_api_alternative_me', 'fear_coinmarketcap']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Colunas obrigatórias ausentes: {missing_cols}")
            raise ValueError(f"Colunas obrigatórias ausentes: {missing_cols}")
        
        # Features de diferença e médias móveis para indicadores de medo
        for col in required_cols:
            df[f'{col}_diff'] = df[col].diff().fillna(0)
            df[f'{col}_rolling_3d'] = df[col].rolling(3).mean().fillna(df[col])
            df[f'{col}_rolling_7d'] = df[col].rolling(7).mean().fillna(df[col])
        
        # Definir colunas de features
        self.features = [
            'dia_do_ano', 'dia_da_semana', 'semana', 'fim_de_semana', 
            'mes', 'trimestre', 'dia_do_ano_sin', 'dia_do_ano_cos', 
            'dia_da_semana_sin', 'dia_da_semana_cos',
            'hour', 'hour_sin', 'hour_cos'
        ]
        
        # Adicionar features de indicadores de medo e suas derivadas
        for col in required_cols:
            self.features.extend([col, f'{col}_diff', f'{col}_rolling_3d', f'{col}_rolling_7d'])
        
        # Selecionar features
        X = df[self.features]
        
        # Selecionar targets (colunas que terminam com _min_value ou _max_value)
        self.target_columns = [col for col in df.columns if col.endswith('_min_value') or col.endswith('_max_value')]
        if not self.target_columns:
            logger.error("Nenhuma coluna target (_min_value ou _max_value) encontrada")
            raise ValueError("Nenhuma coluna target (_min_value ou _max_value) encontrada")
            
        logger.info(f"Targets selecionados: {self.target_columns}")
        y = df[self.target_columns]
        
        return X, y, df_full

    def build_model(self, input_dim, output_dim):
        """
        Constrói a arquitetura do modelo de ML.
        
        Args:
            input_dim: Dimensão de entrada (número de features)
            output_dim: Dimensão de saída (número de targets)
            
        Returns:
            Modelo compilado
        """
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(128, activation='relu', input_dim=input_dim),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dropout(0.3),

            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dropout(0.2),

            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.BatchNormalization(),

            tf.keras.layers.Dense(output_dim)
        ])
        
        optimizer = tf.keras.optimizers.Adam(learning_rate=1e-3)
        model.compile(optimizer=optimizer, loss='mse', metrics=['mae', 'mse'])
        
        logger.info(f"Modelo construído com {input_dim} inputs e {output_dim} outputs")
        model.summary(print_fn=logger.info)
        
        return model
    
    def train(self, X, y, validation_split=0.2, epochs=150, batch_size=16):
        """
        Treina o modelo com os dados fornecidos.
        
        Args:
            X: Features
            y: Targets
            validation_split: Proporção de dados para validação
            epochs: Número de épocas de treinamento
            batch_size: Tamanho do batch
            
        Returns:
            História do treinamento
        """
        # Normalizar os dados
        X_scaled = self.scaler.fit_transform(X)
        
        # Dividir em treino e teste
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=validation_split, random_state=RANDOM_SEED
        )
        
        # Construir modelo
        self.model = self.build_model(X_train.shape[1], len(self.target_columns))
        
        # Callbacks para melhorar o treinamento
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=20,
            restore_best_weights=True,
            verbose=1
        )
        
        checkpoint_path = os.path.join(DATA_DIR, "best_model.h5")
        model_checkpoint = ModelCheckpoint(
            checkpoint_path,
            monitor='val_loss',
            save_best_only=True,
            verbose=1
        )
        
        reduce_lr = ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=10,
            min_lr=0.00001,
            verbose=1
        )
        
        # Treinar o modelo
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_test, y_test),
            callbacks=[early_stopping, model_checkpoint, reduce_lr],
            verbose=1
        )
        
        # Avaliar modelo
        self.evaluate(X_test, y_test)
        
        # Plotar histórico de treinamento
        self.plot_training_history(history)
        
        return history
    
    def evaluate(self, X_test, y_test):
        """
        Avalia o modelo em dados de teste.
        
        Args:
            X_test: Features de teste
            y_test: Targets de teste
        """
        y_pred = self.model.predict(X_test)
        
        # Calcular métricas
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        logger.info(f"Métricas de avaliação:")
        logger.info(f"Erro quadrático médio (MSE): {mse:.4f}")
        logger.info(f"Erro absoluto médio (MAE): {mae:.4f}")
        logger.info(f"R² Score: {r2:.4f}")
        
        # Salvar métricas
        metrics_df = pd.DataFrame({
            'metric': ['MSE', 'MAE', 'R2'],
            'value': [mse, mae, r2]
        })
        metrics_df.to_csv(os.path.join(DATA_DIR, "model_metrics.csv"), index=False)
        
        return mse, mae, r2
    
    def plot_training_history(self, history):
        """
        Gera gráficos do histórico de treinamento.
        
        Args:
            history: Histórico retornado pelo treinamento do modelo
        """
        plt.figure(figsize=(12, 5))
        
        # Plot de perda (loss)
        plt.subplot(1, 2, 1)
        plt.plot(history.history['loss'], label='Train Loss')
        plt.plot(history.history['val_loss'], label='Validation Loss')
        plt.title('Model Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        plt.grid(True)
        
        # Plot de MAE
        plt.subplot(1, 2, 2)
        plt.plot(history.history['mae'], label='Train MAE')
        plt.plot(history.history['val_mae'], label='Validation MAE')
        plt.title('Model MAE')
        plt.xlabel('Epoch')
        plt.ylabel('MAE')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig(os.path.join(DATA_DIR, "training_history.png"))
        logger.info(f"Gráficos de treinamento salvos em {os.path.join(DATA_DIR, 'training_history.png')}")
    
    def predict(self, date=None, fear_api_alternative_me=None, fear_coinmarketcap=None, last_row=None):
        """
        Realiza previsão para uma data específica.
        
        Args:
            date: Data para previsão (padrão: hoje)
            fear_api_alternative_me: Valor do índice de medo da API alternativa
            fear_coinmarketcap: Valor do índice de medo do CoinMarketCap
            last_row: Última linha do dataset (para obter valores default)
            
        Returns:
            DataFrame com as previsões
        """
        if self.model is None:
            logger.error("Modelo não treinado. Execute o método train() primeiro.")
            raise ValueError("Modelo não treinado.")
            
        # Definir data padrão (hoje)
        if date is None:
            date = datetime.now()
        elif isinstance(date, str):
            date = pd.to_datetime(date)
            
        # Se last_row fornecido, extrair valores padrão
        if last_row is not None:
            if fear_api_alternative_me is None and 'fear_api_alternative_me' in last_row:
                fear_api_alternative_me = int(last_row['fear_api_alternative_me'].iloc[0])
            if fear_coinmarketcap is None and 'fear_coinmarketcap' in last_row:
                fear_coinmarketcap = int(last_row['fear_coinmarketcap'].iloc[0])
        
        # Verificar se temos os valores necessários
        if fear_api_alternative_me is None or fear_coinmarketcap is None:
            logger.error("Valores de medo não fornecidos e não encontrados na última linha.")
            raise ValueError("Valores de medo (fear indices) são obrigatórios para previsão.")
            
        # Extrair features temporais
        dia_do_ano = date.timetuple().tm_yday
        dia_da_semana = date.weekday()
        semana = date.isocalendar()[1]
        fim_de_semana = 1 if dia_da_semana >= 5 else 0
        mes = date.month
        trimestre = (mes - 1) // 3 + 1
        
        # Features cíclicas
        dia_do_ano_sin = np.sin(2 * np.pi * dia_do_ano / 365)
        dia_do_ano_cos = np.cos(2 * np.pi * dia_do_ano / 365)
        dia_da_semana_sin = np.sin(2 * np.pi * dia_da_semana / 7)
        dia_da_semana_cos = np.cos(2 * np.pi * dia_da_semana / 7)
        
        # Valores calculados para features derivadas
        # Na primeira previsão, assumimos diff como 0 e rolling values iguais aos valores atuais
        fear_api_diff = 0
        fear_cmc_diff = 0
        fear_api_rolling_3d = fear_api_alternative_me
        fear_api_rolling_7d = fear_api_alternative_me
        fear_cmc_rolling_3d = fear_coinmarketcap
        fear_cmc_rolling_7d = fear_coinmarketcap
        
        # Criar vetor de features na mesma ordem usada no treinamento
        feature_values = [
            dia_do_ano, dia_da_semana, semana, fim_de_semana, 
            mes, trimestre, dia_do_ano_sin, dia_do_ano_cos, 
            dia_da_semana_sin, dia_da_semana_cos,
            fear_api_alternative_me, fear_api_diff, fear_api_rolling_3d, fear_api_rolling_7d,
            fear_coinmarketcap, fear_cmc_diff, fear_cmc_rolling_3d, fear_cmc_rolling_7d
        ]
        
        # Verificar se o número de features corresponde ao esperado
        if len(feature_values) != len(self.features):
            logger.error(f"Número incorreto de features. Esperado: {len(self.features)}, Obtido: {len(feature_values)}")
            logger.error(f"Features esperadas: {self.features}")
            raise ValueError("Número incorreto de features para previsão.")
        
        predict_features = np.array([feature_values])
        
        # Normalizar features
        predict_scaled = self.scaler.transform(predict_features)
        
        # Fazer previsão
        prediction = self.model.predict(predict_scaled)
        
        # Criar dicionário e DataFrame
        predict_dict = dict(zip(self.target_columns, prediction[0]))
        df_predict = pd.DataFrame([predict_dict])
        
        # Adicionar informações da data e índices de medo
        df_predict['data_previsao'] = date.strftime('%Y-%m-%d')
        df_predict['fear_api_alternative_me'] = fear_api_alternative_me
        df_predict['fear_coinmarketcap'] = fear_coinmarketcap
        
        # Salvar previsão
        predict_path = os.path.join(DATA_DIR, "predict.csv")
        df_predict.to_csv(predict_path, index=False)
        logger.info(f"Previsão salva em {predict_path}")
        
        return df_predict
        
def predict():
    """Função principal para execução do script."""
    try:
        # Caminho para o dataset
        dataset_path = os.path.join(DATA_DIR, "dataset2.csv")
        
        # Instanciar e treinar o modelo
        predictor = CryptoPredictor(dataset_path)
        
        # Carregar e pré-processar dados
        logger.info("Iniciando carregamento e pré-processamento de dados...")
        initial_df = predictor.load_data()
        clean_df = predictor.preprocess_data(initial_df)
        
        # Engenharia de features
        logger.info("Realizando engenharia de features...")
        X, y, df_full = predictor.engineer_features(clean_df)
        
        # Treinar modelo
        logger.info("Iniciando treinamento do modelo...")
        predictor.train(X, y, epochs=1000, batch_size=1000)
        
        # Preparar dados para previsão
        last_row = df_full.iloc[-1:]
        
        # Fazer previsão para hoje
        logger.info("Realizando previsão para a data atual...")
        today = datetime.now()
        predictions = predictor.predict(
            date=today,
            last_row=last_row
        )
        
        # Exibir previsões
        logger.info(f"Previsões para {today.strftime('%Y-%m-%d')}:\n{predictions.to_string()}")
        
        logger.info("Processamento concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro na execução: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    predict()