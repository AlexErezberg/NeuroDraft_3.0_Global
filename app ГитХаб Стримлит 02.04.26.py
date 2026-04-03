import streamlit as st
import json
import random
import traceback
import re
import io
import plotly.graph_objects as go
from docx import Document

class NeuroExpertMaster:
    def __init__(self, matrix_data):
        try:
            # СТЫКОВКА: Берем данные напрямую из памяти Стримлита
            self.lib = matrix_data
            
            def deep_find(data, target):
                if isinstance(data, dict):
                    if target in data: return data[target]
                    for v in data.values():
                        found = deep_find(v, target)
                        if found: return found
                return None
            
            self.rv = deep_find(self.lib, "risk_verification")
            self.sr = deep_find(self.lib, "suicide_risk")
            self.nv = deep_find(self.lib, "neuro_vectors")
            # st.toast — это маленькое всплывающее окно в Стримлите
            st.toast("✅ ПРИЛОЖЕНИЕ ЗАПУЩЕНО")
        except Exception as e: 
            st.error(f"❌ Ошибка инициализации: {e}")
            self.lib = {}

    def apply_gender(self, text, gender, is_endo=False):
        if isinstance(text, list):
            forbidden = "(органика)" if is_endo else "(эндоген)"
            # 1. Сначала ВЫКИДЫВАЕМ всё чуждое:
            filtered = [str(t) for t in text if forbidden not in str(t).lower()]
            # 2. А теперь выбираем только из того, что осталось:
            text = random.choice(filtered) if filtered else random.choice(text)

        text = str(text)
        is_fem = (gender == 'а')
        if is_fem: text = text.replace("ен{g}", "на").replace("{g}", "а")
        else: text = text.replace("{g}", "")

        fem_map = {"инертен": "инертна", "активен": "активна", "спокоен": "спокойна", "ориентирован": "ориентирована",
                   "адекватен": "адекватна", "неустойчив": "неустойчива", "заторможен": "заторможена",
                   "подвижен": "подвижна", "зависим": "зависима", "резв": "резва", "доступен": "доступна"}
        if is_fem:
            for m, f in fem_map.items(): text = re.sub(rf"\b{m}\b", f, text)
            text = text.replace("пациент ", "пациентка ")
        else: text = text.replace("пациентка", "пациент")

        text = text.replace("['", "").replace("']", "").replace("'", "").replace('"', "")
        text = re.sub(r"\(.*?\)", "", text).replace("..", ".").replace(" ,", ",").replace(",,", ",").replace(". ,", ". ")
        sentences = [s.strip().capitalize() for s in text.split('.') if s.strip()]
        return ". ".join(sentences) + "." if sentences else ""

    def run(self, code_str, pr_in, t_in):
        try:
            head, s_raw = code_str.split('/')
            raw_typ = head.rstrip('мж'); gen = 'а' if head.endswith('ж') else ''
            s = [int(x) for x in s_raw if x.isdigit()][:10]
            while len(s) < 10: s.append(0)

            st_log = self.lib.get("status_logic", {}); cl_bases = self.lib.get("clinical_bases", {})
            concl = cl_bases.get("conclusions", self.lib.get("conclusions", {}))
            adj_lib = self.lib.get("phenomenology_adjustments", {})
            intros = st_log.get("intros", {})

            typ_key = raw_typ if raw_typ in intros else ('0' if raw_typ.startswith('0') else raw_typ)
            is_endo = (typ_key == "8"); is_organ = typ_key in ["1","2","3","4","5"]
            is_norm_logic = typ_key.startswith('0') and sum(s) < 10
            presets = [p.strip() for p in pr_in.split(',') if p.strip()]; tags = [t.strip().lower() for t in t_in.split(',') if t.strip()]

            # --- 1. Психологический статус ---
            st_raw = [intros.get(typ_key, intros.get("0", "")), cl_bases.get(raw_typ if raw_typ in cl_bases else str(round(sum(s) / 10)), "")]
            # Добавляем ПА в статус, если есть тег
            if "па" in tags: st_raw.append(self.lib.get("tags", {}).get("па", ""))
            for p in presets:
                # Ищем надстройку и как ввел (ретик), и капсом (РЕТИК) на всякий случай
                p_data = adj_lib.get(p, adj_lib.get(p.upper(), {}))
                st_raw.append(p_data.get("status", ""))
            for t in tags:
                if t != "па": st_raw.append(self.lib.get("tags", {}).get(t, ""))
            if hasattr(self, 'sr') and self.sr:
                # Берем фразу по типу профиля (3, 8, 0*) или дефолт "0"
                s_phrase = self.sr.get(typ_key, self.sr.get("0", ""))
                if s_phrase:
                    st_raw.append(s_phrase)
            status_text = ". ".join([self.apply_gender(p, gen, is_endo).rstrip('.') for p in st_raw if p]) + "."

            # --- 2. РЕЗУЛЬТАТЫ ---
            f_res = []
            f_keys = ["attention", "visual_gnosis", "spatial", "dynamic_praxis", "afferent_praxis", "cube", "calculation", "speech", "memory", "thinking"]
            for i, k in enumerate(f_keys):
                f_res.append(self.apply_gender(self.lib.get("functions", {}).get(k, {}).get(str(s[i]), [""]), gen, is_endo))
                for p in presets:
                    res_adj = adj_lib.get(p, {}).get("results", "")
                    if res_adj and ((i == 3 and p in ["Апрдин", "леврег", "праврег"]) or (i == 7 and p in ["Асенс", "Асем", "Ааф"])):
                        f_res.append(self.apply_gender(res_adj, gen, is_endo))

            # --- 3. ЗАКЛЮЧЕНИЕ ---
            final = []
            # Вектор Депрессии/Горя
            if (typ_key == "9" or any(p.startswith('Д') for p in presets)) and self.nv:
                final.append(self.apply_gender(self.nv.get("9", ""), gen, is_endo))

            # САММАРИ (Синтез по баллам)
            summ_list = concl.get("functional_summaries", [""])
            s_sum = sum(s); s_idx = 0 if s_sum <= 7 else (1 if s_sum <= 15 else 2)
            if is_norm_logic: s_idx = 0
            final.append(self.apply_gender(summ_list[s_idx if s_idx < len(summ_list) else -1], gen, is_endo))

            # --- СИНТЕЗ (ЦЕМЕНТ) ---
            # 1. Берем данные. Если это словарь (старый вид) - превращаем в список значений
            raw_synth = concl.get("synthesis", [])
            synth_list = list(raw_synth.values()) if isinstance(raw_synth, dict) else raw_synth

            if synth_list and s_sum >= 3:
                # Определяем корзину (0, 1 или 2)
                s_idx = 1 if is_endo else (0 if s_sum <= 7 else (1 if s_sum <= 15 else 2))
                # Безопасный забор фразы (чтобы не было IndexError)
                target_phrase = synth_list[s_idx if s_idx < len(synth_list) else -1]
                final.append(self.apply_gender(target_phrase, gen, is_endo))

            # --- ВЕКТОРЫ (Аддитивная сборка: Личина + ВСЕ Теги + ПА) ---
            v_parts = []

            # 1. Базовый вектор (ТОЛЬКО для избранных 8, 7, 9)
            if is_endo or (typ_key in ["9", "7"]):
                base_v = self.nv.get(typ_key, "")
                if base_v: v_parts.append(base_v)

            # 2. А ТЕГИ ДОСТУПНЫ ВСЕМ (Выровнял влево!)
            for t in tags:
                if t in self.nv and t != "па":
                    v_parts.append(self.nv[t])

            # 3. ПА ТОЖЕ ДЛЯ ВСЕХ (Выровнял влево!)
            if "па" in tags and "па" in self.nv:
                v_parts.append(self.nv["па"])

            # 4. СБОРКА И ЧИСТКА (Выровнял влево!)
            if v_parts:
                v_clean = [random.choice(p) if isinstance(p, list) else p for p in v_parts]
                final.append(self.apply_gender(" ".join(v_clean), gen, is_endo))

            # ФАКТОРЫ С БУСТЕРАМИ
            if not is_norm_logic:
                f_active = []; f_p = concl.get("factors", {})
                b1 = 3 if any(p in ["н", "Апат", "асте"] for p in presets) and is_organ else 0
                b2 = 3 if any(p in ["Асенс", "Ааф", "Аак", "Асем", "Апркин", "Апркон", "АгнП", "АгнЛ", "неглект"] for p in presets) and is_organ else 0
                b3 = 3 if any(p in ["праврег", "леврег", "Аэф", "Апрдин"] for p in presets) and is_organ else 0

                if (s[0] + s[6] + b1 >= 3): f_active.append(self.apply_gender(f_p.get('neurodynamic', ''), gen, is_endo).rstrip('.') + " (I блок)")
                if (s[1] + s[2] + s[5] + b2 >= 3): f_active.append(self.apply_gender(f_p.get('spatial', ''), gen, is_endo).rstrip('.') + " (II блок)")
                if (s[3] + s[9] + b3 >= 3): f_active.append(self.apply_gender(f_p.get('regulatory', ''), gen, is_endo).rstrip('.') + " (III блок)")

                if f_active:
                    res_f = f_active[0]
                    for n_f in f_active[1:]: res_f = res_f.rstrip(".") + ", " + n_f[:1].lower() + n_f[1:]
                    for p in presets:
                        concl_adj = adj_lib.get(p, {}).get("conclusion", "")
                        if concl_adj: res_f = res_f.rstrip(".") + ". " + self.apply_gender(concl_adj, gen, is_endo)
                    final.append(res_f)

            # РЕЗЮМЕ И ВАРИАТИВНЫЙ РИСК
            final.append(self.apply_gender(concl.get("personality_emotional_resume", {}).get("stable" if is_norm_logic else "unstable", ""), gen, is_endo))
            if self.rv:
                risk_opts = self.rv.get(typ_key, self.rv.get("0", ""))
                final.append(self.apply_gender(risk_opts, gen, is_endo))

            return f"ПСИХОЛОГИЧЕСКИЙ СТАТУС:\n{status_text}\n\nРЕЗУЛЬТАТЫ:\n{' '.join(f_res)}\n\nЗАКЛЮЧЕНИЕ:\n" + "\n".join([p.strip() for p in final if p.strip()])
            return final_res

        except Exception: 
            return traceback.format_exc()

# Загрузка JSON-аккумулятора
@st.cache_data
def load_matrix():
    with open('expert_matrix.json', 'r', encoding='utf-8-sig') as f:
        return json.load(f)

matrix = load_matrix()

# --- ВОТ ЭТОГО У ТЕБЯ НЕ ХВАТАЕТ (ВСТАВЬ В НАЧАЛО) ---
def reset_app():
    if "fio_input" in st.session_state: st.session_state["fio_input"] = "Иванов И.И."
    if "age_input" in st.session_state: st.session_state["age_input"] = 65
    if "profile_select" in st.session_state: st.session_state["profile_select"] = "0*"
    for i in range(10):
        if f"s_{i}" in st.session_state: st.session_state[f"s_{i}"] = 0
    if "adj_ms" in st.session_state: st.session_state["adj_ms"] = []
    if "tags_ms" in st.session_state: st.session_state["tags_ms"] = []
    st.rerun()

st.set_page_config(page_title="NeuroExpert Web", layout="wide")

import base64

# 1. ФУНКЦИЯ КОДИРОВАНИЯ КАРТИНКИ (Чтобы вшить в HTML)
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return ""

# Кодируем твой мозг
img_base64 = get_base64_image("brain3.jpg")

# --- СУПЕР-СЛИМ ШАПКА (В ОДНУ СТРОКУ) ---
st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, #0e1117 0%, #1c1f26 100%); 
        padding: 8px 15px; 
        border-radius: 10px; 
        border-left: 5px solid #FF4B4B; 
        display: flex; 
        align-items: center; 
        gap: 15px;
        margin-bottom: 15px;
    ">
        <img src="data:image/jpeg;base64,{img_base64}" style="width: 40px; height: 40px; border-radius: 5px;">
        <div style="display: flex; flex-direction: column;">
            <h2 style="color: #ffffff; margin: 0; font-family: 'Segoe UI'; font-size: 1.4em; line-height: 1;">
                <span style="color: #FF4B4B;">Neuro</span>Expert
            </h2>
            <span style="color: #808495; font-style: italic; font-size: 0.75em;">Комплексная система синдромального нейропсихологического анализа</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 1. СЕКРЕТНЫЙ ЗАМОК (В САМОМ ВЕРХУ ПЕРЕД ПРОВЕРКОЙ) ---
PASSWORD = "1111" # <--- УБЕДИСЬ, ЧТО ОН ТУТ!

if "auth" not in st.session_state:
    st.session_state["auth"] = False

# --- 2. ТЕПЕРЬ ПРОВЕРЯЕМ ---
if not st.session_state["auth"]:
    # Твоя монолитная шапка (NeuroExpert)
    # ... (вставь сюда свой блок с градиентом и мозгом) ...
    
    pwd_input = st.text_input("🔑 Доступ к системе:", type="password")
    if pwd_input == PASSWORD:
        # ЗАСТАВКА (Строго 1.5 сек)
        with st.empty():
            st.markdown(f"""
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 300px; background-color: #0e1117;">
                    <img src="data:image/jpeg;base64,{img_base64}" style="width: 80px; filter: grayscale(100%) brightness(1.5);">
                    <h2 style="color: #FF4B4B; font-family: 'Segoe UI'; margin-top: 20px; letter-spacing: 2px;">INITIALIZING...</h2>
                </div>
            """, unsafe_allow_html=True)
            import time
            time.sleep(1.5)
            st.session_state["auth"] = True
            st.rerun()
    elif pwd_input:
        st.error("❌ Отказано")
    st.stop() # ОСТАНАВЛИВАЕМ ВСЁ ДО ВВОДА ПАРОЛЯ

# --- 2. ЛЕВАЯ ПАНЕЛЬ (ПОЯВИТСЯ ТОЛЬКО ПОСЛЕ ПАРОЛЯ) ---
with st.sidebar:
    # 1. МОЗГИ (Ужатые)
    c1, c2, c3 = st.columns([1, 2, 1]) 
    with c2:
        try: st.image("brain2.jpg", width=120)
        except: st.write("🧠")
            
    # 2. МИКРО-КНОПКИ В ОДИН РЯД (Сброс и Гайд теперь тут!)
    c_rst, c_gde = st.columns(2)
    with c_rst:
        if st.button("♻️ СБРОС", type="secondary", use_container_width=True):
            reset_app()
    with c_gde:
        try:
            with open("AppGuide.pdf", "rb") as f:
                st.download_button("📚 ГАЙД", f, "AppGuide.pdf", use_container_width=True)
        except: pass

    st.header("📋 Пациент")
    
    fio = st.text_input("ФИО", "Иванов И.И.", key="fio_input")
    
    # Пол и Возраст в одну строку для компактности
    c_age, c_sex = st.columns([1, 1])
    with c_age:
        age = st.number_input("Возраст", 1, 110, 65, key="age_input")
    with c_sex:
        p_gen = st.radio("Пол", ["м", "ж"], horizontal=True)
    
    p_type = st.selectbox("Тип", ["0*", "0+", "00", "0т", "0-", "0000", "0", "0сон", "1", "2", "3", "4", "5", "7", "8", "9", "9гэ"], key="profile_select")

    st.markdown("---")
    
    # Надстройки и Теги
    adj_keys = list(matrix.get("phenomenology_adjustments", {}).keys())
    presets = st.multiselect("🛠 Надстройки", adj_keys, key="adj_ms")
    tag_keys = list(matrix.get("tags", {}).keys())
    selected_tags = st.multiselect("🏷 Теги", tag_keys, key="tags_ms")

    # ТВОИ КРЕДИТЫ (Cognicore Systems)
    st.markdown("""
        <div style="background-color: #1c1f26; padding: 10px; border-radius: 10px; border: 1px solid #3d404a; text-align: center; margin-top: 20px;">
            <p style="color: #808495; font-size: 0.7em; margin: 0;">© 2026 Все права защищены</p>
            <p style="color: #FF4B4B; font-weight: bold; font-size: 0.9em; margin: 5px 0;">NEURO-EXPERT ENGINE</p>
            <p style="color: #ffffff; font-size: 0.75em; margin: 0;">Разработка и методология:<br><b>Cognicore Systems</b></p>
            <hr style="margin: 8px 0; border: 0.5px solid #333;">
            <p style="color: #555; font-size: 0.6em;">Commercial v85.6-STABLE</p>
        </div>
    """, unsafe_allow_html=True)

# --- 3. ЦЕНТРАЛЬНОЕ ПОЛЕ (ФУНКЦИИ) ---
st.subheader("📊 Функции (0-5)")
f_names = ["Внимание", "Зрит.Гнозис", "Простр.Гнозис", "Дин.Праксис", "Кин.Праксис", "Констр.Праксис", "Счет", "Речь", "Память", "Мышление"]
scores = []

# УБРАЛИ КОЛОНКИ: теперь ползунки идут СТРОГО 1, 2, 3... без путаницы на смарте
for i, name in enumerate(f_names):
    scores.append(st.slider(f"{i+1}. {name}", 0, 5, 0, key=f"s_{i}"))

# --- ФУНКЦИЯ ДИАЛОГОВОГО ОКНА ---
@st.dialog("📄 ИТОГОВЫЙ ПРОТОКОЛ", width="large")
def show_result_dialog(report_text, fio_name, p_type, presets, selected_tags, scores, f_names):
    # --- 1. ЛОГИКА ЯДРА (N, D, Org, Sch) ---
    core_label = "Org"
    d_presets = ["Дког", "Дгор", "Дгорсом", "Дсом", "Дтр"]
    has_d_preset = any(p in presets for p in d_presets)
    if p_type == "9" or p_type == "Дгэ" or has_d_preset: 
        core_label = "D"
    elif p_type == "8": core_label = "Sch"
    elif p_type in ["0", "0т", "0*", "0+", "0-", "00"]: core_label = "N"

    # --- 2. ЛОГИКА БУСТЕРОВ ДЛЯ БЛОКОВ ---
    is_organ = p_type in ["1", "2", "3", "4", "5"]
    b1 = 3 if any(p in ["н", "Апат", "асте"] for p in presets) and is_organ else 0
    b2 = 3 if any(p in ["Асенс", "Ааф", "Аак", "Асем", "Апркин", "Апркон", "АгнП", "АгнЛ", "неглект"] for p in presets) and is_organ else 0
    b3 = 3 if any(p in ["праврег", "леврег", "Аэф", "Апрдин"] for p in presets) and is_organ else 0

    # --- 3. СБОРКА ГРАФИКА (Чтобы не было NameError!) ---
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r = scores + [scores[0]],       # Берем только ПЕРВЫЙ балл
        theta = f_names + [f_names[0]], # Берем только ПЕРВОЕ название
        fill='toself',
        fillcolor='rgba(255, 75, 75, 0.3)',
        line=dict(color='#FF4B4B', width=2)
))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5]), angularaxis=dict(tickfont=dict(size=10, color="white"))),
        showlegend=False, height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        annotations=[dict(x=0.5, y=0.5, text=core_label, showarrow=False, font=dict(size=32, color="#FF4B4B", family="Arial Black"))]
    )

    # --- 4. РАЗМЕТКА: БЛОКИ (0.2) | ГРАФИК (0.6) | СЕТИ (0.2) ---
    col_blocks, col_chart, col_nets = st.columns([0.2, 0.6, 0.2])

    with col_blocks:
        st.write("🧠 **Блоки:**")
        # Проверка по твоей формуле (с учетом b1, b2, b3)
        blks = [
            ("БЛОК I", scores[0] + scores[6] + b1 >= 3),
            ("БЛОК II", scores[1] + scores[2] + scores[5] + b2 >= 3),
            ("БЛОК III", scores[3] + scores[9] + b3 >= 3)
        ]
        for name, active in blks:
            bg = "#FF4B4B" if active else "#1c1f26"
            tc = "white" if active else "#555"
            st.markdown(f'<div style="background:{bg}; color:{tc}; padding:8px; border-radius:5px; margin-bottom:5px; text-align:center; font-weight:bold; font-size:0.75em; border:1px solid #333;">{name}</div>', unsafe_allow_html=True)

    with col_chart:
        st.plotly_chart(fig, use_container_width=True)

    with col_nets:
        st.write("🔎 **Сети:**")
        networks = ["ДЭП", "МСА", "МКАС", "ТАЛАМ", "РЕТИК", "СТРИАР", "МПС"]
        for net in networks:
            is_active = any(p.upper() == net.upper() for p in presets)
            bg = "#FF4B4B" if is_active else "#1c1f26"
            tc = "white" if is_active else "#444"
            st.markdown(f'<div style="background:{bg}; color:{tc}; padding:4px; border-radius:5px; margin-bottom:4px; text-align:center; font-size:0.7em; font-weight:bold; border:1px solid #333;">{net}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.text_area("Текст заключения:", report_text, height=300)
    
    # КНОПКИ (Ворд / Копировать / Выход)
    c1, c2, c3 = st.columns(3)
    with c1:
        doc = Document()
        doc.add_paragraph(f"ПРОТОКОЛ: {fio_name}\n\n{report_text}")
        bio = io.BytesIO(); doc.save(bio)
        st.download_button("📥 ВОРД", bio.getvalue(), f"{fio_name}.docx", use_container_width=True)
    with c2:
        if st.button("📋 КОПИРОВАТЬ", use_container_width=True):
            st.code(report_text, language=None)
    with c3:
        if st.button("❌ ВЫХОД", use_container_width=True): st.rerun()
        
# --- 5. САМА КНОПКА ЗАПУСКА (В САМОМ НИЗУ) ---
if st.button("🚀 СГЕНЕРИРОВАТЬ ПРОТОКОЛ"):
    full_code = f"{p_type}{p_gen}/{''.join(map(str, scores))}"
    engine = NeuroExpertMaster(matrix)
    report = engine.run(full_code, ",".join(presets), ",".join(selected_tags))
    
    # ВНИМАНИЕ: Передаем ВСЕ ПАРАМЕТРЫ, чтобы график и лейблы их увидели
    show_result_dialog(
        report_text=report, 
        fio_name=fio, 
        p_type=p_type, 
        presets=presets, 
        selected_tags=selected_tags, 
        scores=scores, 
        f_names=f_names
    )
