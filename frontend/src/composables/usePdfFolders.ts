/**
 * usePdfFolders — File System Access API + IndexedDB persistence
 * dla 4 dedykowanych folderów PDF (auto-zapis per oddział/typ dokumentu).
 *
 * Foldery:
 *  - report_main     → umowy (główny / Warszawa, branch_id == 1)
 *  - protocol_main   → protokoły (główny / Warszawa, branch_id == 1)
 *  - report_gdansk   → umowy (Gdańsk, branch_id != 1)
 *  - protocol_gdansk → protokoły (Gdańsk, branch_id != 1)
 *
 * Fallback: gdy File System Access API niedostępne (Firefox/Safari)
 * → savePdf zwraca false, frontend używa zwykłego download (<a download>).
 *
 * Persistencja directoryHandle między sesjami przez IndexedDB (klucze:
 * 'pdf-folder-<key>'). Handle jest strukturą serializowalną przez
 * structured clone (IndexedDB go wspiera).
 */
import { ref, computed } from 'vue'
import { openDB, type IDBPDatabase } from 'idb'

/** Klucze folderów — stabilne identyfikatory persisted w IndexedDB. */
export type PdfFolderKey =
  | 'report_main'
  | 'protocol_main'
  | 'report_gdansk'
  | 'protocol_gdansk'

/** Typ dokumentu — mapowany na parę folderów (główny / Gdańsk). */
export type PdfDocType = 'contract' | 'protocol'

const DB_NAME = 'rao-fs'
const DB_VERSION = 1
const STORE = 'handles'
const KEY_PREFIX = 'pdf-folder-'

/** Minimalny typ FileSystemDirectoryHandle (Chrome/Edge only — brak w lib.dom dla TS). */
interface FsDirHandle {
  name: string
  queryPermission(opts: { mode: 'read' | 'readwrite' }): Promise<PermissionState>
  requestPermission(opts: { mode: 'read' | 'readwrite' }): Promise<PermissionState>
  getFileHandle(name: string, opts?: { create?: boolean }): Promise<FsFileHandle>
}
interface FsFileHandle {
  name: string
  createWritable(): Promise<FsWritableStream>
}
interface FsWritableStream {
  write(data: ArrayBuffer | Blob): Promise<void>
  close(): Promise<void>
}

let dbPromise: Promise<IDBPDatabase> | null = null
function getDB(): Promise<IDBPDatabase> {
  if (!dbPromise) {
    dbPromise = openDB(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains(STORE)) {
          db.createObjectStore(STORE)
        }
      },
    })
  }
  return dbPromise
}

/** IndexedDB helpers — get/set/delete directoryHandle per klucz. */
async function getHandle(key: PdfFolderKey): Promise<FsDirHandle | null> {
  try {
    const db = await getDB()
    return (await db.get(STORE, KEY_PREFIX + key)) as FsDirHandle | null
  } catch {
    return null
  }
}

async function setHandle(key: PdfFolderKey, handle: FsDirHandle): Promise<void> {
  try {
    const db = await getDB()
    await db.put(STORE, handle, KEY_PREFIX + key)
  } catch {
    /* silent fail — fallback do zwykłego download */
  }
}

async function deleteHandle(key: PdfFolderKey): Promise<void> {
  try {
    const db = await getDB()
    await db.delete(STORE, KEY_PREFIX + key)
  } catch {
    /* silent fail */
  }
}

function isSupported(): boolean {
  return typeof window !== 'undefined' && 'showDirectoryPicker' in window
}

/**
 * Sprawdza / prosi o uprawnienie readwrite dla handle.
 * Zwraca true gdy można zapisywać.
 */
async function ensurePermission(handle: FsDirHandle): Promise<boolean> {
  const opts = { mode: 'readwrite' as const }
  try {
    if ((await handle.queryPermission(opts)) === 'granted') return true
    if ((await handle.requestPermission(opts)) === 'granted') return true
    return false
  } catch {
    return false
  }
}

/** Zapisuje bytes do pliku `filename` w folderze handle. */
async function writeFile(handle: FsDirHandle, filename: string, bytes: ArrayBuffer): Promise<boolean> {
  try {
    const fileHandle = await handle.getFileHandle(filename, { create: true })
    const writable = await fileHandle.createWritable()
    await writable.write(bytes)
    await writable.close()
    return true
  } catch {
    return false
  }
}

export function usePdfFolders() {
  const folders = ref<Record<PdfFolderKey, FsDirHandle | null>>({
    report_main: null,
    protocol_main: null,
    report_gdansk: null,
    protocol_gdansk: null,
  })

  const hasFileSystemAccess = computed(() => isSupported())

  /** Ładuje wszystkie handle z IndexedDB do ref (np. w onMounted). */
  async function loadFolders(): Promise<void> {
    if (!isSupported()) return
    const keys: PdfFolderKey[] = ['report_main', 'protocol_main', 'report_gdansk', 'protocol_gdansk']
    const entries = await Promise.all(
      keys.map(async (k) => [k, await getHandle(k)] as const),
    )
    for (const [k, h] of entries) {
      folders.value[k] = h
    }
  }

  /**
   * Otwiera dialog wyboru folderu i zapisuje handle w IndexedDB.
   * Zwraca nazwę wybranego folderu lub null (anulowano / błąd / brak wsparcia).
   */
  async function pickFolder(key: PdfFolderKey): Promise<string | null> {
    if (!isSupported()) return null
    try {
      const handle = (await window.showDirectoryPicker({ mode: 'readwrite' })) as unknown as FsDirHandle
      await setHandle(key, handle)
      folders.value[key] = handle
      return handle.name
    } catch (e) {
      // AbortError = user cancelled — nie traktuj jako błąd
      if (e && typeof e === 'object' && 'name' in e && (e as { name: string }).name === 'AbortError') {
        return null
      }
      return null
    }
  }

  /** Usuwa handle z IndexedDB i czyści ref. */
  async function clearFolder(key: PdfFolderKey): Promise<void> {
    await deleteHandle(key)
    folders.value[key] = null
  }

  /**
   * Zapisuje PDF (bytes) do wszystkich skonfigurowanych folderów dla danej
   * kombinacji (branchId, type). Zwraca liczbę folderów do których udało się
   * zapisać (0 → frontend używa zwykłego download).
   *
   * Logika mapowania:
   *  - type === 'contract'  → report_main (zawsze) + report_gdansk (gdy branchId != 1)
   *  - type === 'protocol'  → protocol_main (zawsze) + protocol_gdansk (gdy branchId != 1)
   *
   * Uwaga: folder główny jest zapisywany zawsze (dla umów z Gdańska też
   * trafia do głównego archiwum), folder Gdańsk dodatkowo gdy branchId != 1.
   * Brak skonfigurowanego handle dla folderu = pomijany (nie błąd).
   */
  async function savePdf(
    bytes: ArrayBuffer,
    filename: string,
    branchId: number | null,
    type: PdfDocType,
  ): Promise<number> {
    if (!isSupported()) return 0

    const targets: PdfFolderKey[] = []
    if (type === 'contract') {
      targets.push('report_main')
      if (branchId != null && branchId !== 1) targets.push('report_gdansk')
    } else {
      targets.push('protocol_main')
      if (branchId != null && branchId !== 1) targets.push('protocol_gdansk')
    }

    let savedCount = 0
    for (const key of targets) {
      const handle = folders.value[key] ?? (await getHandle(key))
      if (!handle) continue
      // odśwież ref jeśli był niezaładowany
      if (!folders.value[key]) folders.value[key] = handle
      const ok = await ensurePermission(handle)
      if (!ok) continue
      const written = await writeFile(handle, filename, bytes)
      if (written) savedCount += 1
    }
    return savedCount
  }

  return {
    folders,
    hasFileSystemAccess,
    loadFolders,
    pickFolder,
    clearFolder,
    savePdf,
  }
}
