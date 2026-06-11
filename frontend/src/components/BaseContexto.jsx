/**
 * Seção de gerenciamento da base de contexto.
 * Permite listar, adicionar e remover documentos (manual e referências).
 * Suporta upload de arquivo único (PDF/DOCX) e upload de pasta com agrupamento por nome.
 */

import { useState, useEffect, useRef } from 'react'
import { apiFetch } from '../api'

const TIPO_LABEL = {
  manual:     { label: 'Manual',     badge: 'bg-purple-100 text-purple-700' },
  referencia: { label: 'Referência', badge: 'bg-teal-100 text-teal-700'    },
}

const EXTS_ACEITAS = ['pdf', 'docx']

function extValida(nome) {
  const ext = nome.split('.').pop().toLowerCase()
  return EXTS_ACEITAS.includes(ext)
}

export default function BaseContexto({ onUploadChange }) {
  const [documentos,  setDocumentos]  = useState([])
  const [carregando,  setCarregando]  = useState(false)
  const [enviando,    setEnviando]    = useState(false)
  const [progresso,   setProgresso]   = useState({ atual: 0, total: 0 })
  const [erro,        setErro]        = useState('')
  const [tipo,        setTipo]        = useState('manual')
  const [modoPasta,   setModoPasta]   = useState(false)
  const [nomeGrupo,   setNomeGrupo]   = useState('')
  const [gruposAbertos, setGruposAbertos] = useState(new Set())
  const inputArquivoRef = useRef(null)
  const inputPastaRef   = useRef(null)

  useEffect(() => {
    carregarLista()
  }, [])

  async function carregarLista() {
    setCarregando(true)
    try {
      const res = await apiFetch('/base/listar')
      const data = await res.json()
      setDocumentos(data.documentos || [])
    } catch {
      setErro('Erro ao carregar a base. Verifique se o backend está rodando.')
    } finally {
      setCarregando(false)
    }
  }

  async function handleUploadArquivo(e) {
    const arquivo = e.target.files[0]
    if (!arquivo) return

    if (!extValida(arquivo.name)) {
      setErro('Selecione um arquivo PDF ou DOCX.')
      return
    }

    setEnviando(true)
    setErro('')

    const form = new FormData()
    form.append('arquivo', arquivo)
    form.append('tipo', tipo)

    try {
      const res = await apiFetch('/base/upload', { method: 'POST', body: form })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Erro ao enviar.')
      }
      await carregarLista()
    } catch (err) {
      setErro(err.message)
    } finally {
      setEnviando(false)
      if (inputArquivoRef.current) inputArquivoRef.current.value = ''
    }
  }

  function abrirSeletorPasta() {
    if (!nomeGrupo.trim()) return
    inputPastaRef.current?.click()
  }

  async function handleUploadPasta(e) {
    const todos = Array.from(e.target.files)
    const arquivos = todos.filter(f => extValida(f.name))

    if (inputPastaRef.current) inputPastaRef.current.value = ''

    if (arquivos.length === 0) {
      setErro('Nenhum arquivo PDF ou DOCX encontrado na pasta selecionada.')
      return
    }

    const grupoFinal = nomeGrupo.trim()

    setEnviando(true)
    setErro('')
    setProgresso({ atual: 0, total: arquivos.length })
    onUploadChange?.({ enviando: true, atual: 0, total: arquivos.length })

    const erros = []

    for (let i = 0; i < arquivos.length; i++) {
      setProgresso({ atual: i + 1, total: arquivos.length })
      onUploadChange?.({ enviando: true, atual: i + 1, total: arquivos.length })

      const form = new FormData()
      form.append('arquivo', arquivos[i])
      form.append('tipo', tipo)
      form.append('grupo', grupoFinal)

      try {
        const res = await apiFetch('/base/upload', { method: 'POST', body: form })
        if (!res.ok) {
          const data = await res.json()
          erros.push(`${arquivos[i].name}: ${data.detail || 'Erro ao enviar.'}`)
        }
      } catch (err) {
        erros.push(`${arquivos[i].name}: ${err.message}`)
      }
    }

    setEnviando(false)
    setProgresso({ atual: 0, total: 0 })
    onUploadChange?.({ enviando: false, atual: 0, total: 0 })
    setModoPasta(false)
    setNomeGrupo('')

    if (erros.length > 0) {
      setErro(`Erros na indexação:\n${erros.join('\n')}`)
    }

    await carregarLista()
  }

  async function handleRemover(id, nome) {
    if (!confirm(`Remover "${nome}" da base?`)) return
    try {
      await apiFetch(`/base/${id}`, { method: 'DELETE' })
      setDocumentos(prev => prev.filter(d => d.id !== id))
    } catch {
      setErro('Erro ao remover o documento.')
    }
  }

  function toggleGrupo(nome) {
    setGruposAbertos(prev => {
      const next = new Set(prev)
      next.has(nome) ? next.delete(nome) : next.add(nome)
      return next
    })
  }

  async function handleRemoverGrupo(nome) {
    if (!confirm(`Remover todos os arquivos do grupo "${nome}"?`)) return
    try {
      await apiFetch(`/base/grupo/${encodeURIComponent(nome)}`, { method: 'DELETE' })
      await carregarLista()
    } catch {
      setErro('Erro ao remover o grupo.')
    }
  }

  // Separa documentos com e sem grupo
  const grupoMap = {}
  const semGrupo = []
  documentos.forEach(doc => {
    if (doc.grupo) {
      if (!grupoMap[doc.grupo]) grupoMap[doc.grupo] = { tipo: doc.tipo, docs: [] }
      grupoMap[doc.grupo].docs.push(doc)
    } else {
      semGrupo.push(doc)
    }
  })

  const totalManual = documentos.filter(d => d.tipo === 'manual').length
  const totalRef    = documentos.filter(d => d.tipo === 'referencia').length

  const statusEnvio = progresso.total > 0
    ? `Indexando arquivo ${progresso.atual} de ${progresso.total}...`
    : 'Indexando...'

  return (
    <div className="flex flex-col gap-6">
      {/* Resumo da base */}
      <div className="grid grid-cols-2 gap-3">
        <ResumoCard valor={totalManual} label="Manual"     cor="purple" />
        <ResumoCard valor={totalRef}   label="Referências" cor="teal"   />
      </div>

      {/* Adicionar documento */}
      <div className="bg-gray-50 dark:bg-slate-700/50 rounded-xl p-4 border border-gray-200 dark:border-slate-600">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-slate-200 mb-3">Adicionar documento</h3>

        {/* Seleção de tipo */}
        <div className="flex gap-2 mb-3">
          {['manual', 'referencia'].map(t => (
            <button
              key={t}
              onClick={() => setTipo(t)}
              className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
                tipo === t
                  ? 'bg-blue-600 text-white'
                  : 'bg-white dark:bg-slate-700 border border-gray-200 dark:border-slate-600 text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-600'
              }`}
            >
              {t === 'manual' ? '📖 Manual' : '📁 Referência'}
            </button>
          ))}
        </div>

        <p className="text-xs text-gray-500 dark:text-slate-400 mb-3">
          {tipo === 'manual'
            ? 'PDFs ou DOCXs com critérios e normas do escritório. Aceita arquivos individuais ou pastas agrupadas por tema.'
            : 'PDFs de projetos anteriores já revisados e aprovados.'}
        </p>

        {/* Inputs ocultos */}
        <input
          ref={inputArquivoRef}
          type="file"
          accept=".pdf,.docx"
          onChange={handleUploadArquivo}
          className="hidden"
        />
        <input
          ref={inputPastaRef}
          type="file"
          accept=".pdf,.docx"
          webkitdirectory=""
          multiple
          onChange={handleUploadPasta}
          className="hidden"
        />

        {/* Botões de upload */}
        <div className="flex gap-2">
          <button
            onClick={() => inputArquivoRef.current?.click()}
            disabled={enviando}
            className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
              enviando
                ? 'bg-gray-200 dark:bg-slate-600 text-gray-400 dark:text-slate-500 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            {enviando && progresso.total === 0 ? '⏳ Indexando...' : '+ Arquivo'}
          </button>

          <button
            onClick={() => { setModoPasta(v => !v); setNomeGrupo('') }}
            disabled={enviando}
            className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
              enviando
                ? 'bg-gray-200 dark:bg-slate-600 text-gray-400 dark:text-slate-500 cursor-not-allowed'
                : modoPasta
                  ? 'bg-indigo-100 text-indigo-700 border border-indigo-300'
                  : 'bg-indigo-600 hover:bg-indigo-700 text-white'
            }`}
          >
            {enviando && progresso.total > 0 ? '⏳ Aguarde...' : '📂 Pasta'}
          </button>
        </div>

        {/* Formulário de nome do grupo */}
        {modoPasta && !enviando && (
          <div className="mt-3 bg-indigo-50 rounded-lg p-3 border border-indigo-200">
            <p className="text-xs font-medium text-indigo-700 mb-2">
              Nome do grupo <span className="text-indigo-400 font-normal">(ex: Churrasqueiras, Piscinas...)</span>
            </p>
            <div className="flex gap-2">
              <input
                type="text"
                value={nomeGrupo}
                onChange={e => setNomeGrupo(e.target.value)}
                placeholder="Nome do grupo"
                autoFocus
                onKeyDown={e => e.key === 'Enter' && abrirSeletorPasta()}
                className="flex-1 text-sm px-3 py-1.5 rounded-lg border border-indigo-200 bg-white focus:outline-none focus:border-indigo-400"
              />
              <button
                onClick={abrirSeletorPasta}
                disabled={!nomeGrupo.trim()}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  nomeGrupo.trim()
                    ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }`}
              >
                Selecionar →
              </button>
              <button
                onClick={() => { setModoPasta(false); setNomeGrupo('') }}
                className="px-3 py-1.5 rounded-lg text-sm text-gray-500 hover:bg-gray-200 transition-colors"
              >
                Cancelar
              </button>
            </div>
          </div>
        )}

        {/* Progresso de upload de pasta */}
        {enviando && progresso.total > 0 && (
          <div className="mt-3">
            <div className="flex justify-between text-xs text-gray-500 dark:text-slate-400 mb-1">
              <span>{statusEnvio}</span>
              <span>{Math.round((progresso.atual / progresso.total) * 100)}%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-slate-600 rounded-full h-1.5">
              <div
                className="bg-indigo-500 h-1.5 rounded-full transition-all duration-300"
                style={{ width: `${(progresso.atual / progresso.total) * 100}%` }}
              />
            </div>
          </div>
        )}

        {enviando && progresso.total === 0 && (
          <p className="text-xs text-gray-400 dark:text-slate-500 mt-2 text-center">
            Aguarde — a indexação pode levar alguns minutos.
          </p>
        )}
      </div>

      {/* Mensagem de erro */}
      {erro && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-sm text-red-700 whitespace-pre-wrap">{erro}</p>
        </div>
      )}

      {/* Lista de documentos */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 dark:text-slate-200 mb-3">
          Documentos indexados ({documentos.length})
        </h3>

        {carregando ? (
          <p className="text-sm text-gray-400 text-center py-4">Carregando...</p>
        ) : documentos.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-4">
            Nenhum documento na base ainda.
          </p>
        ) : (
          <div className="flex flex-col gap-3">
            {/* Grupos */}
            {Object.entries(grupoMap).map(([nome, { tipo: tipoGrupo, docs }]) => {
              const aberto = gruposAbertos.has(nome)
              return (
                <div key={nome} className="border border-indigo-200 rounded-xl overflow-hidden">
                  {/* Cabeçalho do grupo */}
                  <div className="flex items-center justify-between bg-indigo-50 dark:bg-indigo-900/30 px-4 py-2.5">
                    {/* Chevron + info */}
                    <button
                      onClick={() => toggleGrupo(nome)}
                      className="flex items-center gap-2 flex-1 text-left"
                    >
                      <span
                        className="text-indigo-400 text-xs transition-transform duration-200"
                        style={{ display: 'inline-block', transform: aberto ? 'rotate(0deg)' : 'rotate(-90deg)' }}
                      >
                        ▼
                      </span>
                      <div>
                        <p className="text-sm font-semibold text-indigo-800 dark:text-indigo-300">📁 {nome}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${TIPO_LABEL[tipoGrupo]?.badge}`}>
                            {TIPO_LABEL[tipoGrupo]?.label}
                          </span>
                          <span className="text-xs text-gray-400 dark:text-slate-500">
                            {docs.length} arquivo{docs.length !== 1 ? 's' : ''}
                          </span>
                        </div>
                      </div>
                    </button>

                    <button
                      onClick={() => handleRemoverGrupo(nome)}
                      className="text-xs text-red-400 hover:text-red-600 transition-colors px-2 py-1 rounded hover:bg-red-50"
                      title="Remover grupo inteiro"
                    >
                      ✕ grupo
                    </button>
                  </div>

                  {/* Arquivos do grupo — visíveis apenas quando aberto */}
                  {aberto && (
                    <ul className="divide-y divide-gray-100">
                      {docs.map(doc => (
                        <li
                          key={doc.id}
                          className="flex items-center justify-between bg-white dark:bg-slate-800 px-4 py-2.5"
                        >
                          <div>
                            <p className="text-sm text-gray-700 dark:text-slate-200 truncate max-w-[180px]">
                              {doc.nome_arquivo}
                            </p>
                            <span className="text-xs text-gray-400 dark:text-slate-500">{doc.total_chunks} chunks</span>
                          </div>
                          <button
                            onClick={() => handleRemover(doc.id, doc.nome_arquivo)}
                            className="text-gray-300 hover:text-red-500 transition-colors p-1 rounded"
                            title="Remover arquivo"
                          >
                            ✕
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )
            })}

            {/* Documentos sem grupo */}
            {semGrupo.length > 0 && (
              <ul className="flex flex-col gap-2">
                {semGrupo.map(doc => (
                  <li
                    key={doc.id}
                    className="flex items-center justify-between bg-white dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded-lg px-4 py-3"
                  >
                    <div>
                      <p className="text-sm font-medium text-gray-800 dark:text-slate-100 truncate max-w-[200px]">
                        {doc.nome_arquivo}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${TIPO_LABEL[doc.tipo]?.badge}`}>
                          {TIPO_LABEL[doc.tipo]?.label}
                        </span>
                        <span className="text-xs text-gray-400">{doc.total_chunks} chunks</span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleRemover(doc.id, doc.nome_arquivo)}
                      className="text-gray-400 hover:text-red-500 transition-colors p-1 rounded"
                      title="Remover documento"
                    >
                      ✕
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function ResumoCard({ valor, label, cor }) {
  const cores = {
    purple: 'bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800',
    teal:   'bg-teal-50 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 border-teal-200 dark:border-teal-800',
  }
  return (
    <div className={`rounded-xl p-4 border text-center ${cores[cor]}`}>
      <p className="text-2xl font-bold">{valor}</p>
      <p className="text-xs mt-1">{label}</p>
    </div>
  )
}
