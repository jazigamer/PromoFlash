import telebot
import time
import random

BOT_TOKEN = "7631672822:AAEsGUxW9_Bt6TpjJRWlUEFqCei1ovqwSVw"
CHANNEL_ID = "@meuCanalDeOfertas"  # troca pelo teu canal
bot = telebot.TeleBot(BOT_TOKEN)

def carregar_produtos():
    produtos = []
    with open("links.txt", "r", encoding="utf-8") as f:
        linhas = f.readlines()
        for linha in linhas:
            parts = linha.strip().split("|")
            if len(parts) == 3:
                produtos.append({
                    "titulo": parts[0].strip(),
                    "descricao": parts[1].strip(),
                    "link": parts[2].strip()
                })
    return produtos

produtos = carregar_produtos()

while True:
    produto = random.choice(produtos)
    mensagem = f"💥 OFERTA RELÂMPAGO 💥\n{produto['titulo']}\n{produto['descricao']}\n👉 [Compre aqui]({produto['link']})"
    bot.send_message(CHANNEL_ID, mensagem, parse_mode="Markdown")
    print("Mensagem enviada:", produto["titulo"])
    time.sleep(3600)  # espera 1 hora
