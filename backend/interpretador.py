
import re
import unicodedata
from datetime import date

from database import get_connection


MONTHS = {
    "janeiro": 1, "fevereiro": 2, "marco": 3,
    "abril": 4, "maio": 5, "junho": 6,
    "julho": 7, "agosto": 8, "setembro": 9,
    "outubro": 10, "novembro": 11, "dezembro": 12,
}


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )
    return texto.lower().strip()


def carregar_skills():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT DISTINCT nome_skill FROM "InHire".skills'
            )
            return [row[0] for row in cursor.fetchall()]


def carregar_cargos():
    query = """
        SELECT DISTINCT d.valor_dominio
        FROM "InHire".colaboradores c
        JOIN "InHire".dominios d
            ON d.id = c.id_cargo
        WHERE c.status = TRUE
          AND c.deletado IS DISTINCT FROM TRUE
          AND d.valor_dominio IS NOT NULL
        ORDER BY d.valor_dominio
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return [linha[0] for linha in cursor.fetchall()]


def adicionar_meses(ano, mes, quantidade):
    indice = ano * 12 + mes - 1 + quantidade
    return indice // 12, indice % 12 + 1


def interpretar_solicitacao(texto):
    texto_normalizado = normalizar(texto)
    hoje = date.today()


    skills_encontradas = []

    for skill in carregar_skills():
        nome = normalizar(skill)

        # Nome completo da competência
        nome_encontrado = bool(
            re.search(
                rf"(?<!\w){re.escape(nome)}(?!\w)",
                texto_normalizado,
            )
        )

        # Nome principal antes dos parênteses
        nome_principal = normalizar(
            skill.split("(")[0]
        ).strip()

        nome_principal_encontrado = bool(
            re.search(
                rf"(?<!\w){re.escape(nome_principal)}(?!\w)",
                texto_normalizado,
            )
        )

        if nome_encontrado or nome_principal_encontrado:
            skills_encontradas.append(skill)

    percentual = re.search(
        r"(\d{1,3})\s*%",
        texto_normalizado,
    )

    disponibilidade = (
        int(percentual.group(1))
        if percentual else None
    )


    periodo = []

    # Identifica datas numéricas: 01/2027 ou 01-2027
    data_numerica = re.search(
        r"\b(0?[1-9]|1[0-2])[/\-](\d{4})\b",
        texto_normalizado,
    )

    # Identifica período explícito: outubro a dezembro de 2026
    meses_explicitos = re.search(
        r"(?:de\s+)?("
        + "|".join(MONTHS)
        + r")\s+a\s+("
        + "|".join(MONTHS)
        + r")\s+de\s+(\d{4})",
        texto_normalizado,
    )

    # Identifica quantidade: próximos 6 meses
    quantidade = re.search(
        r"proximos\s+(\d+)\s+meses",
        texto_normalizado,
    )

    if meses_explicitos:
        mes_inicio = MONTHS[meses_explicitos.group(1)]
        mes_fim = MONTHS[meses_explicitos.group(2)]
        ano_inicio = int(meses_explicitos.group(3))

        ano_fim = (
            ano_inicio + 1
            if mes_fim < mes_inicio
            else ano_inicio
        )

        ano, mes = ano_inicio, mes_inicio

        while (ano, mes) <= (ano_fim, mes_fim):
            periodo.append((ano, mes))
            ano, mes = adicionar_meses(ano, mes, 1)

    else:
        # Quantidade de meses solicitada ou padrão de 3 meses
        total = (
            int(quantidade.group(1))
            if quantidade
            else 3
        )

        # Data inicial explícita tem prioridade sobre o mês atual
        if data_numerica:
            mes_inicio = int(data_numerica.group(1))
            ano_inicio = int(data_numerica.group(2))
        else:
            mes_inicio = hoje.month
            ano_inicio = hoje.year

        for indice in range(total):
            periodo.append(
                adicionar_meses(
                    ano_inicio,
                    mes_inicio,
                    indice,
                )
            )

    
    quantidade_solicitada = re.search(
    r"\b(?:quero|preciso de|busco|encontre|selecione)\s+"
    r"(\d+)\s+"
    r"(?:colaboradores|profissionais|pessoas|candidatos|funcionarios|"
    r"analistas|desenvolvedores|engenheiros|arquitetos|"
    r"administradores|tecnicos|assistentes|coordenadores|"
    r"especialistas|gerentes|estagiarios|trainees)\b",
    texto_normalizado,
    )

    quantidade_candidatos = (
        int(quantidade_solicitada.group(1))
        if quantidade_solicitada
        else 1
    )
    
    senioridades = {
        "trainee": "Trainee",
        "junior": "Júnior",
        "pleno": "Pleno",
        "senior": "Sênior",
    }

    senioridade = None

    for termo, descricao in senioridades.items():
        padrao = rf"\b{termo}(?:es|s)?\b"

        if re.search(padrao, texto_normalizado):
            senioridade = descricao
            break

    
    
    cargo = None

    cargos = sorted(
        carregar_cargos(),
        key=lambda nome: len(normalizar(nome)),
        reverse=True,
    )

    for nome_cargo in cargos:
        nome_normalizado = normalizar(nome_cargo)

        # Permite singular ou plural na primeira palavra
        palavras = nome_normalizado.split(" ", 1)

        if len(palavras) == 2:
            primeira, restante = palavras

            padrao = (
                rf"(?<!\w){re.escape(primeira)}s?"
                rf"\s+{re.escape(restante)}(?!\w)"
            )
        else:
            padrao = (
                rf"(?<!\w){re.escape(nome_normalizado)}s?(?!\w)"
            )

        if re.search(padrao, texto_normalizado):
            cargo = nome_cargo
            break

    return {
        "tipo": "colaborador",
        "senioridade": senioridade,
        "skills": list(dict.fromkeys(skills_encontradas)),
        "percentual": disponibilidade,
        "periodo": periodo,
        "quantidade_candidatos": quantidade_candidatos,
        "cargo": cargo,
    }


if __name__ == "__main__":
    solicitacao = input("\nO que você procura? ")

    filtros = interpretar_solicitacao(solicitacao)

    print("\nFILTROS IDENTIFICADOS\n")
    print("Tipo:", filtros["tipo"])
    print("Cargo:", filtros["cargo"])
    print("Senioridade:", filtros["senioridade"])
    print("Skills:", filtros["skills"])
    print("Disponibilidade:", filtros["percentual"])
    print("Período:", filtros["periodo"])
