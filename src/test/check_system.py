import requests
import json
import time

URL = "http://127.0.0.1:8000/api/v1/chat"

def test_chat(msg, label):
    print(f"\n--- Teste: {label} ---")
    # Certifique-se de que o session_id muda se quiser testar memória nova
    payload = {"message": msg, "session_id": "test_monitor_v2", "level": "beginner"}

    start = time.time()
    try:
        # stream=True é o segredo para ver o chunking
        with requests.post(URL, json=payload, stream=True) as r:
            # Verifica se deu erro HTTP (404, 500, etc)
            if r.status_code != 200:
                print(f"❌ ERRO HTTP {r.status_code}: {r.text}")
                return ""

            print("Recebendo Stream:", end=" ", flush=True)
            full_text = ""
            for chunk in r.iter_content(chunk_size=None):
                if chunk:
                    text = chunk.decode("utf-8")
                    print(text, end="", flush=True)
                    full_text += text

        end = time.time()
        print(f"\n\n⏱️ Tempo Total: {end - start:.4f}s")
        return full_text
    except Exception as e:
        print(f"\n❌ Erro de conexão: {e}")
        return ""

if __name__ == "__main__":
    # 1. Primeira vez (Cache MISS - Vai demorar uns segundos)
    test_chat("Qual a diferença entre make e do?", "CACHE MISS (Esperado)")

    # 2. Segunda vez (Cache HIT - Deve ser instantâneo)
    test_chat("Qual a diferença entre make e do?", "CACHE HIT (Esperado)")

    # 3. Variação (Cache HIT Semântico - Frase diferente, mesmo sentido)
    test_chat("Explique make vs do", "CACHE HIT SEMÂNTICO (Teste de Elite)")
