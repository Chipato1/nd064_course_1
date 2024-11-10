import sqlite3
import logging
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import sys

conn_count = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global conn_count
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    conn_count = conn_count + 1
    app.logger.info("DB Connection established")
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
# Configure logging

app.logger.setLevel(logging.DEBUG)

class InfoFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.INFO


stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
stdout_handler.addFilter(InfoFilter())  # Only allow INFO level
app.logger.addHandler(stdout_handler)

stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.WARNING) 
app.logger.addHandler(stderr_handler)


# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    app.logger.info("Main route called")
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    app.logger.info("A certain post is called")
    post = get_post(post_id)
    if post is None:
      app.logger.warning("The Post doesnt exists, returning 404 error page")
      return render_template('404.html'), 404
    else:
      app.logger.info(f"The Post is {post['title']}")
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info("About Us called")
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        app.logger.info("Post Created with title: " + str(title))
        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            return redirect(url_for('index'))

    return render_template('create.html')


@app.route('/healthz')
def healthcheck():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )
    app.logger.info('Heatlh request successfull')
    app.logger.debug('Debug Message')
    return response

@app.route('/metrics')
def metrics():
    global conn_count
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    post_count = len(posts)  # Get the count of posts
    connection.close()
    
    response = app.response_class(
        response=json.dumps({
            "db_connection_count": conn_count,
            "post_count": post_count
        }),
        status=200,
        mimetype='application/json'
    )
    app.logger.info('Metrics Send')
    return response

# start the application on port 3111
if __name__ == "__main__":
   app.run(host='0.0.0.0', port='3111')
