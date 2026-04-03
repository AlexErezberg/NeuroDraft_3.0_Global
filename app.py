import streamlit as st
import json
import random
import traceback
import re
import io
import plotly.graph_objects as go
from docx import Document

data = {}

class NeuroDraftAssistant:
    def __init__(self, matrix_data):
        self.lib = matrix_data
        # Глубокий радар для поиска баз (Риски, Векторы)
        def deep_find(data_source, target):
            if isinstance(data_source, dict):
                if target in data_source: 
                    return data_source[target]
                for v in data_source.values():
                    found = deep_find(v, target)
                    if found: return found
            return None
        
        self.rv_db = deep_find(self.lib, "risk_verification")
        self.sr_db = deep_find(self.lib, "suicide_risk")
        self.nv_db = deep_find(self.lib, "neuro_vectors")

    def run(self, code_str, pr_in="", t_in="", lang='ru', moca=None, mmse=None, gds=None, mri=""):
        # Прокидываем переменную data для старой логики
        data = self.lib
        try:
            head, s_raw = code_str.split('/')
            raw_typ = head.rstrip('мж')
            # Дальше твой оригинальный код с отступом 12 пробелов
            
        except Exception as e:
            return f"❌ Ошибка в run: {e}"

        except Exception as e:
            return f"❌ Ошибка в run: {e}"

    def apply_gender(self, raw_data, gender, is_endo=False, lang='ru'):
        if not raw_data: return ""
        # 1. Рандомизация и Паттерны (Organic/Thought_disorder)
        if isinstance(raw_data, list) and len(raw_data) > 0:
            target_pattern = "thought_disorder" if is_endo else "organic"
            # Фильтр: берем нужное или нейтральное
            filtered = [item for item in raw_data if isinstance(item, dict) and
                        (item.get("pattern") == target_pattern or item.get("pattern") is None)]
            target_obj = random.choice(filtered if filtered else raw_data)
        else:
            target_obj = raw_data

        # 2. Выбор языка
        if isinstance(target_obj, dict):
            text = target_obj.get(lang, target_obj.get('ru', ''))
        else:
            text = str(target_obj)

        # 3. Чистка мусора
        text = text.replace("['", "").replace("']", "").replace("'", "").replace('"', "").strip()

        # 4. Гендер (Только для RU)
        if lang == 'ru':
            is_fem = (gender == 'а')
            if is_fem:
                text = text.replace("ен{g}", "на").replace("{g}", "а")
                f_map = {"инертен": "инертна", "активен": "активна", "спокоен": "спокойна", "ориентирован": "ориентирована"}
                for m, f in f_map.items(): text = re.sub(rf"\b{m}\b", f, text)
                text = text.replace("пациент ", "пациентка ")
            else:
                text = text.replace("{g}", "").replace("пациентка", "пациент")

        text = re.sub(r"\(.*?\)", "", text).replace("..", ".").replace(" ,", ",").replace(". ,", ". ")
        sentences = [s.strip().capitalize() for s in text.split('.') if s.strip()]
        return ". ".join(sentences) + "." if sentences else ""

    def run(self, code_str, pr_in="", t_in="", lang='ru', moca=None, mmse=None, gds=None, mri=""):
        try:
            # --- 1. ПАРСИНГ И ГЕНДЕРНАЯ ГИГИЕНА ---
            head, s_raw = code_str.split('/')
            raw_typ = head.rstrip('мж')
            # Гендер только для RU, для Запада - нейтрально
            gen = ('а' if head.endswith('ж') else '') if lang == 'ru' else ''
            s = [int(x) for x in s_raw if x.isdigit()][:10]
            while len(s) < 10: s.append(0)

            # --- 2. НАВИГАТОР ПО МАТРЁШКАМ (ПОЛНЫЙ И БЕЗОПАСНЫЙ) ---
            intros = self.lib.get("intros", {})
            concl = self.lib.get("conclusions", {})

            # Эти разделы живут внутри conclusions
            recom_db = concl.get("recommendations", {})
            blocks_db = concl.get("brain_blocks", {})
            synth_db = concl.get("synthesis", {})
            pers_db = concl.get("personality_emotional_resume", {})
            factors_db = concl.get("factors", {})

            # Эти разделы могут быть в корне или в concl — ищем везде, чтобы не «ослепнуть»
            cl_b = self.lib.get("clinical_bases", concl.get("clinical_bases", {}))
            f_db = self.lib.get("functions", concl.get("functions", {}))

            # Критичные для рисков и векторов библиотеки
            rv_lib = concl.get("risk_verification", self.lib.get("risk_verification", {}))
            nv_lib = concl.get("_vectors", self.lib.get("_vectors", {}))

            # Остальное
            behav_db = self.lib.get("behavioral_patterns", self.lib.get("behavioral_patterns", {}))
            sr_lib = self.lib.get("suicide_risk", self.lib.get("suicide_risk", {}))
            adj_lib = self.lib.get("phenomenology_adjustments", self.lib.get("phenomenology_adjustments", {}))

            # --- ЛОГИКА КЛЮЧЕЙ (ОСТАВЛЯЕМ ТВОЮ БРОНЕБОЙНУЮ) ---
            t_k = str(raw_typ).strip()
            if t_k not in intros:
                if t_k.isdigit() and int(t_k) in intros:
                    t_k = int(t_k)
                else:
                    t_k = "0"

            is_endo = (str(t_k) == "8")
            is_organ = str(t_k) in ["1","2","3","4","5"]
            is_norm_logic = str(t_k).startswith('0') and sum(s) < 10

            presets = [p.strip() for p in pr_in.split(',') if p.strip()]
            tags = [t.strip().lower() for t in t_in.split(',') if t.strip()]

            # --- 3. СТАТУС (MSE) ---
            st_raw = []

            # 1. INTRO (0, 1, 8...) — Строго из корня
            raw_intro = intros.get(t_k, intros.get("0", ""))
            st_raw.append(raw_intro)

            # 2. CLINICAL BASE (Клиника) — Строго из корня cl_b
            raw_clin = cl_b.get(raw_typ, cl_b.get(str(round(sum(s)/10)), ""))
            st_raw.append(raw_clin)

            # 3. BEHAVIOR (Поведение) — Строго из корня behav_db
            st_raw.append(behav_db.get(t_k, behav_db.get("0", "")))

            # 4. ТЕГИ И НАДСТРОЙКИ (ПА, Синдромы, Пресеты)
            # Добавлена итерация по списку tags для поиска в секции data["tags"]
            tags_db = data.get("tags", {})
            for t in tags:
                t_val = tags_db.get(t)
                if t_val:
                    st_raw.append(self.apply_gender(t_val, gen, is_endo, lang))

            if "па" in tags or "panic" in tags:
                # Извлечение из nv_db через apply_gender для поддержки списков
                st_raw.append(self.apply_gender(self.nv_db.get("panic-history", ""), gen, is_endo, lang))

            for p in presets:
                # Вшиваем статус напрямую из adj_lib через apply_gender
                p_status = adj_lib.get(p, {}).get("status", "")
                if p_status:
                    st_raw.append(self.apply_gender(p_status, gen, is_endo, lang))

            # 5. SUICIDE RISK (Риск в MSE) — Строго из корня sr_lib
            raw_sr = sr_lib.get(t_k, sr_lib.get("0*", sr_lib.get("0", "")))

            if not raw_sr:
                raw_sr = sr_lib.get("0w", sr_lib.get("0-", ""))

            if raw_sr:
                st_raw.append(self.apply_gender(raw_sr, gen, is_endo, lang))

            # ФИНАЛЬНАЯ СКЛЕЙКА (Гендерная мясорубка)
            # Прогоняем каждый кусок ЧЕРЕЗ apply_gender один раз!
            status_parts = [self.apply_gender(p, gen, is_endo, lang).strip().rstrip('.') for p in st_raw if p]
            status_text = ". ".join(status_parts) + "."

            # --- 4. ПРОФИЛЬ (ВПФ) С БУСТЕРАМИ ---
            f_res = []
            f_keys = ["attention", "visual_gnosis", "spatial", "dynamic_praxis", "afferent_praxis", "cube", "calculation", "speech", "memory", "thinking"]

            # 1. Сначала ПРЕАМБУЛА (Сетевые надстройки в самое начало)
            network_p = ["ndyn", "v-frontal", "msa", "mcas", "striar"]
            for p in presets:
                if p in network_p:
                    res_adj = adj_lib.get(p, {}).get("results", "")
                    if res_adj:
                        f_res.append(self.apply_gender(res_adj, gen, is_endo, lang))

            # 2. ОСНОВНОЙ ЦИКЛ ПО ФУНКЦИЯМ
            # Маппинг: какой пресет в какой индекс (i) подмешивать
            p_map = {
                "apr-dyn": 3, "apr-kin": 4, "apr-con": 5,
                "a-sens": 7, "a-eff": 7, "a-dyn": 7, "a-aff": 7, "a-amn": 7, "a-sem": 7,
                "v-gnosis": 1, "v-neglect": 2, "r-reg": 9, "l-reg": 9
            }

            for i, k in enumerate(f_keys):
                # Базовое описание из f_db (по баллу s[i])
                f_val = f_db.get(k, {}).get(str(s[i]), "")
                if f_val:
                    f_res.append(self.apply_gender(f_val, gen, is_endo, lang))

                # Вшиваем надстройки (бустеры) по нашей карте p_map
                for p in presets:
                    if p_map.get(p) == i:
                        res_adj = adj_lib.get(p, {}).get("results", "")
                        if res_adj:
                            f_res.append(self.apply_gender(res_adj, gen, is_endo, lang))

            # --- 5. ЗАКЛЮЧЕНИЕ (СИНТЕЗ И ВЕРИФИКАЦИЯ) ---
            final = []

            # 1. ОБНОВЛЕННЫЙ СЛОВАРЬ ШАБЛОНОВ (RU/EN/ES/PT)
            scr_tpl = {
                "ru": "Результаты скрининга (MoCA: {m}, MMSE: {mm}, GDS: {g}) подтверждают {s} когнитивное снижение{d}.",
                "en": "Screening results (MoCA: {m}, MMSE: {mm}, GDS: {g}) corroborate {s} cognitive impairment{d}.",
                "es": "Los resultados del screening (MoCA: {m}, MMSE: {mm}, GDS: {g}) confirman un deterioro cognitivo {s}{d}.",
                "pt": "Os resultados do rastreio (MoCA: {m}, MMSE: {mm}, GDS: {g}) confirmam um compromisso cognitivo {s}{d}."
            }

            # 2. СТЕПЕНИ ТЯЖЕСТИ
            sev_map = {
                "severe":   {"ru": "выраженное", "en": "severe",   "es": "grave",    "pt": "grave"},
                "moderate": {"ru": "умеренное",  "en": "moderate", "es": "moderado", "pt": "moderado"},
                "mild":     {"ru": "легкое",     "en": "mild",     "es": "leve",     "pt": "leve"}
            }

            # 3. ЛОГИКА ОПРЕДЕЛЕНИЯ И ВЫВОДА
            if moca or mmse or gds:
                # Оценка когнитивной тяжести
                m_val = int(moca) if (moca and str(moca).isdigit()) else 30
                if m_val < 11: s_key = "severe"
                elif m_val < 19: s_key = "moderate"
                else: s_key = "mild"

                # Оценка депрессии по GDS (триггер для текста)
                dep_add = ""
                if gds and str(gds).isdigit():
                    gv = int(gds)
                    if gv > 9:
                        dep_add = {"ru": " и тяжелую депрессию", "en": " and severe depression", "es": " y depresión grave", "pt": " e depressão grave"}.get(lang)
                    elif gv > 4:
                        dep_add = {"ru": " и легкую депрессию", "en": " and mild depression", "es": " y depresión leve", "pt": " e depressão leve"}.get(lang)

                s_word = sev_map[s_key].get(lang, sev_map[s_key]["en"])
                tpl = scr_tpl.get(lang, scr_tpl["en"])

                # Формируем строку: m=MoCA, mm=MMSE, g=GDS, s=степень, d=хвост про депрессию
                final.append(tpl.format(
                    m=moca or "—",
                    mm=mmse or "—",
                    g=gds or "—",
                    s=s_word,
                    d=dep_add or ""
                ))

            # MRI Сцепка (Match or Silent)
            if mri and lang != 'ru':
                m_low = mri.lower()
                mri_matches = []

                # Карта под твои f_keys (0-9)
                correlations = [
                    ("frontal", [0, 3, 9], 4, {
                        "en": "Frontal imaging findings correlate with identified executive dysfunction and impaired motor programming.",
                        "es": "Los hallazgos frontales correlacionan con la disfunción ejecutiva identificada y la alteración de la programación motora.",
                        "pt": "Os achados de imagem frontal correlacionam-se com a disfunción ejecutiva identificada."
                    }),
                    ("temporal", [7, 8], 3, {
                        "en": "Temporal imaging findings correlate with identified semantic disintegration and mnemonic deficits.",
                        "es": "Los hallazgos temporales correlacionan con la desintegración semántica и los déficits mnésicos.",
                        "pt": "Os achados de imagem temporal correlacionam-se com a desintegração semântica."
                    }),
                    ("parietal", [2, 4, 6], 4, {
                        "en": "Parietal structural findings match the observed visuospatial fragmentation and somatosensory deficits.",
                        "es": "Los hallazgos parietales coinciden con la fragmentación visoespacial observada.",
                        "pt": "Os achados estruturais parietais coincidem com a fragmentação visoespacial."
                    }),
                    ("occipital", [1, 2], 4, {
                        "en": "Occipital imaging findings correlate with identified visual processing deficits and perceptual fragmentation.",
                        "es": "Los hallazgos occipitales correlacionan con los déficits de procesamiento visual.",
                        "pt": "Os achados occipitais correlacionam-se com os déficits de processamento visual."
                    }),
                    ("limbic", [8, 9], 3, {
                        "en": "Limbic system involvement is highly consistent with the observed affective dysregulation and mnemonic interference.",
                        "es": "La afectación del sistema límbico es consistente con la desregulación afectiva y la interferencia mnésica observada.",
                        "pt": "O envolvimento do sistema límbico é consistente com a desregulação afetiva observada."
                    }),
                    ("callosal", [3, 4], 3, {
                        "en": "Findings in the corpus callosum are consistent with the observed callosal disconnection syndrome and interhemispheric transfer failure.",
                        "es": "Los hallazgos en el cuerpo calloso coinciden con el síndrome de desconexión callosa.",
                        "pt": "Os achados no corpo caloso coincidem com a síndrome de desconexão calosa."
                    }),
                    ("cerebellar", [0, 9], 3, {
                        "en": "Cerebellar structural changes match the identified Dysmetria of Thought (CCAS), correlating with executive and dynamic instability.",
                        "es": "Los hallazgos cerebelosos coinciden con la dismetría del pensamiento (CCAS).",
                        "pt": "Os achados cerebelares coincidem com a dismetria do pensamento (CCAS)."
                    }),
                    ("subcortical", [0, 3], 4, {
                        "en": "Subcortical findings match the observed bradyphrenia and impaired motor initiation.",
                        "es": "Los hallazgos subcorticales coinciden con la bradifrenia identificada.",
                        "pt": "Os achados subcorticais coincidem com a bradifrenia identificada."
                    }),
                    ("hippocampal", [8], 2, {
                        "en": "Hippocampal volume reduction is highly consistent with the recorded episodic memory impairment.",
                        "es": "La reducción del volumen hipocampal es consistente con el deterioro de la memoria episódica.",
                        "pt": "A redução do volume hipocampal é consistente com o comprometimento da memória."
                    })
                ]

                for zone, indices, threshold, texts in correlations:
                    if zone in m_low:
                        score = sum(s[i] for i in indices)
                        if score >= threshold:
                            # Достаем строку из словаря по ключу lang
                            mri_matches.append(texts.get(lang, texts['en']))
                        else:
                            # Сообщение о компенсации
                            if lang == 'es':
                                mri_matches.append(f"Se observan hallazgos en {zone}; sin embargo, la compensación funcional se mantiene preservada.")
                            elif lang == 'pt':
                                mri_matches.append(f"Observam-se achados em {zone}; no entanto, a compensação funcional mantém-se preservada.")
                            else:
                                mri_matches.append(f"Noted {zone} structural findings; however, cognitive functions remain within the compensated range.")

                if mri_matches:
                    # Теперь в списке только строки, join сработает
                    final.append(" ".join(mri_matches))

            # --- 5.1. АЛГОРИТМ ВЫДЕЛЕНИЯ ВЕДУЩИХ ПИКОВ (MMPI-STYLE) ---
            final = []

            # 🔥 ШАГ 0: ИНИЦИАЛИЗАЦИЯ ВСЕХ ПЕРЕМЕННЫХ (ЧТОБЫ НЕ БЫЛО ОШИБОК)
            st_key = str(t_k)
            avg_s = sum(s) / 10
            m_val = int(moca) if (moca and str(moca).isdigit()) else 30
            g_val = int(gds) if (gds and str(gds).isdigit()) else 0
            has_dep_preset = any(p.startswith('dep-') for p in presets)
            
            # --- ШАГ 1: ДЕТЕКТОР ДИССОЦИАЦИИ (MoCA vs ЛУРИЯ) ---
            if m_val < 20 and avg_s < 1.0:
                dis_warn = {
                    "ru": "Внимание: отмечается выраженная диссоциация между низкими показателями скрининга и сохранностью операциональных звеньев в углубленном обследовании, что требует исключения установочного поведения.",
                    "en": "Note: a marked dissociation is observed between low screening scores and the preservation of operational components in the in-depth assessment, necessitating the exclusion of malingering or effort-related bias.",
                    "es": "Nota: se observa una marcada disociación entre las bajas puntuaciones del screening y la preservación de los componentes operativos, lo que requiere descartar conductas de simulación.",
                    "pt": "Nota: observa-se uma marcada dissociação entre os baixos escores de rastreio e a preservação dos componentes operacionais, necessitando a exclusão de comportamentos de simulação."
                }.get(lang)
                if dis_warn:
                    final.append(f"⚠️ !!! {dis_warn.upper()} !!! ⚠️")

            # --- ШАГ 2: ДЕТЕКТОР АФФЕКТИВНОЙ ДИССОЦИАЦИИ (GDS vs ПСИХОТИП) ---
            if (has_dep_preset or st_key == "9") and g_val < 5 and gds is not None:
                dep_dis_warn = {
                    "ru": "Внимание: отмечается аффективная диссоциация (низкий балл по GDS при клинически верифицированном депрессивном радикале), что может указывать на диссимуляцию",
                    "en": "Note: affective dissociation (low GDS score despite clinically verified depressive core), suggesting potential dissimulation or lack of insight",
                    "es": "Nota: disociación afectiva (baja puntuación GDS a pesar del núcleo depresivo clínicamente verificado), lo que sugiere posible disimulación",
                    "pt": "Nota: dissociação afetiva (baixo escore GDS apesar do núcleo depressivo clinicamente verificado), sugerindo possível dissimulação"
                }.get(lang)
                if dep_dis_warn:
                    final.append(f"⚠️ !!! {dep_dis_warn.upper()} !!! ⚠️")

            # Пик — это индекс, который >= 3 баллов И заметно хуже среднего (+0.8 к среднему)
            peaks = [i for i, val in enumerate(s) if val >= 3 and val >= (avg_s + 0.8)]
            
            # 2. Маппинг доменов (RU/EN/ES/PT)
            dom_map = {
                0: {"ru": "внимания", "en": "attention", "es": "atención", "pt": "atenção"},
                1: {"ru": "зрительного гнозиса", "en": "visual perception", "es": "percepción visual", "pt": "percepção visual"},
                2: {"ru": "пространственных функций", "en": "visuospatial processing", "es": "procesamiento visoespacial", "pt": "processamento visoespacial"},
                3: {"ru": "динамического праксиса", "en": "motor programming", "es": "programación motora", "pt": "programação motora"},
                4: {"ru": "афферентного праксиса", "en": "somatosensory processing", "es": "procesamiento somatosensorial", "pt": "processamento somatosensorial"},
                5: {"ru": "праксиса", "en": "praxis", "es": "praxia", "pt": "praxia"},
                6: {"ru": "счетных операций", "en": "calculation", "es": "cálculo", "pt": "cálculo"},
                7: {"ru": "речевых функций", "en": "language functions", "es": "funciones del lenguaje", "pt": "funções da linguagem"},
                8: {"ru": "памяти", "en": "memory functions", "es": "funciones de memoria", "pt": "funções de memória"},
                9: {"ru": "исполнительных функций", "en": "executive functions", "es": "funciones ejecutivas", "pt": "funções executivas"}
            }

            lead_phrase = ""
            if avg_s >= 3.5:
                # Кейс: Тотальный завал (Деменция/МСА)
                lead_phrase = {
                    "ru": "Клиническая картина отражает системный когнитивный распад с диффузным дефицитом во всех функциональных доменах.",
                    "en": "The clinical picture reflects a systemic cognitive collapse with profound deficits across all functional domains.",
                    "es": "El cuadro clínico refleja un colapso cognitivo sistémico con déficits profundos en todos los dominios funcionales.",
                    "pt": "O quadro clínico reflete um colapso cognitivo sistêmico com déficits profundos em todos os domínios funcionais."
                }.get(lang)
            elif peaks:
                # Кейс: Выделенные пики (называем не более двух главных)
                names = [dom_map[i].get(lang, dom_map[i]['en']) for i in peaks[:2]]
                if len(names) == 1:
                    tpl = {"ru": "Профиль определяется преобладающим дефицитом в сфере {}, выступающим ядром нарушений.", 
                           "en": "The profile is defined by a predominant deficit in {}, serving as the primary core of the impairment."}.get(lang, "Deficit in {}")
                    lead_phrase = tpl.format(names[0])
                else:
                    tpl = {"ru": "Клиническая картина определяется сочетанным дефицитом в сферах {} и {}, указывающим на системный функциональный сбой.",
                           "en": "The clinical picture is dominated by a combined deficit in {} and {}, suggesting a systemic functional failure."}.get(lang, "Deficit in {} and {}")
                    lead_phrase = tpl.format(names[0], names[1])

            if lead_phrase:
                final.append(lead_phrase)

            # Функциональный итог
            summ_list = concl.get("functional_summaries", [])
            s_sum = sum(s)
            s_idx = 1 if s_sum > 7 else 0
            if summ_list:
                # Берем фразу из списка по индексу
                final.append(self.apply_gender(summ_list[s_idx if s_idx < len(summ_list) else -1], gen, is_endo, lang))

            # Факторы (Блоки) + Бустеры
            f_a = []
            b1 = 3 if any(p in ["ndyn", "н", "msa"] for p in presets) else 0
            b2 = 3 if any(p in ["v-gnosis", "A-aff"] for p in presets) else 0
            b3 = 3 if any(p in ["r-reg", "l-reg"] for p in presets) else 0
            # Словарь для локализации плашек блоков
            b_label = {
                "ru": ["(I блок)", "(II блок)", "(III блок)"],
                "en": ["(I block)", "(II block)", "(III block)"],
                "es": ["(Unidad I)", "(Unidad II)", "(Unidad III)"],
                "pt": ["(Unidade I)", "(Unidade II)", "(Unidade III)"]
            }.get(lang, ["(I block)", "(II block)", "(III block)"])

            f_a = []
            # УБИРАЕМ "+ b_label" ОТСЮДА! Пусть будет просто голый текст фактора.
            if (s[0]+s[6]+b1 >= 4): f_a.append(self.apply_gender(factors_db.get('dynamic',''), gen, is_endo, lang).rstrip('.'))
            if (s[1]+s[2]+s[8]+b2 >= 3): f_a.append(self.apply_gender(factors_db.get('spatial',''), gen, is_endo, lang).rstrip('.'))
            if (s[3]+s[9]+b3 >= 3): f_a.append(self.apply_gender(factors_db.get('regulatory',''), gen, is_endo, lang).rstrip('.'))

            if f_a:
                # Склеиваем факторы через точку с запятой для веса
                final.append("; ".join(f_a).capitalize() + ".")

            st_key = str(t_k)  # ВОТ ЭТА СТРОЧКА СПАСЕТ ТЕБЯ ОТ ERROR
            total_score = sum(s) # До кучи, чтобы и по сумме не вылетело

            # --- 5.1. НЕЙРОПСИХОЛОГИЯ (БЛОКИ И СИНТЕЗ) ---
            def fix_rim(txt):
                if not txt: return ""
                res = txt
                # 1. Сначала исправляем ТРОЙКИ (III), чтобы i не съела часть слова
                res = res.replace("iii блока", "III блока").replace("iii блок", "III блок")
                res = res.replace("unidad iii", "Unidad III").replace("unit iii", "Unit III")
                res = res.replace("unidade iii", "Unidade III") # Порта

                # 2. Потом ДВОЙКИ (II)
                res = res.replace("ii блока", "II блока").replace("ii блок", "II блок")
                res = res.replace("unidad ii", "Unidad II").replace("unit ii", "Unit II")
                res = res.replace("unidade ii", "Unidade II") # Порта

                # 3. В конце ЕДИНИЦЫ (I)
                res = res.replace("i блока", "I блока").replace("i блок", "I блок")
                res = res.replace("unidad i", "Unidad I").replace("unit i", "Unit I")
                res = res.replace("unidade i", "Unidade I") # Порта

                # 4. На всякий случай ловим одиночные "luria" для солидности
                res = res.replace("luria", "Luria")
                return res

            # --- 5.1. УМНОЕ ОПИСАНИЕ БЛОКОВ МОЗГА (БЕЗ ОКРОШКИ) ---
            # 1 БЛОК
            if (s[0] + s[6] + b1 >= 4):
                b1_lvl = "2" if ((gds and int(gds) > 9) or max(s[0], s[6]) >= 3) else "1"
                b1_raw = blocks_db.get("block_1", [])
                # Проверка: если это словарь - берем по уровню, если список - берем как есть
                b1_data = b1_raw.get(b1_lvl, b1_raw) if isinstance(b1_raw, dict) else b1_raw
                if b1_data:
                    final.append(fix_rim(self.apply_gender(b1_data, gen, is_endo, lang)))

            # 2 БЛОК
            if (s[1] + s[2] + s[8] + b2 >= 3):
                b2_max = max(s[1], s[2], s[8])
                b2_lvl = "3" if b2_max >= 4 else ("2" if b2_max == 3 else "1")
                b2_raw = blocks_db.get("block_2", [])
                b2_data = b2_raw.get(b2_lvl, b2_raw) if isinstance(b2_raw, dict) else b2_raw
                if b2_data:
                    final.append(fix_rim(self.apply_gender(b2_data, gen, is_endo, lang)))

            # 3 БЛОК (ТВОЙ НОВЫЙ ИЕРАРХИЧЕСКИЙ МАССИВ)
            if (s[3] + s[9] + b3 >= 3):
                b3_max = max(s[3], s[9])
                b3_lvl = "3" if b3_max >= 4 else ("2" if b3_max == 3 else "1")
                b3_raw = blocks_db.get("block_3", [])
                # Здесь точно словарь, так как ты его обновил, но защита не помешает
                b3_data = b3_raw.get(b3_lvl, b3_raw) if isinstance(b3_raw, dict) else b3_raw
                if b3_data:
                    final.append(fix_rim(self.apply_gender(b3_data, gen, is_endo, lang)))

            # --- 5.2. ЛИЧНОСТНО-ЭМОЦИОНАЛЬНОЕ РЕЗЮМЕ (ФИНАЛЬНАЯ ВЕРСИЯ) ---
            # 1. Списки триггеров
            stable_pool = ['0', '00', '0w', '0+', '0*', '1', '2', '3', '4', '5']
            unstable_pool = ['0-', '7', '8', '9']
            unstable_tags = ['tox-hist', 'malingering-p', 'antisocial-p', 'panic-history', 'па']
            dep_presets = ['dep-grief', 'dep-somatic', 'dep-cog', 'dep-anxious', 'dep-adjustment']

            # 2. Проверка условий
            has_bad_tag = any(t in tags for t in unstable_tags)
            has_dep_preset = any(p in presets for p in dep_presets)

            # 3. РАСЧЕТ ОРГАНИЧЕСКОГО ЗАВАЛА (Индексы: 0, 3, 6, 7, 9)
            # Внимание + Дин.праксис + Счет + Речь + Мышление
            org_score = s[0] + s[3] + s[6] + s[7] + s[9]

            # 4. ВЫБОР КЛЮЧА (ИЕРАРХИЯ ПРИОРИТЕТОВ)
            p_key = "stable" # Дефолт

            # А. ПРИОРИТЕТ: АФФЕКТ И ПСИХИАТРИЯ (unstable)
            if st_key in unstable_pool or has_bad_tag or has_dep_preset or (gds and int(gds) > 9):
                p_key = "unstable"

            # Б. ПРИОРИТЕТ: ОРГАНИЧЕСКИЙ ДЕФИЦИТ (unstable_org)
            # Снижаем порог до 5 баллов ИЛИ если есть хоть одна "тройка" (v >= 3)
            # Это убьет "стабильность" при твоем профиле 2/1112211011
            elif org_score >= 5 or any(v >= 3 for v in s):
                p_key = "unstable_org"

            # В. ПРИОРИТЕТ: СПЕЦИФИЧЕСКИЙ КЛЮЧ
            elif st_key in pers_db:
                p_key = st_key

            # Г. ФОЛБЭК: СТАБИЛЬНОСТЬ
            elif st_key in stable_pool:
                p_key = "stable"

            # 5. ВЫТЯГИВАЕМ ТЕКСТ
            p_text = pers_db.get(p_key, [])
            if p_text:
                final.append(self.apply_gender(p_text, gen, is_endo, lang))

            # --- 5.3. КЛИНИЧЕСКИЙ РИСК И ВЕРИФИКАЦИЯ (ПРЯМАЯ СКЛЕЙКА) ---
            v_parts = []

            # 1. Сначала Тяжелые профили (Нейровекторы: 8, 9)
            if str(t_k) in ["8", "9"]:
                raw_v = nv_lib.get(str(t_k), [])
                if raw_v: v_parts.append(raw_v)

            # 2. Затем Паника (если есть тег)
            if any(t in tags for t in ["па", "panic", "panic-history"]):
                raw_p = nv_lib.get("panic-history", rv_lib.get("panic-history", []))
                if raw_p: v_parts.append(raw_p)

            # 3. В САМЫЙ КОНЕЦ: Верификация (RV-Риск: 0, 0*, 0w, 00, 8, 9)
            # Определяем ключ: если 8/9, берем их, иначе норму/органику
            rv_key = t_k if str(t_k) in rv_lib and str(t_k) not in ["0", "0т"] else ("0*" if (is_norm_logic or is_organ) else "0")
            raw_rv = rv_lib.get(str(rv_key), [])
            if raw_rv:
                v_parts.append(raw_rv)

            # ФИНАЛЬНЫЙ ВЫВОД В ОТЧЕТ
            for vp in v_parts:
                if vp:
                    # apply_gender вытянет нужный перевод из списка [{ru:...}]
                    final.append(self.apply_gender(vp, gen, is_endo, lang))

            # --- 5.4. КОДИРОВАНИЕ ПО МКФ (ICF CODING) ---
            icf_list = []
            icf_block = ""
            icf_map = [
                (0, "b140", {"ru": "Внимание", "en": "Attention", "es": "Atención", "pt": "Atenção"}),
                (1, "b1560", {"ru": "Зрит. восприятие", "en": "Visual perception", "es": "Percepción visual", "pt": "Percepção visual"}),
                (2, "b1561", {"ru": "Простр. восприятие", "en": "Visuospatial perception", "es": "Percepción visoespacial", "pt": "Percepção visoespacial"}),
                (3, "b176", {"ru": "Дин. праксис", "en": "Sequencing movements", "es": "Secuenciación motora", "pt": "Sequenciamento motor"}),
                (4, "b176", {"ru": "Афф. праксис", "en": "Complex movements", "es": "Movimientos complejos", "pt": "Movimientos complexos"}),
                (5, "b164", {"ru": "Констр. праксис", "en": "Executive functions", "es": "Funciones ejecutivas", "pt": "Funções executivas"}),
                (6, "b172", {"ru": "Счет", "en": "Calculation", "es": "Cálculo", "pt": "Cálculo"}),
                (7, "b167", {"ru": "Речь", "en": "Language functions", "es": "Funciones del lenguaje", "pt": "Funções da linguagem"}),
                (8, "b144", {"ru": "Память", "en": "Memory functions", "es": "Funciones de memoria", "pt": "Funções de memória"}),
                (9, "b164", {"ru": "Мышление", "en": "Higher cognitive functions", "es": "Funciones cognitivas superiores", "pt": "Funções cognitivas superiores"})
            ]

            for idx, b_code, names in icf_map:
                val = s[idx]
                # ИЗМЕНЕНО: Код попадает в таблицу МКФ только если дефицит 2 балла и выше
                if val > 1:
                    qual = val if val <= 3 else 4
                    label = names.get(lang, names['en'])
                    icf_list.append(f"{b_code}.{qual} ({label})")

            if icf_list:
                h_icf = {"ru": "КЛАССИФИКАЦИЯ МКФ", "en": "ICF CLASSIFICATION", "es": "CLASIFICACIÓN CIF", "pt": "CLASSIFICAÇÃO CIF"}.get(lang, "ICF")
                icf_block = f"\n\n{h_icf}:\n" + ", ".join(icf_list)

            # --- 6. РЕКОМЕНДАЦИИ (С АВТОМАТИЧЕСКИМ МКФ-ИНЖЕКТОРОМ) ---
            recoms_output = []
            d_map = {
                "block_1": "d160", "block_2": "d110", "block_3": "d210",
                "8": "d175", "9": "d175", "7": "d330", "panic-history": "d570"
            }
            e_map_presets = {
                # Блок 1: Нейродинамика и режим
                "ndyn": "e250", "msa": "e250", "retic": "e250", "н": "e250",
                
                # Блок 2: Инструменты и навигация
                "vci-svd": "e115", "v-gnosis": "e115", "A-aff": "e115",
                "apr-kin": "e115", "apr-dyn": "e115", "apr-con": "e155", # e155 - архитектура (пространство)
                
                # Блок 3: Контроль и поддержка (Люди)
                "r-reg": "e310", "l-reg": "e310", "a-dyn": "e310", # e310 - Семья/Родные
                
                # Специфика
                "8": "e355", "9": "e580", # e580 - Службы/Психиатрия
                "panic-history": "e355" # e355 - Терапевтический альянс
            }
            dep_presets = ["dep-grief", "dep-somatic", "dep-cog", "dep-anxious", "dep-adjustment"]

            def fetch_text(key):
                r_data = recom_db.get(key, [])
                if isinstance(r_data, list) and len(r_data) > 0:
                    item = r_data[0]
                    txt = item.get(lang, item.get('ru', ''))
                    if "(ICF:" in txt or "(CIF:" in txt: return txt

                    if key == "block_1": cur_val = max(s[0], s[6])
                    elif key == "block_2": cur_val = max(s[1], s[2], s[8])
                    elif key == "block_3": cur_val = max(s[3], s[9])
                    else: cur_val = 3 if (is_endo or t_k in ["8", "9"]) else 2

                    # --- ПРАВКА ТУТ: Убираем нули в скобках (ICF: d160.0) ---
                    # Если баллы по нулям, но рекомендация всё равно вызвана (бустером или пресетом)
                    if cur_val == 0: cur_val = 1

                    qual = cur_val if cur_val <= 4 else 4
                    icf_label = "CIF" if lang in ['es', 'pt'] else "ICF"

                    codes = []
                    d_code = d_map.get(key)
                    if d_code: codes.append(f"{d_code}.{qual}")

                    # --- 1. Твой рабочий цикл (не трогай его) ---
                    e_code = None
                    for p in presets:
                        if p in e_map_presets: e_code = e_map_presets[p]
                        elif p in dep_presets: e_code = "e355"

                    if e_code: codes.append(f"{e_code}.{qual}")

                    # --- 2. ЮВЕЛИРНАЯ ДОБАВКА (ЛОПУХ) ---
                    # Если пресет ничего не дал, но баллы высокие — докидываем код
                    if not e_code:
                        auto_e = None
                        if key == "block_1" and cur_val >= 3: auto_e = "e250"
                        elif key == "block_2" and cur_val >= 3: auto_e = "e115"
                        elif key == "block_3" and cur_val >= 3: auto_e = "e310"
                        elif (is_endo or t_k == "8") and not e_code: auto_e = "e310"

                        if auto_e: codes.append(f"{auto_e}.{qual}")
                    if codes:
                        txt = f"{txt.rstrip('. ')} ({icf_label}: {', '.join(codes)})"

                    if lang == 'ru' and gen == 'а':
                        txt = txt.replace("ен{g}", "на").replace("{g}", "а").replace("пациент ", "пациентка ")
                    else:
                        txt = txt.replace("{g}", "")
                    return txt
                return ""

            if (s[0] + s[6] + b1 >= 4): recoms_output.append(fetch_text("block_1"))
            if (s[1] + s[2] + s[8] + b2 >= 3): recoms_output.append(fetch_text("block_2"))
            if (s[3] + s[9] + b3 >= 3): recoms_output.append(fetch_text("block_3"))

            if is_endo or t_k == "8": recoms_output.append(fetch_text("8"))
            if t_k == "9": recoms_output.append(fetch_text("9"))
            if t_k == "7": recoms_output.append(fetch_text("7"))
            if "па" in tags or "panic" in tags: recoms_output.append(fetch_text("panic-history"))

            clean_res = [r for r in recoms_output if r and len(r) > 1]
            unique_res = []
            seen_texts = set()
            for x in clean_res:
                base_text = x.split(' (ICF:')[0].split(' (CIF:')[0].strip()
                if base_text not in seen_texts:
                    unique_res.append(x)
                    seen_texts.add(base_text)

            # --- ФИНАЛЬНАЯ СБОРКА UI И ВЫВОД ---
            ui = self.lib.get("ui_labels", {})
            r_label_dict = recom_db.get("label", {})
            r_h = r_label_dict.get(lang, ui.get('recommendations_header', {}).get(lang, "RECOMMENDATIONS"))

            h1 = ui.get('status_header', {}).get(lang, 'MSE')
            h2 = ui.get('results_header', {}).get(lang, 'PROFILE')
            h3 = ui.get('conclusion_header', {}).get(lang, 'SUMMARY')

            rec_text = ""
            if unique_res:
                rec_text = f"{r_h.upper()}:\n" + "\n\n".join(unique_res)

            res_summary = " ".join([p.strip() for p in final if p.strip()])

            final_report = (
                f"{h1}:\n{status_text}\n\n"
                f"{h2}:\n{' '.join(f_res)}\n\n"
                f"{h3}:\n{res_summary}\n"
                f"{icf_block}\n\n"
                f"{rec_text}"
            )
            return final_report

            # --- ФИНАЛЬНАЯ СБОРКА UI И ВЫВОД ---
            ui = self.lib.get("ui_labels", {})

            r_label_dict = recom_db.get("label", {})
            r_h = r_label_dict.get(lang, ui.get('recommendations_header', {}).get(lang, "RECOMMENDATIONS"))

            h1 = ui.get('status_header', {}).get(lang, 'MSE')
            h2 = ui.get('results_header', {}).get(lang, 'PROFILE')
            h3 = ui.get('conclusion_header', {}).get(lang, 'SUMMARY')

            # Склеиваем рекомендации (без ** и один раз)
            rec_text = ""
            if unique_res:
                rec_text = f"{r_h.upper()}:\n" + "\n\n".join(unique_res)

            # Собираем итоговый текст заключения (все блоки из final)
            res_summary = " ".join([p.strip() for p in final if p.strip()])

            # ФИКС: Убираем дубли из финальной строки.
            # Раньше ты вставлял и res_summary (где уже был rec_text), и r_h, и rec_text отдельно.
            final_report = (
                f"{h1}:\n{status_text}\n\n"
                f"{h2}:\n{' '.join(f_res)}\n\n"
                f"{h3}:\n{res_summary}\n"
                f"{icf_block}"
                # УДАЛИЛ ПОВТОРНУЮ СТРОКУ f"\n\n{rec_text}" - ОНА УЖЕ В res_summary
            )
            return final_report

        except Exception as e:
            return f"❌ Error in run: {e}"

# Загрузка JSON-аккумулятора
@st.cache_data
def load_matrix():
    with open('massive-mulilang.json', 'r', encoding='utf-8-sig') as f:
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
    
    # --- НОВЫЕ ПАРАМЕТРЫ ДЛЯ NEURODRAFT 3.0 ---
    if "lang_sel" in st.session_state: st.session_state["lang_sel"] = "en"
    if "moca_in" in st.session_state: st.session_state["moca_in"] = 30
    if "mmse_in" in st.session_state: st.session_state["mmse_in"] = 30
    if "gds_in" in st.session_state: st.session_state["gds_in"] = 0
    # ------------------------------------------
    
    st.rerun()

st.set_page_config(page_title="NeuroDraft 3.0", layout="wide")

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
                <span style="color: #FF4B4B;"></span>NeuroDraft
            </h2>
            <span style="color: #808495; font-style: italic; font-size: 0.75em;">Comprehensive system of syndromic neuropsychological analysis</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 1. СЕКРЕТНЫЙ ЗАМОК (В САМОМ ВЕРХУ ПЕРЕД ПРОВЕРКОЙ) ---
PASSWORD = "1111" # <--- УБЕДИСЬ, ЧТО ОН ТУТ!

if "auth" not in st.session_state:
    st.session_state["auth"] = False

# --- 2. ТЕПЕРЬ ПРОВЕРЯЕМ ---
if not st.session_state["auth"]:
    # Твоя монолитная шапка (Draft)
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

    # --- ВСТАВКА: ВЫБОР ЯЗЫКА ---
    st.markdown("---")
    # Английский по умолчанию (index=0), Русский в конце
    lang = st.selectbox("🌐 LANGUAGE / ЯЗЫК", ["en", "es", "pt", "ru"], index=0, key="lang_sel")
    
    # Сразу тянем переводы заголовков из твоего массива massive-mulilang.json
    ui = matrix.get("ui_labels", {})
    status_h = ui.get("status_header", {}).get(lang, "STATUS")
    results_h = ui.get("results_header", {}).get(lang, "RESULTS")
    conclusion_h = ui.get("conclusion_header", {}).get(lang, "CONCLUSION")
    recs_h = ui.get("recs_header", {}).get(lang, "RECOMMENDATIONS")
    # ----------------------------

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
            <p style="color: #FF4B4B; font-weight: bold; font-size: 0.9em; margin: 5px 0;">NeuroDraftAssistant</p>
            <p style="color: #ffffff; font-size: 0.75em; margin: 0;">Разработка и методология:<br><b>Cognicore Systems</b></p>
            <hr style="margin: 8px 0; border: 0.5px solid #333;">
            <p style="color: #555; font-size: 0.6em;">Commercial v85.6-STABLE</p>
        </div>
    """, unsafe_allow_html=True)

# --- 3. ЦЕНТРАЛЬНОЕ ПОЛЕ (ФУНКЦИИ / ДОМЕНЫ) ---
# Тянем заголовок секции из ui_labels (status_h мы определили в сайдбаре)
st.subheader(f"📊 {status_h} (0-5)")

# Динамический список меток из твоего массива massive-mulilang.json
f_labels = [
    matrix.get("attention", {}).get("label", {}).get(lang, "Attention"),
    matrix.get("visual_gnosis", {}).get("label", {}).get(lang, "Visual Gnosis"),
    matrix.get("spatial", {}).get("label", {}).get(lang, "Spatial"),
    matrix.get("dynamic_praxis", {}).get("label", {}).get(lang, "Dynamic Praxis"),
    matrix.get("afferent_praxis", {}).get("label", {}).get(lang, "Afferent Praxis"),
    matrix.get("cube", {}).get("label", {}).get(lang, "Visuoconstructive"),
    matrix.get("calculation", {}).get("label", {}).get(lang, "Calculation"),
    matrix.get("speech", {}).get("label", {}).get(lang, "Language"),
    matrix.get("memory", {}).get("label", {}).get(lang, "Memory"),
    matrix.get("thinking", {}).get("label", {}).get(lang, "Executive")
]

scores = []

# Отрисовка ползунков: теперь они "умные" и мультиязычные
for i, label in enumerate(f_labels):
    scores.append(st.slider(f"{i+1}. {label}", 0, 5, 0, key=f"s_{i}"))

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
    engine = NeuroDraftAssistant(matrix)
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
