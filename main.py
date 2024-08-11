import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# setup
conn = sqlite3.connect('cache.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM rss_item")
rows = cursor.fetchall()
conn.close()
titles = []
links = []
authors = []
timestamps = []
contents = []

# cleanup
n=50
for row in rows[:n]:
    titles.append(row[2])
    links.append(row[4])
    authors.append(row[3])
    timestamps.append(row[6])
    contents.append(row[7])

# vectorize contents using TF-IDF
vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = vectorizer.fit_transform(contents)

# cosine similarity matrix
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

# group similar entries
threshold = 0.5
groups = []
visited = set()

for i in range(len(contents)):
    if i in visited:
        continue
    group = [i]
    visited.add(i)
    for j in range(i + 1, len(contents)):
        if cosine_sim[i][j] > threshold and j not in visited:
            group.append(j)
            visited.add(j)
    groups.append(group)

for id, group in enumerate(groups):
    print(f"Group {id + 1}:")
    for entry in group:
        print(f"Title: {titles[entry]}")
        print(f"Content: {contents[entry]}")

