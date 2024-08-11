import sqlite3
conn = sqlite3.connect('cache.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM rss_item")
rows = cursor.fetchall()
conn.close()


# print("Title")
# for row in rows:
#     print(row[2])

# print("links")
# for row in rows:
#     print(row[4])

# print("author")
# for row in rows:
#     print(row[3])

# print("timestamp")
# for row in rows:
#     print(row[6])

# print("content")
# for row in rows:
#     print(row[7])
