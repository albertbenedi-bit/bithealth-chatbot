
interface ImportMetaEnv {
  readonly VITE_BACKEND_ORCHESTRATOR_URL: string
  readonly VITE_AUTH_SERVICE_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
