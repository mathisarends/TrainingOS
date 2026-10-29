import { defineConfig } from 'lit-canon-api';

export default defineConfig({
  input: './openapi.json',
  output: './src/api/generated',
  request: {
    path: './src/api/request.ts',
    exports: ['ApiError'],
    typeExports: ['ApiRequestOptions'],
  },
  excludeTags: ['system'],
  mutationOperations: ['start_google_login', 'complete_google_login'],
});
