/**
 * useFileDownload — pobieranie pliku przez <a download> zamiast window.open
 * Parsuje Content-Disposition header żeby pobrać sugerowaną nazwę pliku.
 * RAO-P2-018: fix dla PDF otwierającego się w viewerze zamiast pobrania.
 */
export function useFileDownload() {
  /**
   * Parsuje filename z Content-Disposition headera.
   * Obsługuje: filename="foo.pdf" i filename*=UTF-8''foo.pdf (RFC 5987)
   */
  function parseFilename(contentDisposition, fallback = 'plik.pdf') {
    if (!contentDisposition) return fallback
    // RFC 5987: filename*=UTF-8''...
    const rfc5987 = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i)
    if (rfc5987) {
      try { return decodeURIComponent(rfc5987[1]) } catch { /* fallback */ }
    }
    // Klasyczny: filename="..."
    const classic = contentDisposition.match(/filename="?([^";\n]+)"?/i)
    if (classic) return classic[1].trim()
    return fallback
  }

  /**
   * Pobiera blob response jako plik przez <a download>.
   * @param {Blob} blob - dane pliku
   * @param {string} contentDisposition - nagłówek Content-Disposition z response
   * @param {string} fallbackFilename - nazwa jeśli header nie zawiera nazwy
   */
  function downloadBlob(blob, contentDisposition, fallbackFilename = 'plik.pdf') {
    const filename = parseFilename(contentDisposition, fallbackFilename)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    setTimeout(() => URL.revokeObjectURL(url), 10000)
  }

  return { downloadBlob, parseFilename }
}
