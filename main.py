import sys
import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QListWidget, QTextEdit, QSlider, QLabel, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

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

class RSSViewer(QMainWindow):
    def __init__(self, groups, titles, contents, ids):
        super().__init__()
        self.setWindowTitle("RSS Feed Groups")
        self.setGeometry(100, 100, 1000, 600)
        self.groups = groups
        self.titles = titles
        self.contents = contents
        self.ids = ids

        # Load Inter font
        font = QFont("Inter", 10)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # Create list widget for group titles
        self.list_widget = QListWidget()
        self.list_widget.setFont(font)
        self.list_widget.currentRowChanged.connect(self.on_list_selection)
        layout.addWidget(self.list_widget)

        # Create text edit for content display
        self.text_edit = QTextEdit()
        self.text_edit.setFont(font)
        layout.addWidget(self.text_edit)

        # Create slider and label for similarity threshold
        slider_layout = QVBoxLayout()
        self.threshold_label = QLabel("Similarity Threshold")
        self.threshold_label.setFont(font)
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setMinimum(0)
        self.threshold_slider.setMaximum(100)
        self.threshold_slider.setValue(50)
        self.threshold_slider.setTickInterval(1)
        self.threshold_slider.setTickPosition(QSlider.TicksBelow)
        self.threshold_slider.setSingleStep(1)
        self.threshold_slider.valueChanged.connect(self.on_threshold_change)

        slider_layout.addWidget(self.threshold_label)
        slider_layout.addWidget(self.threshold_slider)
        layout.addLayout(slider_layout)

        self.update_groups()

    def on_list_selection(self, index):
        if index >= 0:
            group = self.groups[index]
            self.text_edit.clear()
            for entry in group:
                self.text_edit.append(f"Title: {self.titles[entry]}")
                self.text_edit.append(f"Content: {self.contents[entry]}")
                self.text_edit.append("="*80)
                self.text_edit.append("")

    def on_threshold_change(self):
        threshold = self.threshold_slider.value() / 100.0
        self.update_groups(threshold)

    def update_groups(self, threshold=0.5):
        ids, titles, links, authors, contents = fetch_data(spam_keywords)
        self.groups = group_entries(contents, threshold)
        self.titles = titles
        self.contents = contents
        self.list_widget.clear()
        for idx, group in enumerate(self.groups):
            group_title = titles[group[0]]
            self.list_widget.addItem(f"Group {idx + 1}: {group_title}")

if __name__ == "__main__":
    spam_keywords_file = 'spam_keywords.txt'
    spam_keywords = load_spam_keywords(spam_keywords_file)
    ids, titles, links, authors, contents = fetch_data(spam_keywords)
    initial_groups = group_entries(contents, threshold=0.5)

    app = QApplication(sys.argv)
    viewer = RSSViewer(initial_groups, titles, contents, ids)
    viewer.show()
    sys.exit(app.exec_())
