# Project Context: Google Photos AI Retrieval Discovery Engine

## Executive Overview
The **Google Photos AI Retrieval Discovery Engine** is an AI-powered insights system and RAG-based assistant designed to analyze real-world user feedback across public channels. Its goal is to uncover, categorize, and quantify how users struggle to retrieve old visual memories from Google Photos when their memory of the image is incomplete or ambiguous.

---

## Core Problem Statement

### The Gap Between Metadata Search and Human Visual Memory
Google Photos users accumulate thousands of visual assets over years, including photos, videos, screenshots, documents, and scans. 

* **Conventional Search Capability**: Operates effectively when users recall exact metadata—such as a specific person's name, geotagged location, exact date, or explicit keyword.
* **Human Memory Reality**: Users frequently remember visual memories only **partially or contextually**. For example:
  * *"The photo of the small café we visited during our Goa trip"*
  * *"The screenshot of the medicine prescribed when I was sick last year"*
  * *"A picture of a red book on a wooden table from a few years ago"*

Users often forget precise dates, exact location tags, filenames, or specific words embedded in images.

> **Core Insight**: The problem is not simply **searching for photos**, but **retrieving a known visual memory from incomplete, ambiguous, or imperfect human memory**.

---

## Data Corpus & Multi-Channel Feedback Scope

User conversations about retrieval difficulties exist across fragmented public channels. The Discovery Engine aggregates and structures data across 6 primary sources:

1. **Apple App Store** (`app_store/`): Ratings, customer reviews, and feedback on iOS retrieval & search performance.
2. **Google Play Store** (`play_store/`): Reviews on Android photo management, backup issues, and search UX.
3. **Reddit** (`reddit_reviews/`): Deep user discussions, workarounds, and complaints on subreddits like r/googlephotos and r/techsupport.
4. **Google Help Community** (`community_reviews/`): Official support forum threads detailing specific user failure modes and feature gaps.
5. **YouTube Comments** (`youtube_reviews/`): User feedback on Google Photos feature demos, updates, and tutorial videos.
6. **Social Media** (`socialmedia_reviews/`): Public commentary on visual memory features, memories timeline, and search UX.

---

## Analytical & Behavioral Framework

The discovery engine processes raw feedback through a 6-stage structured insight pipeline:

```
[ User Memory ] ➔ [ Retrieval Intent ] ➔ [ Search Behavior ] ➔ [ Retrieval Failure ] ➔ [ Underlying Problem ] ➔ [ Opportunity Area ]
```

1. **User Memory**: What specific details the user retains (e.g., color, context, emotion, co-occurring events).
2. **Retrieval Intent**: What the user is trying to accomplish (e.g., find receipt, relive vacation moment, show a friend a document).
3. **Search Behavior**: Strategies, search queries, filters, or manual scrolling workarounds used.
4. **Retrieval Failure**: Where and why the attempt breaks down (e.g., zero search results, date misalignments, face tag gaps).
5. **Underlying Problem**: Root cause in indexing, metadata mapping, UI navigation, or search understanding.
6. **Opportunity Area**: Prioritized, evidence-backed product enhancements for Google Photos teams.

---

## Primary Research & Discovery Questions

The system enables internal stakeholders to explore key product questions grounded in real user evidence:

* **Asset Vulnerability**: What types of visual media (photos, videos, screenshots, document scans) are hardest for users to retrieve?
* **Memory Retention vs. Loss**: What details do users typically remember vs. what do they commonly forget?
* **Query Patterns & Workarounds**: How do users phrase queries when exact details are forgotten, and what workarounds do they employ?
* **Friction & Breakdown Points**: Where do retrieval journeys fail most frequently?
* **Problem Frequency**: Which retrieval issues occur repeatedly across distinct platforms and user segments?
* **High-Impact Opportunities**: Which user pain points represent the most meaningful opportunities for improving retrieval success?

---

## System Architecture & Target Outcome

### System Deliverables
1. **Curated & Filtered Corpus**: A source-backed dataset structured by relevance, memory attributes, and retrieval failure taxonomy.
2. **RAG-based AI Assistant**: A lightweight retrieval-augmented generation assistant enabling natural language Q&A over the multi-source review corpus.

### Strategic Product Value
* **Target Audience**: Product Managers, UX Researchers, Data Analysts, Core Experience Engineering, and Leadership.
* **Ultimate Goal**: Empower the Google Photos Core Experience team to increase the success rate of users attempting to find a remembered photo that they cannot precisely describe when starting their search.
