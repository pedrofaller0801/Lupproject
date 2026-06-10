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
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 w-full max-w-sm">
        <h1 className="text-xl font-bold text-gray-900 mb-1">Revisor de Projetos</h1>
        <p className="text-sm text-gray-500 mb-6">Digite a senha para acessar.</p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <input
            type="password"
            value={senha}
            onChange={e => setSenha(e.target.value)}
            placeholder="Senha"
            autoFocus
            className="px-4 py-2.5 rounded-lg border border-gray-200 text-sm focus:outline-none focus:border-blue-400"
          />

          {erro && <p className="text-sm text-red-600">{erro}</p>}

          <button
            type="submit"
            disabled={carregando || !senha}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-200 disabled:text-gray-400 text-white font-medium py-2.5 rounded-lg text-sm transition-colors"
          >
            {carregando ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  )
}
