/**
 * useFileDownload — pobieranie pliku przez <a download> zamiast window.open
 * Parsuje Content-Disposition header żeby pobrać sugerowaną nazwę pliku.
 * RAO-P2-018: fix dla PDF otwierającego się w viewerze zamiast pobrania.
 * RAO-P3-013: saveToFolder — inteligentny zapis do skonfigurowanych folderów PDF.
 * RAO-TECH-003 (2026-07-11): konsolidacja — usePdfFolders zamiast useTargetFolder.
 */
import { usePdfFolders } from './usePdfFolders'

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

  /**
   * Inteligentny zapis PDF: do folderów per-oddział (jeśli skonfigurowane) lub <a download> (fallback).
   * RAO-TECH-003: konsolidacja z useTargetFolder → usePdfFolders.
   * @param {Blob} blob - dane pliku
   * @param {string} contentDisposition - nagłówek Content-Disposition
   * @param {string} fallbackFilename - nazwa pliku fallback
   * @param {'umowy'|'protokoly'|'zestawienia'} docType - typ dokumentu
   * @param {number|null} branchId - ID oddziału (do mapowania folderów per-oddział)
   * @returns {Promise<boolean>} true jeśli zapisano do co najmniej jednego folderu
   */
  async function saveToFolder(blob, contentDisposition, fallbackFilename = 'plik.pdf', docType = 'zestawienia', branchId = null) {
    const filename = parseFilename(contentDisposition, fallbackFilename)

    // Mapuj docType na PdfDocType (usePdfFolders obsługuje tylko contract/protocol)
    if (docType === 'umowy' || docType === 'protokoly') {
      const pdfType = docType === 'umowy' ? 'contract' : 'protocol'
      const { savePdf, loadFolders } = usePdfFolders()
      await loadFolders()
      const bytes = blob instanceof ArrayBuffer ? blob : await blob.arrayBuffer()
      const savedCount = await savePdf(bytes, filename, branchId, pdfType)
      if (savedCount > 0) return true
    }

    // Fallback: standardowe pobieranie (zestawienia lub brak skonfigurowanego folderu)
    downloadBlob(blob, contentDisposition, fallbackFilename)
    return false
  }

  return { downloadBlob, parseFilename, saveToFolder }
}
