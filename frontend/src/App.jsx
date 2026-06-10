/**
 * Componente raiz da aplicação.
 * Gerencia o estado global e a navegação entre as duas seções:
 *   - Novo Projeto: upload + análise + relatório
 *   - Base de Contexto: gerenciamento dos documentos indexados
 */

import { useState } from 'react'
import Upload       from './components/Upload'
import Relatorio    from './components/Relatorio'
import BaseContexto from './components/BaseContexto'
import Login        from './components/Login'
import { apiFetch, getToken, clearToken } from './api'

// Seções disponíveis na navegação
const SECOES = [
  { id: 'projeto', label: '📄 Novo Projeto',      sub: 'Uso diário'        },
  { id: 'base',    label: '📚 Base de Contexto', sub: 'Setup / opcional'  },
]

export default function App() {
  const [autenticado, setAutenticado] = useState(!!getToken())
  const [secaoAtiva,  setSecaoAtiva]  = useState('projeto')

  if (!autenticado) {
    return <Login onLogin={() => setAutenticado(true)} />
  }

  // Estado da análise: null | 'carregando' | { relatorio, arquivo }
  const [analise,  setAnalise]  = useState(null)
  const [erro,     setErro]     = useState('')
  const [aprovando, setAprovando] = useState(false)

  // Inicia a análise do PDF enviado
  async function handleAnalisar(arquivo) {
    setErro('')
    setAnalise('carregando')

    const form = new FormData()
    form.append('arquivo', arquivo)

    try {
      const res = await apiFetch('/analisar', {
        method: 'POST',
        body: form,
        signal: AbortSignal.timeout(120_000),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Erro desconhecido na análise.')
      }

      const relatorio = await res.json()
      setAnalise({ relatorio, arquivo })

    } catch (err) {
      setErro(err.message || 'Erro ao analisar o projeto. Tente novamente.')
      setAnalise(null)
    }
  }

  // Aprova o relatório e envia o projeto para a base de referências
  async function handleAprovar() {
    if (!analise || analise === 'carregando') return

    setAprovando(true)
    setErro('')

    const form = new FormData()
    form.append('arquivo',   analise.arquivo)
    form.append('tipo',      'referencia')
    form.append('relatorio', JSON.stringify(analise.relatorio))

    try {
      const res = await apiFetch('/base/upload', { method: 'POST', body: form })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Erro ao salvar na base.')
      }
      alert('Projeto aprovado e salvo na base de referências com sucesso!')
      handleDescartar()
    } catch (err) {
      setErro(err.message)
    } finally {
      setAprovando(false)
    }
  }

  // Descarta o relatório atual e volta ao estado inicial
  function handleDescartar() {
    setAnalise(null)
    setErro('')
  }

  const carregando = analise === 'carregando'
  const temRelatorio = analise && analise !== 'carregando'

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Cabeçalho */}
      <header className="bg-white border-b border-gray-200 shadow-sm no-print">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-gray-900">Revisor de Projetos</h1>
            <p className="text-xs text-gray-500">Sistema RAG · Gemini 2.5 Flash</p>
          </div>
          <button
            onClick={() => { clearToken(); setAutenticado(false) }}
            className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
          >
            Sair
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Navegação entre seções */}
        <nav className="flex gap-2 mb-8 no-print">
          {SECOES.map(secao => (
            <button
              key={secao.id}
              onClick={() => { setSecaoAtiva(secao.id); handleDescartar() }}
              className={`
                flex-1 py-3 px-4 rounded-xl text-left transition-all border
                ${secaoAtiva === secao.id
                  ? 'bg-white border-blue-500 shadow-sm'
                  : 'bg-gray-50 border-gray-200 hover:bg-white'}
              `}
            >
              <p className={`text-sm font-semibold ${secaoAtiva === secao.id ? 'text-blue-600' : 'text-gray-700'}`}>
                {secao.label}
              </p>
              <p className="text-xs text-gray-400">{secao.sub}</p>
            </button>
          ))}
        </nav>

        {/* Seção: Novo Projeto */}
        {secaoAtiva === 'projeto' && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-base font-semibold text-gray-800 mb-5">
              Enviar projeto para revisão
            </h2>

            {/* Mensagem de erro */}
            {erro && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-5">
                <p className="text-sm text-red-700">{erro}</p>
              </div>
            )}

            {/* Exibe upload ou relatório, conforme o estado */}
            {!temRelatorio ? (
              <Upload onAnalisar={handleAnalisar} carregando={carregando} />
            ) : (
              <Relatorio
                relatorio={analise.relatorio}
                onAprovar={handleAprovar}
                onDescartar={handleDescartar}
              />
            )}

            {/* Overlay de aprovação */}
            {aprovando && (
              <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
                <div className="bg-white rounded-xl p-6 shadow-xl">
                  <p className="text-sm font-medium text-gray-700">
                    ⏳ Indexando projeto na base...
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Seção: Base de Contexto */}
        {secaoAtiva === 'base' && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-base font-semibold text-gray-800 mb-5">
              Base de contexto
            </h2>
            <BaseContexto />
          </div>
        )}
      </main>
    </div>
  )
}
