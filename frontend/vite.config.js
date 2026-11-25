import {defineConfig} from 'vite';
export default defineConfig({server:{proxy:{'/api':'http://127.0.0.1:8000','/auth':'http://127.0.0.1:8000','/worksites':'http://127.0.0.1:8000','/memberships':'http://127.0.0.1:8000'}}});
