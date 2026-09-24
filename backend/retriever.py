import re

import chromadb
from sentence_transformers import SentenceTransformer


# =========================================================
# MODEL
# =========================================================

model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


# =========================================================
# DATABASE
# =========================================================

client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_collection(
    name="tamil_literature"
)


# =========================================================
# LITERATURE WORKS
# =========================================================

WORK_KEYWORDS = {

    "Thirukkural": [
        "திருக்குறள்",
        "திருக்குறளை",
        "திருக்குறளில்",
        "திருக்குறளின்",
        "திருக்குறளுக்கு",
        "குறள்",
        "குறளை",
        "குறளில்",
        "குறளின்",
        "குறளுக்கு"
    ],

    "Purananuru": [
        "புறநானூறு",
        "புறநானூற்றை",
        "புறநானூற்றில்",
        "புறநானூற்றின்",
        "புறநானூற்றுக்கு"
    ],

    "Akananuru": [
        "அகநானூறு",
        "அகநானூற்றை",
        "அகநானூற்றில்",
        "அகநானூற்றின்",
        "அகநானூற்றுக்கு"
    ],

    "Natrinai": [
        "நற்றிணை",
        "நற்றிணையை",
        "நற்றிணையில்",
        "நற்றிணையின்",
        "நற்றிணைக்கு"
    ],

    "Kuruntokai": [
        "குறுந்தொகை",
        "குறுந்தொகையை",
        "குறுந்தொகையில்",
        "குறுந்தொகையின்",
        "குறுந்தொகைக்கு"
    ],

    "Silappatikaram": [
        "சிலப்பதிகாரம்",
        "சிலப்பதிகாரத்தை",
        "சிலப்பதிகாரத்தில்",
        "சிலப்பதிகாரத்தின்",
        "சிலப்பதிகாரத்திற்கு"
    ],

    "Manimekalai": [
        "மணிமேகலை",
        "மணிமேகலையை",
        "மணிமேகலையில்",
        "மணிமேகலையின்",
        "மணிமேகலைக்கு"
    ]
}


# =========================================================
# DETECT WORK
# =========================================================

def detect_work(question):

    if not question:
        return None

    for work, keywords in WORK_KEYWORDS.items():

        for keyword in keywords:

            if keyword in question:
                return work

    return None


# =========================================================
# TAMIL NUMBER WORDS
# =========================================================

TAMIL_NUMBER_WORDS = {

    "முதல்": "1",
    "முதலாம்": "1",
    "ஒன்று": "1",
    "ஒரு": "1",

    "இரண்டாவது": "2",
    "இரண்டாம்": "2",
    "இரண்டு": "2",

    "மூன்றாவது": "3",
    "மூன்றாம்": "3",
    "மூன்று": "3",

    "நான்காவது": "4",
    "நான்காம்": "4",
    "நான்கு": "4",

    "ஐந்தாவது": "5",
    "ஐந்தாம்": "5",
    "ஐந்து": "5",

    "ஆறாவது": "6",
    "ஆறாம்": "6",
    "ஆறு": "6",

    "ஏழாவது": "7",
    "ஏழாம்": "7",
    "ஏழு": "7",

    "எட்டாவது": "8",
    "எட்டாம்": "8",
    "எட்டு": "8",

    "ஒன்பதாவது": "9",
    "ஒன்பதாம்": "9",
    "ஒன்பது": "9",

    "பத்தாவது": "10",
    "பத்தாம்": "10",
    "பத்து": "10"
}


# =========================================================
# DETECT EXACT VERSE / POEM NUMBER
# =========================================================

def detect_verse_number(question):

    if not question:
        return None

    text = question.strip()


    for word in sorted(
        TAMIL_NUMBER_WORDS,
        key=len,
        reverse=True
    ):

        if word in text:
            return TAMIL_NUMBER_WORDS[word]


    match = re.search(
        r"(\d{1,4})\s*(?:ஆம்|ஆவது|வது|ம்)",
        text
    )

    if match:
        return match.group(1)


    match = re.search(
        r"(?:பாடல்|குறள்|எண்)\s*(?:எண்\s*)?(\d{1,4})",
        text
    )

    if match:
        return match.group(1)


    match = re.search(
        r"\b(\d{1,4})\b",
        text
    )

    if match:
        return match.group(1)


    return None


# =========================================================
# CITATION
# =========================================================

def make_citation(metadata):

    if not metadata:
        return "Tamil Literature"

    work = metadata.get(
        "work",
        "Tamil Literature"
    )

    number = metadata.get(
        "verse_number",
        ""
    )


    if work == "Thirukkural":

        if number:
            return f"திருக்குறள் — குறள் {number}"

        return "திருக்குறள்"


    if number:
        return f"{work} — பாடல்/பதிவு {number}"


    return work


# =========================================================
# EXACT DATABASE LOOKUP
# =========================================================

def exact_search(work, verse_number):

    try:

        results = collection.get(
            where={
                "$and": [
                    {"work": work},
                    {"verse_number": str(verse_number)}
                ]
            },
            include=[
                "documents",
                "metadatas"
            ]
        )

        documents = results.get(
            "documents",
            []
        )

        metadatas = results.get(
            "metadatas",
            []
        )

        if documents:

            return {
                "documents": [documents],
                "metadatas": [metadatas]
            }

    except Exception:
        pass

    return None


# =========================================================
# VERIFIED THIRUKKURAL CHAPTERS / TOPICS
# =========================================================

THIRUKKURAL_TOPICS = {

    "வான்சிறப்பு": (11, 20),
    "நீத்தார் பெருமை": (21, 30),
    "அறன் வலியுறுத்தல்": (31, 40),

    "அன்பு": (71, 80),
    "அன்புடைமை": (71, 80),

    "இனியவை": (91, 100),
    "செய்ந்நன்றி": (101, 110),
    "நடுவுநிலை": (111, 120),
    "அடக்கம்": (121, 130),
    "ஒழுக்கம்": (131, 140),
    "பொறுமை": (151, 160),
    "அழுக்காறு": (161, 170),
    "வெஃகாமை": (171, 180),
    "புறங்கூறாமை": (181, 190),
    "பயனில சொல்லாமை": (191, 200),
    "தீவினை": (201, 210),
    "ஒப்புரவு": (211, 220),
    "ஈகை": (221, 230),
    "புகழ்": (231, 240),
    "அருள்": (241, 250),

    "ஊழ்": (371, 380),

    "கல்வி": (391, 400),
    "கேள்வி": (411, 420),
    "அறிவு": (421, 430),
    "குற்றம்": (431, 440),

    "முயற்சி": (611, 620),
    "ஆள்வினை": (611, 620),

    "நட்பு": (781, 790),
    "கூடா நட்பு": (811, 820),

}


# =========================================================
# TOPIC KEYWORDS
# =========================================================

TOPIC_KEYWORDS = {

    "வான்சிறப்பு": [
        "வான்சிறப்பு",
        "மழை",
        "மழையை"
    ],

    "நீத்தார் பெருமை": [
        "நீத்தார்",
        "துறவு",
        "துறவிகள்"
    ],

    "அறன் வலியுறுத்தல்": [
        "அறம்",
        "அறனை",
        "அறத்தை"
    ],

    "அன்பு": [
        "அன்பு",
        "அன்பைப்",
        "அன்பை",
        "அன்பின்",
        "அன்புடைய",
        "அன்புடைமை"
    ],

    "இனியவை": [
        "இனியவை",
        "இனிய சொல்"
    ],

    "செய்ந்நன்றி": [
        "நன்றி",
        "செய்ந்நன்றி",
        "நன்றியை"
    ],

    "நடுவுநிலை": [
        "நடுவுநிலை",
        "நடுநிலை"
    ],

    "அடக்கம்": [
        "அடக்கம்",
        "அடக்கத்தை"
    ],

    "ஒழுக்கம்": [
        "ஒழுக்கம்",
        "ஒழுக்கத்தை"
    ],

    "பொறுமை": [
        "பொறுமை",
        "பொறுத்தல்",
        "பொறுமையை"
    ],

    "ஈகை": [
        "ஈகை",
        "கொடை",
        "தானம்"
    ],

    "அருள்": [
        "அருள்",
        "கருணை",
        "கருணையை"
    ],

    "கல்வி": [
        "கல்வி",
        "கற்க",
        "கற்றல்",
        "கற்றவர்",
        "கல்வியை",
        "கல்வியைப்",
        "படிப்பு"
    ],

    "கேள்வி": [
        "கேள்வி",
        "கேள்வியை",
        "கேட்பது"
    ],

    "அறிவு": [
        "அறிவு",
        "அறிவை",
        "அறிவுடைய"
    ],

    "குற்றம்": [
        "குற்றம்",
        "குற்றத்தை",
        "குற்றங்கள்"
    ],

    "முயற்சி": [
        "முயற்சி",
        "முயற்சியை",
        "உழைப்பு",
        "உழைப்பை"
    ],

    "நட்பு": [
        "நட்பு",
        "நண்பர்",
        "நண்பன்",
        "நட்பை"
    ],

    "கூடா நட்பு": [
        "கூடா நட்பு",
        "தீய நட்பு"
    ]

}


# =========================================================
# DETECT TOPIC
# =========================================================

def detect_topic(question):

    if not question:
        return None

    # More specific topics first
    topics = sorted(
        TOPIC_KEYWORDS.items(),
        key=lambda item: max(
            len(keyword)
            for keyword in item[1]
        ),
        reverse=True
    )

    for topic, keywords in topics:

        for keyword in keywords:

            if keyword in question:

                return topic

    return None


# =========================================================
# TOPIC SEARCH
# =========================================================

def topic_search(
    work,
    topic
):

    if work != "Thirukkural":
        return None

    topic_range = THIRUKKURAL_TOPICS.get(
        topic
    )

    if not topic_range:
        return None

    start_number, end_number = topic_range


    try:

        results = collection.get(
            where={
                "work": "Thirukkural"
            },
            include=[
                "documents",
                "metadatas"
            ]
        )

        documents = results.get(
            "documents",
            []
        )

        metadatas = results.get(
            "metadatas",
            []
        )

        matched_documents = []
        matched_metadatas = []


        for document, metadata in zip(
            documents,
            metadatas
        ):

            number = metadata.get(
                "verse_number"
            )

            if not number:
                continue

            try:
                number_int = int(number)
            except ValueError:
                continue


            if start_number <= number_int <= end_number:

                matched_documents.append(
                    document
                )

                matched_metadatas.append(
                    metadata
                )


        if matched_documents:

            return {
                "documents": [
                    matched_documents
                ],
                "metadatas": [
                    matched_metadatas
                ]
            }

    except Exception:
        pass


    return None


# =========================================================
# SEMANTIC SEARCH
# =========================================================

def semantic_search(
    question,
    requested_work=None,
    top_k=5
):

    query_embedding = model.encode(
        [question]
    ).tolist()


    if requested_work:

        return collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            where={
                "work": requested_work
            }
        )


    return collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )


# =========================================================
# MAIN SEARCH
# =========================================================

def search_verses(
    question,
    top_k=5
):

    requested_work = detect_work(
        question
    )

    requested_number = detect_verse_number(
        question
    )


    # =====================================================
    # 1. EXACT NUMBER SEARCH
    # =====================================================

    if requested_work and requested_number:

        exact_result = exact_search(
            requested_work,
            requested_number
        )

        if exact_result:
            return exact_result


    # =====================================================
    # 2. VERIFIED TOPIC SEARCH
    # =====================================================

    requested_topic = detect_topic(
        question
    )

    if requested_work and requested_topic:

        topic_result = topic_search(
            requested_work,
            requested_topic
        )

        if topic_result:
            return topic_result


    # =====================================================
    # 3. SEMANTIC FALLBACK
    # =====================================================

    return semantic_search(
        question,
        requested_work,
        top_k
    )