from flask import Flask, request, render_template_string, jsonify, redirect, url_for, session
from datetime import datetime
import os
import json

app = Flask(__name__)

# —————————————————————— Variáveis obrigatórias ——————————————————————
app.secret_key = os.environ["SECRET_KEY"]
USERNAME = os.environ["FLASK_USER"]
PASSWORD = os.environ["FLASK_PASS"]

# —————————————————————— Caminho persistente no volume montado ——————————————————————
HISTORICO_FILE = "/data/historico.json"  # ⬅ volume persistente

def carregar_historico():
    if os.path.exists(HISTORICO_FILE):
        with open(HISTORICO_FILE, "r") as f:
            return json.load(f)
    return []

def salvar_historico():
    with open(HISTORICO_FILE, "w") as f:
        json.dump(historico_lixo, f)

historico_lixo = carregar_historico()

# —————————————————————— ROTA PARA REGISTRO DO CAIXOTE ——————————————————————
@app.route('/registo_lixo', methods=['GET'])
def registo_lixo():
    contador = request.args.get("deposito", "")
    hora_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Só registra se o valor for diferente do último
    if not historico_lixo or historico_lixo[0]["deposito"] != contador:
        historico_lixo.insert(0, {"hora": hora_atual, "deposito": contador})
        salvar_historico()
    return "OK", 200

# —————————————————————— LOGIN ——————————————————————
@app.route('/', methods=['GET', 'POST'])
def login():
    erro = ""
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['user'] = USERNAME
            return redirect(url_for('dashboard'))
        else:
            erro = "Credenciais inválidas"
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
      <meta charset="UTF-8">
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
        input, button {
          width: 100%;
          padding: 10px;
          margin: 10px 0;
        }
        button {
          background: #4CAF50;
          color: white;
          border: none;
          border-radius: 5px;
          cursor: pointer;
        }
        .erro {
          color: red;
          font-size: 0.9em;
        }
      </style>
    </head>
    <body>
      <form method="POST">
        <div class="card">
          <h2>🔐 Login</h2>
          <input type="text" name="username" placeholder="Utilizador" required>
          <input type="password" name="password" placeholder="Palavra-passe" required>
          <button type="submit">Entrar</button>
          <p class="erro">{{ erro }}</p>
        </div>
      </form>
    </body>
    </html>
    """, erro=erro)

# —————————————————————— DASHBOARD ——————————————————————
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
      <meta charset="UTF-8">
      <title>🚮 Dashboard do Caixote de Lixo</title>
      <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
      <style>
        body { font-family: sans-serif; padding: 20px; background: #f4f4f4; margin: 0; }
        h1 { color: #2c3e50; display: flex; align-items: center; margin-bottom: 15px; }
        .card { background: white; padding: 12px; border-radius: 8px; margin-bottom: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: flex; justify-content: space-between; }
        .deposito { color: #2196F3; font-weight: bold; }
        canvas { background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 15px; }
      </style>
    </head>
    <body>
      <h1>🚮 Histórico do Caixote de Lixo</h1>
      <p>Total de eventos: <strong id="total_lixo">0</strong></p>
      <canvas id="grafico_lixo" width="600" height="200"></canvas>
      <div id="historico_lixo"></div>

      <script>
        function atualizarLixo() {
          fetch('/historico_lixo')
            .then(response => response.json())
            .then(data => {
              document.getElementById("total_lixo").innerText = data.length;
              const divL = document.getElementById("historico_lixo");
              divL.innerHTML = "";

              const labelsL = [], contagensL = [];
              data.slice().reverse().forEach(item => {
                const c = document.createElement("div");
                c.className = "card";
                c.innerHTML = `<span>${item.hora}</span><span class="deposito">Contagem: ${item.deposito}</span>`;
                divL.appendChild(c);
                labelsL.push(item.hora.split(" ")[1]);
                contagensL.push(parseInt(item.deposito) || 0);
              });

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
                      suggestedMax: 10,
                      precision: 0
                    }
                  },
                  plugins: {
                    legend: { display: true, position: 'top' }
                  }
                }
              });
            })
            .catch(err => console.error("Erro ao buscar histórico:", err));
        }

        setInterval(atualizarLixo, 3000);
        atualizarLixo();
      </script>
    </body>
    </html>
    """)

# —————————————————————— API JSON ——————————————————————
@app.route('/historico_lixo')
def historico_lixo_json():
    return jsonify(historico_lixo[:20])

# —————————————————————— START SERVER ——————————————————————
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
