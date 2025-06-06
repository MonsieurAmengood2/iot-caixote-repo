# app.py
from flask import Flask, request, render_template_string, jsonify, redirect, url_for, session
from datetime import datetime
import os

app = Flask(__name__)

# —————————————————————— Variáveis de ambiente obrigatórias ——————————————————————
# Se alguma destas não estiver definida, a app falha no arranque.
#
#   - SECRET_KEY: usada pelo Flask para criptografar sessões
#   - FLASK_USER : nome de utilizador para acesso ao dashboard
#   - FLASK_PASS : senha para acesso ao dashboard
# Certifique-se de definir estas variáveis no ambiente onde a app vai correr.
app.secret_key = os.environ["SECRET_KEY"]
USERNAME = os.environ["FLASK_USER"]
PASSWORD = os.environ["FLASK_PASS"]

# —————————————————————— HISTÓRICO DO CAIXOTE (apenas “hora” e “contagem”) ——————————————————————
# Cada entrada é um dicionário {"hora": "2025-06-06 13:07:25", "deposito": "1"}
historico_lixo = []

# —————————————————————— ROTA PARA REGISTRO DO CAIXOTE ——————————————————————
@app.route('/registo_lixo', methods=['GET'])
def registo_lixo():
    """
    Recebe por query string apenas:
      - deposito: inteiro ou string que representa quantas vezes a tampa foi aberta.

    Exemplo de chamada:
      GET /registo_lixo?deposito=7

    O código registra o timestamp atual (data+hora) e o valor de `deposito` em
    uma lista interna `historico_lixo`. Ele insere no início (índice 0), para
    que a lista mantenha os eventos mais recentes primeiro.

    Retorna:
      "OK", 200
    """
    contador = request.args.get("deposito", "")
    hora_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Adiciona nova entrada no topo da lista
    historico_lixo.insert(0, {"hora": hora_atual, "deposito": contador})
    return "OK", 200

# —————————————————————— ROTA DE LOGIN ——————————————————————
@app.route('/', methods=['GET', 'POST'])
def login():
    erro = ""
    if request.method == 'POST':
        # Verifica credenciais
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['user'] = USERNAME
            return redirect(url_for('dashboard'))
        else:
            erro = "Credenciais inválidas"
    # Renderiza formulário de login (HTML inline)
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
      <meta charset="UTF-8" />
      <title>🔐 Login</title>
      <style>
        body {
          font-family: sans-serif;
          background: #e8f0fe;
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100vh;
          margin: 0;
        }
        .card {
          background: white;
          padding: 30px;
          border-radius: 10px;
          box-shadow: 0 0 10px rgba(0,0,0,0.2);
          width: 300px;
        }
        input {
          width: 100%;
          padding: 10px;
          margin: 10px 0;
          box-sizing: border-box;
        }
        button {
          width: 100%;
          padding: 10px;
          background: #4CAF50;
          color: white;
          border: none;
          border-radius: 5px;
          cursor: pointer;
        }
        button:hover {
          background: #45A049;
        }
        .erro {
          color: red;
          font-size: 0.9em;
          margin-top: 5px;
        }
      </style>
    </head>
    <body>
      <form method="POST">
        <div class="card">
          <h2>🔐 Login</h2>
          <input type="text" name="username" placeholder="Utilizador" required />
          <input type="password" name="password" placeholder="Palavra-passe" required />
          <button type="submit">Entrar</button>
          <p class="erro">{{ erro }}</p>
        </div>
      </form>
    </body>
    </html>
    """, erro=erro)

# —————————————————————— DASHBOARD DO CAIXOTE (apenas contagem) ——————————————————————
@app.route('/dashboard')
def dashboard():
    # Se não estiver autenticado, redireciona para login
    if 'user' not in session:
        return redirect(url_for('login'))

    # HTML inline do Dashboard
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
      <meta charset="UTF-8" />
      <title>🚮 Dashboard do Caixote de Lixo</title>
      <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
      <style>
        body {
          font-family: sans-serif;
          padding: 20px;
          background: #f4f4f4;
          margin: 0;
        }
        h1 {
          color: #2c3e50;
          margin-bottom: 15px;
          display: flex;
          align-items: center;
        }
        h1 img {
          height: 32px;
          margin-right: 10px;
        }
        h1 span {
          vertical-align: middle;
        }
        .card {
          background: white;
          padding: 12px;
          border-radius: 8px;
          box-shadow: 0 2px 5px rgba(0,0,0,0.1);
          margin-bottom: 8px;
          display: flex;
          justify-content: space-between;
          font-size: 0.95em;
        }
        .deposito {
          color: #2196F3;
          font-weight: bold;
        }
        canvas {
          background: white;
          border-radius: 8px;
          box-shadow: 0 2px 5px rgba(0,0,0,0.1);
          margin-bottom: 15px;
        }
      </style>
    </head>
    <body>
      <h1>
        <!-- Substitua o src pelo caminho correto do seu logo -->
        <img src="https://raw.githubusercontent.com/your-usuario/your-repo/main/logo.png" alt="Logo" />
        <span>🚮 Histórico do Caixote de Lixo</span>
      </h1>

      <p>Total de eventos: <strong id="total_lixo">0</strong></p>
      <canvas id="grafico_lixo" width="600" height="200"></canvas>
      <div id="historico_lixo"></div>

      <script>
        function atualizarLixo() {
          fetch('/historico_lixo')
            .then(response => response.json())
            .then(data => {
              // Exibe o total de eventos
              document.getElementById("total_lixo").innerText = data.length;

              // “Limpa” a lista de histórico
              const divL = document.getElementById("historico_lixo");
              divL.innerHTML = "";

              // Prepara arrays para o gráfico (somente “contagem”)
              const labelsL = [];
              const contagensL = [];

              // Percorre do mais antigo (embaixo) ao mais recente (cima)
              data.slice().reverse().forEach(item => {
                // Cria um cartão para cada evento:
                // ex.: { "hora": "2025-06-06 13:07:25", "deposito": "1" }
                const c = document.createElement("div");
                c.className = "card";
                c.innerHTML = `
                  <span>${item.hora}</span>
                  <span class="deposito">Contagem: ${item.deposito}</span>
                `;
                divL.appendChild(c);

                // Hora (só HH:MM:SS) para o rótulo do eixo X
                labelsL.push(item.hora.split(" ")[1]);
                contagensL.push(parseInt(item.deposito) || 0);
              });

              // Gera (ou reinicializa) o gráfico de linha
              const ctx = document.getElementById("grafico_lixo").getContext("2d");
              if (window.grafLixo) window.grafLixo.destroy();

              window.grafLixo = new Chart(ctx, {
                type: 'line',
                data: {
                  labels: labelsL,
                  datasets: [{
                    label: 'Contagem',
                    data: contagensL,
                    borderColor: '#2196F3',
                    backgroundColor: 'rgba(33, 150, 243, 0.2)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.2
                  }]
                },
                options: {
                  scales: {
                    y: {
                      beginAtZero: true,
                      precision: 0
                    }
                  },
                  plugins: {
                    legend: {
                      display: true,
                      position: 'top'
                    }
                  }
                }
              });
            })
            .catch(err => {
              console.error("Falha ao buscar /historico_lixo:", err);
            });
        }

        // Atualiza a cada 3 segundos
        setInterval(atualizarLixo, 3000);
        // Chamada inicial
        atualizarLixo();
      </script>
    </body>
    </html>
    """
    return render_template_string(html)

# —————————————————————— ROTA QUE RETORNA O HISTÓRICO EM JSON ——————————————————————
@app.route('/historico_lixo')
def historico_lixo_json():
    # Retorna somente as 20 primeiras entradas (índice 0 a 19).
    return jsonify(historico_lixo[:20])

# —————————————————————— INICIALIZAÇÃO DO SERVIDOR ——————————————————————
if __name__ == "__main__":
    # Porta padrão (8080), mas respeita variável de ambiente PORT (no Fly e outros PaaS)
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
