import { create } from 'zustand'

interface AppState {
  currentRoute: string
  setRoute: (route: string) => void
  fileChanges: string[]
  addFileChange: (file: string) => void
  isWatcherActive: boolean
  toggleWatcher: () => void
  projectStats: {
    files: number
    lines: number
    modules: number
  }
}

export const useAppStore = create<AppState>((set) => ({
  currentRoute: '/',
  setRoute: (route) => set({ currentRoute: route }),
  fileChanges: [],
  addFileChange: (file) => set((state) => ({
    fileChanges: [file, ...state.fileChanges.slice(0, 9)]
  })),
  isWatcherActive: false,
  toggleWatcher: () => set((state) => ({ isWatcherActive: !state.isWatcherActive })),
  projectStats: {
    files: 145,
    lines: 39663,
    modules: 31
  }
}))
