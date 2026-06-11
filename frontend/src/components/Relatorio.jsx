/**
 * Componente de exibição do relatório de revisão.
 * Organiza os apontamentos por categoria e exibe o resumo geral.
 */

import { useRef } from 'react'
import Apontamento from './Apontamento'

// Categorias e seus ícones
const CATEGORIAS = [
  { key: 'Técnico',     icone: '⚙️', cor: 'border-orange-400' },
  { key: 'Normativo',   icone: '📋', cor: 'border-purple-400' },
  { key: 'Estético',    icone: '🎨', cor: 'border-pink-400'   },
  { key: 'Funcional',   icone: '🏗️', cor: 'border-teal-400'   },
]

export default function Relatorio({ relatorio, onAprovar, onDescartar }) {
  const { projeto, data_analise, resumo, total_apontamentos, apontamentos = [] } = relatorio
  const conteudoRef = useRef(null)

  async function exportarPDF() {
    const html2pdf = (await import('html2pdf.js')).default
    const el = conteudoRef.current
    html2pdf()
      .set({
        margin:      10,
        filename:    `revisao_${projeto.replace(/\s+/g, '_')}.pdf`,
        image:       { type: 'jpeg', quality: 0.95 },
        html2canvas: { scale: 2, useCORS: true, height: el.scrollHeight, windowHeight: el.scrollHeight },
        jsPDF:       { unit: 'mm', format: 'a4', orientation: 'portrait' },
        pagebreak:   { mode: 'avoid-all' },
      })
      .from(el)
      .save()
  }

  // Agrupa apontamentos por categoria
  const porCategoria = CATEGORIAS.reduce((acc, cat) => {
    acc[cat.key] = apontamentos.filter(a => a.categoria === cat.key)
    return acc
  }, {})

  // Conta apontamentos por severidade para o resumo visual
  const contagem = apontamentos.reduce((acc, a) => {
    acc[a.severidade] = (acc[a.severidade] || 0) + 1
    return acc
  }, {})

  return (
    <div>
    <div ref={conteudoRef}>
      {/* Cabeçalho do relatório */}
      <div className="bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl p-6 mb-6">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-slate-100">{projeto}</h2>
            <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
              Análise gerada em {new Date(data_analise + 'T12:00:00').toLocaleDateString('pt-BR', {
                day: '2-digit', month: 'long', year: 'numeric'
              })}
            </p>
          </div>

          {/* Contador de apontamentos por severidade */}
          <div className="flex gap-3">
            {contagem['alta']  && <Contador valor={contagem['alta']}  cor="red"    label="Alta"  />}
            {contagem['média'] && <Contador valor={contagem['média']} cor="yellow" label="Média" />}
            {contagem['baixa'] && <Contador valor={contagem['baixa']} cor="blue"   label="Baixa" />}
          </div>
        </div>

        {/* Resumo geral */}
        {resumo && (
          <div className="mt-4 p-4 bg-gray-50 dark:bg-slate-700 rounded-lg border border-gray-200 dark:border-slate-600">
            <p className="text-sm text-gray-700 dark:text-slate-300">{resumo}</p>
          </div>
        )}

        {/* Total */}
        <p className="text-sm text-gray-500 dark:text-slate-400 mt-3">
          {total_apontamentos === 0
            ? 'Nenhum apontamento identificado.'
            : `${total_apontamentos} apontamento${total_apontamentos > 1 ? 's' : ''} identificado${total_apontamentos > 1 ? 's' : ''}.`}
        </p>
      </div>

      {/* Apontamentos por categoria */}
      {CATEGORIAS.map(({ key, icone, cor }) => {
        const lista = porCategoria[key]
        if (lista.length === 0) return null

        return (
          <div key={key} className={`bg-white dark:bg-slate-800 border-l-4 ${cor} border border-gray-200 dark:border-slate-700 rounded-xl p-5 mb-4`}>
            <h3 className="text-base font-semibold text-gray-800 dark:text-slate-100 mb-4">
              {icone} {key}
              <span className="ml-2 text-sm font-normal text-gray-500 dark:text-slate-400">({lista.length})</span>
            </h3>
            <div className="flex flex-col gap-3">
              {lista.map((ap, i) => (
                <Apontamento key={i} apontamento={ap} />
              ))}
            </div>
          </div>
        )
      })}

    </div>

      {/* Botões de ação */}
      <div className="flex gap-3 mt-6">
        {total_apontamentos === 0 && (
          <button
            onClick={onAprovar}
            className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
          >
            ✓ Aprovar e salvar na base
          </button>
        )}

        <button
          onClick={exportarPDF}
          className="bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 text-gray-700 dark:text-slate-200 font-medium py-3 px-6 rounded-lg transition-colors"
        >
          Exportar PDF
        </button>

        <button
          onClick={onDescartar}
          className="bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 text-gray-700 dark:text-slate-200 font-medium py-3 px-6 rounded-lg transition-colors"
        >
          Descartar
        </button>
      </div>
    </div>
  )
}

// Componente auxiliar para contadores de severidade
function Contador({ valor, cor, label }) {
  const cores = {
    red:    'bg-red-100 text-red-700',
    yellow: 'bg-yellow-100 text-yellow-700',
    blue:   'bg-blue-100 text-blue-700',
  }
  return (
    <div className={`flex flex-col items-center px-3 py-1 rounded-lg ${cores[cor]}`}>
      <span className="text-xl font-bold">{valor}</span>
      <span className="text-xs">{label}</span>
    </div>
  )
}
