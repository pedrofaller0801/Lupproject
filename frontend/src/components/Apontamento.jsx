/**
 * Card individual de um apontamento de revisão.
 * Exibe severidade com cor, descrição, critério do manual e projeto de referência.
 */

// Mapeamento de severidade para estilos Tailwind
const SEVERIDADE_ESTILO = {
  alta:   { badge: 'bg-red-100 text-red-700 border-red-200',    dot: 'bg-red-500',    label: 'Alta'  },
  média:  { badge: 'bg-yellow-100 text-yellow-700 border-yellow-200', dot: 'bg-yellow-500', label: 'Média' },
  baixa:  { badge: 'bg-blue-100 text-blue-700 border-blue-200', dot: 'bg-blue-500',   label: 'Baixa' },
}

// Ícone por origem do apontamento
const ORIGEM_LABEL = {
  visual:  '👁 Visual',
  textual: '📄 Textual',
}

export default function Apontamento({ apontamento }) {
  const {
    descricao,
    severidade,
    origem,
    pagina_referencia,
    criterio_manual,
    projeto_referencia,
  } = apontamento

  const estilo = SEVERIDADE_ESTILO[severidade] || SEVERIDADE_ESTILO['baixa']

  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-white hover:shadow-sm transition-shadow">
      {/* Cabeçalho: severidade + origem + página */}
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border ${estilo.badge}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${estilo.dot}`} />
          {estilo.label}
        </span>

        {origem && (
          <span className="text-xs text-gray-500">
            {ORIGEM_LABEL[origem] || origem}
          </span>
        )}

        {pagina_referencia && (
          <span className="text-xs text-gray-400 ml-auto">
            Prancha {pagina_referencia}
          </span>
        )}
      </div>

      {/* Descrição principal */}
      <p className="text-sm text-gray-800 mb-3">{descricao}</p>

      {/* Critério do manual */}
      {criterio_manual && criterio_manual !== 'null' && (
        <div className="bg-gray-50 rounded p-2 mb-2 border-l-2 border-gray-300">
          <p className="text-xs text-gray-500 font-medium mb-0.5">Critério do manual</p>
          <p className="text-xs text-gray-700">{criterio_manual}</p>
        </div>
      )}

      {/* Projeto de referência */}
      {projeto_referencia && projeto_referencia !== 'null' && (
        <p className="text-xs text-gray-400">
          📁 Referência: <span className="font-medium text-gray-600">{projeto_referencia}</span>
        </p>
      )}
    </div>
  )
}
