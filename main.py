import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import tkinter as tk
from tkinter import scrolledtext

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

spam_keywords_file = 'spam_keywords.txt'
spam_keywords = load_spam_keywords(spam_keywords_file)

conn = sqlite3.connect('/home/polarhive/.local/share/newsboat/cache.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM rss_item")
rows = cursor.fetchall()
conn.close()
titles = []
links = []
authors = []
timestamps = []
contents = []

n = len(rows)/10
count = 0
for row in rows:
    title = row[2]
    content = row[7]
    if not is_spam(title, content, spam_keywords):
        titles.append(title)
        links.append(row[4])
        authors.append(row[3])
        timestamps.append(row[6])
        contents.append(content)
        count += 1
    if count >= n:
        break

# Vectorize contents using TF-IDF
vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = vectorizer.fit_transform(contents)

# Cosine similarity matrix
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

# Group similar entries
threshold = 0.1
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

# Create the GUI
class RSSViewer(tk.Tk):
    def __init__(self, groups, titles, contents):
        super().__init__()
        self.title("RSS Feed Groups")
        self.geometry("800x600")
        self.groups = groups
        self.titles = titles
        self.contents = contents

        # Create a listbox to display the groups
        self.listbox = tk.Listbox(self, width=50, height=30)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)

        # Create a scrolled text widget to display the content
        self.text_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=80, height=30)
        self.text_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Populate the listbox with group titles
        for idx, group in enumerate(groups):
            group_title = titles[group[0]]
            self.listbox.insert(tk.END, f"Group {idx + 1}: {group_title}")

    def on_select(self, event):
        selected_idx = self.listbox.curselection()[0]
        group = self.groups[selected_idx]
        self.text_area.delete('1.0', tk.END)
        for entry in group:
            self.text_area.insert(tk.END, f"Title: {self.titles[entry]}\n")
            self.text_area.insert(tk.END, f"Content: {self.contents[entry]}\n\n")
            self.text_area.insert(tk.END, "="*80 + "\n\n")

if __name__ == "__main__":
    app = RSSViewer(groups, titles, contents)
    app.mainloop()
