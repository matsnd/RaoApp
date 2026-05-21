/**
 * useTargetFolder — File System Access API + IndexedDB persistence
 * RAO-P3-013: konfigurowalny folder pobierania PDF
 * Fallback automatyczny gdy API niedostępne lub brak permission.
 */
import { openDB } from 'idb'

const DB_NAME = 'rao-fs'
const DB_VERSION = 1
const STORE = 'handles'
const KEY = 'rao-root-folder'

async function getDB() {
  return openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE)
      }
    },
  })
}

export function useTargetFolder() {
  /** Sprawdza czy File System Access API jest dostępne */
  function isSupported() {
    return typeof window !== 'undefined' && 'showDirectoryPicker' in window
  }

  /** Pobiera zapisany handle z IndexedDB */
  async function getStoredHandle() {
    if (!isSupported()) return null
    try {
      const db = await getDB()
      return await db.get(STORE, KEY)
    } catch {
      return null
    }
  }

  /** Zapisuje handle do IndexedDB */
  async function setStoredHandle(handle) {
    try {
      const db = await getDB()
      await db.put(STORE, handle, KEY)
    } catch { /* silent fail */ }
  }

  /** Usuwa handle z IndexedDB */
  async function clearStoredHandle() {
    try {
      const db = await getDB()
      await db.delete(STORE, KEY)
    } catch { /* silent fail */ }
  }

  /**
   * Sprawdza uprawnienia do zapisu.
   * Zwraca true jeśli można zapisywać, false jeśli trzeba prosić o permission.
   */
  async function verifyPermission(handle) {
    if (!handle) return false
    try {
      const opts = { mode: 'readwrite' }
      if (await handle.queryPermission(opts) === 'granted') return true
      if (await handle.requestPermission(opts) === 'granted') return true
      return false
    } catch {
      return false
    }
  }

  /**
   * Otwiera dialog wyboru folderu i zapisuje handle.
   * Zwraca { success: bool, folderName: string|null }
   */
  async function pickFolder() {
    if (!isSupported()) return { success: false, folderName: null }
    try {
      const handle = await window.showDirectoryPicker({ mode: 'readwrite' })
      await setStoredHandle(handle)
      return { success: true, folderName: handle.name }
    } catch (e) {
      // AbortError = user cancelled
      if (e.name === 'AbortError') return { success: false, folderName: null }
      return { success: false, folderName: null }
    }
  }

  /**
   * Zwraca nazwę aktualnie zapisanego folderu.
   * null jeśli brak.
   */
  async function getStoredFolderName() {
    const handle = await getStoredHandle()
    return handle ? handle.name : null
  }

  /**
   * Zapisuje blob do podfolderu.
   * @param {Blob} blob
   * @param {string} filename - np. "S_129_2026.pdf"
   * @param {'umowy'|'protokoly'|'zestawienia'} subfolder
   * @returns {Promise<boolean>} true jeśli zapisano, false jeśli fallback
   */
  async function saveToSubfolder(blob, filename, subfolder) {
    if (!isSupported()) return false
    let handle = await getStoredHandle()
    if (!handle) return false
    const hasPermission = await verifyPermission(handle)
    if (!hasPermission) {
      // Handle jest zapisany ale uprawnienia wygasły (np. po zamknięciu przeglądarki)
      // Spróbuj automatycznie ponownie przydzielić uprawnienia
      try {
        const opts = { mode: 'readwrite' }
        if (await handle.requestPermission(opts) === 'granted') {
          // Uprawnienia przydzielone ponownie
        } else {
          // Użytkownik anulował lub uprawnienia nie zostały przydzielone
          return false
        }
      } catch {
        // Handle jest nieważny (SecurityError), usuń z IndexedDB
        await clearStoredHandle()
        return false
      }
    }
    try {
      // Utwórz/pobierz podfolder
      const subHandle = await handle.getDirectoryHandle(subfolder, { create: true })
      // Utwórz plik
      const fileHandle = await subHandle.getFileHandle(filename, { create: true })
      const writable = await fileHandle.createWritable()
      await writable.write(blob)
      await writable.close()
      return true
    } catch {
      return false
    }
  }

  return {
    isSupported,
    pickFolder,
    clearStoredHandle,
    getStoredFolderName,
    saveToSubfolder,
    verifyPermission,
    getStoredHandle,
  }
}
