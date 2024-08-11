from sqlite3 import connect
from os.path import expanduser
from flask import Flask, jsonify, request, render_template
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

db_path = expanduser('~/.local/share/newsboat/cache.db')
spam_path = expanduser('~/.local/share/newsboat/spam_keywords.txt')

app = Flask(__name__)

def is_spam(title, content, spam_keywords):
    title_lower = title.lower()
    content_lower = content.lower()
    for keyword in spam_keywords:
        variations = [keyword.lower(), f"#{keyword.lower()}"]
        if any(variation in title_lower or variation in content_lower for variation in variations):
            return True
    return False

def fetch_data(spam_keywords):
    conn = connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, author, url, content FROM rss_item WHERE unread = 1")
    rows = cursor.fetchall()
    conn.close()

    ids, titles, links, authors, contents = [], [], [], [], []

    if not rows:
        return ids, titles, links, authors, contents

    for row in rows:
        id, title, author, url, content = row
        if not is_spam(title, content, spam_keywords):
            ids.append(id)
            titles.append(title)
            links.append(url)
            authors.append(author)
            contents.append(content)

    return ids, titles, links, authors, contents

def group_entries(contents, threshold):
    if not contents or all(not content.strip() for content in contents):
        return []

    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(contents)
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

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

    return groups

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_groups', methods=['POST'])
def update_groups():
    """
    Update and return grouped articles based on the similarity threshold.
    """
    threshold = float(request.form.get('threshold', 0.5))

    with open(spam_path, 'r') as f:
        spam_keywords = [line.strip() for line in f]

    ids, titles, links, authors, contents = fetch_data(spam_keywords)
    groups = group_entries(contents, threshold)

    return jsonify({
        'ids': ids,
        'titles': titles,
        'links': links,
        'authors': authors,
        'contents': contents,
        'groups': groups
    })

@app.route('/mark_as_read', methods=['POST'])
def mark_as_read():
    ids_to_mark = request.json.get('ids', [])
    if not ids_to_mark:
        return jsonify({'error': 'No IDs provided'}), 400

    conn = connect(db_path)
    cursor = conn.cursor()
    cursor.executemany("UPDATE rss_item SET unread = 0 WHERE id = ?", [(id,) for id in ids_to_mark])
    conn.commit()
    conn.close()

    return jsonify({'status': 'success', 'marked_ids': ids_to_mark})

if __name__ == '__main__':
    app.run(debug=True)
