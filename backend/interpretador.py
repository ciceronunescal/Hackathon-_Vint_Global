import re
import unicodedata
from datetime import date
from difflib import SequenceMatcher

from database import get_connection

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None


MONTHS = {
    'janeiro': 1, 'fevereiro': 2, 'marco': 3, 'abril': 4,
    'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
    'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12,
}

ALIASES_SKILLS = {
    'py': 'python',
    'js': 'javascript',
    'ts': 'typescript',
    'reactjs': 'react',
    'react js': 'react',
    'nodejs': 'node.js',
    'node js': 'node.js',
    'postgres': 'postgresql',
}

# Apenas aliases relativamente inequívocos. Um alias só será usado
# se seu destino existir entre os cargos cadastrados.
ALIASES_CARGOS = {
    'dev backend': 'desenvolvedor backend',
    'dev front end': 'desenvolvedor frontend',
    'dev frontend': 'desenvolvedor frontend',
    'dev full stack': 'desenvolvedor fullstack',
    'dev fullstack': 'desenvolvedor fullstack',
}

SENIORIDADES = {
    'trainee': 'Trainee',
    'junior': 'Júnior',
    'pleno': 'Pleno',
    'senior': 'Sênior',
}

# Evita interpretar requisitos de prazo/disponibilidade como competências.
FINAL_REQUISITOS = re.compile(
    r'\b(?:\d{1,3}\s*%|a\s+partir\s+de|a\s+partir\s+do|'
    r'por\s+\d+\s+mes(?:es)?|durante\s+\d+\s+mes(?:es)?|'
    r'proximos?\s+\d+\s+mes(?:es)?|'
    r'em\s+(?:janeiro|fevereiro|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro|\d{1,2}[/\-]\d{4})|disponibilidade|disponivel|iniciando|inicio\s+em)',
    re.IGNORECASE,
)


def normalizar(texto):
    texto = unicodedata.normalize('NFKD', str(texto or ''))
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    texto = texto.lower().strip()
    texto = re.sub(r'\s+', ' ', texto)
    return texto


def canonico(texto):
    """Forma comparável: mantém letras/números, inclusive + e #."""
    texto = normalizar(texto)
    texto = re.sub(r'[^\w+#]+', ' ', texto, flags=re.UNICODE)
    return ' '.join(texto.split())


def carregar_skills():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                SELECT DISTINCT nome_skill
                FROM "InHire".skills
                WHERE nome_skill IS NOT NULL
                  AND status IS DISTINCT FROM FALSE
                  AND deletado IS DISTINCT FROM TRUE
                ORDER BY nome_skill
            ''')
            return [row[0] for row in cursor.fetchall()]


def carregar_cargos():
    query = '''
        SELECT DISTINCT d.valor_dominio
        FROM "InHire".colaboradores c
        JOIN "InHire".dominios d ON d.id = c.id_cargo
        WHERE c.status = TRUE
          AND c.deletado IS DISTINCT FROM TRUE
          AND d.valor_dominio IS NOT NULL
        ORDER BY d.valor_dominio
    '''
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return [row[0] for row in cursor.fetchall()]


def adicionar_meses(ano, mes, quantidade):
    indice = ano * 12 + mes - 1 + quantidade
    return indice // 12, indice % 12 + 1


def contem_termo(texto, termo):
    return bool(re.search(r'(?<!\w)' + re.escape(termo) + r'(?!\w)', texto))


def pontuacao(a, b):
    if fuzz is not None:
        return fuzz.ratio(a, b)
    return SequenceMatcher(None, a, b).ratio() * 100


def melhor_correspondencia(termo, opcoes, limite=88, margem=6):
    """Retorna (opcao, nota, confiavel); evita empates/termos curtos."""
    chave = canonico(termo)
    if len(chave) < 4 or len(opcoes) == 0:
        return None, 0, False

    resultados = sorted(
        ((pontuacao(chave, canonico(opcao)), opcao) for opcao in opcoes),
        reverse=True,
    )
    nota, opcao = resultados[0]
    segunda = resultados[1][0] if len(resultados) > 1 else 0
    return opcao, round(nota, 1), nota >= limite and nota - segunda >= margem


def variantes_skill(skill):
    completo = canonico(skill)
    principal = canonico(str(skill).split('(')[0])
    return set(filter(None, (completo, principal)))


def localizar_skills_exatas(texto, skills):
    texto_busca = f' {canonico(texto)} '
    encontradas = []
    trechos_encontrados = set()

    # Longas primeiro: uma competência específica prevalece sobre a genérica.
    for skill in sorted(skills, key=lambda s: max(map(len, variantes_skill(s))), reverse=True):
        for variante in sorted(variantes_skill(skill), key=len, reverse=True):
            padrao = re.compile(r'(?<!\w)' + re.escape(variante) + r'(?!\w)')
            match = padrao.search(texto_busca)
            if match:
                chave = (match.start(), match.end())
                if chave not in trechos_encontrados:
                    encontradas.append(skill)
                    trechos_encontrados.add(chave)
                break
    return encontradas


def extrair_termos_skills(texto):
    """Identifica itens em cláusulas explícitas de competências."""
    entrada = normalizar(texto)
    padrao = re.compile(
        r'\b(?:com|conhecimento(?:s)?\s+em|experiencia\s+em|'
        r'dominio\s+de|habilidade(?:s)?\s+em)\s+(.+?)(?=[.;\n]|$)'
    )
    termos = []
    for match in padrao.finditer(entrada):
        trecho = match.group(1)
        fim = FINAL_REQUISITOS.search(trecho)
        if fim:
            trecho = trecho[:fim.start()]
        for parte in re.split(r'\s*,\s*|\s+e\s+|\s+/\s+', trecho):
            fim_parte = FINAL_REQUISITOS.search(parte)
            if fim_parte:
                parte = parte[:fim_parte.start()]
            parte = parte.strip(' ,.;:')
            parte = re.sub(r'^(?:as?|os?)\s+', '', parte)
            if parte and len(canonico(parte)) >= 2:
                termos.append(parte)
    return termos


def analisar_skills(texto, skills):
    encontradas = localizar_skills_exatas(texto, skills)
    avisos = []
    correcoes = []
    desconhecidas = []

    # Índice somente para correspondência de termos explícitos.
    alternativas = {}
    for skill in skills:
        for variante in variantes_skill(skill):
            alternativas.setdefault(variante, []).append(skill)

    for alias, destino in ALIASES_SKILLS.items():
        candidatos = alternativas.get(canonico(destino), [])
        texto_alias = canonico(texto)
        if alias == 'js':
            # Nao trata o sufixo de Node.js/React JS como skill JavaScript avulsa.
            texto_alias = re.sub(r'(?<!\w)(?:node|react)\s+js(?!\w)', ' ', texto_alias)
        if len(candidatos) == 1 and contem_termo(texto_alias, canonico(alias)):
            if candidatos[0] not in encontradas:
                encontradas.append(candidatos[0])
                correcoes.append({'digitado': alias, 'interpretado': candidatos[0]})

    for termo in extrair_termos_skills(texto):
        chave = canonico(termo)
        if not chave:
            continue

        # Já está presente como competência exata ou como parte de uma
        # competência composta (ex.: "Python e Django" no próprio texto).
        if any(chave in variantes_skill(s) for s in encontradas):
            continue
        if chave in ALIASES_SKILLS and any(
            canonico(ALIASES_SKILLS[chave]) in variantes_skill(s) for s in encontradas
        ):
            continue

        # Aceita destino exato não ambíguo.
        exatas = alternativas.get(chave, [])
        if len(exatas) == 1:
            if exatas[0] not in encontradas:
                encontradas.append(exatas[0])
            continue
        if len(exatas) > 1:
            desconhecidas.append(termo)
            avisos.append(f'Competência ambígua: "{termo}". Verifique a denominação cadastrada.')
            continue

        limite = 82 if len(chave) >= 5 else 94
        opcao, nota, segura = melhor_correspondencia(chave, list(alternativas), limite, 8)
        if opcao and segura and len(alternativas[opcao]) == 1:
            skill = alternativas[opcao][0]
            if skill not in encontradas:
                encontradas.append(skill)
            correcoes.append({'digitado': termo, 'interpretado': skill})
        else:
            desconhecidas.append(termo)
            sugestao = f' Possível correspondência: "{alternativas[opcao][0]}".' if opcao and nota >= 65 and len(alternativas[opcao]) == 1 else ''
            avisos.append(f'Competência não reconhecida: "{termo}".{sugestao}')

    return list(dict.fromkeys(encontradas)), avisos, correcoes, list(dict.fromkeys(desconhecidas))


def analisar_cargo(texto, cargos):
    entrada = canonico(texto)
    for cargo in sorted(cargos, key=lambda s: len(canonico(s)), reverse=True):
        nome = canonico(cargo)
        palavras = nome.split(' ', 1)
        if len(palavras) == 2:
            primeira, restante = palavras
            padrao = rf'(?<!\w){re.escape(primeira)}s?\s+{re.escape(restante)}(?!\w)'
        else:
            padrao = rf'(?<!\w){re.escape(nome)}s?(?!\w)'
        if re.search(padrao, entrada):
            return cargo, [], []

    for alias, destino in ALIASES_CARGOS.items():
        if contem_termo(entrada, canonico(alias)):
            correspondentes = [c for c in cargos if canonico(c) == canonico(destino)]
            if len(correspondentes) == 1:
                return correspondentes[0], [], [{'digitado': alias, 'interpretado': correspondentes[0]}]

    # Limita fuzzy a frases com indicadores de função, para não confundir
    # uma frase de disponibilidade com nome de cargo.
    radicais = ('analista', 'desenvolvedor', 'engenheiro', 'arquiteto',
                'administrador', 'tecnico', 'assistente', 'coordenador',
                'especialista', 'gerente', 'estagiario', 'trainee', 'dev')
    palavras = entrada.split()
    candidatos = []
    for i, palavra in enumerate(palavras):
        if any(pontuacao(palavra.rstrip('s'), r) >= 78 for r in radicais):
            for largura in range(1, min(6, len(palavras) - i) + 1):
                frase = ' '.join(palavras[i:i+largura])
                # Exclui senioridade, normalmente separada do cargo.
                frase = re.sub(r'\s+(?:junior|pleno|senior|trainee)s?$', '', frase)
                candidatos.append(frase)

    if not candidatos:
        return None, [], []

    resultados = []
    for candidato in candidatos:
        opcao, nota, segura = melhor_correspondencia(candidato, cargos, 89, 6)
        if opcao:
            resultados.append((nota, segura, opcao, candidato))
    if not resultados:
        return None, [], []

    nota, segura, cargo, digitado = max(resultados, key=lambda x: x[0])
    if segura:
        return cargo, [], [{'digitado': digitado, 'interpretado': cargo}]
    if nota >= 70:
        return None, [f'Cargo não reconhecido com segurança. Possível cargo: "{cargo}".'], []
    return None, ['Não foi possível identificar o cargo informado.'], []




def interpretar_periodo(texto, hoje=None):
    """Retorna ([(ano, mes)], origem) sem consultar o banco.

    Origens: padrao, duracao, inicio, mes_especifico, intervalo.
    """
    hoje = hoje or date.today()
    texto = normalizar(texto)
    mes_rx = '|'.join(MONTHS)
    mes_ref = rf'(?:{mes_rx})'
    # O ano de um mes sem ano explicito e o proximo mes com esse nome.
    def resolver_mes(nome, ano=None):
        mes = MONTHS[nome]
        if ano:
            return int(ano), mes
        return (hoje.year + (mes < hoje.month)), mes

    def sequencia(inicio, total):
        if not 1 <= total <= 120:
            raise ValueError('O período deve estar entre 1 e 120 meses.')
        return [adicionar_meses(inicio[0], inicio[1], i) for i in range(total)]

    def intervalo(inicio, fim):
        total = (fim[0] - inicio[0]) * 12 + (fim[1] - inicio[1]) + 1
        if not 1 <= total <= 120:
            raise ValueError('O intervalo deve ter de 1 a 120 meses, em ordem cronológica.')
        return sequencia(inicio, total), 'intervalo'

    # 01/2027 a 03/2027, ou de 15/01/2027 ate 30/03/2027.
    intervalo_numerico = re.search(
        r'\b(?:de\s+)?(?:\d{1,2}/)?(0?[1-9]|1[0-2])[/\-](\d{4})'
        r'\s+(?:a|ate)\s+(?:\d{1,2}/)?(0?[1-9]|1[0-2])[/\-](\d{4})\b',
        texto,
    )
    if intervalo_numerico:
        m1, a1, m2, a2 = map(int, intervalo_numerico.groups())
        return intervalo((a1, m1), (a2, m2))

    # janeiro a marco de 2027; janeiro de 2027 a marco de 2028.
    intervalo_nomeado = re.search(
        rf'\b(?:de\s+)?({mes_rx})(?:\s+de\s+(\d{{4}}))?'
        rf'\s+(?:a|ate)\s+({mes_rx})(?:\s+de\s+(\d{{4}}))?\b',
        texto,
    )
    if intervalo_nomeado:
        nome1, ano1, nome2, ano2 = intervalo_nomeado.groups()
        if ano1:
            inicio = (int(ano1), MONTHS[nome1])
        elif ano2:
            # Quando o ano aparece apenas no fim, assumi-lo tambem no inicio.
            inicio = (int(ano2), MONTHS[nome1])
        else:
            inicio = resolver_mes(nome1)
        if ano2:
            fim = (int(ano2), MONTHS[nome2])
        elif ano1:
            fim = (int(ano1), MONTHS[nome2])
        else:
            fim = (inicio[0], MONTHS[nome2])
        if not ano2 and fim < inicio:
            fim = (fim[0] + 1, fim[1])
        return intervalo(inicio, fim)

    # Duracao explicita prevalece sobre o horizonte padrao.
    duracao = re.search(
        r'\b(?:proximos?\s+|por\s+|durante\s+)(\d+)\s+mes(?:es)?\b',
        texto,
    )
    total = int(duracao.group(1)) if duracao else 3
    if not 1 <= total <= 120:
        raise ValueError('O período deve estar entre 1 e 120 meses.')

    # A partir de / iniciando em / inicio em = tres meses (ou duracao dada).
    inicio_prefixo = r'(?:a\s+partir\s+(?:de|do)\s+|iniciando\s+em\s+|inicio\s+em\s+)'
    inicio_nomeado = re.search(
        rf'\b{inicio_prefixo}({mes_rx})(?:\s+de\s+(\d{{4}}))?\b', texto
    )
    inicio_numerico = re.search(
        rf'\b{inicio_prefixo}(?:\d{{1,2}}/)?(0?[1-9]|1[0-2])[/\-](\d{{4}})\b', texto
    )
    if inicio_numerico:
        mes, ano = map(int, inicio_numerico.groups())
        return sequencia((ano, mes), total), 'inicio'
    if inicio_nomeado:
        return sequencia(resolver_mes(*inicio_nomeado.groups()), total), 'inicio'

    # "em janeiro" ou "em 01/2027": apenas um mes, salvo duracao informada.
    # Inclui "no mes de janeiro" para evitar usar o horizonte de tres meses.
    pontual_prefixo = r'(?:em\s+|no\s+mes\s+de\s+)'
    pontual_nomeado = re.search(
        rf'\b{pontual_prefixo}({mes_rx})(?:\s+de\s+(\d{{4}}))?\b', texto
    )
    pontual_numerico = re.search(
        rf'\b{pontual_prefixo}(?:\d{{1,2}}/)?(0?[1-9]|1[0-2])[/\-](\d{{4}})\b', texto
    )
    if pontual_numerico:
        mes, ano = map(int, pontual_numerico.groups())
        return sequencia((ano, mes), total if duracao else 1), 'duracao' if duracao else 'mes_especifico'
    if pontual_nomeado:
        return sequencia(resolver_mes(*pontual_nomeado.groups()), total if duracao else 1), 'duracao' if duracao else 'mes_especifico'

    # Data numerica sem preposicao: considera inicio do periodo.
    numero_solto = re.search(r'\b(?:\d{1,2}/)?(0?[1-9]|1[0-2])[/\-](\d{4})\b', texto)
    if numero_solto:
        mes, ano = map(int, numero_solto.groups())
        return sequencia((ano, mes), total), 'inicio'

    # Mes citado isoladamente: necessidade pontual, se nao houver duracao.
    mes_solto = re.search(rf'\b({mes_rx})(?:\s+de\s+(\d{{4}}))?\b', texto)
    if mes_solto:
        return sequencia(resolver_mes(*mes_solto.groups()), total if duracao else 1), 'duracao' if duracao else 'mes_especifico'

    return sequencia((hoje.year, hoje.month), total), 'duracao' if duracao else 'padrao'

def interpretar_solicitacao(texto):
    texto_normalizado = normalizar(texto)
    hoje = date.today()

    skills, avisos, correcoes, desconhecidas = analisar_skills(
        texto, carregar_skills()
    )

    percentual = re.search(r'\b(\d{1,3})\s*%', texto_normalizado)
    disponibilidade = int(percentual.group(1)) if percentual else None
    if disponibilidade is not None and not 0 <= disponibilidade <= 100:
        raise ValueError('A disponibilidade deve estar entre 0% e 100%.')

    # Periodo: diferenciar mes pontual, data inicial e intervalos.
    periodo, origem_periodo = interpretar_periodo(texto_normalizado, hoje)

    quantidade_solicitada = re.search(
        r'\b(?:quero|preciso\s+de|busco|encontre|selecione)\s+'
        r'(\d+)\s+'
        r'(?:colaboradores|profissionais|pessoas|candidatos|funcionarios|'
        r'analistas|desenvolvedores|engenheiros|arquitetos|'
        r'administradores|tecnicos|assistentes|coordenadores|'
        r'especialistas|gerentes|estagiarios|trainees)\b',
        texto_normalizado,
    )
    quantidade_candidatos = int(quantidade_solicitada.group(1)) if quantidade_solicitada else 1

    senioridade = None
    for termo, descricao in SENIORIDADES.items():
        if re.search(rf'\b{termo}(?:es|s)?\b', texto_normalizado):
            senioridade = descricao
            break

    cargo, avisos_cargo, correcoes_cargo = analisar_cargo(
        texto, carregar_cargos()
    )
    avisos.extend(avisos_cargo)
    correcoes.extend(correcoes_cargo)

    return {
        'tipo': 'colaborador',
        'senioridade': senioridade,
        'skills': skills,
        'percentual': disponibilidade,
        'periodo': periodo,
        'origem_periodo': origem_periodo,
        'periodo_padrao': origem_periodo == 'padrao',
        'duracao_informada': bool(re.search(r'\b(?:proximos?\s+|por\s+|durante\s+)\d+\s+mes(?:es)?\b', texto_normalizado)),
        'quantidade_candidatos': quantidade_candidatos,
        'cargo': cargo,
        'avisos': avisos,
        'correcoes': correcoes,
        'termos_nao_reconhecidos': desconhecidas,
    }


if __name__ == '__main__':
    solicitacao = input('\nO que você procura? ')
    filtros = interpretar_solicitacao(solicitacao)
    print('\nFILTROS IDENTIFICADOS\n')
    for chave, valor in filtros.items():
        print(f'{chave}: {valor}')
