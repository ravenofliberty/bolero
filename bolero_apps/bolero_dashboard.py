import logging
import datetime
import random

import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

from words.word_metadata import Gender, Tags, Words
from persistence.mongo import PersistenceManager
from bolero_apps.bolero_dashboard_reports import (
    get_data, performance_review_raport, practice_section, edit_section
)


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
        page_icon=":smiley:",
        layout='wide',
        initial_sidebar_state='auto',
    )

    st.title(f'Project Bolero')

    pm = PersistenceManager()

    overview_df, stats_df, data_df, practice_df, worst_words_df = get_data(pm)

    # Sidebar
    with st.sidebar:
        st.markdown(f"German special letters:  **ä, ö, ü, ß / Ä, Ö, Ü, ẞ**")
        st.info("Worst words")
        st.dataframe(worst_words_df.style.background_gradient(axis=0, cmap='RdYlGn').format('{:.2f}'),
                     height=25 * len(worst_words_df))

    # Word Bank
    st.header("Word Bank")
    end_columns = ["verb_forms", "see_also"]
    st.dataframe(overview_df[
        [c for c in overview_df.columns if c not in end_columns] + end_columns
        ].style.background_gradient(axis=0, subset=['perc_to_eng', 'perc_to_ger'], cmap='RdYlGn'))

    # Performance Review
    st.header("Performance Review")
    performance_review_raport(stats_df, overview_df, practice_df)

    # Practice section
    st.header("Practice section")
    if st.checkbox(f"Open practice section"):
        practice_section(data_df, pm, worst_words_df)

    # Edit Section
    st.header(f'Edit Word-bank')
    if st.checkbox(f"Open Edit Section"):
        edit_section(data_df, pm)
