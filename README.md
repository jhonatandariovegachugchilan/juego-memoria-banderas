# Juego de Memoria de Banderas (Desktop GUI)

Juego interactivo de memoria de parejas (Pairs / Match-2) desarrollado en Python con interfaz gráfica nativa (`tkinter`), animaciones de volteo de cartas en pseudo-3D, mecánicas dinámicas de barajado, temporizador de precisión en milisegundos y registro de mejores tiempos (Leaderboard).

## ✨ Características y Mecánicas

- **Vistas Completas**:
  - **Menú Principal**: Selección de dificultad y opciones de juego.
  - **Tablero de Juego (HUD)**: Temporizador continuo (MM:SS:ms), contador de errores y control de pares descubiertos.
  - **Pantalla de Victoria y Leaderboard**: Registro de los 10 mejores tiempos clasificados por tiempo y fallos en archivo local JSON.
- **Niveles de Dificultad**:
  - **Fácil (4x4)**: 16 cartas (8 pares). Banderas de Europa. Memorización de 3.0s.
  - **Normal (6x6)**: 36 cartas (18 pares). Banderas de Europa. Memorización de 4.0s.
  - **Difícil (8x8)**: 64 cartas (32 pares). Banderas de Europa y del Mundo. Memorización de 5.0s.
- **Mecánica Dinámica de Barajado (Configurable)**:
  - Si fallas un par, **todas las cartas no descubiertas se reubican aleatoriamente**, aumentando el desafío cognitivo. Se puede activar/desactivar desde el menú.
- **Penalización por Error**:
  - Opción de sumar +5 segundos al cronómetro por cada error cometido.
- **Animaciones Suaves y Control Antispam**:
  - Efecto de giro de carta (compresión y expansión en el eje horizontal X).
  - Máquina de estados que bloquea clics accidentales o rápidos mientras se revelan o evalúan cartas.
- **Sin Dependencias Externas**:
  - Diseñado con la librería estándar `tkinter`, con banderas dibujadas de manera procedural vectorial. No requiere instalar paquetes externos como `pygame`.

## 🚀 Requisitos y Ejecución

Solo necesitas Python 3 instalado.

```bash
cd juego_banderas
python main.py
```
