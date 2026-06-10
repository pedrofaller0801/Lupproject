const TOKEN_KEY = 'lup_token'

export const getToken  = ()      => localStorage.getItem(TOKEN_KEY) || ''
export const setToken  = (token) => localStorage.setItem(TOKEN_KEY, token)
export const clearToken = ()     => localStorage.removeItem(TOKEN_KEY)

export async function apiFetch(url, options = {}) {
  const res = await fetch(url, {
    ...options,
    headers: {
      'X-Access-Token': getToken(),
      ...options.headers,
    },
  })

  if (res.status === 401) {
    clearToken()
    window.location.reload()
  }

  return res
}
