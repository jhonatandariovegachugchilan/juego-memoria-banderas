import json
import os

LEADERBOARD_FILE = os.path.join(os.path.dirname(__file__), "leaderboard.json")

# Diccionario de banderas y códigos/colores representativos
# Incluye banderas de Europa y del resto del mundo para todos los niveles
FLAGS_DATA = [
    # Europa
    {"id": "ES", "name": "España", "colors": ["#AA151B", "#F1BF00", "#AA151B"], "type": "horizontal"},
    {"id": "FR", "name": "Francia", "colors": ["#0055A4", "#FFFFFF", "#EF4135"], "type": "vertical"},
    {"id": "DE", "name": "Alemania", "colors": ["#000000", "#DD0000", "#FFCE00"], "type": "horizontal"},
    {"id": "IT", "name": "Italia", "colors": ["#009246", "#FFFFFF", "#CE2B37"], "type": "vertical"},
    {"id": "PT", "name": "Portugal", "colors": ["#046A38", "#DA291C"], "type": "vertical_split"},
    {"id": "NL", "name": "Países Bajos", "colors": ["#AE1C28", "#FFFFFF", "#21468B"], "type": "horizontal"},
    {"id": "BE", "name": "Bélgica", "colors": ["#000000", "#FDDA24", "#EF3340"], "type": "vertical"},
    {"id": "IE", "name": "Irlanda", "colors": ["#169B62", "#FFFFFF", "#FF883E"], "type": "vertical"},
    {"id": "SE", "name": "Suecia", "colors": ["#006AA7", "#FECC00"], "type": "nordic"},
    {"id": "PL", "name": "Polonia", "colors": ["#FFFFFF", "#DC143C"], "type": "horizontal_two"},
    {"id": "AT", "name": "Austria", "colors": ["#ED2939", "#FFFFFF", "#ED2939"], "type": "horizontal"},
    {"id": "GR", "name": "Grecia", "colors": ["#0D5EAF", "#FFFFFF"], "type": "stripes_blue"},
    {"id": "FI", "name": "Finlandia", "colors": ["#FFFFFF", "#003580"], "type": "nordic_white"},
    {"id": "DK", "name": "Dinamarca", "colors": ["#C60C30", "#FFFFFF"], "type": "nordic_red"},
    {"id": "NO", "name": "Noruega", "colors": ["#BA0C2F", "#00205B", "#FFFFFF"], "type": "nordic_norway"},
    {"id": "CH", "name": "Suiza", "colors": ["#DA291C", "#FFFFFF"], "type": "swiss_cross"},
    {"id": "UA", "name": "Ucrania", "colors": ["#0057B7", "#FFD700"], "type": "horizontal_two"},
    {"id": "RO", "name": "Rumanía", "colors": ["#002B7F", "#FCD116", "#CE1126"], "type": "vertical"},
    # Mundo
    {"id": "AR", "name": "Argentina", "colors": ["#75AADB", "#FFFFFF", "#75AADB"], "type": "horizontal"},
    {"id": "BR", "name": "Brasil", "colors": ["#009739", "#FEDD00", "#012169"], "type": "brazil"},
    {"id": "JP", "name": "Japón", "colors": ["#FFFFFF", "#BC002D"], "type": "circle"},
    {"id": "MX", "name": "México", "colors": ["#006847", "#FFFFFF", "#CE1126"], "type": "vertical"},
    {"id": "CO", "name": "Colombia", "colors": ["#FCD116", "#003893", "#CE1126"], "type": "colombia"},
    {"id": "CA", "name": "Canadá", "colors": ["#FF0000", "#FFFFFF", "#FF0000"], "type": "canada"},
    {"id": "CL", "name": "Chile", "colors": ["#0039A6", "#FFFFFF", "#D52B1E"], "type": "chile"},
    {"id": "PE", "name": "Perú", "colors": ["#D91023", "#FFFFFF", "#D91023"], "type": "vertical"},
    {"id": "UY", "name": "Uruguay", "colors": ["#0038A8", "#FFFFFF"], "type": "stripes_blue"},
    {"id": "KR", "name": "Corea del Sur", "colors": ["#FFFFFF", "#CD2E3A", "#0047A0"], "type": "korea"},
    {"id": "US", "name": "EE. UU.", "colors": ["#B22234", "#FFFFFF", "#3C3B6E"], "type": "usa"},
    {"id": "ZA", "name": "Sudáfrica", "colors": ["#007749", "#001489", "#E03C31", "#FFB612"], "type": "horizontal"},
    {"id": "EG", "name": "Egipto", "colors": ["#CE1126", "#FFFFFF", "#000000"], "type": "horizontal"},
    {"id": "AU", "name": "Australia", "colors": ["#00008B", "#FFFFFF", "#FF0000"], "type": "horizontal"},
]

def load_leaderboard():
    """Carga los mejores tiempos desde archivo JSON."""
    if not os.path.exists(LEADERBOARD_FILE):
        return {"Fácil (4x4)": [], "Normal (6x6)": [], "Difícil (8x8)": []}
    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Asegurar claves
            for diff in ["Fácil (4x4)", "Normal (6x6)", "Difícil (8x8)"]:
                if diff not in data:
                    data[diff] = []
            return data
    except Exception:
        return {"Fácil (4x4)": [], "Normal (6x6)": [], "Difícil (8x8)": []}

def save_score(difficulty, name, time_ms, errors):
    """Guarda una puntuación en el leaderboard si entra en el Top 10."""
    data = load_leaderboard()
    scores = data.get(difficulty, [])
    scores.append({
        "name": name.strip() or "Jugador",
        "time_ms": time_ms,
        "time_formatted": format_time(time_ms),
        "errors": errors
    })
    # Ordenar primero por menor tiempo, luego por menos errores
    scores.sort(key=lambda x: (x["time_ms"], x["errors"]))
    data[difficulty] = scores[:10]  # Mantener Top 10
    
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return data[difficulty]

def is_top_score(difficulty, time_ms, errors):
    """Verifica si el tiempo obtenido clasifica para el Top 10."""
    data = load_leaderboard()
    scores = data.get(difficulty, [])
    if len(scores) < 10:
        return True
    last = scores[-1]
    return (time_ms, errors) < (last["time_ms"], last["errors"])

def format_time(ms):
    """Convierte milisegundos a formato MM:SS:ms."""
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    centiseconds = (ms % 1000) // 10
    return f"{minutes:02d}:{seconds:02d}:{centiseconds:02d}"

