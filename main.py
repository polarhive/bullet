import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import tkinter as tk
from tkinter import scrolledtext

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

# GUI
class RSSViewer(tk.Tk):
    def __init__(self, groups, titles, contents):
        super().__init__()
        self.title("RSS Feed Groups")
        self.geometry("800x600")
        self.groups = groups
        self.titles = titles
        self.contents = contents
        self.listbox = tk.Listbox(self, width=50, height=30)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)

        self.text_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=80, height=30)
        self.text_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        for idx, group in enumerate(groups):
            self.listbox.insert(tk.END, f"Group {idx + 1}")

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
