
# Add this optimized route to your app.py

@app.route('/articles-fast')
def articles_fast():
    """Optimized articles page with previews and pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Show fewer articles per page
    
    conn = sqlite3.connect('news_database.db')
    cursor = conn.cursor()
    
    # Get only essential fields + preview
    cursor.execute("""
        SELECT id, title, 
               SUBSTR(content, 1, 200) as preview,
               source_name, date_added, category
        FROM articles 
        ORDER BY date_added DESC 
        LIMIT ? OFFSET ?
    """, (per_page, (page-1) * per_page))
    
    articles = []
    for row in cursor.fetchall():
        articles.append({
            'id': row[0],
            'title': row[1],
            'preview': row[2] + '...' if len(row[2]) == 200 else row[2],
            'source_name': row[3],
            'date_added': row[4],
            'category': row[5]
        })
    
    # Get total count for pagination
    cursor.execute("SELECT COUNT(*) FROM articles")
    total = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('articles_fast.html', 
                         articles=articles,
                         page=page,
                         per_page=per_page,
                         total=total,
                         has_next=page * per_page < total,
                         has_prev=page > 1)
