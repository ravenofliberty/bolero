import logging
import datetime
import random

import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

from words.word_metadata import Gender, Tags, Words
from persistence.mongo import PersistenceManager


def get_random_n_from_list(n, l):
    _l = [a for a in l] # just to be safe
    res = []
    for i in range(n):
        _len = len(_l)
        pick = random.randint(0, _len-1)
        res.append(_l.pop(pick))
    return res


if __name__ == "__main__":
    st.set_page_config(
        page_title='Bolero',
        page_icon=':bell:',
        layout='wide',
        initial_sidebar_state='auto',
    )

    st.title(f'Project Bolero')

    pm = PersistenceManager()

    st.header(f'Word bank')
    data = list(pm.client.bolero_data.find())
    for doc in data:
        del doc["_id"]
        # del doc['practice_data']
        doc["Example: German"] = list(doc["example"].keys())[0]
        doc["Example: English"] = list(doc["example"].values())[0]
        del doc["example"]

    data_df = pd.DataFrame(data)
    overview_df = data_df[[c for c in data_df.columns if c not in ["practice_data"]]]
    overview_df["verb_forms"] = overview_df["verb_forms"].apply(lambda x: ", ".join([v for k, v in x.items()]) if all(list(x.values())) else "---")
    overview_df["tags"] = overview_df["tags"].apply(lambda x: [v for v in x if v != "NA"] if any([v!="NA" for v in x]) else "---")
    overview_df["see_also"] = overview_df["see_also"].apply(lambda x: [v for v in x if v != "NA"] if any([v != "NA" for v in x]) else "---")

    cols_overview = st.columns([0.1, 5, 0.1])
    cols_overview[1].dataframe(overview_df[[c for c in overview_df.columns if c != "verb_forms"] + ["verb_forms"]])

    st.subheader(f"Performance Report")
    practice_df = pd.DataFrame(data_df.set_index('word')['practice_data'].to_dict()).T
    practice_df['to_ger'] = practice_df['to_ger'].apply(lambda x: {datetime.datetime.fromisoformat(k): v for k, v in x.items()})
    practice_df['to_eng'] = practice_df['to_eng'].apply(lambda x: {datetime.datetime.fromisoformat(k): v for k, v in x.items()})

    stats = {}
    for word, r in practice_df.T.to_dict().items():
        right_to_ger = sum(pd.Series(r['to_ger']))
        total_to_ger = len(pd.Series(r['to_ger']))
        fail_to_ger = total_to_ger - right_to_ger
        perc_to_ger = right_to_ger / total_to_ger

        right_to_eng = sum(pd.Series(r['to_eng']))
        total_to_eng = len(pd.Series(r['to_eng']))
        fail_to_eng = total_to_eng - right_to_eng
        perc_to_eng = right_to_eng / total_to_eng

        stats[word] = {
            'right_to_ger': right_to_ger,
            'total_to_ger': total_to_ger,
            'fail_to_ger': fail_to_ger,
            'perc_to_ger': perc_to_ger,
            'right_to_eng': right_to_eng,
            'total_to_eng': total_to_eng,
            'fail_to_eng': fail_to_eng,
            'perc_to_eng': perc_to_eng,
        }

    stats_df = pd.DataFrame(stats).T
    stats_df['cls'] = data_df.set_index("word")['cls']

    labels = 'Success (To Ger)', 'Fail (To Ger)', 'Success (To Eng)', 'Fail (To Eng)'
    colors = ['#3D8DF5', '#ADCCF7', '#16A163', '#C7EBD1']
    explode = [0, 0, 0, 0]
    cols = st.columns([3, 3, 3])
    count = 0
    for cls in Words.__members__.keys():
        _stats_df = stats_df[stats_df['cls'] == cls].sum()
        sizes = [
            _stats_df['right_to_eng'],
            _stats_df['fail_to_eng'],
            _stats_df['right_to_ger'],
            _stats_df['fail_to_ger'],
        ]
        fig1, ax1 = plt.subplots(figsize=(5,5))
        ax1.title.set_text(cls)
        ax1.pie(sizes, explode=explode, labels=labels, autopct="%1.1f%%", shadow=False, startangle=90, colors=colors)
        ax1.axis("equal")
        cols[count].pyplot(fig1)
        count += 1

    by_date_to_ger = {}
    for row in practice_df.iterrows():
        for _d, res in row[1]['to_ger'].items():
            d = _d.date()
            if by_date_to_ger.get(d, None) is None:
                by_date_to_ger[d] = {"Success": 1, "Fail": 0} if res else {"Success": 0, "Fail": 1}
            else:
                if res:
                    by_date_to_ger[d]["Success"] += 1
                else:
                    by_date_to_ger[d]["Fail"] += 1

    by_date_to_eng = {}
    for row in practice_df.iterrows():
        # print(row[0])
        for _d, res in row[1]['to_eng'].items():
            d = _d.date()
            if by_date_to_eng.get(d, None) is None:
                by_date_to_eng[d] = {"Success": 1, "Fail": 0} if res else {"Success": 0, "Fail": 1}
            else:
                if res:
                    by_date_to_eng[d]["Success"] += 1
                else:
                    by_date_to_eng[d]["Fail"] += 1

    col1, col2 = st.columns([3,3])
    col1.markdown("**english -> german**")
    col1.line_chart(pd.DataFrame(by_date_to_ger).T)
    col2.markdown("**german -> english**")
    col2.line_chart(pd.DataFrame(by_date_to_eng).T)

    st.header("Practice section")
    fix_seed = st.number_input("Fix seed", value=100)
    random.seed(fix_seed)

    category = st.selectbox("Select word type", ['All'] + list(Words.__members__.keys()))
    _df = data_df[data_df['cls'] == category] if category != 'All' else data_df
    words = _df['word'].to_list()
    word_per_test = st.slider("How many words in one test", min_value=2, max_value=len(words), value=4)

    with st.form("practice"):
        random_words = get_random_n_from_list(word_per_test, words)

        answer_key_to_eng = _df.set_index('word')['meaning'].to_dict()
        answer_key_to_ger = _df.set_index('meaning')['word'].to_dict()

        st.subheader(f"Provide translation from German to English: ")
        test_answers_to_eng = {}
        for word in random_words[:len(random_words)//2]:
            test_answers_to_eng[word] = st.text_input(f"{word}")

        st.subheader(f"Provide translation from English to German: ")
        test_answers_to_ger = {}
        for word in random_words[len(random_words)//2:]:
            test_answers_to_ger[word] = st.text_input(f"{answer_key_to_eng[word]}")

        submitted_test = st.form_submit_button("Submit test")

    if submitted_test:
        """ Results: """
        test_results = {k: {"to_eng": None, "to_ger": None} for k in random_words}

        # To Eng
        for k, v in test_answers_to_eng.items():
            test_results[k]["to_eng"] = True if answer_key_to_eng[k] == v else False

        # To Ger
        for k, v in test_answers_to_ger.items():
            test_results[k]["to_ger"] = True if v.lower() == k.lower() else False

        st.info(f"Test results:")
        test_results_df = pd.DataFrame(test_results)
        st.dataframe(test_results_df)

        if test_results_df.all().all():
            st.info("Well done! Test passed")
        elif test_results_df.any().any():
            st.info(f"Could be better, some errors: {test_results}")
        else:
            st.error(f"Terrible, all wrong: {test_results}")

        # Saving results
        for word, res in test_results.items():
            practice_data_results = _df.set_index('word')['practice_data'].to_dict()
            practice_data_result = practice_data_results[word]

            # To eng
            if res['to_eng'] is not None:
                practice_data_result['to_eng'][datetime.datetime.now().isoformat()] = res['to_eng']

            # To ger
            if res['to_ger'] is not None:
                practice_data_result['to_ger'][datetime.datetime.now().isoformat()] = res['to_ger']

            pm.update_practice_data(word, practice_data_result)

        st.info(f"Results saved")

    st.header(f'Edit Word-bank')
    col1, _ = st.columns([1,8])
    mode = col1.select_slider("Insert / Update mode", ["Insert", "Update"])

    if mode == "Insert":
        with st.form("insert"):
            word = st.text_input("word")
            meaning = st.text_input("meaning")
            gender = st.selectbox("Gender", Gender.__members__.keys())
            cls = st.selectbox("Class", Words.__members__.keys())

            cols_verb = st.columns([3,3])
            ich = cols_verb[0].text_input("ich (Verbs only)", None)
            du = cols_verb[0].text_input("du (Verbs only)", None)
            er = cols_verb[0].text_input("er (Verbs only)", None)

            wir = cols_verb[1].text_input("wir (Verbs only)", None)
            ihr = cols_verb[1].text_input("ihr (Verbs only)", None)
            sie = cols_verb[1].text_input("sie (Verbs only)", None)


            example_ger = st.text_input("Example in German", "---")
            example_eng = st.text_input("Example in English", "---")
            tag_1 = st.selectbox("Tag 1", ["NA"]+[t for t in Tags.__members__.keys()], index=0)
            tag_2 = st.selectbox("Tag 2", ["NA"]+[t for t in Tags.__members__.keys()], index=0)
            tag_3 = st.selectbox("Tag 3", ["NA"]+[t for t in Tags.__members__.keys()], index=0)
            see_also_1 = st.text_input("See Also 1", "NA")
            see_also_2 = st.text_input("See Also 2", "NA")

            submitted_insert = st.form_submit_button("Insert word")

        example = {"---": "---"}
        if example_eng != "---" or example_ger != "---":
            assert example_eng != "---" and example_ger != "---", f"Example must be in eng and ger"
            example = {example_ger: example_eng}

        if submitted_insert:
            json = {
                "word": word,
                "meaning": meaning,
                "gender": gender,
                "cls": cls,
                "example": example,
                "tags": [tag_1, tag_2, tag_3],
                "see_also": [see_also_1, see_also_2],
                "practice_data": {
                    "to_ger": {datetime.datetime.now().isoformat(): True},
                    "to_eng": {datetime.datetime.now().isoformat(): True},
                },
                "verb_forms": {
                    "ich": ich,
                    "du": du,
                    "er": er,
                    "wir": wir,
                    "ihr": ihr,
                    "sie": sie,
                },
            }

            pm.update_all(json)
            st.info(f"Word {word} was saved in mongo")

    elif mode == "Update":
        col1, _ = st.columns([1, 8])
        word = col1.selectbox("Select word", sorted(data_df['word'].to_list(), key=str.casefold), index=0)

        data_json = pm.pull_data(word=word)

        with st.form("Update"):
            word = st.text_input("word", word)
            meaning = st.text_input("meaning", data_json["meaning"])
            gender = st.selectbox("Gender", Gender.__members__.keys(), list(Gender.__members__.keys()).index(data_json["gender"]))
            cls = st.selectbox("Class", Words.__members__.keys(), list(Words.__members__.keys()).index(data_json["cls"]))

            cols_verb = st.columns([3,3])
            ich = cols_verb[0].text_input("ich (Verbs only)", data_json["verb_forms"]["ich"])
            du = cols_verb[0].text_input("du (Verbs only)", data_json["verb_forms"]["du"])
            er = cols_verb[0].text_input("er (Verbs only)", data_json["verb_forms"]["er"])

            wir = cols_verb[1].text_input("wir (Verbs only)", data_json["verb_forms"]["wir"])
            ihr = cols_verb[1].text_input("ihr (Verbs only)", data_json["verb_forms"]["ihr"])
            sie = cols_verb[1].text_input("sie (Verbs only)", data_json["verb_forms"]["sie"])

            example_ger = st.text_input("Example in German", list(data_json["example"].keys())[0])
            example_eng = st.text_input("Example in English", list(data_json["example"].values())[0])
            tag_1 = st.selectbox("Tag 1", list(Tags.__members__.keys()), list(Tags.__members__.keys()).index(data_json["tags"][0]))
            tag_2 = st.selectbox("Tag 2", list(Tags.__members__.keys()), list(Tags.__members__.keys()).index(data_json["tags"][1]))
            tag_3 = st.selectbox("Tag 3", list(Tags.__members__.keys()), list(Tags.__members__.keys()).index(data_json["tags"][2]))
            see_also_1 = st.text_input("See Also 1", data_json["see_also"][0])
            see_also_2 = st.text_input("See Also 2", data_json["see_also"][1])

            submitted_update = st.form_submit_button("Update word")

        example = {"---": "---"}
        if example_eng != "---" or example_ger != "---":
            assert example_eng != "---" and example_ger != "---", f"Example must be in eng and ger"
            example = {example_ger: example_eng}

        if submitted_update:
            json = {
                "word": word,
                "meaning": meaning,
                "gender": gender,
                "cls": cls,
                "example": example,
                "tags": [tag_1, tag_2, tag_3],
                "see_also": [see_also_1, see_also_2],
                "practice_data": {
                    "to_ger": {datetime.datetime.now().isoformat(): True},
                    "to_eng": {datetime.datetime.now().isoformat(): True},
                },
                "verb_forms": {
                    "ich": ich,
                    "du": du,
                    "er": er,
                    "wir": wir,
                    "ihr": ihr,
                    "sie": sie,
                },
            }

            pm.update_all(json)
            st.info(f"Word {word} was updated in mongo")

    else:
        st.error(f"Undefined mode: {mode}")


