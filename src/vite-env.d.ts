/// <reference types="vite/client" />

declare global {
  interface Window {
    liquidGlass?: (
      element: Element,
      options?: {
        scale?: number;
        chroma?: number;
        border?: number;
        mapBlur?: number;
        blur?: number;
        saturate?: number;
        radius?: number;
        fallbackBlur?: number;
      },
    ) => { supported: boolean; refresh: () => void; destroy: () => void };
  }
}

export {};
