"""
MELH-003: Diagrama de Ishikawa (Espinha de Peixe) Dinâmico

Gera análise de causa raiz usando a metodologia 6M:
- Mão de Obra (Pessoal)
- Máquina (Equipamento)
- Método (Processo)
- Material (Insumos)
- Medição (Instrumentação)
- Meio Ambiente (Ambiente)

Substitui diagramas estáticos por análise dinâmica baseada em dados.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class CategoriaIshikawa(str, Enum):
    """Categorias 6M para Diagrama de Ishikawa"""
    MAO_DE_OBRA = "mao_de_obra"      # Fatores humanos/pessoal
    MAQUINA = "maquina"              # Problemas de equipamento
    METODO = "metodo"                # Processo/procedimentos
    MATERIAL = "material"            # Matérias-primas/insumos
    MEDICAO = "medicao"              # Instrumentação/sensores
    MEIO_AMBIENTE = "meio_ambiente"  # Fatores ambientais


class SeveridadeCausa(str, Enum):
    """Níveis de severidade das causas raiz"""
    CRITICA = "critica"      # Ação imediata necessária
    ALTA = "alta"            # Resolver em 24h
    MEDIA = "media"          # Resolver em 1 semana
    BAIXA = "baixa"          # Monitorar e planejar


@dataclass
class CausaRaiz:
    """Causa raiz individual identificada"""
    categoria: CategoriaIshikawa
    causa: str
    descricao: str
    severidade: SeveridadeCausa
    confianca: float  # 0.0 - 1.0
    evidencias: List[str] = field(default_factory=list)
    recomendacoes: List[str] = field(default_factory=list)
    tags_relacionadas: List[str] = field(default_factory=list)
    frequencia: int = 1  # Quantas vezes esta causa aparece


@dataclass
class DiagramaIshikawa:
    """Resultado completo da análise Ishikawa"""
    declaracao_problema: str
    gerado_em: datetime
    periodo_analise_horas: int
    categorias: Dict[str, List[CausaRaiz]]
    causa_primaria: Optional[CausaRaiz]
    total_causas_identificadas: int
    score_qualidade_dados: float
    recomendacoes: List[str]


class ServicoAnaliseIshikawa:
    """
    Gerador Dinâmico de Diagrama de Ishikawa

    Usa dados em tempo real para identificar causas raiz de problemas
    de qualidade, falhas de equipamento ou problemas de produção.
    """

    # Padrões de causa mapeados para categorias
    PADROES_CAUSA = {
        CategoriaIshikawa.MAO_DE_OBRA: {
            "padroes": [
                "erro_operador", "falta_treinamento", "fadiga", "comunicacao",
                "troca_turno", "erro_humano", "supervisao"
            ],
            "palavras_tag": ["operador", "manual", "humano", "usuario"],
            "palavras_alarme": ["operador", "manual", "bypass", "override", "interlock"]
        },
        CategoriaIshikawa.MAQUINA: {
            "padroes": [
                "falha_equipamento", "desgaste", "calibracao", "manutencao",
                "quebra", "mecanico", "eletrico"
            ],
            "palavras_tag": ["motor", "bomba", "valvula", "correia", "britador", "alimentador", "elevador", "transportador"],
            "palavras_alarme": ["falha", "trip", "sobrecarga", "quebra", "fault", "failure", "overload"]
        },
        CategoriaIshikawa.METODO: {
            "padroes": [
                "violacao_procedimento", "sequencia_errada", "timing", "pop",
                "desvio_processo", "receita", "batelada"
            ],
            "palavras_tag": ["setpoint", "receita", "batelada", "sequencia", "etapa"],
            "palavras_alarme": ["sequencia", "etapa", "procedimento", "desvio", "limite"]
        },
        CategoriaIshikawa.MATERIAL: {
            "padroes": [
                "contaminacao", "umidade", "mudanca_grade", "fornecedor",
                "especificacao", "qualidade", "variacao"
            ],
            "palavras_tag": ["material", "alimentacao", "entrada", "grade", "umidade", "ferro", "granulometria"],
            "palavras_alarme": ["qualidade", "contaminacao", "especificacao", "grade", "teor"]
        },
        CategoriaIshikawa.MEDICAO: {
            "padroes": [
                "deriva_sensor", "erro_calibracao", "falha_instrumento",
                "precisao", "exatidao", "range"
            ],
            "palavras_tag": ["sensor", "transmissor", "analisador", "balanca", "medidor", "vazao", "nivel", "pressao", "temperatura"],
            "palavras_alarme": ["sensor", "sinal", "comunicacao", "offline", "bad_quality", "comm_loss"]
        },
        CategoriaIshikawa.MEIO_AMBIENTE: {
            "padroes": [
                "temperatura_ambiente", "umidade", "clima", "sazonal",
                "poeira", "vento", "chuva"
            ],
            "palavras_tag": ["ambiente", "clima", "externo", "temperatura_ext", "umidade_ar"],
            "palavras_alarme": ["clima", "ambiente", "ambiental", "extremo", "chuva", "vento"]
        }
    }

    # Nomes em português das categorias
    NOMES_CATEGORIAS = {
        CategoriaIshikawa.MAO_DE_OBRA: "Mão de Obra",
        CategoriaIshikawa.MAQUINA: "Máquina",
        CategoriaIshikawa.METODO: "Método",
        CategoriaIshikawa.MATERIAL: "Material",
        CategoriaIshikawa.MEDICAO: "Medição",
        CategoriaIshikawa.MEIO_AMBIENTE: "Meio Ambiente"
    }

    ICONES_CATEGORIAS = {
        CategoriaIshikawa.MAO_DE_OBRA: "👤",
        CategoriaIshikawa.MAQUINA: "⚙️",
        CategoriaIshikawa.METODO: "📋",
        CategoriaIshikawa.MATERIAL: "📦",
        CategoriaIshikawa.MEDICAO: "📏",
        CategoriaIshikawa.MEIO_AMBIENTE: "🌡️"
    }

    def __init__(self):
        """Inicializa o serviço de análise Ishikawa"""
        self.cache_analise: Dict[str, DiagramaIshikawa] = {}
        logger.info("ServicoAnaliseIshikawa inicializado")

    async def analisar(
        self,
        declaracao_problema: str,
        alarmes: List[Dict[str, Any]],
        dados_tags: List[Dict[str, Any]],
        eventos: Optional[List[Dict[str, Any]]] = None,
        horas: int = 24
    ) -> DiagramaIshikawa:
        """
        Gera diagrama de Ishikawa dinâmico a partir de dados operacionais.

        Args:
            declaracao_problema: Descrição do problema a analisar
            alarmes: Eventos de alarme recentes
            dados_tags: Snapshots de valores de tags com anomalias
            eventos: Eventos adicionais opcionais (trocas de turno, manutenção, etc.)
            horas: Período de análise em horas

        Returns:
            DiagramaIshikawa com causas raiz categorizadas
        """
        logger.info(f"Gerando análise Ishikawa para: {declaracao_problema}")

        categorias: Dict[str, List[CausaRaiz]] = {
            cat.value: [] for cat in CategoriaIshikawa
        }

        # Analisar alarmes para causas raiz
        causas_alarme = self._analisar_alarmes(alarmes, horas)
        for causa in causas_alarme:
            categorias[causa.categoria.value].append(causa)

        # Analisar dados de tags para padrões
        causas_tags = self._analisar_tags(dados_tags, horas)
        for causa in causas_tags:
            categorias[causa.categoria.value].append(causa)

        # Analisar eventos se fornecidos
        if eventos:
            causas_eventos = self._analisar_eventos(eventos, horas)
            for causa in causas_eventos:
                categorias[causa.categoria.value].append(causa)

        # Deduplicar e rankear causas dentro de cada categoria
        for nome_cat in categorias:
            categorias[nome_cat] = self._deduplicar_causas(categorias[nome_cat])
            categorias[nome_cat] = sorted(
                categorias[nome_cat],
                key=lambda c: (c.severidade.value, -c.confianca),
                reverse=False  # Crítico primeiro
            )

        # Encontrar causa primária
        todas_causas = [c for causas in categorias.values() for c in causas]
        causa_primaria = self._identificar_causa_primaria(todas_causas)

        # Gerar recomendações
        recomendacoes = self._gerar_recomendacoes(categorias, causa_primaria)

        # Calcular score de qualidade dos dados
        qualidade_dados = self._calcular_qualidade_dados(alarmes, dados_tags, eventos)

        diagrama = DiagramaIshikawa(
            declaracao_problema=declaracao_problema,
            gerado_em=datetime.utcnow(),
            periodo_analise_horas=horas,
            categorias=categorias,
            causa_primaria=causa_primaria,
            total_causas_identificadas=len(todas_causas),
            score_qualidade_dados=qualidade_dados,
            recomendacoes=recomendacoes
        )

        # Cachear resultado
        chave_cache = f"{declaracao_problema[:50]}_{horas}h"
        self.cache_analise[chave_cache] = diagrama

        logger.info(f"Análise Ishikawa completa: {len(todas_causas)} causas identificadas")
        return diagrama

    def _analisar_alarmes(self, alarmes: List[Dict], horas: int) -> List[CausaRaiz]:
        """Extrai causas raiz dos dados de alarme"""
        causas = []

        for alarme in alarmes:
            tipo_alarme = alarme.get("alarm_type", "").lower()
            tag_id = alarme.get("tag_id", "")
            mensagem = alarme.get("message", "").lower()
            contagem = alarme.get("count", 1)

            categoria = self._classificar_alarme(tipo_alarme, tag_id, mensagem)
            severidade = self._determinar_severidade(alarme)

            causa = CausaRaiz(
                categoria=categoria,
                causa=alarme.get("alarm_type", "Alarme Desconhecido"),
                descricao=alarme.get("message", f"Alarme em {tag_id}"),
                severidade=severidade,
                confianca=min(0.5 + (contagem * 0.1), 0.95),  # Maior contagem = maior confiança
                evidencias=[f"Alarme ocorreu {contagem} vezes em {horas}h"],
                recomendacoes=self._obter_recomendacoes_alarme(categoria, tipo_alarme),
                tags_relacionadas=[tag_id] if tag_id else [],
                frequencia=contagem
            )
            causas.append(causa)

        return causas

    def _analisar_tags(self, dados_tags: List[Dict], horas: int) -> List[CausaRaiz]:
        """Extrai causas raiz de anomalias nos valores de tags"""
        causas = []

        for tag in dados_tags:
            tag_id = tag.get("tag_id", "")
            nome_tag = tag.get("name", tag_id).lower()
            valor = tag.get("value")
            qualidade = tag.get("quality", "GOOD")
            tem_anomalia = tag.get("is_anomaly", False)
            cv = tag.get("coefficient_of_variation", 0)

            # Pular tags com boa qualidade e estáveis
            if qualidade == "GOOD" and not tem_anomalia and cv < 15:
                continue

            categoria = self._classificar_tag(tag_id, nome_tag)

            # Qualidade ruim indica problemas de medição
            if qualidade in ["BAD", "UNCERTAIN", "COMM_LOSS"]:
                causa = CausaRaiz(
                    categoria=CategoriaIshikawa.MEDICAO,
                    causa=f"Problema de Qualidade do Sinal: {qualidade}",
                    descricao=f"Tag {nome_tag} mostrando qualidade {qualidade}",
                    severidade=SeveridadeCausa.ALTA if qualidade == "COMM_LOSS" else SeveridadeCausa.MEDIA,
                    confianca=0.85,
                    evidencias=[f"Status de qualidade: {qualidade}"],
                    recomendacoes=[
                        "Verificar fiação e conexões do sensor",
                        "Verificar alimentação do transmissor",
                        "Checar interferência eletromagnética"
                    ],
                    tags_relacionadas=[tag_id]
                )
                causas.append(causa)

            # Alta variabilidade indica instabilidade do processo
            if cv > 25:
                causa = CausaRaiz(
                    categoria=categoria,
                    causa=f"Alta Variabilidade do Processo",
                    descricao=f"Tag {nome_tag} mostrando {cv:.1f}% de CV (limite: 25%)",
                    severidade=SeveridadeCausa.MEDIA if cv < 50 else SeveridadeCausa.ALTA,
                    confianca=0.7,
                    evidencias=[f"Coeficiente de Variação: {cv:.1f}%"],
                    recomendacoes=[
                        "Revisar sintonia da malha de controle",
                        "Verificar perturbações a montante",
                        "Verificar estabilidade do setpoint"
                    ],
                    tags_relacionadas=[tag_id]
                )
                causas.append(causa)

            # Anomalia detectada
            if tem_anomalia:
                causa = CausaRaiz(
                    categoria=categoria,
                    causa=f"Anomalia Detectada",
                    descricao=f"Modelo detectou anomalia em {nome_tag}",
                    severidade=SeveridadeCausa.ALTA,
                    confianca=tag.get("anomaly_confidence", 0.75),
                    evidencias=[
                        f"Valor atual: {valor}",
                        f"Faixa esperada: {tag.get('expected_min')} - {tag.get('expected_max')}"
                    ],
                    recomendacoes=[
                        "Investigar mudanças recentes",
                        "Verificar equipamentos relacionados",
                        "Revisar histórico de manutenção"
                    ],
                    tags_relacionadas=[tag_id]
                )
                causas.append(causa)

        return causas

    def _analisar_eventos(self, eventos: List[Dict], horas: int) -> List[CausaRaiz]:
        """Extrai causas raiz de eventos operacionais"""
        causas = []

        for evento in eventos:
            tipo_evento = evento.get("type", "").lower()
            descricao = evento.get("description", "")

            if "turno" in tipo_evento or "handover" in tipo_evento:
                causa = CausaRaiz(
                    categoria=CategoriaIshikawa.MAO_DE_OBRA,
                    causa="Troca de Turno",
                    descricao=f"Troca de turno ocorreu: {descricao}",
                    severidade=SeveridadeCausa.BAIXA,
                    confianca=0.4,
                    evidencias=[f"Evento: {descricao}"],
                    recomendacoes=[
                        "Revisar procedimentos de passagem de turno",
                        "Verificar tarefas incompletas na troca de turno"
                    ]
                )
                causas.append(causa)

            elif "manutencao" in tipo_evento or "maintenance" in tipo_evento:
                causa = CausaRaiz(
                    categoria=CategoriaIshikawa.MAQUINA,
                    causa="Manutenção Recente",
                    descricao=f"Atividade de manutenção: {descricao}",
                    severidade=SeveridadeCausa.MEDIA,
                    confianca=0.6,
                    evidencias=[f"Evento de manutenção: {descricao}"],
                    recomendacoes=[
                        "Verificar se manutenção foi concluída corretamente",
                        "Checar resultados dos testes pós-manutenção"
                    ]
                )
                causas.append(causa)

            elif "material" in tipo_evento or "grade" in tipo_evento:
                causa = CausaRaiz(
                    categoria=CategoriaIshikawa.MATERIAL,
                    causa="Mudança de Material",
                    descricao=f"Mudança de material/grade: {descricao}",
                    severidade=SeveridadeCausa.MEDIA,
                    confianca=0.65,
                    evidencias=[f"Evento de material: {descricao}"],
                    recomendacoes=[
                        "Verificar especificações do material",
                        "Checar ajustes de processo para novo material"
                    ]
                )
                causas.append(causa)

        return causas

    def _classificar_alarme(self, tipo_alarme: str, tag_id: str, mensagem: str) -> CategoriaIshikawa:
        """Classifica alarme em categoria Ishikawa"""
        texto_combinado = f"{tipo_alarme} {tag_id} {mensagem}".lower()

        for categoria, padroes in self.PADROES_CAUSA.items():
            for palavra in padroes["palavras_alarme"]:
                if palavra in texto_combinado:
                    return categoria

        # Padrão para máquina na maioria dos alarmes
        return CategoriaIshikawa.MAQUINA

    def _classificar_tag(self, tag_id: str, nome_tag: str) -> CategoriaIshikawa:
        """Classifica tag em categoria Ishikawa"""
        texto_combinado = f"{tag_id} {nome_tag}".lower()

        for categoria, padroes in self.PADROES_CAUSA.items():
            for palavra in padroes["palavras_tag"]:
                if palavra in texto_combinado:
                    return categoria

        # Padrão para método em tags de processo
        return CategoriaIshikawa.METODO

    def _determinar_severidade(self, alarme: Dict) -> SeveridadeCausa:
        """Determina severidade baseada nas propriedades do alarme"""
        prioridade = alarme.get("priority", "").upper()
        contagem = alarme.get("count", 1)

        if prioridade == "CRITICAL" or contagem > 10:
            return SeveridadeCausa.CRITICA
        elif prioridade == "HIGH" or contagem > 5:
            return SeveridadeCausa.ALTA
        elif prioridade == "MEDIUM" or contagem > 2:
            return SeveridadeCausa.MEDIA
        else:
            return SeveridadeCausa.BAIXA

    def _obter_recomendacoes_alarme(self, categoria: CategoriaIshikawa, tipo_alarme: str) -> List[str]:
        """Obtém recomendações baseadas na categoria e tipo de alarme"""
        recomendacoes = {
            CategoriaIshikawa.MAO_DE_OBRA: [
                "Revisar ações do operador que levaram ao alarme",
                "Verificar se treinamento de reciclagem é necessário",
                "Verificar se procedimentos estão sendo seguidos"
            ],
            CategoriaIshikawa.MAQUINA: [
                "Verificar histórico de manutenção do equipamento",
                "Verificar condição mecânica",
                "Revisar disponibilidade de peças de reposição"
            ],
            CategoriaIshikawa.METODO: [
                "Revisar procedimentos operacionais",
                "Verificar lógica de sequência",
                "Verificar parâmetros da receita"
            ],
            CategoriaIshikawa.MATERIAL: [
                "Verificar certificados de qualidade do material",
                "Verificar conformidade do fornecedor",
                "Revisar resultados de inspeção de recebimento"
            ],
            CategoriaIshikawa.MEDICAO: [
                "Calibrar sensores",
                "Verificar integridade do sinal",
                "Verificar configuração do transmissor"
            ],
            CategoriaIshikawa.MEIO_AMBIENTE: [
                "Verificar condições ambientais",
                "Revisar impacto do clima nas operações",
                "Verificar sistemas de climatização"
            ]
        }
        return recomendacoes.get(categoria, ["Investigar causa raiz"])

    def _deduplicar_causas(self, causas: List[CausaRaiz]) -> List[CausaRaiz]:
        """Remove causas duplicadas, mantendo maior confiança"""
        vistos = {}
        for causa in causas:
            chave = f"{causa.categoria.value}_{causa.causa}"
            if chave not in vistos or causa.confianca > vistos[chave].confianca:
                if chave in vistos:
                    # Mesclar evidências
                    causa.evidencias.extend(vistos[chave].evidencias)
                    causa.frequencia += vistos[chave].frequencia
                vistos[chave] = causa

        return list(vistos.values())

    def _identificar_causa_primaria(self, causas: List[CausaRaiz]) -> Optional[CausaRaiz]:
        """Identifica a causa raiz primária mais provável"""
        if not causas:
            return None

        # Pontuar cada causa
        causas_pontuadas = []
        for causa in causas:
            pontuacao = 0

            # Peso da severidade
            pesos_severidade = {
                SeveridadeCausa.CRITICA: 100,
                SeveridadeCausa.ALTA: 75,
                SeveridadeCausa.MEDIA: 50,
                SeveridadeCausa.BAIXA: 25
            }
            pontuacao += pesos_severidade[causa.severidade]

            # Peso da confiança
            pontuacao += causa.confianca * 50

            # Peso da frequência
            pontuacao += min(causa.frequencia * 5, 25)

            causas_pontuadas.append((pontuacao, causa))

        # Retornar causa com maior pontuação
        causas_pontuadas.sort(key=lambda x: x[0], reverse=True)
        return causas_pontuadas[0][1] if causas_pontuadas else None

    def _gerar_recomendacoes(
        self,
        categorias: Dict[str, List[CausaRaiz]],
        causa_primaria: Optional[CausaRaiz]
    ) -> List[str]:
        """Gera recomendações priorizadas"""
        recomendacoes = []

        if causa_primaria:
            nome_cat = self.NOMES_CATEGORIAS.get(causa_primaria.categoria, causa_primaria.categoria.value)
            recomendacoes.append(
                f"🎯 PRIORIDADE: Resolver {causa_primaria.causa} ({nome_cat})"
            )
            recomendacoes.extend(causa_primaria.recomendacoes[:2])

        # Adicionar recomendações de causas críticas
        for nome_cat, causas in categorias.items():
            for causa in causas:
                if causa.severidade == SeveridadeCausa.CRITICA and causa != causa_primaria:
                    recomendacoes.append(
                        f"⚠️ CRÍTICO: {causa.causa} - {causa.recomendacoes[0] if causa.recomendacoes else 'Investigar'}"
                    )

        # Limitar a 5 recomendações
        return recomendacoes[:5]

    def _calcular_qualidade_dados(
        self,
        alarmes: List[Dict],
        dados_tags: List[Dict],
        eventos: Optional[List[Dict]]
    ) -> float:
        """Calcula score de qualidade dos dados de entrada"""
        score = 0.0
        fatores = 0

        # Qualidade dos dados de alarme
        if alarmes:
            score += 0.3 * min(len(alarmes) / 10, 1.0)
            fatores += 1

        # Qualidade dos dados de tag
        if dados_tags:
            boa_qualidade = sum(1 for t in dados_tags if t.get("quality") == "GOOD")
            score += 0.4 * (boa_qualidade / len(dados_tags)) if dados_tags else 0
            fatores += 1

        # Qualidade dos dados de evento
        if eventos:
            score += 0.3 * min(len(eventos) / 5, 1.0)
            fatores += 1

        return score / fatores if fatores > 0 else 0.5

    def para_dict(self, diagrama: DiagramaIshikawa) -> Dict[str, Any]:
        """Converte DiagramaIshikawa para dicionário para serialização JSON"""
        return {
            "declaracao_problema": diagrama.declaracao_problema,
            "gerado_em": diagrama.gerado_em.isoformat(),
            "periodo_analise_horas": diagrama.periodo_analise_horas,
            "categorias": {
                nome_cat: {
                    "nome": self.NOMES_CATEGORIAS.get(CategoriaIshikawa(nome_cat), nome_cat),
                    "icone": self.ICONES_CATEGORIAS.get(CategoriaIshikawa(nome_cat), "❓"),
                    "causas": [
                        {
                            "categoria": causa.categoria.value,
                            "causa": causa.causa,
                            "descricao": causa.descricao,
                            "severidade": causa.severidade.value,
                            "confianca": causa.confianca,
                            "evidencias": causa.evidencias,
                            "recomendacoes": causa.recomendacoes,
                            "tags_relacionadas": causa.tags_relacionadas,
                            "frequencia": causa.frequencia
                        }
                        for causa in causas
                    ]
                }
                for nome_cat, causas in diagrama.categorias.items()
            },
            "causa_primaria": {
                "categoria": diagrama.causa_primaria.categoria.value,
                "categoria_nome": self.NOMES_CATEGORIAS.get(diagrama.causa_primaria.categoria, ""),
                "causa": diagrama.causa_primaria.causa,
                "descricao": diagrama.causa_primaria.descricao,
                "severidade": diagrama.causa_primaria.severidade.value,
                "confianca": diagrama.causa_primaria.confianca
            } if diagrama.causa_primaria else None,
            "total_causas_identificadas": diagrama.total_causas_identificadas,
            "score_qualidade_dados": diagrama.score_qualidade_dados,
            "recomendacoes": diagrama.recomendacoes
        }

    # Manter compatibilidade com código existente
    async def analyze(self, problem_statement: str, alarms: List[Dict], tag_data: List[Dict],
                      events: Optional[List[Dict]] = None, hours: int = 24) -> DiagramaIshikawa:
        """Alias para analisar() - compatibilidade"""
        return await self.analisar(problem_statement, alarms, tag_data, events, hours)

    def to_dict(self, diagram: DiagramaIshikawa) -> Dict[str, Any]:
        """Alias para para_dict() - compatibilidade"""
        return self.para_dict(diagram)


# Instância singleton
_servico_ishikawa: Optional[ServicoAnaliseIshikawa] = None


def get_ishikawa_service() -> ServicoAnaliseIshikawa:
    """Obtém ou cria instância do serviço de análise Ishikawa"""
    global _servico_ishikawa
    if _servico_ishikawa is None:
        _servico_ishikawa = ServicoAnaliseIshikawa()
    return _servico_ishikawa


# ============================================
# Aliases de compatibilidade (nomes em inglês)
# ============================================
IshikawaCategory = CategoriaIshikawa
RootCause = CausaRaiz
IshikawaDiagram = DiagramaIshikawa
IshikawaAnalysisService = ServicoAnaliseIshikawa
