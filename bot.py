import telebot
import time
import random
import os
import logging
from datetime import datetime
from collections import deque

# ===== CONFIGURAÇÕES =====
BOT_TOKEN = os.getenv("BOT_TOKEN", "7631672822:AAEsGUxW9_Bt6TpjJRWlUEFqCei1ovqwSVw")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1002925417422")
LINKS_FILE = "links.txt"

# ⏰ CONFIGURAÇÕES DE TEMPO (em segundos)
TEMPO_MINIMO = 180    # 30 minutos
TEMPO_MAXIMO = 7200    # 2 horas
TEMPO_ALEATORIO_EXTRA = 600  # 10 minutos extras de variação

# 🔄 CONFIGURAÇÕES ANTI-REPETIÇÃO
PRODUTOS_SEM_REPETIR = 15  # Número de produtos únicos antes de repetir

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)

bot = telebot.TeleBot(BOT_TOKEN)

# ===== FUNÇÃO PARA CARREGAR PRODUTOS =====
def carregar_produtos():
    produtos = []
    try:
        with open(LINKS_FILE, "r", encoding="utf-8") as f:
            for i, linha in enumerate(f, 1):
                linha = linha.strip()
                if not linha or linha.startswith("#"):
                    continue
                    
                parts = linha.split("|")
                if len(parts) == 3 and all(part.strip() for part in parts):
                    produtos.append({
                        "titulo": parts[0].strip(),
                        "descricao": parts[1].strip(),
                        "link": parts[2].strip()
                    })
                    logging.info(f"✅ Produto carregado: {parts[0].strip()}")
                else:
                    logging.warning(f"⚠️ Linha {i}: formato incorreto - {linha}")
    except FileNotFoundError:
        logging.error(f"Arquivo {LINKS_FILE} não encontrado!")
    except Exception as e:
        logging.error(f"Erro ao carregar produtos: {e}")
    
    return produtos

# ===== FUNÇÃO PARA CALCULAR TEMPO ALEATÓRIO =====
def calcular_tempo_espera():
    """Calcula tempo aleatório entre 30 minutos e 2 horas + variação extra"""
    tempo_base = random.randint(TEMPO_MINIMO, TEMPO_MAXIMO)
    tempo_extra = random.randint(0, TEMPO_ALEATORIO_EXTRA)
    tempo_total = tempo_base + tempo_extra
    
    # Converte para minutos para exibir
    minutos_total = tempo_total // 60
    proximo_horario = datetime.now().timestamp() + tempo_total
    
    logging.info(f"⏰ Próximo envio em {minutos_total} minutos")
    logging.info(f"🕐 Próximo horário: {datetime.fromtimestamp(proximo_horario).strftime('%H:%M:%S')}")
    
    return tempo_total

# ===== GERADOR DE MENSAGENS VARIADAS =====
def gerar_mensagem(produto, ultimas_mensagens):
    introducoes = [
        "🔥 Achado do dia!",
        "💥 Promoção que tá voando!",
        "🚨 Oferta que vale cada centavo!",
        "👀 Dá uma olhada nisso!",
        "💰 Achado imperdível!",
        "🛒 Promo exclusiva de hoje!",
        "⚡ Essa aqui não vai durar muito!",
        "📦 Produto em alta — confere!",
        "⭐ Top tendência da semana!",
        "📣 Acabei de ver isso e lembrei de você!"
    ]

    chamadas = [
        "👉 Aproveita enquanto tá com desconto:",
        "🔗 Clica pra garantir o teu:",
        "💸 Tá mais barato que nunca:",
        "🎯 Eu não perderia essa se fosse tu:",
        "📲 Link direto aqui:",
        "✅ Confere o valor antes que acabe:",
        "🔥 Clica aqui e vê o preço agora:",
        "🕒 Últimas unidades disponíveis:",
        "💼 Oferta por tempo limitadíssimo:",
        "🚀 Só vai quem é esperto:"
    ]

    # Evitar repetições muito próximas
    intro = random.choice([i for i in introducoes if i not in ultimas_mensagens]) \
        if len(ultimas_mensagens) < len(introducoes) else random.choice(introducoes)
    call = random.choice([c for c in chamadas if c not in ultimas_mensagens]) \
        if len(ultimas_mensagens) < len(chamadas) else random.choice(chamadas)
    
    ultimas_mensagens.append(intro)
    ultimas_mensagens.append(call)
    if len(ultimas_mensagens) > 6:
        ultimas_mensagens.pop(0)
        ultimas_mensagens.pop(0)

    return (
        f"{intro}\n\n"
        f"📌 {produto['titulo']}\n"
        f"{produto['descricao']}\n\n"
        f"{call}\n"
        f"{produto['link']}"
    )

# ===== SISTEMA INTELIGENTE DE SELEÇÃO DE PRODUTOS =====
class GerenciadorProdutos:
    def __init__(self, produtos):
        self.todos_produtos = produtos.copy()
        self.produtos_disponiveis = produtos.copy()
        self.produtos_utilizados = deque(maxlen=PRODUTOS_SEM_REPETIR)
        self.contador_rodada = 0
        
    def obter_produto(self):
        # Se já usou muitos produtos únicos, reinicia a lista
        if not self.produtos_disponiveis:
            self.produtos_disponiveis = self.todos_produtos.copy()
            self.contador_rodada += 1
            logging.info(f"🔄 Rodada {self.contador_rodada} iniciada - {len(self.produtos_disponiveis)} produtos disponíveis")
        
        # Remove produtos recentemente usados das opções
        produtos_validos = [p for p in self.produtos_disponiveis 
                          if p['titulo'] not in [pu['titulo'] for pu in self.produtos_utilizados]]
        
        # Se não há produtos válidos (todos foram usados recentemente), 
        # usa qualquer um disponível
        if not produtos_validos:
            produto = random.choice(self.produtos_disponiveis)
        else:
            produto = random.choice(produtos_validos)
        
        # Remove o produto escolhido da lista de disponíveis
        if produto in self.produtos_disponiveis:
            self.produtos_disponiveis.remove(produto)
        
        # Adiciona aos produtos utilizados recentemente
        self.produtos_utilizados.append(produto)
        
        logging.info(f"📦 Produtos restantes nesta rodada: {len(self.produtos_disponiveis)}")
        return produto

# ===== LOOP PRINCIPAL =====
def main_loop():
    logging.info("🤖 Iniciando bot com sistema anti-repetição...")
    produtos = carregar_produtos()
    if not produtos:
        logging.error("Nenhum produto válido encontrado! Verifique o arquivo links.txt")
        return False

    # 🆕 NOVO: Sistema inteligente de produtos
    gerenciador = GerenciadorProdutos(produtos)
    ultimas_mensagens = []
    contador = 0

    logging.info(f"🎯 Sistema configurado: {len(produtos)} produtos, {PRODUTOS_SEM_REPETIR} produtos únicos consecutivos")

    while True:
        try:
            # 🆕 NOVO: Usa o gerenciador em vez de random.choice
            produto = gerenciador.obter_produto()
            mensagem = gerar_mensagem(produto, ultimas_mensagens)
            bot.send_message(CHANNEL_ID, mensagem, parse_mode="Markdown")
            contador += 1

            logging.info(f"✅ [{contador}] Enviada: {produto['titulo']}")
            if contador % 10 == 0:
                logging.info(f"📊 Total de {contador} mensagens enviadas")

            # Tempo de espera variável
            tempo_espera = calcular_tempo_espera()
            logging.info(f"💤 Aguardando {tempo_espera//60} minutos até o próximo envio...")
            time.sleep(tempo_espera)

        except telebot.apihelper.ApiException as e:
            logging.error(f"❌ Erro da API Telegram: {e}")
            logging.info("🔄 Tentando novamente em 60 segundos...")
            time.sleep(60)
        except Exception as e:
            logging.error(f"❌ Erro inesperado: {e}")
            logging.info("🔄 Reiniciando em 30 segundos...")
            time.sleep(30)

# ===== EXECUÇÃO =====
if __name__ == "__main__":
    if not BOT_TOKEN or BOT_TOKEN.startswith("763167"):
        logging.warning("⚠️ AVISO: Configure a variável de ambiente BOT_TOKEN para segurança.")
    
    while True:
        try:
            main_loop()
        except KeyboardInterrupt:
            logging.info("👋 Bot interrompido manualmente.")
            break
        except Exception as e:
            logging.error(f"💥 Erro crítico no loop principal: {e}")
            logging.info("🔄 Reiniciando em 60 segundos...")
            time.sleep(60)