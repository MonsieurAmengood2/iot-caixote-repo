# app.py
from flask import Flask, request, render_template_string, jsonify, redirect, url_for, session
from datetime import datetime
import os

app = Flask(__name__)

# —————————————————————— Variáveis de ambiente obrigatórias ——————————————————————
# Se alguma destas não estiver definida, a app falha no arranque.
app.secret_key = os.environ["SECRET_KEY"]
USERNAME = os.environ["FLASK_USER"]
PASSWORD = os.environ["FLASK_PASS"]

# —————————————————————— HISTÓRICO DO CAIXOTE ——————————————————————
historico_lixo = []

# —————————————————————— ROTA PARA REGISTRO DO CAIXOTE ——————————————————————
@app.route('/registo_lixo', methods=['GET'])
def registo_lixo():
    """
    Recebe por query string:
      - nivel   : nível do caixote em %
      - deposito: contador de vezes que o caixote foi aberto
    Exemplo:
      GET /registo_lixo?nivel=45.3&deposito=7
    """
    nivel = request.args.get("nivel", "")
    contador = request.args.get("deposito", "")
    hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    historico_lixo.insert(0, {"hora": hora, "nivel": nivel, "deposito": contador})
    return "OK", 200

# —————————————————————— ROTA DE LOGIN ——————————————————————
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
    <html><head><title>Login</title><style>
    body { font-family: sans-serif; background: #e8f0fe; display: flex; justify-content: center; align-items: center; height: 100vh; }
    .card { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.2); width: 300px; }
    input { width: 100%; padding: 10px; margin: 10px 0; }
    button { width: 100%; padding: 10px; background: #4CAF50; color: white; border: none; border-radius: 5px; }
    .erro { color: red; font-size: 0.9em; }
    </style></head><body>
    <form method="POST">
        <div class="card">
            <h2>🔐 Login</h2>
            <input type="text" name="username" placeholder="Utilizador" required>
            <input type="password" name="password" placeholder="Palavra-passe" required>
            <button type="submit">Entrar</button>
            <p class="erro">{{ erro }}</p>
        </div>
    </form></body></html>
    """, erro=erro)

# —————————————————————— DASHBOARD DO CAIXOTE ——————————————————————
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    html = """
    <!DOCTYPE html><html><head>
    <title>🚮 Dashboard do Caixote de Lixo</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
      body { font-family: sans-serif; padding: 20px; background: #f4f4f4; }
      h1 { color: #2c3e50; margin-bottom: 15px; }
      .card { background: white; padding: 12px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 8px; }
      .nivel { float: right; color: #FF9800; font-weight: bold; }
      .deposito { float: right; color: #2196F3; font-weight: bold; margin-left: 15px; }
      .alerta { background: #ffdddd; color: #b00; }
      .popup { background: #fff3cd; color: #856404; padding: 10px 15px; border: 1px solid #ffeeba; border-radius: 6px; margin-bottom: 15px; }
    </style></head><body>
      <h1>🚮 Histórico do Caixote de Lixo</h1>
      <div id="popup_lixo"></div>
      <p>Total de eventos: <strong id="total_lixo">0</strong></p>
      <canvas id="grafico_lixo" width="400" height="150"></canvas>
      <div id="historico_lixo"></div>

    <script>
    function atualizarLixo() {
        fetch('/historico_lixo').then(r => r.json()).then(data => {
            document.getElementById("total_lixo").innerText = data.length;
            const divL = document.getElementById("historico_lixo");
            divL.innerHTML = "";
            const labelsL = [], niveisL = [], contagensL = [];
            let cheioDetectado = false;

            data.slice().reverse().forEach(e => {
                const c = document.createElement("div");
                const nivelNum = parseFloat(e.nivel) || 0;
                const isCheio = nivelNum > 80;  // alerta se > 80%
                if (isCheio) cheioDetectado = true;
                c.className = "card" + (isCheio ? " alerta" : "");
                c.innerHTML = `<span>${e.hora}</span>
                               <span class='nivel'>Nível: ${e.nivel}%</span>
                               <span class='deposito'>Contagem: ${e.deposito}</span>`;
                divL.appendChild(c);

                labelsL.push(e.hora.split(" ")[1]);
                niveisL.push(nivelNum);
                contagensL.push(parseInt(e.deposito) || 0);
            });

            if (cheioDetectado) {
                document.getElementById("popup_lixo").innerHTML =
                  "<div class='popup'>⚠️ Atenção: nível do caixote acima de 80%!</div>";
            } else {
                document.getElementById("popup_lixo").innerHTML = "";
            }

            const ctxL = document.getElementById("grafico_lixo").getContext("2d");
            if (window.grafLixo) window.grafLixo.destroy();
            window.grafLixo = new Chart(ctxL, {
                type: 'line',
                data: {
                    labels: labelsL,
                    datasets: [
                      {
                        label: 'Nível (%)',
                        data: niveisL,
                        backgroundColor: 'rgba(255, 152, 0, 0.2)',
                        borderColor: '#FF9800',
                        borderWidth: 2
                      },
                      {
                        label: 'Contagem',
                        data: contagensL,
                        backgroundColor: 'rgba(33, 150, 243, 0.2)',
                        borderColor: '#2196F3',
                        borderWidth: 2
                      }
                    ]
                },
                options: {
                  scales: { y: { beginAtZero: true } }
                }
            });
        });
    }

    setInterval(atualizarLixo, 3000);
    atualizarLixo();
    </script>
    </body></html>
    """
    return render_template_string(html)

# —————————————————————— ROTA QUE RETORNA O HISTÓRICO EM JSON ——————————————————————
@app.route('/historico_lixo')
def historico_lixo_json():
    return jsonify(historico_lixo[:20])

# —————————————————————— INICIALIZAÇÃO DO SERVIDOR ——————————————————————
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
