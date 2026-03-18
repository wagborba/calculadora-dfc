"""Dimension and parameter definitions for the DFC Framework."""

from dataclasses import dataclass, field


@dataclass
class Parameter:
    """A single evaluation parameter within a dimension.

    Attributes:
        id: Unique identifier for the parameter.
        name: Display name of the parameter.
        description: Brief explanation used as hint during evaluation.
    """

    id: str
    name: str
    description: str


@dataclass
class Dimension:
    """A grouped set of parameters with an associated weight.

    Attributes:
        id: Unique identifier for the dimension.
        name: Display name of the dimension.
        weight: Relative weight in the final CF calculation (0.0–1.0).
        parameters: List of parameters belonging to this dimension.
    """

    id: str
    name: str
    weight: float
    parameters: list[Parameter] = field(default_factory=list)


DIMENSIONS: list[Dimension] = [
    Dimension(
        id="performance",
        name="Desempenho",
        weight=0.20,
        parameters=[
            Parameter(
                id="load_time",
                name="Tempo de carregamento",
                description="LCP, FCP e TTI — percepção de velocidade inicial.",
            ),
            Parameter(
                id="slow_connection",
                name="Performance em conexão lenta",
                description="Comportamento em redes 3G/Edge ou instáveis.",
            ),
            Parameter(
                id="bugs_crashes",
                name="Recorrência de bugs e travamentos",
                description="Frequência de erros, crashes ou comportamentos inesperados.",
            ),
            Parameter(
                id="stability",
                name="Estabilidade em uso contínuo",
                description="Degradação de performance após uso prolongado.",
            ),
        ],
    ),
    Dimension(
        id="flows_navigation",
        name="Fluxos & Navegação",
        weight=0.22,
        parameters=[
            Parameter(
                id="steps_per_task",
                name="Quantidade de passos por tarefa",
                description="Número de cliques ou telas para concluir ações comuns.",
            ),
            Parameter(
                id="wayfinding",
                name="Orientação e wayfinding",
                description="Facilidade de saber onde está e para onde ir.",
            ),
            Parameter(
                id="visual_hierarchy",
                name="Hierarquia visual e ícones",
                description="Clareza da estrutura visual e significado dos ícones.",
            ),
            Parameter(
                id="dead_ends",
                name="Becos sem saída",
                description="Situações onde o usuário não consegue avançar nem voltar.",
            ),
        ],
    ),
    Dimension(
        id="feedback_communication",
        name="Feedback & Comunicação",
        weight=0.18,
        parameters=[
            Parameter(
                id="confirmation_error_msgs",
                name="Mensagens de confirmação e erro",
                description="Clareza e utilidade das mensagens exibidas ao usuário.",
            ),
            Parameter(
                id="microinteractions",
                name="Microinterações e estados visuais",
                description="Animações, transições e indicadores de estado de UI.",
            ),
            Parameter(
                id="error_recovery",
                name="Recuperação de erro",
                description="Facilidade de corrigir erros e retomar o fluxo.",
            ),
            Parameter(
                id="progress_indicators",
                name="Indicadores de progresso",
                description="Feedback visual durante processos assíncronos ou longos.",
            ),
        ],
    ),
    Dimension(
        id="input_effort",
        name="Esforço de Entrada",
        weight=0.18,
        parameters=[
            Parameter(
                id="form_efficiency",
                name="Eficiência de formulários",
                description="Quantidade e organização dos campos de entrada.",
            ),
            Parameter(
                id="autocomplete",
                name="Autopreenchimento e automação",
                description="Uso de autocomplete, sugestões e preenchimento inteligente.",
            ),
            Parameter(
                id="realtime_validation",
                name="Validação em tempo real",
                description="Feedback imediato sobre erros de preenchimento.",
            ),
            Parameter(
                id="input_tolerance",
                name="Tolerância a erros de entrada",
                description="Capacidade de aceitar variações de formato (datas, CPF etc.).",
            ),
        ],
    ),
    Dimension(
        id="trust_transparency",
        name="Confiança & Transparência",
        weight=0.12,
        parameters=[
            Parameter(
                id="onboarding",
                name="Onboarding e curva de aprendizado",
                description="Facilidade de entender e começar a usar o produto.",
            ),
            Parameter(
                id="permissions",
                name="Solicitação de permissões",
                description="Contexto e timing das solicitações de acesso/permissão.",
            ),
            Parameter(
                id="privacy_clarity",
                name="Clareza sobre dados e privacidade",
                description="Transparência sobre coleta, uso e armazenamento de dados.",
            ),
        ],
    ),
    Dimension(
        id="accessibility",
        name="Acessibilidade & Adaptação",
        weight=0.10,
        parameters=[
            Parameter(
                id="contrast_readability",
                name="Contraste e legibilidade",
                description="Contraste de cores, tamanho de fonte e legibilidade geral.",
            ),
            Parameter(
                id="touch_targets",
                name="Áreas de toque e alvos de clique",
                description="Tamanho e espaçamento dos elementos interativos.",
            ),
            Parameter(
                id="responsiveness",
                name="Responsividade e adaptação",
                description="Comportamento em diferentes tamanhos de tela e orientações.",
            ),
            Parameter(
                id="assistive_tech",
                name="Suporte a tecnologias assistivas",
                description="Compatibilidade com leitores de tela e outras ferramentas.",
            ),
        ],
    ),
]
