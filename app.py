from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Utilisation en mode non interactif
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import io
import base64
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data'

app.config['ALLOWED_EXTENSIONS'] = {'csv'}
app.jinja_env.globals.update(float=float)
# ...existing code...

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "Aucun fichier sélectionné", 400
        file = request.files['file']
        if file.filename == '':
            return "Nom de fichier vide", 400
        if file and file.filename.endswith('.csv'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'transactions_biat.csv')
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(filepath)
            return render_template('upload_success.html', filename=file.filename)
        else:
            return "Format de fichier non supporté. Veuillez uploader un fichier CSV.", 400
    return render_template('upload.html',)
# ...existing code...

# Charger les données
def load_data():
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'transactions_biat.csv')
    
    df = pd.read_csv(file_path, encoding='utf-8')
    
    # Nettoyer les données (basé sur l'exemple fourni)
    df['banque_emettrice'] = df['banque_emettrice'].replace({'BM7': 'BIAT'})
    df['banque_aquereur'] = df['banque_aquereur'].replace({
        'BMP Paribas': 'BNP Paribas',
        'SG871': 'Société Générale',
        'Univredit': 'Unicredit',
        'Ocelet Agricole': 'Credit Agricole',
        'Zionna Bank': 'Zitouna Bank',
        'Anno Bank': 'Amen Bank',
        'USGSM': 'UBCI'  # Supposition basée sur le contexte
    })
    
    # Corriger les types de données
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df['montant'] = pd.to_numeric(df['montant'], errors='coerce')
    
    return df

# Page d'accueil
@app.route('/')
def index():
    return render_template('index.html')

# Tableau de bord avec statistiques
@app.route('/dashboard')
def dashboard():
    df = load_data()
    
    # Statistiques de base
    total_transactions = len(df)
    total_montant = df['montant'].sum()
    montant_moyen = df['montant'].mean()
    transactions_par_heure = df.groupby(df['timestamp'].dt.hour).size()
    
    # Top 5 des types de transactions
    top_transactions = df['type_transaction'].value_counts().head(5)
    
    # Répartition par pays
    pays_distribution = df['pays'].value_counts().head(10)
    
    # Répartition par type de carte
    carte_distribution = df['type_carte'].value_counts()
    
    # Générer des graphiques
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Graphique 1: Transactions par heure
    axes[0, 0].bar(transactions_par_heure.index, transactions_par_heure.values)
    axes[0, 0].set_title('Transactions par Heure')
    axes[0, 0].set_xlabel('Heure')
    axes[0, 0].set_ylabel('Nombre de Transactions')
    
    # Graphique 2: Top types de transactions
    axes[0, 1].pie(top_transactions.values, labels=top_transactions.index, autopct='%1.1f%%')
    axes[0, 1].set_title('Répartition des Types de Transactions')
    
    # Graphique 3: Répartition par pays
    axes[1, 0].barh(pays_distribution.index.astype(str), pays_distribution.values)
    axes[1, 0].set_title('Top 10 Pays par Transactions')
    axes[1, 0].set_xlabel('Nombre de Transactions')
    
    # Graphique 4: Répartition par type de carte
    axes[1, 1].pie(carte_distribution.values, labels=carte_distribution.index, autopct='%1.1f%%')
    axes[1, 1].set_title('Répartition par Type de Carte')
    
    plt.tight_layout()
    
    # Convertir le graphique en image base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()
    
    return render_template('dashboard.html', 
                         total_transactions=total_transactions,
                         total_montant=total_montant,
                         montant_moyen=montant_moyen,
                         plot_url=plot_url,
                         top_transactions=top_transactions.to_dict(),
                         pays_distribution=pays_distribution.to_dict(),
                         carte_distribution=carte_distribution.to_dict())

# Page des transactions (vue tabulaire)
@app.route('/transactions')
def transactions():
    df = load_data()
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    total_pages = (len(df) // per_page) + 1
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    transactions_data = df.iloc[start_idx:end_idx].to_dict('records')
    
    return render_template('transactions.html', 
                         transactions=transactions_data,
                         page=page,
                         total_pages=total_pages)

# API pour les données de transactions par heure

@app.route('/about')
def about():
    return render_template('about.html')
#route pour les serie temporelles
@app.route('/time_series')
def time_series():
    df = load_data()
    df.set_index('timestamp', inplace=True)
    time_series_data = df.resample('D').size()
    
    # Convertir le graphique en image base64
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(time_series_data.index, time_series_data.values)
    ax.set_title('Transactions au Fil du Temps')
    ax.set_xlabel('Date')
    ax.set_ylabel('Nombre de Transactions')
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()
    
    return render_template('time_series.html', plot_url=plot_url)




if __name__ == '__main__':
    app.run(debug=True)
    

    
