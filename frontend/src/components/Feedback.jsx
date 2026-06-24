/**
 * Botão flutuante de feedback + modal de envio.
 * Envia a mensagem do usuário por e-mail através do endpoint /feedback.
 */

import { useState } from 'react'
import { apiFetch } from '../api'

export default function Feedback() {
  const [aberto,     setAberto]     = useState(false)
  const [mensagem,   setMensagem]   = useState('')
  const [nome,       setNome]       = useState('')
  const [contato,    setContato]    = useState('')
  const [enviando,   setEnviando]   = useState(false)
  const [enviado,    setEnviado]    = useState(false)
  const [erro,       setErro]       = useState('')

  function fechar() {
    setAberto(false)
    setMensagem('')
    setNome('')
    setContato('')
    setEnviado(false)
    setErro('')
  }

  async function handleEnviar() {
    if (!mensagem.trim()) {
      setErro('Escreva sua mensagem antes de enviar.')
      return
    }

    setEnviando(true)
    setErro('')

    const form = new FormData()
    form.append('mensagem', mensagem.trim())
    if (nome.trim())    form.append('nome', nome.trim())
    if (contato.trim()) form.append('contato', contato.trim())

    try {
      const res = await apiFetch('/feedback', { method: 'POST', body: form })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Erro ao enviar feedback.')
      }
      setEnviado(true)
    } catch (err) {
      setErro(err.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <>
      {/* Botão flutuante */}
      <button
        onClick={() => setAberto(true)}
        className="fixed bottom-6 right-6 z-40 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full shadow-lg w-14 h-14 flex items-center justify-center text-2xl transition-transform hover:scale-105 no-print"
        title="Enviar feedback"
      >
        💬
      </button>

      {/* Modal */}
      {aberto && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 no-print px-4">
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl w-full max-w-md p-6">
            {enviado ? (
              <div className="text-center py-4">
                <div className="text-4xl mb-3">✅</div>
                <p className="text-base font-semibold text-gray-800 dark:text-slate-100 mb-1">
                  Feedback enviado!
                </p>
                <p className="text-sm text-gray-500 dark:text-slate-400 mb-5">
                  Obrigado por contribuir com a melhoria do sistema.
                </p>
                <button
                  onClick={fechar}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium py-2 px-5 rounded-lg transition-colors"
                >
                  Fechar
                </button>
              </div>
            ) : (
              <>
                <h3 className="text-base font-semibold text-gray-800 dark:text-slate-100 mb-1">
                  Enviar feedback
                </h3>
                <p className="text-xs text-gray-500 dark:text-slate-400 mb-4">
                  Sua mensagem será enviada diretamente por e-mail para o responsável pelo sistema.
                </p>

                <input
                  type="text"
                  placeholder="Seu nome (opcional)"
                  value={nome}
                  onChange={e => setNome(e.target.value)}
                  className="w-full mb-3 px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                />

                <input
                  type="email"
                  placeholder="Seu e-mail (opcional, para retorno)"
                  value={contato}
                  onChange={e => setContato(e.target.value)}
                  className="w-full mb-3 px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                />

                <textarea
                  placeholder="Conte o que você gostaria de melhorar, relatar ou sugerir..."
                  value={mensagem}
                  onChange={e => setMensagem(e.target.value)}
                  rows={5}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none"
                />

                {erro && (
                  <p className="text-xs text-red-600 dark:text-red-400 mt-2">{erro}</p>
                )}

                <div className="flex gap-2 mt-4">
                  <button
                    onClick={handleEnviar}
                    disabled={enviando}
                    className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                      enviando
                        ? 'bg-gray-200 text-gray-400 cursor-not-allowed dark:bg-slate-700'
                        : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                    }`}
                  >
                    {enviando ? 'Enviando...' : 'Enviar'}
                  </button>
                  <button
                    onClick={fechar}
                    className="py-2 px-4 rounded-lg text-sm font-medium bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-200 hover:bg-gray-200 dark:hover:bg-slate-600 transition-colors"
                  >
                    Cancelar
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </>
  )
}