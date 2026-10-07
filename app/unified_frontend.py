import os
import sys
import time
import json
import pandas as pd
import streamlit as st
import plotly.express as px

# Ensure workspace root is in path
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from app.pm_console import PMConsole

# Page config MUST be the first Streamlit command
st.set_page_config(
    page_title="Google Search Discovery Engine",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Secrets bridge ────────────────────────────────────────────────────────────
# Streamlit Cloud supplies secrets via st.secrets, but LLMSynthesizer and
# taxonomy_engine both read os.environ. Without this the app silently runs in
# "deterministic_fallback" synthesis mode, which looks like it works.
for _key in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
    if not os.environ.get(_key):
        try:
            if _key in st.secrets:
                os.environ[_key] = str(st.secrets[_key])
        except Exception:
            pass  # no secrets configured (e.g. local run without secrets.toml)

# Initialize RAG Engine
@st.cache_resource
def get_console():
    return PMConsole()

def load_data():
    """Loads and preprocesses the enriched corpus."""
    corpus_path = os.path.join(workspace_root, "data_processing", "enriched_corpus.json")
    if not os.path.exists(corpus_path):
        return pd.DataFrame()
    
    with open(corpus_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    
    # Extract taxonomy fields into columns
    if "taxonomy" in df.columns:
        tax_df = pd.json_normalize(df["taxonomy"])
        # Merge back
        df = pd.concat([df.drop(columns=["taxonomy"]), tax_df], axis=1)
        
    return df

def load_total_records_count():
    """Returns the total number of raw (unfiltered) records."""
    unified_path = os.path.join(workspace_root, "data_processing", "unified_corpus.json")
    if not os.path.exists(unified_path):
        return 0
    with open(unified_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return len(data)


def render_dashboard():
    st.title("🔍 UX Research & Feedback Insights Dashboard")
    
    df = load_data()
    
    if df.empty:
        st.error("Enriched corpus not found or empty.")
        return
        
    # Preprocess missing or "Not specified" values
    taxonomy_cols = ["user_memory", "retrieval_intent", "search_behavior", "retrieval_failure", "underlying_problem", "opportunity_area"]
    for col in taxonomy_cols:
        if col in df.columns:
            df[col] = df[col].fillna("Not specified")
            df.loc[df[col] == "N/A", col] = "Not specified"
    
    # Global Filters
    st.markdown("### Filters")
    selected_sources = st.multiselect(
        "Select Channels (Sources)",
        options=df["source"].unique(),
        default=df["source"].unique()
    )
    
    # Filter Data
    filtered_df = df[df["source"].isin(selected_sources)]
    
    st.caption(f"**Total Records Analyzed**: {len(filtered_df):,}")
    
    # Top Level Metrics
    total_unfiltered = load_total_records_count()
    col1, col2, col3 = st.columns(3)
    col1.metric("Distinct Channels", filtered_df["source"].nunique())
    col2.metric("Total Unfiltered Records", f"{total_unfiltered:,}")
    col3.metric("Search-Relevant Records", f"{len(filtered_df):,}")
    
    # Charts
    st.markdown("---")
    st.header("1. Channel & Source Breakdown")
    
    source_counts = filtered_df["source"].value_counts().reset_index()
    source_counts.columns = ["Source", "Count"]
    fig_source = px.pie(source_counts, values="Count", names="Source", title="Feedback Distribution by Channel")
    st.plotly_chart(fig_source, use_container_width=True)
    
    st.markdown("---")
    st.header("2. Opportunity Matrix")
    st.markdown("Identified Problems and their frequency of occurrence across the highly relevant reviews.")
    
    problem_data = {
        "Identified Problem Area": [
            "Search Engine Failing / Zero Results",
            "Incorrect Date/Timeline Sorting",
            "Missing/Lost Photos after Backup",
            "App Crashing/Freezing during Retrieval",
            "Missing or Unrecognized Faces",
            "Inability to find Screenshots/Documents"
        ],
        "Frequency (Count)": [498, 419, 194, 161, 159, 70],
        "Percentage of Relevant Reviews": ["60.6%", "51.0%", "23.6%", "19.6%", "19.3%", "8.5%"],
        "Confidence Score": ["75%", "85%", "90%", "95%", "90%", "95%"]
    }
    prob_df = pd.DataFrame(problem_data)
    
    # Graphical Representation
    fig_matrix = px.bar(
        prob_df.sort_values("Frequency (Count)", ascending=True), 
        x="Frequency (Count)", 
        y="Identified Problem Area", 
        orientation='h',
        title="Opportunity Matrix: Frequency vs. Problem Area",
        color="Frequency (Count)",
        color_continuous_scale="Viridis",
        text="Percentage of Relevant Reviews"
    )
    fig_matrix.update_traces(textposition='outside')
    st.plotly_chart(fig_matrix, use_container_width=True)
    
    # Display as a nice Streamlit dataframe/table
    st.markdown("#### Detailed Data Table")
    st.dataframe(prob_df, use_container_width=True, hide_index=True)


def render_chatbot():
    st.title("💬 PM Q&A Chatbot")
    st.markdown("Ask natural language questions about the user feedback and get grounded, cited answers.")

    console = get_console()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "citations" in message and message["citations"]:
                with st.expander("View Citations"):
                    for idx, cite in enumerate(message["citations"], 1):
                        st.markdown(f"**{idx}. [Review ID: `{cite.get('review_id')}` | Source: {cite.get('source')}]({cite.get('url', '#')})**")
                        st.markdown(f"> *{cite.get('text', 'No text provided')}*")
            if "timings" in message and message["timings"]:
                st.caption(f"Latency: {message['execution_time_sec']}s")

    if prompt := st.chat_input("Ask a question..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Searching knowledge base...")
            
            try:
                result = console.ask(prompt)
                
                if "error" in result:
                    answer = f"Error: {result['error']}"
                    citations = []
                    timings = {}
                    execution_time = 0
                else:
                    answer = result["synthesized_answer"]
                    citations = result["citations"]
                    timings = result["stage_timings"]
                    execution_time = result["execution_time_sec"]

                message_placeholder.markdown(answer)
                
                if citations:
                    with st.expander(f"View {len(citations)} Citations"):
                        for idx, cite in enumerate(citations, 1):
                            st.markdown(f"**{idx}. [Review ID: `{cite.get('review_id')}` | Source: {cite.get('source')}]({cite.get('url', '#')})**")
                            st.markdown(f"> *{cite.get('review_text', cite.get('text', 'Excerpt not available'))}*")
                
                st.caption(f"Latency: {execution_time}s")
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "citations": citations,
                    "timings": timings,
                    "execution_time_sec": execution_time
                })
                
            except Exception as e:
                error_msg = f"An error occurred: {str(e)}"
                message_placeholder.markdown(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})


def render_channel_analysis():
    st.title("📊 Channel Deep Dive")
    df = load_data()
    if df.empty:
        st.error("Enriched corpus not found or empty.")
        return
        
    channels = df["source"].dropna().unique().tolist()
    if not channels:
        st.warning("No channels found.")
        return
        
    selected_channel = st.selectbox("Select Channel", sorted(channels))
    
    channel_df = df[df["source"] == selected_channel]
    total_reviews = len(channel_df)
    
    st.metric(f"Total Reviews from {selected_channel}", total_reviews)
    
    st.markdown("---")
    st.markdown("### Major Problems Identified")
    
    # Analyze data with keywords
    problems = {
        'Search Engine Failing / Zero Results': ['search', 'find', 'result', 'looking for'],
        'Incorrect Date/Timeline Sorting': ['date', 'year', 'month', 'sort', 'order', 'timeline'],
        'Missing/Lost Photos after Backup': ['missing', 'lost', 'deleted', 'backup', 'sync'],
        'App Crashing/Freezing during Retrieval': ['crash', 'slow', 'freeze', 'load', 'bug'],
        'Missing or Unrecognized Faces': ['face', 'person', 'recognize', 'tag'],
        'Inability to find Screenshots/Documents': ['screenshot', 'receipt', 'document', 'text']
    }
    
    problem_counts = {k: 0 for k in problems}
    problem_quotes = {k: [] for k in problems}
    
    for idx, row in channel_df.iterrows():
        text = (str(row.get('title', '')) + ' ' + str(row.get('review', ''))).lower()
        for prob, keywords in problems.items():
            if any(kw in text for kw in keywords):
                problem_counts[prob] += 1
                problem_quotes[prob].append(row)
                
    results = []
    for prob, count in problem_counts.items():
        if count > 0:
            results.append({
                "Problem Area": prob,
                "Count": count,
                "Percentage": f"{(count/total_reviews)*100:.1f}%"
            })
            
    if results:
        res_df = pd.DataFrame(results).sort_values("Count", ascending=False)
        st.dataframe(res_df, use_container_width=True, hide_index=True)
        
        # Show quotes for the topmost problem
        top_problem = res_df.iloc[0]["Problem Area"]
        st.markdown(f"### Highlighted Problem: **{top_problem}**")
        st.markdown(f"Representative consumer quotes from **{selected_channel}**:")
        
        quotes = problem_quotes[top_problem]
        # Sort by rating/score if available to show the "topmost rated" ones
        quotes.sort(key=lambda x: x.get("score", 0), reverse=True)
            
        for i, row in enumerate(quotes[:3]):
            score_str = f"Rating: {row.get('score', 'N/A')}" if 'score' in row else f"Score: {row.get('score', 'N/A')}"
            st.info(f"**{score_str}** | *\"{row.get('review', '')}\"*")
    else:
        st.info("No major specific problems identified in this channel based on current criteria.")



def render_memory_anchors():
    st.title("🧠 Memory Anchor Analysis")
    st.markdown("Analyze how people mentally anchor visual information when retrieving photos.")
    
    df = load_data()
    if df.empty:
        st.error("Enriched corpus not found or empty.")
        return
        
    try:
        from textblob import TextBlob
        def get_sentiment(text):
            polarity = TextBlob(text).sentiment.polarity
            if polarity > 0.1:
                return polarity, "Positive"
            elif polarity < -0.1:
                return polarity, "Negative"
            else:
                return polarity, "Neutral"
    except ImportError:
        def get_sentiment(text):
            text_lower = text.lower()
            positive_words = ['good', 'great', 'awesome', 'excellent', 'love', 'best', 'perfect', 'amazing', 'happy', 'like', 'helpful', 'easy']
            negative_words = ['bad', 'terrible', 'awful', 'worst', 'hate', 'stupid', 'useless', 'crap', 'annoying', 'bug', 'crash', 'fail', 'issue', 'problem', 'lost', 'missing', "can't", "cannot", "hard", "difficult"]
            
            pos_score = sum(1 for w in positive_words if w in text_lower)
            neg_score = sum(1 for w in negative_words if w in text_lower)
            
            polarity = (pos_score - neg_score) * 0.2
            if polarity > 0:
                return polarity, "Positive"
            elif polarity < 0:
                return polarity, "Negative"
            else:
                return 0.0, "Neutral"
        
    # Pre-process memory and sentiment
    mem_records = []
    for idx, row in df.iterrows():
        mem = row.get("user_memory", "Not specified")
        if mem not in ["Not specified", "None", "N/A", ""]:
            text = f"{row.get('title', '')} {row.get('review', '')}".strip()
            # Calculate Sentiment
            polarity, category = get_sentiment(text)
            
            r_data = row.to_dict()
            r_data["mem_category"] = mem
            r_data["sentiment_score"] = polarity
            r_data["sentiment_category"] = category
            r_data["full_text"] = text
            mem_records.append(r_data)
            
    mem_df = pd.DataFrame(mem_records)
    
    # Global metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Evaluated Records", "822")
    col2.metric("Explicit Mention of Anchor", str(len(mem_df)))
    col3.metric("Total Memory Anchor Types", str(mem_df["mem_category"].nunique()) if not mem_df.empty else "0")
    
    if mem_df.empty:
        st.info("No explicit memory anchors identified in the dataset.")
        return

    # Calculate frequencies
    mem_counts = mem_df["mem_category"].value_counts().reset_index()
    mem_counts.columns = ["Cognitive Memory Anchor", "Frequency (Count)"]
    mem_counts["% of Explicit Mentions"] = (mem_counts["Frequency (Count)"] / len(mem_df) * 100).apply(lambda x: f"{x:.1f}%")
    
    st.dataframe(mem_counts, use_container_width=True, hide_index=True)
    
    fig_mem = px.bar(
        mem_counts.sort_values("Frequency (Count)", ascending=True),
        x="Frequency (Count)",
        y="Cognitive Memory Anchor",
        orientation='h',
        title="Frequency of Memory Anchors",
        color="Frequency (Count)",
        color_continuous_scale="Blues",
        text="% of Explicit Mentions"
    )
    fig_mem.update_traces(textposition='outside')
    st.plotly_chart(fig_mem, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### Representative Consumer Quotes by Sentiment & Memory Anchor Combination")
    
    # Filter Section for Evidences
    sentiments = ["All"] + sorted(mem_df["sentiment_category"].unique().tolist())
    anchors = ["All"] + sorted(mem_df["mem_category"].unique().tolist())
    
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        sel_sentiment = st.selectbox("Select Sentiment Filter:", options=sentiments, index=0)
    with f_col2:
        sel_anchor = st.selectbox("Select Memory Anchor Filter:", options=anchors, index=0)
        
    filtered_evidences = mem_df.copy()
    if sel_sentiment != "All":
        filtered_evidences = filtered_evidences[filtered_evidences["sentiment_category"] == sel_sentiment]
    if sel_anchor != "All":
        filtered_evidences = filtered_evidences[filtered_evidences["mem_category"] == sel_anchor]
        
    count = len(filtered_evidences)
    st.caption(f"Found {count} consumer quotes matching {sel_sentiment} Sentiment + {sel_anchor} Memory Anchor.")
    
    if filtered_evidences.empty:
        st.info("No evidences found for the selected filters.")
    else:
        # Sort by absolute sentiment score to get highest sentiment intensity
        filtered_evidences["abs_sentiment"] = filtered_evidences["sentiment_score"].abs()
        top_evidences = filtered_evidences.sort_values(by="abs_sentiment", ascending=False).head(3)
        
        def get_color(sentiment):
            if sentiment == "Positive": return "#00cc96"
            elif sentiment == "Negative": return "#ff4b4b"
            return "#888888"
            
        for idx, row in top_evidences.iterrows():
            color = get_color(row['sentiment_category'])
            sentiment_label = f"{row['sentiment_category'].upper()} ({row['sentiment_score']:.4f})"
            
            st.markdown(f'''
            <div style="
                border: 1px solid rgba(130, 130, 130, 0.2);
                border-left: 4px solid {color};
                border-radius: 4px;
                padding: 15px;
                margin-bottom: 15px;
                background-color: rgba(130, 130, 130, 0.05);
            ">
                <div style="margin-bottom: 10px; display: flex; align-items: center; gap: 10px; font-size: 14px; flex-wrap: wrap;">
                    <span style="background-color: {color}; color: white; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 11px;">
                        {sentiment_label}
                    </span>
                    <span style="opacity: 0.8; font-weight: 500; font-size: 13px;">
                        <b>Channel:</b> {row["source"]} | <b>Anchor:</b> 
                    </span>
                    <span style="background-color: rgba(130, 130, 130, 0.2); padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; border: 1px solid rgba(130, 130, 130, 0.3);">
                        {row["mem_category"]}
                    </span>
                </div>
                <div style="font-style: italic; font-size: 15px; line-height: 1.5; opacity: 0.9;">
                    "{row['full_text']}"
                </div>
            </div>
            ''', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 💡 Key pain points and expectation (cross dataset discovery)")
    
    # Calculate Unmet Needs with Behaviour, Barrier, and Expectation
    problems = {
        'Reliable natural language search': {
            'keywords': ['search', 'find', 'result', 'looking for'],
            'expectation': 'Find photos using simple, everyday words with multiple clues.',
            'behaviour': 'Users type multiple vague clues (who, what, where) in a single query.',
            'barrier': 'Search engine strictly matches keywords and fails on complex queries.'
        },
        'Automatic duplicate cleanup': {
            'keywords': ['screenshot', 'receipt', 'document', 'text', 'duplicate'],
            'expectation': 'Screenshots and documents are separated from personal memories.',
            'behaviour': 'Users manually scroll past hundreds of receipts to find a photo.',
            'barrier': 'Lack of automatic categorization clutters the visual timeline.'
        },
        'Accurate chronological timeline': {
            'keywords': ['date', 'year', 'month', 'sort', 'order', 'timeline'],
            'expectation': 'Photos sorted in correct time order regardless of import origin.',
            'behaviour': 'Users rely on timeline scrolling as a fallback when search fails.',
            'barrier': 'Incorrect sorting disrupts chronological mental anchoring.'
        },
        'Transparent backup status': {
            'keywords': ['missing', 'lost', 'deleted', 'backup', 'sync'],
            'expectation': 'Certainty that photos are safely backed up and retrievable.',
            'behaviour': 'Users constantly check if photos are synced across devices.',
            'barrier': 'Unclear backup states cause anxiety over lost memories.'
        },
        'Stable app performance': {
            'keywords': ['crash', 'slow', 'freeze', 'load', 'bug'],
            'expectation': 'App remains responsive during heavy searches.',
            'behaviour': 'Users abandon searches if the app freezes or takes too long.',
            'barrier': 'Performance bottlenecks during complex retrieval.'
        },
        'Accurate facial recognition': {
            'keywords': ['face', 'person', 'recognize', 'tag'],
            'expectation': 'App correctly tags and retrieves specific people\'s faces.',
            'behaviour': 'Users try to filter by face but cannot find the person.',
            'barrier': 'Unrecognized or mis-grouped faces prevent social anchoring.'
        }
    }
    
    # Calculate frequencies and collect evidence
    unmet_results = []
    total_records = len(df)
    
    for title, info in problems.items():
        matching_rows = []
        for idx, row in df.iterrows():
            text = f"{row.get('title', '')} {row.get('review', '')}".lower()
            if any(kw in text for kw in info['keywords']):
                matching_rows.append(row)
                
        if matching_rows:
            unmet_results.append({
                'title': title,
                'count': len(matching_rows),
                'info': info,
                'rows': matching_rows
            })
            
    # Rank by frequency
    unmet_results.sort(key=lambda x: x['count'], reverse=True)
    
    html_content = ""
    
    for i, res in enumerate(unmet_results):
        rank = i + 1
        share = (res['count'] / total_records) * 100
        
        # Get one representative quote (remove source data as requested)
        quote = "No representative quote available."
        if res['rows']:
            best_row = res['rows'][0]
            quote = f"{best_row.get('title', '')} {best_row.get('review', '')}".strip()
            
        html_content += f"""
<div style="background: #ffffff; border-radius: 20px; border: 1px solid #e2e8f0; padding: 24px; margin-bottom: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
<h3 style="margin: 0; font-size: 22px; font-weight: 800; color: #0f172a; display: flex; align-items: center;">
<span style="background: #e2e8f0; color: #475569; padding: 4px 12px; border-radius: 20px; font-size: 16px; margin-right: 12px; font-weight: 800;">#{rank}</span>
{res['title']}
</h3>
<span style="font-weight: 700; color: #64748b; font-size: 14px; background: #f1f5f9; padding: 4px 10px; border-radius: 12px;">Frequency: {res['count']} ({share:.1f}%)</span>
</div>

<div style="font-size: 15px; font-style: italic; color: #475569; line-height: 1.5; margin-bottom: 20px; padding-left: 16px; border-left: 4px solid #cbd5e1;">
"{quote}"
</div>

<div style="background: #f8fafc; border-radius: 16px; padding: 20px; margin-bottom: 16px;">
<div style="font-size: 18px; font-weight: 800; color: #0f172a; margin-bottom: 8px;">Behaviour</div>
<div style="font-size: 15px; color: #334155; line-height: 1.5;">{res['info']['behaviour']}</div>
</div>

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
<div style="background: #ffe4e6; border: 1px solid #fecdd3; border-radius: 16px; padding: 18px; display: flex; flex-direction: column; gap: 8px;">
<div style="display: flex; align-items: center; gap: 10px;">
<div style="width: 30px; height: 30px; border-radius: 50%; background: #e11d48; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 16px;">!</div>
<div style="font-size: 18px; font-weight: 800; color: #be123c;">The gap</div>
</div>
<div style="font-size: 14.5px; color: #9f1239; line-height: 1.45;">{res['info']['barrier']}</div>
</div>

<div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 16px; padding: 18px; display: flex; flex-direction: column; gap: 8px;">
<div style="display: flex; align-items: center; gap: 10px;">
<div style="width: 30px; height: 30px; border-radius: 50%; background: #dcfce7; color: #16a34a; display: flex; align-items: center; justify-content: center; font-size: 16px;">💡</div>
<div style="font-size: 18px; font-weight: 800; color: #15803d;">The opportunity</div>
</div>
<div style="font-size: 14.5px; color: #166534; line-height: 1.45;">{res['info']['expectation']}</div>
</div>
</div>
</div>
"""
        
    st.markdown(html_content, unsafe_allow_html=True)

def main():
    st.markdown('''
        <style>
        /* Hide main menu and footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Banner styles */
        .main-banner {
            background: linear-gradient(135deg, #1e1e2f 0%, #2d2d44 100%);
            padding: 2.5rem;
            border-radius: 12px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .main-banner h1 {
            color: white;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            font-weight: 800;
        }
        .main-banner p {
            font-size: 1.1rem;
            opacity: 0.85;
            color: white;
        }
        
        /* Custom Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        .stTabs [aria-selected="true"] {
            border-bottom: 2px solid #ff4b4b;
        }
        </style>
        
        <div class="main-banner">
            <h4 style="margin: 0; color: #ff9a9e; font-weight: 600; font-size: 13px; text-transform: uppercase; letter-spacing: 1.5px;">Discovery Intelligence</h4>
            <h1 style="padding-top: 5px;">GOOGLE SEARCH DISCOVERY ENGINE</h1>
            <p>Uncover why users search, what they want, and how to convert visual memories into actions.</p>
        </div>
    ''', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Competitive Analysis", "Memory Anchor Analysis", "Discovery Chat"])
    
    with tab1:
        render_dashboard()
    with tab2:
        render_channel_analysis()
    with tab3:
        render_memory_anchors()
    with tab4:
        render_chatbot()

if __name__ == "__main__":
    main()
