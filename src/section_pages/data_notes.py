# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

"""Data Notes page: dataset overview, completeness by block, methodology, caveats."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.data_loader import data_quality_profile


def render_data_notes(df: pd.DataFrame) -> None:
    """Render the Data Notes page: metrics, block completeness, methodology, definitions.

    Args:
        df: Filtered analysis DataFrame (used for data_quality_profile).
    """
    st.title("Data Notes & Methodology")

    dq = data_quality_profile(df)

    st.subheader("Dataset Overview")
    cols = st.columns(4)
    cols[0].metric("Total respondents", dq["n_rows"])
    cols[1].metric("Variables", dq["n_cols"])
    cols[2].metric("Missing org size", dq["org_size_missing"])
    cols[3].metric("Missing local authority", dq["la_missing"])

    st.divider()

    st.subheader("Response Completeness by Question Block")
    block_df = pd.DataFrame(
        dq["block_completeness"].items(), columns=["Question Block", "Completeness (%)"]
    ).sort_values("Completeness (%)", ascending=False)
    # st.dataframe(block_df, use_container_width=True, hide_index=True)
    # use_container_width=True is deprecated and is already removed in Streamlit since 2025-12-31
    st.dataframe(block_df, width="stretch", hide_index=True)

    st.divider()

    st.subheader("Methodology Notes")
    st.markdown("""
    - **Survey**: Baromedr Cymru Wave 2, conducted in collaboration with NTU VCSE Observatory

    - **Likert Scale**: A psychometric, often 5 or 7-point, survey rating system used to measure attitudes, opinions, and behaviors by gauging the level of agreement, frequency, or satisfaction. **Refer:** [Likert Scale](https://en.wikipedia.org/wiki/Likert_scale) for more information.

    - **Period**: January–February 2026

    - **Sample**: 111 Welsh voluntary sector organisations (self-selected; not a random sample)

    - **Format**: Online survey via Qualtrics; 10–15 minute completion time

    - **Multi-select questions**: Presented in wide format (one column per option; non-null = selected)

    - **Privacy**: All data anonymised prior to analysis. Results suppressed when filtered sample < 5 organisations (k-anonymity)
    """)

    st.subheader("Definitions of volunteering")
    st.markdown("""
    - **Volunteering vs unpaid caring**: This analysis follows the Baromedr definition of volunteering
      and does not treat unpaid caring roles (for family members, for example) as volunteering.

    - **Formal and informal activity**: Many real-world examples (e.g. community clean-ups, emergency response,
      neighbourhood action) can sit on the boundary between formal and informal volunteering. Where possible,
      Baromedr questions focus on activity that organisations can reasonably observe and report.

    - **Age ranges**: Headline figures from other sources about the share of people who volunteer often use specific
      age bands (for example 16–74 or 15–85). Under‑15s and very elderly volunteers may therefore be under-represented
      in population estimates, even if organisations rely on them in practice.
    """)

    st.subheader("Caveats")
    st.markdown("""
    - **Self-selection bias**: Respondents chose to participate; findings may not represent all Welsh voluntary sector organisations

    - **Cardiff over-representation (raw counts)**: 23% of respondents are Cardiff-based; interpret geographic patterns with caution

    - **Powys over-representation (proportional to population)**: 2.34 representation index - respondents are Powys-based; interpret geographic patterns with caution. **NOTE:** Representation index of 1.0 indicates proportional-to-population sampling; values above 1.0 indicate over-representation.

    - **Small sub-groups**: Some local authority and activity type segments have very few respondents. Avoid over-interpreting these segments

    - **Wave 2 only**: Cross-wave trend analysis requires Wave 1 data (not included in this dataset)

    - **Ordinal data**: Likert-scale responses are ordinal, not interval. Median is more appropriate than mean
    """)

    st.subheader("Estimated Number of VCSE Organisations in Wales")
    st.markdown("""
    - For the `est_vcse_orgs` column, it appeas to not be so simple to fully validate those numbers as official local-authority counts counts from an authoritative Wales-wide source.

    - There appears to be some good sector-level sources, but not a clean official table matching this column definition.

    - The reason is that Welsh sector sources use different universes:
      - WCVA says Wales has **32,000+** third sector organisations

      - While NCVO reports **7,009** charities in Wales in its 2023 Almanac

      - Equal to about **2.3 organisations** per 1,000 people.

    - The pre-populated helper CSV sums up to **14,980** organisations, which is about **4.7** per **1,000** people using the total population.

    - That sits neatly between the “registered charities only” count and the broader “all third sector organisations” count.

    - Therefore, `est_vcse_orgs` is only considered plausible as a modelled estimate, but not validated as an official observed count.
    """)


# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
