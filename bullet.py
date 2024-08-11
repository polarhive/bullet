import sqlite3, sys, os
from flask import Flask, render_template, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

def load_spam_keywords(file_path):
    with open(file_path, 'r') as file:
        keywords = [line.strip() for line in file]
    return keywords

def is_spam(title, content, spam_keywords):
    for keyword in spam_keywords:
        variations = [keyword.lower(), f"#{keyword.lower()}"]
        for variation in variations:
            if variation in title.lower() or variation in content.lower():
                return True
    return False

def fetch_data(spam_keywords):
    conn = sqlite3.connect('/home/polarhive/.local/share/newsboat/cache.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, author, url, content FROM rss_item WHERE unread = 1")
    rows = cursor.fetchall()
    conn.close()

    titles = []
    links = []
    authors = []
    contents = []
    ids = []

    n = len(rows)

    if n == 0:
        print("No unread articles")
        sys.exit()
    
    app.run(debug=True)

    count = 0
    for row in rows:
        id, title, author, url, content = row
        if not is_spam(title, content, spam_keywords):
            ids.append(id)
            titles.append(title)
            links.append(url)
            authors.append(author)
            contents.append(content)
            count += 1
        if count >= n:
            break

    return ids, titles, links, authors, contents

def group_entries(contents, threshold):
    if not contents or all(not content.strip() for content in contents):
        return []

    vectorizer = TfidfVectorizer(stop_words='english')
    
    try:
        tfidf_matrix = vectorizer.fit_transform(contents)
    except ValueError as e:
        if str(e) == 'empty vocabulary; perhaps the documents only contain stop words':
            return []
        else:
            raise

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
    spam_keywords_file = 'spam_keywords.txt'
    spam_keywords = load_spam_keywords(spam_keywords_file)
    ids, titles, links, _, contents = fetch_data(spam_keywords)
    initial_groups = group_entries(contents, threshold=0.5)
    
    # Sort groups by size (largest groups first)
    sorted_groups = sorted(enumerate(initial_groups), key=lambda x: len(x[1]), reverse=True)
    sorted_groups = zip(*sorted_groups) if sorted_groups else ([], [])
    
    return render_template('index.html', groups=sorted_groups, titles=titles, contents=contents, links=links, ids=ids)

@app.route('/update_groups', methods=['POST'])
def update_groups():
    threshold = float(request.form['threshold'])
    spam_keywords_file = 'spam_keywords.txt'
    spam_keywords = load_spam_keywords(spam_keywords_file)
    ids, titles, links, contents = fetch_data(spam_keywords)
    groups = group_entries(contents, threshold)
    
    # Sort groups by size (largest groups first)
    sorted_groups = sorted(enumerate(groups), key=lambda x: len(x[1]), reverse=True)
    
    # Unzip the sorted groups
    sorted_groups = zip(*sorted_groups) if sorted_groups else ([], [])
    
    return jsonify(groups=sorted_groups, titles=titles, contents=contents, links=links, ids=ids)

@app.route('/mark_as_read', methods=['POST'])
def mark_as_read():
    ids = request.json.get('ids', [])
    if not ids:
        return jsonify({'status': 'error', 'message': 'No IDs provided'}), 400

    conn = sqlite3.connect(f'/home/{os.getenv("USER")}/.local/share/newsboat/cache.db')
    cursor = conn.cursor()
    cursor.executemany("UPDATE rss_item SET unread = 0 WHERE id = ?", [(id,) for id in ids])
    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=False)
