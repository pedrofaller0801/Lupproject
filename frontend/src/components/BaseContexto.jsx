/**
 * Seção de gerenciamento da base de contexto.
 * Permite listar, adicionar e remover documentos (manual e referências).
 */

import { useState, useEffect, useRef } from 'react'

const TIPO_LABEL = {
  manual:     { label: 'Manual',     badge: 'bg-purple-100 text-purple-700' },
  referencia: { label: 'Referência', badge: 'bg-teal-100 text-teal-700'    },
}

export default function BaseContexto() {
  const [documentos, setDocumentos] = useState([])
  const [carregando, setCarregando] = useState(false)
  const [enviando,   setEnviando]   = useState(false)
  const [erro,       setErro]       = useState('')
  const [tipo,       setTipo]       = useState('manual')
  const inputRef = useRef(null)

  // Carrega a lista ao montar o componente
  useEffect(() => {
    carregarLista()
  }, [])

  async function carregarLista() {
    setCarregando(true)
    try {
      const res = await fetch('/base/listar')
      const data = await res.json()
      setDocumentos(data.documentos || [])
    } catch {
      setErro('Erro ao carregar a base. Verifique se o backend está rodando.')
    } finally {
      setCarregando(false)
    }
  }

  async function handleUpload(e) {
    const arquivo = e.target.files[0]
    if (!arquivo) return
    if (!arquivo.name.toLowerCase().endsWith('.pdf')) {
      setErro('Selecione um arquivo PDF.')
      return
    }

    setEnviando(true)
    setErro('')

    const form = new FormData()
    form.append('arquivo', arquivo)
    form.append('tipo', tipo)

    try {
      const res = await fetch('/base/upload', { method: 'POST', body: form })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Erro ao enviar.')
      }
      await carregarLista()
    } catch (err) {
      setErro(err.message)
    } finally {
      setEnviando(false)
      // Limpa o input para permitir re-upload do mesmo arquivo
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  async function handleRemover(id, nome) {
    if (!confirm(`Remover "${nome}" da base?`)) return
    try {
      await fetch(`/base/${id}`, { method: 'DELETE' })
      setDocumentos(prev => prev.filter(d => d.id !== id))
    } catch {
      setErro('Erro ao remover o documento.')
    }
  }

  const totalManual = documentos.filter(d => d.tipo === 'manual').length
  const totalRef    = documentos.filter(d => d.tipo === 'referencia').length

  return (
    <div className="flex flex-col gap-6">
      {/* Resumo da base */}
      <div className="grid grid-cols-2 gap-3">
        <ResumoCard valor={totalManual} label="Manual"     cor="purple" />
        <ResumoCard valor={totalRef}   label="Referências" cor="teal"   />
      </div>

      {/* Adicionar documento */}
      <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Adicionar documento</h3>

        {/* Seleção de tipo */}
        <div className="flex gap-2 mb-3">
          {['manual', 'referencia'].map(t => (
            <button
              key={t}
              onClick={() => setTipo(t)}
              className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
                tipo === t
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {t === 'manual' ? '📖 Manual' : '📁 Referência'}
            </button>
          ))}
        </div>

        <p className="text-xs text-gray-500 mb-3">
          {tipo === 'manual'
            ? 'PDFs com critérios e normas do escritório (texto extraível).'
            : 'PDFs de projetos anteriores já revisados e aprovados.'}
        </p>

        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          onChange={handleUpload}
          className="hidden"
        />

        <button
          onClick={() => inputRef.current?.click()}
          disabled={enviando}
          className={`w-full py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
            enviando
              ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          {enviando ? '⏳ Indexando...' : '+ Adicionar PDF'}
        </button>

        {enviando && (
          <p className="text-xs text-gray-400 mt-2 text-center">
            Aguarde — a indexação pode levar alguns minutos.
          </p>
        )}
      </div>

      {/* Mensagem de erro */}
      {erro && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-sm text-red-700">{erro}</p>
        </div>
      )}

      {/* Lista de documentos */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Documentos indexados ({documentos.length})
        </h3>

        {carregando ? (
          <p className="text-sm text-gray-400 text-center py-4">Carregando...</p>
        ) : documentos.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-4">
            Nenhum documento na base ainda.
          </p>
        ) : (
          <ul className="flex flex-col gap-2">
            {documentos.map(doc => (
              <li
                key={doc.id}
                className="flex items-center justify-between bg-white border border-gray-200 rounded-lg px-4 py-3"
              >
                <div>
                  <p className="text-sm font-medium text-gray-800 truncate max-w-[200px]">
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
    </div>
  )
}

// Cartão de resumo (total de documentos por tipo)
function ResumoCard({ valor, label, cor }) {
  const cores = {
    purple: 'bg-purple-50 text-purple-700 border-purple-200',
    teal:   'bg-teal-50 text-teal-700 border-teal-200',
  }
  return (
    <div className={`rounded-xl p-4 border text-center ${cores[cor]}`}>
      <p className="text-2xl font-bold">{valor}</p>
      <p className="text-xs mt-1">{label}</p>
    </div>
  )
}
