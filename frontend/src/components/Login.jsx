import { useState } from 'react'
import { setToken } from '../api'

export default function Login({ onLogin }) {
  const [senha,      setSenha]      = useState('')
  const [erro,       setErro]       = useState('')
  const [carregando, setCarregando] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setCarregando(true)
    setErro('')

    try {
      const res = await fetch('/auth', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ senha }),
      })

      if (res.ok) {
        const data = await res.json()
        setToken(data.token)
        onLogin()
      } else {
        setErro('Senha incorreta.')
      }
    } catch {
      setErro('Erro ao conectar. Verifique se o servidor está rodando.')
    } finally {
      setCarregando(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 flex">

      {/* Painel esquerdo — branding */}
      <div className="hidden lg:flex flex-col justify-between w-1/2 bg-slate-800 p-12 border-r border-slate-700">
        <div className="flex items-center gap-2">
          <span className="text-indigo-400 text-lg">◈</span>
          <span className="text-white text-base font-semibold tracking-tight">Revisor de Projetos</span>
        </div>

        <div>
          <h2 className="text-white text-3xl font-bold leading-tight mb-4">
            Revisão inteligente de projetos arquitetônicos
          </h2>
          <p className="text-slate-400 text-sm leading-relaxed max-w-xs">
            Análise automatizada com IA baseada no manual do escritório e em projetos de referência aprovados.
          </p>
        </div>

        <p className="text-slate-600 text-xs">Sistema RAG · Gemini 2.5 Flash</p>
      </div>

      {/* Painel direito — formulário */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">

          {/* Logo mobile */}
          <div className="flex items-center gap-2 mb-10 lg:hidden">
            <span className="text-indigo-400 text-lg">◈</span>
            <span className="text-white text-base font-semibold">Revisor de Projetos</span>
          </div>

          <div className="mb-8">
            <h1 className="text-white text-2xl font-bold mb-1">Entrar</h1>
            <p className="text-slate-400 text-sm">Digite a senha do escritório para continuar.</p>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div>
              <label className="text-slate-400 text-xs font-medium uppercase tracking-widest mb-2 block">
                Senha
              </label>
              <input
                type="password"
                value={senha}
                onChange={e => setSenha(e.target.value)}
                placeholder="••••••••"
                autoFocus
                className="w-full bg-slate-800 border border-slate-700 text-white placeholder-slate-600 px-4 py-3 rounded-lg text-sm focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>

            {erro && (
              <p className="text-red-400 text-sm">{erro}</p>
            )}

            <button
              type="submit"
              disabled={carregando || !senha}
              className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 disabled:border disabled:border-slate-700 text-white font-medium py-3 rounded-lg text-sm transition-colors mt-2"
            >
              {carregando ? 'Entrando...' : 'Acessar →'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
