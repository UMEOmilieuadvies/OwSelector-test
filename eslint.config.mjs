export default [
  {
    files: ['js/**/*.js', 'tests/**/*.mjs', 'tools/**/*.mjs'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        window: 'readonly', document: 'readonly', globalThis: 'readonly',
        fetch: 'readonly', crypto: 'readonly', localStorage: 'readonly',
        sessionStorage: 'readonly', navigator: 'readonly', location: 'readonly',
        Blob: 'readonly', URLSearchParams: 'readonly', setTimeout: 'readonly',
        clearTimeout: 'readonly', console: 'readonly', process: 'readonly'
      }
    },
    rules: {
      'no-debugger': 'error',
      'no-duplicate-case': 'error',
      'no-dupe-keys': 'error',
      'no-unreachable': 'error',
      'no-constant-condition': ['error', {checkLoops:false}]
    }
  }
];
