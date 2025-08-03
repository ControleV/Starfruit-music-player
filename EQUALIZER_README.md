# Equalizador Starfruit Music Player

## Como funciona

O equalizador agora está totalmente integrado ao player de música e **realmente afeta o som das músicas**!

### ✅ Problemas Corrigidos:

1. **Tratamento de arquivos com caracteres especiais**: Nomes com acentos, espaços e caracteres especiais
2. **Sistema de fallback robusto**: Se o equalizador falhar, usa o arquivo original
3. **Botão para ativar/desativar**: Permite usar o player sem equalização
4. **Melhor tratamento de erros**: Mensagens informativas sobre problemas
5. **Cache inteligente**: Evita reprocessar arquivos desnecessariamente

### Funcionalidades:

1. **Interface gráfica melhorada**: Janela do equalizador com design consistente
2. **Processamento real de áudio**: Usa filtros digitais para modificar as frequências
3. **Integração com pygame**: Processa as músicas antes de tocar
4. **Sistema de fallback**: Se houver problemas, usa o arquivo original
5. **Ativar/Desativar**: Controle total sobre quando usar o equalizador

### Controles do Equalizador:

1. **Ativar/Desativar EQ**: Botão para ativar ou desativar o equalizador
2. **Sliders de Frequência**:
   - **Graves (250Hz)**: Controla sons mais baixos (bumbo, baixo)
   - **Médios (2kHz)**: Controla vozes e instrumentos principais  
   - **Agudos (8kHz)**: Controla sons mais altos (pratos, agudos)
3. **Aplicar Equalizador**: Aplica as configurações à música atual
4. **Reset**: Restaura valores padrão (1.0 para todas as frequências)

### Resolução de Problemas:

**Se aparecer erro sobre caracteres especiais:**
- O sistema agora trata automaticamente arquivos com nomes problemáticos
- Usa fallback para arquivo original se não conseguir processar

**Se aparecer aviso sobre ffmpeg:**
- Instale o ffmpeg para melhor suporte a formatos: `https://ffmpeg.org/download.html`
- Ou use apenas arquivos WAV que não precisam do ffmpeg

**Se o equalizador não funcionar:**
- Clique em "Desativar EQ" para usar o player normalmente
- Verifique se o arquivo de música não está corrompido

### Configurações dos sliders:
- **0.0**: Remove completamente essa faixa de frequência
- **1.0**: Mantém o volume original (padrão)
- **2.0**: Dobra o volume dessa faixa de frequência

### Exemplos de uso:
- **Mais graves**: Graves = 1.5, Médios = 1.0, Agudos = 0.8
- **Mais agudos**: Graves = 0.8, Médios = 1.0, Agudos = 1.5  
- **Vocal destacado**: Graves = 0.7, Médios = 1.3, Agudos = 0.9

### Funcionalidades técnicas:

- **Filtros Butterworth**: Processamento de áudio profissional
- **Normalização automática**: Evita distorção
- **Cache de arquivos**: Performance otimizada
- **Suporte MP3 e WAV**: Funciona com os formatos suportados
- **Processamento em C++**: Backend em C++ para operações pesadas (opcional)

### Arquivos importantes:

- `tools/equalizer/equalizer.py`: Interface gráfica do equalizador
- `tools/audio_processor.py`: Processamento de áudio com filtros digitais
- `tools/equalizer/equalizer_backend.c`: Backend em C para processamento pesado
- `app.py`: Integração com o player principal

**Agora o equalizador realmente funciona e modifica o som das suas músicas!** 🎵🎛️
