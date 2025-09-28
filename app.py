# Importe as funções e bibliotecas necessárias
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import bcrypt
import requests
from supabase import create_client, Client

# Inicializa o aplicativo Flask
app = Flask(__name__)
# APLICA O CORS: Permite que o frontend (HTML/JS) se comunique com este backend
CORS(app)

# ==============================
# CONFIGURAÇÃO E INICIALIZAÇÃO DO SUPABASE CLIENT (API)
# ==============================
SUPABASE_URL = "https://ulbaklykimxpsdrtkqet.supabase.co" 
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsYmFrbHlraW14cHNkcnRrcWV0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgzMjc0MjcsImV4cCI6MjA3MzkwMzQyN30.A3_WLF3cNstQtXcOr2Q3OJCvTYqBQe7wmmXHc_WCqAk"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY )
    supabase.table("usuarios").select("id").limit(1).execute()
    print("Conexão com Supabase bem-sucedida e cliente inicializado!")
except Exception as e:
    print(f"ERRO CRÍTICO ao conectar com Supabase: {e}")
    supabase = None

# ==============================
# CONFIGURAÇÃO GOOGLE MAPS API
# ==============================
API_KEY = ""

# ==============================
# ROTA PRINCIPAL PARA EXIBIR A PÁGINA DE REGISTRO
# ==============================
@app.route("/")
def home():
    """
    Esta rota responde ao acesso na URL principal (http://127.0.0.1:5000/ )
    e renderiza o arquivo HTML da página de registro.
    """
    return render_template("registrar.html")

# ==============================
# ROTA: Registrar Usuário (API)
# ==============================
@app.route("/registrar", methods=["POST"])
def registrar():
    """
    Esta rota recebe os dados do formulário (via JavaScript) e os insere no banco.
    """
    if not supabase:
        return jsonify({"erro": "Conexão com o banco de dados não está configurada."}), 503

    data = request.json
    nome = data.get("nome")
    email = data.get("email")
    senha_texto_plano = data.get("senha") # Renomeado para clareza

    if not nome or not email or not senha_texto_plano:
        return jsonify({"erro": "Todos os campos (nome, email, senha) são obrigatórios"}), 400

    # Gera o hash seguro da senha fornecida
    senha_hash = bcrypt.hashpw(senha_texto_plano.encode("utf-8"), bcrypt.gensalt()).decode('utf-8')

    # Prepara os dados para inserção no Supabase
    data_to_insert = {
        "nome": nome,
        "email": email,
        # CORREÇÃO APLICADA AQUI: Usando "senha" para corresponder à sua coluna no Supabase
        "senha": senha_hash 
    }

    try:
        supabase.table("usuarios").insert(data_to_insert).execute()
        return jsonify({"mensagem": "Usuário registrado com sucesso!"}), 201
    except Exception as e:
        if "duplicate key value" in str(e).lower():
            return jsonify({"erro": "Este email já está cadastrado"}), 409
        else:
            # Log do erro no terminal para depuração
            print(f"[ERRO /registrar]: {e}")
            return jsonify({"erro": "Ocorreu um erro inesperado ao registrar o usuário"}), 500

# ==============================
# ROTA: Listar usuários
# ==============================
@app.route("/usuarios", methods=["GET"])
def listar_usuarios():
    if not supabase:
        return jsonify({"erro": "Conexão com o banco de dados não está configurada."}), 503
    try:
        response = supabase.table("usuarios").select("id, nome, email, criado_em").execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({"erro": f"Erro ao listar usuários: {str(e)}"}), 500

# ==============================
# ROTA: Buscar jogadores por posição
# ==============================
@app.route("/jogadores/<posicao>", methods=["GET"])
def buscar_jogadores(posicao):
    if not supabase:
        return jsonify({"erro": "Conexão com o banco de dados não está configurada."}), 503
    try:
        response = supabase.table("jogadores").select("*").eq("posicao", posicao.upper()).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar jogadores: {str(e)}"}), 500

# ==============================
# ROTA: Buscar cidade no Google Maps
# ==============================
@app.route("/cidade/<nome_cidade>", methods=["GET"])
def procurar_cidade(nome_cidade):
    if not API_KEY:
        return jsonify({"erro": "A chave da API do Google Maps não foi configurada no servidor."}), 500
    try:
        response = requests.get(f"https://maps.googleapis.com/maps/api/geocode/json?address={nome_cidade}&key={API_KEY}" )
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"erro": "Falha ao comunicar com a API do Google Maps."}), 502

# ==============================
# Rodar servidor
# ==============================
if __name__ == "__main__":
    if supabase:
        print("Iniciando o servidor Flask em modo de desenvolvimento...")
        app.run(debug=True)
    else:
        print("O servidor Flask não foi iniciado devido a uma falha na conexão com o banco de dados.")
