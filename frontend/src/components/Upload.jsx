/**
 * Área de upload com drag & drop para envio do PDF do projeto.
 */

import { useState, useRef } from 'react'

const TIPOS_PROJETO = [
  { id: 'arquitetonico', label: 'Arquitetônico' },
  { id: 'interiores',    label: 'Interiores'    },
]

export default function Upload({ onAnalisar, carregando }) {
  const [arquivo,      setArquivo]      = useState(null)
  const [arrastando,   setArrastando]   = useState(false)
  const [tipoProjeto,  setTipoProjeto]  = useState('arquitetonico')
  const inputRef                        = useRef(null)

  // Aceita arquivo via seleção ou drag & drop
  function processarArquivo(file) {
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('Selecione um arquivo PDF.')
      return
    }
    setArquivo(file)
  }

  function handleDrop(e) {
    e.preventDefault()
    setArrastando(false)
    processarArquivo(e.dataTransfer.files[0])
  }

  function handleChange(e) {
    processarArquivo(e.target.files[0])
  }

  function handleAnalisar() {
    if (arquivo) onAnalisar(arquivo, tipoProjeto)
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Tipo de projeto */}
      <div>
        <p className="text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-widest mb-2">
          Tipo de projeto
        </p>
        <div className="flex gap-2">
          {TIPOS_PROJETO.map(t => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTipoProjeto(t.id)}
              className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium border transition-all
                ${tipoProjeto === t.id
                  ? 'bg-indigo-600 border-indigo-600 text-white'
                  : 'bg-white dark:bg-slate-700 border-gray-200 dark:border-slate-600 text-gray-600 dark:text-slate-300 hover:border-indigo-300'}`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Zona de drop */}
      <div
        onDragOver={e => { e.preventDefault(); setArrastando(true) }}
        onDragLeave={() => setArrastando(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`
          border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors
          ${arrastando ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-slate-600 hover:border-blue-400 hover:bg-gray-50 dark:hover:bg-slate-700'}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          onChange={handleChange}
          className="hidden"
        />

        <div className="text-4xl mb-3">📄</div>

        {arquivo ? (
          <div>
            <p className="text-sm font-medium text-gray-900 dark:text-slate-100">{arquivo.name}</p>
            <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">
              {(arquivo.size / 1024 / 1024).toFixed(2)} MB · Clique para trocar
            </p>
          </div>
        ) : (
          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-slate-300">
              Arraste o PDF do projeto aqui
            </p>
            <p className="text-xs text-gray-400 dark:text-slate-500 mt-1">ou clique para selecionar</p>
          </div>
        )}
      </div>

      {/* Botão de análise */}
      <button
        onClick={handleAnalisar}
        disabled={!arquivo || carregando}
        className={`
          w-full py-3 px-6 rounded-lg font-medium transition-all
          ${!arquivo || carregando
            ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md'}
        `}
      >
        {carregando ? (
          <span className="flex items-center justify-center gap-2">
            <Spinner />
            Analisando projeto...
          </span>
        ) : (
          'Analisar projeto'
        )}
      </button>

      {carregando && (
        <p className="text-xs text-gray-400 dark:text-slate-500 text-center">
          Aguarde — a análise pode levar até 2 minutos dependendo do tamanho do projeto.
        </p>
      )}
    </div>
  )
}

// Spinner de carregamento
function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
    </svg>
  )
}
