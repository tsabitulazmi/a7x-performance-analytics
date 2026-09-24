import streamlit as st
import plotly.express as px
import pandas as pd

from queries import (
    get_overview,
    get_album_performance,
    get_song_performance,
    get_content_type_distribution,
    get_data_quality,
    get_song_growth,
    get_growth_trend,
    get_latest_growth,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="A7X Music Analytics",
    page_icon="🎸",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        padding-top: 1rem;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .metric-card {
        background-color: #111111;
        border-radius: 12px;
        padding: 18px;
        border: 1px solid #333333;
        text-align: center;
    }

    .metric-label {
        font-size: 0.85rem;
        color: #AAAAAA;
        margin-bottom: 5px;
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
    }

    .section-description {
        color: #888888;
        font-size: 0.95rem;
        margin-bottom: 1rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data(ttl=300)
def load_data():

    overview = get_overview()
    albums = get_album_performance()
    songs = get_song_performance()
    content_types = get_content_type_distribution()
    quality = get_data_quality()

    return (
        overview,
        albums,
        songs,
        content_types,
        quality,
    )


try:

    (
        overview,
        albums,
        songs,
        content_types,
        quality,
    ) = load_data()

except Exception as e:

    st.error("Failed to load data from Amazon Athena.")
    st.exception(e)
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🎸 A7X Analytics")

    st.caption(
        "Avenged Sevenfold Music Performance Analytics"
    )

    st.divider()

    page = st.sidebar.radio(
        "Navigation",
        [
            "Overview",
            "Song Analysis",
            "Album Analysis",
            "Growth Analysis",
            "Data Quality",
        ]
    )

    st.divider()

    st.caption(
        "Data Sources"
    )

    st.caption(
        "Spotify API"
    )

    st.caption(
        "YouTube Data API"
    )

    st.caption(
        "Amazon S3"
    )

    st.caption(
        "Amazon Athena"
    )

    st.caption(
        "dbt"
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def format_number(value):

    if pd.isna(value):
        return "0"

    value = float(value)

    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"

    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"

    return f"{value:,.0f}"


def format_percentage(value):

    if pd.isna(value):
        return "0.00%"

    return f"{float(value):.2%}"


# ============================================================
# OVERVIEW
# ============================================================

if page == "Overview":

    st.title("🎸 A7X Music Performance Analytics")

    st.markdown(
        """
        ### Executive Overview

        An analytical view of Avenged Sevenfold's music performance
        using Spotify metadata and YouTube engagement metrics.
        """
    )

    st.divider()

    overview_row = overview.iloc[0]

    total_songs = overview_row["total_songs"]
    total_albums = overview_row["total_albums"]
    total_views = overview_row["total_views"]
    total_likes = overview_row["total_likes"]
    total_engagement = overview_row["total_engagement"]

    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Songs",
            format_number(total_songs),
        )

    with col2:
        st.metric(
            "Albums",
            format_number(total_albums),
        )

    with col3:
        st.metric(
            "YouTube Views",
            format_number(total_views),
        )

    with col4:
        st.metric(
            "Likes",
            format_number(total_likes),
        )

    with col5:
        st.metric(
            "Engagement",
            format_number(total_engagement),
        )

    st.divider()

    # --------------------------------------------------------
    # ALBUM VIEWS
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Views by Album")

        album_chart = albums.sort_values(
            "total_views",
            ascending=True,
        )

        fig = px.bar(
            album_chart,
            x="total_views",
            y="album_name",
            orientation="h",
            labels={
                "total_views": "YouTube Views",
                "album_name": "Album",
            },
        )

        fig.update_layout(
            height=500,
            showlegend=False,
        )

        fig.update_xaxes(
            tickformat=",",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    # --------------------------------------------------------
    # TOP SONGS
    # --------------------------------------------------------

    with col2:

        st.subheader("Top 10 Songs by Views")

        top_songs = (
            songs
            .sort_values(
                "view_count",
                ascending=False,
            )
            .head(10)
            .sort_values(
                "view_count",
                ascending=True,
            )
        )

        fig = px.bar(
            top_songs,
            x="view_count",
            y="song_name",
            orientation="h",
            labels={
                "view_count": "YouTube Views",
                "song_name": "Song",
            },
        )

        fig.update_layout(
            height=500,
            showlegend=False,
        )

        fig.update_xaxes(
            tickformat=",",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    st.divider()

    # --------------------------------------------------------
    # TOP ENGAGEMENT
    # --------------------------------------------------------

    st.subheader("Songs with Highest Engagement Rate")

    st.info(
        """
        **Engagement Rate** measures audience interaction relative to total YouTube views.

        **Formula:** `(Likes + Comments) ÷ Views × 100`

        A higher percentage indicates more likes and comments relative to the video's
        total views. This metric is defined specifically for this project and may differ
        from engagement-rate definitions used by other analytics platforms.
        """
    )

    top_engagement = (
        songs
        .sort_values(
            "engagement_rate",
            ascending=False,
        )
        .head(10)
        .sort_values(
            "engagement_rate",
            ascending=True,
        )
    )

    fig = px.bar(
        top_engagement,
        x="engagement_rate",
        y="song_name",
        orientation="h",
        labels={
            "engagement_rate": "Engagement Rate",
            "song_name": "Song",
        },
    )

    fig.update_layout(
        height=450,
        showlegend=False,
    )

    fig.update_xaxes(
        tickformat=".2%",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ============================================================
# SONG ANALYSIS
# ============================================================

elif page == "Song Analysis":

    st.title("🎵 Song Analysis")

    st.markdown(
        """
        <div class="section-description">
        Explore song-level reach and audience engagement.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        albums_filter = [
            "All Albums"
        ] + sorted(
            songs["album_name"]
            .dropna()
            .unique()
            .tolist()
        )

        selected_album = st.selectbox(
            "Album",
            albums_filter,
        )

    with col2:

        content_filter = [
            "All Content Types"
        ] + sorted(
            songs["youtube_content_type"]
            .dropna()
            .unique()
            .tolist()
        )

        selected_content = st.selectbox(
            "YouTube Content Type",
            content_filter,
        )

    filtered = songs.copy()

    if selected_album != "All Albums":

        filtered = filtered[
            filtered["album_name"]
            == selected_album
        ]

    if selected_content != "All Content Types":

        filtered = filtered[
            filtered["youtube_content_type"]
            == selected_content
        ]

    # --------------------------------------------------------
    # FILTERED KPIs
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Songs",
            len(filtered),
        )

    with col2:
        st.metric(
            "Views",
            format_number(
                filtered["view_count"].sum()
            ),
        )

    with col3:
        st.metric(
            "Likes",
            format_number(
                filtered["like_count"].sum()
            ),
        )

    with col4:

        avg_engagement = (
            filtered["engagement_rate"].mean()
            if len(filtered) > 0
            else 0
        )

        st.metric(
            "Avg Engagement Rate",
            format_percentage(
                avg_engagement
            ),
        )

    st.divider()

    # --------------------------------------------------------
    # VIEWS VS ENGAGEMENT
    # --------------------------------------------------------

    st.subheader(
        "Reach vs Engagement"
    )

    fig = px.scatter(
        filtered,
        x="view_count",
        y="engagement_rate",
        size="like_count",
        color="album_name",
        hover_name="song_name",
        labels={
            "view_count": "YouTube Views",
            "engagement_rate": "Engagement Rate",
            "album_name": "Album",
        },
    )

    fig.update_xaxes(
        tickformat=",",
    )

    fig.update_yaxes(
        tickformat=".2%",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    # --------------------------------------------------------
    # TOP SONGS
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.subheader(
            "Top Songs by Views"
        )

        top_views = (
            filtered
            .sort_values(
                "view_count",
                ascending=False,
            )
            .head(10)
            .sort_values(
                "view_count",
            )
        )

        fig = px.bar(
            top_views,
            x="view_count",
            y="song_name",
            orientation="h",
        )

        fig.update_xaxes(
            tickformat=",",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with col2:

        st.subheader(
            "Top Songs by Engagement"
        )

        top_engagement = (
            filtered
            .sort_values(
                "engagement_rate",
                ascending=False,
            )
            .head(10)
            .sort_values(
                "engagement_rate",
            )
        )

        fig = px.bar(
            top_engagement,
            x="engagement_rate",
            y="song_name",
            orientation="h",
        )

        fig.update_xaxes(
            tickformat=".2%",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    # --------------------------------------------------------
    # DATA TABLE
    # --------------------------------------------------------

    st.subheader(
        "Song Performance Table"
    )

    display_columns = [
        "song_name",
        "album_name",
        "youtube_content_type",
        "view_count",
        "like_count",
        "comment_count",
        "engagement_count",
        "engagement_rate",
    ]

    st.dataframe(
        filtered[
            display_columns
        ].sort_values(
            "view_count",
            ascending=False,
        ),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# ALBUM ANALYSIS
# ============================================================

elif page == "Album Analysis":

    st.title("💿 Album Analysis")

    st.markdown(
        """
        <div class="section-description">
        Compare performance across Avenged Sevenfold albums.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # ALBUM KPI
    # --------------------------------------------------------

    selected_album = st.selectbox(
        "Select Album",
        albums["album_name"].tolist(),
    )

    album = albums[
        albums["album_name"]
        == selected_album
    ].iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Songs",
            int(album["song_count"]),
        )

    with col2:
        st.metric(
            "Total Views",
            format_number(
                album["total_views"]
            ),
        )

    with col3:
        st.metric(
            "Total Engagement",
            format_number(
                album["total_engagement"]
            ),
        )

    with col4:
        st.metric(
            "Engagement Rate",
            format_percentage(
                album["engagement_rate"]
            ),
        )

    st.divider()

    # --------------------------------------------------------
    # ALBUM COMPARISON
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.subheader(
            "Album Views"
        )

        fig = px.bar(
            albums.sort_values(
                "total_views"
            ),
            x="total_views",
            y="album_name",
            orientation="h",
        )

        fig.update_xaxes(
            tickformat=",",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with col2:

        st.subheader(
            "Average Views per Song"
        )

        fig = px.bar(
            albums.sort_values(
                "avg_views_per_song"
            ),
            x="avg_views_per_song",
            y="album_name",
            orientation="h",
        )

        fig.update_xaxes(
            tickformat=",",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    # --------------------------------------------------------
    # SONGS IN SELECTED ALBUM
    # --------------------------------------------------------

    album_songs = songs[
        songs["album_name"]
        == selected_album
    ].sort_values(
        "view_count",
        ascending=False,
    )

    st.subheader(
        f"Songs in {selected_album}"
    )

    st.dataframe(
        album_songs[
            [
                "song_name",
                "view_count",
                "like_count",
                "comment_count",
                "engagement_count",
                "engagement_rate",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# DATA QUALITY
# ============================================================

elif page == "Data Quality":

    st.title("🔍 Data Quality")

    st.markdown(
        """
        <div class="section-description">
        Monitor API matching and ingestion completeness.
        </div>
        """,
        unsafe_allow_html=True,
    )

    quality_row = quality.iloc[0]

    total = int(
        quality_row["total_songs"]
    )

    spotify_matched = int(
        quality_row["spotify_matched"]
    )

    youtube_matched = int(
        quality_row["youtube_matched"]
    )

    spotify_rate = (
        spotify_matched / total
        if total
        else 0
    )

    youtube_rate = (
        youtube_matched / total
        if total
        else 0
    )

    # --------------------------------------------------------
    # MATCH KPIs
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Songs",
            total,
        )

    with col2:
        st.metric(
            "Spotify Match",
            f"{spotify_rate:.1%}",
        )

    with col3:
        st.metric(
            "YouTube Match",
            f"{youtube_rate:.1%}",
        )

    with col4:

        st.metric(
            "Unmatched",
            total - youtube_matched,
        )

    st.divider()

    # --------------------------------------------------------
    # MATCHING STATUS
    # --------------------------------------------------------

    quality_chart = pd.DataFrame(
        {
            "Source": [
                "Spotify",
                "YouTube",
            ],
            "Matched": [
                spotify_matched,
                youtube_matched,
            ],
            "Unmatched": [
                total - spotify_matched,
                total - youtube_matched,
            ],
        }
    )

    quality_long = quality_chart.melt(
        id_vars="Source",
        var_name="Status",
        value_name="Songs",
    )

    fig = px.bar(
        quality_long,
        x="Source",
        y="Songs",
        color="Status",
        barmode="stack",
        title="API Matching Status",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    # --------------------------------------------------------
    # CONTENT TYPES
    # --------------------------------------------------------

    st.subheader(
        "YouTube Content Types"
    )

    col1, col2 = st.columns(2)

    with col1:

        fig = px.pie(
            content_types,
            names="youtube_content_type",
            values="song_count",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with col2:

        fig = px.bar(
            content_types,
            x="youtube_content_type",
            y="total_views",
        )

        fig.update_yaxes(
            tickformat=",",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    # --------------------------------------------------------
    # INGESTION
    # --------------------------------------------------------

    st.subheader(
        "Latest Ingestion"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Spotify",
            str(
                quality_row[
                    "latest_spotify_ingestion"
                ]
            ),
        )

    with col2:

        st.metric(
            "YouTube",
            str(
                quality_row[
                    "latest_youtube_ingestion"
                ]
            ),
        )

# ============================================================
# GROWTH ANALYSIS
# ============================================================

elif page == "Growth Analysis":

    st.title("Growth Analysis")
    st.caption(
        "Historical YouTube performance and snapshot-to-snapshot growth"
    )

    growth_df = get_song_growth()
    trend_df = get_growth_trend()
    latest_df = get_latest_growth()

    # --------------------------------------------------
    # KPIs
    # --------------------------------------------------

    latest_date = latest_df["ingestion_date"].max()

    total_growth = latest_df["view_growth"].sum()

    avg_daily_growth = latest_df[
        "avg_daily_view_growth"
    ].sum()

    positive_growth_songs = (
        latest_df["view_growth"] > 0
    ).sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Latest Snapshot",
        str(latest_date),
    )

    col2.metric(
        "Total Views Gained",
        f"{total_growth:,.0f}",
    )

    col3.metric(
        "Avg Daily Views Gained",
        f"{avg_daily_growth:,.0f}",
    )

    col4.metric(
        "Songs With Positive Growth",
        positive_growth_songs,
    )

    st.divider()

    # --------------------------------------------------
    # Total views trend
    # --------------------------------------------------

    st.subheader("Total YouTube Views Over Time")

    fig = px.line(
        trend_df,
        x="ingestion_date",
        y="total_views",
        markers=True,
        title="Total Views by Snapshot",
    )

    fig.update_layout(
        xaxis_title="Ingestion Date",
        yaxis_title="Total Views",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    # --------------------------------------------------
    # Top growing songs
    # --------------------------------------------------

    st.subheader("Fastest Growing Songs")

    top_growth = latest_df.head(10).copy()

    fig = px.bar(
        top_growth.sort_values(
            "avg_daily_view_growth"
        ),
        x="avg_daily_view_growth",
        y="song_name",
        orientation="h",
        title="Top 10 Songs by Average Daily View Growth",
    )

    fig.update_layout(
        xaxis_title="Average Daily View Growth",
        yaxis_title="Song",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    # --------------------------------------------------
    # Growth rate
    # --------------------------------------------------

    st.subheader("Highest View Growth Rate")

    top_rate = latest_df.sort_values(
        "view_growth_pct",
        ascending=False,
    ).head(10).copy()

    top_rate["growth_rate_pct"] = (
        top_rate["view_growth_pct"] * 100
    )

    fig = px.bar(
        top_rate.sort_values(
            "growth_rate_pct"
        ),
        x="growth_rate_pct",
        y="song_name",
        orientation="h",
        title="Top 10 Songs by View Growth Rate",
    )

    fig.update_layout(
        xaxis_title="Growth Rate (%)",
        yaxis_title="Song",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    # --------------------------------------------------
    # Song history
    # --------------------------------------------------

    st.subheader("Song Growth History")

    song_list = sorted(
        growth_df["song_name"].dropna().unique()
    )

    selected_song = st.selectbox(
        "Select a song",
        song_list,
    )

    song_history = growth_df[
        growth_df["song_name"] == selected_song
    ].sort_values("ingestion_date")

    fig = px.line(
        song_history,
        x="ingestion_date",
        y="view_count",
        markers=True,
        title=f"{selected_song} — YouTube Views",
    )

    fig.update_layout(
        xaxis_title="Ingestion Date",
        yaxis_title="Views",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.dataframe(
        song_history[
            [
                "ingestion_date",
                "view_count",
                "previous_view_count",
                "view_growth",
                "view_growth_pct",
                "days_since_previous_snapshot",
                "avg_daily_view_growth",
            ]
        ],
        use_container_width=True,
    )